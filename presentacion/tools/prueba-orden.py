#!/usr/bin/env python3
"""Prueba de regresión del orden de las láminas.

    python3 tools/prueba-orden.py [sesiones/SNN-.../index.html]

Cubre las dos mitades de la misma funcionalidad:

  - la rejilla de revisar.js, tecla R, en Chrome headless: que estén todas las
    láminas, que arrastrar una la cambie de sitio de verdad en el deck y no solo
    en la miniatura, que el cambio quede marcado como pendiente mientras el HTML
    no lo diga, que Escape a mitad del arrastre lo cancele, que el botón de
    deshacer devuelva el orden del deck, que un clic sin arrastre lleve a su
    lámina, y que las notas sigan pegadas a su lámina después de moverla;

  - tools/reordenar.py, que es quien lo lleva al archivo: que permute los
    <section> sin tocar su contenido, que el deck resultante pese exactamente lo
    mismo, que concilie un orden que se quedó viejo y avise de lo que conciliar
    le costó, que respalde el anterior, que cierre el pendiente en notas.json
    subiendo la versión, que no cierre un arrastre que llegó mientras corría,
    que no escriba nada cuando el deck ya está en ese orden, y que un fallo de
    escritura no deje ni el deck ni el respaldo a medias;

  - el diferencial entre las dos copias de la misma regla: `conciliar` y
    `lasMovidas` están escritas en JavaScript y en Python, y tienen que decir lo
    mismo. Se extrae el cuerpo de las dos funciones del revisar.js de verdad, se
    corre en node y se compara contra Python sobre cuatrocientos casos. Si no
    hay node, esa parte se salta diciéndolo.

Corre con un perfil de Chrome desechable y sobre copias en un directorio
temporal: no toca las notas reales ni ningún deck del proyecto.
"""
import contextlib
import io
import json
import os
import random
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
import reordenar as R                                    # noqa: E402

RUTA = sys.argv[1] if len(sys.argv) > 1 else \
    "sesiones/S01-presentacion-del-curso-y-evaluacion/index.html"

# ---------------------------------------------------------------- lado Python

DECK_MINIMO = """<html><body>
<div class="reveal"><div class="slides">
      <!-- cabecera del deck, se queda arriba -->
      <section id="uno" data-sid="uno"><h2>Uno</h2><div>anidado</div></section>

      <section id="dos" data-sid="dos"><h2>Dos</h2>
        <aside class="notes"><p>guion con &lt;section&gt; escrito</p></aside>
      </section>

      <section id="tres" data-sid="tres"><h2>Tres</h2>
        <script>var x = "</div>";</script>
      </section>
</div></div>
</body></html>"""


def callado(args):
    """reordenar.main con su parte hablada apagada: aquí solo importa qué hizo."""
    with contextlib.redirect_stdout(io.StringIO()):
        return R.main(args)


def ids_de(html):
    return [x[2] for x in R.laminas(html)[0]]


