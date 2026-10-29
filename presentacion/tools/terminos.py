#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Caza los términos que el deck proyecta sin definirlos en pantalla.

Es la comprobación mecánica de la regla "la lámina se explica sola": lo que el
grupo ve son las láminas, porque el paquete que recibe no lleva el guion. Un
término que solo se define en el `<aside class="notes">` no está definido para
nadie más que para Alberto.

    python3 tools/terminos.py sesiones/SNN-.../index.html
    python3 tools/terminos.py sesiones/SNN-.../index.html --glosario
    python3 tools/terminos.py sesiones/SNN-.../index.html --laminas

Qué cuenta como VISIBLE: el título, el cuerpo, los rótulos y pies de los SVG, y
el pseudocódigo. Lo que NO cuenta: los cuatro bloques de `<aside>`, o sea el guion
de orador, el guion corto y los apuntes de estudio, y los comentarios del HTML.
Los apuntes quedan fuera a propósito: viajan al paquete, pero se leen después de
clase y no arreglan una lámina que no se entendió proyectada.

De dónde salen los términos que vigila, dos fuentes:

  * lo que el propio deck marca con `<strong>` en el cuerpo, que es su convención
    para decir "esto es un término";
  * `sesiones/SNN-.../terminos.txt`, uno por renglón, para los que el deck usa sin
    marcarlos. Ahí van los que se cuelan: los del pseudocódigo, los de los
    títulos y los que aparecen en prosa corrida. `--glosario` imprime un punto de
    partida para ese archivo.

Qué reporta:

  * SIN DEFINIR: el término aparece proyectado y ninguna lámina lo define.
  * USADO ANTES: se define, pero en una lámina posterior a la primera en que se
    usa. El grupo lo leyó sin saber qué era.

