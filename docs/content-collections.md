# Diseño de Content Collections (Astro)

Esquema de referencia para cuando se haga el scaffold del proyecto Astro. Sigue la
Content Layer API (Astro 5+, `src/content.config.ts` con `defineCollection` + `reference()`).
No requiere backend: los datos viven como Markdown/MDX + un `data/` de JSON para el
directorio de investigadores, coherente con el rol de "CRM ligero" descrito en
[CLAUDE.md](../CLAUDE.md).

## Colecciones

### `investigadores`
Corresponde a la sección "Investigadores" del sitemap (equivalente a "Our People" de Cambridge).

```ts
const investigadores = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/investigadores' }),
  schema: z.object({
    nombre: z.string(),
    slug: z.string(), // usado en /investigadores/[slug]
    fotoUrl: z.string().optional(),
    bioBreve: z.string(), // 1-2 líneas, redactada por el equipo, no copiada de CV externo
    lineasInvestigacion: z.array(z.string()),
    sede: z.literal('Querétaro'),
    carpetaDrive: z.string().url(), // referencia a la subcarpeta de papers en Drive
  }),
})
```

### `papers`
Metadatos del insumo protegido por derechos de autor. **No contiene el PDF ni texto
extraído**, solo referencia y metadatos bibliográficos, en cumplimiento de la política
de copyright de CLAUDE.md.

```ts
const papers = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/papers' }),
  schema: z.object({
    titulo: z.string(),
    investigador: reference('investigadores'), // 1 paper -> 1+ investigadores
    editorial: z.string(), // quién retiene el copyright
    anioPublicacion: z.number(),
    doi: z.string().optional(),
    driveFileId: z.string(), // referencia al PDF en Drive, no el archivo en sí
    estadoPipeline: z.enum(['pendiente', 'en_produccion', 'publicado']),
    temasClave: z.array(z.string()), // extraídos por el pipeline, no verbatim del abstract
  }),
})
```

### `capsulas`
La unidad atómica de divulgación (contenido público central del sitio).

```ts
const capsulas = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/capsulas' }),
  schema: z.object({
    titulo: z.string(),
    slug: z.string(),
    serie: reference('series'),
    paperFuente: reference('papers'), // trazabilidad obligatoria a la fuente
    investigadores: z.array(reference('investigadores')),
    formatos: z.array(z.enum(['video', 'audio', 'infografia', 'texto'])),
    videoUrl: z.string().url().optional(),
    audioUrl: z.string().url().optional(),
    resumenCorto: z.string(), // nivel 1 de profundidad progresiva (~30s de lectura)
    fechaPublicacion: z.date(),
    revisadoPor: z.string(), // quién validó precisión + copyright antes de publicar
  }),
})
```

El cuerpo MDX de cada cápsula es el nivel 2 de profundidad ("explicación de 3 minutos"),
y el nivel 3 ("recursos para profundizar") se resuelve enlazando a `serie` e
`investigadores`, no repitiendo contenido.

### `series`
Los ejes temáticos del sitio (Agua, El espacio donde vivimos, Sociedad justa, + futuras).

```ts
const series = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/series' }),
  schema: z.object({
    nombre: z.string(),
    slug: z.string(),
    descripcion: z.string(),
    colorAcento: z.string().optional(), // pendiente de identidad visual institucional
  }),
})
```

### `entrevistas` (serie "3 Preguntas a...")

```ts
const entrevistas = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/entrevistas' }),
  schema: z.object({
    investigador: reference('investigadores'),
    preguntas: z.array(z.object({ pregunta: z.string(), respuesta: z.string() })).length(3),
    paperRelacionado: reference('papers').optional(),
    fechaPublicacion: z.date(),
  }),
})
```

## Relaciones (grafo de contenido)

```
investigadores 1---N papers
papers          1---N capsulas   (paperFuente)
series          1---N capsulas
investigadores  N---N capsulas   (autores/voces de la cápsula, vía reference array)
investigadores  1---N entrevistas
```

## Notas de implementación

- Usar `reference()` en vez de duplicar datos: mantiene la trazabilidad paper → cápsula
  exigida en CLAUDE.md sin acoplar contenido.
- `papers` nunca almacena el PDF ni texto extraído en el repo del sitio; solo
  `driveFileId` y metadatos. El pipeline de ingestión vive fuera del árbol de contenido
  (script o servicio aparte que lee de Drive y escribe estos `.md` de metadatos).
- `estadoPipeline` en `papers` es lo que alimentaría el panel de producción interno del
  CRM ligero mencionado en el sitemap.
- `colorAcento` en `series` queda como placeholder hasta resolver la identidad visual
  institucional (pendiente en el roadmap de CLAUDE.md).

## Implicación de GitHub Pages

Al ser el sitio 100% estático (ver sección de despliegue en CLAUDE.md), todas estas
colecciones se resuelven en **build time** con el `glob()` loader sobre archivos
locales del repo. No usar loaders que requieran una llamada de red en runtime o
credenciales de servidor (ej. un loader que consulte Drive directamente en cada
build sí es válido porque corre en GitHub Actions, pero nunca en el navegador). El
pipeline de ingestión (Drive → metadatos `.md`) debe correr antes o durante el build
en CI, nunca como endpoint expuesto públicamente.

## Siguiente paso sugerido

Con este esquema validado, el scaffold real de Astro (`npm create astro@latest`,
integración de content collections, un dato de ejemplo por colección) es el paso que
sigue cuando se decida avanzar a código funcional.
