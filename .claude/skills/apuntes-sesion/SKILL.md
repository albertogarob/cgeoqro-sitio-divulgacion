---
name: apuntes-sesion
description: Escribe los apuntes de estudio de una sesión del curso Fundamentos de IA de CentroGeo, uno por lámina, los mete en el deck y rehace el paquete que se entrega al grupo, con su lector dentro. Úsalo cuando se pida escribir apuntes, notas de clase o material de estudio para los estudiantes, por ejemplo "escribe los apuntes de la S03", "haz las notas de estudio de la sesión 4" o "prepara material de lectura para el grupo". Recibe el número de sesión como argumento.
---

# Apuntes de estudio de una sesión

Escribes el apunte de cada lámina, lo insertas en el deck y rehaces el paquete. El argumento
es el número: `2`, `S02` o `sesión 2`. Si no viene número, pregúntalo antes de hacer nada.

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

## 1. Qué es un apunte, y qué no

Una lámina puede llevar cuatro bloques de notas, y cada uno tiene un destinatario distinto:

| bloque | quién lo lee | ¿viaja al paquete del grupo? |
|---|---|---|
| `<aside class="notes">` | Alberto, en el apuntador, mientras da la clase | no |
| `<aside class="corto">` | Alberto, cuando la sesión va tarde | no |
| `<aside class="didactica">` | Alberto, estudiando el tema con la lámina delante | no |
| **`<aside class="apuntes">`** | **los estudiantes, después de clase** | **sí, es el único** |

El apunte **no es el guion**. El guion está escrito para decirse en voz alta y lleva
acotaciones de conducción; el apunte está escrito para leerse, en silencio, días después,
por alguien que quizá faltó a esa clase.

Tampoco es un resumen de las viñetas. Las viñetas ya están en la lámina y el lector las tiene
al lado. El apunte dice lo que la lámina **afirma**, que es lo que no cabe en una viñeta.

## 2. Antes de escribir

Lee, en este orden:

1. `presentacion/sesiones/SNN-.../index.html`, el deck entero: sus láminas y su guion de orador. El guion
   es tu materia prima, porque ahí está el argumento de cada lámina desarrollado.
2. `presentacion/admin/plan/SNN.md`, para saber el objetivo de la sesión y su correspondencia con la
   bibliografía.
3. `CLAUDE.md` en la raíz, para el contexto del curso.

**Los apuntes se escriben cuando el deck ya está revisado y cerrado.** Si la sesión todavía
está en revisión, dilo y espera: reescribir cincuenta apuntes porque cambió una lámina es
trabajo tirado.

## 3. Qué lleva cada apunte

Tres o cuatro frases, en uno o dos párrafos. Entre sesenta y cien palabras. En este orden:

- **Qué afirma la lámina**, autocontenido, sin suponer que estuvieron en clase.
- **De dónde sale**, cuando aplique: la referencia a Russell y Norvig, tercera edición, con la
  sección; o la fuente concreta que el guion ya cite. Nunca una cita inventada.
- **Qué hay que retener**, si la lámina tiene una idea que reaparece después en el curso.
- **Una pregunta para pensar o el error típico**, solo donde la lámina lo pida. Si van en
  todas, dejan de leerse.

Van en el HTML así, justo detrás del guion corto, o del guion de orador si no hay corto:

```html
<aside class="apuntes"><p>Primer párrafo.</p><p>Segundo párrafo.</p></aside>
```

**Todas las láminas con guion hablado llevan apunte.** Se libran la portada, el cierre y los
separadores de bloque: entre los apuntes, los separadores hacen de encabezado y no
necesitan texto propio.

### La ficha de la sesión, obligatoria

La lámina de cierre lleva además la ficha, en un `<aside class="ficha">`, con dos partes:

- **Bibliografía.** Abre con la lectura del curso, Russell y Norvig en su tercera edición, con
  el capítulo y las secciones que fije `presentacion/admin/plan/SNN.md`. Sigue con las demás fuentes que la
  sesión cite, cada una con su publicación y su fecha. Solo lo que el deck cite de verdad:
  aquí no se rellena con lecturas que nadie mencionó.
- **Créditos.** La sesión y su fecha; que las diapositivas, el guion y los apuntes son del Dr.
  Alberto García Robledo, con su correo institucional; la **declaración de asistencia de IA**,
  que va justo debajo de la autoría; y CentroGeo con el programa y la orientación.

La declaración es literal y no se reescribe sesión por sesión:

> Elaborados con asistencia de un modelo de lenguaje (Claude, de Anthropic) para redacción,
> diagramas y verificación de fuentes. La selección de contenidos, las decisiones didácticas y
> la revisión final son del autor, que responde de lo que aquí se afirma.

Va en todas las sesiones, por dos razones. La primera es que el curso pide a los estudiantes
que declaren el uso de estas herramientas en una línea, y el material que reciben tiene que
hacer lo mismo. La segunda es que el estándar editorial, el de Nature Portfolio y Springer
entre otros, no admite un modelo de lenguaje como autor porque no puede responder de lo que
afirma, pero sí exige documentar su uso. La declaración deja las dos cosas claras: quién
responde y qué se usó.

**Y compromete a algo.** Decir que la revisión final es del autor solo es cierto si Alberto
recorrió la sesión. Si el deck no está revisado, avísalo al entregar en vez de dar la línea por
buena.

`presentacion/tools/apuntes.py` avisa si falta y devuelve error. La plantilla de sesión ya la trae con los
créditos resueltos, así que lo que hay que escribir es la bibliografía.

