---
name: generar-sesion
description: Genera la presentación completa de una sesión del curso Fundamentos de IA de CentroGeo, con su deck reveal.js, su guion hablado y su paquete web para Classroom. Úsalo cuando se pida preparar, generar o armar una sesión del curso, por ejemplo "genera la sesión 5", "prepara la clase del jueves" o "arma S12". Recibe el número de sesión como argumento.
---

# Generar una sesión del curso

Produces el deck, el guion hablado y el paquete de un archivo de una sesión. El argumento es el número:
`2`, `S02` o `sesión 2`. Si no viene número, pregúntalo antes de hacer nada.

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

## 1. Situarte

Lee, en este orden:

1. `presentacion/admin/sesiones.csv`, la fuente de fechas, bloques, temas y carpetas destino.
2. `presentacion/admin/plan/SNN.md`, el plan detallado de esta sesión: subtemas, correspondencia con la
   bibliografía, qué material de 2024 se reutiliza, qué debe estar en pie y qué prepara.
3. `CLAUDE.md` en la raíz, para el contexto del curso y las reglas permanentes.
4. `presentacion/plantillas/tema-centrogeo/README.md`, para las clases de lámina y su capacidad.
5. **El deck de la sesión anterior**, `presentacion/sesiones/S(NN-1)-*/index.html`. Es obligatorio: hay que
   saber qué se prometió en clase para no contradecirlo. Revisa sobre todo su última lámina.

Si el plan de la sesión menciona material de 2024, ábrelo. Los decks están en
`context/2024/Slides/Shared-AIF-CGeo-Sep24/Slides/` y son `.pptx`. Se leen así:

```python
import zipfile, re
z = zipfile.ZipFile("02-AIF-IntroductionToAI.pptx")
for i in range(1, 60):
    try: x = z.read(f"ppt/slides/slide{i}.xml").decode("utf8", "ignore")
    except KeyError: continue
    print(i, [re.sub(r"\s+", " ", t).strip() for t in re.findall(r"<a:t>(.*?)</a:t>", x, re.S)])
```

## 1 bis. El algoritmo es el eje, y el fundamento un comentario periférico

**Léelo antes de proponer el índice: es lo que decide qué bloques existen.** Política del 26 de
octubre de 2026, de Alberto: **«el objetivo es exponer el algoritmo, sus pasos. Sobre el
fundamento matemático, eso se reduce a comentarios periféricos. Queremos entender al final cómo
funciona el algoritmo y entender sus parámetros, para que cuando usemos la biblioteca entendamos
a grandes rasgos cómo funciona por dentro y cómo tunearlo»**.

**Una sesión de algoritmo deja tres cosas, y son estas:**

1. **Cómo funciona, paso por paso.** Qué entra, qué hace, qué sale. Es el grueso, y va primero.
2. **Cuáles son sus parámetros y qué significan.** Los que aprende de los datos y los que
   elige una persona.
3. **Cómo se tunea en la biblioteca que lo trae.** Qué perilla mueve qué.

**La derivación de dónde salen las fórmulas NO es un bloque.** Por qué contar y dividir es el
estimador correcto, qué criterio lo justifica y cómo se despeja son **comentarios periféricos**:
una frase en la lámina del paso que los usa y una glosa en la ficha. Sin separador, sin sección
propia, sin ejemplo trabajado.

**El nombre del fundamento se dice una vez, pegado al paso que lo usa:** «a contar y promediar
se le llama máxima verosimilitud»; «a sumar uno se le llama suavizado de Laplace, y en la
biblioteca es el parámetro `alpha`». Así el grupo lo reconoce si lo lee en otro sitio, y la
sesión no gasta una sección en deducirlo.

**La prueba, al fijar el índice:** por cada bloque, pregúntate **«¿esto dice cómo funciona el
algoritmo, qué significan sus parámetros, o qué tocar en la biblioteca?»**. Si la respuesta a
las tres es no, es fundamento y se reduce a una frase.

**Y el algoritmo abre la sesión.** Si aparece pasada la primera cuarta parte de las láminas, o
si pesa menos que cualquier otro bloque, el índice está organizado alrededor de los temas y hay
que rehacerlo. En la sesión 16 el deck siguió el orden del capítulo del libro y naive Bayes no
se nombraba hasta la lámina 23 de 40; hubo que reestructurarla entera.

