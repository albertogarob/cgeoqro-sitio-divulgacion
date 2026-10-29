---
name: corregir-sesion
description: Aplica al deck de una sesión las correcciones que Alberto dejó en el modo de revisión, las notas, los guiones reescritos, los guiones cortos, los niveles de recorte, el orden de las láminas, las que pidió nuevas, las que marcó para borrar y las que pidió combinar, leyéndolos del archivo notas.json de la sesión, y cierra el ciclo dando por resueltas solo las que corrigió. Úsalo cuando se pida corregir, aplicar o resolver la revisión de una sesión, por ejemplo "aplica la revisión de la S03", "ya revisé la sesión 4", "corrige el deck con estos comentarios" o "atiende la revisión de la clase del jueves".
---

# Corregir una sesión a partir de su revisión

Alberto revisa un deck servido por `presentacion/tools/servir.py`, con `?review` al final de la URL. Sus
notas se guardan en `presentacion/sesiones/SNN-.../notas.json`, un archivo del propio proyecto. Este skill
las lee de ahí, aplica las correcciones al HTML, vuelve a generar todo lo que se deriva de él,
y da por resueltas las que atendió.

No hace falta ninguna extensión del navegador, ni que Alberto pegue nada. Funciona en cualquier
sesión, con `cat`.

Este documento es autosuficiente. No supongas contexto de conversaciones anteriores.


## Dónde vive esto en este repositorio

Este skill viene del curso y del deck del observatorio enoturístico, donde la carpeta de
la presentación ERA la raíz del proyecto. Aquí no: la raíz es el sitio web en Astro, y
toda la cadena de decks cuelga de **`presentacion/`**.

Así que `tools/`, `sesiones/`, `admin/`, `plantillas/` y `salidas/` hay que leerlos como
`presentacion/tools/`, `presentacion/sesiones/` y demás. Lo más limpio es entrar primero:

```bash
cd presentacion
```

y a partir de ahí todas las órdenes del skill valen tal cual. El puerto del servidor
aquí es el **8933**, no el 8931 del curso ni el 8932 del observatorio.

Hoy hay una sola sesión: `sesiones/S01-sitio-de-divulgacion/`, la visita guiada del
sitio a la dirección general. Ocho de sus catorce paradas no son láminas de texto:
cargan el sitio publicado dentro de un iframe. Si un skill va a tocar esas láminas,
que sepa que ahí dentro no hay contenido que editar, solo el marco y la tira de puntos
de la derecha.

## 0. El ciclo completo

```
Alberto:  /servir-sesion N   y revisa en la liga que da
Alberto:  anota con A y con G, y dice "aplica la revisión de la N"
Tú:       python3 presentacion/tools/notas.py N          lees lo que dejó
Tú:       aplicas las correcciones al index.html
Tú:       corres el pipeline y vuelves a empaquetar
Tú:       python3 presentacion/tools/notas.py N --resuelto ...   das por cerradas las que hiciste
Tú:       python3 presentacion/tools/cambios.py N                 marcas lo que cambiaste, para que lo vea
```

Si tiene el deck abierto, los resaltados de lo resuelto desaparecen solos en unos segundos. Las
láminas corregidas no: el anotador le ofrece recargar con un aviso arriba a la izquierda en
cuanto detecta que tocaste el `index.html`.

## 1. Situarte

**De qué sesión se trata.** Del mensaje, o de la carpeta que te diga. Si no está claro,
**pregúntalo**; nunca lo deduzcas de la fecha.

Antes de tocar el HTML, lee:

1. El propio `presentacion/sesiones/SNN-*/index.html`, entero. Necesitas ver la lámina que cada nota toca y
   las de alrededor.
2. `CLAUDE.md` en la raíz, para las reglas permanentes del curso.
3. `presentacion/admin/plan/SNN.md`, el plan de la sesión, para no corregir en contra de lo planeado.
4. `presentacion/plantillas/tema-centrogeo/README.md`, para las clases de lámina y su capacidad real, si
   alguna corrección va a mover contenido de sitio.

Si la sesión ya se impartió o ya se subió a Classroom, dilo al reportar: la corrección obliga a
volver a subir el paquete.

## 2. Leer las notas

```
python3 presentacion/tools/notas.py 1
```

Devuelve, por lámina, cada nota con su `nid`, su cita y su texto, y aparte los guiones
reescritos pendientes. Con `--json` sale el documento crudo, que es lo que hay en
`presentacion/sesiones/SNN-.../notas.json`:

```json
{"v": 4,
 "notas": {"evaluacion": [{"nid": "n1a2b3", "cita": "50%", "nth": 0,
                           "texto": "subir tareas a 60", "ambito": "lamina",
                           "ts": "2026-09-02T11:20"}]},
 "guiones": {"formulacion-de-problemas": {"texto": "Primer párrafo.\n\nSegundo.", "ts": "..."}},
 "cortos":   {"alphazero": {"texto": "Lo mismo en dos frases.", "ts": "..."}},
 "recortes": {"alphazero": {"nivel": 2, "ts": "..."}},
 "orden":    ["portada", "nueva-k3f", "alphazero"],
 "nuevas":   [{"id": "nueva-k3f", "texto": "Qué debe contener la lámina.", "ts": "..."}],
 "borradas": ["formulacion-de-problemas"],
 "fusiones":  [{"id": "fusion-7c2", "partes": ["mapa-a", "mapa-b"],
                "texto": "Quédate con el ejemplo del decil.", "ts": "..."}]}
```

- La llave de `notas` es el **id de la lámina**, no su número.
- `ambito: "guion"` significa que la nota es sobre el guion hablado, o sea sobre el contenido
  del `<aside class="notes">` de esa lámina. **`"lamina"` es sobre lo que se ve en pantalla.**
  Es la distinción más importante y la más fácil de pasar por alto.
- `cita` es el fragmento que tenía seleccionado, y `nth` cuál de sus apariciones era. Te dicen
  a qué parte exacta se refiere.
