#!/usr/bin/env python3
"""Prueba de las notas en disco: el servidor y el anotador hablando con él.

    python3 tools/prueba-notas.py [sesiones/SNN-.../index.html]

Levanta el servidor de tools/servir.py en un puerto suelto y comprueba dos
cosas, en este orden:

1. Las rutas, sin navegador: que GET devuelva lo que hay, que PUT escriba, que
   un PUT con la versión vieja se rechace con 409 en vez de pisar, que una
   página de otro origen no pueda escribir, y que no se pueda salir de
   sesiones/ ni inventarse una sesión.

2. Que ocho escritores simultáneos sobre la misma sesión no pierdan ni una
   nota. Es el caso de varios agentes corrigiendo a la vez, o de dos pestañas
   abiertas.

3. Las rutas de las alarmas del apuntador: que GET lea admin/alarmas.json, que
   PUT lo escriba, que se filtre lo que no es una hora de reloj y que otro
   origen no pueda escribir.

4. El anotador contra ellas, en Chrome headless: que al abrir lea las notas del
   disco y no del navegador, que una nota nueva acabe en notas.json con su
   ordinal de cita, y que si el archivo cambia por fuera, que es justo lo que
   pasa cuando aplico las correcciones, la vista se ponga al día sola y avise.
   Del apuntador, que las alarmas salgan del disco y que lo que se toque en el
   panel acabe en el archivo.

El camino sin servidor, que es el de un deck abierto con doble clic, se prueba
aparte en tools/prueba-revisar.py, que corre sobre file://.

Trabaja con un perfil de Chrome desechable y hace copia de seguridad del
notas.json que hubiera, así que no toca ni las notas reales ni el perfil real.
"""
import html, importlib.util, json, os, pathlib, re, shutil, subprocess, sys
import tempfile, threading, time, urllib.error, urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
RUTA = sys.argv[1] if len(sys.argv) > 1 else "sesiones/S01-presentacion-del-curso-y-evaluacion/index.html"

R = []
def ok(nombre, cond, extra=""):
    R.append(("OK   " if cond else "FALLA") + "  " + nombre + ("" if cond else "  [" + str(extra) + "]"))