**El libro y los decks de 2024 son material de consulta, nunca el índice.** Alberto: «el libro
de Norvig y mis presentaciones de 2024 son solo material para que los tengas en cuenta en caso
de que te sirva, pero nunca para determinar qué temas se presentan». Un tema entra porque el
algoritmo lo necesita, aunque el libro no lo trate; y un tema que el libro trata se queda fuera
si el algoritmo no lo usa. **«Es lo que se debe enseñar», «Russell y Norvig lo presentan» y «es
lo que enseñaste en 2024» no son razones válidas por sí mismas.**

Lo que esto NO deroga: el formalismo de lo que se queda sigue entero. La regla con la que el
algoritmo decide se escribe con su fórmula y sus símbolos explicados, porque eso **es** cómo
funciona. Lo que se va es la deducción de los estimadores, no la notación.

## 2. Las tres partes que la sesión tiene que cubrir

**Política del 28 de septiembre de 2026, y se comprueba al cerrar.** Una sesión no está
completa hasta que cubre estos tres contenidos:

1. **El tema.** Los fundamentos y la explicación del algoritmo, o de la familia de algoritmos,
   que le da título a la sesión. Es el grueso.
2. **Las tecnologías que lo implementan.** Qué software lleva ese algoritmo dentro hoy, cómo se
   le escribe una regla o una entrada, y qué devuelve. **Nombrarlo en una lista no basta**: hay
   que enseñar su forma, con al menos un fragmento real de cómo se le habla. El fragmento va en
   `<pre><code>`, que queda fuera de MathJax por `skipHtmlTags`.
3. **Las aplicaciones en el contexto geoespacial.** Casos de uso, existentes o hipotéticos, de
   cómo se explota el tema en problemas geoespaciales. Un caso hipotético **se declara
   hipotético en la propia lámina**, por la misma razón por la que no se inventan cifras.

**El ejemplo de juguete con el que se enseña el algoritmo NO cuenta como parte 3**, aunque sea
geoespacial. Es el vehículo didáctico. La parte 3 es otra cosa: para qué sirve esto en un
problema real, quién lo usa o quién podría usarlo, y con qué datos. Es justo la confusión que
se tiene con un ejemplo territorial delante, así que conviene releer esta línea antes de dar la
parte 3 por cubierta.

**Son un requisito de cobertura, no de estructura.** No obligan a tres secciones, ni a ese
orden, ni a que cada parte vaya en un bloque contiguo. La división en bloques es libre. Lo que
no es libre es que los tres estén.

**Reparto y coste.** La clase dura 120 minutos y eso no se mueve, así que las partes 2 y 3 se
pagan con láminas del tema: **3 a 4 láminas para la parte 2** y **4 a 6 para la parte 3**, o
sea de 7 a 10 que salen del núcleo. Cuéntalo al proponer el índice, no al final. Si el recorte
deja el tema por debajo de lo que necesita, dilo en el reporte en vez de apretar la sesión.

**Ninguna de las tres partes puede ser de nivel 1.** Una lámina con `data-recorte="1"` se borra
en el aula sin avisar, y entonces la política se queda en el papel. La parte 3 sí puede ser de
nivel 2.

**La excepción.** Una sesión cuyo tema no es un algoritmo, como la presentación del curso o la
historia de la IA, queda fuera de las partes 2 y 3, y se dice en el reporte en vez de forzarlas.

**Al cerrar, el reporte dice qué láminas cubren cada parte, por su identificador.**

## 2 bis. La parte 2 se CORRE, no se proyecta

**Política del 19 de octubre de 2026.** La sección de tecnologías no está cubierta con el
código en una lámina: **toda sesión con sección «La herramienta» lleva una libreta de Google
Colab**, y Alberto la corre en vivo ahí. Alberto lo pidió así: «para que sea demo también
debería de mostrarles el código corriendo en Google Colab». Cinco sesiones se llaman «demo»
más el nombre de una biblioteca en `presentacion/admin/sesiones.csv`, y en 2024 esas cinco traían libreta.

**Las láminas de código se quedan**, que es lo que él eligió: la libreta corre exactamente lo
que proyectan, así la clase no se cae si falla la conexión y el paquete del grupo sigue
llevando el código.

Cómo se construye, con la sesión 14 como plantilla:

- **El código vive en un solo módulo**, `codigoNN.py`, que leen **el generador del deck y el
  generador de la libreta**. No se copia de un archivo a otro.
- **El generador de la libreta** es `demoNN.py` y escribe `demoNN.ipynb`. Celdas de markdown
  cortas entre celdas de código, y la primera celda imprime la versión de la biblioteca.
