#!/usr/bin/env python3
r"""Qué cambió en el deck desde la última vez que Alberto lo miró.

    python3 tools/cambios.py NN            # compara y guarda lo que cambió
    python3 tools/cambios.py NN --ver      # lo enseña sin guardar nada
    python3 tools/cambios.py NN --foto     # toma la foto de referencia y borra las marcas
    python3 tools/cambios.py NN --olvidar  # igual que --foto

Al corregir una sesión, Alberto quiere **ver los cambios donde están**: marcados
en la propia lámina y en la propia ventana del guion, no en un reporte mío. Lo
pidió el 12 de octubre de 2026.

**Cómo funciona.** Se guarda una foto del deck en `sesiones/SNN-.../.antes.html`,
y esta herramienta compara esa foto con el `index.html` de ahora, palabra a
palabra. Lo que sale se escribe en el apartado `cambios` de `notas.json`, que es
lo único que lee `plantillas/tema-centrogeo/revisar.js` para pintar las marcas.

**La foto se toma cuando Alberto pulsa "ya lo vi", no al empezar cada ronda.**
Así, si se corren tres rondas seguidas sin que él mire, ve todo lo que cambió
desde la última vez que lo vio, y no solo lo último.

**Por qué se compara aquí y no en el navegador.** Por lo mismo que en
`parcelas.py` y en `anclas.py`: cuando el deck llega al navegador, MathJax ya se
llevó el texto de las expresiones, así que media sesión no se podría comparar.
Aquí se lee el HTML crudo, donde el texto todavía está.

**Qué se compara, y qué no.** Se compara el texto que se ve: el cuerpo pieza a
pieza, el guion párrafo a párrafo, el guion corto, el nivel de recorte, y qué
láminas se añadieron, se borraron o se movieron. **Los atributos no**, así que
volver a correr `citas.py`, `parcelas.py` o `anclas.py` no produce ruido: una
pasada que solo renumera no cambia nada.

Su prueba de regresión es `tools/prueba-cambios.py`.
"""
import difflib
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anclas  # noqa: E402  (laminas_de, sin_asides, plano)

PUERTO = 8931


def carpeta(num):
    """La carpeta de la sesión NN, por su número."""
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sesiones")
    pref = "S%02d-" % int(num)
    for d in sorted(os.listdir(base)):
        if d.startswith(pref):
            return os.path.normpath(os.path.join(base, d))
    raise SystemExit("no encuentro la carpeta de la sesión %s" % num)


def texto_de(trozo):
    """El texto visible de un trozo, normalizado para comparar."""
    return re.sub(r'\s+', ' ', anclas.plano(trozo)).strip()


def piezas_visibles(cuerpo):
    """(numero, texto) de cada pieza del cuerpo, en orden.

    El número es el `data-pieza` que escribió `tools/anclas.py`, que es por
    donde el navegador encuentra el elemento. Si la sesión todavía no ha pasado
    por esa herramienta, el número es None y la lámina se marca entera.
    """
    vis = anclas.sin_asides(cuerpo)
    out = []
    for ini, fin, tag, trozo in anclas.piezas_de(vis):
        m = re.search(r'data-pieza="(\d+)"', trozo[:trozo.find('>') + 1])
        out.append((m.group(1) if m else None, texto_de(trozo)))
    return out


def parrafos_de(cuerpo, clase):
    """El texto de cada `<p>` de ese bloque de notas, en orden."""
    m = re.search(r'<aside\b[^>]*class="[^"]*\b%s\b[^"]*"[^>]*>(.*?)</aside>' % clase,
                  cuerpo, re.S)
    if not m:
        return []
    return [texto_de(x) for x in re.findall(r'<p\b[^>]*>(.*?)</p>', m.group(1), re.S)]


def palabras(t):
    """Las unidades del diff: palabras con el espacio que las separa."""
    return re.findall(r'\S+\s*', t)


def diferencia(antes, ahora):
    """El diff palabra a palabra, como lista de [op, texto] con op =, + o -.

    Devuelve None si los dos textos son iguales, que es lo que permite callar
    todo lo que no cambió.
    """
    if antes == ahora:
        return None
    a, b = palabras(antes), palabras(ahora)
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if op == "equal":
            out.append(["=", "".join(a[i1:i2])])
        else:
            if i1 != i2:
                out.append(["-", "".join(a[i1:i2])])
            if j1 != j2:
                out.append(["+", "".join(b[j1:j2])])
    return out


