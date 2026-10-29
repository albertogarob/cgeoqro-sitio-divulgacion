#!/usr/bin/env python3
"""Extrae los apuntes de estudio de un deck a Markdown, y dice cuáles faltan.

    python3 tools/apuntes.py sesiones/S02-.../index.html

Los apuntes son el tercer bloque de notas de una lámina, el `<aside class="apuntes">`,
y el único de los tres que viaja al paquete del grupo. El guion de orador y el guion
corto se quedan en el deck fuente. Están escritos para leerse después de clase, no
para decirse.

Escribe `apuntes.md` junto al deck, con una entrada por lámina: su número, su
título, lo que se ve en pantalla y el apunte. Con eso se sostienen solos,
sin abrir las diapositivas, que es lo que hace falta para leerlo en el teléfono.
El deck sigue siendo la fuente única: `apuntes.md` se genera, no se edita.

Al final lista las láminas que se quedaron sin apunte. Esa lista tiene que salir
vacía. Quedan fuera de la cuenta la portada, el cierre y los separadores de
bloque, que entre los apuntes hacen de encabezado y no necesitan apunte.

Las marcas de cita, que `tools/citas.py` numera en el HTML, salen aquí como `[N]`,
y la bibliografía sale numerada para que los números cuadren.

Los apuntes cierran con la **ficha de la sesión**, que el deck lleva en un
`<aside class="ficha">` dentro de la lámina de cierre: su bibliografía y sus
créditos. Es obligatoria en todas las sesiones, así que si falta se avisa.
"""
import html
import pathlib
import re
import sys

EXENTAS = re.compile(r"\b(portada|cierre|seccion)\b")


def citas(s):
    """La marca de cita se vuelve [N], que es como se lee en un texto plano."""
    return re.sub(r'<cite\s+data-ref="[^"]*"\s*>(\d*)</cite>',
                  lambda m: " [%s]" % m.group(1) if m.group(1) else "", s)


def limpiar(s):
    """Texto plano. Al quitar las etiquetas queda un espacio de sobra antes de la
    puntuación, del tipo "Nature , 1986": se cierra aquí, que este texto se lee."""
    s = citas(s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", html.unescape(s)).strip()
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    return re.sub(r"\s+\[(\d+)\]", r" [\1]", s)


def parrafos(bloque):
    """Un renglón por párrafo, que es como se leen unos apuntes."""
    ps = re.findall(r"<p[^>]*>(.*?)</p>", bloque, re.S)
    return [limpiar(x) for x in ps] if ps else [limpiar(bloque)]


def _sin_comentarios(s):
    return re.sub(r"<!--.*?-->", "", s, flags=re.S)


def ficha_md(bloque):
    """La ficha es HTML sencillo: encabezados, listas y párrafos. Se pasa a
    Markdown a mano, que es más corto que traer un convertidor."""
    # los enlaces se conservan como enlaces de Markdown, no se aplastan a texto
    bloque = re.sub(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r"[\2](\1)", bloque, flags=re.S)
    out = []
    for m in re.finditer(r"<(h3|ul|ol|p)\b[^>]*>(.*?)</\1>", bloque, re.S):
        etiqueta, dentro = m.group(1), m.group(2)
        if etiqueta == "h3":
            out += ["## " + limpiar(dentro), ""]
        elif etiqueta in ("ul", "ol"):
            # la bibliografía va numerada, para que los [N] de los apuntes cuadren
            puntos = re.findall(r"<li[^>]*>(.*?)</li>", dentro, re.S)
            if etiqueta == "ol":
                out += ["%d. %s" % (i, limpiar(x)) for i, x in enumerate(puntos, 1)]
            else:
                out += ["- " + limpiar(x) for x in puntos]
            out.append("")
        else:
            out += [limpiar(dentro), ""]
    return out


def main(ruta):
    p = pathlib.Path(ruta)
    src = _sin_comentarios(p.read_text(encoding="utf-8"))
    t = re.search(r"<title>(.*?)</title>", src, re.S)
    titulo = limpiar(t.group(1)) if t else p.parent.name

    secciones = re.findall(r"<section\b([^>]*)>(.*?)</section>", src, re.S)
    out = ["# Apuntes de %s" % titulo, "",
           "Una entrada por lámina, para leer después de clase. "
           "Se generan del propio deck con `tools/apuntes.py`.", ""]
    con, faltan = 0, []
    for i, (attrs, cuerpo) in enumerate(secciones, 1):
        clase = re.search(r'class="([^"]+)"', attrs)
        clase = clase.group(1) if clase else ""
        h = re.search(r"<h2[^>]*>(.*?)</h2>", cuerpo, re.S) or \
            re.search(r'class="(?:titulo|gracias)"[^>]*>(.*?)</div>', cuerpo, re.S)
        encabezado = limpiar(h.group(1)) if h else ""
        ap = re.search(r'<aside class="apuntes">(.*?)</aside>', cuerpo, re.S)

        if not ap:
            if EXENTAS.search(clase):
                if "seccion" in clase and encabezado:
                    out += ["## " + encabezado, ""]
            else:
                faltan.append(i)
            continue

        con += 1
        out.append("### %d. %s" % (i, encabezado or "(sin título)"))
        out.append("")
        puntos = re.findall(r"<li>(.*?)</li>", cuerpo, re.S)
        if puntos:
            # Un <aside> dentro de una viñeta es la glosa que el deck enseña al
            # pasar el ratón, y no se proyecta. Sin quitarlo, su contenido se
            # pega a la prosa y "En pantalla" dice cosas que en pantalla no
            # están. Mismo caso que en tools/guion.py.
            puntos = [re.sub(r"<aside\b.*?</aside>", "", x, flags=re.S) for x in puntos]
            out.append("*En pantalla: " + "; ".join(limpiar(x) for x in puntos) + "*")
            out.append("")
        out += [x for parrafo in parrafos(ap.group(1)) for x in (parrafo, "")]

    ficha = re.search(r'<aside class="ficha">(.*?)</aside>', src, re.S)
    if ficha:
        out += ficha_md(ficha.group(1))
    p.with_name("apuntes.md").write_text("\n".join(out), encoding="utf-8")
    print("apuntes.md: %d de %d láminas con apunte" % (con, len(secciones)))
    if not ficha:
        print("   FALTA la ficha de la sesión: bibliografía y créditos, "
              'en un <aside class="ficha"> de la lámina de cierre')
    if faltan:
        cuales = ", ".join(str(x) for x in faltan[:24]) + (", ..." if len(faltan) > 24 else "")
        print("   sin apunte: %d lámina%s (%s)"
              % (len(faltan), "" if len(faltan) == 1 else "s", cuales))
        return 1
    # "No falta ninguna" se leía como "todas las láminas llevan apunte", y no es
    # eso: las exentas por su clase no cuentan. Decir cuántas son evita que una
    # lámina de contenido marcada por error como separador pase inadvertida.
    exentas = len(secciones) - con
    print("   no falta ninguna, sin contar %d exenta%s por su clase "
          "(portada, cierre y separadores)"
          % (exentas, "" if exentas == 1 else "s"))
    return 0 if ficha else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "index.html"))
