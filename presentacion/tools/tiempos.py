#!/usr/bin/env python3
"""Estima la duración de un deck reveal.js y dice hasta dónde se llega en clase.

    python3 tools/tiempos.py sesiones/SNN-.../index.html
    python3 tools/tiempos.py sesiones/SNN-.../index.html --observar=46/120
    python3 tools/tiempos.py --ritmo

El modelo tiene dos términos, y el segundo es el que pesa:

1. **El guion hablado.** Las palabras de `<aside class="notes">`, sin las
   acotaciones entre corchetes, divididas entre el ritmo de habla.

2. **El sobrecosto por lámina.** Lo que cuesta una lámina y no está escrito en
   su guion: pasarla, dejar que el grupo la lea, mirar el diagrama, ampliar de
   viva voz lo que el guion resume, contestar a quien pregunta. No depende de lo
   largo que sea el guion, depende de que la lámina exista.

La primera versión de este script solo tenía el primer término, más un recargo
del veinticinco al treinta y cinco por ciento por interacción. Se midió contra
la sesión 3, impartida el 8 de septiembre de 2026, y se quedó corta por un
factor de dos: el deck entero, estimado en ciento cuatro minutos, llegó a su
lámina cuarenta y seis de setenta y siete en las dos horas de clase, con
intervención mínima del grupo. El sobrecosto por lámina sale de esa medición.

**El modelo se recalibra con lo que pasa en el aula.** Después de cada sesión:

    python3 tools/tiempos.py sesiones/S03-.../index.html --observar=46/120

que significa "en ciento veinte minutos llegué a la lámina cuarenta y seis". La
observación se guarda en `admin/ritmo.json`, anclada al identificador de esa
lámina y no solo a su número, y el sobrecosto se vuelve a ajustar con todas las
observaciones acumuladas: la banda se centra en su mediana. Sin observaciones,
se usan los valores por omisión de este archivo.

Los bloques de duración fija que no dependen del guion, como una ronda de
presentaciones, un descanso o una discusión, se declaran con `data-min="15"` en
el `<section>`. Duran lo que dicen, no llevan sobrecosto y **el recorte no los
toca**: un bloque de participación se acorta cambiando su `data-min`, no
marcándolo como recortable.

La portada, el cierre y los separadores de bloque llevan un sobrecosto leve: se
pasan, no se discuten. Una lámina de contenido sin guion escrito **no** es de
tránsito: una lámina de diagrama cuesta lo que cuesta cualquier otra.

Además de la duración completa se reportan las dos duraciones con recorte, que
es lo que la sesión llega a durar si en clase hay que apretar. Una lámina con
`data-recorte="1"` se puede perder sin que nadie se entere; una con
`data-recorte="2"` se puede perder, pero hay que decírselo al grupo. Si tiene
guion corto escrito, en un `<aside class="corto">`, la lámina recortada dura lo
que ese guion más el sobrecosto leve; si no lo tiene, la única salida es
saltarla entera y dura cero. Recortar nunca sale más caro que no recortar.

Estas dos cifras son el suelo, no el plan: dicen a cuánto se puede bajar
recortándolo todo. En clase, el apuntador recorta solo lo que haga falta.

Toda lámina con guion hablado lleva su versión corta, no solo las marcadas: es
la reserva para abreviar a mano una lámina de núcleo el día que la clase se
tuerza de verdad. Se reportan las que no la tienen. Quedan fuera de esa cuenta
la portada, el cierre y los separadores de bloque, cuyo guion ya son dos frases.
"""
import re, sys, html, json, math, pathlib, glob, os, tempfile, statistics

RAIZ = pathlib.Path(__file__).resolve().parent.parent
RITMO_JSON = RAIZ / "admin" / "ritmo.json"
# El horario dice 08:00 a 10:00, pero la clase de verdad empieza a las 08:05 y
# tiene que acabar a las 10:00 en punto, con diez minutos de receso en medio.
# Son 115 menos 10: **105 minutos de exposición**, no 120. Alberto lo fijó el
# 13 de octubre de 2026, al dimensionar la sesión 12.
OBJETIVO = 12                     # la visita guiada dura de diez a quince minutos
                                  # minutos. En el curso esta constante vale 105.

