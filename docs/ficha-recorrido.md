# Ficha de recorrido: cómo corrigen los autores un recorrido

Los recorridos de scrollytelling los redacta el equipo de divulgación, pero quien tiene
la última palabra sobre el contenido es el investigador que firma el artículo. La ficha
de recorrido es el camino para que lo corrija **sin tocar el repositorio, sin cuenta de
GitHub y sin saber nada de Astro**: una hoja de cálculo en Drive, un renglón por paso.

Regla de reparto de trabajo, y es lo que hace que esto funcione:

- **El autor corrige**: el texto de un paso, la imagen que lo acompaña y el crédito de
  esa imagen.
- **El autor no reestructura**: no añade, quita ni reordena pasos, ni cambia de sitio el
  texto en pantalla, ni decide qué gráfico animado va en cada paso. Si quiere un paso
  nuevo, lo pide en la columna de comentarios y lo hacemos nosotros, porque cada paso
  nuevo necesita además su escena visual.

## De dónde sale el contenido

Cada recorrido vive en `src/content/recorridos/<id>.yaml`. Ese archivo es la fuente de
verdad del texto: el componente `src/components/Scrolly<Tema>.astro` ya no lleva los
textos dentro, solo la escena en SVG y su coreografía.

Cada paso tiene:

| Campo | Quién lo toca | Para qué sirve |
|---|---|---|
| `visual` | solo el equipo | Amarra el paso con su escena en el componente. Es el pegamento entre texto y gráfico. |
| `pos` | solo el equipo | Dónde se coloca el subtítulo: izquierda, derecha o centro. |
| `tipo` | solo el equipo | `foto` (imagen a sangre), `figura` (figura del artículo a un costado) o `svg` (gráfico animado). |
| `imagen` | el autor | Ruta de la foto o figura, bajo `public/`. |
| `credito` | el autor | Autoría y licencia de esa imagen. Obligatorio si hay imagen. |
| `texto` | el autor | El subtítulo que se lee en pantalla. |

Como los gráficos se enganchan por `visual` y no por número de paso, insertar un paso
nuevo en medio no descoloca las animaciones. Si alguien borra un paso cuyo `visual` usa
el componente, el build falla con un mensaje que dice exactamente cuál falta.

## El circuito completo

### 1. Sacar la ficha

```bash
npm run ficha:exportar -- utopias
```

Deja `fichas/utopias-ficha.csv` (esa carpeta no se sube al repositorio). Una fila por
paso, con las columnas de la tabla de arriba más `paso` y `comentarios`.

### 2. Subirla a Drive y compartirla

Se sube como hoja de cálculo de Google a la carpeta del investigador y se comparte con
su correo, con permiso de edición. El skill `ficha-recorrido` automatiza este tramo con
las herramientas de Drive; a mano, también vale subir el CSV y abrirlo como Hoja.

### 3. El autor corrige

Escribe sobre las columnas `texto`, `imagen` y `credito`. Lo demás lo deja igual. Lo que
no sea una corrección (un paso nuevo, una foto que quiere aportar, una duda) va en
`comentarios`.

### 4. Traerla de vuelta

Se descarga la hoja como CSV y se revisa en seco, sin escribir nada todavía:

```bash
npm run ficha:importar -- utopias fichas/utopias-ficha.csv
```

Imprime, paso por paso, el antes y el después de cada cambio, y la lista de problemas si
los hay. Cuando el resultado convence:

```bash
npm run ficha:importar -- utopias fichas/utopias-ficha.csv --aplicar
```

### 5. Comprobar y publicar

```bash
npm test
npm run build
```

Y mirar el recorrido en el navegador antes de publicar.

## Qué rechaza el importador, y por qué

Una ficha con cualquiera de estos problemas **no se aplica en absoluto**, ni siquiera en
la parte que estaba bien. Es a propósito: media corrección aplicada es peor que ninguna,
porque nadie sabe en qué estado quedó el recorrido.

- Cambió el encabezado, o el número de filas no coincide con el número de pasos.
- Se tocó `visual`, `pos` o `tipo`.
- Un texto quedó vacío, trae raya larga, dice "QRO" en vez de "Querétaro", o pasa de
  420 caracteres (no cabe en el panel de subtítulos).
- Hay imagen sin crédito, una imagen que no está en el repositorio, o una ruta que no
  empieza con `/`.
- Un paso de gráfico animado recibió imagen, o un paso de foto se quedó sin ella.

Los espacios de más y los saltos de línea que meten las hojas de cálculo se limpian
solos, así que no cuentan como cambios.

## Cuando el autor pide algo que la ficha no puede dar

- **Un paso nuevo**: lo añadimos nosotros al YAML, con su `visual`, y le damos una escena
  en el componente (una foto, una figura permitida por la licencia, o un gráfico SVG
  original).
- **Una foto suya**: primero hay que resolver de quién es y bajo qué licencia se publica
  (ver la política de derechos de autor en `CLAUDE.md`). Si entra, se guarda en
  `public/scrolly/` y ya se puede nombrar desde la ficha.
- **Una figura del artículo**: solo si la licencia del artículo lo permite, revisada
  figura por figura. Ver `docs/licencias-papers.md`.
