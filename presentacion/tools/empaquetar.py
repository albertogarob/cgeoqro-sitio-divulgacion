#!/usr/bin/env python3
"""Empaqueta una sesión en un solo archivo HTML autocontenido.

    python3 tools/empaquetar.py sesiones/S01-.../index.html

Produce salidas/S01-....html: un fichero único que lleva dentro reveal.js, el
tema, las tipografías, los fondos, las imágenes y los videos. Se abre con doble
clic, sin servidor y sin conexión. Es lo que se sube a Classroom en lugar del
PDF, y conserva animaciones, video y navegación, que el PDF perdía.

Qué cambia respecto al deck de trabajo:

  - Se conservan los apuntes de estudio (<aside class="apuntes">) y se inyecta el
    lector que los muestra, con su botón y su vista imprimible. Es lo único de
    los cuatro bloques de notas que viaja al grupo.
  - Se elimina todo lo que solo mira quien da la clase: el guion de orador
    (<aside class="notes">), el guion corto (<aside class="corto">), la nota
    didáctica (<aside class="didactica">), las marcas
    de recorte (data-recorte), los comentarios del deck y del tema, y el plugin
    de notas,
    porque el guion incluye indicaciones de conducción que no van al grupo. Con
    --con-guion se conservan y la tecla S vuelve a abrir la vista de orador.
  - Se quitan el anotador (revisar.js), el apuntador (apuntador.js), el lector de
    estudio (estudio.js) y el pincel (pincel.js), que son herramientas de trabajo
    del docente. Con --con-apuntador se conserva el apuntador, y entonces el
    paquete sirve para presentar sin servidor: tecla T. Implica --con-guion,
    porque el apuntador lee el guion del deck.
  - Se encienden los controles y la barra de progreso, para que se pueda pasar
    lámina con el ratón. Con --sin-controles se deja igual que el original.

Los videos no se incrustan como data: URI sino como blob construido al abrir el
archivo: es lo único que permite hacer seek fiable a un segundo concreto, y de
eso dependen las láminas con data-video.
"""
import argparse
import base64
import os
import pathlib
import re
import sys

TIPOS = {
    ".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg", ".gif": "image/gif", ".svg": "image/svg+xml",
    ".avif": "image/avif", ".ico": "image/x-icon",
    ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf",
    ".otf": "font/otf",
    ".mp4": "video/mp4", ".webm": "video/webm", ".ogv": "video/ogg",
    ".mp3": "audio/mpeg", ".m4a": "audio/mp4", ".ogg": "audio/ogg",
    ".wav": "audio/wav",
}
IMAGENES = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".avif", ".ico"}
MEDIOS = {".mp4", ".webm", ".ogv", ".mp3", ".m4a", ".ogg", ".wav"}

EXTERNO = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|#|\?)", re.I)

PREAMBULO = """<script>
/* Medios incrustados por tools/empaquetar.py.

   Van como blob y no como data: URI porque el seek a un segundo concreto solo
   es fiable sobre un blob, y las láminas con data-video dependen de eso. Este
   bloque corre después de todas las láminas y antes de reveal, así que los
   atributos ya están reescritos cuando el deck arranca. */
(function () {
  var datos = %s;
  var mapa = {};
  Object.keys(datos).forEach(function (clave) {
    var bin = atob(datos[clave][1]), n = bin.length, buf = new Uint8Array(n);
    for (var i = 0; i < n; i++) buf[i] = bin.charCodeAt(i);
    mapa[clave] = URL.createObjectURL(new Blob([buf], { type: datos[clave][0] }));
    datos[clave][1] = '';
  });
  ['data-video', 'data-background-video', 'data-medio'].forEach(function (attr) {
    Array.prototype.forEach.call(document.querySelectorAll('[' + attr + ']'), function (el) {
      var url = mapa[el.getAttribute(attr)];
      if (!url) return;
      if (attr !== 'data-medio') { el.setAttribute(attr, url); return; }
      el.setAttribute('src', url);
      var medio = el.tagName === 'SOURCE' ? el.parentElement : el;
      if (medio && medio.load) medio.load();
    });
  });
})();
</script>
"""


