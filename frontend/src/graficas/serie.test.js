// Pruebas de los ayudantes de la gráfica de valor: npm test (en frontend/).
// Lo que se lee sale del texto de la API; solo `y` (la altura del punto) es un número (RNF-02).
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { marcaEje, puntosGrafica, textoCorte, textoDias, textoResumen } from './serie.js'

const serie = [
  { fecha: '2026-09-10', valor: '56307.89' },
  { fecha: '2026-09-11', valor: '56410.00' },
  { fecha: '2026-10-14', valor: '58940.88' },
]

test('puntosGrafica conserva la cadena de la API y solo convierte la altura', () => {
  const puntos = puntosGrafica(serie)
  assert.equal(puntos.length, 3)
  assert.deepEqual(puntos[2], { fecha: '2026-10-14', texto: '58940.88', y: 58940.88 })
  for (const p of puntos) assert.equal(typeof p.texto, 'string')
  // Los ceros del final se conservan en el texto, aunque el número los pierda.
  assert.equal(puntos[1].texto, '56410.00')
  assert.deepEqual(puntosGrafica([]), [])
})

test('marcaEje agrega solo el separador de miles, sin notación abreviada', () => {
  assert.equal(marcaEje(58000), '58,000')
  assert.equal(marcaEje(1234567.5), '1,234,567.5')
  assert.equal(marcaEje(-2500), '-2,500')
  assert.equal(marcaEje(0), '0')
  assert.equal(marcaEje('auto'), 'auto')
})

test('textoCorte usa el mismo formato que la tarjeta de valor de mercado', () => {
  assert.equal(textoCorte('58940.88', '2026-10-14'), '$58,940.88 · 14/10/2026 (corte)')
  assert.equal(textoCorte('-218.56', '2026-10-14'), '-$218.56 · 14/10/2026 (corte)')
})

test('textoDias distingue el singular', () => {
  assert.equal(textoDias(1), '1 día')
  assert.equal(textoDias(0), '0 días')
  assert.equal(textoDias(35), '35 días')
})

test('textoResumen describe la serie sin calcular nada', () => {
  const resumen = textoResumen({
    nombrePortafolio: 'Principal',
    serie,
    periodo: { fecha_base: '2026-09-10' },
    fechaCorte: '2026-10-14',
  })
  assert.equal(
    resumen,
    'Gráfica de líneas del valor de mercado diario del portafolio «Principal», en pesos mexicanos, ' +
      'del 10/09/2026 (cierre previo al periodo) al 14/10/2026, fecha de corte; ' +
      'empieza en $56,307.89 y termina en $58,940.88.',
  )
  // No menciona el valor máximo, que la API no envía (H-5).
  assert.doesNotMatch(resumen, /máximo/)
})

test('textoResumen omite «cierre previo» y «fecha de corte» cuando no corresponden', () => {
  const resumen = textoResumen({
    nombrePortafolio: 'Principal',
    serie: serie.slice(1),
    periodo: { fecha_base: '2026-09-10' },
    fechaCorte: '2026-10-15',
  })
  assert.equal(
    resumen,
    'Gráfica de líneas del valor de mercado diario del portafolio «Principal», en pesos mexicanos, ' +
      'del 11/09/2026 al 14/10/2026; empieza en $56,410.00 y termina en $58,940.88.',
  )
})

test('textoResumen de una serie vacía es una cadena vacía', () => {
  assert.equal(textoResumen({ nombrePortafolio: 'Principal', serie: [], periodo: null, fechaCorte: '2026-10-14' }), '')
  assert.equal(textoResumen({ nombrePortafolio: 'Principal', serie: null, periodo: null, fechaCorte: '2026-10-14' }), '')
})
