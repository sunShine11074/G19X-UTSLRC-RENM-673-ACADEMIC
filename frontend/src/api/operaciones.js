// Las 19 operaciones del cliente (E02 a E20; Anexo A). Las rutas nunca terminan en «/»
// y la consulta solo lleva fechas AAAA-MM-DD. Los cuerpos se envían tal como los recibe
// cada función: las cifras van como cadenas y los ids como enteros.
import { pedir } from './cliente.js'

const ruta = (base, consulta) => {
  const partes = Object.entries(consulta ?? {}).filter(([, v]) => v !== undefined && v !== null && v !== '')
  if (partes.length === 0) return base
  return base + '?' + partes.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&')
}

// Cuentas y aviso (E02 a E07)
export const verAviso = () => pedir('GET', '/aviso-privacidad')
export const registrarCuenta = ({ correo, contrasena, consentimiento, version_aviso_id }) =>
  pedir('POST', '/cuentas', { cuerpo: { correo, contrasena, consentimiento, version_aviso_id }, sin401: true })
export const iniciarSesion = ({ correo, contrasena }) =>
  pedir('POST', '/sesion', { cuerpo: { correo, contrasena }, sin401: true })
export const cerrarSesion = () => pedir('DELETE', '/sesion', { sin401: true })
export const verCuenta = ({ sin401 = false } = {}) => pedir('GET', '/cuenta', { sin401 })
export const revocarConsentimiento = () => pedir('POST', '/cuenta/revocacion', { cuerpo: { confirmo: true } })

// Catálogo, intervalo e intermediarios (E08 a E11)
export const listarInstrumentos = () => pedir('GET', '/instrumentos')
export const verIntervalo = () => pedir('GET', '/intervalo-datos')
export const listarIntermediarios = () => pedir('GET', '/intermediarios')
export const crearIntermediario = (nombre) => pedir('POST', '/intermediarios', { cuerpo: { nombre } })

// Portafolios (E12 a E16)
export const listarPortafolios = () => pedir('GET', '/portafolios')
export const crearPortafolio = (nombre) => pedir('POST', '/portafolios', { cuerpo: { nombre, divisa_base: 'MXN' } })
export const verPortafolio = (id) => pedir('GET', `/portafolios/${id}`)
export const renombrarPortafolio = (id, nombre) => pedir('PATCH', `/portafolios/${id}`, { cuerpo: { nombre } })
export const eliminarPortafolio = (id, confirmacion) =>
  pedir('DELETE', `/portafolios/${id}`, { cuerpo: { confirmacion } })

// Transacciones (E17 y E18)
export const listarTransacciones = (id) => pedir('GET', `/portafolios/${id}/transacciones`)
export const registrarTransaccion = (id, cuerpo) => pedir('POST', `/portafolios/${id}/transacciones`, { cuerpo })

// Consultas (E19 y E20)
export const verPosiciones = (id, fechaCorte) =>
  pedir('GET', ruta(`/portafolios/${id}/posiciones`, { fecha_corte: fechaCorte }))
export const verTablero = (id, { inicio, fin } = {}) => pedir('GET', ruta(`/portafolios/${id}/tablero`, { inicio, fin }))
