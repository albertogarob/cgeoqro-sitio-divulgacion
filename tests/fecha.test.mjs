// Pruebas de las fechas de publicación.
//
// El fallo que existía: el frontmatter trae "2026-10-29", JavaScript lo lee como
// medianoche UTC, y al pintarlo con el huso local (México, seis horas por detrás)
// salía el día 28. La prueba fija el huso de la máquina a uno por detrás de UTC para
// que el fallo se reproduzca si alguien quita la zona horaria del formateador.
import test from 'node:test';
import assert from 'node:assert/strict';
import { fechaCorta, fechaLarga } from '../src/lib/fecha.ts';

const DEL_FRONTMATTER = new Date('2026-10-29');

test('la fecha del frontmatter se publica tal cual, no un día antes', () => {
  assert.equal(fechaCorta(DEL_FRONTMATTER), '29/10/2026');
  assert.equal(fechaLarga(DEL_FRONTMATTER), '29 de octubre de 2026');
});

test('el huso de la máquina no mueve el día', () => {
  // Las dos orillas: seis horas por detrás de UTC (México) y trece por delante
  // (Nueva Zelanda en verano), que son las que cambian el día en sentidos opuestos.
  const original = process.env.TZ;
  try {
    for (const tz of ['America/Mexico_City', 'Pacific/Auckland', 'UTC']) {
      process.env.TZ = tz;
      assert.equal(fechaCorta(DEL_FRONTMATTER), '29/10/2026', `con TZ=${tz}`);
    }
  } finally {
    process.env.TZ = original;
  }
});

test('el primero de mes, que es donde más duele, tampoco retrocede', () => {
  // Retroceder un día aquí cambia también el mes, y en enero cambia el año.
  assert.equal(fechaCorta(new Date('2026-01-01')), '1/1/2026');
  assert.equal(fechaLarga(new Date('2026-01-01')), '1 de enero de 2026');
});