def recorte_de(attrs):
    m = re.search(r'data-recorte="(\d)"', attrs)
    return m.group(1) if m else None


def lee(ruta):
    """Las láminas de un deck, indexadas por su identificador."""
    html = open(ruta, encoding="utf-8").read()
    out, orden = {}, []
    for ini, fin, attrs, cuerpo in anclas.laminas_de(html):
        sid = (re.search(r'data-sid="([^"]+)"', attrs)
               or re.search(r'id="([^"]+)"', attrs) or [None, None])[1]
        if not sid:
            continue
        orden.append(sid)
        h = re.search(r'<h1\b[^>]*>(.*?)</h1>|<h2\b[^>]*>(.*?)</h2>', cuerpo, re.S)
        titulo = texto_de((h.group(1) or h.group(2)) if h else "") or sid
        out[sid] = {"titulo": titulo, "piezas": piezas_visibles(cuerpo),
                    "guion": parrafos_de(cuerpo, "notes"),
                    "corto": parrafos_de(cuerpo, "corto"),
                    "recorte": recorte_de(attrs)}
    return out, orden


def alinea(a, b):
    """Empareja dos listas de textos y devuelve (i, j) por par.

    Con `None` donde algo se fue o llegó. Se alinea por contenido y no por
    posición, para que insertar una viñeta no desplace a todas las demás.
    """
    pares = []
    sm = difflib.SequenceMatcher(None, a, b)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                pares.append((i1 + k, j1 + k))
        elif op == "replace":
            # se emparejan de a uno mientras haya de los dos
            n = max(i2 - i1, j2 - j1)
            for k in range(n):
                pares.append((i1 + k if i1 + k < i2 else None,
                              j1 + k if j1 + k < j2 else None))
        elif op == "delete":
            for k in range(i1, i2):
                pares.append((k, None))
        else:
            for k in range(j1, j2):
                pares.append((None, k))
    return pares


def compara(antes, ahora):
    """Lo que cambió entre dos decks: un diccionario por lámina."""
    va, oa = antes
    vb, ob = ahora
    laminas = {}

    for sid in ob:
        b = vb[sid]
        if sid not in va:
            laminas[sid] = {"estado": "nueva", "titulo": b["titulo"]}
            continue
        a = va[sid]
        cam = {"estado": "cambiada", "titulo": b["titulo"],
               "piezas": [], "guion": [], "corto": []}

        ta = [t for _, t in a["piezas"]]
        tb = [t for _, t in b["piezas"]]
        for i, j in alinea(ta, tb):
            d = diferencia(ta[i] if i is not None else "",
                           tb[j] if j is not None else "")
            if d:
                cam["piezas"].append({"n": b["piezas"][j][0] if j is not None else None,
                                      "dif": d})
        for clave in ("guion", "corto"):
            for i, j in alinea(a[clave], b[clave]):
                d = diferencia(a[clave][i] if i is not None else "",
                               b[clave][j] if j is not None else "")
                if d:
                    cam[clave].append({"i": j, "dif": d})
        if a["recorte"] != b["recorte"]:
            cam["recorte"] = [a["recorte"], b["recorte"]]
        # movida: cambió de sitio en el deck y no es por lo que entró o salió
        if sid in oa and oa.index(sid) != ob.index(sid):
            vecinas_a = [x for x in oa if x in vb]
            if vecinas_a.index(sid) != ob.index(sid):
                cam["movida"] = [oa.index(sid) + 1, ob.index(sid) + 1]

        if (cam["piezas"] or cam["guion"] or cam["corto"]
                or "recorte" in cam or "movida" in cam):
            laminas[sid] = cam

    for sid in oa:
        if sid not in vb:
            laminas[sid] = {"estado": "borrada", "titulo": va[sid]["titulo"]}
    return laminas


# --------------------------------------------------------------- notas.json
def ruta_notas(carp):
    return os.path.join(carp, "notas.json")


def leer_notas(carp):
    f = ruta_notas(carp)
    if not os.path.exists(f):
        return {"v": 0}
    return json.load(open(f, encoding="utf-8"))