- `nid` identifica la nota. **Guárdalos**: son con lo que después se cierra lo resuelto.
- Una llave que no corresponde a ninguna lámina del deck es una nota huérfana, de una lámina
  que se borró. Se atiende si todavía tiene sentido y, si no, se reporta y se da por resuelta.
- `guiones` son reescrituras pendientes de aplicar al HTML, un párrafo por bloque separado por
  un renglón en blanco. **Se aplican tal cual**, un `<p>` por párrafo, salvo que contengan algo
  prohibido por las reglas de estilo, y entonces se corrige y se dice.
- `cortos` son guiones cortos pendientes, con el mismo formato. Van a un
  `<aside class="corto">` de esa lámina, no al de notas.
- `recortes` son niveles de recorte pendientes, que van a `data-recorte` en el `<section>`.
  `ambito: "corto"` en una nota significa que es sobre el guion corto, no sobre el largo.
- `orden` es el orden nuevo de las láminas, si las arrastró en la rejilla, tecla `R`. Es el
  único apartado que no va por lámina sino por deck: la lista completa de ids. **No lo apliques
  a mano**, que mover sesenta `<section>` a mano es como se pierde una lámina: lo hace
  `presentacion/tools/reordenar.py`, en el paso siguiente, y él mismo lo cierra.
- `nuevas` son **láminas que pidió y que hay que escribir**, cada una con la descripción de lo
  que debe contener. Las mete `reordenar.py` como un `<section>` con `data-pendiente`, y
  escribirlas es tuyo: ver más abajo.
- `borradas` son láminas que se van del deck. También las aplica `reordenar.py`. Ojo con sus
  notas: se quedan huérfanas, y hay que cerrarlas en el mismo pase.
- `fusiones` son **láminas que hay que combinar en una**, con sus partes en el orden en que se
  leen y una nota opcional con el criterio. `reordenar.py` no las funde: las marca. Combinarlas
  es tuyo, y viene explicado más abajo.

**Si no hay nada pendiente**, no supongas que no revisó. Lo más probable es que abriera el deck
con doble clic: sin servidor, las notas se quedan en el navegador y no llegan al archivo. El
anotador se lo avisa con un aviso amarillo en la barra. Pregúntaselo, y si fue eso, ve a la vía
del portapapeles del final.

## 3. Clasificar antes de tocar nada

Recorre las notas y separa en tres montones. Este paso decide lo demás:

| Montón | Qué es | Qué haces |
|---|---|---|
| Directa | dice qué cambiar y por qué. "falta el año", "esto va en la lámina anterior" | la aplicas |
| De criterio | dice el problema, no la solución. "acortar", "esto no se entiende", "muy denso" | decides tú, la aplicas y reportas qué asumiste |
| De Alberto | cambia una decisión que solo él toma | **no la aplicas**, preguntas |

Son de Alberto, y se preguntan siempre:

- Los porcentajes de evaluación, las fechas de entrega y las reglas del curso.
- El alcance del proyecto final, las tareas y los ejercicios de código.
- Comprometerse con un dataset o una herramienta que no esté ya en el deck ni en
  `presentacion/admin/plan/SNN.md`. La biblioteca que le toca al tema de la sesión ya no entra aquí: se
  nombra en la parte de tecnologías, y eso lo confirmó Alberto el 28 de septiembre de 2026.
- Quitar o añadir un tema del temario, no una lámina, un tema.

Una nota de criterio no se deja pendiente por comodidad: se resuelve. "Acortar, me como cuatro
minutos" se atiende recortando el guion de esa lámina y comprobando con `tiempos.py` que la
sesión sigue en banda, y se reporta cuánto se recortó.

## 3 bis. Una nota es un ejemplo, no un inventario

**Política del 29 de septiembre de 2026.** Alberto revisa por muestreo: lo que señala es lo que
le tocó ver. Si solo se arregla esa lámina, el resto del material sigue igual y tiene que
volver a señalarlo. Esa noche señaló trece veces la misma clase de fallo porque cada vez se
corrigió la instancia y no la clase.

Así que por cada nota: **corrige esa lámina, y después barre el deck entero buscando la misma
clase de fallo**, con `grep` cuando se pueda mecanizar y leyendo cuando no. Si la nota toca una
regla que ya está escrita en `CLAUDE.md`, comprueba el material completo contra esa regla, no
el renglón señalado. **El reporte dice cuántas apariciones había y cuántas se corrigieron**, no
solo la que él vio.

## 3 ter. Cuando dice que no entiende, la explicación se valida en el chat

**Política del 29 de septiembre de 2026.** Una nota que dice "no se entiende", "no te entiendo"
o "esto no me queda claro" **no se atiende reescribiendo el deck**. Se atiende así:

1. **Explícaselo en el chat**, en palabras llanas, sin abrir el HTML.
2. **Espera a que conteste.** Va a señalar el punto exacto donde se rompe, y casi nunca es el
   que tú habrías arreglado.
3. **Solo entonces** lleva esa explicación, ya validada, a las láminas.

La razón es de coste. La noche de la sesión ocho la sección de RETE se reescribió tres veces
suponiendo dónde estaba el problema, y las tres fallaron. La cuarta funcionó porque la
explicación se validó antes en el chat, donde Alberto señaló los dos puntos que no cerraban.
Una reescritura a ciegas cuesta una hora; un párrafo en el chat, dos minutos.

Y cuando la explicación del chat funcione, **la sección se reescribe entera a partir de ella**,
no se parchea la que ya estaba. Lo que no se entendió es el orden en que se cuenta, y parchear
conserva justo eso.

## 4. Aplicar las correcciones

Los ids están por duplicado en el HTML, en `id` y en `data-sid`, con el mismo valor. Reveal le
quita el `id` a la lámina visible mientras está en pantalla, por eso el anotador lee `data-sid`.
Para localizar una lámina busca cualquiera de los dos.

Sobre la lámina:

