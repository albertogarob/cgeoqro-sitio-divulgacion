#!/usr/bin/env python3
"""Prueba del estimador de duración, tools/tiempos.py.

    python3 tools/prueba-tiempos.py

Comprueba las cuatro cosas que el estimador tiene que hacer bien:

1. **El modelo.** Que cada clase de lámina cueste lo que dice el modelo: una de
   contenido, su guion más el sobrecosto; una de duración fija, exactamente sus
   minutos, tanto al recortar como sin recortar; una de tránsito, su guion más
   el sobrecosto leve; una recortada, su guion corto, o cero si no lo tiene
   escrito, y nunca más de lo que costaba entera.

2. **La calibración.** Que registrar una observación con --observar produzca un
   sobrecosto que, puesto de vuelta en el modelo, reproduzca los minutos
   observados; que con varias observaciones la banda se centre en su mediana y
   avise de la dispersión; y que las observaciones inválidas se rechacen sin
   tocar el archivo de calibración.

3. **El informe.** Que las líneas que Alberto lee de verdad digan lo que toca:
   el veredicto, hasta qué lámina se llega en la clase, y las dos duraciones
   con recorte.

4. **La robustez.** Que un admin/ritmo.json roto, un deck a medio editar, un
   data-min con una errata o un número absurdo no revienten el script ni lo
   hagan estimar con basura, y que nada de eso deje el archivo de calibración
   envenenado.

Trabaja sobre dos sesiones de mentira, sesiones/S97-prueba-tiempos y
sesiones/S98-prueba-tiempos, que crea y borra, y respalda y restaura
admin/ritmo.json, que es estado real del proyecto.
"""
import importlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import traceback

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
tiempos = importlib.import_module("tiempos")

PRUEBA = RAIZ / "sesiones" / "S98-prueba-tiempos"
OTRA = RAIZ / "sesiones" / "S97-prueba-tiempos"
RITMO = RAIZ / "admin" / "ritmo.json"

R = []


def ok(nombre, cond, extra=""):
    R.append(("OK   " if cond else "FALLA") + "  " + nombre +
             ("" if cond else "  [%s]" % extra))


def casi(a, b, tol=0.01):
    return abs(a - b) <= tol


CFG = {"ritmo_ppm": 135.0, "sobrecosto_lo": 2.0, "sobrecosto_hi": 3.0,
       "sobrecosto_leve": 0.3, "observaciones": []}


def lamina(clase="verde-linea", palabras=135, corto=0, fijo=None, nivel=0,
           titulo="Una lámina", sid=None, notas=None):
    attrs = f'class="{clase}"'
    if fijo is not None:
        attrs += f' data-min="{fijo}"'
    if nivel:
        attrs += f' data-recorte="{nivel}"'
    if sid:
        attrs += f' data-sid="{sid}" id="{sid}"'
    cuerpo = f"<h2>{titulo}</h2>"
    if notas is not None:
        cuerpo += f'<aside class="notes"><p>{notas}</p></aside>'
    elif palabras:
        cuerpo += ('<aside class="notes"><p>%s</p></aside>'
                   % " ".join(["palabra"] * palabras))
    if corto:
        cuerpo += ('<aside class="corto"><p>%s</p></aside>'
                   % " ".join(["breve"] * corto))
    return f"<section {attrs}>{cuerpo}</section>"


def deck(*laminas):
    return "<html><body><div class='slides'>" + "".join(laminas) + \
           "</div></body></html>"


def escribe(html, destino=None):
    destino = destino or (PRUEBA / "index.html")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    return destino


def corre(*args, tiempo=90):
    p = subprocess.run([sys.executable, str(RAIZ / "tools" / "tiempos.py")] +
                       [str(a) for a in args], capture_output=True, text=True,
                       cwd=str(RAIZ), timeout=tiempo)
    return p.returncode, p.stdout, p.stderr


# ------------------------------------------------------- 1. el modelo