def prueba_python(res):
    def ok(n, c, extra=""):
        res.append(("OK   " if c else "FALLA") + "  " + n + (("  [" + str(extra) + "]") if not c and extra else ""))

    # --- el lector de láminas ---
    ids = ids_de(DECK_MINIMO)
    ok("lee las tres láminas y sus ids", ids == ["uno", "dos", "tres"], ids)
    ok("no se traga el </div> escrito dentro de un script",
       R.laminas(DECK_MINIMO)[1] > DECK_MINIMO.index('id="tres"'))
    # reveal le quita el id a la lámina visible, así que manda data-sid
    ok("data-sid manda sobre id",
       ids_de(DECK_MINIMO.replace('id="dos" data-sid="dos"',
                                  'id="viejo" data-sid="nuevo"'))[1] == "nuevo")
    ok("y sin data-sid vale el id",
       ids_de(DECK_MINIMO.replace(' data-sid="dos"', ""))[1] == "dos")
    ok('un ">" dentro de un atributo no rompe la lectura del id',
       ids_de(DECK_MINIMO.replace('<section id="dos"',
                                  '<section data-tip="si x > 0" id="dos"'))[1] == "dos")
    ok("un comentario que nombre el div de las láminas no lo suplanta",
       ids_de('<!-- ojo con <div class="slides"> -->' + DECK_MINIMO) ==
       ["uno", "dos", "tres"])

    # --- conciliar ---
    ok("conciliar respeta el orden pendiente",
       R.conciliar(["c", "a", "b"], ["a", "b", "c"]) == ["c", "a", "b"])
    ok("conciliar tira lo que ya no existe",
       R.conciliar(["c", "z", "a", "b"], ["a", "b", "c"]) == ["c", "a", "b"])
    ok("conciliar mete la lámina nueva detrás de su vecina",
       R.conciliar(["c", "a"], ["a", "b", "c"]) == ["c", "a", "b"],
       R.conciliar(["c", "a"], ["a", "b", "c"]))
    ok("conciliar pone al principio la nueva que abre el deck",
       R.conciliar(["c", "b"], ["a", "b", "c"]) == ["a", "c", "b"],
       R.conciliar(["c", "b"], ["a", "b", "c"]))
    ok("conciliar sin pendiente deja el deck como está",
       R.conciliar([], ["a", "b", "c"]) == ["a", "b", "c"])
    ok("conciliar no duplica un id repetido en el pendiente",
       R.conciliar(["c", "c", "a", "b"], ["a", "b", "c"]) == ["c", "a", "b"])
    # el caso que distingue "detrás de su vecina" de "al final de todo"
    ok("conciliar mete la nueva en medio, no al final",
       R.conciliar(["b", "a"], ["a", "x", "b"]) == ["b", "a", "x"],
       R.conciliar(["b", "a"], ["a", "x", "b"]))
    ok("conciliar con dos nuevas las deja cada una con su vecina",
       R.conciliar(["d", "a"], ["a", "b", "c", "d"]) == ["d", "a", "b", "c"],
       R.conciliar(["d", "a"], ["a", "b", "c", "d"]))

    # --- cuáles cuentan como movidas: la misma regla que la rejilla ---
    ok("una lámina subida al principio es la única movida",
       R.lasMovidas(["a", "b", "c", "d"], ["d", "a", "b", "c"]) == ["d"],
       R.lasMovidas(["a", "b", "c", "d"], ["d", "a", "b", "c"]))
    ok("sin cambios no hay ninguna movida",
       R.lasMovidas(["a", "b", "c"], ["a", "b", "c"]) == [])
    ok("un intercambio de dos cuenta una, no dos",
       len(R.lasMovidas(["a", "b"], ["b", "a"])) == 1)

    # --- permutar de verdad ---
    sal, quiero, viejo, avisos = R.reordenar(DECK_MINIMO, ["tres", "uno", "dos"])
    ok("permuta las láminas", ids_de(sal) == ["tres", "uno", "dos"], ids_de(sal))
    ok("el archivo pesa exactamente lo mismo", len(sal) == len(DECK_MINIMO))
    ok("ninguna lámina cambia por dentro",
       sorted(sal[i:j] for i, j, _ in R.laminas(sal)[0]) ==
       sorted(DECK_MINIMO[i:j] for i, j, _ in R.laminas(DECK_MINIMO)[0]))
    ok("el comentario de cabecera se queda arriba",
       sal.index("<!-- cabecera") < sal.index('id="tres"'))
    ok("lo de fuera del div de láminas no se toca",
       sal.split('<div class="slides">')[0] == DECK_MINIMO.split('<div class="slides">')[0] and
       sal.endswith("</div></div>\n</body></html>"))
    trozo = {i: sal[a:b] for a, b, i in R.laminas(sal)[0]}
    ok("el guion de cada lámina viaja con ella, dentro de su bloque",
       "guion con" in trozo["dos"] and "guion con" not in trozo["uno"] and
       "guion con" not in trozo["tres"], sorted(trozo))
    ok("y el script de la tercera también",
       "var x" in trozo["tres"] and "var x" not in trozo["uno"])

    # --- casos que tienen que fallar en vez de escribir a medias ---
    for nombre, deck, trozo in [
        ("avisa de las láminas sin id",
         DECK_MINIMO.replace(' id="dos" data-sid="dos"', ""), "sin id"),
        ("avisa de los ids repetidos",
         DECK_MINIMO.replace('id="tres" data-sid="tres"', 'id="uno" data-sid="uno"'), "repetidos"),
        ("avisa si no hay div de láminas",
         DECK_MINIMO.replace('<div class="slides">', "<div>"), "slides"),
        ("avisa si un section no cierra",
         DECK_MINIMO.replace("<h2>Dos</h2>", "<h2>Dos</h2><section>"), "cerrar"),
    ]:
        try:
            R.reordenar(deck, ["tres", "uno", "dos"])
            ok(nombre, False, "no lanzó error")
        except R.Error as e:
            ok(nombre, trozo in str(e), str(e))

    # --- los avisos, que son lo que le dice a Alberto que el orden se quedó viejo ---
    def avisos_de(orden, deck=DECK_MINIMO):
        return R.reordenar(deck, orden)[3]

    a = avisos_de(["tres", "cuatro", "uno", "dos"])
    ok("avisa de las láminas del pendiente que ya no existen",
       any("ya no existen" in x and "cuatro" in x for x in a), a)
    a = avisos_de(["tres", "uno"])
    ok("avisa de las láminas nuevas que se quedan junto a su vecina",
       any("vecina" in x and "dos" in x for x in a), a)
    a = R.reordenar(DECK_MINIMO.replace("      <section id=\"dos\"",
                                        "      <!-- parte 2 -->\n      <section id=\"dos\""),
                    ["tres", "uno", "dos"])[3]
    ok("avisa del comentario que hay entre dos láminas",
       any("comentario" in x for x in a), a)
    ok("y no inventa avisos cuando no hay nada que decir",
       avisos_de(["tres", "uno", "dos"]) == [])

    # --- `orden` que no sea una lista no puede mover nada ---
    for basura, como in [("cba", "un texto"), ({"c": 1, "a": 2}, "un diccionario"),
                         (7, "un número")]:
        try:
            R.reordenar(DECK_MINIMO, basura)
            ok("un `orden` que es " + como + " se rechaza", False, "no lanzó error")
        except R.Error as e:
            ok("un `orden` que es " + como + " se rechaza", "no es una lista" in str(e), str(e))

    # --- láminas por escribir y láminas borradas ---
    nueva = [{"id": "nueva-1", "texto": "Un ejemplo geoespacial.\n\nCon reglas & flechas."}]
    sal, quiero, viejo, av = R.reordenar(DECK_MINIMO, ["uno", "nueva-1", "dos", "tres"], nueva, [])
    ok("la lámina por escribir entra en su sitio",
       ids_de(sal) == ["uno", "nueva-1", "dos", "tres"], ids_de(sal))
    trozo = {i: sal[a:b] for a, b, i in R.laminas(sal)[0]}
    ok("y lleva la marca que impide entregarla al grupo",
       'data-pendiente="1"' in trozo["nueva-1"])
    ok("con el encargo dentro, en párrafos y con el HTML escapado",
       "<p>Un ejemplo geoespacial.</p>" in trozo["nueva-1"] and
       "reglas &amp; flechas" in trozo["nueva-1"] and "&" not in
       trozo["nueva-1"].replace("&amp;", ""), trozo["nueva-1"][:120])
    ok("y el encargo también en el guion, para tenerlo delante al escribirla",
       "Encargo:" in trozo["nueva-1"] and "notes" in trozo["nueva-1"])
    ok("las demás láminas no cambian al meter una nueva",
       trozo["uno"] == {i: DECK_MINIMO[a:b] for a, b, i in R.laminas(DECK_MINIMO)[0]}["uno"])

    sal, quiero, viejo, av = R.reordenar(DECK_MINIMO, ["uno", "dos", "tres"], [], ["dos"])
    ok("la lámina borrada desaparece", ids_de(sal) == ["uno", "tres"], ids_de(sal))
    ok("y las que quedan no cambian por dentro",
       {i: sal[a:b] for a, b, i in R.laminas(sal)[0]}["tres"] ==
       {i: DECK_MINIMO[a:b] for a, b, i in R.laminas(DECK_MINIMO)[0]}["tres"])
    ok("lo de fuera del div de láminas sigue intacto al borrar",
       sal.endswith("</div></div>\n</body></html>"))

    sal, _, _, av = R.reordenar(DECK_MINIMO, ["tres", "nueva-2", "uno", "dos"],
                                [{"id": "nueva-2", "texto": ""}], ["uno"])
    ok("las tres cosas a la vez: mover, meter y borrar",
       ids_de(sal) == ["tres", "nueva-2", "dos"], ids_de(sal))
    ok("una lámina por escribir sin descripción lo dice",
       "Sin descripción." in {i: sal[a:b] for a, b, i in R.laminas(sal)[0]}["nueva-2"])

    av = R.reordenar(DECK_MINIMO, ["uno", "dos", "tres"],
                     [{"id": "dos", "texto": "ya escrita"}], ["no-existe"])[3]
    ok("avisa de la lámina por escribir que ya está en el HTML",
       any("ya están en el HTML" in x and "dos" in x for x in av), av)
    ok("y de la marcada para borrar que ya no existe",
       any("ya no existen" in x and "no-existe" in x for x in av), av)

    for basura, campo in [("x", "nuevas"), (7, "borradas")]:
        try:
            R.reordenar(DECK_MINIMO, [], basura if campo == "nuevas" else [],
                        basura if campo == "borradas" else [])
            ok("`%s` que no es lista se rechaza" % campo, False, "no lanzó error")
        except R.Error as e:
            ok("`%s` que no es lista se rechaza" % campo, "no es una lista" in str(e), str(e))

    try:
        R.reordenar(DECK_MINIMO, [], [{"id": 'mal"id', "texto": "x"}], [])
        ok("un id que no vale como atributo HTML se rechaza", False, "no lanzó error")
    except R.Error as e:
        ok("un id que no vale como atributo HTML se rechaza",
           "no vale como atributo" in str(e), str(e))
    try:
        R.reordenar(DECK_MINIMO, [], [], ["uno", "dos", "tres"])
        ok("borrar todas las láminas se rechaza con un mensaje claro", False, "no lanzó error")
    except R.Error as e:
        ok("borrar todas las láminas se rechaza con un mensaje claro",
           "sin ninguna lámina" in str(e), str(e))
    av = R.reordenar(DECK_MINIMO, ["uno", "tres"], [], ["dos"])[3]
    ok("no avisa de 'junto a su vecina' por una lámina que se va a borrar",
       not any("vecina" in x for x in av), av)
    ok("un texto que no es texto no revienta",
       "Sin descripción." in R.reordenar(DECK_MINIMO, ["uno", "n9", "dos", "tres"],
                                         [{"id": "n9", "texto": 7}], [])[0])

    ok("conciliar coloca la lámina por escribir que el orden nombra",
       R.conciliar(["a", "n1", "b"], ["a", "b"], ["n1"]) == ["a", "n1", "b"],
       R.conciliar(["a", "n1", "b"], ["a", "b"], ["n1"]))
    ok("y si el orden no la nombra, la deja al final",
       R.conciliar(["a", "b"], ["a", "b"], ["n1"]) == ["a", "b", "n1"])

    # --- combinar láminas: se marca, no se funde ni se borra nada ---
    fus = [{"id": "f1", "partes": ["tres", "uno"], "texto": 'Con "comillas" & <b>etiquetas</b>.'}]
    sal, _, _, av = R.reordenar(DECK_MINIMO, [], [], [], fus)
    trozo = {i: sal[a:b] for a, b, i in R.laminas(sal)[0]}
    ok("combinar no mueve ni borra ninguna lámina",
       ids_de(sal) == ["uno", "dos", "tres"], ids_de(sal))
    ok("la primera parte queda marcada con las demás",
       'data-combinar="uno"' in trozo["tres"], trozo["tres"][:160])
    ok("y con la nota, en su propio atributo y escapada",
       'data-combinar-nota="Con &quot;comillas&quot; &amp; &lt;b&gt;etiquetas&lt;/b&gt;."'
       in trozo["tres"], trozo["tres"][:240])
    ok("las otras partes apuntan a la primera",
       'data-combinar-en="tres"' in trozo["uno"])
    ok("la que no entra en la fusión no se toca",
       trozo["dos"] == {i: DECK_MINIMO[a:b] for a, b, i in R.laminas(DECK_MINIMO)[0]}["dos"])
    ok("y el contenido de las combinadas sigue entero",
       "guion con" in trozo["dos"] and "<h2>Tres</h2>" in trozo["tres"] and
       "<h2>Uno</h2>" in trozo["uno"])

    dos = R.reordenar(sal, [], [], [], fus)[0]
    ok("aplicarla dos veces no acumula marcas",
       dos.count("data-combinar=") == 1 and dos.count("data-combinar-en=") == 1 and
       dos.count("data-combinar-nota=") == 1, dos.count("data-combinar-nota="))
    ok("y sale igual byte a byte", dos == sal)
    otra = R.reordenar(sal, ["dos", "uno", "tres"], [], [], [])[0]
    ok("y un reordenado posterior no se lleva las marcas por delante",
       otra.count("data-combinar=") == 1 and otra.count("data-combinar-en=") == 1,
       otra.count("data-combinar"))

    # una fusión de tres: el separador de las partes y los dos apuntadores
    tri = R.reordenar(DECK_MINIMO, [], [], [],
                      [{"id": "f3", "partes": ["uno", "dos", "tres"], "texto": ""}])[0]
    t3 = {i: tri[a:b] for a, b, i in R.laminas(tri)[0]}
    ok("una fusión de tres nombra a las dos que absorbe, separadas por espacio",
       'data-combinar="dos tres"' in t3["uno"], t3["uno"][:150])
    ok("y las dos apuntan a la primera",
       'data-combinar-en="uno"' in t3["dos"] and 'data-combinar-en="uno"' in t3["tres"])
    ok("una nota vacía se escribe vacía, no se inventa",
       'data-combinar-nota=""' in t3["uno"], t3["uno"][:150])

    for malas, que in [([{"id": "f", "partes": [1, 2]}], "números"),
                       ([{"id": "f", "partes": [["a"], "b"]}], "listas")]:
        try:
            R.reordenar(DECK_MINIMO, [], [], [], malas)
            ok("una fusión con partes que son %s se rechaza" % que, False, "no lanzó error")
        except R.Error as e:
            ok("una fusión con partes que son %s se rechaza" % que,
               "no son ids de lámina" in str(e), str(e))
    try:
        R.reordenar(DECK_MINIMO, [], [], [],
                    [{"id": "f1", "partes": ["uno", "dos"]},
                     {"id": "f2", "partes": ["tres", "uno"]}])
        ok("una lámina en dos fusiones se rechaza", False, "no lanzó error")
    except R.Error as e:
        ok("una lámina en dos fusiones se rechaza",
           "en más de una fusión" in str(e) and "uno" in str(e), str(e))

    # el aviso tiene que decir lo mismo que el marcado
    sal2, _, _, av2 = R.reordenar(DECK_MINIMO, ["uno", "nue", "dos", "tres"],
                                  [{"id": "nue", "texto": "x"}], [],
                                  [{"id": "f4", "partes": ["uno", "nue"], "texto": ""}])
    ok("una fusión con una lámina por escribir dentro se marca, y no se avisa de lo contrario",
       'data-combinar="nue"' in sal2 and not any("sin partes" in x for x in av2), av2)

    # una marca escrita a mano con comillas simples también se limpia
    manual = DECK_MINIMO.replace('<section id="uno"', '<section data-combinar=\'x\' id="uno"')
    limpia = R.reordenar(manual, [], [], [],
                         [{"id": "f5", "partes": ["uno", "dos"], "texto": ""}])[0]
    ok("una marca vieja con comillas simples no se duplica",
       limpia.count("data-combinar=") == 1, limpia.count("data-combinar="))

    av = R.reordenar(DECK_MINIMO, [], [], ["uno"],
                     [{"id": "f2", "partes": ["uno", "dos"], "texto": ""}])[3]
    ok("avisa de la fusión que se quedó sin partes",
       any("sin partes suficientes" in x for x in av), av)
    try:
        R.reordenar(DECK_MINIMO, [], [], [], "x")
        ok("`fusiones` que no es lista se rechaza", False, "no lanzó error")
    except R.Error as e:
        ok("`fusiones` que no es lista se rechaza", "no es una lista" in str(e), str(e))

    # --- el paquete se niega a llevar una lámina sin escribir ---
    import importlib.util as _iu
    _sp = _iu.spec_from_file_location("empaquetar", RAIZ / "tools" / "empaquetar.py")
    _emp = _iu.module_from_spec(_sp)
    _sp.loader.exec_module(_emp)
    try:
        _emp.Empaquetador.auditar(None, '<section data-pendiente="1"><h2>x</h2></section>')
        ok("empaquetar.py se niega a entregar una lámina por escribir", False, "no paró")
    except SystemExit as e:
        ok("empaquetar.py se niega a entregar una lámina por escribir",
           "por escribir" in str(e), str(e))
    try:
        _emp.Empaquetador.auditar(None, '<section data-combinar="b"><h2>x</h2></section>')
        ok("y tampoco una fusión a medias", False, "no paró")
    except SystemExit as e:
        ok("y tampoco una fusión a medias", "sin combinar" in str(e), str(e))
    try:
        _emp.Empaquetador.sin_pendientes(None, '<section data-combinar-en="a"></section>')
        ok("ni siquiera en la variante con guion, que es la mía", False, "no paró")
    except SystemExit as e:
        ok("ni siquiera en la variante con guion, que es la mía",
           "por combinar" in str(e), str(e))
    try:
        _emp.Empaquetador.auditar(None, "<section><h2>x</h2></section>")
        ok("y no estorba a un deck normal", True)
    except SystemExit as e:
        ok("y no estorba a un deck normal", False, str(e))

    # --- el deck de verdad, entero ---
    real = pathlib.Path(RUTA)
    if real.exists():
        h = real.read_text(encoding="utf-8")
        ids = ids_de(h)
        ok("lee el deck real y todas sus láminas tienen id",
           len(ids) > 5 and all(ids), len(ids))
        vuelta = list(reversed(ids))
        sal, _, _, _ = R.reordenar(h, vuelta)
        ok("da la vuelta al deck real sin perder un byte", len(sal) == len(h))
        ok("el deck real queda del revés", ids_de(sal) == vuelta)
        ok("ninguna lámina del deck real cambia por dentro",
           sorted(sal[i:j] for i, j, _ in R.laminas(sal)[0]) ==
           sorted(h[i:j] for i, j, _ in R.laminas(h)[0]))
        # dos vueltas devuelven el original, carácter por carácter
        otra, _, _, _ = R.reordenar(sal, ids)
        ok("y dos vueltas devuelven el archivo original", otra == h)

    # --- el guion completo del script, sobre copias ---
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="orden-"))
    try:
        d = tmp / "sesiones" / "S99-prueba"
        d.mkdir(parents=True)
        fuente = real if real.exists() else None
        if fuente:
            shutil.copy(fuente, d / "index.html")
        else:
            (d / "index.html").write_text(DECK_MINIMO, encoding="utf-8")
        h = (d / "index.html").read_text(encoding="utf-8")
        ids = ids_de(h)
        nuevo = [ids[-1]] + ids[:-1]
        (d / "notas.json").write_text(json.dumps(
            {"v": 4, "notas": {"x": [{"nid": "n1", "texto": "no se toca"}]},
             "orden": nuevo}), encoding="utf-8")
        antes = R.leer_notas.__module__          # solo para callar a los linters

        viejo_cwd = os.getcwd()
        os.chdir(tmp)
        try:
            rc = callado(["sesiones/S99-prueba/index.html", "--ver"])
        finally:
            os.chdir(viejo_cwd)
        ok("--ver no escribe nada", rc == 0 and ids_de((d / "index.html").read_text(encoding="utf-8")) == ids)
        ok("--ver tampoco cierra el pendiente",
           json.loads((d / "notas.json").read_text(encoding="utf-8"))["orden"] == nuevo)

        rc = callado([str(d / "index.html")])
        h2 = (d / "index.html").read_text(encoding="utf-8")
        ok("aplica el orden al archivo", rc == 0 and ids_de(h2) == nuevo, ids_de(h2)[:3])
        respaldos = sorted(d.glob("index.html.bak.orden.*"))
        ok("deja respaldo del anterior, con fecha en el nombre",
           len(respaldos) == 1 and respaldos[0].read_text(encoding="utf-8") == h,
           [x.name for x in respaldos])
        n = json.loads((d / "notas.json").read_text(encoding="utf-8"))
        ok("cierra el pendiente y sube la versión", n["orden"] == [] and n["v"] == 5, n.get("v"))
        ok("no toca las notas de la sesión", n["notas"]["x"][0]["nid"] == "n1")
        ok("no deja archivos a medias",
           not list(d.glob("*.tmp")) and not list(d.glob("*.json.tmp")))

        rc = callado([str(d / "index.html")])
        ok("una segunda pasada no vuelve a mover nada",
           rc == 0 and (d / "index.html").read_text(encoding="utf-8") == h2)

        # un orden pendiente que ya está aplicado se cierra sin reescribir
        (d / "notas.json").write_text(json.dumps({"v": 9, "orden": nuevo}), encoding="utf-8")
        marca = (d / "index.html").stat().st_mtime_ns
        rc = callado([str(d / "index.html")])
        n = json.loads((d / "notas.json").read_text(encoding="utf-8"))
        ok("un orden ya aplicado se cierra sin tocar el deck",
           rc == 0 and n["orden"] == [] and n["v"] == 10 and
           (d / "index.html").stat().st_mtime_ns == marca)

        # el respaldo de la primera pasada tiene que seguir ahí: aplicar dos veces
        # es lo normal, y con un solo respaldo la segunda se llevaba el original
        (d / "notas.json").write_text(json.dumps({"v": 1, "orden": ids}), encoding="utf-8")
        callado([str(d / "index.html")])
        respaldos = sorted(d.glob("index.html.bak.orden.*"))
        ok("y el respaldo del original no se pisa en la segunda",
           any(x.read_text(encoding="utf-8") == h for x in respaldos),
           [x.name for x in respaldos])

        # --- el arrastre que llega mientras corre el script no se tira ---
        (d / "notas.json").write_text(json.dumps({"v": 1, "orden": ["a", "b"]}),
                                      encoding="utf-8")
        ok("no cierra un orden que cambió mientras tanto",
           R.cerrar_orden(d, {"orden": ["b", "a"]}) is False and
           json.loads((d / "notas.json").read_text(encoding="utf-8"))["orden"] == ["a", "b"])
        ok("y sí cierra el que de verdad aplicó",
           R.cerrar_orden(d, {"orden": ["a", "b"]}) is True and
           json.loads((d / "notas.json").read_text(encoding="utf-8"))["orden"] == [])

        # los tres se cierran juntos, y basta que uno cambie para no cerrar nada
        tres = {"orden": ["a"], "nuevas": [{"id": "n1", "texto": "x"}], "borradas": ["b"],
                "fusiones": [{"id": "f1", "partes": ["a", "b"], "texto": ""}]}
        (d / "notas.json").write_text(json.dumps(dict(tres, v=1)), encoding="utf-8")
        ok("no cierra si cambió la lista de láminas por escribir",
           R.cerrar_orden(d, dict(tres, nuevas=[])) is False and
           json.loads((d / "notas.json").read_text(encoding="utf-8"))["nuevas"] == tres["nuevas"])
        ok("ni si cambió la de borradas, que es la que puede perder una lámina",
           R.cerrar_orden(d, dict(tres, borradas=[])) is False and
           json.loads((d / "notas.json").read_text(encoding="utf-8"))["borradas"] == ["b"])
        ok("ni si cambiaron las fusiones",
           R.cerrar_orden(d, dict(tres, fusiones=[])) is False and
           json.loads((d / "notas.json").read_text(encoding="utf-8"))["fusiones"] ==
           tres["fusiones"])
        ok("ni si cambió el orden",
           R.cerrar_orden(d, dict(tres, orden=["z"])) is False)
        ok("y cierra los tres a la vez cuando coinciden",
           R.cerrar_orden(d, tres) is True and
           all(not json.loads((d / "notas.json").read_text(encoding="utf-8"))[k]
               for k in ("orden", "nuevas", "borradas", "fusiones")))

        # --- se escribe entero o no se escribe ---
        guardado = (d / "index.html").read_text(encoding="utf-8")
        bak = sorted(d.glob("index.html.bak.orden.*"))[0].read_text(encoding="utf-8")
        real = R.os.replace

        def replace_roto(a, b):
            raise OSError(28, "no space left on device")

        R.os.replace = replace_roto
        try:
            try:
                R.escribir(d / "index.html", guardado,
                           "deck reordenado que no llega a escribirse")
                cayo = False
            except R.Error as e:
                cayo = "no se pudo escribir" in str(e)
        finally:
            R.os.replace = real
        ok("si la escritura falla, avisa con un error legible", cayo)
        ok("y ni el deck ni el respaldo quedan a medias",
           (d / "index.html").read_text(encoding="utf-8") == guardado and
           all(x.read_text(encoding="utf-8") in (bak, guardado, h2)
               for x in d.glob("index.html.bak.orden.*")))
        ok("ni deja temporales tirados",
           not list(d.glob("*.tmp")) and not list(d.glob("*.html.tmp")))

        # --- un deck protegido contra escritura no se sobrescribe ---
        (d / "notas.json").write_text(json.dumps({"v": 1, "orden": list(reversed(ids))}),
                                      encoding="utf-8")
        antes_ro = (d / "index.html").read_text(encoding="utf-8")
        os.chmod(d / "index.html", 0o444)
        try:
            rc = callado([str(d / "index.html")])
        finally:
            os.chmod(d / "index.html", 0o644)
        ok("un deck protegido contra escritura no se toca",
           rc == 1 and (d / "index.html").read_text(encoding="utf-8") == antes_ro)

        # --- notas.json que es JSON válido pero no un documento ---
        (d / "notas.json").write_text("[1, 2, 3]", encoding="utf-8")
        try:
            R.leer_notas(d)
            ok("un notas.json que no es un documento da error", False, "no lanzó error")
        except R.Error as e:
            ok("un notas.json que no es un documento da error",
               "no es un documento" in str(e), str(e))

        # --- decir qué sesión es, de las cuatro maneras ---
        # se prueba contra una sesión del proyecto, no contra la del argumento:
        # nombrarla por su número solo tiene sentido dentro de sesiones/
        suya = sorted((RAIZ / "sesiones").glob("S*/index.html"))
        real_dir = suya[0].parent if suya else None
        ok("la carpeta se encuentra por su ruta, por su nombre y por su número",
           real_dir is not None and
           R.carpeta(str(real_dir)) == real_dir and
           R.carpeta(real_dir.name) == real_dir and
           R.carpeta(str(real_dir / "index.html")) == real_dir and
           R.carpeta(real_dir.name[1:3]) == real_dir, real_dir)
        try:
            R.carpeta("no-existe-esta")
            ok("una sesión inventada da error, no traceback", False, "no lanzó error")
        except R.Error as e:
            ok("una sesión inventada da error, no traceback", "no sé qué sesión" in str(e))
        (d / "notas.json").write_text("{esto no es json", encoding="utf-8")
        try:
            R.leer_notas(d)
            ok("un notas.json ilegible da error, no traceback", False, "no lanzó error")
        except R.Error as e:
            ok("un notas.json ilegible da error, no traceback", "ilegible" in str(e))
        del antes
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cuerpo_js(nombre):
    """El texto de una función de revisar.js, con llaves balanceadas.

    Se extrae del archivo de verdad, no de una copia: lo que se compara contra
    Python tiene que ser lo que corre en el navegador.
    """
    js = (RAIZ / "plantillas" / "tema-centrogeo" / "revisar.js").read_text(encoding="utf-8")
    i = js.index("function " + nombre + "(")
    j = js.index("{", i)
    hondo, k = 0, j
    while k < len(js):
        if js[k] == "{":
            hondo += 1
        elif js[k] == "}":
            hondo -= 1
            if hondo == 0:
                return js[i:k + 1]
        k += 1
    raise ValueError("no encuentro el final de " + nombre)


