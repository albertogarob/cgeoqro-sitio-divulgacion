#!/usr/bin/env python3
"""Prueba de regresión de tools/cambios.py.

    python3 tools/prueba-cambios.py

Casos de laboratorio: dos decks de mentira, con la respuesta sabida de antemano.
Lo que se vigila es lo que hace útil la herramienta en el aula: que cace lo que
cambió de verdad, que **no** cace el ruido de volver a correr el pipeline, y que
sepa distinguir una lámina nueva de una borrada y de una movida.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
OK, MAL = [], []


def ok(t, cond, detalle=""):
    (OK if cond else MAL).append(t)
    print(("pasa  " if cond else "FALLA ") + t + ("" if cond else "   [%s]" % detalle))


def lamina(sid, cuerpo, guion, attrs="", corto=""):
    c = ('<aside class="corto"><p>%s</p></aside>' % corto) if corto else ""
    return ('<section id="%s" data-sid="%s"%s><h2>%s</h2><div class="cuerpo">%s</div>'
            '<aside class="notes">%s</aside>%s</section>'
            % (sid, sid, attrs, sid.replace("-", " "), cuerpo, guion, c))


def correr(antes, ahora, *args):
    """Monta una sesión de mentira y corre cambios.py sobre ella."""
    raiz = tempfile.mkdtemp(prefix="cambios-")
    carp = os.path.join(raiz, "sesiones", "S99-de-prueba")
    os.makedirs(carp)
    open(os.path.join(carp, ".antes.html"), "w", encoding="utf-8").write(antes)
    open(os.path.join(carp, "index.html"), "w", encoding="utf-8").write(ahora)
    open(os.path.join(carp, "notas.json"), "w", encoding="utf-8").write('{"v": 1}')
    # cambios.py busca la carpeta desde tools/..; se le pasa por un enlace
    tools = os.path.join(raiz, "tools")
    os.makedirs(tools)
    for f in ("cambios.py", "anclas.py"):
        shutil.copyfile(os.path.join(AQUI, f), os.path.join(tools, f))
    r = subprocess.run([sys.executable, os.path.join(tools, "cambios.py"), "99"]
                       + list(args), capture_output=True, text=True, cwd=raiz)
    doc = json.load(open(os.path.join(carp, "notas.json"), encoding="utf-8"))
    salida = r.stdout + r.stderr
    hay_foto = os.path.exists(os.path.join(carp, ".antes.html"))
    shutil.rmtree(raiz, ignore_errors=True)
    return doc.get("cambios", {}).get("laminas", {}), salida, doc, hay_foto


CUERPO = '<ul><li data-pieza="1">El sensor suena con 0.9.</li>' \
         '<li data-pieza="2">La brigada entró por la esquina.</li></ul>'
GUION = '<p>El sensor suena con 0.9.</p><p>La brigada entró por la esquina.</p>'

print("== lo que no cambió no se reporta ==")
c, out, _, _ = correr(lamina("a", CUERPO, GUION), lamina("a", CUERPO, GUION))
ok("dos decks iguales no producen ningún cambio", not c, json.dumps(c)[:90])
ok("y lo dice", "nada cambió" in out, out)

print()
print("== el ruido del pipeline no cuenta ==")
otro = lamina("a", CUERPO.replace('data-pieza="1"', 'data-pieza="1" data-celdas="2,2"'),
              GUION.replace("<p>", '<p data-sinc="1">', 1))
c, out, _, _ = correr(lamina("a", CUERPO, GUION), otro)
ok("volver a numerar atributos no se reporta como cambio", not c, json.dumps(c)[:90])

print()
print("== una viñeta corregida ==")
nuevo = CUERPO.replace("La brigada entró por la esquina.",
                       "La brigada entró por la esquina de abajo.")
c, out, _, _ = correr(lamina("a", CUERPO, GUION), lamina("a", nuevo, GUION))
ok("la lámina sale marcada", "a" in c, json.dumps(c)[:90])
pz = c.get("a", {}).get("piezas", [])
ok("y dice qué pieza fue", len(pz) == 1 and pz[0]["n"] == "2", json.dumps(pz)[:120])
dif = pz[0]["dif"] if pz else []
ok("con las palabras añadidas marcadas",
   any(op == "+" and "abajo" in t for op, t in dif), json.dumps(dif)[:140])
ok("y lo que no cambió, sin marcar",
   any(op == "=" and "brigada" in t for op, t in dif), json.dumps(dif)[:140])
ok("el guion no se toca, así que no sale", not c["a"]["guion"], json.dumps(c["a"]["guion"]))

print()
print("== un guion reescrito ==")
g2 = GUION.replace("La brigada entró por la esquina.",
                   "La brigada no entró por la esquina.")
c, _, _, _ = correr(lamina("a", CUERPO, GUION), lamina("a", CUERPO, g2))
gu = c.get("a", {}).get("guion", [])
ok("el párrafo del guion sale marcado, con su posición",
   len(gu) == 1 and gu[0]["i"] == 1, json.dumps(gu)[:120])
ok("y la palabra quitada se conserva para enseñarla",
   any(op == "-" for op, t in gu[0]["dif"]) or
   any(op == "+" and "no" in t for op, t in gu[0]["dif"]), json.dumps(gu)[:140])

print()
print("== una viñeta nueva no desplaza a las demás ==")
con3 = ('<ul><li data-pieza="1">El sensor suena con 0.9.</li>'
        '<li data-pieza="2">Una viñeta recién metida en medio.</li>'
        '<li data-pieza="3">La brigada entró por la esquina.</li></ul>')
c, _, _, _ = correr(lamina("a", CUERPO, GUION), lamina("a", con3, GUION))
pz = c.get("a", {}).get("piezas", [])
ok("solo sale la viñeta nueva, no las que se corrieron de número",
   len(pz) == 1 and pz[0]["n"] == "2", json.dumps(pz)[:160])
ok("y sale entera como añadida",
   all(op == "+" for op, t in pz[0]["dif"]), json.dumps(pz[0]["dif"])[:120])

print()
print("== láminas que entran, salen y se mueven ==")
dos_a = lamina("a", CUERPO, GUION) + lamina("b", CUERPO, GUION)
dos_b = lamina("a", CUERPO, GUION) + lamina("c", CUERPO, GUION)
c, _, _, _ = correr(dos_a, dos_b)
ok("la lámina nueva se marca como nueva", c.get("c", {}).get("estado") == "nueva",
   json.dumps(c)[:120])
ok("la que se fue se marca como borrada", c.get("b", {}).get("estado") == "borrada",
   json.dumps(c)[:120])
ok("y la que no se tocó no sale", "a" not in c, json.dumps(c)[:120])

mov_a = lamina("a", CUERPO, GUION) + lamina("b", CUERPO, GUION)
mov_b = lamina("b", CUERPO, GUION) + lamina("a", CUERPO, GUION)
c, _, _, _ = correr(mov_a, mov_b)
ok("una lámina que cambió de sitio se marca como movida",
   "movida" in c.get("a", {}) or "movida" in c.get("b", {}), json.dumps(c)[:160])

print()
print("== el nivel de recorte ==")
c, _, _, _ = correr(lamina("a", CUERPO, GUION),
                    lamina("a", CUERPO, GUION, attrs=' data-recorte="2"'))
ok("cambiar el nivel de recorte se reporta",
   c.get("a", {}).get("recorte") == [None, "2"], json.dumps(c)[:120])

print()
print("== el guion corto ==")
c, _, _, _ = correr(lamina("a", CUERPO, GUION, corto="Version corta."),
                    lamina("a", CUERPO, GUION, corto="Version corta y distinta."))
ok("el guion corto también se compara", len(c.get("a", {}).get("corto", [])) == 1,
   json.dumps(c)[:120])

print()
print("== la foto y el olvido ==")
nuevo = CUERPO.replace("esquina.", "esquina de abajo.")
c, out, doc, hay = correr(lamina("a", CUERPO, GUION), lamina("a", nuevo, GUION), "--foto")
ok("--foto no deja ningún cambio marcado", not c, json.dumps(c)[:90])
ok("y deja la foto en su sitio", hay)
ok("y lo dice", "foto tomada" in out, out)

c, out, doc, _ = correr(lamina("a", CUERPO, GUION), lamina("a", nuevo, GUION), "--ver")
ok("--ver no escribe nada en notas.json", not c, json.dumps(c)[:90])
ok("pero lo enseña por pantalla", "pieza 2" in out, out)

print()
print("== la foto borra de verdad, también por el servidor ==")
# El fallo que esto caza, y que ocurrió el 12 de octubre de 2026: quitar la
# llave `cambios` del documento significa "no la toques" para el servidor, que
# conserva lo que el envío no menciona. Así que --foto parecía limpiar y lo que
# se acababa de dar por visto volvía en la lectura siguiente.
import re as _re
fuente = open(os.path.join(AQUI, "cambios.py"), encoding="utf-8").read()
ok("--foto manda el apartado VACÍO, no lo quita",
   'doc["cambios"] = {}' in fuente and 'doc.pop("cambios"' not in fuente,
   "sigue habiendo un pop" if 'doc.pop("cambios"' in fuente else "no asigna vacío")

c, out, doc, _ = correr(lamina("a", CUERPO, GUION), lamina("a", nuevo, GUION), "--foto")
ok("y el documento queda con el apartado vacío, no sin él",
   doc.get("cambios") == {}, json.dumps(doc.get("cambios", "ausente"))[:60])

print()
print("%d pasan, %d fallan" % (len(OK), len(MAL)))
sys.exit(1 if MAL else 0)
