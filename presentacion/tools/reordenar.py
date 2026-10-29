#!/usr/bin/env python3
"""Lleva al HTML lo que quedó pendiente en la rejilla de la revisión.

    python3 tools/reordenar.py sesiones/SNN-.../index.html
    python3 tools/reordenar.py NN
    python3 tools/reordenar.py NN --ver        solo enseña qué se movería

En la rejilla del anotador, la tecla R de revisar.js, las láminas se arrastran
con el ratón para cambiarlas de sitio, se piden láminas nuevas y se marcan las
que sobran. Eso no toca el deck: los tres cambios viajan como pendientes en
`orden`, `nuevas` y `borradas` de sesiones/SNN-.../notas.json, igual que los
guiones reescritos y los niveles de recorte, y el HTML sigue siendo la fuente
única. Este script es el que los aplica, los tres a la vez.

Qué hace, en orden:

  1. lee `orden`, `nuevas` y `borradas` de notas.json;
  2. concilia el orden con lo que hay hoy en el deck, por si se insertaron o se
     borraron láminas después de arrastrar: las que ya no existen se caen, y las
     que la lista no menciona se meten detrás de la vecina que las precede;
  3. mueve los <section> del index.html a ese orden, sin tocar una sola letra de
     su contenido; saca los de las láminas borradas; y mete, en el sitio que les
     toca, un <section> con data-pendiente por cada lámina por escribir, con la
     descripción de lo que debe contener;
  4. deja los tres pendientes cerrados en notas.json, subiendo su contador de
     versión, que es lo que hace que la pestaña abierta se entere.

Una lámina por escribir es un encargo, no una lámina: hay que escribirla después.
Mientras lleve `data-pendiente`, tools/empaquetar.py se niega a entregar el
paquete, así que no hay manera de que un hueco mío llegue al grupo.

No reescribe nada más. Después hay que regenerar lo que se deriva del deck:

    python3 tools/guion.py    sesiones/SNN-.../index.html
    python3 tools/apuntes.py  sesiones/SNN-.../index.html
    python3 tools/citas.py    sesiones/SNN-.../index.html
    python3 tools/empaquetar.py sesiones/SNN-.../index.html

El archivo anterior queda en sesiones/SNN-.../index.html.bak.orden.AAAAMMDDTHHMMSS,
uno por pasada y sin pisarse, porque el proyecto no está bajo control de versiones
y una permutación de sesenta láminas no se deshace a mano.
"""
import html as html_mod
import importlib.util
import json
import os
import re
import sys
import time
import pathlib
import urllib.error
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent

# Un recorrido de etiquetas, saltando lo que no cuenta: comentarios, scripts y
# hojas de estilo pueden llevar dentro un "<section" que no es una lámina.
TOKEN = re.compile(
    r"<!--.*?-->|<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>"
    r"|<(?P<cierre>/?)(?P<tag>div|section)\b[^>]*>",
    re.S | re.I,
)
ABRE_SLIDES = re.compile(r'<div\b[^>]*\bclass\s*=\s*"[^"]*\bslides\b[^"]*"[^>]*>', re.I)
ATRIB = re.compile(r'\b(?P<cual>data-sid|id)\s*=\s*"(?P<val>[^"]*)"', re.I)
# Un id que valga como atributo HTML sin escapar. Los que pone el anotador son
# así; uno con comillas o con & solo puede venir de editar notas.json a mano, y
# entonces el bloque se escaparía y ya no coincidiría consigo mismo.
ID_OK = re.compile(r"^[A-Za-z0-9._:-]{1,120}$")
# Las marcas de fusión que pone este script, para quitarlas antes de volver a
# ponerlas: así una fusión deshecha en la rejilla se limpia del HTML sola.
COMBI = re.compile(r"""\s+data-combinar(?:-en|-nota)?=(?:"[^"]*"|'[^']*')""", re.I | re.X)
# El final de una etiqueta de apertura, saltando los `>` que van dentro de un
# valor entrecomillado: un data-tip="si x > 0" no acaba la etiqueta.
FIN_ETIQ = re.compile(r'"[^"]*"|\'[^\']*\'|>')
COMENTARIO = re.compile(r"<!--.*?-->", re.S)


class Error(Exception):
    pass