- **Viñetas, no párrafos**, salvo que el párrafo esté justificado. Las tablas sí se permiten.
- **Cada sección empieza por su motivación**, política del 28 de septiembre de 2026: la primera
  lámina después del separador plantea **qué problema resuelve** el concepto y por qué hace
  falta, y la siguiente lo define. Ponerlo solo en el guion del separador no cuenta.
- **Una sección no puede tener una sola lámina**, de la misma fecha. Lleva como mínimo la
  motivación, el concepto y **un ejemplo trabajado**. Y al recortar por tiempo, la lámina que se
  quita nunca es la del ejemplo ni la de la motivación.
- **La lámina se explica sola.** Quien la vea sin oír a Alberto tiene que entenderla: el
  término que usa queda definido en ella, el dibujo lleva sus rótulos, y la conclusión está
  escrita, no solo dicha. **El guion suplementa a la lámina, no la complementa.** La prueba es
  leer la lámina tapando su `<aside class="notes">`: si queda una pregunta sin responder, el
  arreglo va en la lámina. Dos razones prácticas: el paquete que recibe el grupo no lleva el
  guion, y cuando la sesión va tarde lo que se pierde es justo el guion largo.
- **Toda frase corta tiene que sobrevivir la pregunta "¿qué?".** Un verbo sin su complemento no
  es concisión, es ambigüedad: "sin elegir", "no coinciden", "vale la pena anotar". Entre
  repetir un sustantivo y dejar la duda, **se repite**. Y no se sustituye un término técnico ya
  introducido por una paráfrasis coloquial.
- **El lector es alguien que aprende el tema hoy**, política del 29 de septiembre de 2026:
  se escribe para quien ve el tema por primera vez, en las cuatro caras de la lámina. Ninguna
  referencia sin nombrar su referente ("las dos expresiones", "la otra", "ese paso"); todo
  símbolo de una fórmula explicado en la propia lámina, subíndices, primas y letras griegas
  incluidas; toda decisión del algoritmo con su porqué, no solo su enunciado; y ningún término
  que la sesión no haya definido, ni de pasada. No deroga el nivel de posgrado: lo que no se
  puede es suponer que ya conocen el algoritmo que la sesión viene a enseñar.
- **La coordenada va sola, y el globo dice dónde está**, política del 5 de octubre de 2026, que
  **retira** la glosa posicional escrita: "vamos a quitar la regla de que cada vez que menciones
  una parcela tienes que explicar cuál es con expresiones como esta. No sirvió y sólo come
  espacio". Nada de "la (1,2), la que está justo encima de la (1,1)" en ninguna de las cuatro
  caras. En su lugar, toda coordenada del cuerpo y toda expresión que nombre parcelas va
  envuelta en la etiqueta con glosa de `presentacion/tools/glosas.py`, y el globo enseña la rejilla con la
  casilla marcada. Lo que sigue en pie: la lámina que enseña a leer la notación conserva su
  explicación; **las demás etiquetas cortas sí llevan su contenido escrito**, el número de una
  regla con lo que la regla dice, una letra griega con qué guarda, el identificador de un nodo
  con qué condición vigila; y la glosa funcional se queda cuando aporta algo que el dibujo no
  da. La geometría del terreno de la brigada está en CLAUDE.md.
- **Un solo nombre por concepto, y es el del destino**, política del 29 de septiembre de 2026.
  Si el algoritmo con el que cierra la sesión llama match a una operación, la sesión la llama
  match desde la primera lámina, aunque la teoría de la que sale traiga otro nombre. El grupo no
  tiene que aprender dos palabras para la misma cosa y descubrir a la mitad que eran una.
  **La comprobación no es buscar la palabra que decidiste quitar.** Es escribir la tabla de
  concepto a todos sus nombres y mirar qué casilla tiene más de uno. En la sesión ocho se barrió
  "unificar" y sobrevivieron "probar", "encajar" y "coincidir", que eran la misma operación, a
  veces en la misma lámina.
- **El dibujo escribe lo mismo que la fórmula**, política del 29 de septiembre de 2026. Si la
  lámina dice \(\mathrm{Firme}(p)\), el rótulo del SVG dice `Firme(p)` y el video dice
  `Firme(p)`. Un dibujo que dice "la parcela es firme" al lado de una fórmula abre una brecha
  que el grupo tiene que cruzar solo, y el material no se la cruza. De ahí sale una consecuencia
  al elegir la notación: MathJax no entra en un SVG, así que **la notación de la sesión se elige
  dibujable**, sin subíndices ni letras griegas si esos símbolos van a aparecer en un diagrama o
  en una animación.
- **Un mecanismo se explica con un objeto concreto, sostenido**, política del 29 de septiembre
  de 2026. Antes de escribir la sección de un algoritmo, elige la cosa física con la que se
  cuenta entero y no la sueltes: la libreta donde el motor apunta lo que ya vio, no el nodo que
  filtra. La prueba es preguntarse qué imagen produce cada palabra. "Filtro", "nodo", "circula"
  y "deja pasar" no producen ninguna; "libreta", "apuntar" y "comparar dos listas" sí. Los
  nombres técnicos se cuelgan del objeto, una vez cada uno, y a partir de ahí se sigue nombrando
  el objeto.
- **El enlace es lo último que se recorta**, política del 29 de septiembre de 2026. El fallo
  de fondo del material es poner los conceptos y saltarse la frase que los une: el porqué de
  una afirmación, el referente de un demostrativo, de dónde sale un número, dónde está una
  parcela, o de qué concepto simple sale el difícil. Y la causa es mecánica: cuando una lámina
  no cabe o la sesión va larga, el enlace es lo primero que parece grasa. **Al recortar, el
  enlace es lo último que se toca**: si no cabe, se quita una viñeta entera, se parte la lámina
  o se quita otra lámina, nunca la articulación.
