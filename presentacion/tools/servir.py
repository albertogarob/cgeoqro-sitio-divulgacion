#!/usr/bin/env python3
"""Sirve los decks para revisarlos, y guarda sus notas de revisión en disco.

    python3 tools/servir.py          # arranca y lista las sesiones
    python3 tools/servir.py 3        # arranca y da la liga de revisión de la S03
    python3 tools/servir.py --parar  # lo apaga

Además de los archivos del curso, atiende dos rutas:

    GET  /notas/S03-...   devuelve las notas de esa sesión, y en `deck` cuándo
                          se tocó por última vez su index.html

Los archivos se sirven atendiendo `Range`, cosa que SimpleHTTPRequestHandler no
hace. Hace falta para el video: los de la S02 son fragmentos concatenados en un
solo archivo, y cada lámina salta al suyo. Sin rangos el navegador no puede
saltar, así que todas esas láminas mostrarían el primer clip una y otra vez.
    PUT  /notas/S03-...   las guarda en sesiones/S03-.../notas.json
    GET  /alarmas         las alarmas del apuntador, de admin/alarmas.json
    PUT  /alarmas         las guarda ahí

Ahí está la gracia: **las notas viven en disco, no en el navegador**. Se leen
con `cat`, se pueden editar a mano y no dependen de que la extensión de Chrome
esté conectada ni de que nadie copie y pegue nada. El anotador las lee y las
escribe contra estas rutas, y se queda con localStorage solo como red de
seguridad para cuando el servidor no está.

El archivo lleva un contador `v` que sube en cada escritura. Quien guarda manda
el `v` que tenía; si ya no es el vigente, el servidor responde 409 con el
documento bueno y el anotador reaplica su cambio encima. Eso es lo que evita
que una pestaña abierta desde hace rato pise las correcciones recién aplicadas.

    {"v": 3,
     "notas":   {"<id de lámina>": [{"nid": ..., "cita": ..., "nth": ..., "texto": ...,
                                     "ambito": "lamina" | "guion", "ts": ...}]},
     "guiones": {"<id de lámina>": {"texto": ..., "ts": ...}},
     "cortos":   {"<id de lámina>": {"texto": ..., "ts": ...}},
     "recortes": {"<id de lámina>": {"nivel": 0 | 1 | 2, "ts": ...}},
     "orden":    ["<id de lámina>", ...],
     "nuevas":   [{"id": "nueva-xxx", "texto": "qué debe contener", "ts": ...}],
     "borradas": ["<id de lámina>", ...],
     "fusiones": [{"id": "fusion-xxx", "partes": ["<id>", "<id>", ...],
                   "texto": "con qué criterio combinarlas", "ts": ...}],
     "pendientes": [{"id": ..., "texto": ..., "estado": "abierto" | "decidido",
                     "transversal": false, "ts": ...}]}

`cortos` y `recortes` son los otros dos cambios pendientes que deja la revisión:
el guion corto de una lámina, el que el apuntador lee cuando la sesión va tarde,
y su nivel de recorte, que dice cuánto cuesta perderla. Como las reescrituras
del guion, viven aquí hasta que se aplican al HTML, que es la fuente única.

`orden` es el cuarto, y el único que no va por lámina sino por deck: la lista
completa de ids en el orden en que quedaron al arrastrarlas en la rejilla de
revisar.js. Vacía quiere decir que no hay nada pendiente y manda el HTML. Se
lleva al archivo con tools/reordenar.py.

`fusiones` son las láminas que hay que combinar en una, con sus partes en el
orden en que se quieren leer y una nota opcional. Vacía la nota, el criterio lo
decide quien escriba la lámina. Aquí no se combina nada: combinar es trabajo de
contenido, y lo único que viaja es el encargo.

`nuevas` y `borradas` son sus dos compañeras, y van con él: las láminas que se
pidieron en la rejilla pero todavía no existen, cada una con la descripción de lo
que debe contener, y las que se marcaron para borrar y todavía siguen en el HTML.
Los ids de `nuevas` aparecen también en `orden`, que es lo que dice en qué sitio
van; los de `borradas` siguen en `orden` para que devolver una lámina la ponga
donde estaba. Los tres se aplican y se cierran juntos.

`pendientes` es la lista de tareas de esa sesión, la que antes vivía toda junta
en TODO.md. Vive aquí para que varios agentes corrigiendo sesiones distintas no
se pisen: cada uno escribe solo en el archivo de la suya. La maneja
tools/todo.py, y el anotador ni la conoce: el PUT la conserva intacta.

Las alarmas del apuntador viven en `admin/alarmas.json`, y no en el navegador,
por lo mismo: para que sobrevivan a un borrado de datos de Chrome y viajen con
el proyecto. Son globales, no de una sesión, porque el receso cae a la misma
hora las treinta clases.

    {"alarmas": [{"h": "08:55", "t": "Receso", "s": "campana"}]}

Aquí no hay contador de versión, a diferencia de las notas, y es deliberado:
este archivo lo escriben una sola persona y un solo panel, se edita a mano sin
más y es una lista corta. Manda el último que escribe. El apuntador relee el
archivo al abrirse y cada vez que se abre el panel, así que una edición a mano
se recoge sola con solo volver a abrirlo.

Solo escucha en 127.0.0.1, solo escribe en `sesiones/S*/notas.json` y en
`admin/alarmas.json`, y el PUT exige que la petición venga de una página del
propio servidor, así que ninguna otra pestaña del navegador puede tocar los
archivos.

Esto es para trabajar. Lo que se entrega al grupo sigue siendo el paquete de un
archivo de salidas/, que abre con doble clic y sin servidor.
"""
import copy, http.server, json, os, re, shutil, socket, socketserver, subprocess, sys, threading, time
import urllib.error, urllib.request, pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PUERTO = 8933     # el 8931 es del curso y el 8932 el del observatorio enoturístico
SENA = "/admin/sesiones.csv"     # solo está en la raíz del curso: nos identifica
SESION = re.compile(r"^S\d{2}-[A-Za-z0-9-]{1,80}$")
LIMITE = 4 * 1024 * 1024
VACIO = {"v": 0, "notas": {}, "guiones": {}, "cortos": {}, "recortes": {},
         "orden": [], "nuevas": [], "borradas": [], "fusiones": [], "pendientes": [],
         "cambios": {}}