def carga_servir():
    spec = importlib.util.spec_from_file_location("servir", RAIZ / "tools" / "servir.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def cita_del_deck(p):
    """Una viñeta de verdad del deck, con el id de su lámina, para citarla."""
    s = re.sub(r"<!--.*?-->", "", p.read_text(encoding="utf-8"), flags=re.S)
    for m in re.finditer(r'<section[^>]*\sdata-sid="([^"]+)"(.*?)</section>', s, re.S):
        for li in re.findall(r"<li[^>]*>(.*?)</li>", m.group(2), re.S):
            t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", li))).strip()
            if len(t) > 20:
                return m.group(1), t[:40]
    return None, None


def pedir(base, metodo, ruta, cuerpo=None, origen=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(base + ruta, data=datos, method=metodo)
    if datos is not None:
        req.add_header("Content-Type", "application/json")
    if origen:
        req.add_header("Origin", origen)
    def cuerpo_de(r, codigo):
        crudo = r.read().decode("utf-8", "replace")
        try:
            return codigo, json.loads(crudo or "{}")
        except ValueError:
            return codigo, {"crudo": crudo[:120]}   # no todo lo que sirve es JSON
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return cuerpo_de(r, r.status)
    except urllib.error.HTTPError as e:
        return cuerpo_de(e, e.code)


# ---------- 1. las rutas, sin navegador ----------

def prueba_rutas(base, deck):
    r = "/notas/" + deck
    c, d = pedir(base, "GET", r)
    ok("una sesión sin notas devuelve el documento vacío",
       c == 200 and {k: v for k, v in d.items() if k != "deck"} ==
       {"v": 0, "notas": {}, "guiones": {}, "cortos": {}, "recortes": {},
        "orden": [], "nuevas": [], "borradas": [], "fusiones": [],
        "pendientes": [], "cambios": {}}, (c, d))

    c, d = pedir(base, "PUT", r, {"v": 0, "notas": {"una": [{"nid": "n1", "texto": "hola"}]},
                                  "guiones": {}}, origen=base)
    ok("el PUT escribe y sube la versión", c == 200 and d.get("v") == 1, (c, d))

    c, d = pedir(base, "GET", r)
    ok("y el GET devuelve lo escrito",
       c == 200 and d["v"] == 1 and d["notas"]["una"][0]["texto"] == "hola", (c, d))

    ok("el archivo está en la carpeta de la sesión",
       (RAIZ / "sesiones" / deck / "notas.json").exists())

    c, d = pedir(base, "PUT", r, {"v": 0, "notas": {}, "guiones": {}}, origen=base)
    ok("un PUT con la versión vieja no pisa, devuelve 409 y lo vigente",
       c == 409 and d.get("v") == 1 and "una" in d.get("notas", {}), (c, d))

    # el guion corto y el nivel de recorte viajan con las notas, en su apartado
    c, d = pedir(base, "PUT", r,
                 {"v": 1, "notas": {}, "guiones": {},
                  "cortos": {"una": {"texto": "en dos frases", "ts": "2026-09-03T10:00"}},
                  "recortes": {"una": {"nivel": 2, "ts": "2026-09-03T10:00"}}}, origen=base)
    c, d = pedir(base, "GET", r)
    ok("el guion corto y el nivel de recorte se guardan y vuelven",
       d.get("cortos", {}).get("una", {}).get("texto") == "en dos frases" and
       d.get("recortes", {}).get("una", {}).get("nivel") == 2, (c, d))

    # una pestaña vieja, que no conoce esos apartados, no debe llevárselos
    c, d = pedir(base, "PUT", r, {"v": d["v"], "notas": {}, "guiones": {}}, origen=base)
    c, d = pedir(base, "GET", r)
    ok("y un envío que no los menciona no los borra",
       "una" in d.get("cortos", {}) and "una" in d.get("recortes", {}), (c, d))

    # el orden de las láminas: el cuarto cambio pendiente, y el único que no va
    # por lámina sino por deck
    c, d = pedir(base, "PUT", r, {"v": d["v"], "notas": {}, "guiones": {},
                                  "orden": ["dos", "una", "dos", 7, "", "tres"]}, origen=base)
    c, d = pedir(base, "GET", r)
    ok("el orden de las láminas se guarda, sin repetidos ni basura",
       d.get("orden") == ["dos", "una", "tres"], d.get("orden"))
    c, d = pedir(base, "PUT", r, {"v": d["v"], "notas": {}, "guiones": {}}, origen=base)
    c, d = pedir(base, "GET", r)
    ok("y una pestaña que no lo menciona tampoco lo borra",
       d.get("orden") == ["dos", "una", "tres"], d.get("orden"))
    c, d = pedir(base, "PUT", r, {"v": d["v"], "notas": {}, "guiones": {},
                                  "orden": ["dos", "una"]}, origen=base)
    # una pestaña con la versión vieja recibe lo vigente, orden incluido, que es
    # con lo que reaplica su cambio en vez de pisarlo
    c, d = pedir(base, "PUT", r, {"v": 0, "notas": {}, "guiones": {},
                                  "orden": ["una", "dos"]}, origen=base)
    ok("un choque de versiones devuelve también el orden vigente",
       c == 409 and d.get("orden") == ["dos", "una"], (c, d.get("orden")))
    c, d = pedir(base, "GET", r)
    ok("y el orden en disco no se pisó", d.get("orden") == ["dos", "una"], d.get("orden"))
    c, d = pedir(base, "PUT", r, {"v": d["v"], "notas": {}, "guiones": {}, "orden": []},
                 origen=base)
    c, d = pedir(base, "GET", r)
    ok("mandarlo vacío sí lo cierra, que es como se aplica al HTML",
       d.get("orden") == [], d.get("orden"))

    # las dos compañeras del orden: las láminas por escribir y las que se borran
    c, d = pedir(base, "PUT", r, {"v": d["v"], "notas": {}, "guiones": {},
                                  "nuevas": [{"id": "nueva-1", "texto": "un ejemplo",
                                              "ts": "2026-09-22T23:00"},
                                             {"id": "nueva-1", "texto": "repetida"},
                                             {"texto": "sin id"}, "basura"],
                                  "borradas": ["una", "una", 7]}, origen=base)
    c, d = pedir(base, "GET", r)
    ok("las láminas por escribir se guardan, sin repetidas ni basura",
       [x["id"] for x in d.get("nuevas", [])] == ["nueva-1"] and
       d["nuevas"][0]["texto"] == "un ejemplo", d.get("nuevas"))
    ok("y las marcadas para borrar, igual", d.get("borradas") == ["una"], d.get("borradas"))
    c, d = pedir(base, "PUT", r, {"v": d["v"], "notas": {}, "guiones": {}}, origen=base)
    c, d = pedir(base, "GET", r)
    ok("una pestaña que no las menciona no se las lleva",
       len(d.get("nuevas", [])) == 1 and d.get("borradas") == ["una"], (d.get("nuevas"), d.get("borradas")))
    c, d = pedir(base, "PUT", r, {"v": d["v"], "notas": {}, "guiones": {},
                                  "nuevas": [], "borradas": []}, origen=base)
    c, d = pedir(base, "GET", r)
    ok("y mandarlas vacías las cierra, que es como se aplican al HTML",
       d.get("nuevas") == [] and d.get("borradas") == [], (d.get("nuevas"), d.get("borradas")))

    # las láminas que hay que combinar en una
    c, d = pedir(base, "PUT", r, {"v": d["v"], "notas": {}, "guiones": {},
                                  "fusiones": [{"id": "f1", "partes": ["a", "b", "a", 7],
                                                "texto": "junta los dos mapas"},
                                               {"id": "f2", "partes": ["b", "c"]},
                                               {"id": "f3", "partes": ["solo-una"]},
                                               {"partes": ["x", "y"]}]}, origen=base)
    c, d = pedir(base, "GET", r)
    f = d.get("fusiones") or []
    ok("las fusiones se guardan, sin repetidos ni basura",
       len(f) == 1 and f[0]["partes"] == ["a", "b"] and f[0]["texto"] == "junta los dos mapas",
       f)
    # f2 nombraba a "b", que ya estaba en f1, y se quedaba con una sola parte;
    # f3 traía una sola de entrada, y la cuarta no tenía id. Las tres se caen.
    ok("una fusión que se queda con una sola lámina no se guarda",
       not any(x["id"] in ("f2", "f3") for x in f), [x["id"] for x in f])
    c, d = pedir(base, "PUT", r, {"v": d["v"], "notas": {}, "guiones": {}}, origen=base)
    c, d = pedir(base, "GET", r)
    ok("y una pestaña que no las menciona no se las lleva", len(d.get("fusiones") or []) >= 1,
       d.get("fusiones"))

    # un cuerpo que es JSON válido pero no un objeto no tiene .get: sin la guarda
    # el servidor contestaba 500 con traceback
    c, d = pedir(base, "PUT", r, ["esto", "no", "es", "un", "objeto"], origen=base)
    ok("un cuerpo que no es un objeto se rechaza con 400", c == 400, (c, d))
    c, d = pedir(base, "PUT", r, 7, origen=base)
    ok("y un número, también", c == 400, (c, d))

    c, d = pedir(base, "PUT", r, {"v": 1, "notas": {}, "guiones": {}},
                 origen="https://otra.example")
    ok("una página de otro origen no puede escribir", c == 403, (c, d))

    c, d = pedir(base, "GET", "/notas/S99-inventada")
    ok("una sesión que no existe da 404", c == 404, (c, d))

    c, d = pedir(base, "PUT", "/CLAUDE.md", {"v": 0}, origen=base)
    ok("fuera de /notas no se escribe", c == 405, (c, d))

    c, d = pedir(base, "GET", "/notas/../../etc/passwd")
    ok("no se puede salir de sesiones/", c == 404, (c, d))

    c, d = pedir(base, "GET", "/admin/sesiones.csv")
    ok("y los archivos del curso se siguen sirviendo", c == 200, c)

    # sin rangos, un <video> no puede saltar, y los videos de la S02 son
    # fragmentos concatenados: cada lámina mostraría el primero del archivo
    entero = urllib.request.urlopen(base + "/admin/sesiones.csv", timeout=5).read()
    req = urllib.request.Request(base + "/admin/sesiones.csv")
    req.add_header("Range", "bytes=10-19")
    with urllib.request.urlopen(req, timeout=5) as resp:   # ojo: `r` es la ruta de notas
        trozo, codigo = resp.read(), resp.status
        cr, acepta = resp.headers.get("Content-Range"), resp.headers.get("Accept-Ranges")
    ok("los archivos se sirven por trozos, que es lo que el video necesita",
       codigo == 206 and trozo == entero[10:20], (codigo, trozo[:20]))
    ok("y con el rango bien declarado",
       cr == "bytes 10-19/%d" % len(entero), cr)
    ok("y anunciando que acepta saltos", acepta == "bytes", acepta)

    # sin esto el navegador se queda con el tema viejo y maqueta mal sin avisar
    with urllib.request.urlopen(base + "/plantillas/tema-centrogeo/tema-centrogeo.css",
                                timeout=5) as resp:
        cc = resp.headers.get("Cache-Control")
    ok("los archivos se sirven sin caché, que aquí se editan en caliente",
       cc == "no-cache", cc)

    # el navegador no puede saber por su cuenta que el deck cambió: se lo dice
    # el servidor, y con eso el anotador ofrece recargar
    idx = RAIZ / "sesiones" / deck / "index.html"
    antes = pedir(base, "GET", r)[1].get("deck")
    st = idx.stat()
    os.utime(idx, (st.st_atime, st.st_mtime + 10))
    despues = pedir(base, "GET", r)[1].get("deck")
    os.utime(idx, (st.st_atime, st.st_mtime))
    ok("el servidor avisa de cuándo cambió el deck",
       isinstance(antes, int) and despues == antes + 10, (antes, despues))
    ok("y el dato no se guarda en el archivo, es del momento",
       "deck" not in json.loads((RAIZ / "sesiones" / deck / "notas.json").read_text()),
       "se coló en notas.json")

    # los pendientes de la sesión viven en el mismo archivo, pero el anotador ni
    # los conoce: sus guardados no pueden llevárselos por delante
    v = pedir(base, "GET", r)[1]["v"]
    pedir(base, "PUT", r, {"v": v, "notas": {}, "guiones": {},
                           "pendientes": [{"id": "p1", "texto": "algo", "estado": "abierto"}]},
          origen=base)
    v = pedir(base, "GET", r)[1]["v"]
    pedir(base, "PUT", r, {"v": v, "notas": {"x": [{"nid": "n9"}]}, "guiones": {}}, origen=base)
    d = pedir(base, "GET", r)[1]
    ok("un guardado sin pendientes no se los lleva por delante",
       [x["id"] for x in d.get("pendientes", [])] == ["p1"], d.get("pendientes"))


def prueba_concurrencia(base, deck):
    """Ocho escritores a la vez sobre la misma sesión: nadie puede perderse por
    el camino. Es el caso de varios agentes corrigiendo, o de dos pestañas."""
    ruta = "/notas/" + deck
    v0 = pedir(base, "GET", ruta)[1]["v"]
    pedir(base, "PUT", ruta, {"v": v0, "notas": {}, "guiones": {}}, origen=base)

    choques = []

    def escribe(i):
        for intento in range(20):
            doc = pedir(base, "GET", ruta)[1]
            doc["notas"].setdefault("lamina", []).append({"nid": "n%d" % i, "texto": "nota %d" % i})
            c, _ = pedir(base, "PUT", ruta, doc, origen=base)
            if c == 200:
                return
            choques.append(i)
        ok("el escritor %d llegó a guardar" % i, False, "20 intentos y sigue en conflicto")

    hilos = [threading.Thread(target=escribe, args=(i,)) for i in range(8)]
    [h.start() for h in hilos]
    [h.join() for h in hilos]

    d = pedir(base, "GET", ruta)[1]
    nids = sorted(x["nid"] for x in d["notas"].get("lamina", []))
    ok("ocho escritores simultáneos y no se pierde ninguna nota",
       nids == sorted("n%d" % i for i in range(8)), nids)
    ok("y la versión subió una vez por escritura",
       d["v"] == v0 + 9, "v=%d, esperaba %d" % (d["v"], v0 + 9))
    ok("hubo conflictos de verdad que resolver, no fue suerte",
       len(choques) > 0, "ninguno: la prueba no llegó a apretar")


def prueba_alarmas(base):
    c, d = pedir(base, "GET", "/alarmas")
    ok("sin archivo, las alarmas salen vacías", c == 200 and d == {"alarmas": []}, (c, d))

    c, d = pedir(base, "PUT", "/alarmas", {"alarmas": [
        {"h": "09:55", "t": "Cerrar y despedir", "s": "doble"},
        {"h": "08:55", "t": "Receso", "s": "campana"}]}, origen=base)
    ok("el PUT escribe las alarmas", c == 200 and len(d["alarmas"]) == 2, (c, d))
    ok("y las devuelve ordenadas por hora",
       [x["h"] for x in d["alarmas"]] == ["08:55", "09:55"], d)

    ok("el archivo está en admin/alarmas.json", (RAIZ / "admin" / "alarmas.json").exists())
    guardado = json.loads((RAIZ / "admin" / "alarmas.json").read_text(encoding="utf-8"))
    ok("y es un JSON que se puede editar a mano",
       guardado["alarmas"][0] == {"h": "08:55", "t": "Receso", "s": "campana"}, guardado)

    c, d = pedir(base, "GET", "/alarmas")
    ok("el GET devuelve lo escrito",
       c == 200 and d["alarmas"][1]["t"] == "Cerrar y despedir", (c, d))

    # este archivo lo escribe el navegador y se edita a mano: se filtra siempre
    c, d = pedir(base, "PUT", "/alarmas", {"alarmas": [
        {"h": "08:55", "t": "buena", "s": "campana"},
        {"h": "25:99", "t": "hora imposible"},
        {"h": "sin hora", "t": "ni eso"},
        {"t": "sin hora ninguna"},
        "ni siquiera un objeto",
        {"h": "09:00", "t": "sonido inventado", "s": "trompeta"}]}, origen=base)
    ok("lo que no es una hora de reloj se descarta", c == 200 and len(d["alarmas"]) == 2, (c, d))
    ok("y un sonido inventado se queda en ninguno",
       d["alarmas"][1]["s"] == "ninguno", d["alarmas"][1])

    c, d = pedir(base, "PUT", "/alarmas", {"alarmas": []}, origen="https://otra.example")
    ok("una página de otro origen no puede tocar las alarmas", c == 403, (c, d))
    c, d = pedir(base, "GET", "/alarmas")
    ok("y no las tocó", len(d["alarmas"]) == 2, d)


# ---------- 2. el anotador contra las rutas, en Chrome ----------

SEMILLA = """<script>
// headless puede reportar la pestaña como oculta, y entonces el anotador no
// vigila el archivo. Aquí se prueba la vigilancia, así que se fuerza visible.
try { Object.defineProperty(document, "hidden", { get: () => false }); } catch (e) {}
window.confirm = () => true;
window.__P = __DATOS__;
</script>
"""

PRUEBA = """<script>
const R = [];
const ok = (n, c, extra) => R.push((c ? "OK   " : "FALLA") + "  " + n + (extra && !c ? "  [" + extra + "]" : ""));
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
const tecla = (k, code, el) => (el || document).dispatchEvent(new KeyboardEvent("keydown",
  { key: k, keyCode: code, which: code, bubbles: true, cancelable: true }));
const P = window.__P;
const RUTA = "/notas/" + P.deck;
const bajar = () => fetch(RUTA, { cache: "no-store" }).then((r) => r.json());
const plano = (s) => String(s).replace(/\\s+/g, " ").trim();

(async () => {
 try {
  await dormir(1500);
  const secs = [...document.querySelectorAll(".slides > section")];
  const sec = secs.find((s) => s.dataset.sid === P.sid);

  // 1. al abrir, las notas salen del disco
  ok("el localStorage estaba vacío al empezar", P.localVacio, P.localVacio);
  // Se cuentan NOTAS resaltadas, no fragmentos: una cita que cruza una etiqueta,
  // por ejemplo "De 1943 a <strong>Dartmouth</strong>: la gestación", no cabe en
  // un solo <mark> y el anotador la pinta en varios con el mismo data-nid.
  const marcas = [...sec.querySelectorAll("mark.rv-hl")];
  const resaltadas = [...new Set(marcas.map((m) => m.dataset.nid))];
  ok("la nota del disco aparece resaltada", resaltadas.length === 1,
     "notas=" + resaltadas.length + " en " + marcas.length + " marcas");
  ok("y es la que sembramos", resaltadas.length === 1 && resaltadas[0] === "nDISCO",
     resaltadas.join(" | "));
  ok("la barra no avisa de que falte el servidor", !document.querySelector(".rv-off"));
  ok("y no ofrece recargar mientras el deck no cambie",
     !document.querySelector(".rv-recarga"));

  // 2. una nota nueva acaba en el archivo, con su ordinal
  // La nota se ancla a la lámina en pantalla, así que hay que ir a ella primero.
  Reveal.slide(secs.indexOf(sec));
  await dormir(500);
  const li = sec.querySelector(".cuerpo li:last-child") || sec.querySelector(".cuerpo li");
  const rango = document.createRange();
  rango.selectNodeContents(li.firstChild || li);
  const sel = window.getSelection();
  sel.removeAllRanges(); sel.addRange(rango);
  const seleccionado = plano(String(sel));
  ok("se pudo seleccionar texto de la lámina", seleccionado.length > 5, seleccionado);
  tecla("a", 65);
  await dormir(400);
  const ta = document.querySelector(".rv-capa textarea");
  ok("la tecla A abre la caja de nota", !!ta);
  if (ta) {
    ta.value = "nota escrita en la prueba";
    ta.dispatchEvent(new KeyboardEvent("keydown",
      { key: "Enter", keyCode: 13, ctrlKey: true, bubbles: true, cancelable: true }));
  }
  await dormir(900);
  const tras = await bajar();
  const todas = Object.values(tras.notas || {}).flat();
  const mia = todas.find((x) => x.texto === "nota escrita en la prueba");
  ok("la nota nueva llegó al archivo del servidor", !!mia,
     JSON.stringify(todas.map((x) => x.texto)));
  ok("anclada a la lámina que estaba en pantalla",
     !!tras.notas[P.sid] && tras.notas[P.sid].some((x) => x.nid === (mia || {}).nid),
     Object.keys(tras.notas || {}).join(" | "));
  ok("con la cita que se seleccionó", !!mia && plano(mia.cita) === seleccionado,
     mia && mia.cita);
  ok("y con el ordinal de la aparición", !!mia && typeof mia.nth === "number", mia && mia.nth);
  ok("la versión del archivo subió", tras.v > P.v, tras.v + " sobre " + P.v);
  ok("y la nota de antes sigue ahí", todas.some((x) => x.nid === "nDISCO"));

  // 3. si el archivo cambia por fuera, la vista se pone al día sola
  const actual = await bajar();
  const podadas = {};
  Object.keys(actual.notas).forEach((id) => {
    const q = actual.notas[id].filter((x) => x.nid !== "nDISCO");
    if (q.length) podadas[id] = q;
  });
  const resp = await fetch(RUTA, { method: "PUT", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ v: actual.v, notas: podadas, guiones: actual.guiones }) });
  ok("se pudo simular la corrección desde fuera", resp.ok, resp.status);
  for (let i = 0; i < 40 && sec.querySelector('mark.rv-hl[data-nid="nDISCO"]'); i++) await dormir(300);
  ok("el resaltado de la nota corregida desaparece solo",
     !sec.querySelector('mark.rv-hl[data-nid="nDISCO"]'));
  ok("y la nota nueva no se pierde por el camino",
     !!document.querySelector("mark.rv-hl"), "no queda ningún resaltado");
  const av = document.querySelector(".rv-aviso");
  ok("y avisa en pantalla de lo que pasó", !!av, av ? av.textContent : "(sin aviso)");

  // 4. el apuntador: las alarmas salen del disco y lo que se toca vuelve a él
  const marco = document.createElement("iframe");
  document.body.appendChild(marco);
  const falso = { closed: false, document: marco.contentDocument, focus() {}, close() {},
                  scrollTo() {}, addEventListener() {}, prompt: () => null };
  window.open = () => falso;
  tecla("t", 84);
  await dormir(600);
  const dd = falso.document;
  ok("el apuntador se abre contra el servidor", !!dd.getElementById("texto"));
  dd.dispatchEvent(new KeyboardEvent("keydown", { key: "a", bubbles: true, cancelable: true }));
  await dormir(700);
  const filas = () => [...dd.querySelectorAll("#alLista .al")];
  ok("el panel trae la alarma que estaba en el disco",
     filas().length === 1 &&
     filas()[0].querySelector(".alT").value === "Receso del disco",
     filas().map((f) => f.querySelector(".alT").value).join(" | "));
  ok("y dice que se guardan en el proyecto, no en el navegador",
     !dd.getElementById("alFuente").classList.contains("off") &&
     dd.getElementById("alFuente").textContent.includes("admin/alarmas.json"),
     dd.getElementById("alFuente").textContent);

  dd.getElementById("alMas").dispatchEvent(
    new MouseEvent("click", { bubbles: true, cancelable: true }));
  await dormir(400);
  const nueva = filas().find((f) => f.querySelector(".alT").value === "");
  ok("se puede añadir otra desde el panel", !!nueva, filas().length + " filas");
  if (nueva) {
    nueva.querySelector(".alH").value = P.alarmaNueva;
    nueva.querySelector(".alT").value = "Puesta en el panel";
    nueva.querySelector(".alS").value = "timbre";
    nueva.querySelector(".alT").dispatchEvent(new Event("input", { bubbles: true }));
  }
  await dormir(900);
  const enDisco = await fetch("/alarmas", { cache: "no-store" }).then((r) => r.json());
  const puesta = (enDisco.alarmas || []).find((x) => x.t === "Puesta en el panel");
  ok("la alarma nueva llegó al archivo del servidor", !!puesta,
     JSON.stringify(enDisco.alarmas));
  ok("con su hora y su sonido",
     !!puesta && puesta.h === P.alarmaNueva && puesta.s === "timbre", JSON.stringify(puesta));
  ok("y la que ya estaba en el disco sigue ahí",
     (enDisco.alarmas || []).some((x) => x.t === "Receso del disco"),
     JSON.stringify(enDisco.alarmas));
 } catch (e) { R.push("FALLA  excepcion: " + e.message); }
 const div = document.createElement("div");
 div.id = "diag";
 div.textContent = R.join(" ;; ");
 document.body.appendChild(div);
})();
</script>
"""


def prueba_navegador(base, deck, p, sid, cita):
    """Siembra una nota en el archivo y abre el deck contra el servidor."""
    pedir(base, "PUT", "/notas/" + deck,
          {"v": 0, "notas": {sid: [{"nid": "nDISCO", "cita": cita, "nth": 0,
                                    "texto": "esta viene del disco", "ambito": "lamina",
                                    "ts": "2026-09-02T20:00"}]}, "guiones": {},
           "pendientes": [{"id": "p1", "texto": "un pendiente de la sesión",
                           "estado": "abierto"}]},
          origen=base)
    v = pedir(base, "GET", "/notas/" + deck)[1]["v"]

    s = p.read_text(encoding="utf-8")
    m = re.search(r'<script src="[^"]*revisar\.js"></script>', s)
    if not m:
        ok("el deck carga revisar.js", False, "no lo carga")
        return
    # Dos horas lejos de la de ahora, para que ninguna alarma se dispare a media
    # prueba y llene la ventana de avisos.
    ahora = time.localtime()
    lejos = lambda h: "%02d:%02d" % ((ahora.tm_hour + h) % 24, ahora.tm_min)
    pedir(base, "PUT", "/alarmas",
          {"alarmas": [{"h": lejos(3), "t": "Receso del disco", "s": "ninguno"}]},
          origen=base)
    datos = json.dumps({"deck": deck, "sid": sid, "v": v, "localVacio": True,
                        "alarmaNueva": lejos(5)})
    s = s.replace(m.group(0),
                  SEMILLA.replace("__DATOS__", datos) + m.group(0) + PRUEBA)
    tmp = p.with_name("_prueba-notas.html")
    tmp.write_text(s, encoding="utf-8")
    perfil = tempfile.mkdtemp(prefix="rv-notas-")
    try:
        url = "%s/sesiones/%s/%s?review" % (base, deck, tmp.name)
        r = subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
                            "--user-data-dir=" + perfil, "--virtual-time-budget=40000",
                            "--dump-dom", url],
                           capture_output=True, text=True, timeout=180)
        d = re.search(r'<div id="diag">(.*?)</div>', r.stdout.replace("\n", " "), re.S)
        if not d:
            ok("el navegador llegó a medir algo", False, r.stderr[-300:])
            return
        for linea in d.group(1).split(";;"):
            R.append(linea.strip())
        final = pedir(base, "GET", "/notas/" + deck)[1]
        ok("y los pendientes de la sesión siguen intactos tras todo",
           [x["id"] for x in final.get("pendientes", [])] == ["p1"], final.get("pendientes"))
    finally:
        if tmp.exists():
            os.unlink(tmp)
        shutil.rmtree(perfil, ignore_errors=True)