Una definición se reconoce por su forma, no por su contenido: "X es", "un X es",
"X quiere decir", "se llama X", "X: ..." al empezar. Es una heurística, y por eso
el reporte dice en qué lámina creyó ver cada definición, para poder desmentirla.
"""
import html
import re
import sys
import unicodedata
from pathlib import Path

SEP = re.compile(r'</(?:li|p|h2|h3|text|tspan|div|pre|code)>|<br\s*/?>', re.I)
ASIDE = re.compile(r'<aside\b.*?</aside>', re.S | re.I)
# El nombre de un tramo de video no cuenta como PRIMERA MENCIÓN: el tema lo
# esconde fuera de pantalla con .tramo y quien lo enseña es la barra del
# reproductor, que va pasando. Sin esto, "Los cuatro mundos posibles" contaba
# como una mención en pantalla y la lámina de video salía usando términos que no
# define. Desde el 6 de octubre de 2026, con los tramos.
#
# Pero SÍ cuenta como DEFINICIÓN, desde el 8 de octubre de 2026. La barra enseña
# ese texto al grupo mientras corre el tramo, así que una definición escrita ahí
# sí llega a quien mira la lámina. La asimetría es a propósito: no sirve para
# adelantar el primer uso de un término, y sí para saldarlo. El caso que lo
# destapó: la lámina del video de la ponderación por verosimilitud define el
# término en su tercer tramo y en ninguna otra parte visible, y en cuanto el
# título pasó a nombrarlo la herramienta lo daba por indefinido.
TRAMO = re.compile(r'<span class="tramo\b[^"]*"[^>]*>.*?</span>', re.S | re.I)
COMENT = re.compile(r'<!--.*?-->', re.S)
ETIQ = re.compile(r'<[^>]+>')
SECCION = re.compile(r'<section\b([^>]*)>(.*?)</section>', re.S | re.I)
ATRIB = re.compile(r'data-sid="([^"]+)"')
CLASE = re.compile(r'class="([^"]*)"')
AGENDA = 'lo que veremos hoy'     # el título fijo de la lámina de agenda
TITULO = re.compile(r'<h2[^>]*>(.*?)</h2>', re.S | re.I)
FUERTE = re.compile(r'<strong[^>]*>(.*?)</strong>', re.S | re.I)
LATEX = re.compile(r'\\\(.*?\\\)', re.S)


def plano(x):
    """Minúsculas y sin acentos, para comparar sin tropezar con la tilde."""
    x = unicodedata.normalize('NFD', x.lower())
    return ''.join(c for c in x if unicodedata.category(c) != 'Mn')


def frases(bruto, tramos=False):
    """El texto visible de una lámina, partido en fragmentos comparables.

    Con `tramos=True` conserva los rótulos de tramo de un video, cada uno como
    un fragmento aparte. Se usa solo para buscar DEFINICIONES: ver el comentario
    de TRAMO, arriba.
    """
    t = COMENT.sub(' ', bruto)
    t = ASIDE.sub(' ', t)
    t = TRAMO.sub((lambda m: '\n' + m.group(0) + '\n') if tramos else ' ', t)
    t = SEP.sub('\n', t)
    t = ETIQ.sub(' ', t)
    t = html.unescape(t)
    t = LATEX.sub(' ', t)
    salida = []
    for renglon in t.split('\n'):
        for trozo in re.split(r'(?<=[.;?!])\s+', renglon):
            trozo = re.sub(r'\s+', ' ', trozo).strip()
            if trozo:
                salida.append(trozo)
    return salida


def laminas(ruta):
    """(sid, título, [visibles], [negritas], cuenta, [visibles con tramos]).

    `cuenta` dice si la lámina entra en la comprobación. La portada y la agenda
    quedan fuera: las dos nombran de antemano lo que la sesión va a ver, y contar
    esa mención como primer uso marcaría media sesión como usada antes de tiempo.
    """
    doc = Path(ruta).read_text(encoding='utf-8')
    out = []
    for atr, cuerpo in SECCION.findall(doc):
        sid = ATRIB.search(atr)
        sid = sid.group(1) if sid else '?'
        sin_aside = TRAMO.sub(' ', ASIDE.sub(' ', COMENT.sub(' ', cuerpo)))
        tit = TITULO.search(sin_aside)
        tit = re.sub(r'\s+', ' ', ETIQ.sub('', tit.group(1))).strip() if tit else ''
        negritas = []
        for m in FUERTE.findall(sin_aside):
            w = html.unescape(re.sub(r'\s+', ' ', ETIQ.sub('', m))).strip(' .,:;()')
            if w and not w.startswith('\\'):
                negritas.append(w)
        cl = CLASE.search(atr)
        cl = cl.group(1) if cl else ''
        cuenta = 'portada' not in cl and plano(tit) != AGENDA
        out.append((sid, tit, frases(cuerpo), negritas, cuenta,
                    frases(cuerpo, tramos=True)))
    return out


ARTICULO = r'(?:un|una|el|la|los|las)'
COPULA = (r'(?:es|son|da|quiere\s+decir|significa|consiste|se\s+cumple|'
          r'se\s+reconoce|se\s+escribe)')


def patron(termino_plano):
    """El término, tolerando el plural.

    En español el número lo lleva cada palabra del sintagma, así que "cláusula
    aprendida" y "cláusulas aprendidas" son el mismo término y hay que dejar la
    ese opcional en todas. Sin esto, "mundo" y "mundos" se contaban como dos
    términos distintos y la lámina que define uno no definía al otro.
    """
    palabras = [re.escape(w) + r'(?:e?s)?' for w in termino_plano.split()]
    return r'\s+'.join(palabras)


def define(frase_plana, termino_plano):
    """¿Esta frase define el término? Se reconoce la forma, no el contenido."""
    t = patron(termino_plano)
    patrones = [
        rf'\b{ARTICULO}\s+{t}\b[^.;]{{0,80}}?\b{COPULA}\b',   # "un mundo ... es"
        rf'\b{t}\b\s+{COPULA}\b',                              # "mundo es"
        rf'\b{COPULA}\s+(?:{ARTICULO}\s+)?{t}\b',              # "esas reglas son la física"
        rf'\bse\s+(?:les?\s+)?llama[ns]?\b[^.;]{{0,40}}?\b{t}\b',  # "se le llama núcleo", "se les llama"
        rf'^(?:eso|esto|aquello)\s+es\s+(?:{ARTICULO}\s+)?{t}\b',  # "eso es el aprendizaje"
        rf'^{t}\s*:',                                          # "propagación: ..."
    ]
    return any(re.search(p, frase_plana) for p in patrones)


def revisa(ruta, extra=(), saltar=()):
    ls = laminas(ruta)
    if saltar:
        ls = [(sid, tit, frs, ng, cuenta and sid not in saltar, tr)
              for sid, tit, frs, ng, cuenta, tr in ls]
    terminos = {}
    if extra:
        # el glosario del archivo manda: decidir qué es un término es cosa de
        # una persona, y el deck usa la negrita también para dar énfasis
        for w in extra:
            terminos.setdefault(plano(w), w)
    else:
        for _, _, _, negritas, cuenta, _tr in ls:
            if cuenta:
                for w in negritas:
                    terminos.setdefault(plano(w), w)

    informe = []
    for tp, visible in sorted(terminos.items(), key=lambda kv: kv[1].lower()):
        primero = definido = None
        for i, (sid, tit, frs, _, cuenta, con_tramos) in enumerate(ls, 1):
            if not cuenta:
                continue
            for f in frs:
                fp = plano(f)
                if re.search(rf'\b{patron(tp)}\b', fp) and primero is None:
                    primero = (i, sid)
            # La definición se busca sobre el texto CON los tramos: la barra del
            # reproductor los enseña, así que una definición escrita ahí cuenta.
            for f in con_tramos:
                fp = plano(f)
                if re.search(rf'\b{patron(tp)}\b', fp) and definido is None \
                        and define(fp, tp):
                    definido = (i, sid)
        if primero is None:
            continue                      # está en el glosario pero no se proyecta
        informe.append((visible, primero, definido))
    return ls, informe


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip().splitlines()[0])
        return 2
    ruta = Path(argv[1])
    if not ruta.exists():
        print("no existe: %s" % ruta)
        return 2
    glos = ruta.parent / 'terminos.txt'
    extra, heredados, saltar = [], set(), set()
    if glos.exists():
        for l in glos.read_text(encoding='utf-8').splitlines():
            l = l.strip()
            if not l or l.startswith('#'):
                continue
            if l.startswith('!'):
                saltar.add(l[1:].strip())      # "!sid": esa lámina no cuenta
                continue
            if l.startswith('<'):
                l = l[1:].strip()              # "<término": viene de una sesión anterior
                heredados.add(plano(l))
            extra.append(l)

    ls, informe = revisa(ruta, extra, saltar)

    if '--laminas' in argv:
        for i, (sid, tit, frs, _, _, _) in enumerate(ls, 1):
            print("\n%2d. %s" % (i, sid))
            for f in frs:
                print("      " + f)
        return 0

    if '--glosario' in argv:
        print("# términos que el deck marca en negrita, como punto de partida")
        print("# añade a mano los que usa sin marcar, y borra los que no sean términos")
        for visible, _, _ in informe:
            print(visible)
        return 0

    sin = [r for r in informe if r[2] is None and plano(r[0]) not in heredados]
    # Un término marcado con "<" viene de una sesión anterior: el grupo ya lo
    # conoce, así que usarlo antes de que ESTA sesión lo vuelva a definir no es
    # un fallo. Antes la marca eximía de SIN DEFINIR y no de USADO ANTES, y eso
    # delataba como tardíos términos que no tenían por qué definirse aquí.
    tarde = [r for r in informe
             if r[2] and r[2][0] > r[1][0] and plano(r[0]) not in heredados]

    fuente = ("glosario de %s" % glos.name if extra
              else "negritas del deck, SIN glosario: correr --glosario y escribir %s" % glos.name)
    print("terminos.py: %d láminas, %d términos vigilados, %s%s"
          % (len(ls), len(informe), fuente,
             ", %d heredados de sesiones anteriores" % len(heredados) if heredados else ""))
    for visible, primero, _ in sin:
        print("   SIN DEFINIR   %-28s se proyecta desde la lámina %d, %s"
              % (visible, primero[0], primero[1]))
    for visible, primero, definido in tarde:
        print("   USADO ANTES   %-28s se usa en la %d (%s) y se define en la %d (%s)"
              % (visible, primero[0], primero[1], definido[0], definido[1]))
    if not sin and not tarde:
        print("   TODOS LOS TÉRMINOS SE DEFINEN EN PANTALLA, Y ANTES DE USARSE")
        return 0
    print("   %d sin definir, %d usados antes de definirse" % (len(sin), len(tarde)))
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