ALARMAS = RAIZ / "admin" / "alarmas.json"
HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
SONIDOS = ("ninguno", "campana", "timbre", "doble", "suave")
TOPE_ALARMAS = 50

# El servidor atiende varias peticiones a la vez, y comparar la versión y
# escribir tienen que ser un solo paso: si no, dos guardados simultáneos sobre
# la misma sesión leerían la misma versión y uno de los dos se perdería sin que
# nadie se entere. Pasa con varios agentes corrigiendo, o con dos pestañas.
CANDADO = threading.Lock()


def base(puerto=PUERTO):
    return "http://127.0.0.1:%d" % puerto


def archivo(sesion):
    return RAIZ / "sesiones" / sesion / "notas.json"


def existe(sesion):
    return bool(SESION.match(sesion)) and (RAIZ / "sesiones" / sesion / "index.html").exists()


def leer_notas(sesion):
    # copia honda: VACIO lleva dentro diccionarios y listas, y una copia llana
    # repartiría el mismo objeto entre todas las sesiones.
    p = archivo(sesion)
    if not p.exists():
        return copy.deepcopy(VACIO)
    d = json.loads(p.read_text(encoding="utf-8"))
    for k, v in VACIO.items():
        d.setdefault(k, copy.deepcopy(v))
    return d


def escribir_notas(sesion, d):
    """Escritura atómica: nadie ve nunca un archivo a medias."""
    p = archivo(sesion)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


# Un id que valga como atributo HTML sin escapar: es como lo escribe el anotador
# y como lo espera tools/reordenar.py, que si no acaba escapándolo y dejando el
# pendiente atascado para siempre.
ID_OK = re.compile(r"^[A-Za-z0-9._:-]{1,120}$")
# Lo que cabe en un encargo o en la nota de una fusión. Son un párrafo o dos, no
# un tratado, y acaban dentro de un atributo del HTML.
TOPE_TEXTO = 4000


