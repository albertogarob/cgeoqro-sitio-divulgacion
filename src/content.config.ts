import { defineCollection, reference, z } from 'astro:content';
import { glob } from 'astro/loaders';

// Esquema de referencia: docs/content-collections.md
// Política de derechos de autor obligatoria: ver CLAUDE.md. Ninguna colección
// almacena texto verbatim ni imágenes originales de los papers.

const investigadores = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/investigadores' }),
  schema: z.object({
    nombre: z.string(),
    fotoUrl: z.string().optional(),
    bioBreve: z.string(),
    lineasInvestigacion: z.array(z.string()),
    sede: z.literal('Querétaro'),
    carpetaDrive: z.string().url(),
  }),
});

const papers = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/papers' }),
  schema: z.object({
    titulo: z.string(),
    investigador: reference('investigadores'),
    editorial: z.string(),
    anioPublicacion: z.number(),
    doi: z.string().optional(),
    driveFileId: z.string(),
    estadoPipeline: z.enum(['pendiente', 'en_produccion', 'publicado']),
    temasClave: z.array(z.string()),
  }),
});

const series = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/series' }),
  schema: z.object({
    nombre: z.string(),
    descripcion: z.string(),
    colorAcento: z.string().optional(), // pendiente de identidad visual institucional
  }),
});

const capsulas = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/capsulas' }),
  schema: z.object({
    titulo: z.string(),
    serie: reference('series'),
    paperFuente: reference('papers'),
    investigadores: z.array(reference('investigadores')),
    formatos: z.array(z.enum(['video', 'audio', 'infografia', 'texto'])),
    videoUrl: z.string().url().optional(),
    audioUrl: z.string().url().optional(),
    // Página canónica externa del recurso (ej. Google Sites de origen), distinta de
    // la URL de embed. Se usa como respaldo cuando el embed falla (ver CLAUDE.md,
    // limitación de cuota diaria de Google Drive).
    fuenteExternaUrl: z.string().url().optional(),
    // Clave de un componente de scrollytelling dedicado a renderizar en lugar del
    // cuerpo estándar (ej. "utopias"). Ver src/components/Scrolly*.astro.
    scrolly: z.string().optional(),
    resumenCorto: z.string(),
    fechaPublicacion: z.date(),
    revisadoPor: z.string(),
    // Crédito de producción del recurso (ej. video hecho por otro equipo). Se muestra
    // en "Fuente y créditos".
    creditoProduccion: z.string().optional(),
  }),
});

const entrevistas = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/entrevistas' }),
  schema: z.object({
    investigador: reference('investigadores'),
    preguntas: z.array(z.object({ pregunta: z.string(), respuesta: z.string() })).length(3),
    paperRelacionado: reference('papers').optional(),
    fechaPublicacion: z.date(),
    // Video opcional de la entrevista, en modo cine arriba de las preguntas. Usar
    // siempre YouTube (no listado o público), no Google Drive: ver CLAUDE.md sobre
    // los permisos scoped-al-Site de Drive. Puede ser un video con avatar de IA
    // generado desde un guion propio (parafraseado, sin texto verbatim del paper).
    videoUrl: z.string().url().optional(),
    // Nota de producción del video (ej. "Avatar generado con IA a partir de un guion
    // de divulgación propio"). Se muestra bajo el reproductor.
    videoNota: z.string().optional(),
  }),
});

export const collections = { investigadores, papers, series, capsulas, entrevistas };