- **Las cifras del texto de la libreta salen medidas**, de `salida-*.json`, nunca tecleadas.
- **La libreta se ejecuta antes de entregarla**, y ninguna celda puede devolver error:

  ```
  ~/.venvs/jupyter-aif/bin/jupyter nbconvert --to notebook --execute --output /tmp/x.ipynb demoNN.ipynb
  ```

- **La demostración se declara en minutos**, con `data-min` en las láminas de la sección: en la
  sesión 14, `min=2` en cada una de las tres, 6 minutos en total. Sustituye el coste de su
  guion, que es lo que pasa de verdad mientras están en pantalla.
- **El guion dice cuándo pasar a Colab**, con una acotación entre corchetes seguida de la prosa
  que sí se lee: `[A Colab, la celda que ajusta el árbol.]`.

**En el guion la coordenada va SIN glosa.** `par()` mete un `<aside>` dentro, y anidado en el
`<aside class="notes">` descoloca a `anclas.py`, que lee el guion como cuerpo. La glosa es
para el cuerpo.

## 3. Proponer y esperar

Antes de escribir una sola lámina, presenta el guion de la sesión: **una línea por lámina**,
con el tipo de lámina y el minutaje aproximado por bloque. Señala qué sale de 2024 y qué es
nuevo. **Espera aprobación explícita.** Generar cuarenta láminas sin visto bueno es tirar
trabajo.

Si el plan es ambiguo, o hay una decisión de contenido que solo puede tomar Alberto,
pregúntala en este momento, no al final.

### La lámina final es la lista de materiales

**Política del 29 de septiembre de 2026.** Antes de fijar el guion, escribe la lámina a la que
la sesión llega, la que enuncia el algoritmo o el resultado, y **lista las palabras que usa**.
Ese es el temario real de la sesión. Lo que ibas a explicar y no aparece en esa lista se
justifica en una frase o no entra.

En la sesión ocho los cinco pasos de RETE usaban siete palabras. Contra esa lista se cayeron
nueve láminas y media hora de sesión, y ninguna hacía falta.

**El eje es el rendimiento, no la dificultad.** Un concepto no se corta por ser abstracto ni por
llevar fórmula. Se corta por no rendir en la lámina final. Y al revés, **lo que se queda se
queda entero**, con su formalismo y su notación. Alberto lo dijo así: no está peleado con las
matemáticas, está peleado con introducir conceptos abstractos que no rindan.

### De lo fácil a lo difícil, sin saltos

**Política del 29 de septiembre de 2026.** Ordena los conceptos de menor a mayor dificultad, y
comprueba que entre cada uno y el siguiente no haya un salto. El grupo son estudiantes de
posgrado en ciencias de la información geoespacial, **no estudiaron ciencias de la computación**,
y un concepto de la casa se les cae encima sin la escalera.

Entre una sesión completa y una fácil de entender, Alberto prefiere la fácil de entender, y lo
dijo con esas palabras. Si un concepto solo cabe metiéndolo de golpe, la salida es dejarlo
fuera, no meterlo y avisar en el guion.

La comprobación es leer los títulos de las láminas en orden y preguntarse, en cada paso, qué
necesita saber alguien para entender el siguiente. Si la respuesta incluye algo que la sesión
todavía no ha dicho, ahí está el salto.

## 4. Crear el esqueleto

No escribas el HTML desde cero ni copies `demo.html`, cuyas rutas se rompen al moverlo:

```
python3 presentacion/tools/nueva-sesion.py NN
```

Crea la carpeta y copia `presentacion/plantillas/tema-centrogeo/plantilla-sesion.html` con rutas, título,
número, tema y fecha resueltos. Ya trae la infraestructura de revisión completa: anotador con
`A`, `L`, `G` y `E`, resaltado de las citas, vista previa de cada lámina en el guion, botón de
borrado con confirmación, y apuntador con `T`.

Si la carpeta ya existe, el script se niega a sobrescribir. Pregunta antes de borrar nada.

## 5. Escribir el contenido

### Clases de lámina y capacidad real en viñetas de una línea

| Clase | Viñetas | Uso |
|---|---:|---|
| `portada` | | primera lámina, con `.titulo` y `.bajada` |
| `seccion` | | separador de bloque, solo `h2` |
| `guinda-lateral`, `verde-lateral` | 9 | contenido |
| `guinda-linea`, `verde-linea` | 8 | contenido |
| `guinda-sello`, `verde-sello` | 8 | contenido |
| `guinda-banda`, `verde-banda` | 7 | contenido |
| `cierre` | | última lámina, con `.gracias` |