def prueba_modelo():
    ruta = escribe(deck(lamina(palabras=135)))
    a, b = tiempos.costo(tiempos.analiza(ruta)[0], CFG)
    # 135 palabras a 135 ppm es un minuto exacto, más el sobrecosto
    ok("lámina de contenido: guion más sobrecosto",
       casi(a, 3.0) and casi(b, 4.0), f"salió {a:.3f} a {b:.3f}")

    a, b = tiempos.costo(tiempos.analiza(escribe(deck(
        lamina(palabras=540, fijo=15))))[0], CFG)
    ok("lámina de duración fija: sus minutos y ni uno más",
       casi(a, 15.0) and casi(b, 15.0), f"salió {a:.3f} a {b:.3f}")

    for clase in ("portada", "cierre", "seccion"):
        a, b = tiempos.costo(tiempos.analiza(escribe(deck(
            lamina(clase=clase, palabras=135))))[0], CFG)
        ok(f"lámina de tránsito ({clase}): sobrecosto leve, no el de contenido",
           casi(a, 1.3) and casi(b, 1.3), f"salió {a:.3f} a {b:.3f}")

    # Una lámina de diagrama no lleva guion y no por eso es de tránsito:
    # confundir las dos cosas es justo el error que costó el factor 2.5.
    lam = tiempos.analiza(escribe(deck(lamina(palabras=0))))[0]
    a, b = tiempos.costo(lam, CFG)
    ok("lámina de contenido sin guion: cuesta como contenido, no como tránsito",
       casi(a, 2.0) and casi(b, 3.0), f"salió {a:.3f} a {b:.3f}")
    ok("y no se le reclama guion corto",
       not lam["transito"] and lam["palabras"] == 0)

    lams = tiempos.analiza(escribe(deck(lamina(
        notas="[Repartir la hoja y esperar.] uno dos tres"))))
    ok("las acotaciones entre corchetes no cuentan como palabras",
       lams[0]["palabras"] == 3, f"contó {lams[0]['palabras']}")

    lams = tiempos.analiza(escribe(deck(lamina(
        notas="una dos<!-- comentario -->tres cuatro"))))
    ok("un comentario dentro del guion no fusiona ni inventa palabras",
       lams[0]["palabras"] == 4, f"contó {lams[0]['palabras']}")

    lams = tiempos.analiza(escribe(deck(
        lamina(titulo="Real"), "<!-- " + lamina(titulo="Comentada") + " -->")))
    ok("un section dentro de un comentario HTML no cuenta como lámina",
       len(lams) == 1 and lams[0]["titulo"] == "Real",
       f"contó {len(lams)}: {[l['titulo'] for l in lams]}")

    # Verticales de reveal: la envoltura no es una lámina y sus atributos no
    # son de su primer hijo.
    anidado = ('<section class="verde-linea" data-min="45" data-recorte="1">'
               + lamina(titulo="Hijo uno") + lamina(titulo="Hijo dos")
               + "</section>")
    lams = tiempos.analiza(escribe(deck(anidado)))
    ok("las secciones anidadas no heredan los atributos de su envoltura",
       len(lams) == 2 and all(l["fijo"] is None and l["nivel"] == 0 for l in lams),
       f"salieron {[(l['titulo'], l['fijo'], l['nivel']) for l in lams]}")


def prueba_recorte():
    ruta = escribe(deck(lamina(palabras=270, corto=135, nivel=1)))
    lam = tiempos.analiza(ruta)[0]
    ok("recortada con guion corto: dura su corto más el leve",
       casi(tiempos.costo(lam, CFG, 1)[0], 1.3), f"{tiempos.costo(lam, CFG, 1)}")
    ok("sin recortar sigue durando lo entero, en los dos extremos",
       casi(tiempos.costo(lam, CFG, 0)[0], 4.0) and
       casi(tiempos.costo(lam, CFG, 0)[1], 5.0), f"{tiempos.costo(lam, CFG, 0)}")

    lam = tiempos.analiza(escribe(deck(lamina(palabras=270, nivel=1))))[0]
    ok("recortada sin guion corto: se salta entera, cero minutos",
       tiempos.costo(lam, CFG, 1) == (0.0, 0.0), f"{tiempos.costo(lam, CFG, 1)}")

    lam = tiempos.analiza(escribe(deck(lamina(palabras=270, corto=135, nivel=2))))[0]
    ok("el nivel 2 no se recorta cuando solo se recorta el nivel 1",
       casi(tiempos.costo(lam, CFG, 1)[0], 4.0), f"{tiempos.costo(lam, CFG, 1)}")
    ok("el nivel 2 sí se recorta cuando se recortan los dos",
       casi(tiempos.costo(lam, CFG, 2)[0], 1.3), f"{tiempos.costo(lam, CFG, 2)}")

    # Un guion corto más largo que el largo no puede encarecer la lámina: el
    # suelo del recorte tiene que ser un suelo de verdad.
    lam = tiempos.analiza(escribe(deck(lamina(
        clase="seccion", palabras=20, corto=250, nivel=1))))[0]
    entera, corta = tiempos.costo(lam, CFG, 0), tiempos.costo(lam, CFG, 1)
    ok("recortar nunca sale más caro que contar la lámina entera",
       corta[0] <= entera[0] and corta[1] <= entera[1],
       f"entera {entera}, recortada {corta}")

    # Un bloque de duración fija no se evapora al marcarlo como recortable.
    lam = tiempos.analiza(escribe(deck(lamina(fijo=15, nivel=1, corto=30))))[0]
    ok("el recorte no toca los bloques de duración fija",
       tiempos.costo(lam, CFG, 1) == (15.0, 15.0), f"{tiempos.costo(lam, CFG, 1)}")


