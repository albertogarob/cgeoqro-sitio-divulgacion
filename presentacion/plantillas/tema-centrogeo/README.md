# Tema CentroGeo / Secihti 2026 para reveal.js

Port de `context/plantilla/Presentación Secihti-CentroGeo 2026.pptx`. Todas las geometrías
salen del XML de la plantilla, no de mediciones a ojo.

## Uso

Para una sesión nueva, no copies `demo.html`: sus rutas son relativas al directorio del tema y
se rompen al moverlo. Usa el esqueleto:

```
python3 tools/nueva-sesion.py 2
```

Lee `admin/sesiones.csv`, crea la carpeta que ahí se indica y copia
`plantilla-sesion.html` con el título, la fecha y las rutas relativas ya resueltas. No
sobrescribe una sesión existente.

`demo.html` queda como muestra de los layouts con contenido real, y `comparacion.html` como
espejo de la plantilla oficial para verificar fidelidad. El lienzo es de 1280x720 px,
que equivale a los 960x540 puntos de la plantilla, así que **1 pt = 1.3333 px**.

```
sesiones/S03-agentes-con-metas/
├── index.html      ← copia de demo.html
└── ...
```

El tema se referencia con rutas relativas al directorio `plantillas/tema-centrogeo/`.

**Para presentar, abre el archivo directamente en Chrome** (`file://`), como el deck de
MerlinRoads. Verificado que por `file://` cargan las fuentes vendorizadas, los fondos WebP y
el plugin de notas, así que el deck funciona sin conexión y sin servidor. La vista de orador
con la tecla `S` se comporta como en ese deck.

Servir por HTTP también funciona, pero no hace falta y añade una capa donde el navegador
puede bloquear la ventana emergente de la vista de orador sin avisar.

Las transiciones van desactivadas (`transition:'none'`). Con fondos a página completa, el
deslizamiento arrastra la imagen entera y marea en videollamada.

## Clases de diapositiva

| Clase | Fondo | Color de título | Uso |
|---|---|---|---|
| `portada` | fondo-3 | guinda | primera diapositiva, con `.titulo` y `.bajada` |
| `seccion` | fondo-6 | guinda 44pt | separador de bloque, solo `h2` |
| `guinda-linea` | fondo-7 | `#9C2148` | contenido, línea guinda inferior |
| `guinda-lateral` | fondo-8 | `#9C2148` | contenido, barra vertical izquierda |
| `guinda-sello` | fondo-9 | `#9C2148` | contenido, barra vertical y sello |
| `guinda-banda` | fondo-10 | `#9C2148` | contenido, banda guinda texturizada |
| `verde-linea` … `verde-banda` | fondo-11 a 14 | `#155B4E` | las mismas variantes en verde |
| `cierre` | fondo-3 | guinda | última diapositiva, con `.gracias` y `.firma` |

### Portada y cierre

La bajada de la portada lleva el nombre en guinda y, debajo, el programa y la fecha en gris,
dentro de un `span.secundario`:

```html
<div class="bajada"><strong>Sesión 5. Búsqueda informada</strong><br>
  Dr. Alberto García Robledo<br>
  <span class="secundario">Programa Interdisciplinario en Ciencias de la Información
  Geoespacial<br>15 de septiembre de 2026</span></div>
```

El cierre lleva el agradecimiento **por debajo de la regla dorada del fondo**, centrado sobre
la lámina entera y no sobre la caja del logotipo, y debajo la firma:

```html
<section class="cierre">
  <div class="gracias">Muchas Gracias</div>
  <div class="firma">
    <span class="nombre">Dr. Alberto García Robledo</span><br>
    agarcia@centrogeo.edu.mx<br>
    <span class="programa">Programa Interdisciplinario en Ciencias de la Información
    Geoespacial</span>
  </div>
</section>
```

La firma tiene que caber entre el agradecimiento y el sello de Margarita Maza del fondo, que
empieza al 79% de la altura. Cuatro renglones a 16pt lo consiguen; un quinto no cabría.

Las dos cosas vienen ya puestas en `plantilla-sesion.html`, así que una sesión nueva las trae
de fábrica.

Estructura de una diapositiva de contenido:

```html
<section class="guinda-linea">
  <h2>Título de la sesión</h2>
  <div class="cuerpo">
    <ul><li>Punto uno.</li></ul>
  </div>
  <aside class="notes">Guion de esta diapositiva.</aside>
</section>
```

## Capacidad real de cada layout

El sello "Margarita Maza" y las bandas de color invaden la caja de contenido que declara la
plantilla, así que la altura útil se recortó a lo realmente libre. Viñetas de una línea que
caben con holgura:

| Layout | Viñetas seguras |
|---|---|
| `*-lateral` (sin sello) | 9 |
| `*-linea`, `*-sello` | 8 |
| `*-banda` | 7 |
| `seccion` | solo título |

Si te pasas, el texto se recorta en silencio. Para verlo mientras editas, añade la clase
`depurar` al `div.reveal`: marca en rojo toda caja que se desborde.

## Revisar un deck y dejar notas

Levanta el servidor y abre la liga que imprime, con `?revisar` al final de la URL. También se
aceptan `?review`, `?revision` y `?rev`.

```
python3 tools/servir.py NN
```

**Por el servidor, no con doble clic.** Las notas se guardan en
`sesiones/SNN-.../notas.json`, y quien las escribe ahí es el servidor. Sin él se quedan en el
navegador, donde nadie más las ve, y el anotador lo avisa con una etiqueta amarilla en su
barra. Nada se pierde: en cuanto se abre el deck por la liga del servidor, se suben solas.

Aparece una barra abajo a la izquierda con el identificador de la diapositiva actual, y se
habilitan cinco teclas:

| Tecla | Qué hace |
|---|---|
| `A` | Abre una caja de nota para la diapositiva actual. Si antes seleccionaste texto, la nota lo cita. Ctrl+Enter guarda, Escape cancela. |
| `L` | Abre la **lista de notas**, con dos pestañas: las de esta diapositiva y las del deck entero. También la abre el contador de la barra. |
| `G` | Abre el **guion de la lámina en curso** en una ventana aparte, la misma vista con la que se presenta. Ahí se selecciona texto y se anota con `A` igual que en las láminas. `G` o Escape la cierra. |
| `R` | Abre la **rejilla**, el deck entero en miniaturas a pantalla completa, donde las láminas se arrastran con el ratón para cambiarlas de orden. `R` o Escape la cierra. |
| `E` | Junta todas las notas en Markdown, las copia al portapapeles y las muestra. |
| `X` | Abre **lo que cambió** en el deck desde la última vez que lo diste por visto, con el texto de antes y el de ahora, y el botón de darlo por visto. |
| `Z` | **Esconde y muestra** esas marcas, sin olvidarlas. Está pegada a la `X` a propósito, para recordarlas juntas. |
| `Y` | Enciende y apaga la **sincronía del guion con la lámina**. También está como botón en la barra de la ventana del guion. |

`C` cambia el nivel de recorte de la lámina en curso, y está explicada más abajo, con la chapa
que la acompaña.

### El texto citado queda resaltado

Al guardar una nota que cita texto, la frase citada aparece **resaltada en amarillo** sobre la
lámina, y sobre el guion si la nota es del guion. Así se ve de un vistazo qué está anotado y
qué no.

**Un clic en el resaltado abre su nota** para editarla, con Guardar, Cancelar y Eliminar;
Ctrl+Enter guarda, Escape cancela. Mientras se edita, y hasta que se pinche en otro sitio, ese
resaltado se pinta de **naranja**, para que se vea cuál es la nota que está abierta. Si dos
notas citan la misma frase comparten un solo resaltado, con un número volado al lado; al
pincharlo salen las dos.

La marca naranja se suelta al pinchar en cualquier otro punto de la lámina o del guion, al
abrir otra nota, al cambiar de diapositiva, al cerrar el guion y con Escape. Solo puede haber
una nota marcada a la vez.

### La lista de notas

La abre la tecla `L`, y también el contador de la barra. Tiene dos pestañas: **Esta
diapositiva** y **Todo el deck**, esta última agrupada por lámina y en el orden del deck. Cada
nota muestra su ámbito, su cita y su texto, con un botón para editarla y otro para eliminarla.
Es la vía para editar las notas que no citan nada, que no tienen resaltado donde pinchar.

**Pinchar una nota de la lista lleva hasta ella y la deja marcada.** Si la nota es de lámina,
salta a esa diapositiva. Si es del guion, lleva el deck a su lámina, abre la ventana del guion
y baja hasta la frase, dejándola centrada. El botón Editar hace lo mismo y además abre la caja. Las notas de láminas
que ya no existen se listan al final, aparte, y no llevan a ningún lado.

