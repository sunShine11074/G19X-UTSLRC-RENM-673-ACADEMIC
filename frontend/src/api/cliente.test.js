// Pruebas del cliente de la API: npm test (en frontend/).
// fetch se sustituye por una función de la prueba y window por un EventTarget, porque Node no
// tiene navegador; cliente.js se importa después de preparar los dos.
import { afterEach, beforeEach, test } from 'node:test'
import assert from 'node:assert/strict'

globalThis.window = new EventTarget()
const { ErrorApi, MENSAJE_SIN_CONEXION, alTerminarSesion, esPortafolioInexistente, pedir } = await import('./cliente.js')

const fetchOriginal = globalThis.fetch
let llamadas

/** Hace que fetch responda `cuerpo` (objeto → JSON; texto → tal cual) con el estado indicado. */
function responder(estado, cuerpo) {
  globalThis.fetch = async (url, opciones) => {
    llamadas.push({ url, opciones })
    const texto = typeof cuerpo === 'string' ? cuerpo : JSON.stringify(cuerpo)
    return new Response(estado === 204 ? null : texto, { status: estado })
  }
}

/** Ejecuta `fn` y devuelve el error que lanza; falla si no lanza. */
async function errorDe(fn) {
  try {
    await fn()
  } catch (e) {
    return e
  }
  assert.fail('se esperaba un error')
}

beforeEach(() => {
  llamadas = []
})

afterEach(() => {
  globalThis.fetch = fetchOriginal
})

test('una respuesta correcta se devuelve tal cual, con las cifras como cadenas', async () => {
  const datos = { valor_mercado: { valor: '58940.88', divisa: 'MXN' } }
  responder(200, datos)
  assert.deepEqual(await pedir('GET', '/portafolios/1/tablero'), datos)
  const [{ url, opciones }] = llamadas
  assert.equal(url, '/api/portafolios/1/tablero')
  assert.equal(opciones.method, 'GET')
  assert.equal(opciones.credentials, 'same-origin')
  assert.equal(opciones.headers.Accept, 'application/json')
  assert.equal(opciones.body, undefined)
})

test('con cuerpo, lo envía como JSON', async () => {
  responder(201, { id: 7 })
  await pedir('POST', '/portafolios', { cuerpo: { nombre: 'Principal' } })
  const [{ opciones }] = llamadas
  assert.equal(opciones.headers['Content-Type'], 'application/json')
  assert.equal(opciones.body, '{"nombre":"Principal"}')
})

test('un 204 devuelve null', async () => {
  responder(204)
  assert.equal(await pedir('POST', '/sesion/cerrar'), null)
})

test('sin conexión, lanza ErrorApi con estado 0', async () => {
  globalThis.fetch = async () => {
    throw new TypeError('Failed to fetch')
  }
  const e = await errorDe(() => pedir('GET', '/cuenta'))
  assert.ok(e instanceof ErrorApi)
  assert.equal(e.estado, 0)
  assert.equal(e.mensaje, MENSAJE_SIN_CONEXION)
})

test('una respuesta que no es JSON (el proxy sin API) se trata como sin conexión y no cierra la sesión', async () => {
  let avisos = 0
  const quitar = alTerminarSesion(() => avisos++)
  responder(502, '<html><body>Bad Gateway</body></html>')
  const e = await errorDe(() => pedir('GET', '/cuenta'))
  quitar()
  assert.equal(e.estado, 0)
  assert.equal(e.mensaje, MENSAJE_SIN_CONEXION)
  assert.equal(avisos, 0)
})

test('un rechazo de la API conserva su estado, código, mensaje, errores y regla', async () => {
  responder(422, {
    codigo: 'datos_invalidos',
    regla: 'RF-05',
    mensaje: 'Revisa los datos.',
    errores: [{ campo: 'titulos', mensaje: 'Debe ser un número entero.' }],
  })
  const e = await errorDe(() => pedir('POST', '/portafolios/1/transacciones', { cuerpo: {} }))
  assert.ok(e instanceof ErrorApi)
  assert.equal(e.estado, 422)
  assert.equal(e.codigo, 'datos_invalidos')
  assert.equal(e.regla, 'RF-05')
  assert.equal(e.mensaje, 'Revisa los datos.')
  assert.deepEqual(e.errores, [{ campo: 'titulos', mensaje: 'Debe ser un número entero.' }])
})

test('un rechazo sin mensaje ni lista de errores usa el mensaje de sin conexión y una lista vacía', async () => {
  responder(500, { errores: 'no es una lista' })
  const e = await errorDe(() => pedir('GET', '/cuenta'))
  assert.equal(e.estado, 500)
  assert.equal(e.codigo, null)
  assert.equal(e.mensaje, MENSAJE_SIN_CONEXION)
  assert.deepEqual(e.errores, [])
})

test('un 401 avisa a los oyentes y a window que terminó la sesión (N-07)', async () => {
  const recibidos = []
  const quitar = alTerminarSesion((error) => recibidos.push(error))
  let evento = null
  const alEvento = (ev) => (evento = ev)
  window.addEventListener('sesion:terminada', alEvento)
  responder(401, { codigo: 'sesion_requerida', regla: 'RNF-03', mensaje: 'Inicia sesión para continuar.' })

  const e = await errorDe(() => pedir('GET', '/portafolios'))

  window.removeEventListener('sesion:terminada', alEvento)
  quitar()
  assert.equal(e.estado, 401)
  assert.equal(e.codigo, 'sesion_requerida')
  assert.deepEqual(recibidos, [e])
  assert.ok(evento, 'window recibió sesion:terminada')
  assert.equal(evento.detail, e)
})

test('un 401 con sin401 (el inicio de sesión) no avisa a nadie', async () => {
  let avisos = 0
  const quitar = alTerminarSesion(() => avisos++)
  responder(401, { codigo: 'credenciales_invalidas', mensaje: 'Correo o contraseña incorrectos.' })
  const e = await errorDe(() => pedir('POST', '/sesion', { cuerpo: {}, sin401: true }))
  quitar()
  assert.equal(e.estado, 401)
  assert.equal(avisos, 0)
})

test('el oyente que se quita ya no recibe avisos', async () => {
  let avisos = 0
  const quitar = alTerminarSesion(() => avisos++)
  quitar()
  responder(401, { codigo: 'sesion_requerida', mensaje: 'Inicia sesión para continuar.' })
  await errorDe(() => pedir('GET', '/portafolios'))
  assert.equal(avisos, 0)
})

test('esPortafolioInexistente reconoce solo el 404 del portafolio (N-08)', async () => {
  responder(404, { codigo: 'no_encontrado', regla: 'RF-02', mensaje: 'No existe el portafolio.' })
  const portafolio = await errorDe(() => pedir('GET', '/portafolios/999/tablero'))
  assert.equal(esPortafolioInexistente(portafolio), true)

  // E18 usa el mismo código para el intermediario y el instrumento: solo el mensaje los distingue.
  for (const mensaje of ['No existe el intermediario.', 'No existe el instrumento.', 'No existe el recurso.']) {
    assert.equal(esPortafolioInexistente(new ErrorApi({ estado: 404, codigo: 'no_encontrado', mensaje })), false, mensaje)
  }
  assert.equal(esPortafolioInexistente(new ErrorApi({ estado: 403, codigo: 'no_encontrado', mensaje: 'No existe el portafolio.' })), false)
  assert.equal(esPortafolioInexistente(new ErrorApi({ estado: 0 })), false)
  assert.equal(esPortafolioInexistente(null), false)
  assert.equal(esPortafolioInexistente(undefined), false)
})
