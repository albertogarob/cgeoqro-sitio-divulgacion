#!/usr/bin/env python3
"""Prueba del paquete que se entrega al grupo: qué lleva y qué no.

    python3 tools/prueba-paquete.py [sesiones/SNN-.../index.html]

Empaqueta una copia del deck con las cuatro clases de nota puestas a mano, el
guion de orador, el guion corto, la nota didáctica y los apuntes de estudio, más
una marca de recorte y un comentario. Después comprueba dos cosas sobre el
archivo entregado:

1. Que no lleve **nada de lo que solo mira quien da la clase**: ni guion, ni guion
   corto, ni nota didáctica, ni data-recorte, ni el anotador, ni el apuntador, ni
   el lector de estudio, ni el pincel, ni comentarios. Y que
   la variante --con-guion, la de archivo propio, sí los conserve.

2. Que el **lector de apuntes** funcione dentro del archivo, en Chrome headless y
   sobre file://, que es como lo abre un estudiante: que aparezca el botón, que el
   panel muestre el apunte de la lámina en curso, que la lámina se encoja en vez
   de taparse, y que los apuntes completos listen todas las entradas.

Trabaja sobre una sesión de mentira, sesiones/S99-prueba-paquete, que crea y borra.
Por omisión parte de la S01, que no tiene video y se empaqueta en un segundo.
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
RUTA = sys.argv[1] if len(sys.argv) > 1 else "sesiones/S01-presentacion-del-curso-y-evaluacion/index.html"
PRUEBA = RAIZ / "sesiones" / "S99-prueba-paquete"

R = []


def ok(nombre, cond, extra=""):
    R.append(("OK   " if cond else "FALLA") + "  " + nombre + ("" if cond else "  [%s]" % extra))


SEMILLA = """<aside class="notes"><p>Guion de orador que no debe salir.</p></aside>\
<aside class="corto"><p>Guion corto que tampoco debe salir.</p></aside>\
<aside class="didactica"><p>Nota didactica que tampoco debe salir.</p></aside>\
<aside class="apuntes"><p>Apunte de estudio numero %d, este si viaja.\
<cite data-ref="prueba"></cite></p></aside>"""

SONDA = """
<script>
const R = [];
setTimeout(() => {
  location.hash = "#/1";
  setTimeout(() => {
    const b = document.querySelector(".ap-boton");
    R.push("arranca=" + document.body.classList.contains("ap-abierto"));
    // sin abrir los apuntes completos, imprimir tiene que darlos, no hojas
    // en blanco: el contenido se escribe al cargar y se refresca antes de imprimir
    R.push("imprimible=" + (document.querySelectorAll(".ap-texto h2").length > 0));
    R.push("botonOculto=" + (!!b && b.hidden));
    const cerrar = document.querySelector('[data-ap="cerrar"]');
    if (cerrar) cerrar.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    R.push("cierra=" + (!document.body.classList.contains("ap-abierto") && !b.hidden));
    if (b) b.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    setTimeout(() => {
      R.push("panel=" + document.body.classList.contains("ap-abierto"));
      const c = document.querySelector(".ap-cuerpo");
      R.push("texto=" + (c ? c.textContent.trim().slice(0, 40) : "sin panel"));
      const cp = c ? c.getBoundingClientRect() : { width: 0, height: 0 };
      R.push("panelVisible=" + (cp.width > 100 && cp.height > 50));
      R.push("ancho=" + Math.round(document.querySelector(".reveal").getBoundingClientRect().width));
      const t = document.querySelector('[data-ap="todos"]');
      if (t) t.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      setTimeout(() => {
        R.push("completo=" + document.body.classList.contains("ap-completo"));
        // .ap-texto y no .ap-doc: los clones de las láminas traen sus propios h2
        R.push("entradas=" + document.querySelectorAll(".ap-texto h2").length);
        // Que estén en el DOM no basta: el fallo que esto vigila era una clase de
        // estado en el body que le caía encima al propio body y lo escondía todo.
        const doc = document.querySelector(".ap-doc");
        const cd = doc ? doc.getBoundingClientRect() : { width: 0, height: 0 };
        R.push("completoVisible=" + (cd.width > 200 && cd.height > 100));
        // la miniatura es un clon de la lámina: tiene que traerla y tiene que verse
        const m = document.querySelector(".ap-mini");
        const cm = m && m.querySelector(".reveal")
          ? m.querySelector(".reveal").getBoundingClientRect() : { width: 0, height: 0 };
        R.push("miniaturas=" + document.querySelectorAll(".ap-mini").length);
        R.push("miniaturaVisible=" + (cm.width > 100 && cm.height > 50));
        R.push("miniaturaConLamina=" + (!!m && !!m.querySelector(".slides > section")));
        const f = document.querySelector(".ap-todos .ap-ficha");
        R.push("ficha=" + (!!f && /Un libro de prueba/.test(f.textContent) &&
                           /Quien firma la sesion/.test(f.textContent)));
        // la marca de cita lleva a su referencia y la deja resaltada
        const marca = document.querySelector(".ap-doc cite[data-ref]");
        R.push("marca=" + (marca ? marca.textContent : "ninguna"));
        if (marca) marca.dispatchEvent(new MouseEvent("click", { bubbles: true }));
        const li = document.querySelector(".ap-ficha li.ap-resalta");
        R.push("resalta=" + (li ? li.dataset.refId : "ninguna"));
        R.push("sinIdRepetido=" + (document.querySelectorAll('[id="ref-prueba"]').length === 1));
        R.push("bodyVisible=" + (getComputedStyle(document.body).display !== "none" &&
                                 document.body.getBoundingClientRect().height > 100));
        document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
        setTimeout(() => {
          R.push("escape=" + !document.body.classList.contains("ap-completo"));
          // la tecla T alterna entre las láminas y los apuntes completos
          const teclaT = () => document.dispatchEvent(
            new KeyboardEvent("keydown", { key: "t", bubbles: true, cancelable: true }));
          teclaT();
          R.push("tAbre=" + document.body.classList.contains("ap-completo"));
          teclaT();
          R.push("tCierra=" + !document.body.classList.contains("ap-completo"));
          const d = document.createElement("div");
          d.id = "diag"; d.textContent = R.join(" ;; ");
          document.body.appendChild(d);
        }, 250);
      }, 350);
    }, 350);
  }, 600);
}, 1000);
</script>
"""


def sembrar(origen):
    """Copia el deck con las cuatro notas y una marca de recorte en cada lámina.

    La ficha del deck de origen se va con las notas, y sus marcas de cita con
    ella: la prueba pone su propia ficha, con una sola referencia, y si la del
    deck sobrevive quedan dos. El lector se queda con la primera y `citas.py`
    numera contra esa, así que la marca sembrada sale rota y se cae media
    prueba. Se notaba solo desde que hay sesiones con ficha."""
    s = origen.read_text(encoding="utf-8")
    # Los dos patrones toleran atributos de más y comillas simples: una ficha
    # escrita <aside class="ficha" id="cierre"> sobrevivía a la limpieza y traía
    # de vuelta el fallo de las dos fichas sin decir nada.
    s = re.sub(r"""<aside[^>]*\bclass=["'][^"']*\b(?:notes|corto|didactica|apuntes|ficha)\b[^"']*["'][^>]*>"""
               r".*?</aside>", "", s, flags=re.S | re.I)
    # El cuerpo va acotado a `[^<]*`: con `.*?` una marca a la que le falte el
    # cierre se traga todo hasta la siguiente y borra contenido en silencio.
    s = re.sub(r"""<cite[^>]*\bdata-ref=["'][^"']*["'][^>]*>[^<]*</cite>""", "", s, flags=re.I)
    n = [0]

    def repl(m):
        n[0] += 1
        attrs, cuerpo = m.group(1), m.group(2)
        if "data-recorte" not in attrs:
            attrs += ' data-recorte="1"'
        return "<section" + attrs + ">" + cuerpo + (SEMILLA % n[0]) + "</section>"

    s = re.sub(r"<section\b([^>]*)>(.*?)</section>", repl, s, flags=re.S)
    # la ficha de la sesión, que va en la última lámina y cierra los apuntes
    i = s.rfind("</section>")
    s = s[:i] + '<aside class="ficha"><h3>Bibliografia</h3><ol>' \
        '<li id="ref-prueba">Un libro de prueba.</li></ol>' \
        "<h3>Creditos</h3><p>Quien firma la sesion.</p></aside>" + s[i:]
    s = s.replace("<body>", "<body>\n<!-- comentario que no debe viajar -->", 1)
    # El lector de estudio, si el deck de origen todavía no lo carga. Sin esto la
    # prueba de que empaquetar.py lo quita pasaría por casualidad: los decks
    # anteriores al 1 de octubre de 2026 no lo tienen, así que no habría nada
    # que quitar y la aserción saldría en verde con la limpieza desenchufada.
    if "estudio.js" not in s:
        ruta = re.search(r'src="([^"]*)apuntador\.js"', s)
        base = ruta.group(1) if ruta else "../../plantillas/tema-centrogeo/"
        s = s.replace("</body>", '<script src="%sestudio.js"></script>\n</body>'
                      % base, 1)
    PRUEBA.mkdir(parents=True, exist_ok=True)
    (PRUEBA / "index.html").write_text(s, encoding="utf-8")
    llevar_assets(origen, s)
    return n[0]