class Empaquetador:
    def __init__(self, deck, con_guion=False, controles=True, con_apuntador=False):
        self.deck = deck
        self.base = deck.parent
        self.con_guion = con_guion
        # El apuntador dentro del paquete solo tiene sentido con el guion:
        # es lo que lee. Pedirlo implica conservarlo.
        self.con_apuntador = con_apuntador
        if con_apuntador:
            self.con_guion = True
        self.controles = controles
        self.medios = {}     # ruta tal como aparece en el HTML -> Path
        self.faltantes = []
        self.partes = []     # (etiqueta, bytes originales) para el informe

    # -- utilidades ----------------------------------------------------------

    def resolver(self, ref, base):
        """Ruta absoluta de una referencia local, o None si no lo es."""
        if not ref or EXTERNO.match(ref):
            return None
        limpia = ref.split("?")[0].split("#")[0]
        if not limpia:
            return None
        destino = (base / limpia).resolve()
        if not destino.is_file():
            self.faltantes.append(ref)
            return None
        return destino

    def tipo(self, p):
        return TIPOS.get(p.suffix.lower(), "application/octet-stream")

    def base64(self, p):
        return base64.b64encode(p.read_bytes()).decode("ascii")

    def datauri(self, p):
        return "data:%s;base64,%s" % (self.tipo(p), self.base64(p))

    def anotar(self, etiqueta, p):
        self.partes.append((etiqueta, p.stat().st_size))

    # -- hojas de estilo -----------------------------------------------------

    def css(self, ruta, vistos=None):
        """Devuelve el CSS con sus @import resueltos y sus url() incrustadas."""
        vistos = vistos or set()
        if ruta in vistos:
            return ""
        vistos.add(ruta)
        texto = ruta.read_text(encoding="utf-8")
        # Los comentarios del tema explican su cocina, incluido el guion corto.
        # Se quitan antes de incrustar nada, porque después el CSS ya lleva
        # data: URI en base64 y una barra dentro de un blob parecería un cierre.
        texto = re.sub(r"/\*.*?\*/", "", texto, flags=re.S)

        def importar(m):
            p = self.resolver(m.group(1), ruta.parent)
            if p is None:
                return m.group(0)
            self.anotar("css " + p.name, p)
            return self.css(p, vistos)

        texto = re.sub(r'@import\s+(?:url\()?\s*["\']([^"\')]+)["\']\s*\)?\s*;',
                       importar, texto)

        def recurso(m):
            p = self.resolver(m.group(2), ruta.parent)
            if p is None:
                return m.group(0)
            self.anotar(p.name, p)
            return "url(%s)" % self.datauri(p)

        return re.sub(r'url\(\s*(["\']?)([^"\')]+)\1\s*\)', recurso, texto)

    # -- pasadas sobre el HTML ----------------------------------------------

    def con_apuntes(self, html):
        """Inyecta el lector de apuntes, y solo si la sesión los tiene escritos.
        El deck de trabajo no lo carga: es cosa del paquete, y lo abre un
        estudiante. Se busca al lado del tema, que es de donde cuelga."""
        if not re.search(r'<aside\b[^>]*\bclass="[^"]*\bapuntes\b', html):
            return html
        m = re.search(r'href="([^"]*)tema-centrogeo\.css"', html)
        if not m:
            return html
        p = self.resolver(m.group(1) + "apuntes.js", self.base)
        if p is None:
            return html
        self.anotar(p.name, p)
        # Sin su comentario de cabecera, que explica el guion de orador y el guion
        # corto: es lo mismo que se les quita a los del deck y del tema.
        lector = re.sub(r"/\*.*?\*/", "", p.read_text(encoding="utf-8"), flags=re.S).lstrip()
        bloque = "\n<script>\n" + lector + "\n</script>\n"
        pos = html.rfind("</body>")
        return html[:pos] + bloque + html[pos:] if pos >= 0 else html + bloque

    def sin_marcas(self, html):
        """El nivel de recorte dice qué láminas está dispuesto a saltarse quien
        da la clase. Es una nota de conducción, no contenido: no viaja al grupo."""
        return re.sub(r"\s+data-recorte=(\"[^\"]*\"|'[^']*')", "", html)

    def sin_comentarios(self, html):
        """Los comentarios del deck describen su andamiaje. Se quitan antes de
        incrustar el CSS y el JS, para no tocar lo que venga dentro de ellos.
        También los del CSS que el deck lleva en su propio <style>, que cuentan
        cosas como para qué sirve el guion corto."""
        html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
        return re.sub(r"(<style[^>]*>)(.*?)(</style>)",
                      lambda m: m.group(1) + re.sub(r"/\*.*?\*/", "", m.group(2), flags=re.S) +
                                m.group(3),
                      html, flags=re.S)

    def auditar(self, html):
        """Sobre el archivo ya armado, que es lo que se entrega: nada de lo que
        solo mira quien da la clase puede haber sobrevivido, y ninguna lámina
        puede estar sin escribir. Si algo queda, no se entrega un paquete a
        medias, se para.

        Las láminas por escribir son el hueco que deja la rejilla del anotador
        cuando se pide una lámina nueva: llevan data-pendiente y dentro la
        descripción de lo que hay que poner. Al grupo no le llega un encargo
        mío."""
        fugas = [q for pat, q in (
            (r'<aside\b[^>]*\bclass="[^"]*\bnotes\b', "el guion de orador"),
            (r'<aside\b[^>]*\bclass="[^"]*\bcorto\b', "el guion corto"),
            (r'<aside\b[^>]*\bclass="[^"]*\bdidactica\b', "la nota didáctica"),
            (r"\bdata-recorte=", "las marcas de recorte"),
            (r"\bdata-pendiente=", "láminas por escribir"),
            (r"\bdata-combinar", "láminas sin combinar"),
            (r"revisar\.js", "el anotador"),
            (r"apuntador\.js", "el apuntador"),
            # Dos patrones para el lector de estudio, y el segundo es el que
            # vale: incrustar_js() corre ANTES de la auditoría y sustituye el
            # <script src> por el código, así que a esta altura el nombre del
            # archivo ya no está escrito en ninguna parte. Lo que sí sobrevive es
            # una marca de su código, y la llave de localStorage no aparece en
            # nada más. Descubierto el 1 de octubre de 2026 rompiendo la limpieza
            # a propósito: la prueba lo cazó por un comentario del propio script
            # y no por su nombre. Los otros tres, el anotador, el apuntador y el
            # pincel, tienen el mismo agujero y está anotado como pendiente.
            (r"estudio\.js", "el lector de estudio"),
            (r"estudio:modo", "el lector de estudio"),
            (r"pincel\.js", "el pincel"),
        ) if re.search(pat, html)]
        if fugas:
            raise SystemExit("el paquete todavía lleva " + ", ".join(fugas) + ": no se entrega")
        return html

    def sin_pendientes(self, html):
        """Una lámina pedida en la rejilla y todavía sin escribir lleva
        data-pendiente. Mientras esté, no hay paquete: dentro no hay una lámina,
        hay el encargo de escribirla. Lo mismo con data-combinar, que marca dos
        o tres láminas que iban a ser una y todavía son dos o tres."""
        if re.search(r"\bdata-pendiente=", html):
            raise SystemExit("el deck todavía lleva láminas por escribir "
                             "(data-pendiente): no se empaqueta")
        if re.search(r"\bdata-combinar", html):
            raise SystemExit("el deck todavía lleva láminas por combinar "
                             "(data-combinar): no se empaqueta")
        return html

    def sin_guion(self, html):
        # Los tres bloques que no son del grupo: el guion largo, el corto y la
        # nota didáctica, con la que Alberto estudia el tema y decide cómo
        # explicarlo. Los tres se quedan en el deck de trabajo.
        html = re.sub(r'<aside\b[^>]*\bclass="[^"]*\b(?:notes|corto|didactica)\b[^"]*"[^>]*>.*?</aside>\s*',
                      "", html, flags=re.S | re.I)
        html = self.sin_script(html, r'plugin/notes\.js')

        def plugins(m):
            lista = [x.strip() for x in m.group(1).split(",")]
            lista = [x for x in lista if x and x != "RevealNotes"]
            return "plugins:[%s]" % ",".join(lista)

        return re.sub(r'plugins:\s*\[([^\]]*)\]', plugins, html)

    def sin_script(self, html, patron):
        return re.sub(r'[ \t]*<script[^>]*\bsrc="[^"]*%s"[^>]*>\s*</script>\n?' % patron,
                      "", html)

    def con_controles(self, html):
        html = re.sub(r'controls:\s*false', "controls:true", html)
        return re.sub(r'progress:\s*false', "progress:true", html)

    def registrar_medios(self, html):
        """Apunta los videos y audios, y marca los <video src> para el arranque."""
        def atributo(m):
            ref = m.group(2)
            p = self.resolver(ref, self.base)
            if p is None or p.suffix.lower() not in MEDIOS:
                return m.group(0)
            self.medios[ref] = p
            return m.group(0)

        html = re.sub(r'\b(data-video|data-background-video)="([^"]+)"', atributo, html)

        def etiqueta(m):
            def src(n):
                ref = n.group(1)
                p = self.resolver(ref, self.base)
                if p is None or p.suffix.lower() not in MEDIOS:
                    return n.group(0)
                self.medios[ref] = p
                return 'data-medio="%s"' % ref
            return re.sub(r'\bsrc="([^"]+)"', src, m.group(0))

        return re.sub(r'<(?:video|audio|source)\b[^>]*>', etiqueta, html)

    def incrustar_imagenes(self, html):
        def atributo(m):
            nombre, ref = m.group(1), m.group(2)
            p = self.resolver(ref, self.base)
            if p is None or p.suffix.lower() not in IMAGENES:
                return m.group(0)
            self.anotar(p.name, p)
            return '%s="%s"' % (nombre, self.datauri(p))
        return re.sub(r'\b(src|poster|data-background-image)="([^"]+)"', atributo, html)

    def incrustar_css(self, html):
        def enlace(m):
            etiqueta = m.group(0)
            if "stylesheet" not in etiqueta:
                return etiqueta
            ref = re.search(r'\bhref="([^"]+)"', etiqueta)
            p = self.resolver(ref.group(1), self.base) if ref else None
            if p is None:
                return etiqueta
            self.anotar("css " + p.name, p)
            return "<style>\n%s\n</style>" % self.css(p)
        return re.sub(r'<link\b[^>]*>', enlace, html)

    def incrustar_js(self, html):
        def script(m):
            ref = re.search(r'\bsrc="([^"]+)"', m.group(0))
            p = self.resolver(ref.group(1), self.base) if ref else None
            if p is None:
                return m.group(0)
            self.anotar(p.name, p)
            codigo = p.read_text(encoding="utf-8").replace("</script", "<\\/script")
            return "<script>\n%s\n</script>" % codigo
        return re.sub(r'<script\b[^>]*\bsrc="[^"]+"[^>]*>\s*</script>', script, html)

    def incrustar_medios(self, html):
        if not self.medios:
            return html
        entradas = []
        for ref, p in sorted(self.medios.items()):
            self.anotar(p.name, p)
            entradas.append('  "%s": ["%s", "%s"]' % (ref, self.tipo(p), self.base64(p)))
        bloque = PREAMBULO % ("{\n" + ",\n".join(entradas) + "\n}")
        # Despues de la última lámina y antes del primer <script> que venga tras ella:
        # así los atributos ya existen y todavía no ha arrancado reveal. Un <script> en
        # el <head> no cuenta, por eso se busca a partir del cierre de las láminas.
        fin = html.rfind("</section>")
        pos = html.find("<script", fin if fin >= 0 else 0)
        if pos < 0:
            pos = html.rfind("</body>")
        if pos < 0:
            raise SystemExit("el deck no tiene dónde insertar los medios")
        return html[:pos] + bloque + html[pos:]

    def viewport(self, html):
        if re.search(r'name="viewport"', html):
            return html
        return html.replace('<meta charset="utf-8">',
                            '<meta charset="utf-8">\n'
                            '<meta name="viewport" content="width=device-width,initial-scale=1">',
                            1)

    # -- orquestación --------------------------------------------------------

    def construir(self):
        html = self.deck.read_text(encoding="utf-8")
        self.partes.append(("index.html", len(html.encode("utf-8"))))
        if not self.con_guion:
            html = self.sin_comentarios(html)
            html = self.sin_guion(html)
            html = self.sin_marcas(html)
        html = self.con_apuntes(html)
        if not self.con_apuntador:
            html = self.sin_script(html, r'apuntador\.js')
        html = self.sin_script(html, r'estudio\.js')
        html = self.sin_script(html, r'revisar\.js')
        html = self.sin_script(html, r'pincel\.js')
        if self.controles:
            html = self.con_controles(html)
        html = self.registrar_medios(html)
        html = self.incrustar_imagenes(html)
        html = self.incrustar_css(html)
        html = self.incrustar_js(html)
        html = self.incrustar_medios(html)
        html = self.viewport(html)
        # La variante con guion es mía y conserva lo que el grupo no ve, así que
        # se salta la auditoría entera. Lo que no se salta es la lámina sin
        # escribir: un deck a medias no se empaqueta ni para mí.
        return self.sin_pendientes(html) if self.con_guion else self.auditar(html)


