---
name: scrollytelling-capsula
description: Genera una cápsula de divulgación tipo scrollytelling (Scrollama + SVG original) a partir de un artículo PDF de la carpeta de Google Drive de CentroGeo Querétaro. Úsalo cuando el usuario pida "crear un scrollytelling", "una cápsula interactiva", o "un recorrido" a partir de un paper de Drive, o mencione un investigador/paper del folder para convertirlo en contenido interactivo. Encapsula todas las reglas del proyecto: acceso a Drive vía Composio, política de derechos de autor, sistema de diseño del scrollytelling, integración con las content collections y convenciones de escritura.
---

# Generar una cápsula de scrollytelling

Automatiza, de principio a fin, convertir un artículo PDF (de la carpeta de Drive de
CentroGeo Querétaro) en una cápsula interactiva de scrollytelling, respetando la
política de derechos de autor y el sistema de diseño ya establecido en este proyecto.

Lee siempre primero [CLAUDE.md](../../../CLAUDE.md): es la fuente de las reglas
(derechos de autor, convenciones de escritura, identidad visual, despliegue). Usa
[src/components/ScrollyUtopias.astro](../../../src/components/ScrollyUtopias.astro)
como **plantilla de referencia** del componente.

## Reglas no negociables

- **Derechos de autor**: asume copyright de la editorial salvo que el PDF diga acceso
  abierto (CC BY, etc.); aun con CC, mantén el enfoque conservador. Prohibido texto
  verbatim y reproducir figuras/tablas/imágenes del paper. Permitido: paráfrasis
  propia, datos y hechos reformulados (los hechos no son copyrightables), gráficos SVG
  100% originales, y cita formal (título, editorial, año, DOI).
- **Escritura**: español accesible para público general. **Nunca "QRO", siempre
  "Querétaro". Prohibido em-dashes (—)**; usa comas, puntos o reestructura.
- **Los PDFs nunca se comitean al repo**: viven solo en `/tmp`. En el repo solo van
  metadatos.
- **Revisión humana**: al terminar, recuerda al usuario que el contenido debe revisarse
  (precisión + copyright) antes de publicar.

## Paso 1. Obtener el paper desde Drive (vía Composio)

Carpeta raíz: `173mm3nHDzPU8Cjhz7HAjSxi_GzUXaCcM`, organizada en subcarpetas por
investigador. Conexión activa: `agarcia@centrogeo.edu.mx`.

1. Descubre las tools: `COMPOSIO_SEARCH_TOOLS` con casos de uso "list files in a Google
   Drive folder" y "download a PDF from Google Drive". Guarda el `session_id`.
2. Lista y navega con `COMPOSIO_MULTI_EXECUTE_TOOL` → `GOOGLEDRIVE_FIND_FILE`
   (`folder_id`, `fields: "files(id,name,mimeType)"`). Repite en la subcarpeta del
   investigador elegido (algunas contienen subcarpetas como "Revistas"/"Congresos").
3. Descarga con `GOOGLEDRIVE_DOWNLOAD_FILE` (`fileId`). Devuelve
   `downloaded_file_content.s3url` (enlace temporal, ~1h).
4. Extrae el texto en bash:

   ```bash
   cd /tmp && mkdir -p papers && cd papers
   curl -s "<s3url>" -o paper.pdf
   pdftotext -layout paper.pdf paper.txt
   ```

5. Lee `paper.txt` (título, autores, resumen, cuerpo, conclusiones). Identifica: tema,
   datos concretos citables (cifras, fechas, porcentajes), el arco (problema, hallazgo,
   implicación) y la licencia (busca "Creative Commons" / "acceso abierto").

## Paso 2. Diseñar la narrativa (7-8 pasos)

Arco sugerido: **lugar/problema → contexto → hallazgo o programa → idea central →
escala/impacto → reflexión**. Cada paso = un `texto` de subtítulo (paráfrasis breve) y,
cuando aplique, un "momento de datos" visual.

Convierte cifras del paper en momentos visuales variados (no repitas el mismo efecto):

- **Contador animado** (ej. "8 millones de visitas") con `requestAnimationFrame`.
- **Arreglo "1 de cada N"** (dots, algunos resaltados).
- **Barra** que se llena (`width` con transición).
- **Encendido escalonado** de nodos (`transition-delay: calc(var(--i) * 90ms)`).
- **Trazos que se dibujan** (`stroke-dasharray`/`stroke-dashoffset`).
- **Anillo/expansión** para el cierre.
- **Movimiento de cámara** (zoom/paneo) sobre el SVG entre pasos.

