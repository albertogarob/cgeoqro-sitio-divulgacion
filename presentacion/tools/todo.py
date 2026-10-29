#!/usr/bin/env python3
"""Los pendientes de cada sesión, guardados en el archivo de esa sesión.

    python3 tools/todo.py                      # todo lo abierto, sesión por sesión
    python3 tools/todo.py 3                     # solo la S03
    python3 tools/todo.py 3 --todo              # incluye lo ya decidido
    python3 tools/todo.py 3 --abrir "texto"     # añade un pendiente
    python3 tools/todo.py 3 --abrir "texto" --transversal   # afecta a las 30 sesiones
    python3 tools/todo.py 3 --decidir p2        # lo pasa a decidido, no se borra
    python3 tools/todo.py 3 --borrar p9         # lo quita, para lo abierto por error
    python3 tools/todo.py --md                  # lo mismo, en Markdown, para TODO.md

Viven en el apartado `pendientes` de `sesiones/SNN-.../notas.json`, uno por
sesión. Esa es la razón de que estén ahí y no todos juntos en TODO.md: con
varios agentes corrigiendo sesiones distintas a la vez, cada uno escribe solo en
el archivo de la suya y nadie pisa a nadie.

Lo decidido no se borra: queda como registro de lo que no hay que volver a
abrir, que es para lo que servía esa sección de TODO.md.
"""
import argparse, csv, datetime, textwrap, importlib.util, json, pathlib, sys, urllib.error, urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def carga_servir():
    spec = importlib.util.spec_from_file_location("servir", RAIZ / "tools" / "servir.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


SERVIR = carga_servir()


def bajar(sesion):
    if SERVIR.responde() is True:
        with urllib.request.urlopen(SERVIR.base() + "/notas/" + sesion, timeout=5) as r:
            return json.loads(r.read().decode())
    return SERVIR.leer_notas(sesion)


def subir(sesion, doc):
    """Por el servidor si lo hay, que es lo que serializa las escrituras."""
    if SERVIR.responde() is True:
        req = urllib.request.Request(
            SERVIR.base() + "/notas/" + sesion,
            data=json.dumps(doc).encode(), method="PUT",
            headers={"Content-Type": "application/json", "Origin": SERVIR.base()})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return json.loads(r.read().decode())["v"]
        except urllib.error.HTTPError as e:
            if e.code == 409:
                sys.exit("Alguien escribió mientras tanto. Repite el comando.")
            raise
    doc = dict(doc, v=doc["v"] + 1)
    SERVIR.escribir_notas(sesion, doc)
    return doc["v"]


def titulo(sesion):
    """El nombre legible de la sesión, de admin/sesiones.csv. La carpeta sola se
    lee mal como encabezado: viene recortada y sin acentos."""
    try:
        with open(RAIZ / "admin" / "sesiones.csv", encoding="utf-8") as f:
            for fila in csv.DictReader(f):
                if pathlib.PurePath(fila["carpeta"]).name == sesion:
                    return "S%02d. %s  (%s)" % (int(fila["num"]), fila["tema"], fila["fecha"])
    except Exception:
        pass
    return sesion


def hoy():
    return datetime.date.today().isoformat()


def nuevo_id(pendientes):
    usados = {int(x["id"][1:]) for x in pendientes if str(x.get("id", "")).startswith("p")
              and x["id"][1:].isdigit()}
    return "p%d" % (max(usados, default=0) + 1)


def envuelve(texto, sangria):
    """En la terminal, un párrafo de diez renglones sin envolver no se lee."""
    return textwrap.fill(texto, width=94, initial_indent=sangria,
                         subsequent_indent=" " * len(sangria))


def pinta(sesion, pendientes, todos, md=False, aparte=()):
    """`aparte` son los pendientes que ya se listan en otro sitio, los
    transversales cuando se está mirando el curso entero."""
    fuera = {id(x) for x in aparte}
    abiertos = [x for x in pendientes
                if x.get("estado") != "decidido" and id(x) not in fuera]
    decididos = [x for x in pendientes
                 if x.get("estado") == "decidido" and id(x) not in fuera]
    if not abiertos and not (todos and decididos):
        return False
    print("\n" + ("## " + titulo(sesion) if md else titulo(sesion)))
    for x in abiertos:
        t = "  [transversal]" if x.get("transversal") else ""
        if md:
            print("- %s%s" % (x["texto"], t))
        else:
            print(envuelve(x["texto"] + t, "  %-4s" % x.get("id", "?")))
    if todos and decididos:
        print("\n" + ("### Decidido, no volver a abrir" if md else "  Decidido, no volver a abrir:"))
        for x in decididos:
            print(("- " + x["texto"]) if md else envuelve(x["texto"], "  %-4s" % x.get("id", "?")))
    return True


def main():
    ap = argparse.ArgumentParser(description="Pendientes por sesión.")
    ap.add_argument("sesion", nargs="?", help="3, S03 o el nombre de la carpeta")
    ap.add_argument("--abrir", nargs="+", metavar="TEXTO", default=[])
    ap.add_argument("--decidir", nargs="+", metavar="ID", default=[])
    ap.add_argument("--borrar", nargs="+", metavar="ID", default=[],
                    help="quita un pendiente abierto por error; lo atendido va con --decidir")
    ap.add_argument("--transversal", action="store_true",
                    help="con --abrir, marca que afecta a las 30 sesiones")
    ap.add_argument("--todo", action="store_true", help="incluye lo ya decidido")
    ap.add_argument("--md", action="store_true", help="salida en Markdown")
    a = ap.parse_args()

    if a.abrir or a.decidir or a.borrar:
        if not a.sesion:
            sys.exit("Dime de qué sesión.")
        sesion = SERVIR.busca(a.sesion)
        doc = bajar(sesion)
        pendientes = doc.get("pendientes") or []
        for texto in a.abrir:
            pendientes.append({"id": nuevo_id(pendientes), "texto": texto,
                               "estado": "abierto", "transversal": a.transversal,
                               "ts": hoy()})
        faltan = [i for i in a.decidir + a.borrar
                  if not any(x.get("id") == i for x in pendientes)]
        if faltan:
            sys.exit("Estos pendientes no están en %s: %s" % (sesion, ", ".join(faltan)))
        for x in pendientes:
            if x.get("id") in a.decidir:
                x["estado"] = "decidido"
        pendientes = [x for x in pendientes if x.get("id") not in a.borrar]
        doc["pendientes"] = pendientes
        v = subir(sesion, doc)
        print("%s: %d abierto%s, %d decidido%s, %d borrado%s. Versión %d."
              % (sesion, len(a.abrir), "" if len(a.abrir) == 1 else "s",
                 len(a.decidir), "" if len(a.decidir) == 1 else "s",
                 len(a.borrar), "" if len(a.borrar) == 1 else "s", v))
        return

    sesiones = [SERVIR.busca(a.sesion)] if a.sesion else SERVIR.sesiones()
    if a.md:
        print("# Pendientes\n")
        print("Generado con `python3 tools/todo.py --md%s`. **No editar a mano**: los pendientes"
              % (" --todo" if a.todo else ""))
        print("viven en el apartado `pendientes` del `notas.json` de cada sesión, y se abren y")
        print("cierran con `tools/todo.py`. Este archivo es una vista, como `guion.md`.\n")
        print("Al %s." % datetime.date.today().strftime("%d de %B de %Y")
              .replace("September", "septiembre").replace("October", "octubre")
              .replace("November", "noviembre").replace("December", "diciembre"))
    todos_los_puntos = {s: (bajar(s).get("pendientes") or []) for s in sesiones}
    # Los transversales se sacan de su sesión y se listan juntos: viven en el
    # archivo de la sesión que los levantó, pero no son de esa sesión.
    transversales = [] if a.sesion else [
        x for s in sesiones for x in todos_los_puntos[s] if x.get("transversal")]
    abiertos_t = [x for x in transversales if x.get("estado") != "decidido"]
    cerrados_t = [x for x in transversales if x.get("estado") == "decidido"]
    if abiertos_t or (a.todo and cerrados_t):
        print("\n" + ("## Transversal" if a.md else "Transversal, afecta a las 30 sesiones"))
        for x in abiertos_t:
            print(("- " + x["texto"]) if a.md else envuelve(x["texto"], "      "))
        if a.todo and cerrados_t:
            print("\n" + ("### Decidido, no volver a abrir" if a.md
                          else "  Decidido, no volver a abrir:"))
            for x in cerrados_t:
                print(("- " + x["texto"]) if a.md else envuelve(x["texto"], "      "))
    algo = bool(abiertos_t)
    for s in sesiones:
        algo = pinta(s, todos_los_puntos[s], a.todo, a.md, aparte=transversales) or algo
    if not algo:
        print("No hay nada pendiente.")



if __name__ == "__main__":
    main()
