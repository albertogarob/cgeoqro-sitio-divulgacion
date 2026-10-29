"""Resaltado de sintaxis para los bloques de código de los decks.

Alberto lo pidió el 30 de septiembre de 2026, al revisar la sesión 9, sobre las
dos láminas que enseñan la forma de la biblioteca.

**Se resuelve aquí y no con highlight.js** por dos razones medidas: el plugin
que trae reveal vendorizado pesa 900 KB, que se sumarían a cada paquete de
`salidas/` encima de los 2.1 MB de MathJax; y sus temas, monokai y zenburn, son
oscuros y chocan con la plantilla institucional. Marcando los tokens desde
Python el paquete no engorda ni un byte y los colores son los de la casa.

El CSS de las clases vive en `plantillas/tema-centrogeo/tema-centrogeo.css`, con
las demás, para que las 30 sesiones compartan la misma paleta.

Los bloques van en `<pre><code>`, que MathJax deja en paz por `skipHtmlTags`, de
modo que los `<span>` de dentro no corren riesgo de que se los lleve.

Uso, desde el generador de una sesión:

    from codigo import py
    ...  f'<pre><code>{py(FUENTE)}</code></pre>'  ...
"""
import html
import io
import keyword
import tokenize

# Los nombres de la biblioteca que hay que distinguir del resto: se pintan como
# tipo, no como variable, porque son lo que la lámina está enseñando.
TIPOS = {
    "FuzzySystem", "FuzzySet", "LinguisticVariable", "Triangular_MF",
    "Trapezoidal_MF", "Gaussian_MF", "Sigmoid_MF", "InvSigmoid_MF",
    "InvGaussian_MF", "DoubleGaussian_MF", "CrispSet", "AutoTriangle",
    # hmmlearn, sesión 13. Las clases de modelo de la biblioteca, que es lo que
    # la lámina enseña: el resto de la línea es numpy y asignaciones.
    "CategoricalHMM", "GaussianHMM", "GMMHMM", "MultinomialHMM",
}


def py(fuente):
    """Devuelve el código Python con sus tokens marcados, ya escapado.

    Lo que no se reconoce sale tal cual, escapado: el resaltado nunca puede
    perder un carácter del original, porque lo que se proyecta es código que
    alguien podría copiar."""
    fuente = fuente.strip("\n")
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(fuente).readline))
    except (tokenize.TokenError, IndentationError):
        # Un fragmento que no es un módulo completo, por ejemplo con la primera
        # línea indentada, no se tokeniza. Sale sin resaltar antes que roto.
        return html.escape(fuente)

    lineas = fuente.split("\n")
    # Se marca por posición, de atrás hacia adelante, para no mover los índices
    # de los tokens que todavía quedan por insertar en esa misma línea.
    marcas = []
    for t in toks:
        cl = clase(t)
        if not cl:
            continue
        (fi, ci), (ff, cf) = t.start, t.end
        if fi != ff:                      # una cadena de varias líneas
            continue
        marcas.append((fi - 1, ci, cf, cl))

    for fila, ini, fin, cl in sorted(marcas, reverse=True):
        L = lineas[fila]
        lineas[fila] = (L[:ini] + "\x00" + cl + "\x01" + L[ini:fin] + "\x02" + L[fin:])

    # Cada línea va envuelta en su propio span, numerada desde 1. Es lo que
    # permite encender líneas sueltas del bloque mientras Alberto lee el
    # párrafo que habla de ellas, en vez de encender el bloque entero.
    # Alberto lo pidió el 13 de octubre de 2026: "no se puede hacer un
    # highlighting para líneas o bloques individuales de código. eso sería
    # mucho mejor".
    #
    # Se puede envolver sin romper nada porque el marcado de arriba descarta
    # las cadenas de varias líneas, así que **ningún span cruza un salto de
    # línea**. Si algún día dejara de ser cierto, la comprobación de abajo lo
    # detecta y la línea sale sin envolver antes que con el marcado roto.
    partes = []
    for i, L in enumerate(lineas, 1):
        esc = html.escape(L)
        if esc.count("\x00") != esc.count("\x02"):
            partes.append(esc)           # span a caballo: mejor sin envolver
        else:
            partes.append('<span class="cl" data-cl="%d">%s</span>' % (i, esc))
    out = "\n".join(partes)
    out = out.replace("\x00", '<span class="cd-').replace("\x01", '">')
    return out.replace("\x02", "</span>")


def clase(t):
    """La clase CSS de un token, o None si no se resalta."""
    if t.type == tokenize.COMMENT:
        return "com"
    if t.type == tokenize.STRING:
        return "str"
    if t.type == tokenize.NUMBER:
        return "num"
    if t.type == tokenize.NAME:
        if keyword.iskeyword(t.string):
            return "kw"
        if t.string in TIPOS:
            return "tipo"
        if t.string in ("True", "False", "None", "self"):
            return "kw"
    return None
