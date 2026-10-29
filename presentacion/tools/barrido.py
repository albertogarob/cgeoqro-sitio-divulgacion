#!/usr/bin/env python3
"""¿El resaltado barre la lámina de arriba hacia abajo, sin saltarse nada?

    python3 tools/barrido.py sesiones/SNN-.../index.html
    python3 tools/barrido.py sesiones/SNN-.../index.html --todas

**Alberto lo pidió el 13 de octubre de 2026**, revisando la sesión 13: "en el
resaltado saltas del primer párrafo al primer bullet pero te pasaste por el arco
la figura que está en medio, y se ve raro... las láminas se leen visualmente de
arriba hacia abajo, no saltes como canguro violando esta ley: la lámina va
resaltando sus elementos en un barrido de arriba hacia abajo sin saltarse
bullets o figuras".

**Qué se mide, y es una sola cosa:** el orden en que cada pieza de la lámina se
enciende **por primera vez** al recorrer el guion. Ese orden tiene que ser el
orden en que las piezas están en la lámina, de arriba hacia abajo, y ninguna
puede quedarse sin encenderse nunca.

**Lo que NO se mide, porque sería un falso positivo:** que una pieza vuelva a
encenderse después. Volver al dibujo mientras se explica la viñeta de abajo es
correcto y es lo que hace el tramo de la acotación; lo que no vale es llegar a
la viñeta de abajo **sin haber pasado antes** por el dibujo.

El arreglo casi nunca es escribir guion nuevo: es **mover** el párrafo de la
acotación y su prosa al sitio que les toca, delante de las viñetas que están
por debajo de la figura.

Hay que correrlo después de `tools/anclas.py`, que es quien escribe las marcas.
Devuelve 1 si alguna lámina rompe el barrido.
"""
import argparse
import pathlib
import re
import sys

# Las láminas sin piezas que resaltar, o cuyo guion no las recorre.
EXENTAS = {"portada", "cierre", "gracias", "bibliografia"}


def piezas_del_cuerpo(seccion):
    """Los números de pieza del cuerpo, en el orden en que están escritos."""
    # Se corta en el aside de las NOTAS, no en el primer aside que aparezca:
    # el globo de una cifra es un <aside class="gl-pop"> y vive dentro del
    # cuerpo, así que cortar ahí se comía la mitad de las piezas.
    cuerpo = re.split(r'<aside class="notes"', seccion, 1)[0]
    return [int(x) for x in re.findall(r'data-pieza="(\d+)"', cuerpo)]


def encendidas(seccion):
    """El orden en que cada pieza se enciende por primera vez."""
    notas = re.search(r'<aside class="notes">(.*?)</aside>', seccion, re.S)
    if not notas:
        return []
    primera = {}
    for i, p in enumerate(re.finditer(r'data-sinc="([^"]+)"', notas.group(1))):
        for x in (int(v) for v in p.group(1).split()):
            primera.setdefault(x, i)
    return sorted(primera, key=lambda k: primera[k])


def revisa(ruta, todas=False):
    h = pathlib.Path(ruta).read_text(encoding="utf8")
    mal = tot = 0
    for m in re.finditer(r'<section([^>]*)>(.*?)</section>', h, re.S):
        at, cuerpo = m.group(1), m.group(2)
        sid = re.search(r'data-sid="([^"]+)"', at)
        sid = sid.group(1) if sid else "?"
        if sid in EXENTAS or "seccion" in at or "portada" in at or "cierre" in at:
            continue
        orden_lamina = piezas_del_cuerpo(cuerpo)
        if len(orden_lamina) < 2:
            continue
        tot += 1
        orden_guion = encendidas(cuerpo)
        nunca = [p for p in orden_lamina if p not in orden_guion]
        esperado = [p for p in orden_lamina if p in orden_guion]
        bien = orden_guion == esperado and not nunca
        if bien and not todas:
            continue
        if not bien:
            mal += 1
        marca = "bien" if bien else "ROTO"
        print(f"  {marca}  {sid}")
        if not bien:
            print(f"        enciende {orden_guion}, y la lámina va "
                  f"{orden_lamina}")
            if nunca:
                print(f"        NUNCA se encienden: {nunca}")
    print(f"barrido.py: {tot} láminas con piezas, {mal} rompen el barrido")
    if not mal:
        print("   EL RESALTADO BARRE DE ARRIBA HACIA ABAJO EN TODAS")
    return 1 if mal else 0


def main(argv):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("deck")
    p.add_argument("--todas", action="store_true")
    a = p.parse_args(argv[1:])
    return revisa(a.deck, a.todas)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