Cada entrada lleva su identificador, `<li id="ref-gencast">`, y **lo que la sesión cita se
marca donde se cita**, en el guion de orador y en el apunte, **nunca en el cuerpo de la
lámina**, que es lo único que se proyecta:

```html
En diciembre de 2024, <strong>GenCast</strong> se publica en Nature.<cite data-ref="gencast"></cite>
```

La marca va vacía: el número lo pone `presentacion/tools/citas.py` según el orden de la bibliografía. Se
marca solo donde se nombra una fuente concreta, no cada cifra, y en el apunte al final de la
frase que la usa. El apunte es donde el grupo puede pulsarla, porque es lo que viaja al paquete.

## 4. Cómo se escribe

Registro **formal y escrito**, que no es el mismo que el del guion:

- **Años, porcentajes y cifras grandes en dígitos**: 1957, 26%, 450 reglas. Igual que en el
  guion, que desde el 6 de octubre de 2026 también los lleva en cifra.
- El término en inglés entre paréntesis la primera vez que aparece: aprendizaje supervisado
  (supervised learning).
- Frases cortas, una idea por frase. Sin viñetas dentro del apunte.
- **Sin acotaciones entre corchetes** y sin ninguna indicación de conducción: eso es del guion.
- **Sin prometer nada** que Alberto no haya decidido: ni ejercicios, ni bibliotecas concretas,
  ni el formato del proyecto final.
- Nada de bibliografía, citas o cifras inventadas. Lo que no puedas confirmar va marcado con
  `[VERIFICAR]` y lo reportas al final.
- **Ninguna actividad** que Alberto no haya autorizado: ni lecturas asignadas, ni tareas, ni
  plazos. La bibliografía de la ficha no cuenta, esa sí va.
- **Nunca el día de la semana de una sesión** ni **un número de sesión exacto** en una
  referencia cruzada. Se dice "la sesión anterior", "la próxima sesión", o se nombra por su
  contenido: "cuando formulamos los problemas".
- Nunca el punto medio (U+00B7) ni el guion largo (U+2014), en ningún archivo del curso.
- No repitas la misma palabra distintiva a lo largo de los apuntes. Se leen de corrido.

Y una regla de fondo: **el apunte tiene que sostenerse solo en un teléfono**, sin la lámina
al lado, porque así es como se va a leer la mitad de las veces.

## 5. Pipeline

En este orden, y no entregues con algo en rojo:

```
python3 presentacion/tools/citas.py      presentacion/sesiones/SNN-*/index.html    # numera las citas y revisa que existan
python3 presentacion/tools/apuntes.py    presentacion/sesiones/SNN-*/index.html    # extrae apuntes.md y dice cuáles faltan
python3 presentacion/tools/verifica.py   presentacion/sesiones/SNN-*/index.html    # los apuntes van ocultos, no deben afectar
python3 presentacion/tools/empaquetar.py presentacion/sesiones/SNN-*/index.html    # rehace el paquete, con el lector dentro
python3 presentacion/tools/prueba-paquete.py                          # que el paquete no lleve nada tuyo
grep -rnP '\x{00B7}|\x{2014}' presentacion/sesiones/SNN-*/
```

`apuntes.py` **tiene que decir "no falta ninguna"**. `apuntes.md` se genera del deck y no se
edita a mano, igual que `guion.md`.

`empaquetar.py` conserva los apuntes, inyecta el lector y **audita el archivo entregado**: si
sobrevive un guion, un guion corto, una marca de recorte, el anotador o el apuntador, no
entrega el paquete, para. Esa red es la razón de que el paquete se pueda subir sin revisarlo a
mano.

## 6. Cómo lo leen

En el paquete, el lector abre el panel **de entrada**, al costado y con el apunte de la lámina
en curso, encogiendo la lámina en vez de taparla. Se cierra con Cerrar, con la tecla `A` o con
Escape, y un botón abajo a la izquierda lo devuelve. Dentro del panel, **Ver todos** abre los
**apuntes completos**: cada apunte con la miniatura de su lámina al lado, de corrido, para
leerlos o para imprimirlos o guardarlos en PDF desde el navegador.

**El material del grupo es el paquete, y nada más.** Aquí vivía un paso que convertía
`apuntes.md` en un Documento de Google "para el teléfono", y Alberto lo retiró el 27 de
octubre de 2026 con estas palabras: «quítalo, no sé de dónde salió eso». Así que no se crea
ningún documento, no se sube nada a Drive y no se arma ningún adjunto: los apuntes se leen en
el paquete, con su lector dentro, o en `presentacion/sesiones/SNN-.../apuntes.md`.

Y la regla de siempre, que no es de este paso sino del curso entero: **nunca publiques nada al
grupo**. Lo que vaya a Classroom se queda en borrador y se le reporta a Alberto para que él lo
revise y lo publique. El paquete pesado lo sube él a mano: no es un adjunto de API.

## 7. Cerrar

Abre los pendientes de la sesión, que viven en su propio archivo y no en `TODO.md`:

```
python3 presentacion/tools/todo.py NN --abrir "..."
python3 presentacion/tools/todo.py --md --todo > TODO.md
```

Reporta:

- Cuántos apuntes escribiste y cuántas láminas quedaron exentas.
- Qué quedó marcado con `[VERIFICAR]`.
- Qué decisiones de contenido tomaste que Alberto podría querer revisar.
- Si hace falta algo en Classroom, que quedó en borrador, con su liga.

Y dile cómo revisarlos: abriendo el paquete de `presentacion/salidas/`, donde el panel sale solo y basta
avanzar láminas, o leyendo `presentacion/sesiones/SNN-.../apuntes.md`, que es el mismo texto en Markdown.