def llevar_assets(origen, sembrado):
    """Copia al directorio de prueba los archivos que el deck referencia por ruta
    relativa y que cuelgan de su propia carpeta, como `img/portada.webp`.

    Sin esto, `empaquetar.py` corre desde `S99-prueba-paquete/`, no encuentra la
    imagen y avisa con FALTAN, y la prueba falla aunque el paquete de verdad esté
    bien. No hacía falta hasta que un deck trajo su primera imagen propia. Las
    rutas que suben con `../` son el tema y reveal, que ya se resuelven solas."""
    refs = re.findall(r'(?:src|poster|data-background-image|data-video)="([^"]+)"',
                      sembrado)
    for ref in set(refs):
        if ref.startswith(("http:", "https:", "data:", "/", "..")):
            continue
        fuente = (origen.parent / ref).resolve()
        if not fuente.is_file():
            continue
        destino = PRUEBA / ref
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fuente, destino)


def numerar():
    """citas.py pone el número de cada marca a partir de la bibliografía."""
    return subprocess.run([sys.executable, str(RAIZ / "tools" / "citas.py"),
                           str(PRUEBA / "index.html")],
                          capture_output=True, text=True, timeout=120)


def empaquetar(destino, con_guion=False):
    orden = [sys.executable, str(RAIZ / "tools" / "empaquetar.py"),
             str(PRUEBA / "index.html"), "-o", str(destino)]
    if con_guion:
        orden.append("--con-guion")
    r = subprocess.run(orden, capture_output=True, text=True, timeout=300)
    return r.returncode, (r.stdout + r.stderr)


