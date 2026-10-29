#!/usr/bin/env python3
r"""Marca cada lámina con las parcelas del terreno que menciona.

    python3 tools/parcelas.py sesiones/SNN-.../index.html

Escribe en cada `<section>` un `data-celdas="2,2 2,1 3,2"` con las casillas de
la rejilla que esa lámina nombra, mirando TODO lo que la lámina contiene: el
cuerpo, los rótulos de los dibujos, el guion de orador, el guion corto y el
apunte de estudio. Alberto lo pidió así el 8 de octubre de 2026: "toda lámina
que haga mención a alguna de las celdas, ya sea en bullet, dibujos, animaciones
o guión".

Ese atributo es lo único que lee `plantillas/tema-centrogeo/parcelas.js`, el
mapa flotante que se abre con el botón "Ver parcelas" o con la tecla M y se
queda abierto al cambiar de lámina, marcando las casillas de la lámina en curso.

**Por qué se calcula aquí y no en el navegador.** MathJax se lleva el texto de
las expresiones al componerlas, así que \(\mathrm{Soc}(2,2)\) deja de ser texto
y pasa a ser un dibujo sin coordenada legible. Buscarlas en tiempo de ejecución
obligaría a correr antes que MathJax y a depender de su orden de arranque. Aquí
se leen del HTML crudo, que es donde todavía están, y el resultado queda escrito
e inspeccionable, como hace `citas.py` con los números de las citas.

Se corre en el pipeline después de `ids.py` y antes de `empaquetar.py`. Es
idempotente: vuelve a calcular el atributo entero en cada pasada, así que una
lámina que deja de nombrar una parcela lo pierde.

Su prueba de regresión es `tools/prueba-parcelas.py`.
"""
import re
import sys

# La rejilla del terreno de la brigada es de cuatro por cuatro. La primera
# coordenada es la columna, de izquierda a derecha, y la segunda la fila
# contando desde abajo, así que la (1,1) es la esquina de abajo a la izquierda.
LADO = 4
COORD = re.compile(r'\((\d)\s*,\s*(\d)\)')
SECCION = re.compile(r'<section\b([^>]*)>(.*?)</section>', re.S)


def celdas_de(trozo):
    """Las parcelas que nombra ese trozo de HTML, en orden de lectura.

    Se mira el HTML entero de la lámina, con sus `<aside>` dentro, porque el
    guion y el apunte también nombran parcelas y la lámina las menciona igual.
    Lo que NO se mira es el `<template>` del propio mapa, que lo excluye quien
    llama.
    """
    out = []
    for c, f in COORD.findall(trozo):
        c, f = int(c), int(f)
        if 1 <= c <= LADO and 1 <= f <= LADO and (c, f) not in out:
            out.append((c, f))
    return sorted(out)


def sin_mapa(html):
    """El HTML sin el template del mapa, que nombra las dieciséis casillas."""
    return re.sub(r'<template id="mapa-parcelas">.*?</template>', ' ', html, flags=re.S)


def main(ruta):
    html = open(ruta, encoding="utf-8").read()
    salida, fin, tocadas, total = [], 0, 0, 0
    for m in SECCION.finditer(sin_mapa(html)):
        pass                                   # solo para contar con el mismo barrido
    # Se recorre sobre el HTML real, pero el template se neutraliza por posición.
    hueco = None
    t = re.search(r'<template id="mapa-parcelas">.*?</template>', html, flags=re.S)
    if t:
        hueco = (t.start(), t.end())

    for m in SECCION.finditer(html):
        if hueco and m.start() >= hueco[0] and m.end() <= hueco[1]:
            continue
        attrs, cuerpo = m.group(1), m.group(2)
        # Solo las láminas de verdad, o sea las que no contienen otra. En una
        # pila vertical el `<section>` de fuera no se proyecta nunca, así que
        # marcarlo a él y no a las de dentro deja la pila sin mapa.
        if "<section" in cuerpo:
            salida.append(html[fin:m.start()])
            salida.append("<section%s>%s</section>"
                          % (re.sub(r'\s*data-celdas="[^"]*"', '', attrs), m.group(2)))
            fin = m.end()
            continue
        if hueco and m.start() < hueco[0] < m.end():
            cuerpo = cuerpo.replace(html[hueco[0]:hueco[1]], " ")
        cel = celdas_de(cuerpo)
        # Una lámina que nombra más de media rejilla no está mencionando
        # parcelas: está DIBUJANDO la rejilla entera, con su rótulo en cada
        # casilla, como hace la lámina que enseña a leer la notación. Ahí el
        # mapa flotante sobra, porque el terreno ya está en pantalla.
        if len(cel) > LADO * LADO // 2:
            cel = []
        limpio = re.sub(r'\s*data-celdas="[^"]*"', '', attrs)
        nuevo = limpio
        if cel:
            marca = " ".join("%d,%d" % c for c in cel)
            # Se escribe junto al data-sid, que es el atributo que identifica la
            # lámina, para que el HTML quede legible.
            if 'data-sid="' in limpio:
                nuevo = limpio.replace(' data-sid="', ' data-celdas="%s" data-sid="' % marca, 1)
            else:
                nuevo = limpio + ' data-celdas="%s"' % marca
            tocadas += 1
        total += 1
        salida.append(html[fin:m.start()])
        salida.append("<section%s>%s</section>" % (nuevo, m.group(2)))
        fin = m.end()
    salida.append(html[fin:])
    nuevo_html = "".join(salida)
    if nuevo_html != html:
        open(ruta, "w", encoding="utf-8").write(nuevo_html)
    print("parcelas.py: %d de %d láminas nombran alguna parcela" % (tocadas, total))
    if not t:
        print("   AVISO: el deck no declara <template id=\"mapa-parcelas\">, "
              "así que el mapa flotante no se activa")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "index.html"))
