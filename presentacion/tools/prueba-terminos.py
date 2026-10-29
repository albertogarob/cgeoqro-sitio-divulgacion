#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prueba de regresión de tools/terminos.py.

Cada caso es un deck de mentira, escrito a mano, con una sola cosa mal. No usa
los decks reales: si una sesión cambia, la prueba no debe romperse.

    python3 tools/prueba-terminos.py
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import terminos                                            # noqa: E402

FALLOS = []


def deck(*secciones):
    return "<html><body>" + "\n".join(secciones) + "</body></html>"


def sec(sid, titulo, cuerpo, notas="", apuntes="", clase="verde-sello"):
    a = '<aside class="notes"><p>%s</p></aside>' % notas if notas else ''
    b = '<aside class="apuntes"><p>%s</p></aside>' % apuntes if apuntes else ''
    return ('<section id="%s" class="%s" data-sid="%s"><h2>%s</h2><div class="cuerpo">%s</div>%s%s</section>'
            % (sid, clase, sid, titulo, cuerpo, a, b))


def corre(html, glosario=()):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / 'index.html'
        p.write_text(html, encoding='utf-8')
        _, informe = terminos.revisa(p, glosario)
    sin = {r[0] for r in informe if r[2] is None}
    tarde = {r[0]: (r[1][0], r[2][0]) for r in informe if r[2] and r[2][0] > r[1][0]}
    vistos = {r[0] for r in informe}
    return sin, tarde, vistos


def caso(nombre, cond, detalle=""):
    print(("  ok   " if cond else "  FALLA ") + nombre + ("" if cond else "   " + detalle))
    if not cond:
        FALLOS.append(nombre)


# ---------------------------------------------------------------- 1. lo básico
h = deck(
    sec("uno", "Qué es propagar",
        "<ul><li>Un <strong>literal</strong> es un símbolo o su negación.</li></ul>"),
    sec("dos", "Se usa", "<ul><li>Si a la cláusula le queda un literal, ese es cierto.</li></ul>"))
sin, tarde, vistos = corre(h)
caso("el término definido antes de usarse no se reporta", not sin and not tarde)
caso("el término en negrita entra en la vigilancia", "literal" in vistos)

# ------------------------------------------- 2. definido solo en el guion: MAL
h = deck(
    sec("uno", "El algoritmo",
        '<pre class="pseudo"><code>si no hay ninguna <strong>suposición viva</strong>:</code></pre>',
        notas="Una suposición viva es un símbolo cuyo valor se eligió."))
sin, tarde, _ = corre(h)
caso("definirlo solo en el guion NO cuenta como definirlo", "suposición viva" in sin,
     "sin=%s" % sin)

# --------------------------------------- 3. definido solo en los apuntes: MAL
h = deck(sec("uno", "El núcleo", "<ul><li>El <strong>núcleo</strong> señala tres cláusulas.</li></ul>",
             apuntes="El núcleo es el grupo más pequeño de cláusulas que se contradicen."))
sin, _, _ = corre(h)
caso("definirlo solo en los apuntes NO cuenta", "núcleo" in sin, "sin=%s" % sin)

# ----------------------------------------------------- 4. usado antes: se ve
h = deck(
    sec("uno", "Tres respuestas", "<ul><li>Si hay mundos de los dos tipos, no se sabe.</li></ul>"),
    sec("dos", "Cuáles", "<ul><li>Un <strong>mundo</strong> es un terreno completo.</li></ul>"))
sin, tarde, _ = corre(h)
caso("el término usado antes de su definición se reporta", tarde.get("mundo") == (1, 2),
     "tarde=%s" % tarde)
caso("y no se reporta además como sin definir", "mundo" not in sin)

# ------------------------------------------------- 5. el glosario del archivo
h = deck(sec("uno", "Dónde se rompe", "<ul><li>La física se escribió parcela por parcela.</li></ul>"))
sin, _, vistos = corre(h, ["física"])
caso("el glosario añade términos que el deck no marca", "física" in sin, "sin=%s" % sin)
h2 = deck(sec("uno", "X", "<ul><li>Nada que ver.</li></ul>"))
sin2, _, vistos2 = corre(h2, ["cuantificador"])
caso("un término del glosario que no se proyecta no se reporta", not vistos2)

# --------------------------------------------- 6. acentos y mayúsculas
h = deck(
    sec("uno", "Refutar", "<ul><li><strong>Refutación</strong> es probar por el contrario.</li></ul>"),
    sec("dos", "Se usa", "<ul><li>La REFUTACIÓN cierra la pregunta.</li></ul>"))
sin, tarde, _ = corre(h)
caso("compara sin distinguir acentos ni mayúsculas", not sin and not tarde,
     "sin=%s tarde=%s" % (sin, tarde))

# --------------------------------------------- 7. las formas de definir
formas = {
    "es":            "Un <strong>choque</strong> es toparse con algo imposible.",
    "quiere decir":  "<strong>Obligar</strong> quiere decir que no hay otra posibilidad.",
    "se llama":      "A eso se le llama <strong>resolución</strong>, y basta con ella.",
    "dos puntos":    "<strong>Propagación</strong>: lo que se deduce sin suponer nada.",
    "articulo + es": "El <strong>núcleo</strong> de un problema imposible es el grupo menor.",
}
for nombre, cuerpo in formas.items():
    sin, _, _ = corre(deck(sec("uno", "T", "<ul><li>%s</li></ul>" % cuerpo)))
    caso("reconoce la definición por '%s'" % nombre, not sin, "sin=%s" % sin)