De cada nota se guardan la **cita**, el texto que estaba seleccionado, y **cuál de sus
apariciones** era. El resaltado en sí no se guarda: se vuelve a localizar en cada carga
buscando esa cita dentro del texto de la lámina, y por eso la nota sigue a su frase aunque se
reordenen las viñetas. Guardar la aparición es lo que permite citar una sola palabra que se
repita en la lámina y que se resalte la que era, no la primera.

Si edito la lámina y la frase cambia, la nota no se pierde, pero deja de estar resaltada, y la
lista la marca como *cita sin localizar*. La búsqueda tolera cambios de espaciado y de
mayúsculas, y encuentra la cita aunque cruce etiquetas, por ejemplo un `<strong>` a media
frase.

El resaltado vive solo en el navegador y solo con `?revisar`: no toca el archivo, no entra en
el PDF de decktape, y el `<aside class="notes">` original queda intacto, así que el apuntador
sigue mostrando el guion limpio.

### Lo que cambió desde la última vez, la tecla `X`

Al cerrar una ronda de correcciones, `tools/cambios.py` compara el deck con la foto que guarda
en `sesiones/SNN-.../.antes.html` y escribe en `notas.json` qué cambió. El anotador lo pinta
**donde está**, que es lo que Alberto pidió el 12 de octubre de 2026:

- **En la lámina**, la pieza tocada lleva un filo verde, y pasar el ratón por encima abre un
  globo con **el texto de antes**. No se tacha nada dentro de la viñeta: la lámina tiene que
  seguir viéndose como se va a proyectar, y un tachado la desbordaría. La marca no toca el
  flujo, así que no mueve el texto de sitio.
- **En la ventana del guion** sí se tacha, porque esa ventana es para leer y comparar: el
  párrafo cambiado sale con las palabras nuevas marcadas y las quitadas tachadas.
- **En la rejilla**, las láminas tocadas llevan un filo verde.
- **La barra** cuenta cuántas láminas cambiaron, y la tecla `X` abre la lista entera.

**La tecla `Z` las esconde y las vuelve a mostrar**, sin olvidarlas, y la elección se recuerda
en ese deck. Escondidas no se pinta nada: ni en la lámina, ni en la ventana del guion, ni en la
rejilla. **Lo que sí se queda es la chapa de la barra**, apagada y diciendo "escondidos": si
desapareciera del todo, no habría manera de saber que hay algo esperando a que lo mires. La lista
de la `X` se sigue abriendo a propósito, aunque estén escondidas.

**La foto se toma cuando pulsas "ya lo vi"**, no al empezar cada ronda. Así, si se corrigen tres
rondas seguidas sin que mires, ves todo lo que cambió desde la última vez que lo viste. Ese
botón entra por `PUT /foto/<sesion>` del servidor, porque hay que copiar un archivo y una
pestaña no puede; sin servidor solo borra las marcas y lo avisa.

El cálculo no se hace en el navegador, por la misma razón que las parcelas y las anclas: cuando
el deck llega aquí, MathJax ya se llevó el texto de las expresiones.

### La vista de guion, la de la tecla `G`

**Es la misma vista con la que se da la clase**, la de la tecla `T`: una ventana aparte, una
lámina a la vez, columna estrecha, letra grande, el párrafo en curso resaltado y el resto
atenuado. Las flechas arriba y abajo recorren los párrafos y pasan de lámina al llegar al
final; las de los lados pasan de lámina directamente; un clic pone en curso el párrafo
pinchado. Al cambiar de diapositiva en el deck, la ventana cambia con él.

Hasta el 8 de octubre de 2026 era otra cosa: el deck entero como manuscrito continuo dentro de
la propia página, con la vista previa de cada lámina al lado. Alberto la cambió por esta para
revisar el guion tal como lo va a leer en clase.

Lo que esta ventana añade a la de presentar:

- **Se anota con `A`.** Se selecciona texto y se pulsa `A`: la nota queda con ámbito guion, o
  guion corto si lo seleccionado estaba en su bloque, y la caja para escribirla se abre dentro
  de esta misma ventana, que es donde está el cursor. En el export, las notas sobre el guion
  se marcan con `(guion)` para distinguirlas de las que son sobre la lámina.
- **Los resaltados de las notas ya puestas** se ven sobre el guion y se pinchan para editarlas,
  igual que sobre la lámina, y debajo del guion aparece el texto de cada una.
- **Lee la reescritura pendiente**, si la hay. El apuntador lee siempre el archivo, a
  propósito, para no decir en clase algo que nunca se aplicó al HTML; revisando es al revés.
- **La barra de abajo**, con lo que se puede cambiar de esta lámina: reescribir el guion,
  escribir el guion corto y los tres botones de nivel de recorte. El pie dice cuántas notas
  lleva la lámina, cuánto dura su guion y qué significa el nivel que tiene puesto.

Lo que la de presentar hace y esta no: los relojes, las alarmas, las barras de avance y el
recorte en vivo. Revisando no hay clase que cronometrar.

`+` y `-` cambian el tamaño de letra y `N` el modo oscuro, como en el apuntador, y las dos
preferencias se recuerdan aparte de las suyas. La ventana es siempre emergente: la de imagen
sobre imagen, la que `V` elige en el apuntador, aquí no se ofrece, porque solo hay una y
estorbaría a la de presentar.

El botón **Editar guion** convierte el guion en un área editable. Un renglón en blanco separa
párrafos; Ctrl+Enter guarda y Escape cancela. Lo que se escriba se guarda como **reescritura
pendiente**, junto a las notas, marcada con el banderín "guion reescrito", y la ventana pasa a
mostrar la versión nueva. El botón **Revertir** la descarta y devuelve la del deck.

La reescritura **no toca el deck**: el `<aside class="notes">` del HTML sigue igual, y con él
el apuntador, `guion.md` y el PDF. Solo la vista de revisión muestra la versión nueva, y solo
hasta que se aplique al HTML. Esa es la parte que aplico yo, porque el HTML es la fuente
única. El export con `E` la incluye aparte, bajo `## Guion reescrito`, con el id de cada
lámina y su texto completo, listo para pegármelo. La barra avisa con un contador ámbar cuántos
guiones hay reescritos sin exportar, y el botón **Borrar todas** no los toca: se descartan uno
a uno con Revertir.

**El CSS de la columna no está copiado en el anotador**: lo publica `apuntador.js` en
`window.ApuntadorTema.lecturaCSS`, para que las dos vistas no se separen con el tiempo. Si un
deck no cargara el apuntador, la ventana abre igual, sin estilar la columna.

### El nivel de recorte y el guion corto

Cada lámina puede declarar cuánto cuesta perderla, con `data-recorte` en su `<section>`:

| Marca | Qué significa |
|---|---|
| sin marca | **Núcleo.** No se recorta nunca: o la sesión no cumple su objetivo, o la siguiente se rompe porque la da por vista |
| `data-recorte="1"` | **Se pierde y nadie se entera.** Repite o refuerza algo ya dicho. Se corta sin avisar al grupo y sin deber nada |
| `data-recorte="2"` | **Se pierde, pero hay que decirlo.** El contenido importa y no es hoy, así que al cortarla se anuncia y queda pendiente |

Que una lámina se **abrevie** o se **salte** no lo decide el nivel: lo decide si tiene guion
corto escrito, en un `<aside class="corto">` al lado del guion largo. El guion corto es lo que
se dice de esa lámina cuando la sesión va tarde, en dos o tres frases. Sin él, la única salida
es saltarla entera.

En la vista de revisión, **todas** las láminas llevan una **chapa** abajo a la derecha, encima
del número de lámina, que dice su nivel y si ya tiene guion corto escrito. Las de núcleo van en
gris y las marcadas en dorado y en ámbar. Arriba se encimaría con el logotipo institucional,
que en este tema ocupa esa esquina.

La chapa se ve en la lámina y también en la vista general con Escape, donde se agranda a
propósito, porque ahí la lámina va reducida a la quinta parte. Esa vista es la que deja leer de
un golpe cómo está repartido el deck y qué láminas siguen sin su versión corta. Callan sobre el
guion corto la portada, el cierre y los separadores de bloque, que no lo necesitan.

`C` recorre los tres estados de la lámina en curso, núcleo, 1 y 2, y un clic en la chapa hace
lo mismo. Un aviso recuerda cada vez qué acaba de significar.