def prueba_diferencial(res):
    """Las dos reglas están escritas dos veces, en JS y en Python. Tienen que
    decir lo mismo: es lo que hace que la rejilla y el script cuenten igual."""
    def ok(n, c, extra=""):
        res.append(("OK   " if c else "FALLA") + "  " + n +
                   (("  [" + str(extra) + "]") if not c and extra else ""))

    if not shutil.which("node"):
        res.append("OK     (sin node: el diferencial JS contra Python no se corrió)")
        return
    casos = []
    rnd = random.Random(20260922)
    for _ in range(400):
        n = rnd.randint(1, 9)
        deck = ["s%d" % i for i in range(n)]
        pend = deck[:]
        rnd.shuffle(pend)
        # a veces se quita alguna, se inventa otra o se repite una
        if rnd.random() < 0.4 and pend:
            pend.pop(rnd.randrange(len(pend)))
        if rnd.random() < 0.3:
            pend.insert(rnd.randrange(len(pend) + 1), "fantasma")
        if rnd.random() < 0.2 and pend:
            pend.append(pend[0])
        casos.append([pend, deck])
    prog = ("const ORDEN_DECK=[];\nconst idsNuevas = () => [];\n" + cuerpo_js("conciliar") + "\n" +
            cuerpo_js("lasMovidas").replace("const a = ORDEN_DECK", "const a = deck") +
            "\n" + """
    const casos = JSON.parse(process.argv[1]);
    const r = casos.map(([pend, deck]) => {
      ORDEN_DECK.length = 0; deck.forEach((x) => ORDEN_DECK.push(x));
      const c = conciliar(pend);
      return [c, [...lasMovidas(c)]];
    });
    console.log(JSON.stringify(r));
    """).replace("function lasMovidas(quiero)", "function lasMovidas(quiero, deck = ORDEN_DECK)")
    try:
        salida = subprocess.run(["node", "-e", prog, "--", json.dumps(casos)],
                                capture_output=True, text=True, timeout=60)
        suyo = json.loads(salida.stdout)
    except Exception as e:
        res.append("FALLA  el diferencial JS contra Python no pudo correr  [%s]" % e)
        return
    malos_c, malos_m = [], []
    for (pend, deck), (c_js, m_js) in zip(casos, suyo):
        c_py = R.conciliar(pend, deck)
        if c_py != c_js:
            malos_c.append((pend, deck, c_py, c_js))
        m_py = R.lasMovidas(deck, c_py)
        if sorted(m_py) != sorted(m_js):
            malos_m.append((pend, deck, m_py, m_js))
    ok("conciliar dice lo mismo en el navegador y en el script",
       not malos_c, "%d de %d divergen, p.ej. %s" % (len(malos_c), len(casos), malos_c[:1]))
    ok("y cuáles cuentan como movidas, también",
       not malos_m, "%d de %d divergen, p.ej. %s" % (len(malos_m), len(casos), malos_m[:1]))