def prueba_hasta_donde():
    ruta = escribe(deck(*[lamina(titulo=f"L{i}") for i in range(10)]))
    lams = tiempos.analiza(ruta)
    vivo, pausado = tiempos.hasta_donde(lams, CFG, minutos=9.0)
    ok("hasta_donde corta donde el acumulado pasa del límite",
       (vivo, pausado) == (3, 2), f"salió {(vivo, pausado)}")
    ok("hasta_donde cuenta la lámina que cierra justo en el límite",
       tiempos.hasta_donde(lams, CFG, minutos=12.0)[0] == 4,
       f"salió {tiempos.hasta_donde(lams, CFG, minutos=12.0)}")
    lo, hi = tiempos.duracion(lams, CFG, hasta=3)
    ok("duracion(hasta=n) suma solo las n primeras láminas",
       casi(lo, 9.0) and casi(hi, 12.0), f"salió {lo:.2f} a {hi:.2f}")
    ok("duracion sin hasta suma el deck entero",
       casi(tiempos.duracion(lams, CFG)[0], 30.0),
       f"{tiempos.duracion(lams, CFG)}")


# --------------------------------------------------- 2. la calibración

def deck_calibracion(destino, contenido=19):
    laminas = [lamina(clase="portada", palabras=60, fijo=2, titulo="Portada"),
               lamina(clase="seccion", palabras=10, titulo="1. Bloque")]
    laminas += [lamina(palabras=150, titulo=f"L{i}", sid=f"l{i}")
                for i in range(contenido)]
    return escribe(deck(*laminas), destino / "index.html")


def prueba_calibracion():
    """El viaje de ida y vuelta: registro una observación y el sobrecosto que
    sale, puesto de vuelta en el modelo, reproduce los minutos observados."""
    deck_calibracion(PRUEBA)
    RITMO.unlink(missing_ok=True)
    cod, sal, err = corre(PRUEBA / "index.html", "--observar=12/60",
                          "--fecha=2026-01-01", "--nota=prueba")
    ok("--observar termina bien", cod == 0, f"código {cod}: {err.strip()[:200]}")

    d = json.loads(RITMO.read_text(encoding="utf-8"))
    obs = d.get("observaciones", [])
    ok("la observación queda guardada con su sesión, su fecha y su nota",
       len(obs) == 1 and obs[0]["sesion"] == "S98" and obs[0]["laminas"] == 12
       and obs[0]["fecha"] == "2026-01-01" and obs[0]["nota"] == "prueba",
       f"quedó {obs}")
    ok("y anclada al identificador de la lámina, no solo a su número",
       obs[0].get("sid") == "l9" and obs[0].get("total") == 21,
       f"sid={obs[0].get('sid')} total={obs[0].get('total')}")
    ok("el archivo guardado es JSON estándar, sin Infinity ni NaN",
       "Infinity" not in RITMO.read_text() and "NaN" not in RITMO.read_text())

    cfg = tiempos.carga_cfg()
    lams = tiempos.analiza(PRUEBA / "index.html")
    a = tiempos.sobrecosto_observado(lams, cfg, 12, 60)
    centro = dict(cfg, sobrecosto_lo=a, sobrecosto_hi=a)
    lo, hi = tiempos.duracion(lams, centro, hasta=12)
    ok("el sobrecosto ajustado reproduce los minutos observados",
       casi(lo, 60.0, 0.05) and casi(hi, 60.0, 0.05),
       f"reprodujo {lo:.2f} a {hi:.2f} en vez de 60")

    # La banda no solo contiene la observación: la contiene con el ancho que
    # dice el margen, ni más ni menos.
    ok("la banda sale centrada en lo observado, con el margen declarado",
       casi(cfg["sobrecosto_lo"], a * (1 - tiempos.MARGEN), 0.005) and
       casi(cfg["sobrecosto_hi"], a * (1 + tiempos.MARGEN), 0.005),
       f"banda {cfg['sobrecosto_lo']:.3f} a {cfg['sobrecosto_hi']:.3f}, "
       f"esperaba {a*(1-tiempos.MARGEN):.3f} a {a*(1+tiempos.MARGEN):.3f}")
    lo, hi = tiempos.duracion(lams, cfg, hasta=12)
    ok("y los 60 minutos observados caen dentro, no en el borde",
       lo < 60 - 0.5 and 60 + 0.5 < hi, f"banda {lo:.2f} a {hi:.2f}")

    # ajusta() sin pasar por carga_cfg, que endereza bandas y taparía el error
    crudo = dict(tiempos.OMISION, observaciones=list(cfg["observaciones"]))
    salida, _ = tiempos.ajusta(crudo)
    ok("ajusta deja la banda en orden por sí sola, sin que nadie la enderece",
       salida["sobrecosto_lo"] <= salida["sobrecosto_hi"],
       f"{salida['sobrecosto_lo']:.3f} a {salida['sobrecosto_hi']:.3f}")
    ok("ajusta pone el mínimo abajo y el máximo arriba, no al revés",
       salida["sobrecosto_lo"] < a < salida["sobrecosto_hi"],
       f"{salida['sobrecosto_lo']:.3f} < {a:.3f} < {salida['sobrecosto_hi']:.3f}")

    corre(PRUEBA / "index.html", "--observar=15/60")
    obs = json.loads(RITMO.read_text(encoding="utf-8"))["observaciones"]
    ok("volver a observar la misma sesión sustituye, no duplica",
       len(obs) == 1 and obs[0]["laminas"] == 15, f"quedó {obs}")

    a1 = tiempos.sobrecosto_observado(lams, cfg, 12, 60)
    a2 = tiempos.sobrecosto_observado(lams, cfg, 12, 90)
    ok("más minutos para las mismas láminas implican más sobrecosto",
       a2 > a1, f"{a2:.2f} no es mayor que {a1:.2f}")


