#!/usr/bin/env python3
r"""Ancla cada párrafo del guion a la pieza de la lámina de la que habla.

    python3 tools/anclas.py sesiones/SNN-.../index.html
    python3 tools/anclas.py sesiones/SNN-.../index.html --ver      # sin escribir
    python3 tools/anclas.py sesiones/SNN-.../index.html --limpiar  # quita las marcas

Escribe dos atributos, y nada más:

  * `data-pieza="3"` en cada elemento resaltable del cuerpo de la lámina, en
    orden de lectura: la línea en llano, cada fórmula, cada dibujo, cada viñeta,
    cada bloque de pseudocódigo y cada video.
  * `data-sinc="3"` en cada `<p>` del guion de orador, diciendo de qué pieza
    habla ese párrafo. Puede nombrar dos, `data-sinc="2 4"`, cuando el párrafo
    manda mirar el dibujo y además desarrolla una viñeta.

Eso es lo único que lee la sincronía del guion con la lámina, la que se enciende
con la tecla Y: mientras se lee un párrafo en el apuntador, la lámina resalta su
pieza. Alberto la pidió el 12 de octubre de 2026, con dos objetivos: "que los
estudiantes asocien lo que escuchan de mí a un elemento de la lámina y que yo
pueda ver a qué elemento está asociado lo que estoy diciendo".

**Por qué se calcula aquí y no en el navegador.** Por lo mismo que en
`tools/parcelas.py`: MathJax se lleva el texto de las expresiones al componerlas,
así que en tiempo de ejecución \(\mathrm{Soc}(t)\) ya no es texto que se pueda
comparar. Aquí se lee el HTML crudo, donde todavía está, y el resultado queda
escrito e inspeccionable. Con `--ver` se audita el emparejamiento antes de
escribirlo.

**Qué NO hace.** No adivina. Un párrafo cuyo mejor candidato no despega del
segundo se queda sin ancla, y sin ancla la lámina no resalta nada: en clase es
mejor que no se mueva nada que resaltar la viñeta equivocada. Y un guion de un
solo párrafo no se ancla, porque ese párrafo habla de la lámina entera.

**Lo escrito a mano se respeta.** Un párrafo con `data-sinc-mano="1"` conserva
su `data-sinc` tal cual y no se recalcula nunca, así que una corrección a mano
sobrevive a las pasadas siguientes.

Y hay una forma más cómoda de decirlo, por clase de pieza en vez de por número:
`data-sinc-mano="formula"`, `"dibujo"` o `"codigo"` ancla ese párrafo a todas las
piezas de esa clase de la lámina, y encima de lo que el emparejador encuentre.
Es robusta a insertar una viñeta, que es lo que haría frágil escribir el número.
Existe para el único caso que el emparejamiento no alcanza sin adivinar: una
fórmula que es una **cuenta**, y que por política no se lee en voz alta, así que
el párrafo del guion no puede contener su expresión.

Es idempotente, se corre después de `ids.py` y antes de `empaquetar.py`, y su
prueba de regresión es `tools/prueba-anclas.py`.
"""
import math
import re
import sys
import unicodedata

# Las piezas resaltables, en el orden en que se buscan dentro del cuerpo. El
# `svg` de primer nivel es el dibujo de la lámina; los de dentro de un `aside`
# ya quedaron fuera al quitar los aside, que es donde viven las glosas.
PIEZA = re.compile(r'<(li|p|pre|svg|video|img|table|figure)\b', re.I)

# Palabras que no distinguen nada. No es una lista de parada general: son las
# que aparecen en casi cualquier frase del material y, de contarlas, emparejan
# cualquier párrafo con cualquier viñeta.
VACIAS = set("""
 a al ahi ahora algo alguna algunas alguno algunos ante antes aqui asi aun aunque
 cada como con contra cual cuales cuando dado dados dan dar de del desde donde dos
 el ella ellas ellos en entre era eran es esa esas ese eso esos esta estan estas
 este esto estos fue fueron ha hace hacen hacia han hasta hay la las le les lo los
 mas me mi mientras mismo mucho muy nada ni no nos nunca o otra otras otro otros
 para parte pero poco por porque pues que queda quedan se sea segun ser si sin
 sobre solo son su sus tal tambien tan tanto te tiene tienen toda todas todo todos
 tras un una unas uno unos ya yo
""".split())