def recortar(t):
    return t[:TOPE_TEXTO] if isinstance(t, str) else ""


def limpiar_orden(lista):
    """El orden de las láminas: una lista de ids, sin repetidos y sin basura.

    Es lo único que el anotador manda y que no está indexado por lámina, así que
    conviene filtrarlo aquí: un id que no sea texto rompería tools/reordenar.py,
    que es quien lo lleva al HTML."""
    if not isinstance(lista, list):
        return []
    vistos, r = set(), []
    for x in lista:
        if isinstance(x, str) and ID_OK.match(x) and x not in vistos:
            vistos.add(x)
            r.append(x)
    return r


def limpiar_nuevas(lista):
    """Las láminas por escribir: id, descripción y sello, sin repetidos.

    El id es lo que las ata a su sitio en `orden`, así que una entrada sin id no
    sirve para nada y se cae. El texto es la descripción de lo que debe contener,
    y puede estar vacío: se escribe después, en la rejilla."""
    if not isinstance(lista, list):
        return []
    vistos, r = set(), []
    for x in lista:
        if not isinstance(x, dict):
            continue
        i = x.get("id")
        if not isinstance(i, str) or not ID_OK.match(i) or i in vistos:
            continue
        vistos.add(i)
        r.append({"id": i, "texto": recortar(x.get("texto")),
                  "ts": x.get("ts") if isinstance(x.get("ts"), str) else ""})
    return r


def limpiar_fusiones(lista):
    """Las láminas que hay que combinar en una.

    Una fusión sin dos partes no dice nada, y una lámina no puede estar en dos a
    la vez: la segunda que la nombre se queda sin ella. El texto es la nota con
    la que se combinan, y puede ir vacío."""
    if not isinstance(lista, list):
        return []
    usados, vistos, r = set(), set(), []
    for x in lista:
        if not isinstance(x, dict):
            continue
        i = x.get("id")
        if not isinstance(i, str) or not ID_OK.match(i) or i in vistos:
            continue
        crudas = x.get("partes")
        if not isinstance(crudas, list):
            # una cadena suelta se iteraría carácter a carácter y fabricaría partes
            continue
        partes, hay = [], set()
        for y in crudas:
            if isinstance(y, str) and ID_OK.match(y) and y not in hay and y not in usados:
                hay.add(y)
                partes.append(y)
        if len(partes) < 2:
            continue
        vistos.add(i)
        usados |= hay
        r.append({"id": i, "partes": partes, "texto": recortar(x.get("texto")),
                  "ts": x.get("ts") if isinstance(x.get("ts"), str) else ""})
    return r


def limpiar_alarmas(lista):
    """Deja solo alarmas con una hora de reloj de verdad, ordenadas. Este
    archivo se edita a mano y lo escribe el navegador: se filtra siempre, no se
    confía en ninguno de los dos."""
    if not isinstance(lista, list):
        return []
    salida = []
    for x in lista[:TOPE_ALARMAS]:
        if not isinstance(x, dict) or not HORA.match(str(x.get("h", ""))):
            continue
        salida.append({"h": x["h"],
                       "t": str(x.get("t") or "")[:120],
                       "s": x.get("s") if x.get("s") in SONIDOS else "ninguno"})
    salida.sort(key=lambda x: x["h"])
    return salida


def leer_alarmas():
    if not ALARMAS.exists():
        return []
    d = json.loads(ALARMAS.read_text(encoding="utf-8"))
    return limpiar_alarmas(d.get("alarmas") if isinstance(d, dict) else d)


def escribir_alarmas(lista):
    """Escritura atómica, como las notas: nadie ve nunca un archivo a medias."""
    ALARMAS.parent.mkdir(parents=True, exist_ok=True)
    tmp = ALARMAS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"alarmas": lista}, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    os.replace(tmp, ALARMAS)