def main():
    ap = argparse.ArgumentParser(description="Empaqueta una sesión en un solo HTML.")
    ap.add_argument("deck", nargs="?", default="index.html", help="sesiones/SNN-.../index.html")
    ap.add_argument("-o", "--salida", help="por omisión salidas/<carpeta de la sesión>.html")
    ap.add_argument("--con-guion", action="store_true",
                    help="conserva el guion de orador y la tecla S")
    ap.add_argument("--sin-controles", action="store_true",
                    help="no enciende controles ni barra de progreso")
    ap.add_argument("--con-apuntador", action="store_true",
                    help="conserva el apuntador, tecla T, e implica --con-guion. "
                         "Para presentar desde el paquete, sin servidor")
    args = ap.parse_args()

    deck = pathlib.Path(args.deck).resolve()
    if not deck.is_file():
        print("no existe: %s" % deck, file=sys.stderr)
        return 1

    raiz = pathlib.Path(__file__).resolve().parent.parent
    salida = pathlib.Path(args.salida).resolve() if args.salida else \
        raiz / "salidas" / (deck.parent.name + ".html")
    salida.parent.mkdir(parents=True, exist_ok=True)

    emp = Empaquetador(deck, con_guion=args.con_guion,
                       controles=not args.sin_controles,
                       con_apuntador=args.con_apuntador)
    html = emp.construir()
    salida.write_text(html, encoding="utf-8")

    peso = salida.stat().st_size
    print("%s, %.1f MB" % (os.path.relpath(salida, raiz), peso / 1e6))
    agrupado = {}
    for etiqueta, tam in emp.partes:
        agrupado[etiqueta] = agrupado.get(etiqueta, 0) + tam
    for etiqueta, tam in sorted(agrupado.items(), key=lambda x: -x[1])[:8]:
        print("   %-42s %7.1f KB" % (etiqueta, tam / 1e3))
    if emp.faltantes:
        print("FALTAN, quedaron sin incrustar:", file=sys.stderr)
        for f in sorted(set(emp.faltantes)):
            print("   " + f, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