# --------------------------------- 8. el texto de un SVG sí es texto proyectado
h = deck(
    sec("uno", "Dibujo",
        '<svg viewBox="0 0 10 10"><text>El salto no cronologico salta varios niveles</text></svg>'))
sin, _, vistos = corre(h, ["salto no cronologico"])
caso("el rótulo de un SVG cuenta como proyectado", "salto no cronologico" in sin,
     "vistos=%s" % vistos)

h = deck(
    sec("uno", "Dibujo",
        '<svg viewBox="0 0 10 10"><text>Un salto no cronologico es el que se brinca niveles</text></svg>'))
sin, _, _ = corre(h, ["salto no cronologico"])
caso("y un SVG también puede definir el término", not sin, "sin=%s" % sin)

# ---- 8b. dos rótulos contiguos de un SVG no se leen como una sola frase
h = deck(
    sec("uno", "Dibujo",
        '<svg viewBox="0 0 10 10">'
        '<text>Socavon en la 2,2</text><text>una suposicion es lo que se elige</text></svg>'))
sin, _, _ = corre(h, ["socavon en la 2,2"])
caso("dos rótulos contiguos no se funden en una frase", "socavon en la 2,2" in sin,
     "sin=%s" % sin)

# ------------------------------------- 9. no confunde un término con otro mayor
h = deck(
    sec("uno", "A", "<ul><li>Una <strong>cláusula</strong> es una disyunción.</li></ul>"),
    sec("dos", "B", "<ul><li>La <strong>cláusula aprendida</strong> se guarda.</li></ul>"))
sin, _, vistos = corre(h)
caso("'cláusula aprendida' no se da por definida por 'cláusula'",
     "cláusula aprendida" in sin and "cláusula" not in sin, "sin=%s" % sin)

# ---------------------------------------- 10. el orden lo da la posición real
h = deck(
    sec("uno", "A", "<ul><li>Sin nada.</li></ul>"),
    sec("dos", "B", "<ul><li>Aquí aparece el <strong>modelo</strong> por primera vez.</li></ul>"),
    sec("tres", "C", "<ul><li>Un modelo es una asignación completa.</li></ul>"))
_, tarde, _ = corre(h)
caso("el número de lámina que reporta es el real", tarde.get("modelo") == (2, 3),
     "tarde=%s" % tarde)

# ---------------------------------------- 11. el comentario HTML no es visible
h = deck(sec("uno", "A", "<!-- un pivote es el símbolo que se cancela -->"
                         "<ul><li>El <strong>pivote</strong> se cancela.</li></ul>"))
sin, _, _ = corre(h)
caso("un comentario del HTML no define nada", "pivote" in sin, "sin=%s" % sin)

# --------------------------- 12. la portada y la agenda no cuentan como uso
h = deck(
    sec("portada", "Sesión 7: DPLL", "<ul><li>Todo sobre <strong>DPLL</strong>.</li></ul>",
        clase="portada"),
    sec("agenda", "Lo que veremos hoy", "<ul><li>Qué es <strong>DPLL</strong>.</li></ul>"),
    sec("uno", "El algoritmo", "<ul><li><strong>DPLL</strong> es el algoritmo de 1962.</li></ul>"))
sin, tarde, _ = corre(h)
caso("la portada y la agenda no cuentan como primer uso", not sin and not tarde,
     "sin=%s tarde=%s" % (sin, tarde))

# -------------------- 13. con glosario, la negrita deja de mandar
h = deck(sec("uno", "A", "<ul><li>Esto es <strong>importantísimo</strong> y ya.</li></ul>"
                         "<ul><li>Y aquí sale un cuantificador sin definir.</li></ul>"))
sin, _, vistos = corre(h, ["cuantificador"])
caso("con glosario, la negrita deja de mandar",
     vistos == {"cuantificador"}, "vistos=%s" % vistos)

# ------------------- 14. el rótulo de un tramo de video define, pero no estrena
# Las dos mitades de la asimetría del 8 de octubre de 2026. La barra del
# reproductor enseña el rótulo del tramo mientras corre, así que una definición
# escrita ahí cuenta; pero el rótulo va pasando, así que no sirve para fijar la
# primera mención de un término.
TRAMO = ('<span class="tramo" data-start="0" data-end="5">La <strong>ponderacion</strong> '
         'es pesar cada mundo.</span>')
h = deck(sec("video", "El cuarto algoritmo", TRAMO),
         sec("dos", "Despues", "<ul><li>Y aplicamos la ponderacion al terreno.</li></ul>"))
sin, tarde, _ = corre(h, ["ponderacion"])
caso("una definicion escrita en un tramo de video cuenta",
     "ponderacion" not in sin, "sin=%s" % sin)
caso("y el tramo no adelanta la primera mencion a su lamina",
     tarde.get("ponderacion") is None and not sin, "tarde=%s sin=%s" % (tarde, sin))

# El caso inverso: un termino que SOLO aparece en un tramo, y sin definirse,
# no se reporta, porque el tramo no cuenta como mencion proyectada.
h = deck(sec("video", "El cuarto algoritmo",
             '<span class="tramo" data-start="0" data-end="5">Aqui sale la ponderacion.</span>'))
sin, tarde, vistos = corre(h, ["ponderacion"])
caso("un termino solo nombrado en un tramo no se reporta",
     not sin and not tarde, "sin=%s tarde=%s" % (sin, tarde))

print()
if FALLOS:
    print("FALLAN %d pruebas: %s" % (len(FALLOS), ", ".join(FALLOS)))
    sys.exit(1)
print("todas las pruebas pasan")