def prueba_varias_observaciones():
    deck_calibracion(PRUEBA)
    deck_calibracion(OTRA)
    RITMO.unlink(missing_ok=True)
    corre(PRUEBA / "index.html", "--observar=12/60")
    corre(OTRA / "index.html", "--observar=12/90")
    cfg = tiempos.carga_cfg()
    ok("las observaciones quedan ordenadas por sesión",
       [o["sesion"] for o in cfg["observaciones"]] == ["S97", "S98"],
       f"{[o['sesion'] for o in cfg['observaciones']]}")

    lams = tiempos.analiza(PRUEBA / "index.html")
    a1 = tiempos.sobrecosto_observado(lams, cfg, 12, 60)
    a2 = tiempos.sobrecosto_observado(lams, cfg, 12, 90)
    centro = (a1 + a2) / 2          # la mediana de dos valores es su promedio
    ok("con dos observaciones la banda se centra en su mediana",
       casi(cfg["sobrecosto_lo"], centro * (1 - tiempos.MARGEN), 0.01) and
       casi(cfg["sobrecosto_hi"], centro * (1 + tiempos.MARGEN), 0.01),
       f"banda {cfg['sobrecosto_lo']:.3f} a {cfg['sobrecosto_hi']:.3f}, "
       f"mediana esperada {centro:.3f}")

    _, inf = tiempos.ajusta(dict(cfg))
    ok("y avisa de que las dos observaciones discrepan entre sí",
       any("discrepan" in l for l in inf), f"{inf}")

    # La observación se movió de sitio: el identificador manda sobre el número.
    lams = [lamina(clase="portada", palabras=60, fijo=2, titulo="Portada"),
            lamina(clase="seccion", palabras=10, titulo="Nueva")]
    lams += [lamina(palabras=150, titulo=f"L{i}", sid=f"l{i}") for i in range(19)]
    escribe(deck(lamina(palabras=150, titulo="Insertada", sid="nueva"), *lams),
            PRUEBA / "index.html")
    _, inf = tiempos.ajusta(dict(tiempos.carga_cfg()))
    ok("si la lámina observada se movió, se reencuentra por su identificador",
       any("se movió" in l for l in inf), f"{inf}")

    escribe(deck(lamina(palabras=150, titulo="Otra cosa")), PRUEBA / "index.html")
    _, inf = tiempos.ajusta(dict(tiempos.carga_cfg()))
    ok("si la lámina observada desapareció, la observación se descarta",
       any("ya no está" in l for l in inf), f"{inf}")


