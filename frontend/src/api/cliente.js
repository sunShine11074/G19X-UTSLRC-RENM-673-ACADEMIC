// Cliente de la API (Anexo A del plan del 18 oct; 4.2, «Cliente de la API»).
// Toda petición va a /api por el proxy de Vite, con la cookie de sesión del mismo
// origen. Las respuestas se devuelven tal cual: las cifras siguen siendo cadenas.

export const MENSAJE_SIN_CONEXION = 'No se pudo conectar con el servidor. Intenta de nuevo.'

export class ErrorApi extends Error {
  constructor({ estado = 0, codigo = null, mensaje = MENSAJE_SIN_CONEXION, errores = [], datos = null, regla = null } = {}) {
    super(mensaje)
    this.name = 'ErrorApi'
    this.estado = estado
    this.codigo = codigo
    this.mensaje = mensaje
    this.errores = errores
    this.datos = datos
    this.regla = regla
  }
}

// Eventos de la sesión: un 401 en una operación con sesión avisa a SesionProvider (N-07).
const oyentes = new Set()

export function alTerminarSesion(fn) {
  oyentes.add(fn)
  return () => oyentes.delete(fn)
}

function emitirSesionTerminada(error) {
  for (const fn of oyentes) fn(error)
  window.dispatchEvent(new CustomEvent('sesion:terminada', { detail: error }))
}

export async function pedir(metodo, ruta, { cuerpo, sin401 = false } = {}) {
  const opciones = { method: metodo, credentials: 'same-origin', headers: { Accept: 'application/json' } }
  if (cuerpo !== undefined) {
    opciones.headers['Content-Type'] = 'application/json'
    opciones.body = JSON.stringify(cuerpo)
  }
  let r
  try {
    r = await fetch('/api' + ruta, opciones)
  } catch {
    throw new ErrorApi({ estado: 0, mensaje: MENSAJE_SIN_CONEXION })
  }
  if (r.status === 204) return null
  let datos
  try {
    datos = await r.json()
  } catch {
    // Respuesta que no es JSON: el proxy sin API (502/504) o un error intermedio.
    throw new ErrorApi({ estado: 0, mensaje: MENSAJE_SIN_CONEXION })
  }
  if (r.ok) return datos
  const error = new ErrorApi({
    estado: r.status,
    codigo: datos?.codigo ?? null,
    mensaje: datos?.mensaje ?? MENSAJE_SIN_CONEXION,
    errores: Array.isArray(datos?.errores) ? datos.errores : [],
    datos: datos?.datos ?? null,
    regla: datos?.regla ?? null,
  })
  if (r.status === 401 && !sin401) emitirSesionTerminada(error)
  throw error
}

// N-08: el portafolio ajeno o inexistente. E18 usa el mismo código para un
// intermediario o un instrumento inexistente, y solo el mensaje los distingue.
export const MENSAJE_PORTAFOLIO_INEXISTENTE = 'No existe el portafolio.'

export function esPortafolioInexistente(e) {
  return !!e && e.estado === 404 && e.codigo === 'no_encontrado' && e.mensaje === MENSAJE_PORTAFOLIO_INEXISTENTE
}
