# La visita guiada al sitio

Presentación del sitio de divulgación a la dirección general, el 29 de octubre de
2026. Catorce paradas, de doce a quince minutos.

Lo que la distingue del deck del observatorio enoturístico, de donde viene toda la
maquinaria: **ocho de las catorce láminas son el sitio de verdad**. Cargan la página
publicada dentro de la lámina, en un iframe. Una captura de un recorrido de
scrollytelling está muerta, y el argumento del sitio es que se mueve.

## Para trabajar

    python3 tools/servir.py 1       # arranca y da las ligas
    python3 tools/servir.py --parar # lo apaga

El puerto es el **8933**: el 8931 es del curso y el 8932 el del observatorio, y los
tres servidores conviven.

El paquete de un archivo está en `salidas/S01-para-presentar.html`. Abre con doble
clic, trae el apuntador dentro, y **necesita conexión**, porque las paradas cargan el
sitio de verdad desde https://albertogarob.github.io/cgeoqro-sitio-divulgacion/

## Las teclas

| Tecla | Qué hace | Dónde se pulsa |
|---|---|---|
| **T** | abre el apuntador | en el deck |
| **M** | dentro del apuntador, enseña la lámina arriba y el guion abajo | en el apuntador |
| **V** | el apuntador pasa a ventana flotante, por encima de las demás | en el apuntador |
| **Y** | enciende el resaltado sincronizado | en el apuntador |
| **↓ ↑** | mueve el guion párrafo a párrafo, y con él el resaltado | en el apuntador |
| **I** | deja el sitio de la parada sordo a los clics, y lo devuelve | en el deck |
| **D** | modo demo: el sitio ocupa la lámina entera, sin tira de puntos ni resaltado | en el deck |

## El control de las paradas

Una parada tiene un iframe con el sitio dentro, y **se puede picar desde el primer
momento**: al play del recorrido, a un enlace, a lo que sea.

Lo que hay que saber: en cuanto el foco entra en el iframe, **las flechas dejan de
mover el deck**, porque es otro origen y el teclado ya no vuelve. No estorba si se
presenta con el apuntador abierto, que es lo normal: desde esa ventana las flechas
mueven el deck igual. Quien presente sin apuntador y se quede sin flechas pulsa **el
botón de la barra**, que deja el iframe sordo a los clics y devuelve el teclado. Al
cambiar de parada el sitio vuelve a estar vivo.

El resaltado sincronizado marca **la tira de puntos de la derecha y, a la vez, lo que
ese punto señala dentro del sitio**. La tira dice qué mirar en cada parada y barre de
arriba hacia abajo mientras avanzas el guion; el contorno rojo dentro del iframe lo
dibuja el propio sitio, que trae un oyente para eso (`src/components/VisitaGuiada.astro`),
porque desde el deck no se puede tocar el DOM de otro origen. Si lo señalado se queda
fuera de la pantalla, el sitio se desplaza solo hasta enseñarlo.

El contorno va acompañado de **una penumbra sobre el resto de la página**, que es una
sola capa oscura con un agujero por cada cosa resaltada. Cuando un punto señala varias
cosas a la vez, las varias quedan claras: esa es la razón de que sea una capa con
agujeros y no una sombra por contorno.

**Un párrafo del guion sin `data-sinc` apaga las dos cosas**, contorno y penumbra. Van
sin anclaje la frase con la que abre cada parada, que sirve para decir qué es esa página
antes de señalar nada, y el párrafo del recorrido donde toca el demo a mano.

Y para el demo de verdad está la tecla **D**: el sitio pasa a ocupar la lámina entera,
se va la tira de puntos y se apaga el resaltado, de modo que la página se ve como la
vería cualquiera. Mientras dure, avanzar el guion no vuelve a encender nada. D otra vez,
o cambiar de parada, lo devuelve todo.

## Lo que dicen las herramientas

| Herramienta | Qué caza | Estado al 29 de octubre |
|---|---|---|
| `verifica-lamina-por-lamina.py` | texto recortado por debajo del borde | sin desbordes ni colisiones |
| `titulos.py` | títulos de más de una línea | los 4 caben en una línea |
| `gordas.py` | láminas gordas de texto | ninguna, de 4 medidas |
| `barrido.py` | resaltado que salta en vez de barrer | 11 láminas con piezas, 0 rompen el barrido |
| `tiempos.py` | cuánto dura | 12 a 15 min; 10 a 12 recortando los dos niveles |
| `guion.py` | regenera `guion.md` desde el deck | 14 de 14 con guion |
| `empaquetar.py` | el archivo único | 1.4 MB, con apuntador |

El objetivo de `tiempos.py` se bajó a **12 minutos** (en el deck del observatorio son
10). La calibración de `admin/ritmo.json` se trajo tal cual: 135 palabras por minuto
medidas, y un sobrecosto por lámina que sigue siendo **un supuesto sin medir**.

## Qué se puede recortar en vivo

`data-recorte` dice cuánto cuesta perder una parada.

* **Las series temáticas**, nivel 1. Se cae sin que nadie lo note.
* **La ficha de un investigador**, nivel 2. Se cae, pero hay que decir que existe.
* **De dónde sale cada cosa**, nivel 2. Es la de derechos de autor: solo se cae si la
  junta se está yendo de tiempo y el tema no ha salido.

Las que no se tocan son las dos del concepto, el catálogo, el recorrido, las
entrevistas, lo que no se ve y lo que se pide.

## `anclas.py` NO se corre sobre este deck

El pipeline del curso lo incluye, y aquí rompe el deck. `anclas.py` renumera los
`data-sinc` del guion contando las piezas de la lámina, y en estas paradas cuenta como
pieza el rótulo "Qué mirar aquí" de la tira: corre todos los anclajes un número, y el
punto 1 de cada parada deja de encenderse. Pasó el 29 de octubre de 2026 y lo cazó
`barrido.py`, que saltó de 0 a 8 láminas rotas.

Aquí los `data-sinc` se escriben a mano, porque además de encender el punto de la tira
son los que mandan el selector al sitio. Si hace falta comprobar que cada punto tiene su
párrafo, se mira con `barrido.py`, que es el que entiende esta clase de lámina.

## El riesgo que hay que mirar antes de entrar

**Si no hay conexión, las ocho paradas en vivo se quedan en blanco.** No hay respaldo
grabado todavía. Si la sala es dudosa, hay dos salidas: levantar el sitio en local y
apuntar los iframes a `http://localhost:4321`, o grabar un video de cada parada y
cambiarlas por video. Las dos cuestan trabajo y ninguna está hecha.