def main():
    p = (RAIZ / RUTA).resolve() if not os.path.isabs(RUTA) else pathlib.Path(RUTA)
    if not p.exists():
        print("no existe " + str(p))
        return 1
    deck = p.parent.name
    sid, cita = cita_del_deck(p)
    if not sid:
        print("ese deck no tiene ninguna viñeta que citar")
        return 1

    servir = carga_servir()
    srv = servir.Servidor(("127.0.0.1", 0),
                          lambda *a, **k: servir.Manejador(*a, directory=str(RAIZ), **k))
    base = "http://127.0.0.1:%d" % srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    notas = RAIZ / "sesiones" / deck / "notas.json"
    alarmas = RAIZ / "admin" / "alarmas.json"
    # Las pruebas parten de cero y devuelven los archivos como estaban: esa sesión
    # tiene notas y pendientes de verdad, y las alarmas son las de Alberto.
    guardado = notas.read_text(encoding="utf-8") if notas.exists() else None
    guardadas = alarmas.read_text(encoding="utf-8") if alarmas.exists() else None
    notas.unlink(missing_ok=True)
    alarmas.unlink(missing_ok=True)
    try:
        prueba_rutas(base, deck)
        prueba_concurrencia(base, deck)
        prueba_alarmas(base)
        notas.unlink(missing_ok=True)          # el navegador también empieza de cero
        alarmas.unlink(missing_ok=True)
        prueba_navegador(base, deck, p, sid, cita)
    finally:
        srv.shutdown()
        if guardado is None:
            notas.unlink(missing_ok=True)
        else:
            notas.write_text(guardado, encoding="utf-8")
        if guardadas is None:
            alarmas.unlink(missing_ok=True)
        else:
            alarmas.write_text(guardadas, encoding="utf-8")

    print("\n".join(R))
    malas = [x for x in R if x.startswith("FALLA")]
    print("%d de %d fallan" % (len(malas), len(R)) if malas
          else "las %d pruebas de las notas en disco pasan" % len(R))
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main())