En la barra de la ventana del guion están los tres botones de nivel, con la definición del que
está puesto en el pie, y debajo del guion largo el **guion corto**, con su botón **Escribir
guion corto** o **Editar guion corto**. Se escribe con el mismo editor que el largo y se
corrige igual, con Ctrl+Enter para guardar y Escape para cancelar, y **Revertir** para
descartarlo. El bloque dice cuánto dura la versión corta frente a la larga.

El bloque sale en **todas las láminas**, no solo en las marcadas. El núcleo no se pierde
nunca, pero contarlo corto no es perderlo, y esa salida no existe si no está escrita. Donde
falta, el hueco lo dice, así que recorrer el deck con la ventana del guion abierta es también
la manera de ver lo que queda por escribir. Quedan fuera la portada, el cierre y los separadores de bloque, cuyo guion ya son dos
frases, salvo que estén marcados o ya lo traigan. `tools/tiempos.py` lista las que se quedaron
sin versión corta.

Se pueden anotar los dos guiones con `A`, y en el export las notas sobre el corto se marcan
con `(guion corto)` para no confundirlas con las del largo.

Como las reescrituras del guion, **el nivel y el guion corto no tocan el deck**: viajan junto a
las notas, en `notas.json`, hasta que se aplican al HTML. La barra los cuenta aparte, el export
con `E` los saca bajo `## Guion corto` y `## Nivel de recorte`, y en cuanto el HTML los dice
dejan de contar como pendientes.

### La rejilla: cambiar el orden de las láminas

La tecla `R` abre el deck entero en miniaturas, a pantalla completa, y **una lámina se arrastra
con el ratón hasta su sitio**, como en PowerPoint. Mientras se arrastra, la lámina agarrada se
queda donde está, atenuada; una copia sigue al cursor; y **entre las dos láminas donde caería se
dibuja una línea vertical**. La malla no se recoloca hasta que se suelta, así que nada baila
debajo del cursor mientras se decide. Arrimarse al borde de arriba o de abajo desplaza la
rejilla sola.

- **Un clic sin arrastre** lleva a esa lámina y cierra la rejilla.
- **Escape a mitad de un arrastre** lo cancela: la lámina no se había movido. Con nada agarrado,
  Escape cierra la rejilla.
- **`Ctrl+Z` deshace** el último movimiento, y otra vez el anterior, hasta cien pasos. También
  está el botón **Deshacer** de la barra, que lleva la cuenta de cuántos quedan. La pila vive en
  memoria y se pierde al recargar, como los trazos del pincel: lo que importa conservar es el
  orden vigente, no el camino que se siguió hasta él.
- **`Ctrl+Z` a mitad de un arrastre** cancela el arrastre y no hace nada más. Pulsarlo otra vez
  ya deshace el movimiento anterior.
- **Descartar los cambios**, en la barra de arriba, tira el orden, las láminas por escribir y
  las marcadas para borrar de una vez, y también se deshace con `Ctrl+Z`.

### Pedir una lámina nueva y borrar una que sobra

Cada miniatura trae dos botones, que aparecen al pasar el ratón por encima:

- **`+`** inserta detrás de ella una **lámina por escribir**, y abre en el acto la caja donde
  se dice qué debe contener. Eso es texto y nada más: es el encargo que yo leo después para
  escribirla. Abajo del todo hay otro botón para añadirla al final del deck.
- **`×`** marca la lámina para **borrarla**. Si tiene notas de revisión, se avisa de cuántas se
  irán con ella antes de marcarla.

Las dos cosas se ven en el acto: la lámina por escribir aparece en el deck, con su borde
punteado y el encargo dentro, y la marcada para borrar sale de él. En la rejilla, en cambio, la
marcada **no desaparece**: se queda atenuada y tachada, sin número, con el botón `↺` para
devolverla. Es lo que permite arrepentirse sin tener que buscarla.

Una lámina por escribir se pulsa para volver a editar su encargo, se arrastra como cualquier
otra, y su `×` la retira del todo, que para eso todavía no existe en el HTML. `Ctrl+Z` deshace
las tres cosas: insertar, describir y borrar.

### Combinar dos o más láminas en una

Para quitar redundancia y acortar la sesión, se pide que varias láminas se combinen en una
sola. **`Ctrl+clic`** selecciona láminas, contiguas o no, y **`Shift+clic`** marca el tramo
desde la última. Con dos o más marcadas aparece en la barra el botón **Combinar en una**, que
abre una caja para decir con qué criterio combinarlas. **La nota es opcional**: vacía significa
que el criterio lo decide quien escriba la lámina.

Las partes se van a leer en el orden en que están en la rejilla, y la lámina resultante se
queda en el sitio de la primera. Cada una lleva una chapa azul, **combina 1 de 3**, que dice
cuál es cuál; al pulsarla se reabre la nota, y desde ahí se saca una lámina de la combinación o
se deshace entera. Si al sacar una se queda con una sola parte, la combinación se deshace: una
lámina combinada consigo misma no quiere decir nada.

Una lámina no puede estar en dos combinaciones a la vez, y una marcada para borrar no se deja
seleccionar. Al revés también: **marcar para borrar una lámina que está en una combinación la
saca de ella** en el mismo paso, y `Ctrl+Z` devuelve las dos cosas de una vez. Si no, el
encargo quedaría apuntando a una lámina que el HTML va a perder.

**Combinar no borra ni mueve nada.** Las partes se quedan todas en el deck, marcadas, hasta que
la lámina única esté escrita, así que el minutaje sigue contando tres donde va a haber una
hasta ese momento. Al aplicarse, la primera parte queda con `data-combinar` nombrando a las
demás y `data-combinar-nota` con el criterio, y cada una de las otras con `data-combinar-en`.
Nada se pierde: el material entero sigue ahí, que es justo lo que hace falta para combinarlo.

Escribir la lámina combinada es trabajo de contenido, no de un script, y lo hace
`/corregir-sesion` en el mismo pase: decide qué sobrevive, refunde el guion, el guion corto y
los apuntes, borra las sobrantes y quita las marcas. Mientras quede una, `empaquetar.py` se
niega a empaquetar.

Al aplicarse con `tools/reordenar.py`, la borrada desaparece del `index.html` y la nueva entra
como un `<section>` con **`data-pendiente="1"`** y el encargo dentro, en el cuerpo y en el
guion. Mientras esa marca esté, **`tools/empaquetar.py` se niega a empaquetar**, y también en
la variante `--con-guion`, que es la mía: un deck a medias no se empaqueta ni para mí.

`Ctrl+Z` es también la tecla del pincel, y el reparto es este: **con la rejilla abierta la tecla
es de la rejilla**, aunque el pincel esté encendido, porque la rejilla tapa la lámina entera y
debajo no se está dibujando nada; con la rejilla cerrada y el pincel encendido, es del pincel; y
con el foco en una caja de texto, de quien escribe.

**El orden nuevo se ve en el acto, pero el HTML no se toca.** El deck se reordena también, para
poder recorrerlo en el orden que va a tener, y el cambio viaja como pendiente junto a las
notas, en el apartado `orden` de `notas.json`. Es el único que no va por lámina sino por deck:
la lista completa de ids.

Mientras no esté aplicado se dice en tres sitios: la barra de abajo lleva una chapa naranja con
cuántas láminas se movieron, la barra de la rejilla lo dice con letras, y cada lámina movida
sale con el borde naranja y una etiqueta con la posición que tenía.

Movida es la que de verdad hubo que sacar de la fila y volver a meter, no la que se corrió una
casilla porque otra se le puso delante: se calcula con la subsecuencia común más larga contra
el orden del HTML. Por eso subir una lámina al principio marca esa y solo esa.

Al archivo lo lleva `tools/reordenar.py`, que permuta los `<section>` sin tocar su contenido,
deja respaldo del anterior y cierra el pendiente. Si entre medias se insertaron o se borraron
láminas, el orden pendiente se concilia en vez de tirarse: las que ya no existen se caen y las
que no menciona se quedan junto a su vecina.

### Lo ya corregido se quita solo

Cuando aplico las correcciones, cierro las notas atendidas con `tools/notas.py --resuelto`. Si
el deck está abierto, sus resaltados desaparecen en unos segundos, sin recargar: el anotador
vigila el archivo y se pone al día.

Para el caso de haber revisado **sin servidor**, hay una vía de respaldo. Junto al deck se deja
un `resueltas.js`:

```js
window.RV_RESUELTAS = {
  sello: "2026-09-02T18:40",
  notas: [{ id: "evaluacion", texto: "subir tareas a 60 y proyecto a 40" }],
  guiones: ["formulacion-de-problemas"],
  cortos: ["alphazero"],
  recortes: ["alphazero"],
  orden: true
};
```

El anotador lo carga al arrancar y se lleva esas notas, así que al recargar quedan solo las
pendientes, con su resaltado, y un aviso verde dice cuántas se fueron. Lo escribe el skill
`/corregir-sesion`; no hay que crearlo a mano.

Solo hace falta en ese caso. Con servidor, las notas se cierran en el archivo y no hay
`resueltas.js` que valga.

`revisar.js` lo inyecta él mismo, relativo al deck, así que no hace falta añadir ninguna
etiqueta al HTML. Va por `<script>` y no por `fetch` porque los decks se abren con doble clic,
y Chrome no deja que una página `file://` lea otro archivo con `fetch`, pero sí cargar un
script suyo. Lo normal es que el archivo no exista, y entonces no pasa nada.

El `sello` marca la tanda y se guarda en `localStorage` al consumirla, de manera que el mismo
archivo no vuelve a borrar en cargas posteriores: una nota nueva que repita el texto sobre la
misma lámina es otra nota, no la que ya se corrigió.

Una reescritura del guion deja de contar como pendiente en cuanto el deck ya la dice, esté o no
en `resueltas.js`. Por eso ya no hace falta darle a **Revertir** después de que yo la aplique.

Sin `?revisar` no se carga nada de esto, así que al presentar no hay riesgo de abrir una caja
de notas por error.

Cada `<section>` debe llevar un `id` estable. Se generan con:

```
python3 tools/ids.py sesiones/SNN-.../index.html
```

El ciclo completo, resaltado incluido, tiene prueba de regresión en Chrome headless:

```
python3 tools/prueba-revisar.py [sesiones/SNN-.../index.html]
```

Siembra notas de mentira en un perfil de Chrome desechable, así que no toca las notas reales.
Cubre el camino sin servidor. El camino normal, con las notas en disco, lo cubre la otra:

```
python3 tools/prueba-notas.py [sesiones/SNN-.../index.html]
```

Y la rejilla que cambia el orden, con el script que lo lleva al HTML, la cubre la tercera:

```
python3 tools/prueba-orden.py [sesiones/SNN-.../index.html]
```

Hay que correr las tres después de tocar `revisar.js`.

## Apuntador para presentar

Tecla `T` sobre el deck. Abre una ventana con el guion de la diapositiva actual en columna
estrecha, unos 40 caracteres por línea, y tipografía grande.

La columna estrecha es el punto: lo que delata a quien lee no es mirar hacia abajo, sino el
barrido horizontal del ojo en líneas largas. Con renglones cortos la vista abarca la línea
completa de un golpe y el movimiento es casi imperceptible en cámara.

Las acotaciones entre corchetes se muestran atenuadas y en cursiva, porque no se leen en voz
alta.

**El apuntador lee siempre el guion del archivo**, nunca una reescritura guardada en el
navegador. Es deliberado: lo que se lee en clase tiene que ser exactamente lo que está en el
HTML, para que no se quede una versión viviendo solo en el navegador y se acabe leyendo en voz
alta algo que nunca se aplicó al deck.

| Tecla dentro del apuntador | Efecto |
|---|---|
| Arriba y abajo | Mueven el párrafo en curso |
| Izquierda y derecha | Cambian de diapositiva en el deck |
| `+` y `-` | Tamaño de letra, se recuerda entre sesiones |
| `N` | Invierte a fondo oscuro |
| `R` | Reinicia los cronómetros |
| `H` | Cambia el horario de la clase, por defecto 08:00 a 10:00 |
| `A` | Abre y cierra el panel de alarmas |
| `Esc` | Cierra el aviso de una alarma, o el panel si está abierto |
| `V` | Alterna entre ventana flotante y emergente, y cierra la actual |
| `Y` | Enciende y apaga la **sincronía del guion con la lámina**, y se recuerda |

### La sincronía del guion con la lámina, la tecla `Y`

Mientras se lee un párrafo del guion, **la lámina resalta la pieza de la que ese párrafo
habla**: la viñeta, la línea en llano, la fórmula, el dibujo o el video. La pieza en curso
queda a plena opacidad y marcada, y el resto de la lámina se atenúa. **El texto lleva un fondo
del mismo rojo muy diluido**, y si es viñeta su propio punto pasa a ese rojo; **el dibujo lleva
un recuadro de 5 px en `#E01B3D`**, el mismo rojo y el mismo grosor de los recuadros que van
dibujados dentro de los diagramas, para que el grupo lea las dos cosas como la misma señal.

Las otras dos formas se probaron y se descartaron el 12 de octubre de 2026, con captura: la
**barra al costado** quedaba pegada al círculo de la viñeta y se leía como un segundo adorno
peleándose con él, y el **recuadro alrededor del texto** no cabe, porque entre dos viñetas hay
3 px medidos y dos viñetas contiguas resaltadas juntaban sus recuadros hasta parecer una tabla.
El fondo no choca con nada, no mueve el texto, y cuando hay dos viñetas seguidas se funden
solas. Alberto la pidió el 12 de octubre de 2026 con
dos objetivos: que el grupo asocie lo que oye con un elemento de la lámina, y que él vea a qué
elemento corresponde lo que está diciendo.

- **Se enciende con `Y`**, desde el deck, desde el apuntador o desde la ventana del guion, y la
  elección se recuerda entre sesiones. La ventana del guion trae además su botón en la barra.
- **Apagada, el deck se ve exactamente igual** que si esto no existiera: toda la pinta cuelga de
  la clase `sinc` en el `<html>`, que solo se pone encendida y con la lámina anclada.
- **Una lámina sin anclas no se toca**, ni siquiera encendida. Nada se atenúa, para que no
  parezca que falla algo.
- **Lo que se resalta no se adivina en el navegador.** Lo escribe `tools/anclas.py` en el HTML:
  `data-pieza` en cada elemento resaltable del cuerpo y `data-sinc` en cada párrafo del guion.
  Es por lo mismo que las parcelas: MathJax se lleva el texto de las expresiones al componerlas.
  Un párrafo cuyo mejor candidato no despega del segundo se queda sin ancla, y entonces el
  resaltado anterior se queda puesto, que es lo que hace falta con las acotaciones de escena.
- **Un guion reescrito y todavía sin aplicar al HTML no lleva anclas**, porque las escribe la
  herramienta sobre el archivo. Al aplicar la reescritura y volver a correr `anclas.py`, vuelven.
- **Al paquete del grupo no llega**, porque ahí no hay guion ni apuntador.

El motor vive en `apuntador.js`, publicado en `window.ApuntadorSync`, y `revisar.js` lo usa a
través de su función `sinc()`. Está ahí y no en un archivo propio porque **un archivo nuevo del
tema no se propaga** a los 30 decks sin editar las 30 páginas. Su prueba es
`tools/prueba-sincronia.py`, que mide la opacidad en Chrome headless, y la de la herramienta es
`tools/prueba-anclas.py`.

### Las acotaciones de escena, en la franja del costado

Lo que va entre corchetes en el guion **no se pinta en la columna de lectura**: sale a una franja
al costado derecho, alineado con su párrafo y rotulado "en escena". Alberto lo pidió el 12 de
octubre de 2026, leyendo en vivo: una acotación delante de la frase obliga a descifrarla y
saltarla mientras se habla.

- **Una acotación que es su propio párrafo deja de ser una parada.** Las flechas no se detienen
  en ella y su texto se pega a la acotación del párrafo siguiente.
- **En el HTML no cambia nada**: se siguen escribiendo entre corchetes y donde toca.
- **La franja ocupa 138 px**, y por eso la ventana nace en 720 y no en 560. Por debajo de 640 se
  repliega y la acotación pasa a verse debajo de su párrafo. Quien tenga un tamaño guardado lo
  conserva, así que hay que ensanchar la ventana una vez.
- Lo hace `alMargen()`, publicada en `window.ApuntadorTema` y usada también por la ventana de
  revisión, para que las dos vistas no se separen.

### El párrafo en curso

El párrafo que se está leyendo va a plena opacidad, con una barra de acento a su izquierda, y
el resto atenuado. **A su izquierda, centrada a su altura**, una marca en gris dice en qué
párrafo se va sobre el total de la lámina, `4/8`, y debajo ese mismo avance en porciento. Se
desplaza con el párrafo, así que el dato está siempre a la altura de la mirada, sin bajar al
pie. Se avanza con las flechas arriba y abajo, o pinchando cualquier párrafo con
el ratón. La ventana se desplaza sola para dejarlo pegado al margen superior, lo más cerca posible del
lente; al pinchar con el ratón no se desplaza, porque ya se está mirando ahí.