# Valores por omisión, calibrados con la sesión 3 del 8 de septiembre de 2026:
# ciento veinte minutos hasta la lámina cuarenta y seis, con intervención mínima
# del grupo. admin/ritmo.json los sustituye en cuanto hay observaciones.
OMISION = {
    "ritmo_ppm": 135,             # palabras por minuto del guion dicho en voz alta
    "sobrecosto_lo": 1.5,         # minutos por lámina de contenido, ritmo vivo
    "sobrecosto_hi": 2.0,         # minutos por lámina de contenido, ritmo pausado
    "sobrecosto_leve": 0.3,       # portada, cierre y separadores de bloque
    "observaciones": [],
}
MARGEN = 0.15                     # holgura de la banda alrededor de la mediana
PISO_SOBRECOSTO = 0.05            # la banda no baja de aquí, para no dar cero
DISPERSION = 1.5                  # si la observación más lenta supera a la más
                                  # rápida por este factor, la calibración avisa
RAZON_ANCHA = 2.0                 # si el sobrecosto pausado dobla al fluido, la
                                  # calibración es demasiado floja para decidir
CLAVE_SESION = re.compile(r"S\d{1,3}\Z")


def _num(v):
    """Convierte a float solo si sale un número finito. Si no, None."""
    if isinstance(v, bool) or not isinstance(v, (int, float, str)):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


# --------------------------------------------------------------- lectura