def laminas(html):
    """Los <section> de primer nivel dentro de <div class="slides">.

    Devuelve (bloques, fin), donde bloques es la lista de (inicio, fin, id) de
    cada lámina, en el orden en que están escritas, y fin es dónde acaba el
    div de las láminas. Los tramos entre bloques, que son sangrías y saltos de
    línea, no se tocan ni se mueven: se quedan donde están.
    """
    # Un comentario que mencione el div de las láminas no es el div de las
    # láminas: se tapan antes de buscarlo, conservando las posiciones.
    m = ABRE_SLIDES.search(COMENTARIO.sub(lambda c: " " * len(c.group(0)), html))
    if not m:
        raise Error('no encuentro <div class="slides"> en el deck')
    divs, secs, ini, bloques, fin = 1, 0, None, [], None
    pos = m.end()
    while True:
        t = TOKEN.search(html, pos)
        if not t:
            break
        pos = t.end()
        if not t.group("tag"):
            continue                       # comentario, script o estilo: de largo
        cierra, tag = t.group("cierre") == "/", t.group("tag").lower()
        if tag == "div":
            divs += -1 if cierra else 1
            if divs == 0:                  # se acabó el div de las láminas
                fin = t.start()
                break
        elif cierra:
            secs -= 1
            if secs == 0:
                bloques.append((ini, t.end(), identidad(html[ini:t.end()])))
        else:
            if secs == 0:
                ini = t.start()
            secs += 1
    if fin is None:
        raise Error('el <div class="slides"> no cierra')
    if secs != 0:
        raise Error("hay un <section> sin cerrar")
    if not bloques:
        raise Error("el deck no tiene ninguna lámina")
    return bloques, fin


def identidad(bloque):
    """El id de una lámina, leído de su etiqueta de apertura.

    data-sid manda sobre id, que es el mismo criterio que sigue el anotador:
    reveal le quita el atributo id a la lámina visible mientras está en pantalla.
    """
    f = FIN_ETIQ.search(bloque)
    while f and f.group(0) != ">":
        f = FIN_ETIQ.search(bloque, f.end())
    if not f:
        raise Error("hay un <section> cuya etiqueta de apertura no cierra")
    abre = bloque[: f.end()]
    sid = ide = None
    for m in ATRIB.finditer(abre):
        if m.group("cual").lower() == "data-sid" and sid is None:
            sid = m.group("val").strip()
        elif m.group("cual").lower() == "id" and ide is None:
            ide = m.group("val").strip()
    return sid or ide or ""


def conciliar(orden, deck, extras=()):
    """El orden pendiente, puesto al día con las láminas que hay hoy.

    Es la misma regla que aplica revisar.js, y tiene que seguir siéndolo: las
    láminas que ya no existen se caen; las que el orden no menciona, porque se
    insertaron después de arrastrar, se meten detrás de la vecina que las
    precede en el deck. `extras` son las láminas por escribir, que todavía no
    están en el HTML pero sí cuentan como existentes.
    """
    hay, r = set(deck) | set(extras), []
    for x in orden:
        if x in hay and x not in r:
            r.append(x)
    for i, x in enumerate(deck):
        if x in r:
            continue
        j = -1
        for k in range(i - 1, -1, -1):
            if deck[k] in r:
                j = r.index(deck[k])
                break
        r.insert(j + 1, x)
    for x in extras:
        if x not in r:
            r.append(x)
    return r


def lasMovidas(deck, quiero):
    """Cuáles cambiaron de sitio de verdad, con la misma regla que la rejilla.

    Contarlas posición a posición exagera: subir una lámina al principio corre
    una casilla a todas las demás y el informe diría que se movió el deck
    entero. Movida es la que no cabe en la subsecuencia común más larga con el
    orden del HTML, que son las que hubo que sacar de la fila y volver a meter.

    Tiene que decir exactamente lo mismo que `lasMovidas` de revisar.js: es el
    número que Alberto ve en la rejilla antes de pedir que se aplique.
    """
    n, m = len(deck), len(quiero)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            d[i][j] = (d[i + 1][j + 1] + 1 if deck[i] == quiero[j]
                       else max(d[i + 1][j], d[i][j + 1]))
    quedan, i, j = set(), 0, 0
    while i < n and j < m:
        if deck[i] == quiero[j]:
            quedan.add(deck[i])
            i += 1
            j += 1
        elif d[i + 1][j] >= d[i][j + 1]:
            i += 1
        else:
            j += 1
    return [x for x in quiero if x not in quedan]


