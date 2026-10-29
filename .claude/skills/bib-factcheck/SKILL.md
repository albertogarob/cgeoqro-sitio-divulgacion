---
name: bib-factcheck
description: Audita y repara la bibliografía de una sesión del curso, campo por campo, contra fuentes autorizadas. Las referencias no vienen de un archivo .bib, sino de la ficha del deck reveal.js, el <aside class="ficha"> de la lámina de cierre, y las citas son las marcas <cite data-ref>. Úsalo cuando se pida verificar, comprobar, completar o corregir la bibliografía, las referencias, las fuentes o las citas de una sesión, por ejemplo "verifica la bibliografía de la S02", "revisa que las referencias de la sesión 4 sean correctas", "comprueba las fuentes del deck del jueves" o "hay citas mal en la ficha". Recibe el número de sesión, o "todas".
---

# Verificación y reparación de la bibliografía de una sesión

Comprueba y completa **campo por campo** cada referencia que cita una sesión, contra fuentes
autorizadas. Corrige la ficha del deck en su sitio y produce un informe por referencia y por
campo, nombrando la fuente y la herramienta que resolvió cada una.

Este documento es autosuficiente. No supongas contexto de conversaciones anteriores.

El argumento es el número de sesión: `2`, `S02` o `sesión 2`. También acepta `todas`, que
recorre las sesiones que tengan ficha. Si no viene argumento, pregúntalo antes de hacer nada.


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

## De dónde salen las referencias en este proyecto

No hay archivo `.bib`. La bibliografía de cada sesión vive **dentro de su deck**, en la ficha:

```html
<aside class="ficha"><h3>Bibliografía</h3>
<ol>
<li id="ref-curso"><strong>Lectura del curso.</strong> Russell, S. y Norvig, P. <em>Artificial
    Intelligence: A Modern Approach</em>, tercera edición. Pearson, 2010. Capítulo 1,
    secciones 1.1 y 1.2.</li>
<li id="ref-turing">Turing, A. Computing machinery and intelligence. <em>Mind</em>, volumen 59,
    páginas 433 a 460, 1950. El artículo que propone la prueba de Turing.</li>
</ol>
<h3>Créditos</h3>
<p>...</p>
</aside>
```

La ficha está en el `<section class="cierre">`, la última lámina. Es obligatoria: sin ella la
sesión no se entrega, y `presentacion/tools/apuntes.py` da error.

Lo que cita la sesión se marca donde se cita, en el guion de orador y en el apunte, **nunca en
el cuerpo de la lámina**, con `<cite data-ref="turing"></cite>`. El número lo pone
`presentacion/tools/citas.py`, que las recoge estén donde estén.