# --------------------------------------------------------------- lado navegador

# Se inyecta ANTES de revisar.js: deja sembrado un orden pendiente que ya se
# quedó viejo, con un id inventado y sin mencionar una lámina que sí existe, para
# que al cargar haya que conciliarlo. Y una nota sobre la lámina que se va a
# mover, para comprobar que sobrevive al viaje.
SEMILLA = """<script>
window.confirm = () => true;
window.__P = (function () {
  const secs = [...document.querySelectorAll(".reveal .slides > section")];
  const ids = secs.map((s) => s.dataset.sid || s.id);
  // pendiente: la penúltima al frente, un id que no existe, y sin la segunda
  const pend = [ids[ids.length - 2], "lamina-que-ya-no-existe"]
      .concat(ids.filter((x, i) => i !== ids.length - 2 && i !== 1));
  const espera = [ids[ids.length - 2], ids[0], ids[1]]
      .concat(ids.filter((x, i) => i > 1 && i !== ids.length - 2));
  localStorage.setItem("orden:__DECK__", JSON.stringify(pend));
  // dos láminas con la marca puesta en el HTML, como las deja reordenar.py:
  // sirven para comprobar que una fusión ya aplicada no cuenta como pendiente
  secs[14].setAttribute("data-combinar", ids[15]);
  secs[15].setAttribute("data-combinar-en", ids[14]);
  localStorage.setItem("fusiones:__DECK__", JSON.stringify([
    { id: "fusion-ya", partes: [ids[14], ids[15]], texto: "ya aplicada", ts: "2026-09-23T00:00" },
  ]));
  const conNota = ids[2];
  const sec = secs[2];
  const li = sec.querySelector(".cuerpo li, h2, h1");
  const cita = li ? li.textContent.replace(/\\s+/g, " ").trim().slice(0, 30) : "";
  localStorage.setItem("revision:__DECK__", JSON.stringify({
    [conNota]: [{ nid: "nOrden", cita, nth: 1, texto: "nota de la lámina que se mueve",
                  ambito: "lamina", ts: "2026-09-22T10:00" }] }));
  return { ids, pend, espera, conNota, cita, n: ids.length,
           yaComb: [ids[14], ids[15]] };
})();
</script>
"""