def marcar(bloque, atributos):
    """Añade atributos a la etiqueta de apertura de un <section>, sin tocar nada
    más de la lámina.

    Antes quita las marcas de fusión que hubiera, para que aplicar dos veces no
    las acumule y para que una fusión deshecha desaparezca del HTML.
    """
    f = FIN_ETIQ.search(bloque)
    while f and f.group(0) != ">":
        f = FIN_ETIQ.search(bloque, f.end())
    if not f:
        raise Error("hay un <section> cuya etiqueta de apertura no cierra")
    abre = COMBI.sub("", bloque[:f.end()])
    extra = "".join(' %s="%s"' % (k, html_mod.escape(str(v), quote=True))
                    for k, v in atributos)
    return abre[:-1].rstrip() + extra + ">" + bloque[f.end():]


def bloque_pendiente(x, sangria):
    """El <section> de una lámina por escribir, tal como entra en el HTML.

    Lleva `data-pendiente`, que es lo que hace que tools/empaquetar.py se niegue
    a entregar un deck con láminas sin escribir, y el encargo en el cuerpo y en
    el guion, para tenerlo delante al escribirla. No es una lámina de verdad: es
    el hueco reservado, con lo que hay que poner en él.
    """
    crudo = x.get("texto")
    texto = (crudo if isinstance(crudo, str) else "").strip() or "Sin descripción."
    parrafos = [html_mod.escape(p.strip()) for p in re.split(r"\n\s*\n", texto) if p.strip()]
    cuerpo = "\n".join("%s  <p>%s</p>" % (sangria, p) for p in parrafos)
    ident = html_mod.escape(x["id"])
    return ('<section id="%s" class="guinda-linea" data-sid="%s" data-pendiente="1">'
            "<h2>Lámina por escribir</h2>\n"
            '%s<div class="cuerpo">\n%s\n%s</div>\n'
            '%s<aside class="notes"><p>Lámina pendiente de escribir. Encargo: %s</p></aside>\n'
            "%s</section>") % (ident, ident, sangria, cuerpo, sangria, sangria,
                               " ".join(parrafos) or "sin descripción", sangria)