## Paso 3. Reglas de diseño del scrollytelling

Copia la estructura de `ScrollyUtopias.astro` y adáptala. Puntos que **no** debes
cambiar (son correcciones ya validadas con el usuario):

- **Full-bleed**: la cápsula usa `bleed` en `Base.astro`. El escenario (`.scrolly-stage`)
  es `position: sticky` a ancho completo.
- **No lo tape el navbar**: mide la altura del `header` por JS y ponla en
  `--stage-top`; el stage usa `top: var(--stage-top); height: calc(100vh - var(--stage-top))`.
  Reasigna en `resize`.
- **Texto = subtítulos flotantes glass, NO diapositivas**: panel
  `rgba(8,18,32,0.72)` + `backdrop-filter: blur(10px)` + borde lateral naranja.
- **Posiciones agrupadas**: no alternes cada paso (marea). Usa tandas de 2-3 por lado
  (patrón validado: `center` → 3× `right` → 3× `left` → `center`).
- **Texto central estratégico**: apertura y cierre con `pos: center`, tratamiento
  propio (centrado, más grande, borde superior en vez de lateral).
- **Camera state machine**: un objeto `camaras: Record<number,string>` con el
  `transform` por paso, aplicado a un grupo `.camera`; transición CSS suave.
- **Capas acumulativas**: grupos `.layer[data-from]` que encienden con `.on` cuando
  `step >= from`; **momentos** `.only[data-only]` que se muestran solo en su paso.
- Gráficos **SVG originales** (malla, nodos, formas estilizadas) para los momentos de
  datos, que son el centro de la narrativa.
- **Fondos fotográficos de licencia libre** como *bookends* (ver más abajo): dan la
  textura documental / NatGeo que pidió el equipo, sin usar figuras del paper.
- Tipografía del sitio: `Archivo Expanded` (títulos), `Roboto Flex` (cuerpo). Acento
  `#e8843f` / `#c45620`.

### Fondos fotográficos (patrón "bookend", validado con Ivvan)

El equipo pidió "más gráficas, fotografías e imágenes" en los recorridos. La forma que
funciona sin pelear con la visualización científica es usar fotos **solo en los pasos
narrativos de apertura/impacto/cierre**, ocultando el SVG en esos pasos, y dejar los
pasos intermedios como ciencia pura (mapa, red, barras). Arco: realidad -> abstracción
-> realidad. Referencia ya implementada: `ScrollySequias.astro`.

- **Origen de las fotos**: nunca figuras del paper. Descarga de **Wikimedia Commons**
  con licencia **CC0 / dominio público / CC BY / CC BY-SA**, verificando la licencia
  **una por una** vía la API (`extmetadata.LicenseShortName`). Wikimedia exige
  `User-Agent` propio y rechaza tamaños de thumbnail arbitrarios: usa `iiurlwidth` de la
  API para obtener un `thumburl` válido, no construyas la URL `/thumb/` a mano. Optimiza
  a ~1600px de ancho, JPEG progresivo calidad ~82, y guarda en `public/scrolly/`.
- **Atribución obligatoria** (CC BY / BY-SA la requieren): guarda un manifiesto
  `public/scrolly/CREDITOS.json` (archivo, título, licencia, autor, fuente) y muestra
  una línea discreta de créditos al final del componente (`.foto-creditos`).
- **Técnica (full-bleed real, sin letterbox)**: capa HTML `.photo-bg` (con `<img
  object-fit:cover>` + un `.photo-scrim` de gradiente para legibilidad) **detrás** del
  SVG; el SVG pierde su `<rect>` de fondo opaco y el degradado oscuro pasa al
  `background` del `.scrolly-stage`. En `aplicar(step)`: enciende la foto cuyo
  `data-photo` coincide, activa el scrim, pon `.map.hide` (opacity 0) en esos pasos, y
  **suprime los `.only` ligados al mapa** en pasos de foto (excepción: chips de cierre
  que se leen bien sobre la foto).

Scrollama se inicializa así (dispara en `onStepEnter`, offset ~0.75):

```js
import scrollama from 'scrollama';
// setStageTop(): mide header.offsetHeight -> --stage-top
// aplicar(step): set data-step, camera transform, toggle .layer.on / .only.on, animar contadores
scrollama().setup({ step: '.scrolly .step', offset: 0.75 }).onStepEnter(r => aplicar(+r.element.dataset.step));
```

### Errores comunes (aprendidos en producción)

