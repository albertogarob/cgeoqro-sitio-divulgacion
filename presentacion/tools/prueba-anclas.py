#!/usr/bin/env python3
"""Prueba de regresión de tools/anclas.py.

    python3 tools/prueba-anclas.py [sesiones/SNN-.../index.html]

Dos mitades. La primera son casos de laboratorio: láminas de mentira escritas
aquí, con la respuesta correcta sabida de antemano. La segunda es integridad
referencial sobre un deck de verdad, que es lo que caza el fallo que importa:
un `data-sinc` que apunta a una pieza que no existe deja la lámina resaltando
nada, y en clase eso no se nota hasta que no se mueve.
"""
import re
import subprocess
import sys
import tempfile
import os
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import anclas  # noqa: E402

OK, MAL = [], []


def ok(t, cond, detalle=""):
    (OK if cond else MAL).append(t)
    print(("pasa  " if cond else "FALLA ") + t + ("" if cond else "   [" + str(detalle) + "]"))


def correr(html, *args):
    """Pasa el HTML por anclas.py de verdad, por la línea de órdenes."""
    d = tempfile.mkdtemp(prefix="anclas-")
    f = os.path.join(d, "index.html")
    open(f, "w", encoding="utf-8").write(html)
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "anclas.py"),
                        f] + list(args), capture_output=True, text=True)
    salida = open(f, encoding="utf-8").read()
    os.unlink(f); os.rmdir(d)
    return salida, r.stdout + r.stderr


def lamina(cuerpo, notas):
    return ('<section id="x" data-sid="x"><h2>T</h2><div class="cuerpo">%s</div>'
            '<aside class="notes">%s</aside></section>' % (cuerpo, notas))


def sincs(html):
    """Los data-sinc de los párrafos del guion, en orden, '' si no lo llevan."""
    a = re.search(r'<aside class="notes">(.*?)</aside>', html, re.S)
    out = []
    for m in re.finditer(r'<p\b([^>]*)>', a.group(1) if a else ""):
        s = re.search(r'data-sinc="([^"]*)"', m.group(1))
        out.append(s.group(1) if s else "")
    return out


def piezas(html):
    return re.findall(r'<(\w+)[^>]*data-pieza="(\d+)"', html)


# ---------------------------------------------------------------- laboratorio
print("== numeración de las piezas ==")
h, _ = correr(lamina(
    '<p class="motiva">El sensor del terreno se lee cada hora.</p>'
    '<svg viewBox="0 0 10 10"><text>cede</text></svg>'
    '<ul><li>La viñeta del sensor.</li><li>La viñeta del terreno.</li></ul>',
    '<p>Uno.</p><p>Dos.</p>'))
ok("cada pieza del cuerpo lleva su número en orden de lectura",
   piezas(h) == [("p", "1"), ("svg", "2"), ("li", "3"), ("li", "4")], piezas(h))

print()
print("== lo que NO es una pieza ==")
h, _ = correr(lamina(
    '<ul><li>Mira la parcela '
    '<span class="gl"><span class="gl-eti">A</span>'
    '<aside class="gl-pop"><svg class="gl-rej"><text>r</text></svg></aside></span>'
    ' del terreno.</li></ul>',
    '<p>Uno del terreno.</p><p>Dos de la parcela.</p>'))
ok("el dibujo de una glosa no es una pieza: vive dentro de un aside",
   piezas(h) == [("li", "1")], piezas(h))
ok("y el li que la contiene sí lo es", ("li", "1") in piezas(h))

h, _ = correr(lamina(
    '<p class="fig"><svg viewBox="0 0 10 10"><text>a</text></svg></p>'
    '<ul><li>Viñeta.</li></ul>',
    '<p>Uno.</p><p>Dos.</p>'))
ok("un p que solo envuelve un dibujo no es pieza: lo es el dibujo",
   piezas(h) == [("svg", "1"), ("li", "2")], piezas(h))

print()
print("== la acotación [Al dibujo...] manda mirar el dibujo ==")
h, _ = correr(lamina(
    '<p class="motiva">Motivación cualquiera.</p>'
    '<svg viewBox="0 0 10 10"><text>cede</text></svg>'
    '<ul><li>La probabilidad de transición vale 0.7 cuando cede.</li></ul>',
    '<p>[Al dibujo, la flecha de la izquierda.] La transición vale 0.7.</p>'
    '<p>[Esperar a que entren todos.]</p>'
    '<p>Una frase sin nada que ver con corvinas ni bicicletas.</p>'))
