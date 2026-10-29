// Iconos de los botones de compartir, como datos y no como marcado, para poder
// comprobar en las pruebas que ninguna red se queda sin el suyo.
//
// Procedencia de cada trazado, que importa porque son marcas de terceros:
//
//  - WhatsApp, Facebook y X vienen de Simple Icons 16.36.0, publicado bajo CC0 1.0
//    (dominio público). Copiados literalmente de ese paquete, no redibujados.
//  - LinkedIn se dibujó aquí: Simple Icons retiró su icono del catálogo, así que no
//    hay versión CC0 que copiar. Es la letra "in" en su forma habitual.
//  - "Copiar enlace" y "Compartir" no son de ninguna marca: son un eslabón de cadena
//    y una flecha de salida, dibujados aquí con trazo.
//
// Los logotipos siguen siendo marcas registradas de sus dueños. Se usan solo para
// nombrar la red a la que lleva cada botón, que es para lo que existen, y cada botón
// lleva además el nombre escrito al lado: el icono no es la única pista.
//
// Todos los trazados están dibujados en una caja de 24 por 24.

export interface Icono {
  /** Trazado SVG, en la caja 0 0 24 24. */
  d: string;
  /** Si se pinta con trazo en vez de relleno. */
  trazo?: boolean;
}

export const CAJA_ICONO = '0 0 24 24';

export const iconos: Record<string, Icono> = {
  whatsapp: {
    d: 'M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z',
  },
  facebook: {
    d: 'M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z',
  },
  x: {
    d: 'M14.234 10.162 22.977 0h-2.072l-7.591 8.824L7.251 0H.258l9.168 13.343L.258 24H2.33l8.016-9.318L16.749 24h6.993zm-2.837 3.299-.929-1.329L3.076 1.56h3.182l5.965 8.532.929 1.329 7.754 11.09h-3.182z',
  },
  linkedin: {
    d: 'M4.2 1.5a2.4 2.4 0 1 0 0 4.8 2.4 2.4 0 0 0 0-4.8zM2 8.1h4.4V22H2zm6.6 0h4.2v1.9c.58-1.1 2-2.26 4.12-2.26 2.94 0 4.42 1.94 4.42 5.26V22h-4.4v-7.6c0-1.8-.64-3.02-2.24-3.02-1.34 0-2.1.9-2.44 1.78-.12.3-.16.72-.16 1.14V22H8.6z',
  },
  copiar: {
    d: 'M10 13a5 5 0 0 0 7.07 0l3-3a5 5 0 0 0-7.07-7.07l-1.5 1.5M14 11a5 5 0 0 0-7.07 0l-3 3a5 5 0 0 0 7.07 7.07l1.5-1.5',
    trazo: true,
  },
  nativo: {
    d: 'M4 12v7a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-7M12 16V3M8 7l4-4 4 4',
    trazo: true,
  },
};

/**
 * Icono de una clave. Falla en build si falta, en vez de pintar un botón mudo: un
 * hueco donde debería ir el logotipo no se nota hasta que alguien lo ve publicado.
 */
export function icono(clave: string): Icono {
  const ic = iconos[clave];
  if (!ic) throw new Error(`No hay icono para "${clave}". Añádelo en src/lib/iconos.ts.`);
  return ic;
}

/**
 * Atributos de pintado del `<svg>` de un icono. Se decide aquí y no en la plantilla
 * para que la bandera `trazo` mande de verdad: escrito a mano en el marcado, un
 * logotipo de marca podía acabar dibujado con trazo, que lo saca hueco y desfigurado,
 * sin que nada lo notara.
 */
export function atributosIcono(clave: string): Record<string, string> {
  return icono(clave).trazo
    ? {
        fill: 'none',
        stroke: 'currentColor',
        'stroke-width': '2',
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
      }
    : { fill: 'currentColor' };
}