def reordenar(html, orden, nuevas=(), borradas=(), fusiones=()):
    """El deck con sus láminas en el orden pedido.

    Cada <section> que sobrevive viaja entero y tal cual; lo que hay entre uno y
    otro se queda en su sitio, porque es sangría. Un comentario suelto entre dos
    láminas no viaja con la suya: se avisa aparte, en `avisos`.

    `nuevas` son las láminas por escribir, cada una con su id y la descripción de
    lo que debe contener: entran como un <section> con data-pendiente en el sitio
    que les da `orden`. `borradas` son ids de láminas del deck que se van.

    `fusiones` son grupos de láminas que hay que combinar en una. Aquí **no se
    combina nada y no se borra nada**: combinar es trabajo de contenido, hay que
    decidir qué sobrevive y refundir el guion y los apuntes, y para eso hace falta
    el material entero. Lo que se hace es marcarlo: la primera parte lleva
    data-combinar con las demás y data-combinar-nota con el criterio, y cada una
    de las otras lleva data-combinar-en apuntando a la primera. Mientras esas
    marcas estén, tools/empaquetar.py se niega a entregar el paquete.
    """
    # El tipo se comprueba aquí, que es por donde entra todo: un texto se
    # iteraría carácter a carácter y un diccionario por sus claves, y las dos
    # cosas moverían láminas de verdad sin que nadie proteste.
    if orden is None:
        orden = []
    if not isinstance(orden, list):
        raise Error("`orden` de notas.json no es una lista, es %s" % type(orden).__name__)
    orden = [x for x in orden if isinstance(x, str)]
    if not isinstance(nuevas, (list, tuple)):
        raise Error("`nuevas` de notas.json no es una lista, es %s" % type(nuevas).__name__)
    if not isinstance(borradas, (list, tuple)):
        raise Error("`borradas` de notas.json no es una lista, es %s" % type(borradas).__name__)
    nuevas = [x for x in nuevas if isinstance(x, dict) and isinstance(x.get("id"), str)
              and x["id"].strip()]
    malos = [x["id"] for x in nuevas if not ID_OK.match(x["id"])]
    if malos:
        raise Error("hay láminas por escribir con un id que no vale como atributo HTML: %s"
                    % ", ".join(malos))
    borradas = [x for x in borradas if isinstance(x, str)]
    if not isinstance(fusiones, (list, tuple)):
        raise Error("`fusiones` de notas.json no es una lista, es %s" % type(fusiones).__name__)
    fusiones = [x for x in fusiones
                if isinstance(x, dict) and isinstance(x.get("partes"), list)]
    # Las partes tienen que ser ids de verdad: una lista con números o con otra
    # lista dentro reventaba con una traza cruda en vez de con un error legible.
    for f in fusiones:
        malas = [y for y in f["partes"] if not isinstance(y, str) or not ID_OK.match(y)]
        if malas:
            raise Error("una fusión tiene partes que no son ids de lámina: %s"
                        % ", ".join(repr(y) for y in malas))
    # Y una lámina no puede estar en dos fusiones: marcar la segunda borraba la
    # marca de la primera y el encargo desaparecía sin que nadie lo dijera.
    dos, vistas = [], set()
    for f in fusiones:
        for y in f["partes"]:
            if y in vistas:
                dos.append(y)
            vistas.add(y)
    if dos:
        raise Error("hay láminas en más de una fusión: %s" % ", ".join(sorted(set(dos))))
    bloques, _ = laminas(html)
    deck = [b[2] for b in bloques]
    if "" in deck:
        raise Error("hay láminas sin id: corre antes python3 tools/ids.py")
    if len(set(deck)) != len(deck):
        raise Error("hay ids repetidos en el deck: corre antes python3 tools/ids.py")
    porEscribir = [x for x in nuevas if x["id"] not in set(deck)]
    ids_nuevas = [x["id"] for x in porEscribir]
    fueraDeck = [x for x in borradas if x in set(deck)]
    quiero = [x for x in conciliar(orden, deck, ids_nuevas) if x not in set(fueraDeck)]
    avisos = []
    yaEscritas = [x["id"] for x in nuevas if x["id"] in set(deck)]
    if yaEscritas:
        avisos.append("%d lámina(s) por escribir ya están en el HTML, se dan por hechas: %s"
                      % (len(yaEscritas), ", ".join(yaEscritas)))
    # El mismo criterio que el marcado de más abajo: cuenta lo que va a existir
    # en el archivo, láminas por escribir incluidas, no solo lo que ya está.
    porVenir = set(deck) | {x["id"] for x in porEscribir}
    for f in fusiones:
        vivas = [y for y in f["partes"] if y in porVenir and y not in set(fueraDeck)]
        if len(vivas) < 2:
            avisos.append("una fusión se quedó sin partes suficientes y no se marca: %s"
                          % ", ".join(f["partes"]))
    huerfanas = [x for x in borradas if x not in set(deck)]
    if huerfanas:
        avisos.append("%d lámina(s) marcadas para borrar ya no existen: %s"
                      % (len(huerfanas), ", ".join(huerfanas)))
    fuera = [x for x in orden if x not in set(deck) | set(ids_nuevas)]
    if fuera:
        avisos.append("el orden pendiente nombra %d lámina(s) que ya no existen: %s"
                      % (len(fuera), ", ".join(fuera)))
    sinMencionar = [x for x in deck if x not in set(orden) | set(fueraDeck)]
    if orden and sinMencionar:
        avisos.append("%d lámina(s) que no estaban al arrastrar se quedan junto a su "
                      "vecina: %s" % (len(sinMencionar), ", ".join(sinMencionar)))
    # Un comentario entre dos láminas se queda donde está, no sigue a la suya.
    for a, b in zip(bloques, bloques[1:]):
        if "<!--" in html[a[1]:b[0]]:
            avisos.append("hay un comentario entre %s y %s: se queda en esa posición, "
                          "no viaja con su lámina" % (a[2], b[2]))
    if not quiero:
        raise Error("el cambio dejaría el deck sin ninguna lámina: no se escribe nada")
    if quiero == deck and not porEscribir and not fusiones:
        return html, quiero, deck, avisos

    texto = {b[2]: html[b[0]:b[1]] for b in bloques}
    sangria = re.search(r"[ \t]*$", html[:bloques[0][0]]).group(0)
    for x in porEscribir:
        texto[x["id"]] = bloque_pendiente(x, sangria)
    # Las marcas de fusión se refrescan solo en las láminas de las fusiones que
    # hay ahora. Las de una fusión ya aplicada NO se tocan: esas marcas son el
    # encargo de escribir la lámina combinada, y barrerlas sería perder el
    # encargo. Se van cuando la lámina única está escrita, no antes.
    for f in fusiones:
        for y in f.get("partes") or []:
            if y in texto and y in set(deck):
                texto[y] = marcar(texto[y], [])
    for f in fusiones:
        partes = [y for y in f["partes"] if y in texto and y not in set(fueraDeck)]
        partes = [y for i, y in enumerate(partes) if partes.index(y) == i]
        if len(partes) < 2:
            continue
        ancla = partes[0]
        texto[ancla] = marcar(texto[ancla],
                              [("data-combinar", " ".join(partes[1:])),
                               ("data-combinar-nota", (f.get("texto") or "").strip())])
        for y in partes[1:]:
            texto[y] = marcar(texto[y], [("data-combinar-en", ancla)])
    # Los separadores se quedan en su posición, que es lo que conserva la sangría
    # del archivo. Si la lista crece, los de más allá se copian del último.
    seps = [html[a[1]:b[0]] for a, b in zip(bloques, bloques[1:])]
    por_defecto = seps[0] if seps else "\n" + sangria
    partes = [html[:bloques[0][0]]]
    for k, ident in enumerate(quiero):
        if k:
            partes.append(seps[k - 1] if k - 1 < len(seps) else por_defecto)
        partes.append(texto[ident])
    partes.append(html[bloques[-1][1]:])
    salida = "".join(partes)
    # Las guardas: ninguna lámina que sobrevive puede haber cambiado por dentro,
    # las borradas tienen que haberse ido, y el resultado tiene que decir
    # exactamente el orden pedido. Si algo no cuadra, no se escribe nada.
    hechos = laminas(salida)[0]
    if [x[2] for x in hechos] != quiero:
        raise Error("el archivo resultante no dice el orden pedido: no se escribe nada")
    for i, j, ident in hechos:
        if salida[i:j] != texto[ident]:
            raise Error("la lámina %s cambió por dentro: no se escribe nada" % ident)
    if set(fueraDeck) & set(x[2] for x in hechos):
        raise Error("una lámina marcada para borrar sigue en el archivo: no se escribe nada")
    return salida, quiero, deck, avisos