- **La lámina final es la lista de materiales**, política del 29 de septiembre de 2026, y es el
  criterio con el que se atiende toda nota que diga "acortar", "sobra", "muy denso" o "esto no
  hacía falta". Lee la lámina a la que la sesión llega, la que enuncia el algoritmo o el
  resultado, y **lista las palabras que usa**. Lo que la sesión explica y no aparece en esa lista
  se justifica en una frase o se va. En la sesión ocho los cinco pasos de RETE usaban siete
  palabras, y contra esa lista se cayeron nueve láminas y media hora. **El eje es el
  rendimiento, no la dificultad**: no se corta un concepto por ser abstracto ni por llevar
  fórmula, se corta por no rendir en la lámina final, y lo que se queda **se queda entero**, con
  su formalismo. Alberto lo dijo así: no está peleado con las matemáticas, está peleado con
  introducir conceptos abstractos que no rindan.
- **De lo fácil a lo difícil, sin saltos**, política del 29 de septiembre de 2026, que es lo que
  hay que comprobar después de reordenar, insertar o combinar láminas. Lee los títulos en su
  orden nuevo y pregúntate en cada paso qué necesita saber alguien para entender el siguiente:
  si la respuesta incluye algo que la sesión todavía no ha dicho, ahí quedó un salto. El grupo
  **no estudió ciencias de la computación**, y entre una sesión completa y una fácil de
  entender, Alberto prefiere la fácil de entender. Si un concepto solo cabe metiéndolo de golpe,
  la salida es dejarlo fuera.
- **El término se dice como lo dice el campo**, política del 28 de septiembre de 2026: si el
  concepto ya se conoce por su palabra inglesa, se usa la inglesa, no una traducción que nadie
  emplea. La prueba es cómo lo llama la biblioteca del tema y la lectura del curso. No deroga la
  regla del idioma: cambia cuál de los dos es el término y cuál la glosa.
- **Cada pieza de la lámina lleva su párrafo en el guion**, política del 12 de octubre de 2026:
  cada viñeta, la línea en llano, cada fórmula, cada dibujo, cada video y cada bloque de código
  tienen al menos un párrafo del guion que habla de ellos. Quedan fuera la portada, los
  separadores de sección, la de agradecimiento y la de bibliografía. Lo comprueba
  `presentacion/tools/anclas.py`, que al final de cada pasada tiene que decir **TODA PIEZA DE TODA LÁMINA
  TIENE SU PÁRRAFO EN EL GUION** y devuelve error si no. El arreglo casi nunca es escribir guion
  nuevo: es **partir en dos el párrafo que cubre dos viñetas de corrido**, que de paso cumple lo
  de una idea por frase. Para la fórmula que es una cuenta, y que por política no se lee en voz
  alta, el generador marca su párrafo con `@formula ` delante y queda anclado a ella.
- **Nunca se dice "la lectura del curso": se dice el autor**, política del 12 de octubre de
  2026. Donde el material la nombre, va "Russell y Norvig"; donde la referencia no aporte nada,
  se quita entera. La bibliografía de la ficha no cambia: sigue abriendo con ellos.
- **Si la lámina habla de una tabla, se dibuja una tabla**, del mismo día. Acota la regla de que
  una tabla no se proyecta, que prohíbe tabular **un proceso**: una traza, un recorrido, una
  serie de valores. Una tabla de probabilidad condicional no es la tabulación de nada, es el
  objeto que se enseña, y se dibuja como tabla. La prueba: si la lámina la llama tabla, dibújala
  como tabla.
- **Ningún número de probabilidad va solo**, política del 13 de octubre de 2026: en la lámina va
  el número y su expresión completa en el globo al pasar el ratón, con `cifra()` de
  `presentacion/tools/glosas.py`; en el guion la expresión se escribe. **La tabla de expresiones va por nombre
  de la cantidad, nunca por su número**, porque el mismo número significa cosas distintas en
  láminas distintas.
- **La lámina con fórmula no lleva explicación en llano**, y esta es la tercera versión de la
  regla en un mismo día, la de la tarde del 13 de octubre de 2026: la línea en llano **sale del
  cuerpo** y se queda en el guion, al final, anunciada como el cierre. Alberto: "quita estos pies
  de lámina en todas las láminas para adelgazarlas". Lo hace solo `llano_al_final()` del
  generador. En las láminas **sin** fórmula la línea en llano sigue en el cuerpo y sigue
  abriendo.
- **El título cabe en UNA línea**, decidido el 13 de octubre de 2026: «títulos de una línea
  únicamente». El largo no se cuenta en caracteres, porque el tema lleva `text-wrap: balance`;
  se mide con `presentacion/tools/titulos.py`, y el presupuesto seguro ronda los 29. Si la afirmación no cabe
  en una línea, gana la línea.
- **Prohibidas las láminas gordas en texto**, política del 13 de octubre de 2026, que
  Alberto fijó tras marcar 26 de las 37 láminas de contenido de la sesión 12 con la
  palabra «gorda». **Ninguna viñeta pasa de dos líneas**, unos 45 caracteres por línea;
  **como mucho tres viñetas** por lámina, más la línea de motivación; y el texto entero
  no pasa de **7 líneas con dibujo** ni de **8 sin él**. Quedan fuera la portada, los
  separadores, la agenda, el repaso, el cierre y la bibliografía. Lo comprueba
  `presentacion/tools/gordas.py`, que mide en Chrome porque una expresión de MathJax ocupa mucho más
  ancho que su LaTeX y en caracteres no se ve. **Al adelgazar, el orden es: primero se
  quita la viñeta que repite algo ya dicho, después se funden dos en una, y solo al final
  se acorta una frase**, que es como se respeta «el enlace es lo último que se recorta».
  Y nunca se corta la cópula que define un término: al adelgazar la sesión 12 cayeron
  siete definiciones de golpe y las cazó `terminos.py`, así que correrlo después no es
  opcional.
- **El vocabulario no se reinventa entre sesiones.** Antes de nombrar un concepto, mira cómo lo
  nombraron las sesiones anteriores, con `grep` sobre `presentacion/sesiones/S*/index.html`, y usa esa
  palabra. Si de verdad hace falta otra, la lámina dice que son lo mismo.
- Respeta la **capacidad de la clase de lámina**, que está en el README del tema. Si el texto
  ya no cabe, parte la lámina en dos antes que encoger el tipo o cambiar el tema.