- **El texto SVG (`<text>`) no se ajusta ni recorta solo**: se desborda y encima. En
  leyendas, ejes o etiquetas, usa textos **cortos** (ej. "D0 leve", no "D0 Anormalmente
  seco") y calcula el espaciado con margen (que la separación entre columnas sea mayor
  que el ancho estimado de la etiqueta más larga). Si la etiqueta es larga, súbela de
  tamaño de fuente hacia abajo o apílala en dos líneas con varios `<tspan>`.
- **Subtítulos vs momentos centrados**: los `only` con números/gráficos grandes van al
  centro; deja las captions a los lados (ver Paso siguiente) para que no se solapen.
  Verifica siempre con captura, no a ojo del código.
- **"EU" en papers suele ser "Estados Unidos", no la Unión Europea**: desambigua en la
  paráfrasis para no confundir al lector.

## Paso 4. Integrar con las content collections

Esquema de referencia: [docs/content-collections.md](../../../docs/content-collections.md)
y [src/content.config.ts](../../../src/content.config.ts).

1. **Investigador** (`src/content/investigadores/<slug>.md`) si no existe: `nombre`,
   `bioBreve` (honesta, sin inventar cargos), `lineasInvestigacion`, `sede: "Querétaro"`,
   `carpetaDrive` (URL de su subcarpeta). Foto y bio reales del perfil institucional en
   `https://web.centrogeo.org.mx/areas-profile/<slug>` (slug tipo inicial+apellido, ej.
   `agarcia`, `rlopez`, `jpina`, `kyanez`): descarga el avatar a
   `public/investigadores/<id>.<ext>`, ponlo en `fotoUrl`, y usa la semblanza como bio.
2. **Paper** (`src/content/papers/<slug>.md`), **solo metadatos**: `titulo`,
   `investigador` (ref), `editorial` (incluye la licencia si es CC), `anioPublicacion`,
   `doi`, `driveFileId`, `estadoPipeline: "publicado"`, `temasClave`. Nunca el texto.
3. **Cápsula** (`src/content/capsulas/<slug>.mdx`): `titulo`, `serie` (ref: `agua`,
   `el-espacio-donde-vivimos` o `sociedad-justa`), `paperFuente` (ref), `investigadores`
   (refs), `formatos`, `resumenCorto`, `fechaPublicacion`, `revisadoPor`,
   `fuenteExternaUrl` (el DOI), y `scrolly: "<clave>"`. **Deja el cuerpo MDX vacío**
   (solo frontmatter): la atribución ya aparece en "Fuente y créditos" (referencia al
   paper, `creditoProduccion` si aplica) y en el pie de página. No metas notas del tipo
   "Esta cápsula está basada en...".
4. **Registrar el componente** en el mapa de
   [src/pages/capsulas/[id].astro](../../../src/pages/capsulas/[id].astro):

   ```js
   import ScrollyMiTema from '../../components/ScrollyMiTema.astro';
   const scrollyComponents = { utopias: ScrollyUtopias, mitema: ScrollyMiTema };
   ```

   La página ya renderiza el componente en modo `bleed` cuando `capsula.data.scrolly`
   está presente, con intro y créditos en contenedores acotados. No hay que tocar más.

El landing destaca automáticamente la cápsula scrolly más reciente ("Empieza por aquí"),
no necesitas cambiar `src/pages/index.astro`.

## Paso 5. Verificar antes de terminar

```bash
# 0 em-dashes y 0 "QRO" en texto visible (excluye rutas/ids con CGeoQRO)
grep -rn "—\|QRO" src/ | grep -v "CGeoQRO\|divulgacioncentrogeo-qro" || echo "limpio"
npm run build   # debe compilar sin errores
```

Luego maneja la página con Playwright headless (instala en un scratch dir en `/tmp`,
no en el repo) y toma capturas de varios pasos para confirmar: full-bleed, que el navbar
no tape el stage, transiciones de cámara, momentos de datos y que los subtítulos no se
solapen con los gráficos centrados. Patrón:

```js
const steps = await page.$$('.scrolly .step');
for (const i of [0,1,5,7]) { await steps[i].scrollIntoViewIfNeeded(); await page.waitForTimeout(1200); await page.screenshot({ path:`/tmp/s${i}.png` }); }
```

Limpia `/tmp` (incluidos PDFs y scratch de Playwright). Verifica que **ningún PDF** haya
entrado al repo: `find . -name "*.pdf" -not -path "./node_modules/*"`.

## Paso 6. Commit

Un commit descriptivo con: el componente nuevo, las entradas de content, y el registro
en `[id].astro`. Recuerda al usuario que revise precisión y copyright antes de difundir.