ACOTACION = re.compile(r'^\[')
AL_DIBUJO = re.compile(
    r'\[\s*(?:al|a la|a los|a las)\s+(dibujo|diagrama|figura|grafica|gráfica|video|'
    r'mapa|esquema|tabla)\b', re.I)


def plano(t):
    r"""El texto visible de un trozo de HTML, con el LaTeX convertido en palabras.

    De `\(\mathrm{Soc}(t)\)` sobreviven `soc` y `t`, que es justo lo que sirve
    para emparejar: el nombre del predicado y sus argumentos. Las órdenes de
    LaTeX, las llaves y los signos se van.
    """
    t = re.sub(r'<(script|style)\b.*?</\1>', ' ', t, flags=re.S | re.I)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = re.sub(r'\\[a-zA-Z]+', ' ', t)            # \mathrm, \sum, \mid
    t = re.sub(r'[\\{}()\[\]|&;=+*/^_$]', ' ', t)
    t = t.replace('&nbsp;', ' ').replace('&amp;', ' ')
    return re.sub(r'\s+', ' ', t).strip()


def fichas(t):
    """Las palabras con las que se compara: sin acentos, sin las vacías.

    Los números se quedan enteros y con su punto, porque `0.8804` es la ficha
    más distintiva que tiene esta sesión. Las palabras de menos de tres letras
    se van, salvo que sean un número.
    """
    t = plano(t).lower()
    t = "".join(c for c in unicodedata.normalize("NFD", t)
                if unicodedata.category(c) != "Mn")
    out = set()
    for w in re.findall(r'[a-z_]+|\d+(?:\.\d+)?', t):
        if w in VACIAS:
            continue
        if re.match(r'^\d', w) or len(w) >= 3:
            out.add(w.rstrip('s') if len(w) > 4 and w.endswith('s') else w)
    return out


def sin_asides(cuerpo):
    """El cuerpo de la lámina sin sus cuatro bloques de notas ni sus glosas."""
    return re.sub(r'<aside\b.*?</aside>', ' ', cuerpo, flags=re.S)


def cierre(html, i, tag):
    """Dónde acaba el elemento que abre en `i`, contando los anidados."""
    abre = re.compile(r'<%s\b' % tag, re.I)
    cie = re.compile(r'</%s\s*>' % tag, re.I)
    # Un elemento vacío se cierra en sí mismo.
    fin_tag = html.find('>', i)
    if fin_tag != -1 and html[fin_tag - 1] == '/':
        return fin_tag + 1
    nivel, j = 1, fin_tag + 1
    while nivel and j < len(html):
        a, c = abre.search(html, j), cie.search(html, j)
        if not c:
            return len(html)
        if a and a.start() < c.start():
            nivel += 1
            j = a.end()
        else:
            nivel -= 1
            j = c.end()
    return j


def laminas_de(html):
    """Las láminas del deck: (inicio, fin, atributos, cuerpo), sin solaparse.

    Lámina es el `<section>` que no contiene otro. En una pila vertical el de
    fuera no se proyecta nunca, así que marcarlo a él y no a los de dentro
    dejaría la pila sin sincronía. Hace falta contar el anidamiento, que es lo
    que una expresión regular no sabe hacer.
    """
    out, j = [], 0
    while True:
        m = re.compile(r'<section\b', re.I).search(html, j)
        if not m:
            return out
        fin = cierre(html, m.start(), "section")
        cab_fin = html.find('>', m.start())
        cuerpo = html[cab_fin + 1:fin - len("</section>")]
        if re.search(r'<section\b', cuerpo, re.I):
            j = cab_fin + 1            # es una pila: las láminas están dentro
            continue
        out.append((m.start(), fin, html[m.start() + len("<section"):cab_fin], cuerpo))
        j = fin