- **No modifiques `presentacion/plantillas/tema-centrogeo/`.** Es un port validado de la plantilla oficial y
  cambiarlo afecta a las 30 sesiones. Si algo no cabe, el problema es el contenido. Si de
  verdad hace falta tocarlo, pregunta primero.
- Resaltado a nivel de lámina, no de viñeta: una o dos palabras clave, las que la condensan.
- Un título de tres líneas se encima con el cuerpo. Acórtalo.

Sobre el guion, registro **formal**, y estas reglas no son negociables:

- Prosa hablada, frases cortas, una idea por frase. Sin viñetas dentro del guion.
- **Los números van en cifra, con punto decimal.** `0.018`, `0.6923`, `1763`, `1 048 576`.
  Nunca deletreados: nada de "cero coma cero uno ocho". El separador decimal es el punto, que es
  el de México, y los miles van con espacio, no con coma. Alberto lo pidió el 6 de octubre de
  2026, después de leer un guion deletreado delante del grupo. **Deroga la regla anterior de
  "cifras y años en letra".** Lo que sí sigue en prosa es el cardinal que acompaña a un
  sustantivo: "los dos sensores", "hay cuatro modelos", "un millón de casillas". En cifra va el
  **valor**: la probabilidad, el resultado, el año, el conteo que la lámina también enseña así.
- **En el guion, las matemáticas también van en LaTeX.** Nunca la versión leída en voz alta:
  nada de "Par sub uno uno", "theta" ni "Firme de p". Va `\(\mathrm{Par}_{1,1}\)`,
  `\(\theta\)`, `\(\mathrm{Firme}(p)\)`. MathJax compone los bloques `notes` y `corto`, que
  no están en `ignoreHtmlClass`.
- **Lo resaltado se mide en el tiempo que dura el párrafo**, política del 12 de octubre de 2026:
  el texto que se enciende en la lámina no puede pedir más tiempo de lectura que el propio
  párrafo, con un presupuesto de 1.2 palabras de lámina por palabra de párrafo. Lo aplica
  `presentacion/tools/anclas.py` sin que haya que escribir nada. **Lo que sí es de contenido**: un arranque
  corto ya no cubre la línea en llano de su lámina, así que el guion abre diciéndola.
- **Y cada figura lleva su speech, no solo su acotación**, del mismo día. La acotación
  `[Al dibujo, ...]` no se lee en voz alta, así que **detrás va siempre la prosa que explica esa
  parte**: una acotación suelta al final, o dos seguidas, dejan la figura sin quien la cuente.
  Mientras se lee esa prosa la figura sigue resaltada, porque la acotación abre un tramo que
  `anclas.py` arrastra hasta la acotación siguiente; eso no hay que escribirlo. La figura va
  aparte y no le quita sitio a la viñeta ni a la línea en llano, que se resaltan a la vez. La
  comprobación es la misma orden, que reporta **SOLO ACOTACIÓN, sin prosa que lo explique**.
  **Y el tramo se cierra solo**: la acotación garantiza el párrafo que viene detrás, y a partir
  de ahí la figura se queda solo mientras el párrafo siga hablando de ella, medido contra los
  rótulos del dibujo. Una lámina cuyo guion narra la figura entera la deja encendida entera, y
  eso es correcto; lo que se arregló el 12 de octubre de 2026 es que se quedara pegada mientras
  Alberto discutía otra cosa.
- **El guion dice cuándo mirar el dibujo y qué decir de él.** Toda lámina con dibujo lleva en
  su guion una acotación entre corchetes que marca el punto en que hay que pasar a la figura, y
  dice **qué parte señalar** y **qué decir de ella**: `[Al dibujo. La barra de arriba, con los
  cuatro mundos. Que los cuatro suman uno.]`. Si el dibujo tiene partes, va una acotación por
  parte, cada una donde toca mirarla, igual que el guion por tramos de una lámina de video.
  Alberto lo pidió el 6 de octubre de 2026. Describir el dibujo en prosa hablada no cuenta: eso
  se lee en voz alta y no dice cuándo girarse hacia la pantalla.
- Acotaciones de escena entre corchetes. No se leen y no cuentan tiempo.
  **Dónde se ve**: desde el 12 de octubre de 2026 las dos vistas de lectura sacan la acotación
  de la columna y la ponen en una franja al costado, rotulada "en escena", y una acotación que
  es su propio párrafo deja de ser una parada del recorrido. **En el HTML no cambia nada**: se
  sigue escribiendo entre corchetes y donde toca.
- Prohibido: las palabras "incómoda" y "brutal"; el énfasis retórico añadido; la empatía
  impostada; las frases coloquiales; el autodesprecio; la presión sobre el grupo; las muletillas
  de atención como "fíjense", "acuérdense" o "piénsenlo"; y repetir la misma palabra distintiva
  a lo largo de la sesión.
- Prohibida la **antítesis enfática**: "no dice que algo falla: dice qué falla", "no es X, es
  Y", "no se trata de A, sino de B". Se dice la afirmación y ya, en el guion y en la lámina.
- Alberto se presenta como **el Dr. Alberto García Robledo**. Se dice "ejercicios de código".
- **No prometas nada que Alberto no haya decidido**: ni ejercicios, ni el formato del proyecto
  final. Las **bibliotecas concretas sí se nombran**, y se enseña su forma, en la parte de
  tecnologías de la sesión, desde el 28 de septiembre de 2026. Fuera de esa parte no se da por
  hecho que el grupo vaya a instalar nada.
- **Las tres partes que toda sesión cubre**, política del 28 de septiembre de 2026: el tema, las
  tecnologías que lo implementan con su forma enseñada, y las aplicaciones geoespaciales, con los
  casos hipotéticos declarados como tales. Es cobertura, no estructura, así que una corrección
  puede reordenar lo que quiera **mientras los tres sigan estando**. Dos trampas al corregir: el
  ejemplo de juguete no cuenta como aplicación aunque sea geoespacial, y ninguna de las tres
  partes puede quedar marcada con `data-recorte="1"`. Si una corrección deja fuera una de las
  tres, se reporta en vez de aplicarla a medias.