def prueba_observaciones_invalidas():
    deck_calibracion(PRUEBA)
    RITMO.unlink(missing_ok=True)
    corre(PRUEBA / "index.html", "--observar=12/60")
    antes = RITMO.read_bytes()
    casos = [
        ("--observar=0/120", "lámina cero"),
        ("--observar=999/120", "lámina que no existe"),
        ("--observar=5/0", "cero minutos"),
        ("--observar=cinco/120", "formato que no es número"),
        ("--observar=5", "formato sin minutos"),
        ("--observar=5/" + "9" * 400, "minutos que desbordan a infinito"),
        ("--observar=" + "9" * 5000 + "/120", "una lámina de cinco mil dígitos"),
    ]
    for arg, que in casos:
        cod, sal, err = corre(PRUEBA / "index.html", arg)
        ok(f"--observar rechaza {que}", cod != 0, f"código {cod}: {sal[:80]}")
    ok("un --observar rechazado no toca admin/ritmo.json",
       RITMO.read_bytes() == antes, "el archivo cambió")
    ok("y el archivo sigue siendo JSON legible",
       isinstance(json.loads(RITMO.read_text(encoding="utf-8")), dict))

    ok("--observar sin deck se rechaza", corre("--observar=5/60")[0] != 0)
    ok("--wpm rechaza un ritmo de cero",
       corre("--wpm=0", PRUEBA / "index.html")[0] != 0)
    for v in ("inf", "nan", "-5"):
        ok(f"--wpm rechaza {v}",
           corre(f"--wpm={v}", PRUEBA / "index.html")[0] != 0)
    ok("--wpm y --observar juntos se rechazan, no se mezclan ritmos",
       corre(PRUEBA / "index.html", "--wpm=200", "--observar=5/60")[0] != 0)
    ok("no quedan temporales de la escritura atómica",
       not list(RITMO.parent.glob("*.tmp")),
       str(list(RITMO.parent.glob("*.tmp"))))


def prueba_atomicidad():
    """Si la escritura falla a media faena, el archivo anterior sobrevive
    entero. Se provoca el fallo desde dentro, con un volcado que revienta."""
    deck_calibracion(PRUEBA)
    RITMO.unlink(missing_ok=True)
    corre(PRUEBA / "index.html", "--observar=12/60")
    antes = RITMO.read_bytes()
    cfg = tiempos.carga_cfg()
    original = tiempos.json.dump

    def revienta(*a, **k):
        a[1].write('{"a_medias":')
        raise OSError("disco lleno de mentira")

    tiempos.json.dump = revienta
    try:
        tiempos.guarda_cfg(cfg)
        fallo = False
    except OSError:
        fallo = True
    finally:
        tiempos.json.dump = original
    ok("una escritura que falla a media faena propaga el error", fallo)
    ok("y deja el archivo anterior intacto, no a medias",
       RITMO.read_bytes() == antes, f"quedó {RITMO.read_bytes()[:60]!r}")
    ok("y sin temporales sueltos", not list(RITMO.parent.glob("*.tmp")))

    modo = RITMO.stat().st_mode & 0o777
    ok("el archivo conserva permisos de lectura para el grupo",
       modo & 0o044 == 0o044, f"modo {oct(modo)}")


# ------------------------------------------------------- 3. el informe