PRUEBA = """<script>
const R = [];
const ok = (n, c, extra) => R.push((c ? "OK   " : "FALLA") + "  " + n + (extra && !c ? "  [" + extra + "]" : ""));
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
const P = window.__P;
const tecla = (k, code) => document.dispatchEvent(new KeyboardEvent("keydown",
  { key: k, keyCode: code, which: code, bubbles: true, cancelable: true }));
const raton = (tipo, x, y, el) => (el || document).dispatchEvent(new MouseEvent(tipo,
  { bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0 }));
// Ojo: cada miniatura es un .reveal con sus .slides dentro, así que un selector
// suelto contaría también las láminas clonadas de la rejilla. El deck de verdad
// es el primero que hay, y se captura antes de abrir nada.
const PISTA = document.querySelector(".reveal .slides");
const enDeck = () => [...PISTA.children].filter((x) => x.tagName === "SECTION")
  .map((s) => s.dataset.sid || s.id);
// Ojo: la copia que sigue al cursor mientras se arrastra es un clon de la celda
// y vive en el body, fuera de la malla. Se cuentan solo las de la malla.
const celdas = () => [...document.querySelectorAll(".rv-rj-lienzo > .rv-rj-cel")];
const enRejilla = () => celdas().map((c) => c.dataset.sid);
const guardado = () => { try { return JSON.parse(localStorage.getItem("orden:__DECK__")) || []; }
                         catch (e) { return ["ilegible"]; } };
const mismos = (a, b) => a.length === b.length && a.every((x, i) => x === b[i]);

// Agarra la celda i y lleva el cursor a la mitad izquierda de la celda j, sin
// soltar: así se puede mirar la línea de inserción a mitad del arrastre.
async function agarrar(i, j, derecha) {
  const c = celdas()[i], d = celdas()[j];
  d.scrollIntoView({ block: "center" });
  await dormir(40);
  const rc = c.getBoundingClientRect(), rd = d.getBoundingClientRect();
  const x = derecha ? rd.right - 4 : rd.left + 3, y = rd.top + 20;
  raton("mousedown", rc.left + 12, rc.top + 12, c);
  raton("mousemove", rc.left + 40, rc.top + 40);
  await dormir(30);
  raton("mousemove", x, y);
  await dormir(30);
  return { x, y };
}

// La lámina que la línea deja a su derecha, leída de la línea dibujada y no de
// lo que la prueba supone: es con la que se comprueba dónde cayó.
const vecinaDeLaLinea = () => {
  const l = document.querySelector(".rv-rj-linea");
  if (!l) return null;
  const r = l.getBoundingClientRect();
  const bajo = document.elementFromPoint(r.right + 20, r.top + 20);
  const c = bajo && bajo.closest && bajo.closest(".rv-rj-lienzo > .rv-rj-cel");
  return c ? c.dataset.sid : null;
};

// El arrastre entero. Si cancelar, se suelta con Escape en vez de con el botón.
async function arrastrar(i, j, cancelar) {
  const p = await agarrar(i, j);
  if (cancelar) tecla("Escape", 27);
  else raton("mouseup", p.x, p.y);
  await dormir(120);
}

const ctrlZ = (donde) => (donde || document).dispatchEvent(new KeyboardEvent("keydown",
  { key: "z", keyCode: 90, which: 90, ctrlKey: true, bubbles: true, cancelable: true }));

(async () => {
 try {
  await dormir(700);
  ok("la semilla encontró láminas con id", !!P && P.n > 5, P && P.n);

  /* ---- al cargar: el orden pendiente se concilia y se ve en el deck ---- */
  ok("el deck arranca en el orden pendiente, ya conciliado",
     mismos(enDeck(), P.espera), enDeck().slice(0, 3) + " vs " + P.espera.slice(0, 3));
  const chapa = () => {
    const b = document.querySelector(".rv-barra .rv-orden");
    return b ? b.textContent : "";
  };
  ok("la barra avisa de que el orden no está aplicado",
     chapa() === "sin aplicar: 1 movida", chapa());
  ok("la nota de la lámina movida sigue resaltada",
     document.querySelectorAll('mark.rv-hl[data-nid~="nOrden"]').length > 0);

  ok("una fusión que el HTML ya dice no cuenta como pendiente",
     !/por combinar/.test(document.querySelector(".rv-barra").textContent),
     document.querySelector(".rv-barra").textContent.slice(0, 70));

  /* ---- la rejilla ---- */
  tecla("R", 82);
  await dormir(400);
  const rej = document.querySelector(".rv-rejilla");
  ok("R abre la rejilla", !!rej);
  ok("la rejilla trae todas las láminas, en el orden del deck",
     mismos(enRejilla(), enDeck()), enRejilla().length + " de " + P.n);
  const limpio = (x) => x.textContent.replace(/\\s+/g, " ").trim();
  ok("cada miniatura es un clon vivo de su lámina",
     celdas().every((c) => c.querySelector(".rv-mini .slides > section")) &&
     celdas().every((c, i) => {
       const sec = [...PISTA.children].filter((x) => x.tagName === "SECTION")[i];
       const copia = sec.cloneNode(true);
       [...copia.querySelectorAll("aside")].forEach((a) => a.remove());
       return limpio(c.querySelector(".rv-mini")).slice(0, 40) ===
              limpio(copia).slice(0, 40);
     }), limpio(celdas()[0].querySelector(".rv-mini")).slice(0, 40));
  ok("las miniaturas no llevan el guion de orador dentro",
     document.querySelectorAll(".rv-rejilla aside.notes").length === 0);
  ok("las láminas movidas están marcadas y dicen de dónde vienen",
     celdas()[0].classList.contains("rv-rj-movida") &&
     /antes /.test(celdas()[0].querySelector(".rv-rj-mov").textContent));
  // el conjunto exacto, no "menos que todas": el orden sembrado sube al frente
  // una sola lámina, así que esa y solo esa puede estar marcada
  ok("las marcadas son exactamente las que se movieron",
     JSON.stringify(celdas().filter((c) => c.classList.contains("rv-rj-movida"))
                            .map((c) => c.dataset.sid)) ===
     JSON.stringify([P.ids[P.ids.length - 2]]),
     celdas().filter((c) => c.classList.contains("rv-rj-movida")).map((c) => c.dataset.sid));
  ok("la numeración va de 1 en adelante",
     celdas()[0].querySelector(".rv-rj-num").textContent === "1" &&
     celdas()[3].querySelector(".rv-rj-num").textContent === "4");

  /* ---- arrastrar de verdad ---- */
  const antes = enRejilla();
  const testigoUno = antes.slice();   // el estado de partida, para el segundo Ctrl+Z
  await arrastrar(4, 1, false);
  const esperado = [antes[0], antes[4]].concat(antes.filter((x, i) => i !== 0 && i !== 4));
  ok("arrastrar cambia el sitio en la rejilla", mismos(enRejilla(), esperado),
     enRejilla().slice(0, 5) + " vs " + esperado.slice(0, 5));
  ok("y lo cambia también en el deck de verdad", mismos(enDeck(), esperado),
     enDeck().slice(0, 5));
  ok("el orden nuevo queda guardado", mismos(guardado(), esperado), guardado().slice(0, 3));
  ok("la numeración se pone al día sola",
     celdas()[1].querySelector(".rv-rj-num").textContent === "2");
  ok("la lámina que se movió queda marcada",
     celdas()[1].classList.contains("rv-rj-movida"));
  ok("no queda ningún fantasma colgando",
     document.querySelectorAll(".rv-rj-fantasma").length === 0 &&
     document.querySelectorAll(".rv-rj-hueco").length === 0);
  ok("la nota sigue pegada a su lámina después de moverla",
     (JSON.parse(localStorage.getItem("revision:__DECK__"))[P.conNota] || []).length === 1);

  /* ---- la línea de inserción, mientras se arrastra ---- */
  const antesL = enRejilla();
  const punto = await agarrar(4, 1);
  const linea = document.querySelector(".rv-rj-linea");
  ok("mientras se arrastra se dibuja una línea de inserción", !!linea);
  ok("la lámina agarrada se queda en su sitio, atenuada",
     celdas()[4].classList.contains("rv-rj-tirando") &&
     mismos(enRejilla(), antesL) && mismos(enDeck(), antesL),
     enRejilla().slice(0, 5));
  ok("la malla no se recoloca hasta soltar",
     celdas()[1].dataset.sid === antesL[1]);
  const rd1 = celdas()[1].getBoundingClientRect();
  const rl1 = linea.getBoundingClientRect();
  ok("la línea cae en el hueco de antes de la lámina de destino",
     Math.abs(rl1.left - (rd1.left - 10)) < 8 && Math.abs(rl1.top - rd1.top) < 8,
     Math.round(rl1.left) + "," + Math.round(rl1.top) + " vs " +
     Math.round(rd1.left) + "," + Math.round(rd1.top));
  ok("y es vertical, tan alta como la lámina",
     rl1.height > rl1.width * 5 && Math.abs(rl1.height - rd1.height) < 8,
     Math.round(rl1.width) + "x" + Math.round(rl1.height));
  raton("mouseup", punto.x, punto.y);
  await dormir(150);
  const esperadoL = [antesL[0], antesL[4]].concat(antesL.filter((x, i) => i !== 0 && i !== 4));
  ok("al soltar, la lámina cae donde decía la línea", mismos(enRejilla(), esperadoL),
     enRejilla().slice(0, 5) + " vs " + esperadoL.slice(0, 5));
  ok("y la línea se va con ella",
     !document.querySelector(".rv-rj-linea") &&
     !document.querySelector(".rv-rj-tirando"));

  /* ---- soltar en la mitad derecha mete la lámina detrás ---- */
  const antesD = enRejilla();
  const pd = await agarrar(6, 1, true);
  const rdD = celdas()[1].getBoundingClientRect();
  const rlD = document.querySelector(".rv-rj-linea").getBoundingClientRect();
  ok("soltando en la mitad derecha, la línea se dibuja al otro lado de la lámina",
     Math.abs(rlD.left - (rdD.right + 6)) < 10,
     Math.round(rlD.left) + " vs " + Math.round(rdD.right + 6));
  const vecina = vecinaDeLaLinea();
  raton("mouseup", pd.x, pd.y);
  await dormir(150);
  const trasD = enRejilla();
  ok("y la lámina cae detrás de aquella sobre la que se soltó",
     trasD[2] === antesD[6] && trasD[1] === antesD[1], trasD.slice(0, 4));
  ok("justo antes de la que la línea dejaba a su derecha",
     vecina && trasD[trasD.indexOf(antesD[6]) + 1] === vecina, vecina);

  /* ---- y al final de la fila, al final del deck ---- */
  const antesU = enRejilla();
  const pu = await agarrar(1, antesU.length - 1, true);
  const rU = celdas()[celdas().length - 1].getBoundingClientRect();
  const rlU = document.querySelector(".rv-rj-linea").getBoundingClientRect();
  ok("soltando detrás de la última, la línea se dibuja a su derecha",
     rlU.left > rU.right - 2 && Math.abs(rlU.left - (rU.right + 6)) < 10,
     Math.round(rlU.left) + " vs " + Math.round(rU.right + 6));
  ok("y ahí no hay ninguna lámina a la derecha de la línea", !vecinaDeLaLinea());
  raton("mouseup", pu.x, pu.y);
  await dormir(150);
  ok("la lámina acaba de última", enRejilla()[enRejilla().length - 1] === antesU[1] &&
     enRejilla().length === P.n, enRejilla().slice(-2));
  ctrlZ();
  await dormir(200);
  ctrlZ();
  await dormir(200);
  ok("y los dos se deshacen", mismos(enRejilla(), antesD), enRejilla().slice(0, 4));

  /* ---- Ctrl+Z a mitad de un arrastre no rompe la malla ---- */
  const antesCancel = enRejilla();
  await agarrar(3, 8);
  ctrlZ();
  await dormir(200);
  ok("Ctrl+Z con un arrastre a medias lo cancela y no deshace nada más",
     mismos(enRejilla(), antesCancel) && !document.querySelector(".rv-rj-linea"),
     enRejilla().slice(0, 4));
  raton("mousemove", 500, 400);
  raton("mouseup", 500, 400);
  await dormir(200);
  const tras = enRejilla();
  ok("Ctrl+Z a mitad de un arrastre no duplica ni pierde láminas",
     tras.length === P.n && new Set(tras).size === P.n, tras.length + " celdas");
  ok("ni deja el orden guardado con repetidos",
     new Set(guardado()).size === guardado().length &&
     (guardado().length === 0 || guardado().length === P.n), guardado().length);
  ok("ni deja copia o línea colgando",
     !document.querySelector(".rv-rj-fantasma") && !document.querySelector(".rv-rj-linea") &&
     !document.querySelector(".rv-rj-tirando"));

  /* ---- Ctrl+Z ---- */
  ok("el botón de deshacer lleva la cuenta de los pasos",
     /Deshacer \\(\\d+\\)/.test(
       document.querySelector('.rv-rj-barra [data-rj="atras"]').textContent),
     document.querySelector('.rv-rj-barra [data-rj="atras"]').textContent);
  ctrlZ();
  await dormir(200);
  ok("Ctrl+Z deshace el último movimiento", mismos(enRejilla(), antesL),
     enRejilla().slice(0, 5) + " vs " + antesL.slice(0, 5));
  ok("y lo deshace también en el deck y en lo guardado",
     mismos(enDeck(), antesL) &&
     (guardado().length === 0 ? mismos(antesL, P.ids) : mismos(guardado(), antesL)),
     guardado().slice(0, 3));
  ctrlZ();
  await dormir(200);
  ok("otro Ctrl+Z deshace el movimiento anterior", mismos(enRejilla(), testigoUno),
     enRejilla().slice(0, 5) + " vs " + testigoUno.slice(0, 5));

  // con el foco en una caja de texto, Ctrl+Z es de quien escribe
  const antesDelTres = enRejilla();
  await arrastrar(3, 0, false);
  const trasArrastre = enRejilla();
  ok("el arrastre de control cambió algo", !mismos(trasArrastre, antesDelTres));
  const caja = document.createElement("textarea");
  document.body.appendChild(caja);
  caja.focus();
  ctrlZ(caja);
  await dormir(150);
  ok("escribiendo en una caja de texto, Ctrl+Z no toca el orden",
     mismos(enRejilla(), trasArrastre), enRejilla().slice(0, 4));
  caja.remove();

  // con la rejilla abierta la tecla es suya aunque el pincel esté encendido:
  // la rejilla tapa la lámina, así que debajo no se está dibujando nada
  document.body.classList.add("pn-activo");
  ctrlZ();
  await dormir(200);
  ok("con la rejilla abierta, Ctrl+Z deshace aunque el pincel esté encendido",
     mismos(enRejilla(), antesDelTres), enRejilla().slice(0, 4) + " vs " +
     antesDelTres.slice(0, 4));

  // pero con la rejilla cerrada, el pincel manda. Hace falta un movimiento
  // nuevo que deshacer, porque el de antes ya se deshizo.
  await arrastrar(2, 6, false);
  const cerrada = enRejilla();
  tecla("R", 82);
  await dormir(250);
  ok("la rejilla se cerró para probar la tecla fuera de ella",
     !document.querySelector(".rv-rejilla"));
  ctrlZ();
  await dormir(200);
  ok("con la rejilla cerrada y el pincel encendido, la tecla es del pincel",
     mismos(enDeck(), cerrada), enDeck().slice(0, 4));
  document.body.classList.remove("pn-activo");
  ctrlZ();
  await dormir(250);
  ok("y apagado el pincel, deshace también con la rejilla cerrada",
     mismos(enDeck(), antesDelTres), enDeck().slice(0, 4) + " vs " +
     antesDelTres.slice(0, 4));
  tecla("R", 82);
  await dormir(400);
  ok("y la rejilla se reabre con lo deshecho puesto",
     mismos(enRejilla(), antesDelTres), enRejilla().slice(0, 4));

  /* ---- deshacer más veces que movimientos ---- */
  for (let k = 0; k < 25; k++) { ctrlZ(); await dormir(40); }
  await dormir(200);
  const vacia = enRejilla();
  ok("deshacer de más no rompe nada",
     vacia.length === P.n && new Set(vacia).size === P.n, vacia.length);
  ok("y el botón de deshacer se queda sin cuenta y apagado",
     document.querySelector('.rv-rj-barra [data-rj="atras"]').disabled &&
     document.querySelector('.rv-rj-barra [data-rj="atras"]').textContent === "Deshacer",
     document.querySelector('.rv-rj-barra [data-rj="atras"]').textContent);

  /* ---- insertar una lámina por escribir ---- */
  const pulsar = (el) => el.dispatchEvent(new MouseEvent("click",
    { bubbles: true, cancelable: true }));
  const enPista = (sid) => [...PISTA.children].find(
    (x) => x.tagName === "SECTION" && (x.dataset.sid || x.id) === sid) || null;

  const antesN = enRejilla();
  const trasCual = celdas()[1].dataset.sid;
  pulsar(celdas()[1].querySelector('[data-rj="mas"]'));
  await dormir(300);
  const cajaN = document.querySelector(".rv-capa");
  ok("el botón + abre la caja del encargo", !!cajaN && !!cajaN.querySelector("textarea"));
  cajaN.querySelector("textarea").value = "Un ejemplo geoespacial con tres reglas.";
  pulsar(cajaN.querySelector('[data-rv="guardar"]'));
  await dormir(400);
  const conNueva = enRejilla();
  const nid = conNueva[conNueva.indexOf(trasCual) + 1];
  ok("la lámina nueva queda detrás de aquella donde se pulsó",
     conNueva.length === antesN.length + 1 && /^nueva-/.test(nid || ""), nid);
  ok("y está también en el deck, marcada como pendiente",
     !!enPista(nid) && enPista(nid).dataset.pendiente === "1");
  ok("con el encargo escrito dentro",
     /tres reglas/.test((enPista(nid).querySelector(".rv-encargo") || {}).textContent || ""),
     (enPista(nid).textContent || "").slice(0, 60));
  ok("la celda la marca como por escribir",
     celdas()[conNueva.indexOf(nid)].classList.contains("rv-rj-nueva"));
  ok("y la barra la cuenta", /1 por escribir/.test(chapa()), chapa());
  ok("la miniatura de la rejilla enseña la lámina nueva",
     /por escribir/i.test(celdas()[conNueva.indexOf(nid)]
       .querySelector(".rv-mini").textContent));

  // pinchar una lámina por escribir abre su encargo, no navega
  pulsar(celdas()[conNueva.indexOf(nid)].querySelector(".rv-mini"));
  await dormir(100);
  const cel = celdas()[conNueva.indexOf(nid)];
  const rr = cel.getBoundingClientRect();
  raton("mousedown", rr.left + 12, rr.top + 60, cel);
  raton("mouseup", rr.left + 12, rr.top + 60);
  await dormir(300);
  const reabre = document.querySelector(".rv-capa");
  ok("pinchar una lámina por escribir reabre su encargo y no cierra la rejilla",
     !!reabre && !!document.querySelector(".rv-rejilla"));
  ok("y la caja trae lo que ya se había escrito",
     /tres reglas/.test(reabre ? reabre.querySelector("textarea").value : ""));
  if (reabre) pulsar(reabre.querySelector('[data-rv="cancelar"]'));
  await dormir(150);

  // Ctrl+Z: primero el encargo escrito, después la lámina entera
  ctrlZ();
  await dormir(250);
  ok("Ctrl+Z deshace lo escrito en el encargo y deja la lámina",
     enRejilla().includes(nid) &&
     /Sin descripción/.test(enPista(nid).querySelector(".rv-encargo").textContent));
  ctrlZ();
  await dormir(250);
  ok("y otro Ctrl+Z se lleva la lámina por escribir",
     !enRejilla().includes(nid) && !enPista(nid) && mismos(enRejilla(), antesN),
     enRejilla().length);
  ok("la barra deja de contarla", !/por escribir/.test(chapa()), chapa());

  // el botón del final la pone al final del todo
  pulsar(document.querySelector('.rv-rejilla [data-rj="mas-final"]'));
  await dormir(300);
  const cajaF = document.querySelector(".rv-capa");
  if (cajaF) pulsar(cajaF.querySelector('[data-rv="guardar"]'));
  await dormir(300);
  const ultima = enRejilla()[enRejilla().length - 1];
  ok("el botón del final añade la lámina detrás de la última",
     /^nueva-/.test(ultima || ""), enRejilla().slice(-2));
  ok("y también en el deck, la última de verdad y marcada",
     !!enPista(ultima) && enPista(ultima).dataset.pendiente === "1" &&
     enDeck()[enDeck().length - 1] === ultima, enDeck().slice(-2));
  ctrlZ();
  await dormir(250);
  ok("y Ctrl+Z la quita", mismos(enRejilla(), antesN), enRejilla().length);

  /* ---- borrar una lámina ---- */
  const antesB = enRejilla();
  const victima = antesB[2];
  pulsar(celdas()[2].querySelector('[data-rj="quitar"]'));
  await dormir(350);
  ok("la lámina marcada sale del deck", !enPista(victima), victima);
  ok("pero se queda en la rejilla, marcada, para poder arrepentirse",
     enRejilla().includes(victima) && celdas()[2].classList.contains("rv-rj-borrada"));
  ok("la celda borrada no lleva número y las de después no lo saltan",
     celdas()[2].querySelector(".rv-rj-num").textContent === "" &&
     celdas()[3].querySelector(".rv-rj-num").textContent === "3");
  ok("y la barra la cuenta", /1 por borrar/.test(chapa()), chapa());

  pulsar(celdas()[2].querySelector('[data-rj="quitar"]'));
  await dormir(350);
  ok("el botón ↺ la devuelve a su sitio exacto",
     !!enPista(victima) && enDeck()[2] === victima, enDeck().slice(0, 4));

  pulsar(celdas()[2].querySelector('[data-rj="quitar"]'));
  await dormir(350);
  ok("se puede volver a marcar, y la celda lo vuelve a decir entera",
     !enPista(victima) && celdas()[2].classList.contains("rv-rj-borrada") &&
     celdas()[2].querySelector(".rv-rj-num").textContent === "" &&
     /1 por borrar/.test(chapa()), chapa());
  ok("y el botón ofrece devolverla, con su símbolo",
     celdas()[2].querySelector('[data-rj="quitar"]').textContent === "↺",
     celdas()[2].querySelector('[data-rj="quitar"]').textContent);
  ctrlZ();
  await dormir(300);
  ok("y Ctrl+Z deshace el borrado, también en su sitio",
     !!enPista(victima) && enDeck()[2] === victima && mismos(enRejilla(), antesB),
     enDeck().slice(0, 4));

  /* ---- borrar e insertar a la vez, y deshacer mezclado ---- */
  const base = enRejilla();
  const aBorrar = base[4];
  pulsar(celdas()[4].querySelector('[data-rj="quitar"]'));
  await dormir(300);
  pulsar(celdas()[4].querySelector('[data-rj="mas"]'));      // detrás de la borrada
  await dormir(300);
  const cajaM = document.querySelector(".rv-capa");
  if (cajaM) {
    cajaM.querySelector("textarea").value = 'Con <b>etiquetas</b> & "comillas".';
    pulsar(cajaM.querySelector('[data-rv="guardar"]'));
  }
  await dormir(400);
  const mezcla = enRejilla();
  const nid2 = mezcla[5];
  ok("se puede insertar una lámina justo detrás de una marcada para borrar",
     /^nueva-/.test(nid2 || "") && mezcla[4] === aBorrar && !enPista(aBorrar),
     mezcla.slice(3, 7));
  ok("el encargo con etiquetas y comillas se guarda tal cual, sin romper nada",
     /<b>etiquetas<\\/b> & "comillas"/.test(
       enPista(nid2).querySelector(".rv-encargo").textContent),
     (enPista(nid2).querySelector(".rv-encargo") || {}).textContent);
  ok("y la barra cuenta las dos cosas",
     /1 por escribir/.test(chapa()) && /1 por borrar/.test(chapa()), chapa());

  // una lámina por escribir se arrastra como cualquier otra
  await arrastrar(5, 0, false);
  ok("una lámina por escribir se arrastra a otra posición",
     enRejilla()[0] === nid2 && enDeck()[0] === nid2, enRejilla().slice(0, 3));

  // y las tres cosas se deshacen en orden inverso
  ctrlZ();
  await dormir(250);
  ok("Ctrl+Z deshace el arrastre de la lámina por escribir",
     enRejilla()[5] === nid2, enRejilla().slice(3, 7));
  ctrlZ();
  await dormir(250);
  ok("otro deshace el encargo escrito",
     /Sin descripción/.test(enPista(nid2).querySelector(".rv-encargo").textContent));
  ctrlZ();
  await dormir(250);
  ok("otro se lleva la lámina por escribir", !enRejilla().includes(nid2));
  ctrlZ();
  await dormir(250);
  ok("y el último deshace el borrado, dejándolo todo como estaba",
     mismos(enRejilla(), base) && !!enPista(aBorrar), enRejilla().slice(3, 7));

  // el botón de descartar está vivo aunque solo haya una lámina por borrar
  pulsar(celdas()[4].querySelector('[data-rj="quitar"]'));
  await dormir(300);
  const bd2 = document.querySelector('.rv-rj-barra [data-rj="deshacer"]');
  ok("Descartar los cambios se puede pulsar con solo un borrado pendiente",
     !bd2.disabled);
  pulsar(bd2);
  await dormir(350);
  // descartar deja el deck como dice el HTML, que es más que deshacer el borrado
  ok("y descarta el borrado, dejando el deck como dice el HTML",
     !!enPista(aBorrar) && mismos(enDeck(), P.ids) && chapa() === "",
     chapa() + " | " + enDeck().slice(0, 3));
  ctrlZ();
  await dormir(300);
  ok("y Ctrl+Z devuelve lo descartado", !enPista(aBorrar));
  ctrlZ();
  await dormir(300);

  ok("pero la lámina ya marcada en el deck lo dice en su celda",
     (() => {
       const c = celdas().find((x) => x.dataset.sid === P.yaComb[0]);
       return !!c && !c.querySelector('[data-rj="fusion"]').hidden &&
              /ya marcada/.test(c.querySelector('[data-rj="fusion"]').textContent);
     })(), "sin chapa");

  /* ---- combinar láminas ---- */
  const conMod = (cel, mod) => {
    const r = cel.getBoundingClientRect();
    const op = { bubbles: true, cancelable: true, clientX: r.left + 12, clientY: r.top + 60,
                 button: 0 };
    op[mod] = true;
    cel.dispatchEvent(new MouseEvent("mousedown", op));
    document.dispatchEvent(new MouseEvent("mouseup", op));
  };
  const botonComb = () => document.querySelector('.rv-rj-barra [data-rj="combinar"]');
  const soltarSel = async () => {
    const c = celdas()[9], r = c.getBoundingClientRect();
    raton("mousedown", r.left + 12, r.top + 60, c);
    raton("mouseup", r.left + 12, r.top + 60);
    await dormir(120);
  };

  const antesF = enRejilla();
  conMod(celdas()[1], "ctrlKey");
  await dormir(120);
  ok("Ctrl+clic selecciona una lámina sin navegar",
     celdas()[1].classList.contains("rv-rj-sel") && !!document.querySelector(".rv-rejilla"));
  ok("con una sola seleccionada todavía no se ofrece combinar", botonComb().hidden);
  conMod(celdas()[6], "ctrlKey");
  await dormir(120);
  ok("y se pueden seleccionar láminas que no son contiguas",
     celdas()[6].classList.contains("rv-rj-sel") &&
     celdas().filter((c) => c.classList.contains("rv-rj-sel")).length === 2);
  ok("con dos, aparece el botón de combinar",
     !botonComb().hidden && /Combinar en una \\(2\\)/.test(botonComb().textContent),
     botonComb().textContent);

  pulsar(botonComb());
  await dormir(350);
  const cajaC = document.querySelector(".rv-capa");
  ok("combinar abre la caja de la nota, que es opcional",
     !!cajaC && !!cajaC.querySelector("textarea") &&
     /Combinar 2 láminas/.test(cajaC.textContent), (cajaC || {}).textContent);
  cajaC.querySelector("textarea").value = "Quédate con el ejemplo del final.";
  pulsar(cajaC.querySelector('[data-rv="guardar"]'));
  await dormir(400);
  ok("las dos láminas quedan marcadas como combinables, y en su sitio",
     mismos(enRejilla(), antesF) &&
     celdas()[1].classList.contains("rv-rj-fusionada") &&
     celdas()[6].classList.contains("rv-rj-fusionada"), enRejilla().slice(0, 3));
  ok("la chapa dice cuál es cuál",
     celdas()[1].querySelector('[data-rj="fusion"]').textContent === "combina 1 de 2" &&
     celdas()[6].querySelector('[data-rj="fusion"]').textContent === "combina 2 de 2",
     celdas()[1].querySelector('[data-rj="fusion"]').textContent);
  ok("las dos siguen en el deck, marcadas, que combinar no es borrar",
     !!enPista(antesF[1]) && !!enPista(antesF[6]) &&
     enPista(antesF[1]).classList.contains("rv-fusion"));
  ok("la barra las cuenta", /1 por combinar/.test(chapa()), chapa());
  ok("y la selección se suelta al combinar",
     celdas().filter((c) => c.classList.contains("rv-rj-sel")).length === 0);

  // la chapa reabre la fusión, y desde ahí se saca una lámina o se deshace
  pulsar(celdas()[1].querySelector('[data-rj="fusion"]'));
  await dormir(300);
  const cajaG = document.querySelector(".rv-capa");
  ok("la chapa reabre la fusión con su nota",
     !!cajaG && /ejemplo del final/.test(cajaG.querySelector("textarea").value));
  pulsar(cajaG.querySelector('[data-rv="romper"]'));
  await dormir(350);
  ok("y se puede deshacer entera",
     !celdas()[1].classList.contains("rv-rj-fusionada") && !/por combinar/.test(chapa()),
     chapa());
  ctrlZ();
  await dormir(300);
  ok("Ctrl+Z devuelve la fusión deshecha",
     celdas()[1].classList.contains("rv-rj-fusionada"), chapa());
  ctrlZ();
  await dormir(300);
  ok("y otro Ctrl+Z deshace la nota escrita",
     celdas()[1].classList.contains("rv-rj-fusionada"));
  ctrlZ();
  await dormir(300);
  ok("y el siguiente se lleva la fusión entera",
     !celdas()[1].classList.contains("rv-rj-fusionada") && !/por combinar/.test(chapa()),
     chapa());

  // sacar una lámina de una fusión de tres
  conMod(celdas()[1], "ctrlKey");
  conMod(celdas()[2], "ctrlKey");
  conMod(celdas()[6], "ctrlKey");
  await dormir(150);
  pulsar(botonComb());
  await dormir(350);
  const cajaT = document.querySelector(".rv-capa");
  if (cajaT) pulsar(cajaT.querySelector('[data-rv="cancelar"]'));
  await dormir(300);
  ok("se pueden combinar tres láminas",
     celdas()[1].querySelector('[data-rj="fusion"]').textContent === "combina 1 de 3" &&
     celdas()[6].querySelector('[data-rj="fusion"]').textContent === "combina 3 de 3");
  pulsar(celdas()[2].querySelector('[data-rj="fusion"]'));
  await dormir(300);
  const cajaS = document.querySelector(".rv-capa");
  pulsar(cajaS.querySelector('[data-rv="sacar"]'));
  await dormir(350);
  ok("y se puede sacar una de ellas, quedándose las otras dos",
     !celdas()[2].classList.contains("rv-rj-fusionada") &&
     celdas()[1].querySelector('[data-rj="fusion"]').textContent === "combina 1 de 2" &&
     celdas()[6].querySelector('[data-rj="fusion"]').textContent === "combina 2 de 2");
  // y marcar una parte para borrar la saca de la fusión, que si no el encargo
  // apuntaría a una lámina que se va
  pulsar(celdas()[6].querySelector('[data-rj="quitar"]'));
  await dormir(350);
  ok("borrar una parte deshace la combinación que se queda coja",
     !celdas()[1].classList.contains("rv-rj-fusionada") &&
     !/por combinar/.test(chapa()) && /1 por borrar/.test(chapa()), chapa());
  ctrlZ();
  await dormir(300);
  ok("y Ctrl+Z devuelve la lámina y la combinación de una vez",
     celdas()[1].classList.contains("rv-rj-fusionada") && !/por borrar/.test(chapa()),
     chapa());
  pulsar(celdas()[1].querySelector('[data-rj="fusion"]'));
  await dormir(300);
  const cajaR = document.querySelector(".rv-capa");
  pulsar(cajaR.querySelector('[data-rv="romper"]'));
  await dormir(350);

  // Shift+clic marca el tramo
  conMod(celdas()[2], "ctrlKey");
  await dormir(100);
  conMod(celdas()[5], "shiftKey");
  await dormir(150);
  ok("Shift+clic marca el tramo entero",
     celdas().filter((c) => c.classList.contains("rv-rj-sel")).length === 4,
     celdas().filter((c) => c.classList.contains("rv-rj-sel")).length);
  // un clic normal suelta la selección
  const cl = celdas()[8];
  const rcl = cl.getBoundingClientRect();
  raton("mousedown", rcl.left + 12, rcl.top + 60, cl);
  raton("mouseup", rcl.left + 12, rcl.top + 60);
  await dormir(200);
  ok("un clic normal suelta la selección y no navega",
     celdas().filter((c) => c.classList.contains("rv-rj-sel")).length === 0 &&
     !!document.querySelector(".rv-rejilla"));

  // una lámina marcada para borrar no entra en la selección
  pulsar(celdas()[3].querySelector('[data-rj="quitar"]'));
  await dormir(300);
  conMod(celdas()[3], "ctrlKey");
  await dormir(150);
  ok("una lámina marcada para borrar no se deja seleccionar",
     !celdas()[3].classList.contains("rv-rj-sel"));
  conMod(celdas()[4], "ctrlKey");
  await dormir(150);
  ok("y con una sola seleccionada el botón de combinar no se ofrece",
     celdas()[4].classList.contains("rv-rj-sel") && botonComb().hidden);
  ctrlZ();
  await dormir(250);
  await soltarSel();
  await dormir(150);

  /* ---- los fondos de reveal siguen siendo los de cada lámina ---- */
  tecla("R", 82);            // la rejilla estaba abierta: se cierra para mirar el deck
  await dormir(200);
  const fondos = () => [...document.querySelectorAll(
    ".reveal > .backgrounds > .slide-background")];
  ok("reveal rehizo un fondo por lámina al reordenar",
     fondos().length === P.n, fondos().length + " de " + P.n);
  Reveal.slide(2);
  await dormir(200);
  const sec2 = Reveal.getCurrentSlide();
  const quiere = (sec2.dataset.backgroundImage || "").split("/").pop();
  const puesto = document.querySelector(
    ".reveal > .backgrounds > .slide-background.present");
  ok("y el que se ve es el de la lámina en la que estamos",
     !quiere || (puesto && puesto.style.backgroundImage.includes(quiere)),
     quiere + " vs " + (puesto ? puesto.style.backgroundImage : "(ninguno)"));
  ok("la lámina en curso es la que dice el índice",
     (sec2.dataset.sid || sec2.id) === enDeck()[2], enDeck()[2]);
  tecla("R", 82);            // y se vuelve a abrir para seguir arrastrando
  await dormir(400);
  ok("la rejilla vuelve a abrirse con el deck ya reordenado",
     celdas().length === P.n && mismos(enRejilla(), enDeck()), celdas().length);

  /* ---- arrastrar una lámina sobre sí misma no cambia nada ---- */
  const igual = enRejilla();
  await arrastrar(2, 2, false);
  ok("arrastrar una lámina sobre sí misma no cambia nada",
     mismos(enRejilla(), igual) && mismos(enDeck(), igual), enRejilla().slice(0, 4));

  /* ---- soltar fuera de la malla deja la lámina donde estaba ---- */
  const antesFuera = enRejilla();
  const cf = celdas()[2];
  const rf = cf.getBoundingClientRect();
  raton("mousedown", rf.left + 12, rf.top + 12, cf);
  raton("mousemove", rf.left + 50, rf.top + 50);
  await dormir(30);
  raton("mousemove", 4, 4);              // la barra de arriba, fuera de la malla
  await dormir(30);
  raton("mouseup", 4, 4);
  await dormir(120);
  ok("soltar fuera de la malla no descoloca nada",
     mismos(enRejilla(), antesFuera) && mismos(enDeck(), antesFuera) &&
     document.querySelectorAll(".rv-rj-fantasma").length === 0,
     enRejilla().slice(0, 4));

  /* ---- Escape a mitad de arrastre no cambia nada ---- */
  const testigo = enRejilla();
  await arrastrar(3, 0, true);
  ok("Escape a mitad del arrastre deja todo como estaba",
     mismos(enRejilla(), testigo) && mismos(enDeck(), testigo) && mismos(guardado(), testigo),
     enRejilla().slice(0, 4));
  ok("y la rejilla sigue abierta", !!document.querySelector(".rv-rejilla"));

  /* ---- deshacer ---- */
  const bd = document.querySelector('.rv-rj-barra [data-rj="deshacer"]');
  bd.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
  await dormir(200);
  ok("deshacer devuelve el orden que dice el HTML", mismos(enDeck(), P.ids),
     enDeck().slice(0, 3) + " vs " + P.ids.slice(0, 3));
  ok("y deja de haber orden pendiente", guardado().length === 0, guardado().length);
  ok("la barra ya no avisa de nada", chapa() === "", chapa());
  ok("el botón de deshacer se apaga solo",
     document.querySelector('.rv-rj-barra [data-rj="deshacer"]').disabled);
  ok("la rejilla se rehace en el orden del deck", mismos(enRejilla(), P.ids));

  /* ---- mover una sola no debe marcar medio deck ---- */
  await arrastrar(6, 0, false);
  const marcadas = celdas().filter((c) => c.classList.contains("rv-rj-movida"));
  ok("subir una lámina al principio marca esa y solo esa",
     marcadas.length === 1 && marcadas[0] === celdas()[0],
     marcadas.length + " marcadas");
  ok("y la barra cuenta una, no todas las que se corrieron",
     chapa() === "sin aplicar: 1 movida", chapa());
  document.querySelector('.rv-rj-barra [data-rj="deshacer"]')
    .dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
  await dormir(200);
  ok("y se vuelve a dejar como estaba", mismos(enDeck(), P.ids));

  /* ---- un clic sin arrastre lleva a su lámina ---- */
  const destino = enRejilla()[3];
  const c3 = celdas()[3];
  c3.scrollIntoView({ block: "center" });
  await dormir(40);
  const r3 = c3.getBoundingClientRect();
  raton("mousedown", r3.left + 12, r3.top + 12, c3);
  raton("mouseup", r3.left + 12, r3.top + 12);
  await dormir(300);
  ok("el clic sin arrastre cierra la rejilla", !document.querySelector(".rv-rejilla"));
  ok("y lleva a la lámina que se pinchó",
     (Reveal.getCurrentSlide().dataset.sid || Reveal.getCurrentSlide().id) === destino,
     destino);

  /* ---- R cierra, y el export lleva el orden ---- */
  tecla("R", 82);
  await dormir(300);
  ok("R vuelve a abrir la rejilla", !!document.querySelector(".rv-rejilla"));
  await arrastrar(5, 0, false);
  const subida = enDeck()[0];
  tecla("R", 82);
  await dormir(200);
  ok("y R la cierra", !document.querySelector(".rv-rejilla"));

  tecla("E", 69);
  await dormir(300);
  const exp = document.querySelector(".rv-capa .rv-prev");
  const txt = exp ? exp.textContent : "";
  ok("el export trae el orden nuevo para aplicarlo sin servidor",
     /## Orden de las láminas/.test(txt) && /reordenar\\.py/.test(txt), txt.slice(0, 60));
  const renglones = txt.split("\\n").filter((x) => /^\\d+\\. \\*\\*/.test(x));
  ok("con la lista completa de láminas, en su orden nuevo",
     renglones.length === P.n && renglones[0].includes(subida), renglones.length);
  ok("y marcando de dónde viene solo la que se movió",
     renglones.filter((x) => x.includes("estaba en la")).length === 1,
     renglones.filter((x) => x.includes("estaba en la")).length);
  const capa = document.querySelector(".rv-capa");
  if (capa) capa.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
 } catch (e) {
  R.push("FALLA  excepción: " + (e && e.message ? e.message : e));
 }
 const d = document.createElement("div");
 d.id = "diag";
 d.textContent = R.join(";;");
 document.body.appendChild(d);
})();
</script>
"""