- **La marca de cita va entre corchetes y en la línea base**, `ACT [6]`, y solo en el guion
  y en el apunte, nunca en el cuerpo que se proyecta. Volada y pegada a la palabra se lee
  como parte del nombre: Alberto leyó "ACT6" y entendió que el sistema se llamaba así. Los
  corchetes los pone el CSS del tema, no el HTML, así que no hay que tocar el `<cite>`. Y
  `guion.py` se corre **después** de `citas.py`, o `guion.md` sale con las citas vacías.
- Nada de bibliografía, citas o cifras inventadas. Lo que no puedas confirmar va marcado con
  `[VERIFICAR]` y se reporta al final.
- Nunca el punto medio (U+00B7) ni el guion largo (U+2014), en ningún archivo del curso. Separa
  con comas, puntos o reestructurando, y en listas en línea con punto y coma. No los sustituyas
  por otro adorno como la barra vertical.

Dos cuidados propios de corregir, que no aparecen al generar:

- **Borrar una lámina deja huérfanas las notas ancladas a ella.** Antes de quitar una, mira si
  hay otras notas con ese id y resuélvelas en el mismo pase.
- **Reescribir el texto de una lámina deja sin resaltado a las notas que citaban ese texto y
  siguen pendientes.** La nota sobrevive, pero la lista la marca como cita sin localizar.
  Avísale cuando pase.

### El nivel de recorte y el guion corto

Los dos son metadatos de la lámina y se aplican al `<section>` que lleva ese id:

- **El nivel** va en `data-recorte="1"` o `data-recorte="2"`. Nivel 0, o sea núcleo, se aplica
  **quitando el atributo**, no poniéndolo a cero. Nivel 1 es lo que se pierde sin que nadie se
  entere; nivel 2 es lo que se pierde pero hay que anunciar en clase.
- **El guion corto** va en un `<aside class="corto">` justo después del `<aside class="notes">`
  de esa lámina, un `<p>` por párrafo. Si la lámina ya lo tiene, se sustituye su contenido. Un
  guion corto vacío significa borrar el aside entero.

El guion corto se escribe con las mismas reglas de registro que el largo, y en dos o tres
frases: es lo que se dice de esa lámina cuando la sesión va tarde. No es un resumen de las
viñetas, es el argumento en una frase y el enlace con la siguiente.

Toda lámina con guion hablado debería llevar su versión corta, no solo las marcadas, y
`tiempos.py` lista al final las que no la tienen. En las sesiones anteriores a esa regla esa
lista sale larga: no las escribas todas de golpe en un pase de correcciones, escribe las de las
láminas que estés tocando y dile cuántas quedan. Si Alberto marca una lámina con nivel y la
deja sin guion corto, díselo: sin él, en clase solo se puede saltar entera. Ofrécele
escribirlo tú, pero no lo inventes sin decirlo.

### El orden de las láminas

Si `notas.json` trae `orden`, el deck se reordenó arrastrando las miniaturas en la rejilla del
anotador, y su navegador ya lo está mostrando así aunque el HTML todavía no lo diga. Se aplica
con su herramienta, **antes del pipeline** y después de las correcciones de texto:

```
python3 presentacion/tools/reordenar.py SNN --ver     qué se mueve, sin escribir nada
python3 presentacion/tools/reordenar.py SNN           lo aplica y cierra el pendiente
```

Permuta los `<section>` sin tocar una letra de su contenido, deja el archivo anterior en
`presentacion/sesiones/SNN-.../index.html.bak.orden.AAAAMMDDTHHMMSS`, uno por pasada, y cierra los tres
apartados él solo, subiendo el contador de versión. No hace falta pasárselos a
`notas.py --resuelto`.

Ojo con el orden de las operaciones: aplícalo **después** de haber insertado o borrado láminas
tú mismo, no antes. Si insertas una lámina después de reordenar, la herramienta la mete junto a
su vecina y puede no ser donde Alberto la quería; díselo en el reporte cuando pase.

### Las láminas que pidió y hay que escribir

Si `notas.json` trae `nuevas`, en la rejilla pidió láminas que todavía no existen, cada una con
la descripción de lo que debe contener. `reordenar.py` las mete en su sitio como un `<section>`
con `data-pendiente="1"`, el encargo en el cuerpo y el mismo encargo en el guion.

**Escribirlas es parte de la corrección, no queda para después.** Para cada una:

1. escribe la lámina de verdad siguiendo el encargo y las reglas de estilo de este skill, con
   su clase de tema, su guion de orador, su guion corto y su apunte de estudio;
2. quita `data-pendiente` del `<section>`, que es lo que la da por escrita;
3. si el encargo pide algo que choca con las reglas del curso, no lo inventes ni lo silencies:
   escríbela como se pueda y dilo en el reporte.

Mientras quede un `data-pendiente`, `presentacion/tools/empaquetar.py` **se niega a empaquetar**. Es
deliberado: un encargo mío no llega al grupo por descuido. Si Alberto pidió la lámina pero no
quiere que la escribas todavía, díselo en el reporte y deja la sesión sin empaquetar.

### Las láminas que hay que combinar en una

Si `notas.json` trae `fusiones`, pidió quitar redundancia juntando láminas. `reordenar.py` las
marca y **no borra nada**: la primera parte queda con `data-combinar` nombrando a las demás y
`data-combinar-nota` con el criterio, y cada una de las otras con `data-combinar-en`. Todo el
material sigue ahí, que es lo que hace falta para combinarlo.

Combinar es trabajo de contenido y es tuyo. Para cada grupo:

1. lee las láminas enteras, con su guion, su guion corto y sus apuntes;
2. escribe **una sola** lámina en el sitio de la primera, siguiendo la nota. Si la nota está
   vacía, decide tú el criterio y **di en el reporte cuál seguiste**;
