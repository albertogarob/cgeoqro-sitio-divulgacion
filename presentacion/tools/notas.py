#!/usr/bin/env python3
"""Lee las notas de revisión de una sesión, y da por resueltas las corregidas.

    python3 tools/notas.py 3                      # qué hay pendiente
    python3 tools/notas.py 3 --json               # el documento crudo
    python3 tools/notas.py 3 --resuelto n1 n2     # borra esas notas, por su nid
    python3 tools/notas.py 3 --guion evaluacion   # y esa reescritura, ya aplicada
    python3 tools/notas.py 3 --corto alphazero    # y ese guion corto, ya aplicado
    python3 tools/notas.py 3 --recorte alphazero  # y ese nivel de recorte

Las notas viven en sesiones/SNN-.../notas.json, que escribe el anotador a
través de tools/servir.py. Este script existe para no tener que editar ese
archivo a mano, porque hay dos cosas fáciles de olvidar y con consecuencias:

- **Subir el contador `v`.** Es lo que hace que la pestaña abierta de Alberto se
  entere del cambio y quite los resaltados. Si no sube, su navegador no solo no
  se entera: la próxima nota que escriba sobrevive con la versión vieja y
  resucita lo que acabas de borrar.
- **Escribir a través del servidor si está levantado**, que es la vía sin
  carreras. Solo si no lo está se toca el archivo directamente.

Nunca des por resuelta una nota que no corregiste: si se borra, se pierde.
"""
import argparse, importlib.util, json, pathlib, sys, urllib.error, urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def carga_servir():
    spec = importlib.util.spec_from_file_location("servir", RAIZ / "tools" / "servir.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


SERVIR = carga_servir()


def hay_servidor():
    return SERVIR.responde() is True


def bajar(sesion):
    if hay_servidor():
        with urllib.request.urlopen(SERVIR.base() + "/notas/" + sesion, timeout=5) as r:
            return json.loads(r.read().decode())
    return SERVIR.leer_notas(sesion)


def subir(sesion, doc):
    """Por el servidor si lo hay, que es lo que evita carreras con el navegador."""
    if hay_servidor():
        req = urllib.request.Request(
            SERVIR.base() + "/notas/" + sesion,
            data=json.dumps(doc).encode(), method="PUT",
            headers={"Content-Type": "application/json", "Origin": SERVIR.base()})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return json.loads(r.read().decode())["v"], "por el servidor"
        except urllib.error.HTTPError as e:
            if e.code == 409:
                sys.exit("Alguien escribió mientras tanto. Vuelve a leer las notas y repite.")
            raise
    doc = dict(doc, v=doc["v"] + 1)
    SERVIR.escribir_notas(sesion, doc)
    return doc["v"], "directo al archivo, sin servidor"


NIVEL = {0: "núcleo, sin data-recorte", 1: 'data-recorte="1"', 2: 'data-recorte="2"'}


def listar(sesion, doc):
    notas = doc.get("notas") or {}
    guiones = doc.get("guiones") or {}
    cortos = doc.get("cortos") or {}
    recortes = doc.get("recortes") or {}
    orden = doc.get("orden") or []
    nuevas = doc.get("nuevas") or []
    borradas = doc.get("borradas") or []
    fusiones = doc.get("fusiones") or []
    total = sum(len(v) for v in notas.values())
    print("%s   versión %d   %d nota%s   %d guion%s reescrito%s   "
          "%d guion%s corto%s   %d recorte%s"
          % (sesion, doc.get("v", 0), total, "" if total == 1 else "s",
             len(guiones), "" if len(guiones) == 1 else "es",
             "" if len(guiones) == 1 else "s",
             len(cortos), "" if len(cortos) == 1 else "es",
             "" if len(cortos) == 1 else "s",
             len(recortes), "" if len(recortes) == 1 else "s"))
    if orden or nuevas or borradas or fusiones:
        print("   y en la rejilla: %s"
              % ", ".join(filter(None, [
                  "el orden cambiado" if orden else "",
                  "%d lámina%s por escribir" % (len(nuevas), "" if len(nuevas) == 1 else "s")
                  if nuevas else "",
                  "%d por borrar" % len(borradas) if borradas else "",
                  "%d combinación%s" % (len(fusiones), "" if len(fusiones) == 1 else "es")
                  if fusiones else ""])))
    if not total and not guiones and not cortos and not recortes and not orden \
            and not nuevas and not borradas and not fusiones:
        print("\nNo hay nada pendiente.")
        return
    for lamina, lista in notas.items():
        print("\n" + lamina)
        for x in lista:
            marca = {"guion": "  (guion)", "corto": "  (guion corto)"}.get(x.get("ambito"), "")
            print("  %s%s" % (x.get("nid", "?"), marca))
            if x.get("cita"):
                print('    cita: "%s"' % x["cita"])
            for renglon in str(x.get("texto", "")).splitlines():
                print("    " + renglon)
    for lamina, g in guiones.items():
        print("\n%s  (guion reescrito, pendiente de aplicar)" % lamina)
        for renglon in str(g.get("texto", "")).splitlines():
            print("    " + renglon)
    for lamina, c in cortos.items():
        print("\n%s  (guion corto, pendiente de aplicar al aside class=\"corto\")" % lamina)
        for renglon in str(c.get("texto", "")).splitlines():
            print("    " + renglon)
    for lamina, x in recortes.items():
        print("\n%s  (nivel de recorte, pendiente de aplicar al section)" % lamina)
        print("    " + NIVEL.get(int(x.get("nivel", 0)), "?"))
    for x in nuevas:
        print("\n%s  (lámina por escribir, pendiente de aplicar al deck)" % x.get("id", "?"))
        for renglon in str(x.get("texto") or "(sin descripción)").splitlines():
            print("    " + renglon)
    for x in borradas:
        print("\n%s  (lámina marcada para borrar)" % x)
    for f in fusiones:
        print("\n%s  (láminas que hay que combinar en una)" % f.get("id", "?"))
        print("    en %s: %s" % ((f.get("partes") or ["?"])[0], ", ".join(f.get("partes") or [])))
        for renglon in str(f.get("texto") or
                           "(sin nota: el criterio lo decides tú al escribirla)").splitlines():
            print("    " + renglon)
    if orden or nuevas or borradas or fusiones:
        # Esto no se cierra desde aquí: lo aplica y lo cierra reordenar.py, que
        # es quien mueve, mete y saca los <section> del HTML.
        print("\n(cambios de la rejilla, pendientes de aplicar al deck)")
        print("    %d lámina%s en la lista del orden. Se aplica todo con:"
              % (len(orden), "" if len(orden) == 1 else "s"))
        print("    python3 tools/reordenar.py %s --ver     para ver qué se mueve" % sesion)
        print("    python3 tools/reordenar.py %s           para aplicarlo" % sesion)


def resolver(sesion, doc, nids, laminas, cortas, niveles):
    notas = doc.get("notas") or {}
    vistos = {x.get("nid") for lista in notas.values() for x in lista}
    fantasmas = [n for n in nids if n not in vistos]
    if fantasmas:
        sys.exit("Estos nid no están en las notas de %s: %s" % (sesion, ", ".join(fantasmas)))
    guiones = doc.get("guiones") or {}
    cortos = doc.get("cortos") or {}
    recortes = doc.get("recortes") or {}
    for lista, mapa, que in ((laminas, guiones, "guion reescrito"),
                             (cortas, cortos, "guion corto"),
                             (niveles, recortes, "nivel de recorte")):
        faltan = [g for g in lista if g not in mapa]
        if faltan:
            sys.exit("Estas láminas no tienen %s pendiente: %s" % (que, ", ".join(faltan)))

    fuera = set(nids)
    quedan, borradas = {}, 0
    for lamina, lista in notas.items():
        resto = [x for x in lista if x.get("nid") not in fuera]
        borradas += len(lista) - len(resto)
        if resto:
            quedan[lamina] = resto
    for g in laminas:
        del guiones[g]
    for g in cortas:
        del cortos[g]
    for g in niveles:
        del recortes[g]
    # Se sube el documento entero, con lo que no se toca tal cual: si se armara
    # uno nuevo con solo estos apartados, sin servidor se perderían los demás.
    doc = dict(doc, notas=quedan, guiones=guiones, cortos=cortos, recortes=recortes)
    v, como = subir(sesion, doc)
    vivas = sum(len(x) for x in quedan.values())
    print("Resueltas %d nota%s, %d guion%s, %d corto%s y %d recorte%s."
          % (borradas, "" if borradas == 1 else "s",
             len(laminas), "" if len(laminas) == 1 else "es",
             len(cortas), "" if len(cortas) == 1 else "s",
             len(niveles), "" if len(niveles) == 1 else "s"))
    print("Quedan %d nota%s, %d guion%s, %d corto%s y %d recorte%s."
          % (vivas, "" if vivas == 1 else "s",
             len(guiones), "" if len(guiones) == 1 else "es",
             len(cortos), "" if len(cortos) == 1 else "s",
             len(recortes), "" if len(recortes) == 1 else "s"))
    print("Versión %d, escrito %s." % (v, como))
    if hay_servidor():
        print("La pestaña abierta de Alberto lo verá en unos segundos, sin recargar.")


def main():
    ap = argparse.ArgumentParser(description="Notas de revisión de una sesión.")
    ap.add_argument("sesion", help="3, S03 o el nombre de la carpeta")
    ap.add_argument("--json", action="store_true", help="el documento crudo")
    ap.add_argument("--resuelto", nargs="+", metavar="NID", default=[],
                    help="nid de las notas ya corregidas")
    ap.add_argument("--guion", nargs="+", metavar="LAMINA", default=[],
                    help="id de las láminas cuyo guion reescrito ya se aplicó")
    ap.add_argument("--corto", nargs="+", metavar="LAMINA", default=[],
                    help="id de las láminas cuyo guion corto ya se aplicó")
    ap.add_argument("--recorte", nargs="+", metavar="LAMINA", default=[],
                    help="id de las láminas cuyo nivel de recorte ya se aplicó")
    a = ap.parse_args()

    sesion = SERVIR.busca(a.sesion)
    doc = bajar(sesion)
    if a.resuelto or a.guion or a.corto or a.recorte:
        return resolver(sesion, doc, a.resuelto, a.guion, a.corto, a.recorte)
    if a.json:
        print(json.dumps(doc, ensure_ascii=False, indent=1))
        return
    listar(sesion, doc)


if __name__ == "__main__":
    main()
