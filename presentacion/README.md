# La visita guiada al sitio

Presentación del sitio de divulgación a la dirección general, el 29 de octubre de
2026. Catorce paradas, de doce a quince minutos.

Lo que la distingue del deck del observatorio enoturístico, de donde viene toda la
maquinaria: **ocho de las trece paradas no son láminas, son el sitio**. Cargan la
página publicada dentro de la lámina, en un iframe. Una captura de un recorrido de
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

## El control de las paradas

Una parada tiene un iframe con el sitio dentro, y **se puede picar desde el primer
momento**: al play del recorrido, a un enlace, a lo que sea.

Lo que hay que saber: en cuanto el foco entra en el iframe, **las flechas dejan de
mover el deck**, porque es otro origen y el teclado ya no vuelve. No estorba si se
presenta con el apuntador abierto, que es lo normal: desde esa ventana las flechas
mueven el deck igual. Quien presente sin apuntador y se quede sin flechas pulsa **el
botón de la barra**, que deja el iframe sordo a los clics y devuelve el teclado. Al
cambiar de parada el sitio vuelve a estar vivo.

El resaltado sincronizado marca **la tira de puntos de la derecha**, no el sitio: no se
puede marcar nada dentro de un iframe de otro origen. Esa tira dice qué mirar en cada
parada, y es la que barre de arriba hacia abajo mientras avanzas el guion.

## Lo que dicen las herramientas

| Herramienta | Qué caza | Estado al 29 de octubre |
|---|---|---|
| `verifica-lamina-por-lamina.py` | texto recortado por debajo del borde | sin desbordes ni colisiones |
| `titulos.py` | títulos de más de una línea | los 4 caben en una línea |
| `gordas.py` | láminas gordas de texto | ninguna, de 4 medidas |
| `barrido.py` | resaltado que salta en vez de barrer | 11 láminas con piezas, 0 rompen el barrido |
| `tiempos.py` | cuánto dura | 12 a 15 min; 10 a 13 recortando |
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

## El riesgo que hay que mirar antes de entrar

**Si no hay conexión, las ocho paradas en vivo se quedan en blanco.** No hay respaldo
grabado todavía. Si la sala es dudosa, hay dos salidas: levantar el sitio en local y
apuntar los iframes a `http://localhost:4321`, o grabar un video de cada parada y
cambiarlas por video. Las dos cuestan trabajo y ninguna está hecha.