3. refunde también el guion hablado, el guion corto y el apunte: no pegues los tres seguidos,
   que el resultado es más largo que las tres juntas y lo que se pedía era acortar;
4. borra las láminas sobrantes y quita las tres marcas `data-combinar*`;
5. atiende las notas de revisión ancladas a las láminas que desaparecen: o se trasladan a la
   combinada, o se cierran diciendo por qué.

Mientras quede una marca `data-combinar`, `empaquetar.py` se niega a empaquetar, igual que con
las láminas por escribir. Si una combinación no te cuadra, no la fuerces: déjala marcada, dilo
en el reporte y deja la sesión sin empaquetar.

`tiempos.py` es la vara para saber si la combinación sirvió: la sesión tiene que bajar de
láminas, no solo de texto.

`guion.md` no se edita nunca a mano: se genera desde el HTML, que es la fuente única.

## 5. Pipeline

En este orden, y no entregues con algo en rojo:

```
python3 presentacion/tools/ids.py        presentacion/sesiones/SNN-*/index.html    # solo si añadiste láminas
python3 presentacion/tools/reordenar.py  SNN                          # solo si hay orden pendiente
python3 presentacion/tools/citas.py      presentacion/sesiones/SNN-*/index.html    # numera las citas y revisa que existan
python3 presentacion/tools/parcelas.py   presentacion/sesiones/SNN-*/index.html    # las parcelas que nombra cada lámina
python3 presentacion/tools/anclas.py     presentacion/sesiones/SNN-*/index.html    # ancla el guion a las piezas de la lámina
python3 presentacion/tools/apuntes.py    presentacion/sesiones/SNN-*/index.html    # extrae apuntes.md, la lista sale vacía
python3 presentacion/tools/guion.py      presentacion/sesiones/SNN-*/index.html    # regenera guion.md, DESPUÉS de citas.py
python3 presentacion/tools/verifica.py   presentacion/sesiones/SNN-*/index.html    # desbordes y colisiones
python3 presentacion/tools/terminos.py   presentacion/sesiones/SNN-*/index.html    # términos sin definir en pantalla
python3 presentacion/tools/gordas.py   presentacion/sesiones/SNN-*/index.html    # láminas gordas de texto
python3 presentacion/tools/figuras.py    presentacion/sesiones/SNN-*/index.html    # que las figuras se lean proyectadas
python3 presentacion/tools/tiempos.py    presentacion/sesiones/SNN-*/index.html    # duración
python3 presentacion/tools/empaquetar.py presentacion/sesiones/SNN-*/index.html    # paquete para el grupo
python3 presentacion/tools/classroom.py  SNN                          # rearma la carpeta de Classroom
python3 presentacion/tools/cambios.py    SNN                          # marca lo que cambió, para que lo vea
grep -rnP '\x{00B7}|\x{2014}' presentacion/sesiones/SNN-*/
```

**`guion.py` va después de `citas.py`**, no antes: al revés las marcas de cita todavía no tienen
número y `guion.md` sale con las citas vacías.

`tiempos.py` dice además a cuánto baja la sesión recortando el nivel 1 y los dos niveles. Es
el suelo, no el plan: en clase el apuntador recorta solo lo que haga falta.

`verifica.py` debe decir "SIN DESBORDES NI COLISIONES": el desborde recorta texto en silencio y
no se nota hasta estar frente al grupo. `tiempos.py` no debe decir ni SOBRA MATERIAL ni FALTA
MATERIAL: con la banda estimada entre 105 y 130 minutos dirá ALCANZA si el extremo alto no
pasa de 120, y AJUSTADO si lo pasa, que también es entregable. Si una corrección deja la sesión corta o larga, se arregla
quitando o agregando láminas, nunca estirando ni podando el guion: lo que llena la sesión es
el número de láminas, no las palabras. Si no está claro qué quitar, dilo en el reporte.

`ids.py` no renombra lo que ya tiene id, así que no rompe las notas pendientes. Córrelo solo
cuando hayas insertado láminas nuevas.

## 5 bis. Marcar lo que cambiaste, para que lo vea

**Al cerrar cada ronda se corre `presentacion/tools/cambios.py SNN`**, y es lo último del
pipeline. Compara el deck con la foto de referencia que hay en
`presentacion/sesiones/SNN-.../.antes.html` y escribe en `notas.json` qué cambió: qué pieza de
cada lámina, qué párrafo del guion, qué guion corto, qué nivel de recorte, y qué
láminas entraron, salieron o se movieron.

El anotador lo pinta donde está: **la pieza tocada queda marcada en la propia
lámina**, con el texto de antes en un globo al pasar el ratón, y **la ventana del
guion enseña las palabras nuevas y las quitadas**. La barra lleva la cuenta y la
tecla `X` abre la lista de todo, con un botón de "ya lo vi" que toma la foto
nueva y borra las marcas. La tecla `Z` las esconde y las vuelve a mostrar sin
olvidarlas, para poder revisar el deck limpio y recuperarlas después.

Alberto lo pidió el 12 de octubre de 2026: quiere ver los cambios en la misma
pantalla donde revisa, no leerse un reporte. Tres cosas que importan al usarlo:

- **La foto se toma cuando él da por visto**, no al empezar la ronda. Así, si se
  corren tres rondas seguidas sin que mire, ve todo lo que cambió desde la última
  vez que lo vio.
- **Volver a correr el pipeline no produce ruido**: se compara el texto que se
  ve, no los atributos, así que renumerar citas, parcelas o anclas no sale.
- **No lo adelantes a mano.** Si tomas tú la foto a mitad de la ronda, lo que
  hiciste antes desaparece y él no lo verá nunca.

## 6. Cerrar lo resuelto

```
python3 presentacion/tools/notas.py 1 --resuelto n1a2b3 n4c5d6 --guion formulacion-de-problemas \
                        --corto alphazero --recorte alphazero
```