class Manejador(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    rangos = False      # solo los archivos anuncian que aceptan saltos

    # ---------- utilidades ----------

    def responder(self, codigo, obj):
        cuerpo = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def sesion(self):
        """El nombre de sesión si la ruta es /notas/<sesion>, o None si no lo es.
        Si lo parece pero no cuadra, contesta el error y devuelve False."""
        if not self.path.startswith("/notas/"):
            return None
        s = self.path[len("/notas/"):].split("?")[0].strip("/")
        if not existe(s):
            self.responder(404, {"error": "no existe la sesión %r" % s})
            return False
        return s

    def es_alarmas(self):
        return self.path.split("?")[0].rstrip("/") == "/alarmas"

    def es_foto(self):
        """La ruta /foto/<sesion>, que es el "ya lo vi" de las marcas de cambio.

        Toma la foto de referencia del deck y borra las marcas de una vez. Va
        por el servidor y no por el navegador porque hay que copiar un archivo,
        y una pestaña no puede. Sin servidor, el botón solo borra las marcas y
        la foto la toma `tools/cambios.py` en la pasada siguiente.
        """
        if not self.path.startswith("/foto/"):
            return None
        s = self.path[len("/foto/"):].split("?")[0].strip("/")
        if not existe(s):
            self.responder(404, {"error": "no existe la sesión %r" % s})
            return False
        return s

    def del_servidor(self):
        """El PUT solo se acepta desde una página servida por nosotros. Los
        navegadores mandan Origin en toda petición que no sea GET, así que esto
        deja fuera a cualquier otra pestaña abierta en la máquina."""
        o = self.headers.get("Origin")
        return o is None or o == base(self.server.server_address[1])

    # ---------- rutas ----------

    def do_GET(self):
        self.rangos = False
        if self.es_alarmas():
            try:
                return self.responder(200, {"alarmas": leer_alarmas()})
            except Exception as e:
                return self.responder(500, {"error": "alarmas.json ilegible: %s" % e})
        s = self.sesion()
        if s is False:
            return
        if s is None:
            return self.estatico()
        try:
            d = leer_notas(s)
            # Cuándo se tocó el deck por última vez. Es lo que le permite al
            # anotador enterarse de que las correcciones ya están aplicadas y
            # ofrecer recargar: las notas se actualizan solas, las láminas no.
            d["deck"] = int((RAIZ / "sesiones" / s / "index.html").stat().st_mtime)
            self.responder(200, d)
        except Exception as e:
            self.responder(500, {"error": "notas.json ilegible: %s" % e})

    def do_PUT(self):
        self.rangos = False
        if self.es_alarmas():
            return self.put_alarmas()
        f = self.es_foto()
        if f is False:
            return
        if f:
            return self.put_foto(f)
        s = self.sesion()
        if s is False:
            return
        if s is None:
            return self.responder(405, {"error": "aquí no se escribe"})
        if not self.del_servidor():
            return self.responder(403, {"error": "origen no permitido"})
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > LIMITE:
            return self.responder(413, {"error": "cuerpo vacío o demasiado grande"})
        try:
            envio = json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception as e:
            return self.responder(400, {"error": str(e)})
        # Un cuerpo que sea lista, número o texto es JSON válido y no tiene .get:
        # sin esto muere con AttributeError y el navegador ve un 500 sin motivo.
        if not isinstance(envio, dict):
            return self.responder(400, {"error": "el cuerpo tiene que ser un objeto"})
        with CANDADO:
            try:
                actual = leer_notas(s)
            except Exception as e:
                return self.responder(500, {"error": "notas.json ilegible: %s" % e})
            if envio.get("v") != actual["v"]:
                # Alguien escribió entre medias. Le devolvemos lo vigente para que
                # reaplique su cambio encima en vez de pisarlo.
                return self.responder(409, actual)
            # `pendientes` no lo toca el anotador, que ni lo conoce: se conserva
            # tal cual salvo que quien escribe lo mande explícitamente.
            # Lo que no venga en el envío se conserva, no se borra: así una
            # pestaña vieja, que no conoce un apartado nuevo, no se lo lleva.
            nuevo = {"v": actual["v"] + 1,
                     "notas": envio.get("notas") or {},
                     "guiones": envio.get("guiones") or {},
                     "cortos": envio.get("cortos", actual.get("cortos")) or {},
                     "recortes": envio.get("recortes", actual.get("recortes")) or {},
                     "orden": limpiar_orden(envio.get("orden", actual.get("orden"))),
                     "nuevas": limpiar_nuevas(envio.get("nuevas", actual.get("nuevas"))),
                     "borradas": limpiar_orden(envio.get("borradas", actual.get("borradas"))),
                     "fusiones": limpiar_fusiones(envio.get("fusiones", actual.get("fusiones"))),
                     "pendientes": envio.get("pendientes", actual.get("pendientes")) or [],
                     # `cambios` lo escribe tools/cambios.py y el anotador solo
                     # lo pinta: se conserva igual que `pendientes`. Quien lo
                     # borra es la acción "ya lo vi", que entra por /foto.
                     "cambios": envio.get("cambios", actual.get("cambios")) or {}}
            escribir_notas(s, nuevo)
        self.responder(200, {"v": nuevo["v"]})

    def put_foto(self, sesion):
        """"Ya lo vi": copia el deck de ahora como foto y borra las marcas.

        Las dos cosas van juntas y en este orden, porque si se borraran las
        marcas sin tomar la foto, la comparación siguiente volvería a sacar lo
        mismo que acaba de darse por visto.
        """
        if not self.del_servidor():
            return self.responder(403, {"error": "origen no permitido"})
        carp = RAIZ / "sesiones" / sesion
        try:
            shutil.copyfile(carp / "index.html", carp / ".antes.html")
        except Exception as e:
            return self.responder(500, {"error": "no pude tomar la foto: %s" % e})
        with CANDADO:
            d = leer_notas(sesion)
            d["cambios"] = {}
            d["v"] = int(d.get("v", 0)) + 1
            escribir_notas(sesion, d)
        self.responder(200, {"v": d["v"]})

    def put_alarmas(self):
        if not self.del_servidor():
            return self.responder(403, {"error": "origen no permitido"})
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > LIMITE:
            return self.responder(413, {"error": "cuerpo vacío o demasiado grande"})
        try:
            envio = json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception as e:
            return self.responder(400, {"error": str(e)})
        lista = limpiar_alarmas(envio.get("alarmas") if isinstance(envio, dict) else envio)
        with CANDADO:
            escribir_alarmas(lista)
        # se devuelve lo que quedó guardado, ya filtrado y ordenado, para que el
        # apuntador se quede con lo mismo que el disco y no con lo que mandó
        self.responder(200, {"alarmas": lista})

    # ---------- archivos, con saltos dentro del video ----------

    def end_headers(self):
        # Sin `Accept-Ranges` el navegador ni intenta saltar dentro de un video,
        # y los videos de la S02 son fragmentos concatenados: sin salto, todas
        # sus láminas muestran el primer clip del archivo.
        if self.rangos:
            self.send_header("Accept-Ranges", "bytes")
            # Y sin `Cache-Control`, el navegador decide por su cuenta cuánto
            # tiempo se fía de lo que ya tiene, y puede no volver a preguntar.
            # Aquí se edita el tema y el anotador en caliente: una hoja de
            # estilo vieja deja las láminas mal maquetadas sin avisar. Con
            # no-cache sigue preguntando, y la respuesta suele ser un 304.
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def estatico(self):
        """Como el servidor de siempre, pero atendiendo `Range`. Es lo que
        SimpleHTTPRequestHandler no hace y lo que un `<video>` necesita."""
        self.rangos = True
        ruta = self.translate_path(self.path)
        cabecera = self.headers.get("Range", "")
        m = re.match(r"bytes=(\d*)-(\d*)\s*$", cabecera.strip()) if cabecera else None
        if not m or not os.path.isfile(ruta):
            return super().do_GET()

        tam = os.path.getsize(ruta)
        desde, hasta = m.group(1), m.group(2)
        if desde == "":                      # bytes=-N: los últimos N
            if hasta == "":
                return super().do_GET()
            ini, fin = max(0, tam - int(hasta)), tam - 1
        else:
            ini = int(desde)
            fin = tam - 1 if hasta == "" else min(int(hasta), tam - 1)
        if ini > fin or ini >= tam:
            self.send_response(416)
            self.send_header("Content-Range", "bytes */%d" % tam)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        largo = fin - ini + 1
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(ruta))
        self.send_header("Content-Range", "bytes %d-%d/%d" % (ini, fin, tam))
        self.send_header("Content-Length", str(largo))
        self.send_header("Last-Modified", self.date_time_string(os.path.getmtime(ruta)))
        self.end_headers()
        if self.command == "HEAD":
            return
        with open(ruta, "rb") as f:
            f.seek(ini)
            queda = largo
            while queda > 0:
                trozo = f.read(min(64 * 1024, queda))
                if not trozo:
                    break
                self.wfile.write(trozo)
                queda -= len(trozo)

    def log_message(self, *a):
        pass