El color guinda o verde distingue el bloque temático, no la jerarquía. Dentro de un mismo
bloque no vayas alternando variantes de fondo sin criterio.

### Reglas de la lámina

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

- **Nunca se dice "la lectura del curso": se dice el autor**, política del 12 de octubre de
  2026. Donde el material la nombre, va "Russell y Norvig"; donde la referencia no aporte nada,
  se quita entera. La bibliografía de la ficha no cambia: sigue abriendo con ellos.
- **Si la lámina habla de una tabla, se dibuja una tabla**, del mismo día. Acota la regla de que
  una tabla no se proyecta, que prohíbe tabular **un proceso**: una traza, un recorrido, una
  serie de valores. Una tabla de probabilidad condicional no es la tabulación de nada, es el
  objeto que se enseña, y se dibuja como tabla. La prueba: si la lámina la llama tabla, dibújala
  como tabla.

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
- **El término se dice como lo dice el campo**, política del 28 de septiembre de 2026: si el
  concepto ya se conoce por su palabra inglesa, se usa la inglesa, no una traducción que nadie
  emplea. La prueba es cómo lo llama la biblioteca del tema y la lectura del curso. No deroga la
  regla del idioma: cambia cuál de los dos es el término y cuál la glosa.
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
- **Resaltado a nivel de lámina, no de viñeta.** Una o dos palabras clave por lámina, las que
  la condensan. En listas de categorías paralelas, ninguna: resaltarlas todas equivale a no
  resaltar nada, porque el resalte es contraste.
- Un título que ocupe tres líneas se encima con el cuerpo. Acórtalo.
- **No modifiques el tema.** `presentacion/plantillas/tema-centrogeo/` es un port validado de la plantilla
  oficial de Secihti y CentroGeo, y cambiarlo afecta a las 30 sesiones. Si algo no cabe, el
  problema es el contenido. Si de verdad hace falta tocarlo, pregunta primero.
- No escribas etiquetas HTML literales dentro de comentarios: las herramientas leen el archivo
  con expresiones regulares y las tomarían por láminas reales.

## 6. Escribir el guion

Cada lámina lleva su guion hablado completo, listo para leerse en voz alta, en su bloque de
notas de orador. El deck es la fuente única: `guion.md` se genera, nunca se edita a mano.

- Prosa hablada. Frases cortas, una idea por frase.
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
- Sin viñetas dentro del guion.
- **Cada pieza de la lámina lleva su párrafo en el guion**, política del 12 de octubre de 2026.
  Cada viñeta, la línea en llano, cada fórmula, cada dibujo, cada video y cada bloque de código
  tienen al menos un párrafo que habla de ellos. Quedan fuera la portada, los separadores de
  sección, la de agradecimiento y la de bibliografía. **Un párrafo que cubre dos viñetas de
  corrido no vale**: se parte en dos, que además es lo de una idea por frase. Lo comprueba
  `presentacion/tools/anclas.py`, que tiene que decir **TODA PIEZA DE TODA LÁMINA TIENE SU PÁRRAFO EN EL
  GUION** y devuelve error si no. Para la fórmula que es una **cuenta**, y que por política no
  se lee en voz alta, su párrafo se marca con `@formula ` delante en el generador y queda
  anclado a ella. La razón de la regla es doble: una pieza sin párrafo es una pieza de la que
  no se dice nada, y además la sincronía del guion con la lámina la deja apagada mientras
  Alberto habla.
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
- Bloques de tres a seis líneas: la ventana del apuntador es angosta.
- Los bloques de duración fija que no dependen del guion, como una ronda de presentaciones,
  un descanso o una discusión, se declaran con `data-min` en el `<section>`.

### El plan de recorte

Una sesión que va larga se recorta en clase, y eso se prepara al escribirla, no en el aula.
Son dos cosas, y las dos se hacen **lámina por lámina, sin excepción**: clasificarla y
escribirle su versión corta. Ninguna sesión se entrega sin las dos.

#### Clasificar las láminas

Toda lámina queda en uno de los tres niveles. El núcleo se declara **no poniendo nada**; los
otros dos van en `data-recorte` del `<section>`:

| Marca | Qué es | Cuándo se pone |
|---|---|---|
| sin marca | núcleo | si al perderla la sesión no cumple su objetivo, o la siguiente se rompe porque la da por vista |
| `data-recorte="1"` | se pierde y nadie se entera | repite o refuerza algo ya dicho, o es el segundo ejemplo de lo mismo |
| `data-recorte="2"` | se pierde, pero hay que decirlo | el contenido importa y no es hoy, y nada de hoy depende de él |