def piezas_de(cuerpo):
    """Las piezas resaltables del cuerpo, en orden: (inicio, fin, tag, texto).

    Solo las de primer nivel: un `p` dentro de un `li` no es una pieza aparte,
    porque resaltar las dos a la vez pinta dos recuadros encajados. La que
    cuenta es la de fuera, que es la que el grupo ve como una unidad.
    """
    out, j = [], 0
    while True:
        m = PIEZA.search(cuerpo, j)
        if not m:
            return out
        tag = m.group(1).lower()
        fin = cierre(cuerpo, m.start(), tag)
        trozo = cuerpo[m.start():fin]
        # Un `<p>` que solo envuelve un dibujo no es pieza: lo es el dibujo.
        if tag == "p" and re.search(r'<svg\b', trozo, re.I):
            j = m.end()
            continue
        if plano(trozo) or tag in ("svg", "video", "img"):
            out.append((m.start(), fin, tag, trozo))
        j = fin                                  # lo de dentro no se mira


# Una pieza cuyo texto es casi todo expresión matemática no compite por
# palabras: al quitarle el LaTeX no le queda prosa con la que emparejar, y sus
# fichas (`soc`, `gri`, `p`, `t`) están en todas las demás piezas de la lámina,
# así que pesan cero. Se reconoce por eso: por lo poco que queda al quitar las
# expresiones.
SIN_LATEX = re.compile(r'\\\(.*?\\\)', re.S)


def es_expresion(trozo):
    """¿Esta pieza es una fórmula y no una frase?"""
    if not re.search(r'\\\(', trozo):
        return False
    resto = plano(SIN_LATEX.sub(" ", trozo))
    return len(resto) < 18


def tiene_latex(texto):
    return bool(re.search(r'\\\(', texto))


def lineas_de_codigo(trozo):
    """Los identificadores de CADA línea de un bloque de código, por su número.

    `tools/codigo.py` envuelve cada línea en un `<span class="cl" data-cl="N">`
    desde el 13 de octubre de 2026, y esto lo lee. Sirve para que un párrafo
    que dice «forward_inference es el filtrado» encienda las dos líneas que lo
    llaman, en vez del bloque entero.

    Devuelve {número de línea: conjunto de identificadores}. Vacío si el bloque
    viene de un generador viejo que todavía no numera sus líneas, y entonces
    todo sigue funcionando como antes: se enciende el bloque completo.
    """
    # Se parte por saltos de línea y no con una expresión sobre el bloque
    # entero: `codigo.py` garantiza que ningún span cruza un salto, y la
    # versión con expresión perdía la ÚLTIMA línea, porque detrás de su
    # `</span>` no viene un salto sino `</code></pre>`.
    out = {}
    for linea in trozo.split("\n"):
        m = re.search(r'<span class="cl" data-cl="(\d+)">(.*)</span>', linea)
        if not m:
            continue
        ids = identificadores(m.group(2))
        if ids:
            out[int(m.group(1))] = ids
    return out


def enunciados_de_codigo(trozo):
    """Agrupa las líneas de un bloque en enunciados, por su sangría.

    En Python una línea que empieza con espacios continúa la anterior que
    empezaba en la columna 0. Encender `red.add_cpds(` y dejar a oscuras sus
    cinco líneas de argumentos deja el bloque partido por la mitad, así que una
    línea encendida arrastra las suyas.

    Devuelve {número de la primera línea del enunciado: [todas sus líneas]}.
    """
    import html as _h
    grupos, actual = {}, None
    for n, linea in enumerate(trozo.split("\n"), 1):
        m = re.search(r'<span class="cl" data-cl="(\d+)">(.*)</span>', linea)
        if not m:
            continue
        num = int(m.group(1))
        crudo = _h.unescape(re.sub(r'<[^>]+>', '', m.group(2)))
        if crudo.strip() and not crudo[:1].isspace():
            actual = num
            grupos[actual] = [num]
        elif actual is not None and crudo.strip():
            grupos[actual].append(num)
    return grupos


