// Formulario de contacto del final de cada cápsula. Al lector solo se le pide el
// correo: el mensaje va prellenado con el título de la cápsula, su enlace y los
// investigadores, para que quien reciba el aviso sepa de dónde viene sin preguntar.
//
// ┌──────────────────────────────────────────────────────────────────────────────┐
// │ PUNTO DE CONFIGURACIÓN. Rellenar los tres valores de FORMULARIO_CONTACTO     │
// │ para que el bloque de contacto aparezca en el sitio publicado.               │
// │ Instrucciones paso a paso: docs/contacto-y-analytics.md                      │
// └──────────────────────────────────────────────────────────────────────────────┘

export interface ConfigFormulario {
  /** ID largo del formulario de Google: el tramo entre /forms/d/e/ y /viewform. */
  formId: string;
  /** Nombre del campo del correo, con la forma "entry.123456789". */
  entryCorreo: string;
  /** Nombre del campo del mensaje, con la forma "entry.987654321". */
  entryMensaje: string;
  /** Respaldo: correo al que escribir si no hay formulario de Google configurado. */
  correoRespaldo: string;
}

export const FORMULARIO_CONTACTO: ConfigFormulario = {
  formId: '',
  entryCorreo: '',
  entryMensaje: '',
  correoRespaldo: '',
};

export type ModoContacto = 'google' | 'correo' | 'ninguno';

const RE_ENTRY = /^entry\.\d+$/;

/** Qué vía de contacto está realmente configurada. */
export function modoContacto(cfg: ConfigFormulario = FORMULARIO_CONTACTO): ModoContacto {
  const google = cfg.formId.trim() && RE_ENTRY.test(cfg.entryCorreo.trim()) && RE_ENTRY.test(cfg.entryMensaje.trim());
  if (google) return 'google';
  if (cfg.correoRespaldo.includes('@')) return 'correo';
  return 'ninguno';
}

export interface DatosContacto {
  tituloCapsula: string;
  /** URL canónica absoluta de la cápsula. */
  url: string;
  /** Nombres de los investigadores de la cápsula. */
  investigadores?: string[];
}

/**
 * Mensaje que viaja prellenado. Texto neutro y corto: identifica la cápsula y a quién
 * va dirigido, sin poner palabras en boca del lector.
 */
export function mensajePrellenado({ tituloCapsula, url, investigadores = [] }: DatosContacto): string {
  const quien = investigadores.filter(Boolean).join(', ');
  const lineas = [
    `Me interesa la cápsula "${tituloCapsula}" del sitio de divulgación de CentroGeo Querétaro y me gustaría saber más.`,
    '',
    `Cápsula: ${url}`,
  ];
  if (quien) lineas.push(`Investigación de: ${quien}`);
  return lineas.join('\n');
}

/** Asunto del correo de respaldo. */
export function asuntoContacto(tituloCapsula: string): string {
  return `Divulgación CentroGeo Querétaro: ${tituloCapsula}`;
}

/** Endpoint al que el formulario hace POST. Solo válido en modo "google". */
export function urlEnvio(cfg: ConfigFormulario = FORMULARIO_CONTACTO): string {
  if (modoContacto(cfg) !== 'google') {
    throw new Error('urlEnvio solo aplica cuando el formulario de Google está configurado.');
  }
  return `https://docs.google.com/forms/d/e/${cfg.formId.trim()}/formResponse`;
}

/**
 * Enlace al formulario de Google ya prellenado, con la vía documentada (usp=pp_url).
 * Es la salida de emergencia visible por si el envío desde la página falla.
 */
export function urlFormularioPrellenado(mensaje: string, cfg: ConfigFormulario = FORMULARIO_CONTACTO): string {
  if (modoContacto(cfg) !== 'google') {
    throw new Error('urlFormularioPrellenado solo aplica cuando el formulario de Google está configurado.');
  }
  const params = new URLSearchParams({ usp: 'pp_url', [cfg.entryMensaje.trim()]: mensaje });
  return `https://docs.google.com/forms/d/e/${cfg.formId.trim()}/viewform?${params.toString()}`;
}

/** Enlace mailto de respaldo, con asunto y cuerpo ya escritos. */
export function urlMailto(datos: DatosContacto, cfg: ConfigFormulario = FORMULARIO_CONTACTO): string {
  if (modoContacto(cfg) !== 'correo') {
    throw new Error('urlMailto solo aplica cuando hay un correo de respaldo configurado.');
  }
  const params = new URLSearchParams({
    subject: asuntoContacto(datos.tituloCapsula),
    body: mensajePrellenado(datos),
  });
  // URLSearchParams codifica el espacio como "+", que un cliente de correo muestra
  // literal en el cuerpo del mensaje.
  return `mailto:${cfg.correoRespaldo.trim()}?${params.toString().replace(/\+/g, '%20')}`;
}
