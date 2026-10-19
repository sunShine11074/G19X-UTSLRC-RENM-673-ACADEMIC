// Pruebas del módulo de formato: node --test frontend/src/formato/formato.test.js
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import {
  aIso,
  conMiles,
  dias,
  fecha,
  fechaCorta,
  momento,
  pesos,
  porCiento,
  tasa,
  textoCaso,
  textoClase,
  textoConsentimiento,
  textoEstado,
  textoTipo,
  titulos,
} from './formato.js'
import { textoParaUsuario } from '../textos/textos.js'

const NBSP = ' '

test('conMiles agrega la coma solo en la parte entera y conserva el signo y los decimales', () => {
  assert.equal(conMiles('0'), '0')
  assert.equal(conMiles('999'), '999')
  assert.equal(conMiles('1000'), '1,000')
  assert.equal(conMiles('12345678'), '12,345,678')
  assert.equal(conMiles('-1234.50'), '-1,234.50')
  assert.equal(conMiles('0.1234567'), '0.1234567')
  assert.equal(conMiles('1234567.8900'), '1,234,567.8900')
})

test('pesos pone el signo antes de «$» y no redondea (sección 7.3 de la recomendación)', () => {
  assert.equal(pesos('-218.56'), '-$218.56')
  assert.equal(pesos('-566.94'), '-$566.94')
  assert.equal(pesos('0.0000'), '$0.0000')
  assert.equal(pesos('0.00'), '$0.00')
  assert.equal(pesos('1234567.8900'), '$1,234,567.8900')
  assert.equal(pesos('58940.88'), '$58,940.88')
  assert.equal(pesos('56307.89'), '$56,307.89')
  assert.equal(pesos('2632.99'), '$2,632.99')
  assert.equal(pesos('9.9629213'), '$9.9629213')
  assert.equal(pesos('14.5'), '$14.5') // las comisiones, tal como se guardaron (H-7)
  assert.equal(pesos('10.00'), '$10.00')
})

test('pesos no altera lo que no es una cifra y marca la ausencia', () => {
  assert.equal(pesos(null), '—')
  assert.equal(pesos(undefined), '—')
  assert.equal(pesos(''), '—')
  assert.equal(pesos('1e5'), '1e5')
})

test('porCiento, tasa y dias llevan su unidad con espacio que no se separa', () => {
  assert.equal(porCiento('4.39'), `4.39${NBSP}%`)
  assert.equal(porCiento('-6.68'), `-6.68${NBSP}%`)
  assert.equal(porCiento('1.00'), `1.00${NBSP}%`)
  assert.equal(tasa('7.06984'), `7.06984${NBSP}%${NBSP}anual`)
  assert.equal(tasa('6.09000'), `6.09000${NBSP}%${NBSP}anual`)
  assert.equal(dias('50'), `50${NBSP}días`)
  assert.equal(dias('28'), `28${NBSP}días`)
  assert.equal(dias('1'), `1${NBSP}día`)
})

test('titulos agrega la coma de miles', () => {
  assert.equal(titulos('1000'), '1,000')
  assert.equal(titulos('220'), '220')
  assert.equal(titulos('0'), '0')
})

test('fecha, fechaCorta y momento reordenan el texto sin interpretarlo', () => {
  assert.equal(fecha('2026-10-14'), '14/10/2026')
  assert.equal(fecha('2026-09-10'), '10/09/2026')
  assert.equal(fechaCorta('2026-10-14'), '14/10')
  assert.equal(momento('2026-10-16T00:00:00-06:00'), '16/10/2026 00:00')
  assert.equal(momento('2026-10-18T19:05:42.123456-06:00'), '18/10/2026 19:05')
  assert.equal(fecha(null), '—')
  assert.equal(fecha('14/10/2026'), '14/10/2026')
})

test('aIso convierte DD/MM/AAAA a AAAA-MM-DD y rechaza lo que no tiene esa forma', () => {
  assert.equal(aIso('14/10/2026'), '2026-10-14')
  assert.equal(aIso('1/9/2026'), '2026-09-01')
  assert.equal(aIso(' 11/09/2026 '), '2026-09-11')
  assert.equal(aIso('2026-10-14'), '2026-10-14')
  assert.equal(aIso('31/13/2026'), null)
  assert.equal(aIso('00/10/2026'), null)
  assert.equal(aIso('32/10/2026'), null)
  assert.equal(aIso('14-10-2026'), null)
  assert.equal(aIso(''), null)
  assert.equal(aIso(null), null)
})

test('textos de los valores fijos de la API (4.5.1)', () => {
  assert.equal(textoClase('accion'), 'Acción')
  assert.equal(textoClase('etf'), 'ETF')
  assert.equal(textoClase('fibra'), 'FIBRA')
  assert.equal(textoClase('cetes'), 'CETES')
  assert.equal(textoTipo('compra'), 'Compra')
  assert.equal(textoTipo('venta'), 'Venta')
  assert.equal(textoCaso('nodo'), 'tasa de un solo plazo')
  assert.equal(textoCaso('interpolación'), 'calculada entre dos plazos')
  assert.equal(textoCaso('extremo inferior'), 'tasa del plazo más corto')
  assert.equal(textoCaso('extremo superior'), 'tasa del plazo más largo')
  assert.equal(textoEstado('activa'), 'Activa')
  assert.equal(textoEstado('bloqueada'), 'Bloqueada')
  assert.equal(textoConsentimiento('otorgamiento'), 'Otorgado')
  assert.equal(textoConsentimiento('revocacion'), 'Revocado')
  assert.equal(textoConsentimiento('web'), 'sitio web')
  assert.equal(textoClase('otra'), 'otra')
  assert.equal(textoClase('toString'), 'toString')
})

test('los mensajes técnicos de la API se sustituyen y los demás llegan igual', () => {
  assert.equal(
    textoParaUsuario('Escribe una fecha válida con el formato AAAA-MM-DD.'),
    'Escribe una fecha válida con el formato DD/MM/AAAA.',
  )
  assert.equal(textoParaUsuario('No existe el portafolio.'), 'No existe el portafolio.')
})

test('formato.js no convierte cifras ni fechas (RD-12; RD-15; RD-16)', () => {
  const fuente = readFileSync(new URL('./formato.js', import.meta.url), 'utf8')
  const codigo = fuente
    .split('\n')
    .filter((l) => !l.trim().startsWith('//') && !l.trim().startsWith('*'))
    .join('\n')
  // Nota para la comprobación de C3: esta lista es la única coincidencia esperada en este archivo.
  for (const prohibido of [
    /Number\s*\(/,
    /parseFloat/,
    /parseInt/,
    /toFixed/,
    /Math\.round/,
    /toLocaleString/,
    /Intl\./,
    /new Date/,
  ]) {
    assert.doesNotMatch(codigo, prohibido)
  }
})