def prueba_navegador(res):
    p = pathlib.Path(RUTA).resolve()
    if not p.exists():
        res.append("FALLA  no existe " + str(p))
        return
    s = p.read_text(encoding="utf-8")
    m = re.search(r'<script src="[^"]*revisar\.js"></script>', s)
    if not m:
        res.append("FALLA  el deck no carga revisar.js")
        return
    deck = json.dumps(p.parent.name)[1:-1]
    s = s.replace(m.group(0),
                  SEMILLA.replace("__DECK__", deck) + m.group(0) +
                  PRUEBA.replace("__DECK__", deck))
    tmp = p.with_name("_prueba-orden.html")
    tmp.write_text(s, encoding="utf-8")
    perfil = tempfile.mkdtemp(prefix="orden-perfil-")
    try:
        r = subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
                            "--allow-file-access-from-files", "--user-data-dir=" + perfil,
                            "--window-size=1600,1000",
                            "--virtual-time-budget=60000", "--dump-dom",
                            "file://" + str(tmp) + "?review"],
                           capture_output=True, text=True, timeout=180)
        d = re.search(r'<div id="diag">(.*?)</div>', r.stdout.replace("\n", " "), re.S)
        salida = d.group(1) if d else "FALLA  no se pudo medir  " + r.stderr[-600:]
    finally:
        if tmp.exists():
            os.unlink(tmp)
        shutil.rmtree(perfil, ignore_errors=True)
    res.extend(x.strip() for x in salida.split(";;"))


def main():
    res = []
    print("### tools/reordenar.py")
    # Cada bloque va envuelto: una excepción que no sea R.Error cortaría la
    # batería entera y las pruebas de después ni llegarían a correr, que es lo
    # peor que puede hacer un arnés, callar por haberse caído.
    for bloque in (prueba_python, prueba_diferencial):
        try:
            bloque(res)
        except Exception as e:
            res.append("FALLA  %s se cayó con una excepción  [%s: %s]"
                       % (bloque.__name__, type(e).__name__, e))
    print("\n".join(res))
    n = len(res)
    print("\n### la rejilla en el navegador")
    web = []
    try:
        prueba_navegador(web)
    except Exception as e:
        web.append("FALLA  la prueba del navegador se cayó  [%s: %s]" % (type(e).__name__, e))
    print("\n".join(web))
    res += web
    malas = [x for x in res if x.startswith("FALLA")]
    print()
    print("%d de %d fallan  (%d del script, %d de la rejilla)"
          % (len(malas), len(res), n, len(web)) if malas
          else "las %d pruebas del orden pasan  (%d del script, %d de la rejilla)"
          % (len(res), n, len(web)))
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main())