def prueba_informe():
    RITMO.unlink(missing_ok=True)
    # Un deck corto: tiene que decir que falta material.
    escribe(deck(lamina(clase="portada", palabras=60), lamina(palabras=135)))
    cod, sal, err = corre(PRUEBA / "index.html")
    ok("un deck corto se reporta como falta de material",
       cod == 0 and "FALTA MATERIAL" in sal, f"veredicto: {sal[-200:]}")

    # Un deck largo: sobra material, y dice hasta dónde se llega.
    escribe(deck(*[lamina(titulo=f"L{i}") for i in range(80)]))
    cod, sal, err = corre(PRUEBA / "index.html")
    ok("un deck largo se reporta como material que sobra",
       "SOBRA MATERIAL" in sal, f"veredicto: {sal[-200:]}")
    m = re.search(r"se llega a la lámina (\d+) si va pausada, (\d+) si va fluida", sal)
    ok("y dice hasta qué lámina se llega en la clase", bool(m), sal[-300:])
    if m:
        lams = tiempos.analiza(PRUEBA / "index.html")
        esperado = tiempos.hasta_donde(lams, tiempos.carga_cfg())
        ok("con los números que da el modelo",
           (int(m.group(2)), int(m.group(1))) == esperado,
           f"informe {m.group(2)},{m.group(1)} contra modelo {esperado}")

    # Un deck a la medida: alcanza.
    escribe(deck(*[lamina(titulo=f"L{i}") for i in range(35)]))
    cod, sal, err = corre(PRUEBA / "index.html")
    ok("un deck a la medida de la clase se reporta como que alcanza",
       "ALCANZA" in sal or "AJUSTADO" in sal, f"veredicto: {sal[-200:]}")

    # Los dos casos se escriben RELATIVOS al objetivo, no contra 120: cuando
    # bajó a 105, al descontar el receso, la versión que lo tenía a pelo se
    # quedó desfasada y marcó en rojo algo que estaba bien.
    obj = tiempos.OBJETIVO
    ok("el veredicto no llama ALCANZA a un deck que se pasa del objetivo",
       "SOBRA" in tiempos.veredicto(obj + 6, obj + 6),
       tiempos.veredicto(obj + 6, obj + 6))
    ok("un deck que cabe fluido y se pasa pausado se marca como ajustado",
       "AJUSTADO" in tiempos.veredicto(obj - 10, obj + 15),
       tiempos.veredicto(obj - 10, obj + 15))

    # Las dos líneas de recorte, con sus cifras, y sin contradecirse.
    escribe(deck(lamina(palabras=270, corto=135, nivel=1, titulo="R1"),
                 lamina(palabras=270, corto=135, nivel=2, titulo="R2"),
                 lamina(palabras=270, titulo="Núcleo")))
    cod, sal, err = corre(PRUEBA / "index.html")
    cfg = tiempos.carga_cfg()
    lams = tiempos.analiza(PRUEBA / "index.html")
    m1 = re.search(r"recortando todo el nivel 1: (\d+) a (\d+)", sal)
    m2 = re.search(r"recortando también el nivel 2: (\d+) a (\d+)", sal)
    ok("con láminas marcadas, el informe da las dos duraciones con recorte",
       bool(m1) and bool(m2) and "no hay nada que recortar" not in sal,
       sal[-400:])
    if m1 and m2:
        e1, e2 = tiempos.duracion(lams, cfg, 1), tiempos.duracion(lams, cfg, 2)
        ok("y no las intercambia: el nivel 2 recorta más que el nivel 1",
           int(m1.group(1)) == round(e1[0]) and int(m2.group(1)) == round(e2[0])
           and int(m2.group(1)) <= int(m1.group(1)),
           f"informe {m1.groups()} y {m2.groups()}, modelo {e1} y {e2}")

    escribe(deck(lamina(palabras=270), lamina(palabras=270)))
    cod, sal, err = corre(PRUEBA / "index.html")
    ok("sin láminas marcadas lo dice, y no imprime cifras de recorte",
       "no hay nada que recortar" in sal and "recortando todo" not in sal,
       sal[-300:])

    escribe(deck(lamina(palabras=270), lamina(palabras=270, corto=30),
                 lamina(clase="portada", palabras=60),
                 lamina(palabras=270, fijo=10, titulo="Discusión")))
    cod, sal, err = corre(PRUEBA / "index.html")
    ok("lista las láminas sin guion corto, y solo esas",
       "sin guion corto: 1 lámina (1)" in sal, sal[-300:])
    ok("y no le reclama guion corto a un bloque de duración fija",
       "sin guion corto: 1 lámina" in sal, sal[-300:])

    # La banda demasiado ancha tiene que avisar en vez de tranquilizar.
    RITMO.write_text(json.dumps({"sobrecosto_lo": 0.4, "sobrecosto_hi": 4.6}),
                     encoding="utf-8")
    escribe(deck(*[lamina(titulo=f"L{i}") for i in range(60)]))
    cod, sal, err = corre(PRUEBA / "index.html")
    ok("una calibración absurdamente dispersa se señala",
       "demasiado disperso" in sal, sal[-400:])
    RITMO.unlink(missing_ok=True)
    escribe(deck(*[lamina(titulo=f"L{i}") for i in range(60)]))
    cod, sal, err = corre(PRUEBA / "index.html")
    ok("y un deck largo con la calibración sana no dispara ese aviso",
       "demasiado disperso" not in sal, sal[-300:])

    cod, sal, err = corre("--ritmo")
    ok("--ritmo funciona y enseña la calibración",
       cod == 0 and "sobrecosto por lámina" in sal,
       f"código {cod}: {sal[:200]}")
    RITMO.unlink(missing_ok=True)
    cod, sal, err = corre("--ritmo")
    ok("--ritmo sin calibración dice que son los valores por omisión",
       cod == 0 and "por omisión" in sal, f"código {cod}: {sal[:200]}")


# ------------------------------------------------------ 4. la robustez