class Servidor(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def demonio(puerto):
    manejador = lambda *a, **k: Manejador(*a, directory=str(RAIZ), **k)
    Servidor(("127.0.0.1", puerto), manejador).serve_forever()


# ---------- arranque, parada y ligas ----------

def responde():
    """¿Contesta el puerto, y es lo nuestro?  True, False o None si no hay nadie."""
    try:
        with urllib.request.urlopen(base() + SENA, timeout=2) as r:
            return r.status == 200
    except urllib.error.HTTPError:
        return False
    except Exception:
        return None


def libre():
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", PUERTO)) != 0


def arrancar():
    if responde():
        return "ya estaba levantado"
    if not libre():
        sys.exit("El puerto %d está ocupado por otra cosa. Libéralo y repite." % PUERTO)
    subprocess.Popen([sys.executable, str(pathlib.Path(__file__).resolve()), "--demonio"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)
    for _ in range(50):
        if responde():
            return "levantado"
        time.sleep(0.1)
    sys.exit("El servidor no respondió. Revisa si el puerto %d está tomado." % PUERTO)


def parar():
    if responde() is None:
        print("No había nada que apagar.")
        return
    # No se guarda el pid: el servidor sobrevive a la terminal que lo lanzó, así
    # que se localiza por lo que es. El patrón no aparece en esta invocación.
    # El patrón lleva la ruta absoluta de ESTE archivo, no "servir.py", porque
    # hay otra copia del proyecto del curso corriendo su propio demonio y el
    # patrón corto se la llevaba por delante.
    subprocess.run(["pkill", "-f",
                    "%s --demonio" % pathlib.Path(__file__).resolve()], check=False)
    print("Servidor apagado.")


def sesiones():
    return sorted(d.name for d in (RAIZ / "sesiones").glob("S*")
                  if (d / "index.html").exists())


def liga(carpeta, revision=True):
    return "%s/sesiones/%s/index.html%s" % (base(), carpeta, "?review" if revision else "")


def busca(arg):
    """Acepta 3, 03, S03 o el nombre completo de la carpeta."""
    todas = sesiones()
    n = arg.strip().lstrip("Ss")
    prefijo = "S%02d-" % int(n) if n.isdigit() else None
    for c in todas:
        if c == arg.strip() or (prefijo and c.startswith(prefijo)):
            return c
    sys.exit("No encuentro la sesión %r. Hay: %s" % (arg, ", ".join(todas) or "ninguna"))


def main(args):
    if "--demonio" in args:
        return demonio(PUERTO)
    if "--parar" in args:
        return parar()
    print(arrancar(), "en", base())
    sueltos = [a for a in args if not a.startswith("-")]
    if sueltos:
        c = busca(sueltos[0])
        print("\nRevisión:  " + liga(c))
        print("Deck:      " + liga(c, revision=False))
        print("Notas:     sesiones/%s/notas.json" % c)
        return
    print()
    for c in sesiones():
        print("  " + liga(c))
    print("\nPara apagarlo:  python3 tools/servir.py --parar")


if __name__ == "__main__":
    main(sys.argv[1:])