Se decide con dos preguntas. Primera: si la quito, ¿la sesión sigue cumpliendo el objetivo que
le fija `presentacion/admin/plan/SNN.md`, y la sesión siguiente sigue en pie, o la da por vista en su
apartado de "qué debe estar en pie"? Si alguna respuesta es no, es **núcleo** y ahí termina.
Segunda, solo si las dos fueron sí: al quitarla, ¿hay que decirle algo al grupo? Si no hay que
decir nada, es **nivel 1**. Si hay que anunciar que se retoma después, porque se prometió o
porque el contenido importa, es **nivel 2**.

La mayoría del deck es núcleo. Un reparto sano son unas cinco o seis láminas de nivel 1,
repartidas por la sesión, y un bloque de nivel 2 al final, que es el recorte más limpio porque
nada posterior depende de él. **Si te sale marcado más de un tercio del deck, el criterio está
mal**: no puede ser prescindible un tercio de la clase. Si dudas, es núcleo.

Al entregar, di cuántas quedaron en cada nivel y por qué las de nivel 2.

#### Escribir el guion corto de cada lámina

**Todas las láminas con guion hablado llevan su versión corta**, no solo las marcadas. Va en un
`<aside class="corto">` justo detrás del `<aside class="notes">` de esa lámina:

```html
<aside class="corto"><p>El argumento en una frase, y el enlace con la siguiente.</p></aside>
```

Dos o tres frases, entre treinta y cuarenta y cinco segundos leídas en voz alta. Mismas reglas
de registro que el guion largo, porque se lee igual, en clase y en voz alta.

**No es un resumen de las viñetas.** Es el argumento de la lámina en una frase, y el enlace con
la siguiente. Lo que se dice de ella cuando hay prisa, no lo que pone en pantalla.

Que la lleven también las de núcleo tiene dos razones, y las dos importan:

- El núcleo no se pierde nunca, pero **sí se puede contar corto** si el día se tuerce de
  verdad. Sin versión corta escrita esa salida no existe, y la única alternativa sería
  saltarse algo que no se puede saltar.
- Escribirla obliga a saber cuál es el argumento de esa lámina en una sola frase. **Si no te
  sale, la lámina no tiene un argumento**: o le sobra material, o hay que partirla en dos, o no
  debería estar. Es la mejor prueba de que el deck está bien cortado, y sale gratis.

Quedan fuera la portada, el cierre y los separadores de bloque, cuyo guion ya son dos frases.
Los bloques con `data-min` también quedan fuera: duran lo que declaran, y **el recorte no
los toca**. En una sesión normal el único es la portada, que declara los tres minutos de
saludo y de comprobar que se ve y se oye.

`tiempos.py` lista las láminas que se quedaron sin ella. **Esa lista tiene que salir vacía.**

Nada de esto descuenta de los 120 minutos: la sesión se escribe para durar lo que dura, y el
recorte es la red por si el día se tuerce.

### La ficha de la sesión

La lámina de cierre lleva su ficha, en un `<aside class="ficha">`, con la **bibliografía** y los
**créditos**. Es obligatoria en todas las sesiones y la plantilla ya la trae con los créditos
resueltos: lo que hay que escribir es la bibliografía, que abre con la lectura del curso,
Russell y Norvig en su tercera edición con el capítulo y las secciones que fije
`presentacion/admin/plan/SNN.md`, y sigue con las demás fuentes que la sesión cite, con su publicación y su
fecha. Solo lo que la sesión cite de verdad.

Cada entrada lleva su identificador, `<li id="ref-gencast">`, y se marca donde se nombra la
fuente con `<cite data-ref="gencast"></cite>` vacío, **en el guion de orador y en el apunte,
nunca en el cuerpo de la lámina**: proyectada se lee como la llamada de una nota al pie que no
existe, porque la bibliografía vive en la ficha y la ficha no se proyecta.
El número lo pone `presentacion/tools/citas.py` según el orden de la bibliografía, y las recoge estén donde
estén. Se marca donde se nombra una fuente concreta, no en cada cifra.

**La marca se compone entre corchetes y en la línea base**, `ACT [6]`, desde el 29 de septiembre
de 2026. Volada y pegada a la palabra se leía como parte del nombre: Alberto leyó "ACT6" en el
guion y entendió que el sistema experto se llamaba así. Los corchetes los pone el CSS del tema y
del lector de apuntes, no el HTML, para que el contenido del `<cite>` siga siendo el número a
secas. **Y `guion.py` se corre después de `citas.py`**: al revés, `guion.md` sale con las citas
vacías.