Abajo en el último párrafo pasa a la lámina siguiente. Arriba en el primero vuelve a la
anterior y se coloca en su último párrafo. Al cambiar de lámina, el cursor arranca por el
primer párrafo.

Las acotaciones entre corchetes también pueden ser el párrafo en curso, porque se leen con la
vista aunque no en voz alta, pero cuentan cero minutos.

### Las dos barras de avance

Encima de los relojes van dos barras finas:

| Barra | Qué mide |
|---|---|
| **lámina** | El párrafo en curso sobre el total de la lámina: en el quinto de ocho, cinco octavos. Se pone ámbar si la lámina se pasa de su tiempo estimado |
| **total** | Cuánto material del deck queda recorrido, pesado por la estimación de cada lámina, no por el número de diapositivas |

La de la lámina va por número de párrafo, no por peso del texto, que es como se recorre de
verdad. La del deck sí va pesada, porque una lámina de treinta segundos y otra de seis minutos
no son lo mismo, y las dos se calculan sobre la estimación sin corregir por el ritmo: miden
material recorrido, no tiempo consumido, que de eso ya se encargan los relojes.

El pie lleva el título de la lámina y seis relojes, en cifras grandes de ancho fijo para
leerlos de reojo sin perder el renglón. Van en una **rejilla de columnas iguales**, centrada
bajo la columna de texto: los seis en fila si la ventana da de sí, tres y tres si no, siempre a
la misma distancia entre ellos y alineados en las mismas columnas.

Van en tres grupos, separados por un filete fino que se dibuja dentro del hueco, sin ocupar
columna, para que los seis queden equidistantes:

| Grupo | Reloj | Qué mide |
|---|---|---|
| Reloj de pared | **hora** | La del sistema, con segundos |
| | **sesión** | Desde que se abrió el apuntador. `R` lo pone a cero, para abrirlo antes de empezar sin falsear la cuenta |
| | **clase** | Lo que falta para la hora de salida. Con signo menos si ya pasó |
| Lámina | **lámina** | Tiempo en la diapositiva actual, vuelve a cero en cada cambio |
| Ritmo | **guion** | Minutos que le quedan al guion, desde el párrafo en curso hasta el final del deck |
| | **holgura** | La resta de clase menos guion, con el veredicto debajo |

Si la lámina declara duración con `data-min`, la misma que lee `tools/tiempos.py`, el reloj de
lámina se enciende en el color de acento al pasarse de esa cuenta. Las que no la declaran no
avisan de nada.

### Cómo se calcula la holgura

`holgura = lo que queda de clase menos lo que queda de guion`. Positiva, sobra tiempo;
negativa, se va tarde. El veredicto que aparece debajo es *holgado* por encima de tres
minutos, *al día* entre más y menos tres, **apura** en ámbar por debajo de menos tres, y
**recorta** en rojo por debajo de menos diez.

Lo que queda de guion se estima como en `tools/tiempos.py`, pero **al párrafo**: cuenta desde
el párrafo en curso, no desde el principio de la lámina, así que baja según se avanza dentro
de una misma diapositiva. Vale `data-min` donde está declarado, y palabras del guion hablado,
sin las acotaciones entre corchetes, entre un ritmo de lectura donde no. Al párrafo en curso
se le descuenta el tiempo que ya se lleva en él, con suelo en cero, de modo que quedarse
parado no congela la holgura: el reloj de clase sigue bajando.

Ese ritmo no es una constante. Se mide durante la propia sesión, dividiendo el tiempo real que
se lleva en los párrafos ya leídos entre lo que costaría leerlos de corrido a 135 palabras por
minuto. Así recoge lo que uno se detiene a explicar de más, que es de donde sale el
sobrecosto, y midiendo por párrafo el factor converge en los primeros minutos en vez de tardar
tres o cuatro láminas. Las acotaciones y los bloques con `data-min` quedan fuera de la medida,
porque su duración no depende de lo que se hable. El factor medido se guarda entre sesiones en
`apuntador:ritmo`, así que la clase siguiente arranca ya calibrada; mientras no haya medida
propia se usa 1.3, que es el sobrecosto de referencia de `tiempos.py`.

El horario por defecto es 08:00 a 10:00, el del curso. `H` lo cambia y se recuerda en el
navegador.

### Recorte en vivo

Los relojes dicen que se va tarde; el recorte dice qué hacer al respecto. Se enciende con `C`,
que abre un panel dentro de la misma ventana del apuntador, con tres modos:

| Modo | Qué entra en el plan |
|---|---|
| **Apagado** | Nada. Es como arranca siempre |
| **Solo nivel 1** | Lo que se pierde sin que nadie se entere |
| **Niveles 1 y 2** | También lo que hay que anunciar al grupo |

El nivel 2 no entra solo aunque haga falta: cortarlo obliga a decir en clase que se retoma
después, y esa decisión es de quien da la clase, no del programa.

Con el modo encendido, el plan se arma solo con lo que queda por dar, en este orden, que es el
del coste de perder cada cosa: **abreviar las de nivel 1, saltar las de nivel 1, abreviar las
de nivel 2 y saltar las de nivel 2.** Dentro de cada grupo entra primero la que más tiempo
devuelve, para tocar el menor número de láminas. Se recorta solo lo que hace falta para cerrar
el retraso, no todo lo marcado, y se devuelve lo recortado en cuanto sobra tiempo, con dos
minutos de margen para que el plan no baile de un segundo a otro.

**El plan cuenta ya en los relojes.** Lo que falta de guion y la holgura se calculan con el
plan puesto, así que dicen cómo va la clase de verdad, no cómo iría sin recortar. El panel
enseña las dos cifras, la de con recorte y la de sin él.

El panel tapa la ventana entera, pero **el pie con los seis relojes se queda encima**, y el
panel se aparta para dejarle sitio. Así se ve la holgura moverse al encender cada modo, que es
justo lo que se está decidiendo. Lo mismo vale para el panel de alarmas.

El panel dice siempre **por qué** la cifra se mueve o no: apagado, cuánto devolvería encenderlo;
encendido sin nada marcado por delante, que no hay nada que recortar; y cuando el plan ya lo
recortó todo y sigue sin alcanzar, que no queda nada más. Y si la hora de salida ya pasó hace
rato, en lugar de un retraso de horas dice que la clase terminó y que eso es un ensayo, porque
fuera del horario la holgura no significa nada.

Cada lámina se puede **fijar a mano** desde el panel, a entera, abreviada o fuera, y entonces
el plan la respeta y no vuelve a tocarla. El botón *auto* la devuelve al plan. El modo y lo
fijado se recuerdan por deck, no globalmente: son la decisión de esa clase.

La **primera fila es siempre la lámina que se está dando**, esté marcada o no. Es la salida de
emergencia: una lámina de núcleo no entra nunca en el plan, pero si el día se torció de verdad
se puede contar corta desde ahí, siempre que tenga guion corto escrito. Las demás filas son
solo las marcadas, que son las que el plan puede tocar.

Al llegar a una lámina recortada, el apuntador lo dice con un banderín sobre el guion. Si va
abreviada, **lee el guion corto** en lugar del largo. Si va fuera, avisa de que se salta, y la
flecha abajo pasa directamente a la siguiente en vez de recorrer sus párrafos; en las de nivel
2 recuerda además que hay que decirle al grupo que se retoma más adelante.

El apuntador lee siempre **lo que dice el HTML**, igual que con el guion: los niveles y los
guiones cortos que sigan pendientes en la vista de revisión no cuentan hasta que se aplican al
deck.

### Alarmas a hora de reloj

Los relojes dicen cuánto falta; las alarmas avisan sin que haya que mirarlos. Sirven para lo
que cae a una hora fija y no depende del guion: el receso, el aviso de que quedan veinte
minutos, la hora de cerrar y despedir.

Se editan con `A`, que abre un panel dentro de la misma ventana del apuntador, no un diálogo,
porque las ventanas flotantes no abren diálogos. Se pueden definir todas las que hagan falta, y
cada una lleva tres cosas:

| Campo | Qué es |
|---|---|
| **Hora** | La hora de reloj a la que se dispara, del propio día. No es un tiempo relativo al guion ni a la lámina |
| **Texto** | Lo que se muestra al dispararse. Si se deja vacío, el aviso dice *Alarma* |
| **Sonido** | Opcional: sin sonido, campana, timbre, doble pitido o suave. El botón **oír** lo prueba antes de la clase |

