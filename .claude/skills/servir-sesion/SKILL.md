---
name: servir-sesion
description: Levanta el servidor local del curso y devuelve la liga para abrir una sesión en el navegador, en modo revisión. Úsalo cuando se pida servir, levantar, abrir o publicar una sesión en local, o simplemente su liga, por ejemplo "levanta la sesión 3", "dame el link de la S04", "quiero revisar la 5", "sirve el deck del jueves" o "apaga el servidor". Recibe el número de sesión.
---

# Servir una sesión y dar su liga

Devuelve la dirección con la que Alberto abre un deck en su navegador para revisarlo. El
argumento es el número de sesión: `3`, `S03`, `03` o el nombre de la carpeta. Sin argumento,
devuelve las de todas las sesiones que existan.


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

## Hazlo

```
python3 presentacion/tools/servir.py 1
```

Eso es todo. El script levanta el servidor si hacía falta, no hace nada si ya estaba, y
imprime las dos ligas de esa sesión: la de revisión, con `?review`, y la del deck limpio.

## Qué devolver

La liga de revisión, en un bloque de código para que sea de un clic, y debajo la del deck sin
anotador por si quiere verlo tal cual:

```
http://127.0.0.1:8932/sesiones/S01-propuesta-observatorio-enoturistico/index.html?review
```

Añade, en una línea, que al terminar basta con que diga **"aplica la revisión de la 3"**: las
notas quedan en su navegador y se leen de ahí, sin que tenga que pegar nada. El skill que las
aplica es `/corregir-sesion`.

Si además te pide que se lo abras, ábrele la pestaña con la extensión de Chrome: `navigate` a
esa misma dirección. Si contesta que hay varios Chrome conectados, no elijas tú, llama a
`switch_browser` para que él dé clic en Conectar en el suyo, y avísale.

Si en esta sesión no están las herramientas `mcp__claude-in-chrome__*`, dale la liga y ya, que
es lo que pidió. No es un fallo y no hay nada que reconfigurar para dársela.

## Lo que hay que decirle si viene al caso

- **Se revisa por esta liga, no con doble clic.** Las notas se guardan en
  `presentacion/sesiones/SNN-.../notas.json`, y quien las escribe ahí es el servidor. Sin él se quedan en el
  navegador, donde no las puedo leer, y el anotador lo avisa con una etiqueta amarilla en su
  barra. No se pierden: en cuanto abra por la liga, se suben solas. Dilo solo si menciona el
  doble clic o si no aparecen notas donde deberían.
- **La S02 necesita el servidor para algo más**: sus videos son fragmentos concatenados en un
  archivo y cada lámina salta al suyo, cosa que solo funciona servida.
- Esto es para trabajar. Lo que se entrega al grupo sigue siendo el paquete de un archivo de
  `presentacion/salidas/`, que abre con doble clic y sin servidor.

## Si algo sale mal

- **"No encuentro la sesión"**: el script lista las que hay. Comprueba el número contra
  `presentacion/admin/sesiones.csv`; puede que esa sesión todavía no esté generada, y entonces lo que toca
  es `/generar-sesion`.
- **"El puerto está ocupado por otra cosa"**: hay algo más escuchando en el 8932. Repórtaselo,
  no lo mates tú.
- Para apagarlo: `python3 presentacion/tools/servir.py --parar`.