**Las entradas son prosa en español, no registros BibTeX.** Cada una lleva, además de los datos
bibliográficos, una **glosa**: la frase final que dice qué papel juega esa fuente en la sesión
("El artículo que propone el Transformer", "El análisis que desalentó las redes neuronales
durante quince años"). La glosa también se verifica, ver el paso 3.

## La regla que gobierna todo: nunca inferir

**Nunca adivines, infieras, autocompletes ni reconstruyas un valor.** Un campo se rellena o se
cambia **solo** cuando una fuente autorizada lo confirma explícitamente. Si después de agotar
la escalera del paso 4 no puedes confirmar un valor, déjalo como está y repórtalo sin resolver,
**aunque sea un solo campo**, por ejemplo solo el año. "No se pudo verificar" siempre es
preferible a un valor sin confirmar. Nunca deduzcas un campo del identificador de la
referencia, de las entradas vecinas, de tu propio conocimiento previo ni de "lo que suele ser
esa publicación".

Esto es más estricto que la regla general del proyecto. `CLAUDE.md` permite dejar `[VERIFICAR]`
en material nuevo; aquí, sobre material que ya existe, **no se toca lo que no se confirma**.
Marca `[VERIFICAR]` únicamente si el propio deck ya lo traía.

**Granularidad.** Se verifica al nivel de **campos**, no de referencias enteras. Autores,
título, año, publicación, volumen, número, páginas, DOI y tipo se comprueban por separado y
cada uno lleva su estado. Una referencia es `VERIFICADA` solo cuando *todos* sus campos están
confirmados uno a uno; si no, es `PARCIAL`, nombrando los campos sin confirmar. Confirmar unos
campos nunca autoriza a inferir los demás.

## Procedimiento

### 1. Localizar la ficha y construir la lista de citas

- Resuelve la carpeta de la sesión desde `presentacion/admin/sesiones.csv`, columna `carpeta`. El deck es
  su `index.html`.
- Extrae el `<aside class="ficha">` de la lámina de cierre. **Si no hay ficha, para y dilo**:
  no hay bibliografía que verificar, y lo que falta es escribirla, que es trabajo del skill
  `/apuntes-sesion`, no de este.
- Parsea las entradas: `<li id="ref-CLAVE">`. La clave es lo que va detrás de `ref-`.
- Extrae todas las marcas `<cite data-ref="CLAVE">` del deck, tanto de las láminas como de los
  `<aside class="apuntes">`.
- Corre `python3 presentacion/tools/citas.py <deck>` y usa su salida, que ya calcula lo que hace falta:
  - **ROTAS**: se cita una clave que no está en la bibliografía.
  - **sin citar**: hay una entrada que nadie cita.
  - **MALFORMADAS**: marcas `<cite>` que no se pudieron leer.
- El conjunto a verificar es **toda entrada de la ficha**, la cite alguien o no. A diferencia
  del proyecto del capítulo, aquí las bibliografías son de siete a doce entradas y una entrada
  sin citar es un defecto que hay que reportar, no un huérfano que se ignora.

**Nada viene pre-verificado.** Que una referencia lleve meses en el deck, o que se haya
proyectado en clase, no es verificación. Comprueba cada entrada por sus propios méritos.

### 2. Los dos casos especiales de este proyecto

**El deck manda; `biblio/` solo sirve para contrastar.** Conviene no confundir dos papeles. La
**fuente canónica de las referencias** es siempre la ficha del deck reveal.js: de ahí sale qué
se cita y con qué texto, y no hay ni debe haber una versión PDF de las diapositivas de donde
sacarlas. Los libros de `biblio/` son otra cosa: son **autoridades contra las que verificar**,
del mismo rango que Crossref o la página del editor, con la ventaja de estar en disco. Nunca al
revés: si el libro y la ficha discrepan, se corrige la ficha, pero la lista de lo que la sesión
cita se lee del deck.

**Toda referencia cuyo texto completo esté en `biblio/` se verifica contra ese PDF, no contra
la red.** Hoy hay dos, y conviene comprobar la carpeta por si se suma alguno:

- `Artificial Intelligence A Modern Approach 3rd. Ed.pdf`, Russell y Norvig, que es la lectura
  del curso y aparece en todas las sesiones.
- `Graph_Machine_Learning_-_Claudio_Stamile__Also_Marzullo.pdf`, el segundo texto del curso,
  que cita la sesión 1 y usará el bloque de aprendizaje.

Buscar en internet los datos de un libro que está en disco es perder el tiempo y arriesgarse a
tomarlos de una edición distinta.

**La lectura del curso, siempre la primera entrada.** Es Russell y Norvig, y el curso cita la
**tercera edición**, que es el PDF de `biblio/`. Con `pdftotext` y `pdfgrep`, que están
instalados, hay que comprobar tres cosas:

1. Que el capítulo y las secciones que declara existan de verdad en la tercera edición.
2. Que digan lo que la ficha les atribuye. Si la entrada afirma "la analogía de los hermanos
   Wright, en 1.1.1", hay que abrir 1.1.1 y verla.
3. Que coincidan con lo que fija `presentacion/admin/plan/SNN.md` para esa sesión, en su apartado de
   correspondencia con la bibliografía. Si el plan y la ficha discrepan, **no elijas tú**:
   repórtalo y pregunta.

**La trampa de las páginas: el PDF y el libro no van sincronizados.** El PDF lleva por delante
la portada y el prefacio, así que sus páginas van adelantadas respecto a las que imprime el
libro. Medido: la **página 39 del PDF** es la **página 20 del libro**, un desfase de 19. Y
`pdfgrep -n` devuelve la página **del PDF**, no la del libro.

Consecuencia práctica: una ficha que dice "páginas 20 y 21" es correcta aunque
`pdftotext -f 20 -l 21` no encuentre nada. Antes de declarar mal una página, **confirma el
desfase**: extrae la página del PDF donde sí está el texto y mira qué número imprime, que en
esta edición sale como primera o última línea del texto extraído. Solo entonces compara.

No des el desfase por constante para todo el libro: compruébalo cerca de la página en cuestión.
Declarar mal una página correcta es peor que no verificarla, porque provoca una corrección que
estropea material que estaba bien.

**Nunca cambies la edición.** El curso cita la tercera, decidido el 1 de septiembre de 2026,
porque es la que el grupo tiene a la mano. La numeración de capítulos de la cuarta es distinta.
Si encuentras una entrada que anuncia la cuarta, es un error y se corrige a la tercera.

**Las fuentes que solo existen como anuncio.** Algunas sesiones citan cosas que no tienen DOI,
como los anuncios de resultados en la Olimpiada Internacional de Matemáticas de 2025. Para
esas, la fuente de verdad es la comunicación oficial de quien lo anuncia, y la entrada debe
decir de quién es el anuncio y de qué fecha. Si no puedes acceder a esa comunicación, marca la
entrada `NO VERIFICADA` y no la reescribas.

### 3. Verificar cada referencia, campo por campo

Para cada entrada, confirma contra una fuente: **autores** (apellidos e iniciales, en orden y
sin omitir a nadie), **título exacto**, **año**, **publicación** (revista, congreso, editorial),
**volumen**, **número**, **páginas**, **DOI** o identificador de arXiv, y el **tipo** (artículo
de revista, ponencia, libro, informe, preprint). Rellena un campo que falte **solo** si una
fuente lo confirma.

**Y verifica también la glosa.** Es la parte más expuesta a error, porque la escribió quien
preparó la sesión y suele afirmar algo comprobable: "el primero que pasa una revisión por
pares", "desalentó las redes neuronales durante quince años", "de la NASA y de IBM, con
licencia abierta". Cada una de esas afirmaciones es un campo más, con su propio estado. Si la
glosa afirma algo que la fuente no sostiene, repórtalo; es exactamente el tipo de error que
llega al grupo por escrito, en los apuntes de estudio.

**Prioridad de las fuentes**, usa la más autorizada que resuelva:

1. Resolutor de DOI (`https://doi.org/<doi>`) o Crossref
   (`https://api.crossref.org/works/<doi>`), y después la **página oficial del editor**: IEEE
   Xplore, ACM DL, Springer, Nature, ScienceDirect, OpenReview, o la **página de resumen de
   arXiv** para preprints.
2. **DBLP** (`https://dblp.org/search/publ/api?q=...&format=json`) para publicaciones de
   cómputo; **Semantic Scholar** y **OpenAlex** como corroboración.
3. Google Scholar solo como último recurso para *localizar* la fuente real, nunca como la
   referencia de registro.

Prefiere al menos dos fuentes independientes que coincidan para cualquier campo que **cambies**.
Registra la dirección de cada fuente que hayas usado de verdad.

### 4. Escalera de herramientas, párate en cuanto un campo quede corroborado

1. **`WebSearch`** para localizar la página autorizada, y **`WebFetch`** para leerla, o las
   API de Crossref, DBLP y OpenAlex, que devuelven JSON limpio y no bloquean.
2. Si una página está **bloqueada, de pago, servida por JavaScript o limitada por frecuencia**,
   escala a **Chromium sin ventana con Playwright**, con el ayudante que trae el skill:
   ```bash
   node "$CLAUDE_PROJECT_DIR/.claude/skills/bib-factcheck/fetch_page.mjs" "<url>"
   ```
   Imprime el texto de la página ya renderizada y sus etiquetas `<meta>` de cita. Si falta
   Chromium, corre `npx playwright install chromium` una vez.
3. Si un campo sigue sin confirmarse al final de la escalera, márcalo `NO VERIFICADO` y
   repórtalo. **No lo rellenes.**

### 4 bis. Las atribuciones históricas, en los dos sentidos

**El peligro no son las citas inventadas, que ya están prohibidas. Son las citas correctas
colgadas de una afirmación falsa.** Se añadió el 24 de septiembre de 2026, después de que la
sesión 7 citara bien a Davis, Putnam, Logemann y Loveland, y bien a Bayardo y Schrag, y aun así
presentara el aprendizaje de cláusulas como una pieza del algoritmo de mil novecientos sesenta
y dos. El aprendizaje de cláusulas llegó treinta años después, y al esqueleto con esa pieza
encima se le llama CDCL. Todas las referencias estaban verificadas.

Por eso, para cada afirmación del deck que ate una **técnica** a un **autor**, a un **año** o a
un **algoritmo con nombre**, hay que comprobarla **en los dos sentidos**:

1. **Hacia adelante:** ¿la fuente citada sostiene lo que la frase dice? Que el artículo exista
   y esté bien citado no dice nada de esto.
2. **Hacia atrás, que es el que se escapa:** ¿la técnica **ya estaba** en ese trabajo, o se le
   añadió después? Un algoritmo clásico acumula décadas de mejoras bajo el mismo nombre, y el
   material acaba atribuyéndole al original cosas que el original no traía.

Las frases que disparan la comprobación son las de esta forma: "X, de tal año", "el algoritmo
de X hace Y", "esto lo trajo Z", "tiene sesenta años y sigue siendo", "con esas dos líneas".
Cuando la respuesta sea que la técnica es posterior, **el deck tiene que decirlo en la lámina**,
no solo en el guion, porque el paquete que recibe el grupo no lleva guion.

Lo que no se pueda resolver se reporta en una lista aparte, junto a las glosas, y **no se
reescribe la afirmación por cuenta propia**: cambiar a qué se atribuye una técnica es contenido,
y lo decide Alberto.

### 5. Editar la ficha

- **Respalda primero:** copia el deck a `<deck>.bak.<marca-de-tiempo>`, con la marca que
  devuelva `date -u +%Y%m%dT%H%M%SZ`, antes de escribir nada.
- **No cambies ninguna clave.** El `id="ref-clave"` está enlazado con los `data-ref` de todas
  las marcas del deck y de los apuntes. Renombrar una clave rompe todas sus citas.
- **No reordenes la bibliografía.** `presentacion/tools/citas.py` numera por el **orden de la lista**, no por
  orden de aparición, así que mover una entrada renumera las citas de toda la sesión y deja
  desincronizado el paquete que ya se entregó. Si una entrada está mal colocada, dilo en el
  informe y deja que lo decida Alberto.
- La **lectura del curso va siempre primera**. Es la única regla de orden que existe.
- Cambia o añade un campo **solo** cuando una fuente lo confirme, y muestra **antes → después**
  de cada cambio. Deja intacto lo que no confirmaste.
- Conserva el formato de la ficha: `<em>` para títulos de publicación y de libro, `<strong>`
  solo en "Lectura del curso", volúmenes y páginas escritos con palabras
  ("volumen 59, páginas 433 a 460"), y el DOI como `doi:10.1145/365153.365168`.
- **Nunca uses el guion largo ni el punto medio**, ni en la ficha ni en el informe. Es regla del
  proyecto entera. Comprueba al terminar con
  `grep -rnP '\x{00B7}|\x{2014}' presentacion/sesiones/SNN-*/`.

### 6. Rehacer lo que depende de la ficha

La ficha no es un archivo suelto: alimenta los apuntes de estudio y el paquete que se entrega.
Después de editar, y en este orden:

```
python3 presentacion/tools/citas.py      presentacion/sesiones/SNN-.../index.html   # renumera y revisa
python3 presentacion/tools/apuntes.py    presentacion/sesiones/SNN-.../index.html   # rehace apuntes.md con la ficha
python3 presentacion/tools/empaquetar.py presentacion/sesiones/SNN-.../index.html   # rehace el paquete de presentacion/salidas/
```

`citas.py` tiene que terminar sin ROTAS, sin MALFORMADAS y sin entradas sin citar. Si la sesión
ya se subió a Classroom, avísalo en el informe: el paquete cambió y hay que volver a subirlo.

### 7. Escribir el registro

Escribe `.claude/skills/bib-factcheck/ledger.json` con el estado de cada entrada, para que una
corrida posterior vea de un vistazo qué sigue sin verificar. **Va indexado por sesión**, porque
las claves se repiten entre sesiones: `ref-curso` existe en la S01 y en la S02 con contenido
distinto. Forma:

```json
{
  "generado_utc": "<date -u -Is>",
  "sesiones": {
    "S01": {
      "turing": {"estado": "VERIFICADA", "campos_sin_verificar": []},
      "eliza":  {"estado": "PARCIAL",    "campos_sin_verificar": ["paginas"]},
      "simon":  {"estado": "NO_VERIFICADA", "campos_sin_verificar": ["año", "publicacion"]}
    }
  }
}
```

Conserva las sesiones que ya estuvieran en el registro y actualiza solo la que trabajaste.
Usa el estado `ROTA` para una clave que se cita y no existe, y `SIN_CITAR` para una entrada que
nadie cita.

### 8. Informe

Produce un informe en Markdown, imprímelo y guarda copia en
`.claude/skills/bib-factcheck/last_report.md`.

**Resumen arriba:** cuántas entradas se revisaron y cuántas se cambiaron, cuántas quedan
`VERIFICADA`, `PARCIAL` y `NO VERIFICADA`, y las listas de claves rotas, entradas sin citar y
marcas malformadas.

**Una sección por referencia:**

- la clave y la entrada corregida, tal como quedó en el HTML,
- **antes → después** de cada campo que cambió, y solo de esos,
- la dirección de las fuentes autorizadas que usaste,
- la herramienta que lo resolvió: `WebSearch`, `WebFetch`, `API de Crossref, DBLP u OpenAlex`,
  `Playwright con Chromium`, o `PDF de biblio/` para la lectura del curso,
- el estado de la entrada y de cada campo, nombrando cuáles no se pudieron confirmar y por qué:
  bloqueado, no encontrado, fuentes en conflicto.

**Listas al final:** claves rotas, entradas sin citar, marcas malformadas, y todos los campos
`NO VERIFICADO` de la sesión, para que se vea de un vistazo qué necesita una persona.

**Y una lista aparte, la de glosas:** cada afirmación de una glosa que no pudiste sostener con
la fuente. Es la que hay que leer primero, porque es la que viaja a los apuntes del grupo.

## Recordatorios

- No te salgas del alcance: no "arregles" entradas añadiendo campos que ninguna fuente
  confirma, ni reescribas la prosa de una glosa que es correcta.
- Esto verifica **los datos de las referencias** y, desde el paso 4 bis, **las atribuciones
  históricas** que cuelgan de ellas. Lo que sigue fuera de alcance es el resto de la prosa del
  deck: una afirmación sin marca de cita al lado no la mira nadie.
- No borres el respaldo `<deck>.bak.*`: queda para que Alberto lo compare.
- Registro formal y español de México, como todo el material del curso.
- Si la sesión no tiene ficha, este skill no aplica. Lo que hace falta es `/apuntes-sesion`.