def limpiar(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def hablado(nota):
    """Texto que sí se pronuncia: quita las acotaciones [entre corchetes]."""
    return re.sub(r"\[[^\]]*\]", " ", nota)


def _sin_comentarios(s):
    """Quita los comentarios HTML, para que ni los regex ni el conteo de
    palabras confundan con contenido lo que está comentado. Se sustituyen por
    un espacio, no por un marcador: un marcador se cuenta como palabra y se
    pega a la palabra siguiente."""
    return re.sub(r"<!--.*?-->", " ", s, flags=re.S)


class DeckIlegible(Exception):
    """El archivo no se puede leer o no se puede analizar como deck."""


ETIQUETA = re.compile(r"<section\b([^>]{0,4096})>|</section\s*>", re.I)


def _hojas(src, nombre):
    """Las secciones que no contienen otra sección, en orden de documento.

    Se recorre con una pila en vez de con un patrón perezoso. Así los
    verticales de reveal, que anidan secciones, no hacen que la envoltura pase
    por lámina ni que sus atributos se le peguen al primer hijo, y un deck a
    medio editar se detecta en el acto en vez de colgar el escaneo.
    """
    pila, hojas = [], []
    for m in ETIQUETA.finditer(src):
        if m.group(0).startswith("</"):
            if not pila:
                raise DeckIlegible(
                    f"{nombre}: hay un </section> sin su apertura. El deck "
                    f"está a medio editar y no lo puedo medir.")
            attrs, ini, hijos = pila.pop()
            if not hijos:
                hojas.append((ini, attrs, src[ini:m.start()]))
            if pila:
                pila[-1][2] += 1
        else:
            pila.append([m.group(1), m.end(), 0])
    if pila:
        raise DeckIlegible(
            f"{nombre}: quedaron {len(pila)} etiquetas <section> sin cerrar. "
            f"El deck está a medio editar y no lo puedo medir.")
    hojas.sort()
    return [(a, c) for _, a, c in hojas]


def analiza(ruta):
    """Devuelve una lista de diccionarios, uno por lámina, con lo que el
    modelo necesita: palabras del guion, palabras del guion corto, minutos
    fijos si los declara, nivel de recorte y de qué clase es la lámina."""
    ruta = pathlib.Path(ruta)
    try:
        texto = ruta.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise DeckIlegible(f"no puedo leer {ruta}: {e}")
    laminas = []
    for attrs, cuerpo in _hojas(_sin_comentarios(texto), str(ruta)):
        t = re.search(r"<h2[^>]*>(.*?)</h2>", cuerpo, re.S) or \
            re.search(r'class="(?:titulo|gracias)"[^>]*>(.*?)</div>', cuerpo, re.S)
        titulo = limpiar(t.group(1))[:44] if t else "(sin título)"
        nota = re.search(r'<aside class="notes">(.*?)</aside>', cuerpo, re.S)
        pal = len(limpiar(hablado(nota.group(1))).split()) if nota else 0
        corto = re.search(r'<aside class="corto">(.*?)</aside>', cuerpo, re.S)
        palc = len(limpiar(hablado(corto.group(1))).split()) if corto else 0
        niv = re.search(r'data-recorte="([12])"', attrs)
        cl = re.search(r'class="([^"]*)"', attrs)
        cl = cl.group(1) if cl else ""
        sid = re.search(r'data-sid="([^"]*)"', attrs) or \
            re.search(r'id="([^"]*)"', attrs)
        fijo = None
        m = re.search(r'data-min="([^"]*)"', attrs)
        if m:
            fijo = _num(m.group(1))
            if fijo is None or fijo < 0:
                print(f"aviso: {ruta.name}, lámina {len(laminas)+1}: "
                      f'data-min="{m.group(1)}" no es un número de minutos; '
                      f"la mido por su guion", file=sys.stderr)
                fijo = None
        laminas.append({
            "n": len(laminas) + 1, "titulo": titulo, "palabras": pal,
            "corto": palc, "nivel": int(niv.group(1)) if niv else 0,
            "fijo": fijo, "sid": sid.group(1) if sid else "",
            # La portada, el cierre y los separadores se pasan, no se discuten.
            # Una lámina de contenido sin guion escrito NO entra aquí: una
            # lámina de diagrama cuesta lo que cuesta cualquier otra, y
            # confundir las dos cosas es el error que costó el factor 2.5.
            "transito": any(x in cl for x in ("portada", "cierre", "seccion")),
        })
    return laminas


# ---------------------------------------------------------------- modelo

def costo(lam, cfg, nivel_recorte=0):
    """Minutos que cuesta una lámina, como banda (lo, hi).

    nivel_recorte dice hasta qué nivel se está recortando: 0 es la sesión
    entera, 1 recorta lo marcado con data-recorte="1", 2 recorta los dos.
    """
    if lam["fijo"] is not None:
        # Un bloque de duración fija dura lo que dice, también al recortar:
        # una discusión de quince minutos no se abrevia sola. Se acorta
        # cambiando su data-min.
        return (lam["fijo"], lam["fijo"])
    base = lam["palabras"] / cfg["ritmo_ppm"]
    if lam["transito"]:
        entera = (base + cfg["sobrecosto_leve"],) * 2
    else:
        entera = (base + cfg["sobrecosto_lo"], base + cfg["sobrecosto_hi"])
    if not (lam["nivel"] and lam["nivel"] <= nivel_recorte):
        return entera
    # Abreviada: dura lo que su guion corto, con el sobrecosto de tránsito,
    # porque abreviar es justamente no detenerse. Sin guion corto escrito no
    # hay manera de abreviarla: se salta entera. Y nunca puede salir más cara
    # que contarla completa, aunque alguien escriba un corto más largo.
    if not lam["corto"]:
        return (0.0, 0.0)
    m = lam["corto"] / cfg["ritmo_ppm"] + cfg["sobrecosto_leve"]
    return (min(m, entera[0]), min(m, entera[1]))


def duracion(laminas, cfg, nivel_recorte=0, hasta=None):
    """Banda (lo, hi) de minutos de las primeras `hasta` láminas."""
    lo = hi = 0.0
    for lam in laminas:
        if hasta is not None and lam["n"] > hasta:
            break
        a, b = costo(lam, cfg, nivel_recorte)
        lo += a
        hi += b
    return lo, hi


def hasta_donde(laminas, cfg, minutos=OBJETIVO):
    """Última lámina que se alcanza en `minutos`, en cada extremo de la banda.

    Devuelve (con_ritmo_vivo, con_ritmo_pausado). La primera es mayor o igual
    que la segunda: si todo fluye se llega más lejos.
    """
    res = []
    for idx in (0, 1):
        acc, ultima = 0.0, 0
        for lam in laminas:
            acc += costo(lam, cfg)[idx]
            if acc > minutos:
                break
            ultima = lam["n"]
        res.append(ultima)
    return res[0], res[1]


# --------------------------------------------------------- calibración

def carga_cfg(avisa=True):
    """Lee admin/ritmo.json. Si no existe o está roto, usa los valores por
    omisión y lo dice, en vez de callarse o de reventar."""
    cfg = dict(OMISION)
    cfg["observaciones"] = []
    if not RITMO_JSON.exists():
        return cfg
    try:
        d = json.loads(RITMO_JSON.read_text(encoding="utf-8"))
        if not isinstance(d, dict):
            raise ValueError("la raíz no es un objeto")
    except (OSError, UnicodeDecodeError, ValueError) as e:
        if avisa:
            print(f"aviso: {RITMO_JSON.name} no se pudo leer ({e}); "
                  f"uso los valores por omisión", file=sys.stderr)
        return cfg
    for k in ("ritmo_ppm", "sobrecosto_lo", "sobrecosto_hi", "sobrecosto_leve"):
        if k not in d:
            continue
        v = _num(d[k])
        if v is not None and v > 0:
            cfg[k] = v
        elif avisa:
            print(f"aviso: {k} inválido en {RITMO_JSON.name}; "
                  f"uso {cfg[k]}", file=sys.stderr)
    if cfg["sobrecosto_hi"] < cfg["sobrecosto_lo"]:
        cfg["sobrecosto_lo"], cfg["sobrecosto_hi"] = \
            cfg["sobrecosto_hi"], cfg["sobrecosto_lo"]
    obs = d.get("observaciones")
    if obs is not None and not isinstance(obs, list):
        if avisa:
            print(f"aviso: 'observaciones' de {RITMO_JSON.name} no es una "
                  f"lista; la ignoro", file=sys.stderr)
        obs = None
    cfg["observaciones"] = obs if isinstance(obs, list) else []
    return cfg


def guarda_cfg(cfg):
    """Escribe admin/ritmo.json de forma atómica: primero un temporal en el
    mismo directorio, después un rename. Un fallo a media escritura no deja
    el archivo a medias."""
    RITMO_JSON.parent.mkdir(parents=True, exist_ok=True)
    datos = {
        "_comentario": "Calibración de tools/tiempos.py. Se ajusta sola con "
                       "--observar; no hace falta editarla a mano.",
        "ritmo_ppm": cfg["ritmo_ppm"],
        "sobrecosto_lo": round(cfg["sobrecosto_lo"], 3),
        "sobrecosto_hi": round(cfg["sobrecosto_hi"], 3),
        "sobrecosto_leve": cfg["sobrecosto_leve"],
        "observaciones": cfg["observaciones"],
    }
    fd, tmp = tempfile.mkstemp(dir=str(RITMO_JSON.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            # allow_nan=False: un infinito escrito aquí deja de ser JSON
            # estándar y envenena la calibración de forma permanente.
            json.dump(datos, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write("\n")
        os.chmod(tmp, 0o644)
        os.replace(tmp, RITMO_JSON)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def deck_de(sesion):
    """Ruta del index.html de una sesión, a partir de su clave, 'S03'.

    La clave viene de un archivo de datos, así que se valida antes de meterla
    en un glob: sin esto, un '../..' en ritmo.json lee decks de fuera.
    """
    if not isinstance(sesion, str) or not CLAVE_SESION.match(sesion):
        return None
    cand = sorted(glob.glob(str(RAIZ / "sesiones" / (sesion + "-*") / "index.html")))
    return cand[0] if cand else None


def sobrecosto_observado(laminas, cfg, hasta, minutos):
    """Qué sobrecosto por lámina explica que en `minutos` se llegara a la
    lámina `hasta`. Devuelve None si no se puede despejar."""
    contenido = [l for l in laminas
                 if l["n"] <= hasta and l["fijo"] is None and not l["transito"]]
    if not contenido:
        return None
    resto = 0.0
    for l in laminas:
        if l["n"] > hasta:
            break
        if l["fijo"] is not None:
            resto += l["fijo"]
        elif l["transito"]:
            resto += l["palabras"] / cfg["ritmo_ppm"] + cfg["sobrecosto_leve"]
        else:
            resto += l["palabras"] / cfg["ritmo_ppm"]
    return (minutos - resto) / len(contenido)


def ajusta(cfg):
    """Recalcula la banda de sobrecosto con todas las observaciones.

    La banda se centra en la mediana de lo observado, no en el mínimo y el
    máximo: una sesión atípica no debe ensanchar la banda para siempre. Si las
    observaciones discrepan mucho entre sí, se avisa en vez de disimularlo.

    Devuelve (cfg, informe), donde informe es la lista de líneas que explican
    de dónde salió cada número.
    """
    valores, informe = [], []
    for o in cfg["observaciones"]:
        if not isinstance(o, dict):
            informe.append("  observación descartada: no es un objeto")
            continue
        ses, lam = o.get("sesion"), o.get("laminas")
        mins = _num(o.get("minutos"))
        if not isinstance(ses, str) or not CLAVE_SESION.match(ses) or \
           not isinstance(lam, int) or isinstance(lam, bool) or lam < 1 or \
           mins is None or mins <= 0:
            informe.append(f"  observación descartada, campos inválidos: {o!r}"[:110])
            continue
        ruta = deck_de(ses)
        if not ruta:
            informe.append(f"  {ses}: no encuentro su deck, la salto")
            continue
        try:
            laminas = analiza(ruta)
        except DeckIlegible as e:
            informe.append(f"  {ses}: {e}"[:110])
            continue
        # La observación se ancló al identificador de la lámina, que ids.py
        # mantiene estable. Si el deck creció o encogió, el número ya no vale
        # y el identificador sí.
        sid = o.get("sid")
        if isinstance(sid, str) and sid:
            pos = next((l["n"] for l in laminas if l["sid"] == sid), None)
            if pos is None:
                informe.append(f"  {ses}: la lámina '{sid}' ya no está en el "
                               f"deck, la salto")
                continue
            if pos != lam:
                informe.append(f"  {ses}: la lámina '{sid}' se movió de la "
                               f"{lam} a la {pos}; uso la posición nueva")
                lam = pos
        if lam > len(laminas):
            informe.append(f"  {ses}: dice lámina {lam} y el deck tiene "
                           f"{len(laminas)}, la salto")
            continue
        a = sobrecosto_observado(laminas, cfg, lam, mins)
        if a is None:
            informe.append(f"  {ses}: no hay láminas de contenido hasta la "
                           f"{lam}, la salto")
            continue
        if a < 0:
            informe.append(f"  {ses}: el guion solo ya dura más que los "
                           f"{mins:g} min observados; cuento sobrecosto cero")
            a = 0.0
        else:
            informe.append(f"  {ses}: lámina {lam} en {mins:g} min  ->  "
                           f"{a:.2f} min por lámina")
        valores.append(a)
    if valores:
        centro = statistics.median(valores)
        cfg["sobrecosto_lo"] = max(PISO_SOBRECOSTO, centro * (1 - MARGEN))
        cfg["sobrecosto_hi"] = max(centro * (1 + MARGEN), cfg["sobrecosto_lo"])
        if len(valores) > 1 and min(valores) > 0 and \
           max(valores) / min(valores) > DISPERSION:
            informe.append(f"  aviso: las observaciones discrepan entre sí "
                           f"({min(valores):.2f} a {max(valores):.2f} min por "
                           f"lámina). La banda se centra en la mediana, "
                           f"{centro:.2f}, pero la estimación es floja.")
    return cfg, informe


# --------------------------------------------------------------- salida

def veredicto(lo, hi):
    """Qué decir de una banda frente a los minutos de exposición que hay."""
    if lo > OBJETIVO:
        return (f"SOBRA MATERIAL, {lo - OBJETIVO:.0f} min de más aun yendo "
                f"fluida; da para {lo / OBJETIVO:.1f} sesiones")
    if hi > OBJETIVO:
        return (f"AJUSTADO: cabe si va fluida, y se pasa hasta "
                f"{hi - OBJETIVO:.0f} min si va pausada")
    if hi >= OBJETIVO * 0.85:
        return "ALCANZA"
    return f"FALTA MATERIAL, {OBJETIVO - hi:.0f} min por debajo de la clase"


def informe(ruta, cfg, wpm=None):
    try:
        laminas = analiza(ruta)
    except DeckIlegible as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if not laminas:
        print(f"error: {ruta} no tiene ninguna lámina", file=sys.stderr)
        return 2
    if wpm:
        cfg = dict(cfg, ritmo_ppm=float(wpm))

    print(f"{'#':>3}  {'diapositiva':<46} {'palabras':>8}  {'minutos':>12}")
    print("-" * 78)
    tot_pal = tot_fijo = 0
    faltan, marcadas = [], 0
    for lam in laminas:
        a, b = costo(lam, cfg)
        marca = []
        if lam["fijo"] is not None:
            tot_fijo += lam["fijo"]
            marca.append("fijo")
            rango = f"{a:4.1f}"
        else:
            tot_pal += lam["palabras"]
            rango = f"{a:4.1f}-{b:4.1f}"
        if lam["nivel"]:
            marca.append("r%d" % lam["nivel"])
            marcadas += 1
        if lam["corto"]:
            marca.append("corto %d s" % round(lam["corto"] / cfg["ritmo_ppm"] * 60))
        elif not lam["transito"] and lam["palabras"] and lam["fijo"] is None:
            # Un bloque de duración fija no se abrevia con un guion corto: se
            # acorta cambiando su data-min. Reclamárselo sería ruido.
            marca.append("sin corto")
            faltan.append(lam["n"])
        print(f"{lam['n']:>3}  {lam['titulo']:<46} {lam['palabras']:>8}  "
              f"{rango:>12}  {' '.join(marca)}")

    lo, hi = duracion(laminas, cfg)
    contenido = sum(1 for l in laminas if l["fijo"] is None and not l["transito"])
    print("-" * 78)
    print(f"     {len(laminas)} láminas, {contenido} de contenido    "
          f"palabras habladas: {tot_pal}   bloques de duración fija: {tot_fijo:.0f} min")
    print(f"     tiempo estimado: {lo:.0f} a {hi:.0f} min   "
          f"({cfg['ritmo_ppm']:.0f} palabras/min, más {cfg['sobrecosto_lo']:.1f} a "
          f"{cfg['sobrecosto_hi']:.1f} min por lámina de contenido)")

    vivo, pausado = hasta_donde(laminas, cfg)
    if pausado < len(laminas):
        print(f"     en {OBJETIVO} minutos se llega a la lámina {pausado} si va "
              f"pausada, {vivo} si va fluida, de {len(laminas)}")

    if marcadas:
        s1 = duracion(laminas, cfg, 1)
        s2 = duracion(laminas, cfg, 2)
        print(f"     recortando todo el nivel 1: {s1[0]:.0f} a {s1[1]:.0f} min")
        print(f"     recortando también el nivel 2: {s2[0]:.0f} a {s2[1]:.0f} min")
    else:
        print("     sin láminas marcadas con data-recorte: no hay nada que recortar")

    if faltan:
        cuales = ", ".join(str(x) for x in faltan[:24]) + (", ..." if len(faltan) > 24 else "")
        print(f"     sin guion corto: {len(faltan)} lámina"
              f"{'' if len(faltan) == 1 else 's'} ({cuales})")
    else:
        print("     todas las láminas con guion llevan su versión corta")

    # El ancho de la banda crece con el deck y eso es normal. Lo que no es
    # normal es que el sobrecosto pausado doble al fluido: entonces la
    # calibración no distingue una sesión que cabe de una que no.
    if cfg["sobrecosto_hi"] > cfg["sobrecosto_lo"] * RAZON_ANCHA:
        print(f"     aviso: el sobrecosto calibrado va de "
              f"{cfg['sobrecosto_lo']:.1f} a {cfg['sobrecosto_hi']:.1f} min por "
              f"lámina, demasiado disperso para decidir con él. Mira "
              f"'tiempos.py --ritmo'.")
    print(f"     objetivo {OBJETIVO} min  ->  {veredicto(lo, hi)}")
    return 0


def muestra_ritmo(cfg):
    print(f"calibración de {RITMO_JSON}")
    print(f"  ritmo del guion:        {cfg['ritmo_ppm']:.0f} palabras por minuto")
    print(f"  sobrecosto por lámina:  {cfg['sobrecosto_lo']:.2f} a "
          f"{cfg['sobrecosto_hi']:.2f} min")
    print(f"  sobrecosto de tránsito: {cfg['sobrecosto_leve']:.2f} min "
          f"(portada, cierre y separadores)")
    if not cfg["observaciones"]:
        print("  sin observaciones registradas: son los valores por omisión")
        return
    print(f"  {len(cfg['observaciones'])} observación"
          f"{'' if len(cfg['observaciones']) == 1 else 'es'}:")
    fresco, inf = ajusta(dict(cfg))
    for l in inf:
        print(l)
    if abs(fresco["sobrecosto_lo"] - cfg["sobrecosto_lo"]) > 0.005 or \
       abs(fresco["sobrecosto_hi"] - cfg["sobrecosto_hi"]) > 0.005:
        print(f"  ATENCIÓN: recalculado ahora daría "
              f"{fresco['sobrecosto_lo']:.2f} a {fresco['sobrecosto_hi']:.2f}. "
              f"Los decks cambiaron desde que se guardó; vuelve a correr "
              f"--observar.")


# ----------------------------------------------------------------- main

def opcion(opts, nombre):
    """Valor de --nombre=valor o de --nombre valor. Devuelve None si no está."""
    for i, x in enumerate(opts):
        if x == nombre and i + 1 < len(opts):
            return opts[i + 1]
        if x.startswith(nombre + "="):
            return x.split("=", 1)[1]
    return None


def main(argv):
    # --wpm admite las dos formas, con signo igual y con espacio. La versión
    # anterior documentaba la del espacio, y aceptar solo una de las dos
    # significaba ignorar el ritmo pedido sin decir nada.
    con_valor = {"--wpm", "--observar", "--nota", "--fecha"}
    rutas, opts, esperando = [], [], False
    for x in argv:
        if esperando:
            opts.append(x)
            esperando = False
        elif x.startswith("--"):
            opts.append(x)
            esperando = x in con_valor
        else:
            rutas.append(x)
    wpm = opcion(opts, "--wpm")
    obs = opcion(opts, "--observar")
    nota = opcion(opts, "--nota") or ""
    fecha = opcion(opts, "--fecha") or ""

    if wpm is not None:
        wpm = _num(wpm)
        if wpm is None or wpm <= 0:
            print("--wpm pide un número finito de palabras por minuto mayor "
                  "que cero", file=sys.stderr)
            return 2
        if obs is not None:
            print("--wpm y --observar no se combinan: la calibración se "
                  "guardaría medida con un ritmo y se usaría con otro",
                  file=sys.stderr)
            return 2

    cfg = carga_cfg()

    if "--ritmo" in opts and obs is None:
        muestra_ritmo(cfg)
        return 0

    if obs is not None:
        if not rutas:
            print("--observar necesita el deck de la sesión observada",
                  file=sys.stderr)
            return 2
        m = re.fullmatch(r"(\d{1,4})\s*/\s*(\d{1,4}(?:\.\d{1,4})?)", obs.strip())
        if not m:
            print("--observar se escribe --observar=LAMINA/MINUTOS, "
                  "por ejemplo --observar=46/120", file=sys.stderr)
            return 2
        lam, mins = int(m.group(1)), float(m.group(2))
        ruta = pathlib.Path(rutas[0])
        try:
            laminas = analiza(ruta)
        except DeckIlegible as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        if lam < 1 or lam > len(laminas):
            print(f"la lámina {lam} no existe: el deck tiene {len(laminas)}",
                  file=sys.stderr)
            return 2
        if mins <= 0:
            print("los minutos observados tienen que ser mayores que cero",
                  file=sys.stderr)
            return 2
        ses = CLAVE_SESION.match(ruta.resolve().parent.name.split("-")[0])
        if not ses:
            print(f"no deduzco la sesión del directorio {ruta.parent.name}; "
                  f"esperaba algo como sesiones/S03-...", file=sys.stderr)
            return 2
        clave = ses.group(0)
        cfg["observaciones"] = [o for o in cfg["observaciones"]
                                if not (isinstance(o, dict) and o.get("sesion") == clave)]
        cfg["observaciones"].append({
            "sesion": clave, "fecha": fecha, "laminas": lam,
            "sid": laminas[lam - 1]["sid"], "total": len(laminas),
            "minutos": mins, "nota": nota,
        })
        cfg["observaciones"].sort(key=lambda o: o.get("sesion", ""))
        cfg, inf = ajusta(cfg)
        try:
            guarda_cfg(cfg)
        except OSError as e:
            print(f"error: no pude escribir {RITMO_JSON}: {e}", file=sys.stderr)
            return 2
        print(f"registrado: {clave}, lámina {lam} en {mins:g} minutos")
        for l in inf:
            print(l)
        print(f"sobrecosto por lámina recalibrado: {cfg['sobrecosto_lo']:.2f} a "
              f"{cfg['sobrecosto_hi']:.2f} min")
        print()

    if not rutas:
        print(__doc__.strip().split("\n\n")[1].strip())
        print("\n    --wpm N        estima con otro ritmo de habla")
        return 2
    ruta = pathlib.Path(rutas[0])
    if not ruta.is_file():
        print(f"no encuentro el deck {ruta}", file=sys.stderr)
        return 2
    return informe(ruta, cfg, wpm)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