def identificadores(trozo):
    """Los nombres de un bloque de código: lo que lleva guion bajo o punto.

    Son las fichas que de verdad distinguen un `pre`: `forward_inference`,
    `pgmpy.inference`. Una palabra corriente del español no lleva ninguno de los
    dos en medio, así que no hay falsos positivos.

    Dos cuidados que costaron una depuración. **No se pasa por `plano()`**, que
    se come los guiones bajos y deja `inf.forward` donde había
    `inf.forward_inference`. Y el separador tiene que llevar algo DETRÁS, o el
    punto final de una frase convierte «pregunta.» en un identificador.

    Del nombre cualificado se guarda también su última parte, porque el guion
    dice `forward_inference` donde el código dice `inf.forward_inference`.
    """
    t = re.sub(r'<[^>]+>', ' ', trozo)
    out = set()
    for w in re.findall(r'[A-Za-z][A-Za-z0-9_]*(?:[._][A-Za-z0-9_]+)+', t):
        if len(w) <= 3:
            continue
        out.add(w.lower())
        cola = w.rsplit(".", 1)[-1]
        if "_" in cola and len(cola) > 3:
            out.add(cola.lower())
    # Y los nombres con mayúscula interior: `TabularCPD`, `DBN`, `DBNInference`.
    # No llevan guion bajo ni punto, así que la regla de arriba no los veía y
    # las líneas que solo los nombran quedaban fuera del alcance de la
    # sincronía. Añadido el 13 de octubre de 2026, cuando Alberto señaló que la
    # lámina del modelo en pgmpy no encendía ninguna línea.
    #
    # Una mayúscula que no va en la primera letra no existe en español, así que
    # de la prosa no entra nada; y un acrónimo que sí se escriba así, GPS o
    # RETE, solo cuenta si además aparece en el código, porque el
    # emparejamiento exige las dos cosas.
    for w in re.findall(r'\b[A-Za-z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*\b', t):
        if len(w) >= 3:
            out.add(w.lower())
    return out


# La portada, los separadores de sección, la de agradecimiento y la de
# bibliografía quedan fuera de la cobertura. Alberto fijó la excepción el 12 de
# octubre de 2026 al pedir la regla: un separador no se narra pieza por pieza, y
# la bibliografía se proyecta mientras se contestan preguntas, no se lee.
EXENTAS = re.compile(r'\b(portada|seccion|cierre)\b')


def exenta(attrs):
    cls = (re.search(r'class="([^"]*)"', attrs) or [None, ""])[1]
    sid = (re.search(r'data-sid="([^"]*)"', attrs) or [None, ""])[1]
    return bool(EXENTAS.search(cls)) or sid == "bibliografia"