s = sincs(h)
ok("la acotación al dibujo ancla el dibujo", "2" in s[0].split(), s)
ok("y el párrafo ancla también la viñeta que desarrolla", "3" in s[0].split(), s)
ok("una acotación de escena sola no ancla nada", s[1] == "", s)
ok("un párrafo sin nada en común no ancla nada", s[2] == "", s)

print()
print("== el emparejamiento por texto ==")
h, _ = correr(lamina(
    '<ul><li>El sensor de grietas suena con probabilidad 0.9.</li>'
    '<li>La brigada no pisó la ladera del oriente.</li>'
    '<li>El periodo cero reparte la creencia mitad y mitad.</li></ul>',
    '<p>La brigada evitó la ladera del oriente esa mañana.</p>'
    '<p>El periodo cero reparte la creencia mitad y mitad entre los dos valores.</p>'))
s = sincs(h)
ok("cada párrafo cae en la viñeta de la que habla", s == ["2", "3"], s)

print()
print("== cuándo no se ancla nada ==")
h, _ = correr(lamina('<ul><li>Una viñeta cualquiera del terreno.</li></ul>',
                     '<p>Un solo párrafo que habla del terreno.</p>'))
ok("un guion de un solo párrafo no se ancla: habla de la lámina entera",
   sincs(h) == [""], sincs(h))

h, _ = correr('<section id="y" data-sid="y"><h2>T</h2>'
              '<aside class="notes"><p>Uno.</p><p>Dos.</p></aside></section>')
ok("una lámina sin cuerpo no ancla nada y no revienta", sincs(h) == ["", ""], sincs(h))

print()
print("== una pila de láminas se salta ==")
h, _ = correr('<section><section id="a" data-sid="a"><div class="cuerpo">'
              '<ul><li>Viñeta del terreno.</li></ul></div>'
              '<aside class="notes"><p>Uno del terreno.</p><p>Dos.</p></aside>'
              '</section></section>')
ok("la lámina de dentro de una pila se procesa igual",
   'data-pieza="1"' in h, h[:160])

print()
print("== idempotencia y limpieza ==")
base = lamina('<p class="motiva">El sensor del terreno se lee cada hora.</p>'
              '<svg viewBox="0 0 10 10"><text>cede</text></svg>'
              '<ul><li>La viñeta del sensor y su hora.</li></ul>',
              '<p>El sensor se lee cada hora.</p>'
              '<p>[Al dibujo, la flecha.] La viñeta del sensor.</p>')
h1, _ = correr(base)
h2, _ = correr(h1)
ok("correrlo dos veces da exactamente lo mismo", h1 == h2)
h3, _ = correr(h1, "--limpiar")
ok("--limpiar quita todos los data-pieza", "data-pieza" not in h3)
ok("--limpiar quita todos los data-sinc", "data-sinc" not in h3)
ok("y deja el contenido intacto",
   re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h3)) ==
   re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', base)))

h4, _ = correr(lamina(
    '<ul><li>Viñeta del sensor.</li><li>Viñeta de la ladera.</li></ul>',
    '<p data-sinc="2" data-sinc-mano="1">El sensor de grietas suena.</p>'
    '<p>La ladera del oriente.</p>'))
ok("un ancla puesta a mano no se recalcula",
   sincs(h4)[0] == "2", sincs(h4))

print()
print("== la cobertura: toda pieza con su párrafo ==")
import subprocess as sp


def cobertura(html):
    """Corre anclas.py y devuelve (código de salida, salida)."""
    d = tempfile.mkdtemp(prefix="anclas-")
    f = os.path.join(d, "index.html")
    open(f, "w", encoding="utf-8").write(html)
    r = sp.run([sys.executable, os.path.join(os.path.dirname(__file__), "anclas.py"), f],
               capture_output=True, text=True)
    os.unlink(f); os.rmdir(d)
    return r.returncode, r.stdout


# una lámina cuya segunda viñeta no la nombra ningún párrafo
rc, out = cobertura(lamina(
    '<ul><li>El sensor de grietas suena con probabilidad 0.9.</li>'
    '<li>La brigada no pisó la ladera del oriente.</li></ul>',
    '<p>El sensor de grietas suena mucho.</p>'
    '<p>Y el sensor de grietas vuelve a sonar.</p>'))
ok("una viñeta sin párrafo se reporta", "piezas sin párrafo" in out, out)
ok("y el comando devuelve error, para que pare el pipeline", rc == 1, rc)
ok("diciendo qué viñeta es", "ladera del oriente" in out, out)

