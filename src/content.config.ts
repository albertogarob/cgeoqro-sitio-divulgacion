import { defineCollection, reference, z } from 'astro:content';
import { glob } from 'astro/loaders';

// Esquema de referencia: docs/content-collections.md
// Política de derechos de autor obligatoria: ver CLAUDE.md — ninguna colección
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
    resumenCorto: z.string(),
    fechaPublicacion: z.date(),
    revisadoPor: z.string(),
  }),
});

const entrevistas = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/entrevistas' }),
  schema: z.object({
    investigador: reference('investigadores'),
    preguntas: z.array(z.object({ pregunta: z.string(), respuesta: z.string() })).length(3),
    paperRelacionado: reference('papers').optional(),
    fechaPublicacion: z.date(),
  }),
});

export const collections = { investigadores, papers, series, capsulas, entrevistas };