def guardar_notas(carp, doc):
    """Escribe por el servidor si está, que es lo que avisa a la pestaña abierta.

    **La versión va tal como se leyó, y la sube el servidor.** Mandarla ya
    subida es un conflicto y el envío se rechaza con un 409; costó un rato
    descubrirlo porque el error caía en el respaldo y la pestaña abierta se
    quedaba sin enterarse, en silencio.
    """
    sesion = os.path.basename(carp)
    cuerpo = json.dumps(doc, ensure_ascii=False, indent=1).encode("utf-8")
    try:
        req = urllib.request.Request("http://127.0.0.1:%d/notas/%s" % (PUERTO, sesion),
                                     data=cuerpo, method="PUT",
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=3).read()
        return "por el servidor"
    except urllib.error.HTTPError as e:
        print("   AVISO: el servidor rechazó el envío (%s). Se escribe el archivo, "
              "y la pestaña abierta no se enterará hasta recargar." % e.code)
    except Exception:
        pass
    doc["v"] = int(doc.get("v", 0)) + 1
    open(ruta_notas(carp), "w", encoding="utf-8").write(
        json.dumps(doc, ensure_ascii=False, indent=1))
    return "en el archivo"


def main(argv):
    num = None
    ver = foto = False
    for a in argv:
        if a in ("--ver",):
            ver = True
        elif a in ("--foto", "--olvidar"):
            foto = True
        elif not a.startswith("-"):
            num = a
    if num is None:
        raise SystemExit("uso: python3 tools/cambios.py NN [--ver|--foto]")

    carp = carpeta(num)
    deck = os.path.join(carp, "index.html")
    ref = os.path.join(carp, ".antes.html")

    if foto:
        shutil.copyfile(deck, ref)
        doc = leer_notas(carp)
        tenia = len((doc.get("cambios") or {}).get("laminas") or {})
        # Vacío, no ausente. El servidor conserva lo que el envío no menciona,
        # que es lo que protege a `pendientes` de una pestaña vieja; quitar la
        # llave significa "no lo toques", así que borrarla aquí resucitaba lo
        # que se acababa de dar por visto. Costó encontrarlo porque el archivo
        # quedaba bien cuando no había servidor.
        doc["cambios"] = {}
        donde = guardar_notas(carp, doc)
        print("cambios.py: foto tomada, %d láminas marcadas se olvidan (%s)"
              % (tenia, donde))
        return 0

    if not os.path.exists(ref):
        # Primera vez: no hay con qué comparar, así que se toma la foto y ya.
        shutil.copyfile(deck, ref)
        print("cambios.py: no había foto de referencia; se toma ahora y no se "
              "marca nada. La próxima pasada ya comparará.")
        return 0

    laminas = compara(lee(ref), lee(deck))
    if ver:
        if not laminas:
            print("cambios.py: nada cambió desde la última foto")
            return 0
        for sid, c in laminas.items():
            print("%s  [%s]  %s" % (sid, c["estado"], c.get("titulo", "")))
            for p in c.get("piezas", []):
                print("   cuerpo, pieza %s: %s" % (p["n"], resumen(p["dif"])))
            for p in c.get("guion", []):
                print("   guion, párrafo %s: %s" % (p["i"], resumen(p["dif"])))
            for p in c.get("corto", []):
                print("   corto, párrafo %s: %s" % (p["i"], resumen(p["dif"])))
            if "recorte" in c:
                print("   nivel de recorte: %s -> %s" % tuple(
                    x or "núcleo" for x in c["recorte"]))
            if "movida" in c:
                print("   movida de la posición %d a la %d" % tuple(c["movida"]))
        return 0

    doc = leer_notas(carp)
    if not laminas:
        tenia = bool((doc.get("cambios") or {}).get("laminas"))
        doc["cambios"] = {}
        if tenia:
            guardar_notas(carp, doc)
        print("cambios.py: nada cambió desde la última foto")
        return 0

    # Qué notas se cerraron desde la foto: las que ya no están vivas.
    antes_doc = (doc.get("cambios") or {})
    doc["cambios"] = {"sello": antes_doc.get("sello") or "",
                      "laminas": laminas}
    donde = guardar_notas(carp, doc)
    npz = sum(len(c.get("piezas", [])) for c in laminas.values())
    ngu = sum(len(c.get("guion", [])) + len(c.get("corto", []))
              for c in laminas.values())
    print("cambios.py: %d láminas tocadas, %d piezas del cuerpo y %d párrafos "
          "del guion (%s)" % (len(laminas), npz, ngu, donde))
    return 0


def resumen(dif):
    mas = sum(len(t.split()) for op, t in dif if op == "+")
    menos = sum(len(t.split()) for op, t in dif if op == "-")
    trozo = " ".join(t.strip() for op, t in dif if op == "+")[:46]
    return "+%d -%d  %s" % (mas, menos, trozo)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