def emparejar(parrafos, piezas):
    """Para cada párrafo, hasta cuatro piezas, o ninguna si no hay nada claro.

    Alberto confirmó el 12 de octubre de 2026 que el resaltado múltiple le gusta
    y se queda: un párrafo que habla de dos viñetas enciende las dos.

    El peso de una palabra es su rareza entre las piezas de ESTA lámina: la que
    está en una sola pieza decide, y la que está en todas no dice nada. Es la
    idea de siempre, y aquí el corpus es la lámina, que es lo que hace que
    funcione sin diccionario.
    """
    fichas_pieza = [fichas(p[3]) for p in piezas]
    n = len(piezas)
    peso = {}
    for i, f in enumerate(fichas_pieza):
        for w in f:
            peso[w] = peso.get(w, 0) + 1
    for w in list(peso):
        peso[w] = math.log((n + 1) / peso[w])

    # Qué piezas son dibujo, para la acotación "[Al dibujo...]".
    dibujos = [i for i, p in enumerate(piezas) if p[2] in ("svg", "video", "img")]
    expresiones = [i for i, p in enumerate(piezas) if es_expresion(p[3])]
    codigos = [i for i, p in enumerate(piezas) if p[2] == "pre"]
    ids_pieza = dict((i, identificadores(piezas[i][3])) for i in codigos)
    lineas_pieza = dict((i, lineas_de_codigo(piezas[i][3])) for i in codigos)
    enunc_pieza = dict((i, enunciados_de_codigo(piezas[i][3])) for i in codigos)
    # De cada línea, todas las de su enunciado: encender la que abre una
    # llamada sin sus argumentos deja el bloque partido.
    con_cola = {}
    for i in codigos:
        m = {}
        for primera, todas in enunc_pieza[i].items():
            for n in todas:
                m[n] = todas
        con_cola[i] = m

    salida = []
    # El dibujo que está vigente. Una acotación "[Al dibujo, ...]" abre un tramo
    # y la figura se queda resaltada en los párrafos siguientes, que son los que
    # la explican. Alberto lo pidió el 12 de octubre de 2026: "necesito el speech
    # de cada figura y que mientras lea ese o esos párrafos se resalte la figura
    # en el slide". Sin esto, la acotación encendía la figura un instante y el
    # párrafo siguiente ya saltaba a una viñeta, con la explicación a medias.
    # El tramo se cierra con la acotación siguiente, sea del dibujo o de escena.
    vigente = None
    debe = 0          # párrafos que el tramo tiene garantizados por su acotación
    for texto in parrafos:
        acot = AL_DIBUJO.search(texto)
        if not acot and ACOTACION.match(texto.strip()):
            vigente = None               # otra acotación de escena: se acabó el tramo
            debe = 0
        fp = fichas(re.sub(r'\[[^\]]*\]', ' ', texto))      # la prosa, sin acotaciones
        # Un párrafo que es solo acotación de escena no habla de ninguna pieza,
        # salvo que la acotación mande mirar el dibujo.
        tiene_prosa = bool(fp)
        marcas = []

        if acot and dibujos:
            # Con varios dibujos, el que mejor case con lo que nombra la
            # acotación: sus rótulos están en el propio SVG.
            if len(dibujos) == 1:
                vigente = dibujos[0]
            else:
                fa = fichas(acot.string[acot.start():])
                vigente = max(dibujos, key=lambda i: len(fa & fichas_pieza[i]))
            # La acotación garantiza el párrafo que viene detrás, que es su
            # explicación. Más allá de ese, la figura se queda solo mientras el
            # guion siga hablando de ella.
            debe = 1
        elif vigente is not None:
            if debe > 0:
                debe -= 1
            else:
                # ¿Este párrafo todavía habla de la figura? Se mide contra los
                # rótulos del propio dibujo, con la misma vara que las demás
                # piezas. Alberto lo pidió el 12 de octubre de 2026: "una vez
                # que resaltas una figura, nunca le quitas el resaltado hasta
                # que cambio de lámina... a veces distrae cuando estoy
                # discutiendo algo que no necesariamente se relaciona a la
                # figura".
                fp0 = fichas(re.sub(r'\[[^\]]*\]', ' ', texto))
                s0 = sum(peso.get(w, 0) for w in fp0 & fichas_pieza[vigente])
                if s0 / math.sqrt(len(fichas_pieza[vigente]) or 1) < UMBRAL:
                    vigente = None
        # El dibujo vigente NO compite con el texto: va aparte y no gasta una de
        # las dos plazas del emparejamiento por palabras. Si gastara una, la
        # línea en llano de la lámina se quedaba fuera en cuanto había figura,
        # que es lo que pasó al estrenar el tramo.
        texto_marcas = []
        if tiene_prosa:
            punt = []
            for i, f in enumerate(fichas_pieza):
                if i == vigente:
                    continue
                comun = fp & f
                s = sum(peso.get(w, 0) for w in comun)
                # Normalizar por el tamaño de la pieza evita que la viñeta más
                # larga gane siempre solo por tener más palabras.
                punt.append((s / math.sqrt(len(f) or 1), i))
            punt.sort(reverse=True)
            # El presupuesto: lo resaltado se lee en el tiempo que dura el
            # párrafo. Alberto lo pidió el 12 de octubre de 2026, viendo un
            # párrafo de ocho palabras que encendía dos viñetas largas: "da la
            # impresión de que fue demasiado texto el resaltado para el tiempo
            # de resaltado". Se mide en palabras, que es la unidad con la que
            # este proyecto mide el tiempo de habla.
            presupuesto = len(fp) * HOLGURA
            gastado = 0
            if punt and punt[0][0] >= UMBRAL:
                # La mejor entra siempre: dejar la lámina sin resaltar nada es
                # peor que resaltar de más.
                texto_marcas.append(punt[0][1])
                gastado = len(fichas_pieza[punt[0][1]])
                # La segunda entra si acompaña de verdad Y si cabe en el tiempo.
                if (len(punt) > 1 and not acot
                        and punt[1][0] >= UMBRAL
                        and punt[1][0] >= 0.75 * punt[0][0]
                        and gastado + len(fichas_pieza[punt[1][1]]) <= presupuesto):
                    texto_marcas.append(punt[1][1])
        if vigente is not None:
            marcas.append(vigente)
        marcas.extend(texto_marcas)
        # Señal exacta 1: un párrafo que escribe matemáticas habla de la
        # expresión de la lámina. Se anclan TODAS las piezas de expresión,
        # porque cuando hay dos son las dos mitades de la misma fórmula,
        # partida solo para que quepa a lo ancho.
        if expresiones and tiene_latex(texto):
            marcas.extend(expresiones)

        # Señal exacta 2: un párrafo que nombra algo del código habla del
        # bloque de código. El nombre lleva guion bajo o punto, así que no se
        # confunde con una palabra del español.
        #
        # Y además se mira QUÉ LÍNEAS nombra, para encender solo esas. Si no
        # acierta ninguna, se enciende el bloque entero, que es el
        # comportamiento de antes del 13 de octubre de 2026.
        ids_texto = identificadores(texto)
        cls = []
        for i in codigos:
            if ids_pieza[i] & ids_texto:
                marcas.append(i)
                suyas = []
                for num, ids in lineas_pieza[i].items():
                    if ids & ids_texto:
                        suyas.extend(con_cola[i].get(num, [num]))
                # Tope: encender más de dos tercios del bloque es, visualmente,
                # lo mismo que encenderlo entero, y no dice de qué línea se
                # está hablando. Pasa cuando el párrafo nombra una clase que
                # aparece en media docena de líneas. En ese caso no se marca
                # ninguna y el bloque se lee completo, que es el respaldo de
                # siempre. Es la misma idea que el tope de palabras resaltadas
                # por palabra de párrafo.
                suyas = sorted(set(suyas))
                cuantas = len(lineas_pieza[i]) or 1
                if len(suyas) * 3 <= cuantas * 2:
                    cls.extend(suyas)
        salida.append((sorted(set(marcas))[:4], sorted(set(cls))))
    return salida