Cada cambio en el panel se guarda solo, y **`quitar` borra esa alarma**.

### Dónde viven las alarmas

**En disco, en `admin/alarmas.json`**, servido por `tools/servir.py` en `GET` y `PUT` de
`/alarmas`. Es el mismo trato que las notas de revisión: el archivo manda y el navegador es la
red de seguridad. Así sobreviven a un borrado de datos de Chrome, viajan con el proyecto y se
pueden leer y editar con cualquier editor.

```json
{"alarmas": [{"h": "08:55", "t": "Mitad de la sesión", "s": "campana"}]}
```

No llevan el nombre de ninguna sesión: son globales, como el horario, porque el receso cae a la
misma hora las treinta clases. Se definen una vez y valen para todo el cuatrimestre.

El panel dice siempre dónde acaban. **Si el deck se abrió con doble clic**, o el servidor está
apagado, no hay disco al que escribir: las alarmas siguen funcionando pero solo en ese
navegador, guardadas en `apuntador:alarmas`, y el panel lo avisa en ámbar. En cuanto se abre por
la liga de `servir.py`, si el archivo está vacío, las que se hubieran capturado sin servidor se
suben solas en vez de perderse.

Aquí no hay contador de versión, a diferencia de `notas.json`, y es deliberado: este archivo lo
escriben una sola persona y un solo panel, y es una lista corta. **Manda el último que
escribe.** El apuntador relee el archivo al abrirse y cada vez que se abre el panel, así que una
edición a mano se recoge sola con solo volver a abrir el panel. Lo que el servidor no acepta es
basura: filtra todo lo que no sea una hora de reloj de verdad, recorta los textos largos, deja
en *sin sonido* cualquier sonido que no exista, y devuelve la lista ya ordenada.

Al dispararse, el aviso aparece **dentro del pie, que crece hacia arriba**, sobre las barras y
los relojes, en el color de acento y con el texto en cifra grande. No se pone encima del
párrafo que se está leyendo: interrumpe sin tapar lo que se dice en voz alta. A la vez, el
borde de la ventana **destella tres veces**, que es lo que se ve por el rabillo del ojo sin
apartar la mirada del lente. Se cierra con un clic encima, o con `Esc`, y si no se cierra se va
solo a los cuarenta y cinco segundos.

En el pie, junto al número de lámina, aparece siempre **cuál es la siguiente alarma y cuánto
falta**, en minutos mientras queda más de diez y en minutos y segundos a partir de ahí. Los dos
últimos minutos van en ámbar.

El sonido lo sintetiza el navegador con osciladores, así que **no hay archivo que vendorizar y
suena igual sin conexión**. Sale por las bocinas del equipo: si se comparte pantalla con audio,
el grupo lo oye, y entonces conviene dejar las alarmas en *sin sonido* y quedarse con el aviso
en pantalla. Para que suene, el navegador exige un gesto del usuario de por medio: lo da la
propia tecla `T` que abre el apuntador, así que basta con abrirlo como siempre.

Una alarma solo suena **una vez al día**, y solo si su hora cayó dentro de un margen de minuto
y medio. Por eso abrir el apuntador a media clase no dispara de golpe todas las alarmas ya
pasadas de la mañana.

Hay **dos clases de ventana** y la tecla `V` alterna entre ellas, recordando la elección. Al
cambiar, la ventana se cierra y se vuelve a abrir con `T`, porque pedir la flotante exige un
gesto del usuario en la ventana del deck.

| | Emergente, la de fábrica | Flotante |
|---|---|---|
| Tamaño y posición | A gusto, hasta maximizarla, **y se recuerdan** | Los decide el navegador, no se maximiza |
| Barra de direcciones | Lleva el `about:blank`, y Chrome no deja quitarla | No lleva |
| Encima de las demás ventanas | No | Sí, Zoom incluido |

La emergente es la de fábrica: `T` la abre mientras no se pida otra cosa con `V`, que guarda
la elección en `apuntador:flotante`. Se abre la primera vez de 560 por 620, centrada y pegada
al borde superior. A partir de ahí se ajusta a mano una vez y **el tamaño y el sitio se
guardan** en `apuntador:caja`, así que vuelve a abrirse igual el resto del cuatrimestre.

La flotante es una ventana de imagen sobre imagen (Document Picture-in-Picture). **No se puede
maximizar**: tiene su propio tamaño máximo y el navegador dibuja su barra de título con el
compositor de vídeo, así que al forzarla se ve rota. Si el navegador no la ofrece, se cae solo
a la emergente.

Agrandar la ventana tiene un costo que conviene tener presente: una ventana grande esparce el
texto por la pantalla y devuelve el movimiento ocular que toda esta geometría trata de evitar.
Para ver más renglones sin ensanchar nada está la tecla menos, que baja el tamaño de letra
dejando la columna igual de estrecha.

Con la flotante, la tecla `H` pregunta el horario en la ventana del deck, porque las ventanas
de imagen sobre imagen no abren diálogos.

Lo que importa de la colocación es ponerla debajo del lente, que es donde
menos se desvía la mirada si la webcam está encima del monitor. **La desviación que se nota no
es la vertical sino la horizontal**: con la ventana en una esquina, a 60 cm de un monitor de 24
pulgadas, la mirada se va unos 17 grados de lado, más del doble que los 8 grados que costaba
mirar hacia abajo. Si tu cámara no está centrada sobre esa pantalla, mueve la ventana a mano
hasta ponerla debajo del lente.

Por lo mismo el renglón de lectura va **pegado al margen superior**, con doce píxeles de aire,
y el título de la lámina y los seis relojes **al pie**: el texto se lee todo el tiempo y lo
demás se mira de vez en cuando, así que la mirada que baja es la ocasional, no la continua.
Debajo del párrafo en curso queda todo lo que falta por decir, que es lo que evita trabarse; lo
que se pierde de vista es lo ya dicho, que importa mucho menos.

Lo que queda de recorrido vertical es el que se hace dentro de un párrafo largo, y eso no se
arregla con la ventana sino escribiendo el guion en párrafos de dos o tres renglones.

## Pincel para dibujar sobre la lámina

La tecla `D` sobre el deck enciende el pincel: un lienzo encima de la lámina y una barra de
pinceles al pie. `D` otra vez, Escape o el botón **Salir** lo apagan, y `Ctrl+Z` deshace el
último trazo sin soltar el lápiz. Funciona dando la clase,
sin `?revisar`, que es para lo que está, y lo implementa `pincel.js`.

Está pensado para la tableta gráfica. De ahí las tres cosas que lo distinguen de dibujar con el
ratón:

- **El ancho del trazo sale de la presión del lápiz**, con el grosor elegido como techo. Un
  lápiz que no reporte presión da 0.5 constante, así que el trazo sale de ancho constante sin
  necesidad de detectar nada, y el ratón dibuja con el grosor elegido, sin modular.
- **La punta de borrar borra.** Se reconoce por `pointerType` de borrador o por el botón 5 del
  lápiz, que es como lo reporta Chrome.
- **La mano apoyada no pinta**: lo que llega como `touch` se ignora, así que el deslizamiento
  con el dedo sigue pasando de lámina mientras se dibuja.

La barra lleva los cinco colores de la plantilla, guinda, verde, dorado, negro y blanco, tres
grosores, el borrador, **Deshacer**, **Limpiar** y **Salir**. Elegir color suelta el borrador,
Deshacer quita el último trazo y Limpiar vacía la lámina en curso, no el deck.

`Ctrl+Z` hace lo mismo que Deshacer. Las dos teclas del pincel, esa y Escape, se atienden en
fase de captura y solo mientras está encendido: apagado, `Ctrl+Z` no toca nada. Con el lápiz
apoyado, deshacer cierra el trazo en curso y lo quita, así que no se queda ninguno abierto.
`Ctrl+Shift+Z` y `Ctrl+Alt+Z` no hacen nada: no hay rehacer que ofrecer.

**Con el foco en una caja de texto, las dos teclas son de quien escribe.** El anotador abre un
`textarea` por nota y otro para reescribir el guion, y el apuntador tiene campos para sus
alarmas: ahí `Ctrl+Z` deshace lo escrito y Escape cierra la caja, aunque el pincel siga
encendido. Sin esa guarda, el pincel se quedaba con la tecla y borraba un trazo de más.

### Los trazos van anclados a la lámina