TABLA = re.compile(r"^\s*\S.*?\s\d+(?:\.\d+)?\s(?:KB|MB|B)$")


def fallo(log):
    """El log de empaquetado termina en la tabla de tamaños de los assets, así que
    cortarlo por la cola daba diagnósticos como "[KB", inservibles justo cuando
    hacen falta. Se tira la tabla y se deja lo que de verdad dice algo. Buscar
    palabras como "error" no bastaba: `empaquetar.py` avisa con "FALTAN"."""
    utiles = [x.rstrip() for x in log.splitlines()
              if x.strip() and not TABLA.match(x.rstrip())]
    return " | ".join(utiles[-4:])[-400:] if utiles else log.strip()[-200:]


def main():
    origen = pathlib.Path(RUTA)
    if not origen.exists():
        print("no existe " + str(origen))
        return 1
    if PRUEBA.exists():
        shutil.rmtree(PRUEBA)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="paq-"))
    try:
        laminas = sembrar(origen)
        r = numerar()
        sembrado = (PRUEBA / "index.html").read_text(encoding="utf-8")
        ok("citas.py numera las marcas contra la bibliografía",
           r.returncode == 0 and '<cite data-ref="prueba">1</cite>' in sembrado,
           r.stdout.strip()[-120:])
        salida = tmp / "grupo.html"
        codigo, log = empaquetar(salida)
        # El diagnóstico iba cortado a los últimos 200 caracteres, que son la
        # tabla de tamaños de los assets, no el error: el fallo salía como "[KB".
        ok("el paquete se construye", codigo == 0 and salida.exists(), fallo(log))
        if not salida.exists():
            # Sin esto el abandono era MUDO: los resultados se imprimen al final
            # de main, después del finally, así que un return aquí se llevaba por
            # delante el diagnóstico del fallo y la prueba salía con código 1 y la
            # salida en blanco. Se descubrió el 1 de octubre de 2026 rompiendo
            # empaquetar.py a propósito para ver si la prueba lo cazaba: lo cazaba,
            # pero no lo decía.
            print("\n".join(R))
            return 1
        s = salida.read_text(encoding="utf-8", errors="ignore")

        ok("sin guion de orador", "Guion de orador que no debe salir" not in s)
        ok("sin guion corto", "Guion corto que tampoco debe salir" not in s)
        ok("sin la nota didactica", "Nota didactica que tampoco debe salir" not in s)
        ok("sin marcas de recorte", "data-recorte" not in s)
        ok("sin el anotador, el apuntador, el lector de estudio ni el pincel",
           "revisar.js" not in s and "apuntador.js" not in s and
           "estudio.js" not in s and "pincel.js" not in s)
        # Fuera de los <script>: el código de MathJax lleva un regex que
        # contiene la secuencia "<!--" y daba un falso positivo.
        sin_js = re.sub(r"<script\b[^>]*>.*?</script>", "", s, flags=re.S)
        ok("sin comentarios del deck", "<!--" not in sin_js)
        ok("con los apuntes de estudio",
           s.count('<aside class="apuntes">') == laminas,
           "%d de %d" % (s.count('<aside class="apuntes">'), laminas))
        ok("y con el lector dentro", ".ap-boton" in s and "ap-todos" in s)

        # el archivo propio sí conserva lo que el del grupo no lleva
        propio = tmp / "propio.html"
        codigo, log = empaquetar(propio, con_guion=True)
        p = propio.read_text(encoding="utf-8", errors="ignore") if propio.exists() else ""
        ok("con --con-guion el archivo propio conserva el guion",
           codigo == 0 and "Guion de orador que no debe salir" in p, fallo(log))
        # La nota didáctica es mía, así que en MI archivo se queda. Es la cara
        # inversa de la prueba de arriba: que la limpieza no se pase de celo.
        ok("y con --con-guion conserva la nota didactica",
           "Nota didactica que tampoco debe salir" in p)

        # La auditoría es la red por si un día falla la limpieza, así que se prueba
        # directo: lo que la limpieza ya quita nunca llegaría a dispararla.
        import importlib.util
        spec = importlib.util.spec_from_file_location("empaquetar", RAIZ / "tools" / "empaquetar.py")
        emp_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(emp_mod)
        emp = emp_mod.Empaquetador(PRUEBA / "index.html")
        fugas = ['<aside class="notes"><p>x</p></aside>',
                 '<aside class="corto"><p>x</p></aside>',
                 '<aside class="didactica"><p>x</p></aside>',
                 "<section data-recorte='1'></section>",
                 '<script src="revisar.js"></script>',
                 '<script src="apuntador.js"></script>',
                 '<script src="estudio.js"></script>',
                 '<script src="pincel.js"></script>']
        paradas = 0
        for f in fugas:
            try:
                emp.auditar("<html>" + f + "</html>")
            except SystemExit:
                paradas += 1
        ok("la auditoría para el paquete si algo se cuela",
           paradas == len(fugas), "%d de %d" % (paradas, len(fugas)))
        ok("y deja pasar un paquete limpio, con sus apuntes",
           emp.auditar('<html><aside class="apuntes"><p>x</p></aside></html>') is not None)

        # el lector, dentro del propio archivo entregado y sobre file://
        sonda = tmp / "sonda.html"
        sonda.write_text(s.replace("</body>", SONDA + "</body>", 1), encoding="utf-8")
        perfil = tempfile.mkdtemp(prefix="paq-perfil-")
        try:
            r = subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
                                "--allow-file-access-from-files", "--user-data-dir=" + perfil,
                                "--window-size=1280,720", "--virtual-time-budget=20000",
                                "--dump-dom", "file://" + str(sonda)],
                               capture_output=True, text=True, timeout=300)
            d = re.search(r'<div id="diag">(.*?)</div>', r.stdout.replace("\n", " "), re.S)
            campos = dict(x.strip().split("=", 1) for x in d.group(1).split(";;")) if d else {}
        finally:
            shutil.rmtree(perfil, ignore_errors=True)

        # La impresión se comprueba imprimiendo: es donde se coló que la página
        # saliera del tamaño de una lámina y una nota por hoja.
        pdf = tmp / "apuntes.pdf"
        perfil2 = tempfile.mkdtemp(prefix="paq-pdf-")
        try:
            subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
                            "--allow-file-access-from-files", "--user-data-dir=" + perfil2,
                            "--virtual-time-budget=20000", "--no-pdf-header-footer",
                            "--print-to-pdf=" + str(pdf), "file://" + str(salida)],
                           capture_output=True, text=True, timeout=300)
        finally:
            shutil.rmtree(perfil2, ignore_errors=True)
        crudo = pdf.read_bytes() if pdf.exists() else b""
        carta = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+612(\.\d+)?\s+792(\.\d+)?\s*\]", crudo)
        cuentas = [int(x) for x in re.findall(rb"/Count\s+(\d+)", crudo)]
        paginas = max(cuentas) if cuentas else 0
        ok("los apuntes se imprimen en tamaño carta", bool(carta), crudo[:0] or str(len(crudo)))
        ok("y con varias notas por página, no una por hoja",
           0 < paginas < laminas, "%d páginas para %d láminas" % (paginas, laminas))

        ok("el panel arranca abierto", campos.get("arranca") == "true", campos)
        ok("los apuntes están escritos desde el arranque, para poder imprimirlos",
           campos.get("imprimible") == "true", campos)
        ok("y el botón se esconde mientras lo está", campos.get("botonOculto") == "true", campos)
        ok("Cerrar lo cierra y devuelve el botón", campos.get("cierra") == "true", campos)
        ok("y el botón lo vuelve a abrir", campos.get("panel") == "true", campos)
        ok("con el apunte de la lámina en curso",
           campos.get("texto", "").startswith("Apunte de estudio"), campos.get("texto"))
        ok("y el panel se ve de verdad, no solo en el DOM",
           campos.get("panelVisible") == "true", campos)
        ok("y la lámina se encoge en vez de taparse",
           campos.get("ancho", "0").isdigit() and int(campos["ancho"]) < 1000, campos.get("ancho"))
        ok("los apuntes completos se abren", campos.get("completo") == "true", campos)
        ok("con una entrada por lámina",
           campos.get("entradas") == str(laminas), campos.get("entradas"))
        ok("los apuntes se dibujan, no solo existen",
           campos.get("completoVisible") == "true", campos)
        ok("cada entrada lleva su miniatura",
           campos.get("miniaturas") == str(laminas), campos.get("miniaturas"))
        ok("la miniatura trae la lámina clonada",
           campos.get("miniaturaConLamina") == "true", campos)
        ok("y se dibuja con su tamaño, no recortada a cero",
           campos.get("miniaturaVisible") == "true", campos)
        ok("y abrirlo no esconde la página entera",
           campos.get("bodyVisible") == "true", campos)
        ok("y Escape lo cierra", campos.get("escape") == "true", campos)
        ok("la tecla T abre los apuntes completos", campos.get("tAbre") == "true", campos)
        ok("y la misma tecla vuelve a las láminas", campos.get("tCierra") == "true", campos)
        ok("los apuntes cierran con la ficha de la sesión",
           campos.get("ficha") == "true", campos)
        ok("las marcas de cita llegan a los apuntes con su número",
           campos.get("marca") == "1", campos.get("marca"))
        ok("y al pulsarlas resaltan su referencia",
           campos.get("resalta") == "prueba", campos.get("resalta"))
        ok("sin duplicar el identificador de la referencia",
           campos.get("sinIdRepetido") == "true", campos)
        ok("y la ficha viaja en el paquete", 'class="ficha"' in s, "no está en el archivo")
    finally:
        shutil.rmtree(PRUEBA, ignore_errors=True)
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n".join(R))
    malas = [x for x in R if x.startswith("FALLA")]
    print("%d de %d fallan" % (len(malas), len(R)) if malas
          else "las %d pruebas del paquete pasan" % len(R))
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main())
