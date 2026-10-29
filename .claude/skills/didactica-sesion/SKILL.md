---
name: didactica-sesion
description: Escribe las notas didácticas de una sesión del curso Fundamentos de IA de CentroGeo, las notas con las que Alberto entiende el tema y decide cómo explicarlo, leyéndolas con la lámina delante. No son el guion hablado ni los apuntes del grupo, y nunca viajan al paquete. Úsalo cuando se pida escribir notas para entender el tema, notas didácticas, notas de estudio propias o ayuda para explicar una sesión, por ejemplo "escribe las notas didácticas de la S09", "ayúdame a entender la sesión 10 con las diapositivas delante" o "necesito notas para mí de esta clase". Recibe el número de sesión y, opcionalmente, un rango de láminas.
---

# Notas didácticas de una sesión

Escribes la nota didáctica de cada lámina y la insertas en el deck. El argumento es el
número de sesión: `9`, `S09` o `sesión 9`. Puede venir además un rango de láminas,
`9 12-20`, y entonces trabajas solo ese tramo. Si no viene número, pregúntalo antes de
hacer nada.

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

## 1. Qué es una nota didáctica, y qué no

Una lámina puede llevar cuatro bloques de notas, y cada uno tiene un destinatario distinto:

| bloque | quién lo lee | ¿viaja al paquete del grupo? |
|---|---|---|
| `<aside class="notes">` | Alberto, en el apuntador, mientras da la clase | no |
| `<aside class="corto">` | Alberto, cuando la sesión va tarde | no |
| **`<aside class="didactica">`** | **Alberto, estudiando, con la lámina delante** | **no** |
| `<aside class="apuntes">` | los estudiantes, después de clase | sí, es el único |

**Nació el 1 de octubre de 2026** y de un problema concreto que planteó Alberto: es muy
visual, para entender el tema recurre a las diapositivas, y cuando algo no le quedaba claro
en la lámina la única salida era el guion de orador, que está escrito para **decirse** en
voz alta y no para explicarle el tema a quien lo lee. Esta es la otra salida.

Se lee con la **tecla I** sobre el deck servido, al costado de la lámina o en ventana
aparte. El lector es `presentacion/plantillas/tema-centrogeo/estudio.js` y enseña dos bloques, la nota
didáctica y el apunte del grupo, cada uno con su rótulo.

**No es el guion.** El guion es lo que se dice en voz alta, con su ritmo y sus acotaciones.
La nota didáctica no se dice: se lee antes, sentado, para entender.

**No es el apunte del grupo.** El apunte lo recibe el grupo y es material del curso. Esto
es de Alberto y solo lo ve él, así que puede decir "este tramo cuesta" o "aquí me voy a
trabar", que en material del grupo no cabría.

**No es un resumen de la lámina.** La lámina está delante mientras se lee. Lo que la nota
aporta es lo que la lámina no dice: de dónde sale el concepto, por qué está aquí, y cómo se
explica.

## 2. Antes de escribir

Lee, en este orden:

1. `presentacion/sesiones/SNN-.../index.html`, el deck entero, con su guion de orador y sus apuntes. El
   guion es materia prima, porque ahí está el argumento desarrollado, pero **no lo copies**:
   está escrito para decirse.
2. `presentacion/admin/plan/SNN.md`, para el objetivo de la sesión y su correspondencia con la lectura
   del curso, que es Russell y Norvig en su tercera edición.
3. `CLAUDE.md` en la raíz, para el contexto del curso y las políticas de redacción.

**Se pueden escribir con el deck todavía abierto**, al contrario que los apuntes del grupo.
Un cambio de lámina obliga a rehacer su nota y nada más, y la nota no viaja a ningún sitio
del que haya que retirarla.

## 3. Qué lleva cada nota, y son tres cosas

En este orden, dos o tres párrafos:

**1. Qué está pasando en esta lámina, en lenguaje simple.** Qué concepto se introduce, de
qué concepto anterior se deriva, y qué problema viene a resolver. Si la lámina tiene una
fórmula, qué dice la fórmula en palabras y qué es cada símbolo. Escrito para quien ve el
tema por primera vez: ese es el lector, y es la política del proyecto, "el lector aprende el
tema hoy".

**2. El enlace con lo que se ve.** Esta es la mitad que Alberto pidió con más énfasis y la
que no existía en ninguna parte: qué viñeta corresponde a qué paso de la explicación, qué
hay que mirar en la figura y en qué orden, qué muestra el video y en qué segundo, y qué
etiqueta de la lámina esconde qué. Si la lámina tiene un diagrama, la nota dice por dónde se
entra al dibujo.

**3. Cómo explicarlo y en qué orden.** Por dónde empezar, qué hay que haber dicho antes de
llegar aquí, dónde está la trampa que se va a atravesar, y qué es lo que el grupo va a
entender mal si se cuenta en otro orden. Esta parte es consejo de docencia, es solo de
Alberto, y es la razón de que el bloque no viaje al paquete.

### La extensión la decide la dificultad, no la cuenta de láminas

De **ciento veinte a doscientas veinte palabras** en una lámina normal. Una lámina difícil
lleva lo que necesite y se dice en el reporte; una lámina de orientación lleva cuarenta
palabras y ya está.

No se fuerza el número hacia arriba ni hacia abajo. El proyecto ya tiene un pendiente abierto
por haber fijado un rango de palabras para los apuntes del grupo que no describía lo que de
verdad se escribía, y la lección es que el número sirve de referencia y no de meta.

## 4. Cómo se escribe, y aquí no se improvisa

Las políticas del proyecto que aplican a este texto, todas verificables:

- **Lenguaje simple y didáctico.** Es el único bloque que puede explicar de cero, así que se
  aprovecha: nada de dar por sabido el algoritmo que la sesión viene a enseñar.
- **Ninguna referencia sin su referente.** "Las dos expresiones", "ese paso", "la primera":
  cada una se sustituye por lo que nombra. Entre repetir el sustantivo y dejar la duda, se
  repite.
- **Toda etiqueta corta va con su contenido.** Una coordenada, el número de una regla, la
  letra de una variable: "la (1,1), la esquina de entrada por donde entró la brigada", "R5,
  *firme y sin gas, luego se puede pisar*". No se exime por repetición.
- **Las matemáticas en LaTeX**, entre `\(` y `\)`, con las funciones en redonda y las
  variables en cursiva: `\(\mathrm{Firme}(p)\)`. Nunca deletreadas en palabras. El lector las
  compone con MathJax, también en la ventana aparte.
- **El vocabulario es el del deck.** Un concepto se llama igual que en la lámina y que en las
  sesiones anteriores. Si el campo lo conoce por su palabra inglesa, se usa la inglesa.
- **Ninguna antítesis enfática**, del tipo "no es X, es Y". Se dice la afirmación y ya.
- **Ni punto medio ni guion largo**, en ningún archivo del curso.
- **Nada inventado.** Ni cifras, ni fuentes, ni atribuciones. Lo que no se pueda confirmar se
  marca con `[VERIFICAR]`. Que el texto sea privado no lo exime: una cifra falsa aquí se dice
  en voz alta en el aula.
- **No se planea participación ni se asignan actividades.** La nota puede decir cómo explicar
  algo; no reserva minutos para preguntas al grupo ni inventa ejercicios, lecturas o plazos.
  Esas dos políticas son sobre lo que la sesión hace, no sobre quién lee el texto.
- **Se pueden usar marcas de cita**, `<cite data-ref="clave"></cite>`, y `presentacion/tools/citas.py` las
  cuenta, así que una fuente citada solo aquí deja de salir huérfana.

## 5. Dónde va en el HTML

Dentro del `<section>` de su lámina, **después del apunte de estudio**, que es el último de
los otros tres:

```html
<aside class="didactica"><p>Primer párrafo.</p><p>Segundo párrafo.</p></aside>
```

**Llevan nota todas las láminas de contenido.** Se libran la portada, los separadores de
bloque y la lámina de cierre, que no tienen tema que entender. Un separador puede llevarla
si el bloque que abre necesita encuadre, y entonces la nota dice qué viene y por qué en ese
orden.

Con un rango de láminas en el argumento, solo ese tramo, y el reporte dice qué quedó sin
nota.

## 6. En sesiones largas, por tramos

Una sesión de cincuenta láminas son unas ocho mil palabras de nota. Trabaja en **tramos de
diez láminas**, insertando cada tramo en el deck antes de seguir con el siguiente, y da una
línea de avance al cerrar cada tramo. Así un fallo cuesta diez notas y no cincuenta.

## 7. El pipeline, después de escribir

Esto es lo que hay que correr, y lo que **no** hace falta, que también importa:

```bash
python3 presentacion/tools/citas.py presentacion/sesiones/SNN-.../index.html
python3 presentacion/tools/tiempos.py presentacion/sesiones/SNN-.../index.html
python3 presentacion/tools/prueba-estudio.py presentacion/sesiones/SNN-.../index.html
python3 presentacion/tools/empaquetar.py presentacion/sesiones/SNN-.../index.html
python3 presentacion/tools/prueba-paquete.py presentacion/sesiones/SNN-.../index.html
```

- `citas.py` **solo si pusiste marcas de cita**, y antes que nada, porque numera.
- `tiempos.py` para confirmar que la estimación **no se movió**: cuenta las palabras del
  guion y del guion corto por su clase exacta, así que la nota didáctica no debería cambiar
  ni un minuto. Si cambia, algo está mal escrito, probablemente la clase del `<aside>`.
- `prueba-estudio.py` comprueba que el lector sigue funcionando y, lo primero de todo, que la
  nota **no se proyecta**.
- `empaquetar.py` rehace el paquete del grupo. Su auditoría se niega a entregarlo si una nota
  didáctica sobrevive, así que esto también es una comprobación.
- `verifica.py` y `terminos.py` **no hacen falta**: el bloque va oculto y las dos herramientas
  descartan los `<aside>` antes de mirar la lámina. Dilo en el reporte en vez de correrlos por
  inercia.

## 8. Criterios de aceptación

No se reporta terminado sin esto, y cada punto con la salida del comando que lo sustenta:

1. **Una nota por lámina de contenido.** Cuenta desde disco:
   `grep -c 'class="didactica"' presentacion/sesiones/SNN-.../index.html`, y di cuántas láminas de
   contenido tiene el deck.
2. **La nota no llega al paquete.** `grep -c 'class="didactica"' presentacion/salidas/SNN-*.html` tiene
   que dar **cero**, y el paquete tiene que haberse regenerado después del deck.
3. **`prueba-estudio.py` en verde**, con su cuenta de pruebas.
4. **`tiempos.py` dice lo mismo que antes**, al minuto.
5. **Ni punto medio ni guion largo**: `grep -n -e '·' -e '—' presentacion/sesiones/SNN-.../index.html`.
6. **Las expresiones matemáticas compuestas**, no en LaTeX crudo: lo mide `prueba-estudio.py`
   en el panel y en la ventana.

## 9. El reporte

Al terminar, di:

- cuántas notas se escribieron y en qué láminas, y cuáles se quedaron sin ella y por qué;
- qué láminas necesitaron una nota más larga de lo normal, y qué las hacía difíciles;
- lo que te quedó dudoso del tema, que es información para Alberto: si al escribir la nota de
  una lámina no pudiste explicar de dónde sale algo, probablemente la lámina tampoco lo
  explica, y eso es un hallazgo sobre el deck, no sobre la nota;
- la salida de los comandos de aceptación.