Reveal escala la lámina de 1280x720 con un `transform` sobre `.slides`, así que el lienzo va
**dentro de `.slides`** y hereda esa escala. Los trazos se guardan en coordenadas de lámina, de
0 a 1280 y de 0 a 720, y se redibujan cuando la escala cambia. Por eso la tinta sigue donde se
dejó al redimensionar la ventana, al entrar en pantalla completa y al compartir pantalla en
Zoom, que es donde se notaría el desajuste. El mapa de píxeles del lienzo se ajusta a lo que
ocupa en pantalla, para que el trazo no salga pixelado en el proyector.

Ojo con `.reveal .slides`, que trae `pointer-events: none` de fábrica: el lienzo declara
`pointer-events: auto` mientras el pincel está encendido, y vuelve a `none` al apagarse, para
no estorbar al anotador ni a los enlaces de la lámina.

### Los trazos no se guardan

Viven en memoria, en un `Map` indexado por el elemento de cada lámina, no por su `id`, porque
reveal le quita el `id` a la lámina visible. Cada lámina guarda los suyos y los recupera al
volver a ella, pero **al recargar la página se pierden**, y eso es a propósito: el dibujo es de
la clase que se está dando. No hay nada en `localStorage` ni en disco.

En la vista general de reveal el pincel se apaga y el lienzo se esconde: ahí las láminas se
escalan y se mueven, y el lienzo no las seguiría.

Nada de esto viaja al paquete del grupo, y `tools/prueba-pincel.py` es su prueba de regresión:
mide los píxeles del lienzo, no el estado interno, así que si el trazo no se ve, falla.

## Lector de estudio, para entender el tema con la lámina delante

`estudio.js`, **tecla I**. Alberto lo pidió el 1 de octubre de 2026: es muy visual, para
entender el tema recurre a las diapositivas, y cuando algo no le quedaba claro en la lámina la
única salida era el guion de orador, que está escrito para decirse en voz alta y no para
explicarle el tema a quien lo lee.

Enseña dos bloques de la lámina en curso, rotulados, porque no tienen el mismo destinatario:

| bloque | qué lleva | rótulo en el panel |
|---|---|---|
| `<aside class="didactica">` | qué pasa en la lámina, el enlace con lo que se ve, y cómo explicarlo | Para entenderlo y explicarlo, solo tú |
| `<aside class="apuntes">` | el apunte que recibe el grupo | Apunte, esto lo recibe el grupo |

Las notas didácticas las escribe el skill `/didactica-sesion`.

**Dos formas de leerlo, a elección, y la elección se recuerda** en `localStorage`, bajo
`estudio:modo`, como hace el apuntador con su tecla `V`:

- **Panel al costado.** La lámina se encoge para dejarle sitio en vez de taparse, que es lo
  que permite leer el texto y mirar el dibujo a la vez. Es el de fábrica.
- **Ventana aparte**, para estudiar con dos monitores. Recuerda su tamaño y su posición en
  `estudio:caja`. Es una ventana emergente y **no** de imagen sobre imagen, al contrario que
  el apuntador: la de imagen sobre imagen se queda encima de todo y no se puede maximizar,
  que es lo que hace falta para presentar, no para estudiar sentado.

El botón `Toda la sesión` pone todas las notas de corrido, con un encabezado por lámina que
lleva a su diapositiva. `Escape` cierra.

## El reproductor de las animaciones, y los tramos

Una lámina con animación la declara con `data-video`. Desde el **6 de octubre de 2026** puede
partirla en **tramos**, y cada tramo es un fragmento de reveal:

```html
<section data-video="videos/mundos.mp4" data-min="4">
  <h2>Cómo se reparte la creencia</h2>
  <span class="tramo"          data-start="0"     data-end="20.55">Los cuatro mundos</span>
  <span class="tramo fragment" data-start="20.55" data-end="32.25">La unidad se reparte</span>
  <span class="tramo fragment" data-start="32.25" data-end="42.9">La suma de los mundos</span>
</section>
```

**El primero no lleva `fragment`** y arranca solo al llegar a la lámina; los demás sí, así que
la barra espaciadora los va sacando y solo pasa de lámina cuando se acaban. El retroceso es el
de reveal, con la flecha izquierda. No hay tecla de avance propia, y eso es deliberado: las
libres se habían acabado entre el anotador, el apuntador, el pincel y el lector de estudio.

**Al acabar un tramo el video se congela** en su último cuadro. Lo decidió Alberto, porque el
bucle de la versión anterior competía con lo que él estaba diciendo. Para volver a verlo están
el botón de repetir y la tecla **V**, que es la única que esta pieza añade.

**Debajo del video hay una barra de controles**, que es lo que Alberto pidió el 6 de octubre
de 2026 cuando la primera versión salió solo con teclas. Lleva **seis botones**: tramo
anterior, pausa o reproduce, tramo siguiente, repetir este tramo, bucle de este tramo y
pantalla completa. Y una pista de progreso sobre el video entero con el **número de cada tramo**
dentro de su banda, el tramo en curso marcado en guinda, el tiempo transcurrido y el total.
Los números son lo que ata el guion, que habla de "el tramo tres", con lo que se ve en la
pista, sin tener que contar bandas.

**Parado al final de un tramo, el botón de reproducir pasa al siguiente**, no reinicia el que
acaba: para volver a verlo está el botón de repetir. En el último tramo no hay siguiente, así
que ahí sí repite, para que darle a reproducir no se quede sin hacer nada.

**El nombre del tramo no se escribe en la barra**: la alargaba hasta salirse de la lámina. Va
en el `title` de la propia barra, al pasar el ratón.

**Pantalla completa es de una caja que se crea al pedirla**, con el video y la barra dentro,
así que los controles siguen estando. Y se deshace al salir, a propósito: una caja permanente
con `z-index` crea su propio contexto de apilado y la mezcla multiplicativa del video deja de
alcanzar el fondo de la lámina, que se pintaba como un rectángulo blanco opaco.

Se puede **pinchar en la pista** para saltar, y el salto arrastra también el fragmento de
reveal, para que el tramo que suena y el que la lámina cree que va sean el mismo. Los botones
de tramo anterior y siguiente **no cambian de lámina**: en el primero y en el último se apagan,
para que un clic de más en clase no salte a otra diapositiva.

**El bucle es un botón, no el comportamiento por omisión.** Sin él, al acabar un tramo el video
se congela.

**Todo esto viaja al paquete del grupo**, para que al repasar avancen a su ritmo. El rótulo del
tramo no se proyecta por su cuenta: lo esconde una regla del tema y lo enseña la barra.

**Dónde va la barra, que costó dos capturas.** Ni centrada ni a todo lo ancho: el sello de la
esquina de abajo a la izquierda llega hasta el 17% y se dibujaba por delante de los botones.
Empieza en el 20% y acaba en el 97%. Y el video baja del 66% al 59% de alto para dejarle sitio:
superpuesta tapaba el pie de la propia animación.

**Los límites de los tramos se sacan del render, no de sumar los `run_time` a mano**:
imprimiendo `self.renderer.time` en cada frontera del guion de Manim.

**Y la lámina declara `data-min`**, porque una lámina de seis tramos ya no cuesta lo que dicen
sus palabras: cuesta el video más lo que se habla sobre cada tramo.

Si una lámina no declara tramos y trae `data-start` y `data-end` en el propio `<section>`, se
comporta como antes: repite ese fragmento en bucle. Las sesiones 2, 6, 7 y 8 llevan **su copia
embebida** de la versión vieja del reproductor, así que no se enteran de los tramos; migrarlas
está anotado como pendiente.

Sus pruebas son `tools/prueba-tramos.py`, que mide el avance, la congelación, la tira y la
tecla V, y corre igual sobre el deck y sobre el paquete; y `tools/prueba-glosas.py`, que
comprueba con `ffprobe` que los tramos encajen sin huecos y que el último no pase de la
duración real del archivo.

**Dos fallos del botón de pausa, los dos los vio Alberto y los dos están en la prueba:**

- **`pintar()` no puede tocar el DOM en cada cuadro.** La primera versión rehacía el icono
  sesenta veces por segundo, así que entre que se apretaba el ratón y se soltaba el nodo ya era
  otro y el clic se perdía: el botón "no funcionaba". Ahora cada pieza se repinta solo si su
  valor cambió. **Y la prueba tiene que mandar el clic al nodo más profundo, capturado antes de
  forzar un repintado**: mandándolo al `<button>` pasaba con el botón roto.