# Cuánto texto se puede resaltar por palabra del párrafo. Un párrafo corto se
# lee en un instante, así que encender con él media lámina deja al grupo con
# texto resaltado que no da tiempo a leer. Con 1.2 la segunda pieza solo entra
# cuando el párrafo de verdad da para las dos.
HOLGURA = 1.2

# Cuánto tiene que puntuar el mejor candidato para que se escriba el ancla.
# Medido sobre la sesión 12: por debajo de 0.35 empiezan a entrar párrafos que
# comparten con la viñeta una sola palabra corriente, y eso en clase resalta la
# viñeta equivocada.
UMBRAL = 0.35


def parrafos_de(aside):
    """Los `<p>` de un bloque de notas: (inicio, fin, atributos, contenido)."""
    out = []
    for m in re.finditer(r'<p\b([^>]*)>(.*?)</p>', aside, re.S):
        out.append((m.start(), m.end(), m.group(1), m.group(2)))
    return out


def limpia_attr(attrs, *nombres):
    for n in nombres:
        attrs = re.sub(r'\s*%s="[^"]*"' % n, '', attrs)
    return attrs


def procesa(html, limpiar=False, ver=False):
    salida, fin = [], 0
    tot_p = tot_anc = tot_lam = lam_con = 0
    informe = []

    for (ini_s, fin_s, attrs, cuerpo) in laminas_de(html):
        sid = (re.search(r'data-sid="([^"]+)"', attrs) or [None, "?"])[1]
        tot_lam += 1

        # El cuerpo se parte en tramos de aside y de no-aside. Así las piezas
        # se numeran sobre lo visible y los párrafos se anclan sobre las notas,
        # sin que un trozo desplace las posiciones del otro.
        tramos = []
        k = 0
        for a in re.finditer(r'<aside\b.*?</aside>', cuerpo, flags=re.S):
            tramos.append(("vis", cuerpo[k:a.start()]))
            tramos.append(("aside", a.group(0)))
            k = a.end()
        tramos.append(("vis", cuerpo[k:]))

        visible = "".join(t for c, t in tramos if c == "vis")
        piezas = piezas_de(visible)
        np = len(piezas)

        # reescribir los tramos visibles con data-pieza
        contador = [0]

        def marca_tramo(txt):
            pz = piezas_de(txt)
            out, prev = [], 0
            for (i0, i1, tag, trozo) in pz:
                contador[0] += 1
                cab_fin = txt.find('>', i0)
                cab = txt[i0:cab_fin]
                cab = limpia_attr(cab, "data-pieza")
                if not limpiar:
                    cab += ' data-pieza="%d"' % contador[0]
                out.append(txt[prev:i0])
                out.append(cab)
                out.append(txt[cab_fin:i1])
                prev = i1
            out.append(txt[prev:])
            return "".join(out)

        # 2. anclar los párrafos del guion
        asides_out = []
        anclas_lam = []
        for clase, txt in tramos:
            if clase == "vis":
                asides_out.append(marca_tramo(txt))
                continue
            cual = re.match(r'<aside\b[^>]*class="([^"]*)"', txt)
            cual = cual.group(1) if cual else ""
            if "notes" not in cual and "corto" not in cual:
                asides_out.append(limpia_attr_ps(txt))
                continue
            ps = parrafos_de(txt)
            tot_p += len(ps) if "notes" in cual else 0
            if limpiar or len(ps) < 2 or not piezas:
                asides_out.append(limpia_attr_ps(txt))
                continue
            pares = emparejar([p[3] for p in ps], piezas)
            out, prev = [], 0
            for (ini, fin_p, at, cont), (marcas, cls) in zip(ps, pares):
                at_limpio = limpia_attr(limpia_attr(at, "data-sinc"),
                                        "data-sinc-cl")
                mano = re.search(r'data-sinc-mano="([^"]*)"', at)
                if mano and mano.group(1) != "1":
                    # Ancla simbólica: el autor dice de QUÉ CLASE de pieza
                    # habla el párrafo, y aquí se resuelve a sus números. Es
                    # robusta a insertar viñetas, que es lo que haría frágil
                    # escribir el número a mano. Existe para el caso que el
                    # emparejador no puede alcanzar sin adivinar: una fórmula
                    # que es una cuenta, y que por política NO se lee en voz
                    # alta, así que el párrafo no puede contener su expresión.
                    clase = mano.group(1)
                    cuales = {"formula": [i for i, pz in enumerate(piezas)
                                          if es_expresion(pz[3])],
                              "dibujo": [i for i, pz in enumerate(piezas)
                                         if pz[2] in ("svg", "video", "img")],
                              "codigo": [i for i, pz in enumerate(piezas)
                                         if pz[2] == "pre"]}.get(clase, [])
                    nuevo_at = at_limpio
                    if cuales:
                        marcas = sorted(set(list(marcas) + cuales))[:3]
                        nuevo_at += ' data-sinc="%s"' % " ".join(
                            str(piezas_num(piezas, i)) for i in marcas)
                elif mano:
                    nuevo_at = at                # a mano y escrita: no se toca
                else:
                    nuevo_at = at_limpio
                    if marcas:
                        nuevo_at += ' data-sinc="%s"' % " ".join(
                            str(piezas_num(piezas, i)) for i in marcas)
                        # Las líneas concretas del bloque de código de las que
                        # habla este párrafo. Sin esto se enciende el bloque
                        # entero, que es lo que hacía antes.
                        if cls:
                            nuevo_at += ' data-sinc-cl="%s"' % " ".join(
                                str(c) for c in cls)
                if marcas and "notes" in cual:
                    tot_anc += 1
                    anclas_lam.append((plano(cont)[:58], [piezas_num(piezas, i) for i in marcas],
                                       [piezas[i][2] for i in marcas]))
                out.append(txt[prev:ini])
                out.append("<p%s>%s</p>" % (nuevo_at, cont))
                prev = fin_p
            out.append(txt[prev:])
            asides_out.append("".join(out))

        if anclas_lam:
            lam_con += 1
        # Cobertura: qué piezas de la lámina no las nombra ningún párrafo del
        # guion. Es la comprobación de la política del 12 de octubre de 2026,
        # "cada viñeta, dibujo y elemento tiene su párrafo en el guion".
        # Se cuenta aparte lo que ancla un párrafo CON PROSA y lo que ancla un
        # párrafo que es solo acotación de escena. Una figura cuyo único párrafo
        # es "[Al dibujo, la barra de arriba.]" no tiene quien la explique: se
        # enciende un instante y se apaga. Alberto lo señaló el 12 de octubre de
        # 2026, y por eso la cobertura exige prosa, no solo la acotación.
        usadas, con_prosa = set(), set()
        for t in asides_out:
            for mm in re.finditer(r'<p([^>]*)>(.*?)</p>', t, re.S):
                at = re.search(r'data-sinc="([^"]*)"', mm.group(1))
                if not at:
                    continue
                nums = at.group(1).split()
                usadas.update(nums)
                if plano(re.sub(r'\[[^\]]*\]', ' ', mm.group(2))).strip():
                    con_prosa.update(nums)
        huerfanas = []
        if not limpiar and not exenta(attrs):
            for k, pz in enumerate(piezas):
                n = str(k + 1)
                if n not in usadas:
                    huerfanas.append((k + 1, pz[2], plano(pz[3])[:54]))
                elif n not in con_prosa:
                    huerfanas.append((k + 1, pz[2],
                                      "SOLO ACOTACIÓN, sin prosa que lo explique: "
                                      + plano(pz[3])[:40]))
        informe.append((sid, np, anclas_lam, huerfanas))

        salida.append(html[fin:ini_s])
        salida.append("<section%s>%s</section>" % (attrs, "".join(asides_out)))
        fin = fin_s

    salida.append(html[fin:])
    return "".join(salida), (tot_lam, lam_con, tot_p, tot_anc), informe