Los `nid` de las notas que corregiste, y los ids de las láminas cuyo guion reescrito, guion
corto o nivel de recorte aplicaste.
El script se encarga de subir el contador de versión y de escribir por el servidor si está
levantado, que es lo que hace que la pestaña abierta de Alberto se entere sin recargar. No
edites `notas.json` a mano: olvidar el contador resucita después lo que acabas de borrar.

Comprueba lo que responde: el número de notas resueltas tiene que ser exactamente el de las que
corregiste. Si no cuadra, párate y repórtalo.

Reglas de honestidad, que son la razón de ser de este paso:

- **Solo lo que de verdad resolviste.** Una nota que dejaste pendiente, o que le devolviste a
  Alberto para que decida, no se cierra. Cerrarla es perderla.
- Nunca vacíes el archivo de golpe. El botón **Borrar todas** del anotador es suyo, no tuyo.

### Si revisó sin servidor

Si abrió el deck con doble clic, sus notas están en el navegador y no en el archivo. Entonces:
que pulse `E`, que lo copia todo al portapapeles, y te lo pegue. El bloque trae lo mismo en
texto, con `(guion)` en lugar de `ambito`, pero sin los `nid`. Para cerrar lo resuelto en ese
caso, escribe `presentacion/sesiones/SNN-.../resueltas.js`:

```js
window.RV_RESUELTAS = {
  sello: "2026-09-02T18:40",
  notas: [{ id: "evaluacion", texto: "subir tareas a 60" }],
  guiones: ["formulacion-de-problemas"],
  cortos: ["alphazero"],
  recortes: ["alphazero"],
  orden: true
};
```

El anotador lo carga solo al arrancar y borra esas notas al recargar, reconociéndolas por su
lámina más su texto. El `sello` es distinto en cada tanda y es lo que impide que el archivo
siga borrando después. Dile que recargue con F5.

Y sugiérele que la próxima vez abra el deck con `/servir-sesion`, que se ahorra todo esto.

## 7. Reportar y cerrar

Reporta, en este orden:

- **Qué aplicaste**, nota por nota, con el id de su lámina y en una línea qué cambió.
- **Qué quedó pendiente** y por qué, separando lo que espera una decisión suya de lo que no
  pudiste hacer.
- **Qué decidiste tú** en las notas de criterio, para que pueda revisarlo.
- **Cómo quedaron `verifica.py` y `tiempos.py`**, con el minutaje antes y después si cambió.
- Cuántas notas cerraste y cuántas quedan vivas.
- Lo que siga marcado con `[VERIFICAR]`.
- Si la sesión ya estaba en Classroom, que hay que volver a subir el paquete.

Deja los pendientes de esta sesión en su propio archivo, no en `TODO.md`:

```
python3 presentacion/tools/todo.py 1 --abrir "subir el paquete corregido a Classroom"
python3 presentacion/tools/todo.py 1 --decidir p2          # lo que quedó zanjado, se guarda como registro
python3 presentacion/tools/todo.py 1 --abrir "..." --transversal    # si afecta a las 30 sesiones
```

Viven en el apartado `pendientes` de `presentacion/sesiones/SNN-.../notas.json`, junto a las notas. Por eso
varios agentes pueden corregir sesiones distintas a la vez sin pisarse: cada uno escribe solo
en el archivo de la suya. Lo decidido no se borra, queda como registro de lo que no hay que
volver a abrir.

`python3 presentacion/tools/todo.py` sin argumentos da la vista de todas las sesiones juntas.

## 8. Si tocaste el anotador o el servidor

Nada de este skill debería obligarte a tocar `presentacion/plantillas/tema-centrogeo/revisar.js` ni
`presentacion/tools/servir.py`. Si aun así hizo falta, es infraestructura compartida por los 30 decks:
pregunta antes y corre después las dos pruebas.

```
python3 presentacion/tools/prueba-revisar.py presentacion/sesiones/SNN-.../index.html   # el anotador, sin servidor
python3 presentacion/tools/prueba-notas.py   presentacion/sesiones/SNN-.../index.html   # las notas en disco
python3 presentacion/tools/prueba-orden.py   presentacion/sesiones/SNN-.../index.html   # la rejilla y reordenar.py
```

## La ronda de auditoría, al cerrar

**Un deck no se audita como se audita código.** Los tres papeles de seguridad, funcionalidad y
pruebas no tocan nada de lo que falla en una presentación. Al terminar el pipeline, y antes de
reportar, corre **una sola ronda de tres auditores**, con **tope duro de cinco minutos cada
uno**, alcance limitado a los archivos de esta sesión, y a cada uno se le dice qué papeles
llevan los otros dos:

1. **Lo aplicado.** Su encargo es demostrar que el reporte miente. Lee desde disco, dictamina
   cada afirmación por separado, busca cambios presentes que el reporte no menciona, y
   comprueba que cada cambio llegó **al paquete de `presentacion/salidas/`** y **a las cuatro caras de la
   lámina**: cuerpo, guion, guion corto y apunte.
2. **Reglas y políticas.** Comprueba lo generado contra `CLAUDE.md` y la memoria del proyecto:
   la lámina se explica sola, sin días ni números de sesión, sin cortes de participación ni
   actividades sin autorizar, tuteo, MathJax, tablas sustituidas por su gráfico, ficha y lámina
   de bibliografía, citas fuera del cuerpo, tipografía, vocabulario continuo, **las tres partes
   cubiertas** con su forma enseñada y sus casos hipotéticos declarados, ninguna de ellas de
   nivel 1, y el pipeline entero en verde.
3. **Correctitud fáctica.** Rehace las cifras del ejemplo por su cuenta, comprueba las
   definiciones, y verifica las atribuciones históricas **en los dos sentidos**: que la fuente
   sostenga la frase, y que la técnica ya estuviera en ese trabajo.

**Una sola ronda.** Si las correcciones sugieren que haría falta otra pasada, se dice en el
reporte en vez de lanzarla. Donde va esta ronda **no va el refutador** de "Afirmaciones de
cambios": el papel uno ya lo es. La sección completa está en `CLAUDE.md`, en "Auditar una
sesión, que no es auditar código".