### Duración

La clase dura 120 minutos y `presentacion/tools/tiempos.py` tiene que decir **ALCANZA**, con la banda
estimada entre 105 y 130 minutos.

**Lo que llena la sesión son las láminas, no las palabras.** Medido en el aula, cada lámina de
contenido cuesta unos tres minutos, de los que solo uno sale del guion escrito. El resto es
pasarla, dejar que la lean, mirar el diagrama, ampliar de viva voz y contestar. Por eso una
sesión corta no se arregla estirando el guion, y una larga no se arregla podándolo: lo que se
mueve es el número de láminas.

Las cifras de diseño. **Una sesión se dimensiona como exposición continua**, sin reservar
ni un minuto para cortes de participación, que están prohibidos salvo que Alberto los pida
para esa sesión. Con el modelo calibrado de `presentacion/admin/ritmo.json`, eso da:

- **De 45 a 49 láminas en total**, de las que 36 a 40 son de contenido.
- Unas **5,400 a 6,000 palabras habladas**, a razón de 150 por lámina.
- Por debajo de 35 láminas de contenido `tiempos.py` dice FALTA MATERIAL, y por encima de
  41 dice AJUSTADO.
- Un bloque con `data-min` **sustituye** láminas, no se suma. El único de una sesión normal
  es la portada, con sus tres minutos.

Mide con `tiempos.py` a media escritura, no al final. Si falta tiempo, agrega láminas; si
sobra, quita láminas. No estires ni podes el guion para cuadrar el número.

El modelo está calibrado con sesiones ya impartidas, en `presentacion/admin/ritmo.json`. La sesión 3 de 2026
se escribió con el modelo anterior, que solo contaba palabras, y salió del doble de larga: dio
104 minutos estimados y en las dos horas llegó a su lámina 46 de 77.

## 7. Reglas de estilo del guion

Registro **formal**. Salieron de correcciones directas de Alberto y no son negociables.

### Prohibido

- Las palabras "incómoda" y "brutal", en cualquier forma.
- **Énfasis retórico añadido**: aposiciones y superlativos acumulados que solo buscan efecto,
  del tipo "la pregunta más básica y más incómoda del curso", "y no es retórico", "y conviene
  decirlo". No adornes la frase para darle peso.
- **Antítesis enfática**: "no dice que algo falla: dice qué falla", "no es X, es Y", "no se
  trata de A, sino de B". Se dice la afirmación y ya. Vale igual para el guion y para el cuerpo
  de la lámina, y es el tic al que se vuelve en los remates de lámina y los cierres de sección.
  Al revisar, buscar los dos patrones: `no ... : ` y `no ... sino`.
- **Empatía impostada**: "porque lo que importa hoy son ustedes", "no se asusten", "nadie los
  va a juzgar".
- **Frases coloquiales**: "trabajo tirado a la basura", "no vuelve a aflojar", "para que lo
  tengan en la cabeza", "qué demonios", "el que sale perdiendo es el que se quedó callado".
- **Autodesprecio y familiaridad**: "lo más probable es que sea culpa mía", "levanten la mano,
  escriban en el chat".
- **Presión sobre el grupo**: "este es el momento de preguntar, porque no vamos a volver".
- **Muletillas de atención**: "fíjense", "ojo con esto", "acuérdense", "guarden esto",
  "piénsenlo", "de verdad".
- **Repetir la misma palabra distintiva** a lo largo de la sesión. Revísalo antes de entregar.
- El **punto medio** (U+00B7) y el **guion largo** (U+2014), en cualquier archivo del curso.
  Separa con comas, puntos o reestructurando, y en listas en línea con punto y coma. No los
  sustituyas por otro adorno como la barra vertical. Este documento los nombra por su código
  justamente para no contenerlos.

### Nada de actividades, días ni números de sesión

Tres prohibiciones que valen para la lámina, el guion, el guion corto y los apuntes. Alberto las
pidió el 17 de septiembre de 2026 al revisar la sesión 5 ya impartida.

- **Ninguna actividad que él no haya autorizado para esa sesión**: ni lecturas asignadas, ni
  tareas, ni entregas, ni plazos, ni ejercicios. La lámina de cierre es donde se cuelan, así que
  revísala siempre. **La bibliografía de la ficha no cuenta como actividad** y sigue siendo
  obligatoria: lo prohibido es convertirla en un encargo del tipo "Lectura: capítulo 3".