def piezas_num(piezas, i):
    """El número que lleva la pieza `i`: su posición, empezando en 1."""
    return i + 1


def limpia_attr_ps(aside):
    """Quita las anclas de los párrafos de un bloque que no se ancla."""
    def f(m):
        return "<p%s>%s</p>" % (limpia_attr(m.group(1), "data-sinc"), m.group(2))
    return re.sub(r'<p\b([^>]*)>(.*?)</p>', f, aside, flags=re.S)


def main(argv):
    ruta = None
    limpiar = ver = False
    for a in argv:
        if a == "--limpiar":
            limpiar = True
        elif a == "--ver":
            ver = True
        elif not a.startswith("-"):
            ruta = a
    ruta = ruta or "index.html"
    html = open(ruta, encoding="utf-8").read()
    nuevo, (tot_lam, lam_con, tot_p, tot_anc), informe = procesa(html, limpiar, ver)

    if ver:
        for sid, np, anclas, _h in informe:
            if not anclas:
                continue
            print("%s   (%d piezas)" % (sid, np))
            for texto, nums, tags in anclas:
                print("   -> %s %-14s %s" % (
                    " ".join(str(n) for n in nums),
                    "[" + ",".join(tags) + "]", texto))
    else:
        if nuevo != html:
            open(ruta, "w", encoding="utf-8").write(nuevo)
    if limpiar:
        print("anclas.py: marcas quitadas de %d láminas" % tot_lam)
        return 0
    pct = (100.0 * tot_anc / tot_p) if tot_p else 0
    print("anclas.py: %d de %d láminas con sincronía, "
          "%d de %d párrafos del guion anclados (%.0f%%)"
          % (lam_con, tot_lam, tot_anc, tot_p, pct))
    sin = [s for s, np, a, h in informe if np and not a]
    if sin:
        print("   sin ancla ninguna: " + ", ".join(sin[:8])
              + (" ..." if len(sin) > 8 else ""))

    # La cobertura, que es la otra mitad y la que de verdad se vigila: toda
    # pieza de una lámina de contenido tiene que tener su párrafo en el guion.
    huecos = [(s, h) for s, np, a, h in informe if h]
    n_h = sum(len(h) for _, h in huecos)
    if not huecos:
        print("   TODA PIEZA DE TODA LÁMINA TIENE SU PÁRRAFO EN EL GUION")
        return 0
    print("   %d piezas sin párrafo que las nombre, en %d láminas:"
          % (n_h, len(huecos)))
    for s, h in huecos:
        print("     %s" % s)
        for n, tag, txt in h:
            print("        pieza %d (%s)  %s" % (n, tag, txt))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