- **`insistir()` no puede resucitar una pausa del usuario.** Reintentaba colocar y reproducir
  durante dos segundos después de montar, así que una pausa dada en ese rato se deshacía sola.

**El corte al final del tramo lo vigilan tres cosas, y hacen falta las tres**: el aviso
`timeupdate`, que llega cada doscientos y pico milisegundos; un repaso cuadro a cuadro; y un
temporizador puesto al tiempo que falta, que es el que salva si la pestaña se ralentiza.

**Una trampa que costó una vuelta:** en Chrome headless el video **no se decodifica**, se
queda en `readyState` 1 y el seek no termina nunca. Así que la congelación no se puede probar
dejándolo correr: hay que sombrear `currentTime` con una propiedad propia y empujar un
`timeupdate`, que es lo que ejercita el vigilante de verdad.

**Tres trampas, las tres ya pagadas:**

- **El bloque necesita su propia regla `display:none`** en `tema-centrogeo.css`. Sin ella el
  texto con el que Alberto estudia se proyecta en clase. Es el mismo fallo de las dos mitades
  que costó el CSS del reproductor.
- **La ventana se escribe por el DOM y no con `document.write`.** Con `write`, la única forma
  de probarla es un iframe, y un iframe recién insertado deja a Chrome headless esperando una
  navegación que no acaba.
- **`importNode` copia el nodo y no lo saca del origen.** Un `while (caja.firstChild)` sobre
  el resultado no termina nunca y cuelga la pestaña. Pasó, y lo cazó la prueba.

Nada de esto viaja al paquete: `empaquetar.py` quita el bloque y el script, y su auditoría se
niega a entregar el archivo si alguno sobrevive. `tools/prueba-estudio.py` es su prueba de
regresión.

## El paquete para estudiantes

```
python3 tools/empaquetar.py sesiones/SNN-tema/index.html
```

Produce `salidas/SNN-tema.html`, un archivo único con reveal.js, el tema, las tipografías,
los fondos, las imágenes y los videos dentro. Se abre con doble clic, sin servidor y sin
conexión, y conserva el video y la navegación, con los controles encendidos.

### Qué no viaja, y quién lo comprueba

Sale **sin nada de lo que solo mira quien da la clase**: sin guion de orador, sin guion corto,
sin las marcas `data-recorte`, sin el anotador, sin el apuntador, sin el pincel y sin los
comentarios del deck ni del tema, que cuentan su cocina. Al terminar, el empaquetador **audita el archivo ya armado**
y, si algo de eso sobrevivió, para en vez de entregar un paquete a medias. Esa red es lo que
permite subirlo a Classroom sin revisarlo a mano.

La variante `--con-guion` es la del archivo propio y lo conserva todo, así que no se sube a
ningún lado.

`tools/prueba-paquete.py` empaqueta una sesión de mentira con las tres clases de nota puestas
y comprueba las dos mitades: que no se filtre nada y que el lector funcione dentro del archivo.

### El lector de apuntes

Lo que **sí** viaja es el `<aside class="apuntes">` de cada lámina, y con él un lector que el
empaquetador inyecta, y solo si la sesión tiene apuntes escritos.

**El panel arranca abierto**, porque el apunte es parte de lo que se entrega y no un extra que
haya que descubrir. Va al costado, con el apunte de la lámina en curso, y **la lámina se encoge
en lugar de taparse**, así que se lee sin perder de vista la diapositiva. Quien no lo quiera lo
cierra con Cerrar, con la tecla `A` o con Escape, y entonces aparece un botón abajo a la
izquierda que lo devuelve. En pantalla estrecha el panel pasa a ocupar la mitad de abajo.

En la portada, en el cierre y en los separadores no hay apunte, y el panel lo dice en lugar de
quedarse en blanco. Desde el panel, **Ver todos** abre los apuntes completos: todas
las láminas con su título, su apunte y **una miniatura de la diapositiva al lado**, de corrido,
con los separadores de bloque haciendo de encabezado. La miniatura es un clon vivo de la
lámina dentro de su propio `.reveal`, reducido a la cuarta parte, así que hereda el tema
entero, fondo incluido, y nunca se desfasa del deck; un clic en ella lleva a esa diapositiva.

Se escriben al cargar y sus miniaturas se montan al abrirlos o antes de imprimir,
que es lo que evita que un Ctrl+P a secas saque hojas en blanco.

La tecla `A` abre y cierra el panel. La tecla **`T` alterna** entre las láminas y los apuntes completos,
en los dos sentidos, y Escape también sale de ellos.

### La ficha de la sesión

Los apuntes cierran con la **ficha**: la bibliografía de la sesión y sus créditos. El deck la
lleva en un `<aside class="ficha">` dentro de la lámina de cierre, y es **obligatoria en todas
las sesiones**. En la propia lámina de cierre, el panel la muestra en lugar del hueco de
apunte, así que el grupo la encuentra por los dos caminos.

Cada entrada de la bibliografía lleva su identificador, `<li id="ref-gencast">`, y lo que la
sesión cita se marca donde se cita, con `<cite data-ref="gencast"></cite>`, **en el guion de
orador y en el apunte, nunca en el cuerpo de la lámina**: el número se compone volado y
proyectado promete una nota al pie que no está. El número lo escribe `tools/citas.py` en el
propio HTML, tomándolo del orden de la bibliografía, así que se ve igual en el paquete y en el
papel sin depender de ningún script. En el paquete, pulsar una marca del apunte abre el
apuntes y deja su referencia resaltada unos segundos; al
copiar la ficha a los apuntes, los `id` se cambian por `data-ref-id` para no duplicarlos.

`tools/apuntes.py` la copia a `apuntes.md`, convierte las marcas en `[N]` y avisa cuando falta
la ficha, con código de salida distinto de cero. `plantillas/tema-centrogeo/plantilla-sesion.html` ya la trae, con los créditos
resueltos y la bibliografía por completar.

### Imprimir

Los apuntes son lo único imprimible del paquete, y salen como un documento de texto: **tamaño
carta**, márgenes normales, cuerpo de 10.5 puntos justificado, y la miniatura de cada lámina
flotada a la derecha con el texto rodeándola, como una figura en un procesador de textos.
Varias notas por página, no una por hoja. La sesión 2, con sus 54 apuntes, sale en 19 páginas.

Para conseguirlo hay que **desactivar la hoja de impresión de reveal**, que pone la página en
1280 por 720 y el cuerpo en veinte puntos. Se hace por la puerta que el propio reveal deja:
todas sus reglas están escritas como `html:not(.print-pdf)`, así que el lector le añade al
`html` la clase `print-pdf` antes de imprimir y se la quita al terminar.

Dos trampas de este camino, las dos con su prueba de regresión:

- La regla que esconde el deck tiene que ser `body > .reveal`, no `.reveal`, porque cada
  miniatura lleva dentro su propio `.reveal` y se escondían todas.
- El clon se escala con `zoom` y va en flujo normal al imprimir, no con `transform` ni en
  posición absoluta.

`tools/prueba-paquete.py` imprime el paquete a PDF y comprueba que la página sea carta y que
entren varias notas por hoja.

## Cómo se validó

La plantilla oficial se renderizó con LibreOffice a PNG y se comparó píxel a píxel con el
render del deck vía decktape, con dos auditorías adversariales independientes de por medio.

Resultado final: **todas las cajas de texto y elementos gráficos caen a 0-2 px de la
plantilla oficial**. El 4.2% de píxeles que difieren es rasterización de texto: LibreOffice y
Chrome aplican hinting y suavizado distintos, y eso no se puede eliminar.

## Diferencias deliberadas con la plantilla

1. **Se omite el recuadro azul de traducción de señas.** La propia plantilla lo rotula
   "(BORRAR)".
2. **La caja de contenido se recortó** a la altura libre real, ver la tabla de capacidad.
3. **Los fondos pasaron de PNG 8K a WebP de 1920 px.** De 49 MB a 300 KB. La diferencia de
   color es de un nivel sobre 255, imperceptible.
4. **Se añadió estilo para tablas, código e imágenes**, que la plantilla no contempla.

## Limitaciones conocidas

- Los pesos 500 y 600 de Noto Sans se distinguen poco a través de la compresión de Zoom.
  Para enfatizar, apóyate en el color o en la cursiva, no solo en la negrita.
- Montserrat solo está vendorizado en peso 600 y no se usa: la plantilla lo declara en un
  shape decorativo vacío.
- El subconjunto latino de las fuentes no incluye flechas ni símbolos matemáticos poco
  comunes. Si hacen falta, hay que ampliar el subconjunto.