# la misma, con su párrafo
rc, out = cobertura(lamina(
    '<ul><li>El sensor de grietas suena con probabilidad 0.9.</li>'
    '<li>La brigada no pisó la ladera del oriente.</li></ul>',
    '<p>El sensor de grietas suena mucho.</p>'
    '<p>La brigada evitó la ladera del oriente.</p>'))
ok("con su párrafo, la cobertura sale limpia",
   "TODA PIEZA DE TODA LÁMINA" in out, out)
ok("y el comando devuelve cero", rc == 0, rc)

# las láminas exentas no cuentan
for cls in ("portada", "seccion", "cierre"):
    rc, out = cobertura(
        '<section id="x" class="%s" data-sid="x"><h2>T</h2><div class="cuerpo">'
        '<ul><li>Una viñeta del terreno que nadie narra.</li>'
        '<li>Y otra de la ladera que tampoco.</li></ul></div>'
        '<aside class="notes"><p>Algo distinto.</p><p>Y otra cosa.</p></aside>'
        '</section>' % cls)
    ok("una lámina de clase %s queda fuera de la cobertura" % cls, rc == 0, out)

rc, out = cobertura(
    '<section id="bibliografia" data-sid="bibliografia"><h2>Bibliografía</h2>'
    '<div class="cuerpo"><ul><li>Markov, A. A. Science in Context, 2006.</li>'
    '<li>Baum y Petrie. Annals of Mathematical Statistics, 1966.</li></ul></div>'
    '<aside class="notes"><p>Queda proyectada.</p><p>Y nada más.</p></aside></section>')
ok("la lámina de bibliografía queda fuera de la cobertura", rc == 0, out)

print()
print("== el tramo del dibujo: la figura sigue encendida mientras se explica ==")
CUERPO_FIG = ('<p class="motiva">El tiempo se corta en periodos iguales.</p>'
              '<svg viewBox="0 0 10 10"><text>Soc(1)</text></svg>'
              '<ul><li>Cada periodo trae su copia de las dos variables.</li>'
              '<li>La flecha horizontal va de un estado al siguiente.</li></ul>')
h, _ = correr(lamina(CUERPO_FIG,
    '<p>[Al dibujo, la fila de los estados.]</p>'
    '<p>El tiempo se corta en periodos iguales.</p>'
    '<p>Cada periodo trae su copia de las dos variables.</p>'
    '<p>La flecha horizontal va de un estado al siguiente.</p>'))
s3 = sincs(h)
ok("la acotación enciende el dibujo", s3[0] == "2", s3)
ok("y sigue encendido en el párrafo que lo explica", "2" in s3[1].split(), s3)
# Hasta el 12 de octubre de 2026 esta prueba exigía lo contrario: que la figura
# siguiera encendida en TODOS los párrafos de detrás. Alberto lo señaló como un
# fallo, "a veces distrae cuando estoy discutiendo algo que no necesariamente se
# relaciona a la figura", y ahora el tramo se cierra cuando el guion cambia de
# tema. Lo que sigue garantizado es el párrafo que explica la acotación.
ok("y se apaga cuando el párrafo deja de hablar de la figura",
   "2" not in s3[3].split(), s3)
ok("sin desbancar a la línea en llano, que va aparte",
   "1" in s3[1].split(), s3)
ok("ni a la viñeta de cada párrafo",
   "3" in s3[2].split() and "4" in s3[3].split(), s3)

h, _ = correr(lamina(CUERPO_FIG,
    '<p>[Al dibujo, la fila de los estados.]</p>'
    '<p>El tiempo se corta en periodos iguales.</p>'
    '<p>[Esperar a que terminen de copiar.]</p>'
    '<p>La flecha horizontal va de un estado al siguiente.</p>'))
s4 = sincs(h)
ok("una acotación de escena cierra el tramo del dibujo",
   "2" not in s4[3].split(), s4)

# El tramo no dura hasta el final de la lámina: se apaga cuando el guion deja
# de hablar de la figura. Alberto lo señaló el 12 de octubre de 2026: "una vez
# que resaltas una figura, nunca le quitas el resaltado hasta que cambio de
# lámina... a veces distrae".
CUERPO_FIG2 = ('<p class="motiva">El terreno se dibuja periodo a periodo.</p>'
               '<svg viewBox="0 0 10 10"><text>Soc(1)</text><text>Gri(1)</text>'
               '<text>periodo 1</text></svg>'
               '<ul><li>La brigada no pisó la ladera del oriente aquella mañana.</li>'
               '<li>Soc(1) y Gri(1) son las dos variables del periodo 1.</li></ul>')
