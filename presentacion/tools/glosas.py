"""Los ayudantes que escriben una etiqueta corta con su glosa al pasar el ratón.

La política está en CLAUDE.md, en "Una etiqueta corta nunca va sola": cada vez
que el material nombra una celda por su coordenada o una regla por su número,
dice también qué esconde. Cuando el deck le da a la etiqueta un globo, la glosa
posicional deja de escribirse en la lámina, porque el dibujo ya la da. Lo que NO
sale es la glosa del guion: el grupo la oye y no puede pasar el ratón por una
proyección.

Estrenado en la sesión 8 el 29 de septiembre de 2026, dentro de su gen08.py, y
subido aquí el 30 para que las demás sesiones no lo copien. El CSS vive en
plantillas/tema-centrogeo/tema-centrogeo.css y el JavaScript en
plantillas/tema-centrogeo/glosas.js. La prueba es tools/prueba-glosas.py.

Dos decisiones de forma, y las dos vienen de un fallo:

  * la expresión va en su PROPIO elemento, no suelta junto al globo. Con el
    texto y el globo como hermanos dentro del mismo tramo, MathJax dejó una
    expresión sin componer y se proyectó el LaTeX en crudo.
  * el globo es un `<aside>`, no un `<span>`. Las herramientas del proyecto
    quitan los `<aside>` antes de leer una lámina, así que su contenido deja de
    colarse en `guion.md` y de contar como texto proyectado en `terminos.py`,
    que es lo que hacía cuando era un `<span>`.

Uso típico, desde el generador de una sesión:

    from glosas import reglas, parcela, expresion

    rn = reglas({
        "R1": (r"\\(\\mathrm{SinGrieta}(p) \\Rightarrow \\mathrm{Firme}(q)\\)",
               "si el sensor calla, la vecina no tiene socavón"),
    })
    ...  f"la regla {rn('R1')} dispara"  ...
    ...  f"la parcela {parcela(1, 1)} es la entrada"  ...
"""


def rejilla_mini(celdas, lado=4, c=22):
    """La rejilla del terreno en pequeño, con las parcelas dadas marcadas.

    La primera coordenada es la columna, de izquierda a derecha, y la segunda la
    fila contando desde abajo, igual que en el terreno grande de las sesiones
    del bloque de lógica. Así la (1,1) es la esquina de abajo a la izquierda."""
    o = [f'<svg class="gl-rej" viewBox="0 0 {lado * c} {lado * c}" '
         f'width="{lado * c}" height="{lado * c}" aria-hidden="true">']
    for cx in range(1, lado + 1):
        for cy in range(1, lado + 1):
            px, py = (cx - 1) * c, (lado - cy) * c
            on = " gl-on" if (cx, cy) in celdas else ""
            o.append(f'<rect class="gl-celda{on}" x="{px}" y="{py}" '
                     f'width="{c}" height="{c}"/>')
    o.append("</svg>")
    return "".join(o)


def expresion(expr, celdas, glosa=""):
    """Una expresión que habla de parcelas, con la rejilla al pasar el ratón.

    `celdas` son las parcelas que la expresión nombra, en tuplas (columna,
    fila). El globo enseña el terreno con esas casillas marcadas, que es lo que
    ahorra reconstruir la geometría de memoria.

    `glosa` queda para el caso en que la expresión necesite una aclaración que
    NO esté ya escrita en la lámina. Si está escrita, no se repite aquí."""
    g = f'<span class="gl-glosa">{glosa}</span>' if glosa else ""
    return (f'<span class="gl" tabindex="0"><span class="gl-eti">{expr}</span>'
            f'<aside class="gl-pop">{rejilla_mini(set(celdas))}{g}</aside></span>')


def cifra(valor, expr):
    """Un número de probabilidad con su expresión completa al pasar el ratón.

    Alberto lo pidió el 13 de octubre de 2026: "nunca pongas números sueltos de
    probabilidad, siempre pon la expresión completa. Ahora si el espacio es un
    problema, y yo creo que sí: cuando pase el mouse encima de un número, un
    popup muestra la expresión matemática completa".

    En la lámina va el número a secas, que es lo que cabe, y el globo lleva la
    expresión entera. En el guion no se usa esto: ahí la expresión se escribe,
    porque una proyección no se puede señalar con el ratón.

    `expr` va en LaTeX y la compone MathJax, igual que la glosa de una regla.
    """
    return (f'<span class="gl gl-cifra" tabindex="0">'
            f'<span class="gl-eti">{valor}</span>'
            f'<aside class="gl-pop"><span class="gl-expr">{expr}</span></aside></span>')


def parcela(x, y, glosa=""):
    """Una parcela por su nombre formal, con su casilla al pasar el ratón.

    La notación es \\(\\mathrm{Par}(x,y)\\) y no lleva subíndice a propósito:
    MathJax no entra en un SVG, así que un subíndice no se puede dibujar, y la
    política "el dibujo escribe lo mismo que la fórmula" obliga a elegir una
    notación dibujable."""
    return expresion(rf"\(\mathrm{{Par}}({x},{y})\)", [(x, y)], glosa)


def reglas(tabla):
    """Devuelve la función que escribe la etiqueta de una regla de `tabla`.

    `tabla` va de etiqueta a (expresión en LaTeX, glosa en palabras), y cada
    sesión trae la suya: las reglas de la sesión 8 no son las de la 9.

    El globo NO repite la glosa en palabras: esa va escrita en la lámina, a la
    vista, porque proyectada nadie pasa el ratón. En el globo va solo la
    expresión, que es lo que no cabe en el renglón. La glosa de la tabla queda
    para el guion, que es donde el material la dice en voz alta."""
    def rn(n, marca=True):
        """`marca` pone la clase con la que el tema la pinta en la lámina que
        enumera las reglas; fuera de ahí la etiqueta va en el cuerpo del texto."""
        expr = tabla[n][0]
        cl = "gl rn" if marca else "gl"
        return (f'<span class="{cl}" tabindex="0"><span class="gl-eti">{n}</span>'
                f'<aside class="gl-pop"><span class="gl-exp">{expr}</span></aside></span>')
    return rn
