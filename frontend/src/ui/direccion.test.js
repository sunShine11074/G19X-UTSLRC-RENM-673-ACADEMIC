// Pruebas de la dirección de la Delta: node --test frontend/src/ui/direccion.test.js
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { conSigno, direccion } from './direccion.js'

test('direccion lee solo el texto de la API', () => {
  for (const cifra of ['0', '0.00', '-0.00', '+0.0', '']) assert.equal(direccion(cifra), 'igual', cifra)
  for (const cifra of ['12.5', '0.01', '1000.00']) assert.equal(direccion(cifra), 'sube', cifra)
  for (const cifra of ['-3.10', '-0.01']) assert.equal(direccion(cifra), 'baja', cifra)
})

test('conSigno agrega «+» solo a lo que sube', () => {
  assert.equal(conSigno('$1,234.56', '1234.56'), '+$1,234.56')
  assert.equal(conSigno('4.39 %', '4.39'), '+4.39 %')
  assert.equal(conSigno('-$3.10', '-3.10'), '-$3.10')
  assert.equal(conSigno('$0.00', '0.00'), '$0.00')
  assert.equal(conSigno('+$5.00', '5.00'), '+$5.00')
})