h, _ = correr(lamina(CUERPO_FIG2,
    '<p>El terreno se dibuja periodo a periodo.</p>'
    '<p>[Al dibujo, la fila de los estados.]</p>'
    '<p>Un apunte cualquiera que no nombra nada del dibujo.</p>'
    '<p>La brigada no pisó la ladera del oriente aquella mañana.</p>'))
s5 = sincs(h)
ok("la acotación garantiza el párrafo que la explica, nombre lo que nombre",
   "2" in s5[2].split(), s5)
ok("pero el siguiente ya no, si no habla de la figura",
   "2" not in s5[3].split(), s5)

h, _ = correr(lamina(CUERPO_FIG2,
    '<p>El terreno se dibuja periodo a periodo.</p>'
    '<p>[Al dibujo, la fila de los estados.]</p>'
    '<p>Un apunte cualquiera que no nombra nada del dibujo.</p>'
    '<p>Soc(1) y Gri(1) son las dos variables del periodo 1.</p>'))
s6 = sincs(h)
ok("y si sigue hablando de la figura, la figura sigue encendida",
   "2" in s6[3].split(), s6)

print()
print("== una figura sin prosa que la explique se reporta ==")
rc, out = cobertura(lamina(CUERPO_FIG,
    '<p>El tiempo se corta en periodos iguales.</p>'
    '<p>Cada periodo trae su copia de las dos variables.</p>'
    '<p>La flecha horizontal va de un estado al siguiente.</p>'
    '<p>[Al dibujo, la fila de los estados.]</p>'))
ok("la acotación al final deja la figura sin speech, y se dice",
   rc == 1 and "SOLO ACOTACIÓN" in out, out)
rc, out = cobertura(lamina(CUERPO_FIG,
    '<p>[Al dibujo, la fila de los estados.]</p>'
    '<p>El tiempo se corta en periodos iguales.</p>'
    '<p>Cada periodo trae su copia de las dos variables.</p>'
    '<p>La flecha horizontal va de un estado al siguiente.</p>'))
ok("con su prosa detrás, la figura queda cubierta", rc == 0, out)

print()
print("== el ancla simbólica, para la fórmula que es una cuenta ==")
h, _ = correr(lamina(
    '<p class="motiva">La historia completa tiene siete factores.</p>'
    '<p class="formula">\\(0.5 \\times 0.7 \\times 0.9\\)</p>'
    '<ul><li>Siete factores: la previa y dos por periodo.</li></ul>',
    '<p>Siete factores: la previa del periodo 0 y dos por periodo.</p>'
    '<p data-sinc-mano="formula">La cuenta entera está escrita en la lámina.</p>'))
s2 = sincs(h)
ok("el párrafo marcado se ancla a la fórmula, sin llevarla dentro",
   "2" in s2[1].split(), s2)
rc, out = cobertura(lamina(
    '<p class="motiva">Una historia completa del terreno tiene siete factores.</p>'
    '<p class="formula">\\(0.5 \\times 0.7 \\times 0.9\\)</p>'
    '<ul><li>La previa del periodo 0, y dos por cada periodo.</li></ul>',
    '<p>Una historia completa del terreno tiene siete factores.</p>'
    '<p>Son la previa del periodo 0, y dos por cada periodo.</p>'
    '<p data-sinc-mano="formula">La cuenta entera está escrita en la lámina.</p>'))
ok("y con eso la cobertura de esa lámina cierra", rc == 0, out)

print()
print("== --ver no escribe nada ==")
d = tempfile.mkdtemp(prefix="anclas-")
f = os.path.join(d, "index.html")
open(f, "w", encoding="utf-8").write(base)
subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "anclas.py"),
                f, "--ver"], capture_output=True, text=True)
ok("--ver deja el archivo como estaba", open(f, encoding="utf-8").read() == base)
os.unlink(f); os.rmdir(d)

