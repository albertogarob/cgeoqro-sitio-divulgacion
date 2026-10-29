#!/usr/bin/env python3
"""Prueba de regresión de tools/gordas.py, el cazador de láminas gordas.

No comprueba que el script corra: comprueba que **detecte**. La forma de
probarlo es sembrar el defecto sobre una copia del deck y exigir que lo cace,
porque un medidor que siempre dice "ninguna" también sale en verde.

Siembra cuatro casos sobre un temporal, sin tocar el original:

  1. Una viñeta de tres líneas en una lámina que cumplía.
  2. Una cuarta y una quinta viñeta.
  3. Una lámina estructural alargada, que NO debe salir (va exenta).
  4. Una lámina marcada con `data-sin-tope`, que tampoco.

Y comprueba sobre el deck intacto que no inventa hallazgos.

Uso:

    python3 tools/prueba-gordas.py [sesiones/SNN-.../index.html]
"""

import pathlib
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gordas import EXENTAS

RAIZ = pathlib.Path(__file__).resolve().parent.parent
POR_OMISION = RAIZ / "sesiones/S12-razonamiento-en-el-tiempo/index.html"

# Una frase lo bastante larga para ocupar dos renglones a este cuerpo.
LARGA = ("Esta viñeta se ha escrito deliberadamente larga para que ocupe dos "
         "renglones completos en la lámina y el medidor tenga que cazarla "
         "como lo que es, una viñeta gorda de texto.")

fallos = []


def corre(deck):
    r = subprocess.run([sys.executable, str(RAIZ / "tools/gordas.py"), str(deck)],
                       capture_output=True, text=True, timeout=600)
    return r.stdout + r.stderr


def cuantas(salida):
    m = re.search(r"gordas\.py: (\d+) láminas gordas", salida)
    if not m:
        raise AssertionError("gordas.py no informó el conteo:\n%s" % salida)
    return int(m.group(1))


def comprueba(nombre, cond, detalle=""):
    print("  %s %s%s" % ("ok  " if cond else "FALLA", nombre,
                         "" if cond else "   " + detalle))
    if not cond:
        fallos.append(nombre)


def primera_lamina_limpia(html):
    """Devuelve el sid de una lámina con viñetas y que hoy cumple el tope."""
    for m in re.finditer(r'<section[^>]*data-sid="([^"]+)"[^>]*>(.*?)</section>',
                         html, re.S):
        sid, cuerpo = m.group(1), m.group(2)
        # Tiene que ser una lámina NO exenta, o los dos primeros casos
        # pasarían en vacío: el medidor no mira las estructurales.
        if sid in EXENTAS or "<section" in cuerpo:
            continue
        if len(re.findall(r"<li[ >]", cuerpo)) == 3 and "data-sin-tope" not in m.group(0):
            return sid
    raise AssertionError("no hay ninguna lámina con tres viñetas donde sembrar")


def main():
    deck = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else POR_OMISION).resolve()
    if not deck.exists():
        sys.exit("prueba-gordas.py: no existe %s" % deck)
    html = deck.read_text(encoding="utf8")
    sid = primera_lamina_limpia(html)
    print("prueba-gordas.py: sembrando sobre %s, lámina %s" % (deck.name, sid))

    base = corre(deck)
    comprueba("el deck intacto sale limpio", cuantas(base) == 0, base.strip())

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="pr-gordas-"))

    def siembra(nombre, transforma):
        d = tmp / (nombre + ".html")
        d.write_text(transforma(html), encoding="utf8")
        # El deck enlaza el tema por ruta relativa, así que la copia tiene que
        # vivir al lado del original o se queda sin CSS y todo mide igual.
        junto = deck.with_name("_pr_%s.html" % nombre)
        junto.write_text(d.read_text(encoding="utf8"), encoding="utf8")
        try:
            return corre(junto)
        finally:
            junto.unlink(missing_ok=True)

    def mete_vineta_larga(h):
        i = h.index('data-sid="%s"' % sid)
        j = h.index("<li", i)
        return h[:j] + "<li>%s</li>" % LARGA + h[j:]

    s1 = siembra("larga", mete_vineta_larga)
    comprueba("caza la viñeta de tres líneas",
              cuantas(s1) == 1 and "viñeta de" in s1 and sid in s1, s1.strip())

    def mete_vinetas_de_mas(h):
        i = h.index('data-sid="%s"' % sid)
        j = h.index("<li", i)
        return h[:j] + "<li>Una.</li><li>Dos.</li>" + h[j:]

    s2 = siembra("quinta", mete_vinetas_de_mas)
    comprueba("caza las viñetas de más",
              cuantas(s2) >= 1 and "viñetas, el tope es" in s2, s2.strip())

    def alarga_estructural(h):
        i = h.index('data-sid="bibliografia"')
        j = h.index("<li", i)
        return h[:j] + "<li>%s</li>" % LARGA + h[j:]

    s3 = siembra("exenta", alarga_estructural)
    comprueba("no marca la lámina estructural exenta",
              cuantas(s3) == 0, s3.strip())

    def marca_sin_tope(h):
        h = mete_vineta_larga(h)
        return h.replace('data-sid="%s"' % sid,
                         'data-sid="%s" data-sin-tope' % sid, 1)

    s4 = siembra("sintope", marca_sin_tope)
    comprueba("data-sin-tope exime la lámina", cuantas(s4) == 0, s4.strip())

    print()
    if fallos:
        print("prueba-gordas.py: %d FALLOS: %s" % (len(fallos), ", ".join(fallos)))
        return 1
    print("prueba-gordas.py: las 5 comprobaciones en verde")
    return 0


if __name__ == "__main__":
    sys.exit(main())