def carpeta(arg):
    """La carpeta de la sesión, dicha como sea.

    Vale la ruta del index.html, la de la carpeta, el nombre de la carpeta o el
    número de sesión: es lo que imprime tools/notas.py cuando hay orden
    pendiente, y no tiene que acordarse uno de en qué forma.
    """
    p = pathlib.Path(arg)
    if p.suffix == ".html" or p.name == "index.html":
        if not p.exists():
            raise Error("no existe " + str(p))
        # resolver la carpeta, no el archivo: si el deck es un enlace simbólico,
        # la sesión es la carpeta donde está el enlace, no la del destino.
        return p.parent.resolve()
    if p.is_dir():
        return p.resolve()
    suya = RAIZ / "sesiones" / str(arg)
    if suya.is_dir():
        return suya
    if re.fullmatch(r"[Ss]?\d{1,2}", str(arg)):
        n = "S%02d" % int(str(arg).lstrip("Ss"))
        cand = sorted((RAIZ / "sesiones").glob(n + "-*"))
        if not cand:
            raise Error("no encuentro la sesión " + n)
        return cand[0]
    raise Error("no sé qué sesión es " + str(arg))


def leer_notas(dest):
    p = dest / "notas.json"
    if not p.exists():
        return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise Error("notas.json ilegible: %s" % e)
    if not isinstance(d, dict):
        raise Error("notas.json no es un documento, es %s" % type(d).__name__)
    return d


SERVIR = None