- **Nunca el día de la semana de una sesión**: ni "el jueves recorrimos", ni "el martes empieza
  el bloque", ni "nos vemos el martes". Se dice "la sesión anterior", "la próxima sesión".
- **Nunca un número de sesión exacto en una referencia cruzada**: ni "lo vimos en la sesión 3",
  ni "vuelve en la sesión 22". Se nombra por su contenido: "cuando formulamos los problemas",
  "en el bloque de metaheurísticas". La excepción es la identidad del propio deck: la portada y
  la ficha sí llevan su número.

Las dos últimas tienen la misma razón: el calendario se mueve, y un asueto o una clase que se
salta dejan el material diciendo un día y un número que ya no son.

Antes de entregar, barre el `index.html` buscando los cinco días hábiles y la palabra "sesión"
seguida de un número o de su nombre en letra.

### La lámina de Bibliografía, obligatoria

**El deck termina con una lámina titulada "Bibliografía", y va al final de todo, después de la
de agradecimiento.** Alberto lo fijó el 17 de septiembre de 2026 para las 30 sesiones: la deja
en pantalla mientras responde preguntas.

- Lleva las referencias **completas**, en un `<ol>`, en el mismo orden que la ficha. Ese orden
  es el que fija el número de las marcas de cita, así que los números coinciden.
- **Sin las glosas de la ficha.** En la ficha se explica para qué sirve cada fuente; en la
  lámina va solo la referencia.
- Una referencia completa no cabe con el cuerpo del tema. La lámina necesita su propio tamaño,
  y **la regla va sobre el `li`, no sobre el `.cuerpo`**: el tema fija el tamaño en el propio
  `li`, así que una regla en el padre no se hereda y no hace nada. Conviene ensanchar también
  la caja al 95.19%, como los diagramas.
- Lleva guion, guion corto y apunte como cualquier otra lámina.

### Cómo se nombra Alberto

- Se presenta como **el Dr. Alberto García Robledo**.
- Se dice "ejercicios de código", nunca "libretas de código".

### Qué no prometer

Nada que Alberto no haya decidido:

- **Ejercicios y tareas**: no digas "van a programar" ni describas el formato de las entregas.
- **Bibliotecas concretas**: se nombran, y se enseña su forma, **en la parte de tecnologías
  de la sesión**, desde que Alberto lo confirmó el 28 de septiembre de 2026. Z3, Experta,
  Simpful, PyBBN, hmmlearn y Keras entran ahí cuando le toca a su tema. Fuera de esa parte
  sigue valiendo lo de antes: no se da por hecho que el grupo vaya a instalar nada, ni se
  promete una demostración en vivo que él no haya decidido.
- **El proyecto final**: no supongas que consiste en construir algo ni describas su alcance.

### Rigor

Nada de bibliografía, citas o cifras inventadas. Si citas, que sea verificable. Lo que no
puedas confirmar va marcado con `[VERIFICAR]` en el guion, y lo reportas al final.

## 8. Pipeline obligatorio

En este orden, y no entregues con algo en rojo:

```
python3 presentacion/tools/ids.py       presentacion/sesiones/SNN-*/index.html    # tras agregar láminas
python3 presentacion/tools/citas.py     presentacion/sesiones/SNN-*/index.html    # numera las citas y revisa que existan
python3 presentacion/tools/parcelas.py  presentacion/sesiones/SNN-*/index.html    # las parcelas que nombra cada lámina
python3 presentacion/tools/anclas.py    presentacion/sesiones/SNN-*/index.html    # ancla el guion a las piezas de la lámina
python3 presentacion/tools/apuntes.py   presentacion/sesiones/SNN-*/index.html    # extrae apuntes.md, la lista sale vacía
python3 presentacion/tools/guion.py     presentacion/sesiones/SNN-*/index.html    # extrae guion.md, DESPUÉS de citas.py
python3 presentacion/tools/verifica.py  presentacion/sesiones/SNN-*/index.html    # desbordes y colisiones
python3 presentacion/tools/terminos.py  presentacion/sesiones/SNN-*/index.html    # términos sin definir en pantalla
python3 presentacion/tools/gordas.py  presentacion/sesiones/SNN-*/index.html    # láminas gordas de texto
python3 presentacion/tools/figuras.py   presentacion/sesiones/SNN-*/index.html    # que las figuras se lean proyectadas
python3 presentacion/tools/titulos.py   presentacion/sesiones/SNN-*/index.html    # TODOS LOS TÍTULOS EN UNA LÍNEA
python3 presentacion/tools/barrido.py   presentacion/sesiones/SNN-*/index.html    # el resaltado, de arriba hacia abajo
python3 presentacion/tools/verifica-lamina-por-lamina.py presentacion/sesiones/SNN-*/index.html   # el que sí mide
python3 presentacion/tools/tiempos.py   presentacion/sesiones/SNN-*/index.html    # duración
python3 presentacion/tools/empaquetar.py presentacion/sesiones/SNN-*/index.html      # paquete para el grupo
python3 presentacion/tools/classroom.py  SNN                            # la carpeta de Classroom
python3 presentacion/tools/cambios.py   SNN                            # toma la foto de referencia
grep -rnP '\x{00B7}|\x{2014}' presentacion/sesiones/SNN-*/
```