# ------------------------------------------------------- integridad en un deck
ruta = sys.argv[1] if len(sys.argv) > 1 else None
if ruta and os.path.exists(ruta):
    print()
    print("== integridad referencial sobre %s ==" % ruta)
    html = open(ruta, encoding="utf-8").read()
    rotas, total, sinpieza = [], 0, 0
    for m in re.finditer(r'<section\b([^>]*)>(.*?)</section>', html, re.S):
        attrs, cuerpo = m.group(1), m.group(2)
        if "<section" in cuerpo:
            continue
        sid = (re.search(r'data-sid="([^"]+)"', attrs) or [None, "?"])[1]
        vis = anclas.sin_asides(cuerpo)
        nums = set(re.findall(r'data-pieza="(\d+)"', vis))
        for pm in re.finditer(r'<p\b([^>]*)>', cuerpo):
            sm = re.search(r'data-sinc="([^"]*)"', pm.group(1))
            if not sm:
                continue
            total += 1
            for n in sm.group(1).split():
                if n not in nums:
                    rotas.append((sid, n, sorted(nums)))
    ok("ninguna ancla apunta a una pieza que no existe", not rotas, rotas[:4])
    ok("el deck tiene anclas de verdad", total > 0, total)
    # ninguna pieza dentro de un aside
    malas = []
    for m in re.finditer(r'<aside\b[^>]*>(.*?)</aside>', html, re.S):
        if 'data-pieza="' in m.group(1):
            malas.append(m.group(0)[:70])
    ok("ninguna pieza numerada dentro de un bloque de notas", not malas, malas[:2])
    print("   %d anclas comprobadas" % total)

# ---------------------------------------------------------------------------
# Las LÍNEAS del bloque de código, del 13 de octubre de 2026.
#
# Alberto pidió "un highlighting para líneas o bloques individuales de código".
# Lo escribe anclas.py en `data-sinc-cl`, emparejando los nombres que dice el
# párrafo con los que aparecen en cada línea, y lo numera tools/codigo.py.
print()
print("las líneas del bloque de código")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from codigo import py as _hl                                         # noqa: E402

FUENTE = """from pgmpy.models import DynamicBayesianNetwork as DBN
red = DBN()
red.add_cpds(
    TabularCPD(("Soc", 0), 2, [[0.5], [0.5]]),
    TabularCPD(("Soc", 1), 2, [[0.8, 0.3], [0.2, 0.7]]))
red.initialize_initial_state()"""

_pre = '<pre><code>%s</code></pre>' % _hl(FUENTE)
_notas = ("<p>Una entrada cualquiera, sin nombrar nada del código.</p>"
          "<p>add_cpds recibe las tablas.</p>"
          "<p>initialize_initial_state copia las tablas a los periodos "
          "siguientes.</p>"
          "<p>Con DBN se crea la red vacía.</p>")
_sal, _ = correr(lamina(_pre + "<ul><li>Una viñeta cualquiera de la lámina.</li>"
                        "<li>Y otra viñeta distinta.</li></ul>", _notas))


def cls(html):
    """Los data-sinc-cl de los párrafos del guion, en orden."""
    a = re.search(r'<aside class="notes">(.*?)</aside>', html, re.S)
    out = []
    for m in re.finditer(r'<p([^>]*)>', a.group(1)):
        g = re.search(r'data-sinc-cl="([^"]*)"', m.group(1))
        out.append(g.group(1) if g else "")
    return out


_c = cls(_sal)
ok("tools/codigo.py numera cada línea del bloque",
   _sal.count('class="cl" data-cl=') == 6, _sal.count('class="cl" data-cl='))
ok("un párrafo que no nombra código no ancla ninguna línea", _c[0] == "", _c)
# add_cpds abre en la línea 3 y sus dos argumentos van en la 4 y la 5: el
# arrastre de la continuación es lo que impide que el bloque se vea partido.
ok("una línea encendida arrastra sus líneas de continuación",
   _c[1] == "3 4 5", _c)
ok("y una línea suelta se enciende sola", _c[2] == "6", _c)
# DBN no lleva guion bajo ni punto: entra por la regla de la mayúscula
# interior, añadida el 13 de octubre de 2026.
ok("un nombre con mayúscula interior también ancla", _c[3] == "1 2", _c)

# El tope de dos tercios: un párrafo que nombra algo presente en casi todas las
# líneas no ancla ninguna, porque encenderlas todas no dice nada.
_notas2 = "<p>Entrada.</p><p>Aquí se usa TabularCPD y también DBN y add_cpds.</p>"
_sal2, _ = correr(lamina(_pre + "<ul><li>Una viñeta.</li><li>Otra viñeta.</li></ul>",
                         _notas2))
ok("un párrafo que encendería más de dos tercios del bloque no ancla nada",
   cls(_sal2)[1] == "", cls(_sal2))

print()
print("%d pasan, %d fallan" % (len(OK), len(MAL)))
sys.exit(1 if MAL else 0)