def servir():
    """tools/servir.py cargado a demanda, como hace tools/notas.py."""
    global SERVIR
    if SERVIR is None:
        spec = importlib.util.spec_from_file_location("servir", RAIZ / "tools" / "servir.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        SERVIR = m
    return SERVIR


def por_servidor(sesion, doc, version):
    """Cierra a través del servidor, si está levantado. Devuelve "hecho",
    "choque" o "no".

    Es la vía sin carreras, la misma que usa tools/notas.py: el servidor
    serializa las escrituras con un cerrojo y comprueba el contador de versión,
    así que no puede pisar una nota que el navegador acabe de guardar. Escribir
    el archivo por nuestra cuenta sí podía, y además bajaba el contador."""
    try:
        s = servir()
        if s.responde() is not True:
            return "no"
        base = s.base()
        req = urllib.request.Request(
            base + "/notas/" + sesion, data=json.dumps(dict(doc, v=version)).encode(),
            method="PUT",
            headers={"Content-Type": "application/json", "Origin": base})
        with urllib.request.urlopen(req, timeout=5):
            return "hecho"
    except urllib.error.HTTPError as e:
        # 409: alguien escribió entre medias, y entonces no se cierra nada
        return "choque" if e.code == 409 else "no"
    except Exception:
        return "no"


def cerrar_orden(dest, aplicado):
    """Da por aplicados los tres pendientes del deck, subiendo la versión.

    El contador es lo que hace que la pestaña abierta se entere, igual que en
    tools/notas.py. Escritura atómica, como la del servidor.

    `aplicado` es lo que de verdad se llevó al HTML, los tres apartados. Se
    vuelve a leer el archivo antes de cerrarlo porque entre una cosa y otra
    Alberto puede haber movido otra lámina: si lo que hay ahora no es lo que se
    aplicó, no se cierra nada, que sería tirar su cambio sin decírselo.
    """
    p = dest / "notas.json"
    d = leer_notas(dest)
    hay = {k: d.get(k) or [] for k in ("orden", "nuevas", "borradas", "fusiones")}
    if not any(hay.values()):
        return True
    if any(list(hay[k]) != list(aplicado.get(k) or []) for k in hay):
        return False
    for k in hay:
        d[k] = []
    version = int(d.get("v") or 0)
    r = por_servidor(dest.name, d, version)
    if r == "choque":
        return False
    if r == "no":
        d["v"] = version + 1
        escribir_json(p, d)
    return True


def escribir_atomico(destino, texto):
    """Escribe entero o no escribe: nadie ve nunca un archivo a medias.

    Sin esto, un disco lleno deja truncado el archivo que se estaba escribiendo,
    y si el truncado es el respaldo, lo peor es que parece bueno.
    """
    tmp = destino.with_name(destino.name + ".tmp")
    try:
        tmp.write_text(texto, encoding="utf-8")
        os.replace(tmp, destino)
    except OSError as e:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise Error("no se pudo escribir %s: %s" % (destino, e))


def escribir_json(destino, doc):
    escribir_atomico(destino, json.dumps(doc, ensure_ascii=False, indent=1))


def escribir(deck, antes, salida):
    """Respaldo del anterior y escritura del nuevo, los dos atómicos.

    El respaldo lleva la fecha en el nombre y no se pisa nunca: aplicar dos veces
    seguidas es lo normal, y con un respaldo único la segunda pasada se llevaba
    por delante el original, que es justo lo que no se puede perder en un
    proyecto sin control de versiones.

    Se respalda el texto con el que se calculó la salida, no lo que haya en el
    disco ahora, y va primero: si no se puede escribir, se para antes de tocar el
    deck.
    """
    marca = time.strftime("%Y%m%dT%H%M%S")
    copia = deck.parent / ("index.html.bak.orden." + marca)
    # dos pasadas dentro del mismo segundo no pueden compartir respaldo
    n = 1
    while copia.exists():
        n += 1
        copia = deck.parent / ("index.html.bak.orden.%s-%d" % (marca, n))
    escribir_atomico(copia, antes)
    escribir_atomico(deck, salida)
    return copia


def main(argv):
    args = [x for x in argv if not x.startswith("--")]
    ver = "--ver" in argv
    if not args:
        print(__doc__.strip())
        return 2
    try:
        dest = carpeta(args[0])
        deck = dest / "index.html"
        if not deck.exists():
            raise Error("no existe " + str(deck))
        if not os.access(deck, os.W_OK):
            # os.replace no necesita permiso sobre el destino, así que sin esta
            # comprobación un deck protegido se sobrescribía igual.
            raise Error("%s está protegido contra escritura" % deck)
        # el valor crudo del archivo: es con el que se compara al cerrarlo, para
        # no dar por aplicado un cambio que llegó mientras corría esto
        d = leer_notas(dest)
        pend = {k: d.get(k) or [] for k in ("orden", "nuevas", "borradas", "fusiones")}
        orden, nuevas = pend["orden"], pend["nuevas"]
        borradas, fusiones = pend["borradas"], pend["fusiones"]
        html = deck.read_text(encoding="utf-8")
        salida, quiero, viejo, avisos = reordenar(html, orden, nuevas, borradas, fusiones)
    except Error as e:
        print("error: %s" % e)
        return 1

    for a in avisos:
        print("aviso: " + a)
    if not any(pend.values()):
        print("%s: no hay ningún cambio pendiente en notas.json, nada que hacer." % dest.name)
        return 0
    # Las tres cuentas van por separado: una lámina nueva no está "movida", y una
    # borrada tampoco. Movida es lo que dice lasMovidas entre lo que sobrevive.
    ids_nuevas = [x["id"] for x in nuevas if x["id"] not in set(viejo)]
    seBorran = [x for x in borradas if x in set(viejo)]
    base = [x for x in viejo if x not in set(seBorran)]
    solo = [x for x in quiero if x not in set(ids_nuevas)]
    fuera = set(lasMovidas(base, solo))
    movidas = [(i, x) for i, x in enumerate(quiero) if x in fuera]
    combina = [f for f in fusiones
               if len([y for y in f.get("partes") or []
                       if y in set(viejo) and y not in set(seBorran)]) > 1]
    if not movidas and not ids_nuevas and not seBorran and not combina:
        print("%s: el deck ya está así. Se cierra el pendiente." % dest.name)
        if not ver and not cerrar_orden(dest, pend):
            print("aviso: el pendiente cambió mientras corría esto, "
                  "se deja como está. Vuelve a correrlo.")
        return 0
    print("%s: %d lámina(s) cambian de sitio, %d por escribir, %d se borran, "
          "%d combinación(es)."
          % (dest.name, len(movidas), len(ids_nuevas), len(seBorran), len(combina)))
    for i, x in movidas:
        print("  %3d  %-44s (estaba en la %d)" % (i + 1, x, viejo.index(x) + 1))
    for x in ids_nuevas:
        enc = next((y.get("texto") or "" for y in nuevas if y["id"] == x), "")
        print("  %3d  %-44s POR ESCRIBIR: %s"
              % (quiero.index(x) + 1, x, " ".join(enc.split())[:60] or "(sin descripción)"))
    for x in seBorran:
        print("  --   %-44s SE BORRA (estaba en la %d)" % (x, viejo.index(x) + 1))
    for f in combina:
        partes = [y for y in f["partes"] if y in set(viejo) and y not in set(seBorran)]
        print("  --   SE COMBINAN en %s: %s" % (partes[0], ", ".join(partes)))
        print("       %s" % (" ".join((f.get("texto") or "").split())
                             or "(sin nota: el criterio lo decide quien la escriba)"))
    if ver:
        print("(--ver: no se escribió nada)")
        return 0
    try:
        copia = escribir(deck, html, salida)
    except Error as e:
        print("error: %s" % e)
        return 1
    if not cerrar_orden(dest, pend):
        print("aviso: mientras corría esto cambió algo más en la rejilla. El deck "
              "lleva lo de antes y el pendiente sigue abierto: vuelve a correrlo.")
    print("escrito %s, respaldo en %s" % (deck, copia))
    if combina:
        print("ojo: las láminas marcadas con data-combinar hay que escribirlas como una "
              "sola y borrar las sobrantes. Hasta entonces empaquetar.py no entrega nada.")
    print("ahora: guion.py, apuntes.py, citas.py y empaquetar.py sobre esta sesión")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
