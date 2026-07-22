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
- Al crear el repositorio real en GitHub, actualizar `site` y `base` en
  `astro.config.mjs` (hay un TODO marcado ahí) con la URL definitiva.
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
temáticas: **Agua**, **El espacio donde vivimos**, y **Sociedad justa**. El segundo
ejemplo revisado presenta un video de divulgación basado en un capítulo de libro
académico sobre geopolítica tecnológica (rivalidad EE.UU.–China), con tono
académico-profesional dirigido a público interesado en política internacional.

Nota: el contenido embebido (video/diapositivas en sí) no es accesible por fetch
automatizado (Google Sites renderiza vía JavaScript y los recursos están incrustados).
**Antes de definir plantillas o guiones de las "cápsulas de conocimiento", revisar
manualmente ambos enlaces en el navegador** para identificar: duración de los videos,
estructura narrativa (introducción/problema/hallazgos/cierre), nivel técnico del
lenguaje, y estilo visual de las diapositivas. Usar esto como línea base de
consistencia con el trabajo ya iniciado por el equipo, en lugar de partir de cero.

## Identidad visual institucional

El sitio debe seguir los estándares visuales institucionales de CentroGeo
(https://www.centrogeo.org.mx/). Al momento de este análisis inicial, el sitio central
estaba en construcción ("Estamos trabajando en nuestro sitio para darte un mejor
servicio") y solo expone: logotipo institucional (wordmark horizontal, con variante
blanca para fondos oscuros) y un tono formal/gubernamental. No se encontró manual de
marca ni paleta de colores explícita.

**Antes de fijar estilos, componentes o layout en Astro:**
1. Volver a revisar https://www.centrogeo.org.mx/ (puede que ya no esté en
   construcción) para extraer paleta de colores, tipografía, y patrones de layout
   reales.
2. Buscar si existe un manual de identidad gráfica institucional (PDF o página
   dedicada) en el sitio o solicitarlo al equipo de CentroGeo.
3. Cualquier decisión de diseño (colores, tipografía, componentes UI) debe
   verificarse contra esta identidad institucional antes de introducir estilos
   propios o genéricos. Si no hay información suficiente, usar un estilo neutro e
   institucional (formal, sobrio) como default temporal, dejando explícito que es
   provisional hasta validar contra el manual de marca real.

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

- [ ] Revisar en navegador los dos recursos de Ivvan y documentar hallazgos concretos
      (duración, estructura, tono) en este archivo.
- [ ] Revisar de nuevo el sitio central de CentroGeo cuando esté completo y extraer
      paleta/tipografía real.
- [ ] Definir mecanismo de acceso reproducible a la carpeta de Drive de papers.
- [ ] Prototipar el pipeline de ingestión → guion → video con un solo paper de prueba.
- [ ] Decidir estructura de datos del CRM ligero en Astro (colecciones de contenido:
      investigadores, papers, cápsulas).