def prueba_ritmo_roto():
    escribe(deck(lamina(palabras=135)))
    ruta = PRUEBA / "index.html"
    for contenido, que in [("{esto no es json", "un JSON roto"),
                           ("[]", "una lista en vez de un objeto"),
                           ("", "un archivo vacío")]:
        RITMO.write_text(contenido, encoding="utf-8")
        cod, sal, err = corre(ruta)
        ok(f"con {que} sigue estimando y avisa",
           cod == 0 and "aviso" in err, f"código {cod}, stderr: {err.strip()[:120]}")

    RITMO.write_text(json.dumps({"ritmo_ppm": -5, "sobrecosto_lo": "mucho",
                                 "sobrecosto_hi": True, "sobrecosto_leve": 0}),
                     encoding="utf-8")
    cfg = tiempos.carga_cfg(avisa=False)
    ok("los valores absurdos se descartan y se usan los de omisión",
       cfg["ritmo_ppm"] == tiempos.OMISION["ritmo_ppm"] and
       cfg["sobrecosto_lo"] == tiempos.OMISION["sobrecosto_lo"],
       f"quedó {cfg['ritmo_ppm']} y {cfg['sobrecosto_lo']}")

    RITMO.write_text('{"sobrecosto_lo": Infinity, "sobrecosto_hi": Infinity}',
                     encoding="utf-8")
    cfg = tiempos.carga_cfg(avisa=False)
    ok("un Infinity en el archivo no envenena la estimación",
       cfg["sobrecosto_lo"] == tiempos.OMISION["sobrecosto_lo"],
       f"quedó {cfg['sobrecosto_lo']}")

    RITMO.write_text(json.dumps({"sobrecosto_lo": 5, "sobrecosto_hi": 2}),
                     encoding="utf-8")
    cfg = tiempos.carga_cfg(avisa=False)
    ok("una banda al revés se endereza en vez de dar duraciones negativas",
       cfg["sobrecosto_lo"] <= cfg["sobrecosto_hi"],
       f"{cfg['sobrecosto_lo']} a {cfg['sobrecosto_hi']}")

    RITMO.write_text(json.dumps({"observaciones": {"no": "soy lista"}}),
                     encoding="utf-8")
    cfg = tiempos.carga_cfg(avisa=False)
    ok("unas observaciones que no son una lista se ignoran",
       cfg["observaciones"] == [], f"{cfg['observaciones']}")

    RITMO.write_text(json.dumps({"observaciones": [
        "no soy un objeto",
        {"sesion": "S96", "laminas": 3, "minutos": 10},
        {"sesion": "S98", "laminas": 99999, "minutos": 10},
        {"sesion": "S98", "laminas": 1, "minutos": -4}]}), encoding="utf-8")
    cfg2, inf = tiempos.ajusta(dict(tiempos.carga_cfg(avisa=False)))
    ok("las observaciones inservibles se descartan una por una",
       len(inf) == 4 and all("descartad" in l or "salto" in l for l in inf),
       f"informe: {inf}")
    ok("y sin ninguna válida la banda se queda en la de omisión",
       cfg2["sobrecosto_lo"] == tiempos.OMISION["sobrecosto_lo"],
       f"{cfg2['sobrecosto_lo']}")

    # El campo sesion entra en un glob: no puede salirse del proyecto.
    ok("deck_de rechaza una travesía de rutas",
       tiempos.deck_de("../../../../tmp/fuera") is None)
    ok("deck_de rechaza comodines",
       tiempos.deck_de("*") is None and tiempos.deck_de("S0*") is None)
    ok("deck_de sí encuentra una sesión de verdad",
       tiempos.deck_de("S98") is not None)

    RITMO.unlink(missing_ok=True)
    cod, sal, err = corre(ruta)
    ok("sin admin/ritmo.json se estima con los valores por omisión",
       cod == 0 and "1.5 a 2.0" in sal, f"código {cod}")


