#!/usr/bin/env python3
"""Numera las citas de un deck contra su bibliografía, y avisa de lo que no cuadra.

    python3 tools/citas.py sesiones/S02-.../index.html

En la lámina y en el apunte se escribe la marca sin número, pegada a lo que cita:

    con <strong>GenCast</strong><cite data-ref="gencast"></cite>

Y la bibliografía de la ficha lleva su identificador en cada entrada:

    <li id="ref-gencast">Probabilistic weather forecasting...</li>

Este script rellena cada marca con el número que le toca **por su orden en la
bibliografía**, no por orden de aparición. Así una fuente citada tres veces lleva
siempre el mismo número, y mover una lámina no renumera nada.

Avisa de las dos cosas que se rompen en la práctica:

- Una marca que apunta a una entrada que no existe. Eso es un error y devuelve 1.
- Una entrada que nadie cita. Eso es solo un aviso: la lectura del curso puede
  estar en la bibliografía sin que ninguna lámina la señale.

Se corre después de tocar el deck o la bibliografía, como `ids.py`. El número vive
en el HTML, así que se ve igual en la lámina, en el paquete, en los apuntes
impreso y en apuntes.md, sin que haga falta ningún script en el navegador.
"""
import pathlib
import re
import sys

# El cuerpo va acotado a `[^<]*`, no a `.*?`: la marca lleva dentro un número y
# nada más, y con `.*?` una a la que se le olvidara el `</cite>` se tragaba todo
# hasta la siguiente marca. Como `sustituir` descarta el cuerpo y el deck se
# escribe en disco, eso borraba texto del curso sin avisar de nada.
MARCA = re.compile(r'<cite\s+data-ref="([^"]+)"\s*>([^<]*)</cite>')
# Acotarlo deja fuera a las marcas malformadas, así que hay que contarlas: si no,
# se quedarían sin numerar en silencio, que es el otro modo de fallar callando.
APERTURA = re.compile(r"<cite\b", re.I)


def main(ruta):
    p = pathlib.Path(ruta)
    src = p.read_text(encoding="utf-8")

    ficha = re.search(r'<aside class="ficha">(.*?)</aside>', src, re.S)
    if not ficha:
        print("no hay ficha de sesión: sin bibliografía no hay a qué citar")
        return 1
    claves = re.findall(r'<li id="ref-([^"]+)"', ficha.group(1))
    if not claves:
        print("la bibliografía no tiene entradas con id, del tipo <li id=\"ref-gencast\">")
        return 1
    numero = {k: i + 1 for i, k in enumerate(claves)}

    rotas, usadas, puestas = [], set(), [0]

    def sustituir(m):
        clave = m.group(1)
        if clave not in numero:
            rotas.append(clave)
            return m.group(0)
        usadas.add(clave)
        puestas[0] += 1
        return '<cite data-ref="%s">%d</cite>' % (clave, numero[clave])

    # Cada `<cite` del deck tiene que casar con una marca completa. Las que no,
    # están malformadas: les falta el cierre, llevan comillas simples o traen
    # etiquetas dentro. Se cuentan antes de sustituir, sobre el texto original.
    malformadas = len(APERTURA.findall(src)) - len(MARCA.findall(src))

    nuevo = MARCA.sub(sustituir, src)
    if nuevo != src:
        p.write_text(nuevo, encoding="utf-8")

    print("citas.py: %d marcas numeradas sobre %d referencias" % (puestas[0], len(claves)))
    if malformadas:
        print("   MALFORMADAS: %d marcas <cite> que no se pudieron leer. Revisa que "
              "cada una cierre con </cite>, use comillas dobles y no lleve etiquetas "
              "dentro. Se quedaron sin numerar." % malformadas)
    if rotas:
        print("   ROTAS: %s. No están en la bibliografía." % ", ".join(sorted(set(rotas))))
    sin_citar = [k for k in claves if k not in usadas]
    if sin_citar:
        print("   sin citar: %s" % ", ".join(sin_citar))
    if not rotas and not sin_citar and not malformadas:
        print("   todas las referencias se citan y todas las citas existen")
    return 1 if (rotas or malformadas) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "index.html"))
