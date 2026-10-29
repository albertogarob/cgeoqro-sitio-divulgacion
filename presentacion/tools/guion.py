#!/usr/bin/env python3
"""Extrae el guion de orador de un deck reveal.js a Markdown.

    python3 tools/guion.py sesiones/S01-.../index.html

Lee las <aside class="notes"> y los títulos, y escribe guion.md junto al deck.
Así el guion nunca se desincroniza de las diapositivas: hay una sola fuente.

Recoge también el nivel de recorte de cada lámina, en data-recorte, y su guion
corto, en <aside class="corto">, que es lo que se dice de ella cuando la sesión
va tarde. Los dos salen marcados debajo del guion largo.
"""
import re, sys, html, pathlib

def limpiar(s):
    # La marca de cita se vuelve [N], que es como se lee en texto plano y como
    # la compone el deck desde el 29 de septiembre de 2026. Sin esto, quitar las
    # etiquetas dejaba el número pegado a la palabra anterior y se leía como
    # parte del nombre: Alberto leyó "ACT6" y entendió que el sistema se llamaba
    # así. Correr guion.py DESPUÉS de citas.py, o los números salen vacíos.
    s = re.sub(r'<cite\s+data-ref="[^"]*"\s*>(\d*)</cite>',
               lambda m: " [%s]" % m.group(1) if m.group(1) else "", s)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()

def _sin_comentarios(s):
    """Enmascara los comentarios HTML para que los regex no los confundan
    con contenido. Devuelve el texto enmascarado y una función que restaura."""
    guardados = []
    def guarda(m):
        guardados.append(m.group(0))
        return "\x00COMENTARIO%d\x00" % (len(guardados) - 1)
    limpio = re.sub(r"<!--.*?-->", guarda, s, flags=re.S)
    def restaura(t):
        for i, g in enumerate(guardados):
            t = t.replace("\x00COMENTARIO%d\x00" % i, g)
        return t
    return limpio, restaura

def main(ruta):
    p = pathlib.Path(ruta)
    src, _ = _sin_comentarios(p.read_text(encoding="utf-8"))
    titulo = limpiar(re.search(r"<title>(.*?)</title>", src, re.S).group(1))
    secciones = re.findall(r"<section\b[^>]*>(.*?)</section>", src, re.S)
    clases = re.findall(r"<section\b([^>]*)>", src)

    out = [f"# Guion de {titulo}", ""]
    con, sin = 0, []
    for i, (cuerpo, attrs) in enumerate(zip(secciones, clases), 1):
        m = re.search(r'class="([^"]+)"', attrs)
        clase = m.group(1) if m else ""
        t = re.search(r"<h2[^>]*>(.*?)</h2>", cuerpo, re.S)
        if not t:
            t = re.search(r'class="(?:titulo|gracias)"[^>]*>(.*?)</div>', cuerpo, re.S)
        encabezado = limpiar(t.group(1)) if t else f"({clase})"
        nota = re.search(r'<aside class="notes">(.*?)</aside>', cuerpo, re.S)
        corto = re.search(r'<aside class="corto">(.*?)</aside>', cuerpo, re.S)
        niv = re.search(r'data-recorte="([12])"', attrs)
        out.append(f"## {i}. {encabezado}")
        out.append("")
        puntos = re.findall(r"<li>(.*?)</li>", cuerpo, re.S)
        if puntos:
            # Un <aside> dentro de una viñeta no se proyecta: es una glosa que
            # el deck enseña al pasar el ratón. Sin quitarlo, su texto se pega
            # a la prosa y "En pantalla" dice cosas que en pantalla no están.
            puntos = [re.sub(r"<aside\b.*?</aside>", "", x, flags=re.S) for x in puntos]
            out.append("En pantalla: " + "; ".join(limpiar(x) for x in puntos[:8]))
            out.append("")
        if nota:
            out.append(limpiar(nota.group(1)))
            con += 1
        else:
            out.append("_(sin guion)_")
            sin.append(i)
        out.append("")
        if niv:
            cuanto = ("se pierde sin que nadie se entere"
                      if niv.group(1) == "1" else "se pierde, pero hay que decirlo")
            out.append(f"**Recorte {niv.group(1)}**: {cuanto}.")
            out.append("")
        if corto:
            out.append("**Guion corto:** " + limpiar(corto.group(1)))
            out.append("")
    p.with_name("guion.md").write_text("\n".join(out), encoding="utf-8")
    print(f"guion.md: {len(secciones)} diapositivas, {con} con guion"
          + (f", sin guion: {sin}" if sin else ""))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "index.html")
