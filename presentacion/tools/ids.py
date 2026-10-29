#!/usr/bin/env python3
"""Asigna un id estable a cada diapositiva de un deck, derivado de su título.

    python3 tools/ids.py sesiones/S01-.../index.html

Los ids son el ancla de la retroalimentación: sobreviven a que se inserten o
reordenen láminas, cosa que los números no. Las diapositivas que ya tienen id
no se renombran, para no romper notas previas.

Cada sección recibe además un `data-sid` con el mismo valor. Hace falta porque
reveal.js, con hash activo, le quita el atributo `id` a la lámina visible para
que el navegador no salte por anclaje, y se lo devuelve al salir. El anotador
lee `data-sid`, que reveal no toca.
"""
import re, sys, pathlib, unicodedata

def slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return re.sub(r"-+", "-", t)[:34].strip("-")

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
    p = pathlib.Path(ruta); s, restaura = _sin_comentarios(p.read_text(encoding="utf-8"))
    usados = set(re.findall(r'<section id="([^"]+)"', s))
    partes, prev, nuevos = [], 0, 0
    for b in re.finditer(r"<section\b([^>]*)>(.*?)</section>", s, re.S):
        attrs, cuerpo = b.group(1), b.group(2)
        actual = re.search(r'id="([^"]+)"', attrs)
        if actual:
            idd = actual.group(1)
        else:
            t = re.search(r"<h2[^>]*>(.*?)</h2>", cuerpo, re.S) or \
                re.search(r'class="(?:titulo|gracias)"[^>]*>(.*?)</div>', cuerpo, re.S)
            base = slug(re.sub(r"<[^>]+>", "", t.group(1)) if t else "diapositiva") or "diapositiva"
            idd, n = base, 2
            while idd in usados:
                idd, n = f"{base}-{n}", n + 1
            usados.add(idd); nuevos += 1
            attrs = f' id="{idd}"' + attrs
        if "data-sid=" not in attrs:
            attrs = attrs.rstrip() + f' data-sid="{idd}"'
        partes.append(s[prev:b.start()] + "<section" + attrs + ">" + cuerpo + "</section>")
        prev = b.end()
    p.write_text(restaura("".join(partes) + s[prev:]), encoding="utf-8")
    print(f"{nuevos} ids nuevos, {len(usados)} en total, todos con data-sid")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "index.html")