En una sesión recién generada `cambios.py` no tiene con qué comparar, así que
toma la foto y calla. A partir de ahí, cada ronda de correcciones marcará lo que
cambie desde la última vez que Alberto lo dio por visto.

**`guion.py` va después de `citas.py`**, no antes: al revés las marcas de cita todavía no tienen
número y `guion.md` sale con las citas vacías.

`verifica.py` debe decir "SIN DESBORDES NI COLISIONES". El desborde recorta texto en silencio
y no se nota hasta estar frente al grupo.

`tiempos.py` marca con `r1` y `r2` las láminas recortables y dice cuánto dura la versión corta
de cada una. Al final lista las que no tienen ninguna: **esa lista tiene que salir vacía**, y
mientras no lo esté la sesión no está terminada.

Los identificadores se escriben por duplicado, en `id` y en `data-sid`. Reveal le quita el
`id` a la lámina visible mientras está en pantalla, así que el anotador lee `data-sid`.

## 9. Cerrar

Abre los pendientes de la sesión, que viven en su propio archivo y no en `TODO.md`:

```
python3 presentacion/tools/todo.py NN --abrir "Revisión de Alberto" "Subir el paquete a Classroom"
python3 presentacion/tools/todo.py NN --abrir "..." --transversal   # si afecta a las 30 sesiones
python3 presentacion/tools/todo.py NN --decidir p3                  # lo zanjado, se guarda como registro
```

Como mínimo entran ahí la revisión de Alberto, la entrega a Classroom, lo que siga marcado
con `[VERIFICAR]` y cualquier particularidad del deck que costaría redescubrir, por ejemplo
de dónde salieron sus medios o por qué sus tiempos no son los del original.

`TODO.md` no se edita a mano: es una vista de todos los pendientes que se regenera con
`python3 presentacion/tools/todo.py --md --todo > TODO.md`.

Reporta:

- Duración estimada y número de láminas.
- Cuántas láminas quedaron en cada nivel de recorte, y por qué las de nivel 2.
- Qué se reutilizó de 2024 y qué se escribió desde cero.
- Qué quedó marcado con `[VERIFICAR]`.
- Qué decisiones tomaste que Alberto podría querer revisar.

Y recuérdale cómo revisarla. **Servida, no con doble clic**: sin servidor las notas se quedan
en el navegador y no llegan a `presentacion/sesiones/SNN-.../notas.json`, que es de donde se leen.

```
python3 presentacion/tools/servir.py NN
```

`A` anota la lámina, `G` abre el guion completo, con la vista previa de cada lámina y el botón
para reescribir el guion, y también se anota ahí, `L` abre la lista de notas y lleva a
cualquiera de ellas, `T` abre el apuntador para presentar. El texto citado queda resaltado en
amarillo: un clic abre su nota para editarla y la marca en naranja mientras tanto. Al terminar
le basta con decir que ya revisó; `E`, que exporta al portapapeles, es solo el respaldo para
cuando revisó sin servidor.

## 10. Cómo llegan las correcciones

Las notas quedan en `presentacion/sesiones/SNN-.../notas.json` y se leen con `python3 presentacion/tools/notas.py NN`.
Si revisó sin servidor, en cambio, te pega un bloque como este:

```
## Notas de revisión, S02-...
- **evaluacion**  (cita: "50%")
  subir tareas a 60
- **la-pregunta-de-fondo**  (guion)  (cita: "...")
  quita esto
```

Cada punto va anclado al identificador de la lámina, no a su número. Las marcadas con
`(guion)` son sobre el guion hablado; las demás sobre lo que se ve en pantalla.

**Eso no se aplica desde aquí: se aplica con el skill `/corregir-sesion`**, que sabe leer el
bloque, corregir el deck, correr el pipeline y dejar el navegador solo con lo pendiente.

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