def prueba_decks_rotos():
    RITMO.unlink(missing_ok=True)
    cod, sal, err = corre(escribe("<html><body>nada</body></html>"))
    ok("un deck sin láminas se reporta, no revienta",
       cod != 0 and "lámina" in err, f"código {cod}, stderr: {err.strip()[:120]}")

    cod, sal, err = corre(PRUEBA / "no-existe.html")
    ok("un archivo que no existe se reporta, no revienta",
       cod != 0 and "encuentro" in err, f"código {cod}")

    cod, sal, err = corre(RAIZ / "sesiones")
    ok("un directorio en vez de un deck se reporta, no revienta",
       cod != 0 and "Traceback" not in err, f"código {cod}: {err[:150]}")

    binario = PRUEBA / "binario.html"
    binario.write_bytes(bytes(range(256)) * 8)
    cod, sal, err = corre(binario)
    ok("un archivo que no es texto se reporta, no revienta",
       cod != 0 and "Traceback" not in err, f"código {cod}: {err[:150]}")

    for valor in ("1.2.3", ".", "abc", "9" * 400, "-3"):
        escribe(deck(f'<section class="verde-linea" data-min="{valor}">'
                     f'<h2>T</h2><aside class="notes"><p>uno dos</p></aside>'
                     f'</section>'))
        cod, sal, err = corre(PRUEBA / "index.html")
        ok(f'un data-min="{valor[:12]}" avisa y se mide por el guion',
           cod == 0 and "aviso" in err and "Traceback" not in err,
           f"código {cod}: {err[:150]}")

    # Un deck a medio editar cuelga el patrón perezoso: hay que decirlo, no
    # tardar dos minutos en no decir nada.
    escribe("<div class='slides'>" +
            ('<section class="verde-linea"><h2>T</h2>' + "texto " * 250) * 3000 +
            "</div>")
    try:
        cod, sal, err = corre(PRUEBA / "index.html", tiempo=25)
        ok("un deck con secciones sin cerrar se reporta en el acto",
           cod != 0 and "medio editar" in err, f"código {cod}: {err[:150]}")
    except subprocess.TimeoutExpired:
        ok("un deck con secciones sin cerrar se reporta en el acto", False,
           "se colgó más de 25 segundos")


def prueba_wpm():
    escribe(deck(lamina(palabras=270)))
    ruta = PRUEBA / "index.html"
    RITMO.unlink(missing_ok=True)
    _, a, _ = corre(ruta)
    _, b, _ = corre(ruta, "--wpm=270")
    _, c, _ = corre(ruta, "--wpm", "270")
    saca = lambda s: float(re.search(r"tiempo estimado: (\d+)", s).group(1))
    ok("--wpm cambia la parte del guion pero no el sobrecosto",
       saca(b) < saca(a) and saca(b) >= 2.0, f"{saca(a)} y {saca(b)}")
    ok("--wpm acepta la forma con espacio igual que la del signo igual",
       c == b, "las dos formas dan informes distintos")


# ------------------------------------------------- 5. contra el deck real

def prueba_deck_real():
    ruta = RAIZ / "sesiones" / "S03-agentes-con-metas-y-formulacion-de-pro" / "index.html"
    if not ruta.exists():
        ok("regresión contra la S03", False, "no encuentro el deck de la S03")
        return
    lams = tiempos.analiza(ruta)
    cfg = dict(tiempos.OMISION)
    lo, hi = tiempos.duracion(lams, cfg, hasta=46)
    ok("la S03 hasta la lámina 46 estima una banda que contiene los 120 "
       "minutos que duró de verdad",
       lo <= 120 <= hi, f"banda {lo:.0f} a {hi:.0f}")
    ok("la S03 entera se estima en más de una sesión y media",
       tiempos.duracion(lams, cfg)[0] > 180,
       f"{tiempos.duracion(lams, cfg)[0]:.0f} min")
    ok("la S03 no cabe en 120 minutos y el script lo dice",
       tiempos.hasta_donde(lams, cfg)[1] < len(lams))


# ------------------------------------------------------------------ main

def main():
    respaldo = RITMO.read_bytes() if RITMO.exists() else None
    pruebas = [prueba_modelo, prueba_recorte, prueba_hasta_donde,
               prueba_calibracion, prueba_varias_observaciones,
               prueba_observaciones_invalidas, prueba_atomicidad,
               prueba_informe, prueba_ritmo_roto, prueba_decks_rotos,
               prueba_wpm, prueba_deck_real]
    try:
        for p in pruebas:
            # Un reventón en una prueba no puede ocultar el resultado de las
            # demás: se anota como falla y se sigue.
            try:
                p()
            except Exception:
                ok(f"{p.__name__} corre sin reventar", False,
                   traceback.format_exc().strip().splitlines()[-1])
    finally:
        shutil.rmtree(PRUEBA, ignore_errors=True)
        shutil.rmtree(OTRA, ignore_errors=True)
        for t in RITMO.parent.glob("*.tmp"):
            t.unlink(missing_ok=True)
        if respaldo is None:
            RITMO.unlink(missing_ok=True)
        else:
            RITMO.write_bytes(respaldo)
    for l in R:
        print(l)
    fallas = [l for l in R if l.startswith("FALLA")]
    print("-" * 60)
    print(f"{len(R) - len(fallas)} de {len(R)} pruebas pasan")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
