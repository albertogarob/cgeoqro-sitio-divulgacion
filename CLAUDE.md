# CGeoQRO - Sitio de Divulgación

## Contexto del proyecto

Prototipo de sitio web construido con **Astro** para la divulgación científica, dirigida
principalmente al público general, del conocimiento generado por investigadores del
**CentroGeo Querétaro (CentroGeo QRO)** a partir de sus publicaciones académicas.

Astro debe funcionar no solo como generador de sitio estático, sino también como un
**CRM ligero**: gestión de investigadores, sus papers, y los contenidos de divulgación
derivados de cada uno (video, diapositivas, texto, cápsulas de conocimiento, etc.).

CentroGeo es el Centro de Investigación en Ciencias de Información Geoespacial, vinculado
a la Secretaría de Ciencia, Humanidades, Tecnología e Innovación del gobierno mexicano.
CentroGeo Querétaro es una de sus sedes. El sitio institucional central
(https://www.centrogeo.org.mx/) estaba, al momento de este análisis, en construcción y
no expone contenido sustantivo sobre la organización ni sedes adicionales; retomar su
revisión cuando el sitio esté completo (ver sección de Identidad Visual).

## Stack técnico

- **Astro** como framework principal (generación estática + capa ligera de CRM).
- Sin backend definido aún: evaluar necesidad real antes de introducir uno (DB, API,
  auth) solo cuando el CRM lo requiera, no de forma anticipada.

## Despliegue: GitHub Pages (restricción obligatoria mientras no se diga lo contrario)

El sitio se lanza inicialmente en **GitHub Pages**. Esto impone restricciones duras
sobre lo que se puede construir, y deben respetarse en todo el desarrollo:

- **100% estático**: `output: 'static'` en `astro.config.mjs`. Nada de SSR, API
  routes con lógica de servidor, ni `output: 'server'`/`'hybrid'`. Cualquier
  funcionalidad "dinámica" (formularios, búsqueda, panel de producción del CRM) debe
  resolverse client-side o con servicios externos (ej. Formspree, Algolia), nunca con
  cómputo en servidor propio.
- **Base path**: el sitio vive en un subpath (`/<repo>/`), no en la raíz del dominio,
  salvo que el repo se llame `<org>.github.io`. Todos los enlaces internos y rutas de
  assets deben construirse con `import.meta.env.BASE_URL` (o helpers de Astro como
  `base` en `astro.config.mjs`), nunca hardcodeados con `/`.
- **`trailingSlash: 'always'`**: GitHub Pages resuelve `/ruta/` a `/ruta/index.html`;
  sin la barra final se producen 404 intermitentes.
- **Sin secretos en el cliente**: sin backend propio, cualquier API key (ej. para
  transcripción, generación de video/audio con IA) debe usarse solo en tiempo de
  build (GitHub Actions secrets) o en un servicio externo, nunca embebida en el
  bundle del navegador.
- **Rutas sensibles a mayúsculas/minúsculas**: el file system del build y el CDN de
  GitHub Pages distinguen mayúsculas; mantener slugs siempre en minúsculas.
- **Despliegue**: vía GitHub Actions (`.github/workflows/deploy.yml`, usando
  `withastro/action` + `actions/deploy-pages`), no despliegue manual.
- Repo actual: https://github.com/albertogarob/cgeoqro-sitio-divulgacion (**privado**).
  GitHub Pages en repos privados de cuentas personales requiere plan GitHub
  Pro/Team/Enterprise; con plan gratuito, el workflow `deploy.yml` no podrá publicar
  hasta que el repo se haga público o se confirme un plan compatible.
- Esta restricción es el estado inicial, no necesariamente permanente: si más
  adelante se requiere backend real (ej. CRM con autenticación, base de datos), se
  debe migrar a otro hosting (Vercel, Netlify, servidor propio) y esta sección debe
  actualizarse.

## Fuente de datos (insumos)

Los papers completos en PDF están almacenados en Google Drive, organizados en carpetas
por nombre de investigador:

https://drive.google.com/drive/folders/173mm3nHDzPU8Cjhz7HAjSxi_GzUXaCcM

Por ahora este es un recurso externo manual; no hay sincronización automatizada. Antes
de construir cualquier pipeline de ingestión, definir cómo se accederá de forma
reproducible (descarga manual puntual, script con credenciales de servicio de Google
Drive API, o carpeta local sincronizada).

## Política de derechos de autor (regla obligatoria)

**Todos los papers están protegidos por derechos de autor de las editoriales que los
publicaron**, independientemente de que el autor sea investigador de CentroGeo. Esta
regla aplica a cualquier tarea de generación de contenido en este proyecto, sin
excepción:

**Prohibido:**
- Reproducir bloques de texto verbatim (citas largas, párrafos completos, abstracts
  copiados tal cual).
- Extraer o reutilizar imágenes, figuras, gráficas o tablas originales del PDF.
- Cualquier material que pueda constituir infracción de copyright de la editorial.

**Permitido:**
- Resúmenes en lenguaje propio y paráfrasis conceptual de los hallazgos.
- Generación de ilustraciones/animaciones/video **desde cero**, no derivadas
  visualmente de las figuras originales del paper.
- Citación formal (referencia bibliográfica completa, DOI) sin reproducir el
  contenido protegido.

Cualquier subagente o script que genere contenido de divulgación debe verificar que
cumple esta política antes de publicar o entregar el resultado.

## Referencias existentes de estilo (precedente del equipo)

Ivvan, compañero del equipo, ya generó dos recursos de divulgación a partir de papers
(aparentemente con apoyo de IA): un video y unas diapositivas, publicados en:

- https://sites.google.com/centrogeo.edu.mx/divulgacioncentrogeo-qro/temas/el-espacio-donde-vivimos
- https://sites.google.com/centrogeo.edu.mx/divulgacioncentrogeo-qro/temas/sociedad-justa

Estas páginas forman parte de un sitio en Google Sites organizado en tres líneas
temáticas: **Agua**, **El espacio donde vivimos**, y **Sociedad justa**.

**Cerrado 2026-07-21** (inspección con Playwright headless, ya que el fetch estático
no basta — Google Sites carga el contenido embebido vía llamadas autenticadas a la
API de Google en el navegador):

**"Sociedad justa"** — un video (`usa_vs_china_sigloxxi_joaquin_pina.mp4`, título en
pantalla "USA vs China: Siglo XXI") alojado en Google Drive con permisos públicos
("cualquiera con el link"), embebido vía `drive.google.com/file/d/<id>/preview`.
Estilo animación tipo pizarra/whiteboard con iconos dibujados a mano. Basado en el
capítulo de José Joaquín Piña Mondragón, *"Estados Unidos vs. China ¿Conflicto
comercial o lucha por el liderazgo tecnológico en el siglo XXI?"*, del libro *El
T-MEC en el marco de la confrontación China-Estados Unidos* (Instituto para el
Desarrollo Industrial y la Transformación Digital A.C.). Al ser un archivo público
de Drive, **esta URL de `/preview` sí se puede embeber en un `<iframe>` externo**
(verificado cargándola en un contexto de navegador sin autenticación: responde 200
y reproduce el video). Ejemplo aplicado en
`src/content/capsulas/usa-china-siglo-xxi.mdx`.

**Advertencia (observada 2026-07-21 en producción)**: los embeds de `/preview` de
Drive están sujetos a una **cuota de reproducción diaria por archivo** propia de
Google Drive; tras varias cargas seguidas del mismo archivo (durante nuestras
pruebas automatizadas) el iframe mostró "No se pudo cargar el video". Es una
limitación de Drive, no del código. Por eso `capsulas/[id].astro` agrega un enlace
de respaldo ("Ábrelo en una pestaña nueva") junto al iframe. **Para contenido de
video que sí generemos nosotros en el pipeline de producción, preferir alojarlo en
YouTube (no listado o público) en vez de Google Drive**, ya que YouTube no tiene
esta cuota y es el estándar de facto para embeds de video en la web.

**"El espacio donde vivimos"** — *no* es un video simple, es un **widget interactivo
de storytelling** ("Historias entrelazadas en la periferia", basado en el paper de
Fabricio Espinosa Ortiz, 2024): slides ilustrados con estilo de ilustración
generada por IA, música ambiental opcional, texto narrativo en lenguaje llano, y un
recuadro fijo "¿Por qué importa este conocimiento?" en cada slide. Se sirve a
través de un proxy interno de Google Sites (`*-atari-embeds.googleusercontent.com`,
subdominio dinámico por sesión) — **no tiene una URL pública estable para embeber**,
y además la página completa de Google Sites envía `X-Frame-Options: DENY`, por lo
que tampoco se puede iframe-ar la página en sí.

**Conclusión práctica**: este segundo formato (ilustración propia + paráfrasis +
callout de "por qué importa") es exactamente el patrón de cápsula que ya definimos
en este documento (ver "Pipeline de generación de contenido" y "Conceptos de
divulgación"). En vez de intentar reembeberlo, lo replicamos como plantilla propia
para nuestras cápsulas.

## Identidad visual institucional

**Actualizado 2026-07-21**: el sitio central de CentroGeo (https://www.centrogeo.org.mx/)
ya no está en construcción. Tiene un sistema de diseño real con variables CSS
propias, extraído de `https://www.centrogeo.org.mx/css/styles.css`. Copia de
referencia guardada en [docs/referencia-visual/](docs/referencia-visual/)
(`centrogeo-styles.css`, `logo_centrogeo_wide.svg`, `logo_centrogeo_wide-white.svg`).

**Tipografía:**
- Títulos: `"ingra-wide"` (vía Adobe Typekit, `use.typekit.net/etx4aom.css`), pesos 300–700.
- Cuerpo: `"Roboto Flex"` (Google Fonts), pesos 300–700.
- Topbar/footer gubernamental (gob.mx): `"Montserrat"`.

**Paleta de colores (tokens `--cg-color-*`):**
| Token | Hex | Uso observado |
|---|---|---|
| `naranja-300` | `#c45620` | Color de acento principal: títulos, links activos, botones primarios |
| `naranja-500` | `#9c4419` | Hover de acento |
| `naranja-100` | `#f4d2c1` | Fondos suaves de acento |
| `cafe` | `#6e3d14` | Acompaña al naranja en el logo |
| `gris-700` | `#232323` | Texto de encabezados, footer oscuro |
| `gris-500` | `#343434` | Texto de cuerpo |
| `gris-300` / `gris-100` | `#d9d9d9` / `#f3f3f3` | Fondos y bordes suaves |
| `blanco` | `#ffffff` | Fondos de tarjetas/header |
| `verde-500`, `azul-500`, `amarillo-500` (+ variantes `-100`) | `#2a6f4d`, `#19439c`, `#916802` | Colores de estado/categoría secundarios |
| Topbar/footer gob.mx | `#611232` (vino) sobre `#13322b` | Franja gubernamental obligatoria, no forma parte de la identidad propia de CentroGeo |

**Otros tokens reutilizables**: radios de borde (`--cg-border-radius-s/m/b`: 8/16/24px),
espaciado en escala de 8px (`--cg-space-size-*`), sombras suaves
(`--cg-box-shadow-s/m`), transición estándar `200ms ease`.

**Logotipo**: wordmark horizontal `logo_centrogeo_wide.svg` (colores naranja/café),
con variante blanca para fondos oscuros. Siempre acompañado del logo de SECIHTI y,
en el topbar/footer, del logo de gob.mx (franja institucional obligatoria del
gobierno mexicano — mantenerla si el sitio se presenta como oficial de CentroGeo,
opcional si este prototipo se posiciona como proyecto independiente de divulgación).

**Aplicación a este proyecto**: al maquetar el sitio Astro, usar `naranja-300`
(`#c45620`) como acento primario, `Roboto Flex` para cuerpo y `ingra-wide` (o una
alternativa gratuita similar tipo "Archivo Expanded" si Typekit no es accesible
fuera del dominio de CentroGeo) para títulos, y respetar la escala de espaciado de
8px. Esto reemplaza el placeholder neutro usado en `src/layouts/Base.astro`
mientras no se aplique — pendiente de implementación real.

**Pendiente**: no se encontró un manual de marca formal en PDF, solo el CSS en
producción; si el equipo de CentroGeo tiene un brand book más completo (uso del
isotipo, versiones mínimas, zona de protección del logo), solicitarlo para
completar este apartado.

## Pipeline de generación de contenido (tipo NotebookLM)

Propuesta de flujo automatizado para convertir papers en materiales ricos de
divulgación, respetando la política de derechos de autor:

1. **Ingestión**: cargar PDFs por investigador desde la carpeta de Drive
   correspondiente.
2. **Extracción conceptual**: identificar hallazgos clave, contribuciones y contexto
   del paper (no extracción de texto literal ni de figuras).
3. **Guionización**: generar un guion original de divulgación en lenguaje propio,
   parafraseado y adaptado a público general, con nivel de profundidad progresivo.
4. **Producción multi-formato**:
   - Video generado por IA (narración + imágenes/animaciones generadas desde cero).
   - Audio/podcast.
   - Infografías o diapositivas originales.
   - Texto de divulgación (cápsula corta).
5. **Trazabilidad**: mantener metadatos de qué paper originó cada contenido (autor,
   título, DOI/referencia) para atribución correcta, sin necesidad de reproducir el
   material protegido.
6. **Revisión humana**: cada pieza generada debe pasar por revisión antes de
   publicarse, tanto por precisión de contenido como por cumplimiento de copyright.

## Conceptos de divulgación a explorar

- **Cápsulas de conocimiento**: unidades breves y autocontenidas de divulgación
  (un hallazgo o tema por cápsula), consumibles en pocos minutos, con posibilidad de
  encadenarse en series temáticas.
- **Profundidad progresiva**: cada cápsula ofrece 2-3 niveles de detalle (resumen de
  30 segundos → explicación de 3 minutos → recursos para profundizar), permitiendo
  que el usuario elija cuánto quiere adentrarse.
- **Series temáticas**: agrupar cápsulas por eje temático (siguiendo el precedente de
  Ivvan: Agua, Espacio donde vivimos, Sociedad justa), facilitando navegación tipo
  CRM por tema en vez de por investigador.
- **Colaboración investigador-IA con revisión humana**: la IA genera el primer
  borrador de guion/video, pero el investigador original (o un revisor) valida
  precisión y tono antes de publicar.
- **Mapa de conocimiento navegable**: vista tipo grafo o índice que conecta cápsulas
  entre sí por temas o investigadores relacionados, facilitando descubrimiento
  serendípico de contenido relacionado.

## Próximos pasos / roadmap abierto

- [x] Revisar los dos recursos de Ivvan y documentar hallazgos concretos (2026-07-21,
      vía Playwright headless; ver sección de Referencias existentes de estilo).
- [x] Revisar de nuevo el sitio central de CentroGeo y extraer paleta/tipografía real
      (2026-07-21, ver sección Identidad visual institucional).
- [ ] Definir mecanismo de acceso reproducible a la carpeta de Drive de papers.
- [ ] Prototipar el pipeline de ingestión → guion → video con un solo paper de prueba.
- [x] Decidir estructura de datos del CRM ligero en Astro (colecciones de contenido:
      ver [docs/content-collections.md](docs/content-collections.md), ya implementado
      en `src/content.config.ts`).
- [ ] Aplicar la identidad visual real (colores/tipografía de CentroGeo) al layout,
      reemplazando el estilo neutro provisional de `src/layouts/Base.astro`.
- [ ] Cargar contenido real (al menos un investigador/paper/cápsula) reemplazando los
      ejemplos de placeholder en `src/content/`.
