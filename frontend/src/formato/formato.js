// Formato de cifras, fechas y valores fijos que envía la API (SRS 4.5.1, «Formato de cifras y fechas»).
//
// Regla de cifras (RD-12; RD-16; RNF-02): toda cifra llega como texto, ya calculada y redondeada
// por el motor. Aquí solo se agregan separadores de miles, el símbolo de pesos y la unidad, y se
// reordenan las fechas. Nada convierte una cifra a número ni interpreta una fecha con hora: este
// archivo no usa ninguna de las conversiones que prohíbe la regla de cifras del Anexo A del plan.
// Todas las vistas usan estas mismas funciones, para que la tarjeta, la etiqueta del corte, la
// última fila de la tabla y el total de posiciones digan exactamente lo mismo.

import { VALORES_FIJOS } from '../textos/textos.js'

const ESPACIO_FIJO = ' ' // espacio que no se separa entre la cifra y su unidad
const RAYA = '—' // sin dato

const PATRON_CIFRA = /^-?\d+(\.\d+)?$/
const PATRON_ISO = /^(\d{4})-(\d{2})-(\d{2})$/
const PATRON_MOMENTO = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/
const PATRON_DDMMAAAA = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/

function esTexto(valor) {
  return typeof valor === 'string' && valor !== ''
}

/** Agrega la coma de miles a la parte entera de una cifra en texto, sin convertirla: '-1234.50' → '-1,234.50'. */
export function conMiles(cifra) {
  if (!esTexto(cifra)) return RAYA
  if (!PATRON_CIFRA.test(cifra)) return cifra // no es una cifra: se deja como llegó
  const negativo = cifra.startsWith('-')
  const s = negativo ? cifra.slice(1) : cifra
  const punto = s.indexOf('.')
  const entera = punto === -1 ? s : s.slice(0, punto)
  const decimales = punto === -1 ? '' : s.slice(punto) // el punto y los dígitos, tal cual
  const agrupada = entera.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return (negativo ? '-' : '') + agrupada + decimales
}

/** Importe o precio en pesos, con el signo antes de «$»: '-218.56' → '-$218.56'; '58940.88' → '$58,940.88'. */
export function pesos(cifra) {
  if (!esTexto(cifra)) return RAYA
  if (!PATRON_CIFRA.test(cifra)) return cifra
  const negativo = cifra.startsWith('-')
  return (negativo ? '-' : '') + '$' + conMiles(negativo ? cifra.slice(1) : cifra)
}

/** Por ciento con espacio fijo: '4.39' → '4.39 %'; '-6.68' → '-6.68 %'. */
export function porCiento(cifra) {
  if (!esTexto(cifra)) return RAYA
  return conMiles(cifra) + ESPACIO_FIJO + '%'
}

/** Títulos con separador de miles: '1000' → '1,000'. */
export function titulos(cifra) {
  return conMiles(cifra)
}

/** Fecha AAAA-MM-DD reordenada como texto: '2026-10-14' → '14/10/2026'. */
export function fecha(iso) {
  if (!esTexto(iso)) return RAYA
  const m = PATRON_ISO.exec(iso)
  return m ? `${m[3]}/${m[2]}/${m[1]}` : iso
}

/** Fecha corta para el eje de la gráfica: '2026-10-14' → '14/10'. */
export function fechaCorta(iso) {
  if (!esTexto(iso)) return RAYA
  const m = PATRON_ISO.exec(iso)
  return m ? `${m[3]}/${m[2]}` : iso
}

/**
 * Momento ISO 8601 que la API ya envía con el desfase de la Ciudad de México:
 * '2026-10-16T00:00:00-06:00' → '16/10/2026 00:00'. Se corta el texto; no se cambia de zona.
 */
export function momento(iso) {
  if (!esTexto(iso)) return RAYA
  const m = PATRON_MOMENTO.exec(iso)
  return m ? `${m[3]}/${m[2]}/${m[1]} ${m[4]}:${m[5]}` : iso
}

/** Tasa anual publicada o aplicada: '7.06984' → '7.06984 % anual'. */
export function tasa(cifra) {
  if (!esTexto(cifra)) return RAYA
  return conMiles(cifra) + ESPACIO_FIJO + '%' + ESPACIO_FIJO + 'anual'
}

/** Días y plazos: '50' → '50 días'; '1' → '1 día'. */
export function dias(cifra) {
  if (!esTexto(cifra)) return RAYA
  return conMiles(cifra) + ESPACIO_FIJO + (cifra === '1' ? 'día' : 'días')
}

/**
 * Lo que el usuario escribe en un campo de fecha, de DD/MM/AAAA a AAAA-MM-DD, sin Date:
 * '14/10/2026' → '2026-10-14'; '1/9/2026' → '2026-09-01'. Un texto ya AAAA-MM-DD se devuelve igual.
 * Devuelve null si no tiene esa forma o el mes o el día no existen en ningún año; que el día exista
 * en ese mes lo valida la API, con su mensaje.
 */
export function aIso(texto) {
  if (typeof texto !== 'string') return null
  const t = texto.trim()
  let dia
  let mes
  let anio
  const iso = PATRON_ISO.exec(t)
  if (iso) {
    ;[, anio, mes, dia] = iso
  } else {
    const m = PATRON_DDMMAAAA.exec(t)
    if (!m) return null
    dia = m[1].padStart(2, '0')
    mes = m[2].padStart(2, '0')
    anio = m[3]
  }
  if (!/^(0[1-9]|1[0-2])$/.test(mes)) return null
  if (!/^(0[1-9]|[12]\d|3[01])$/.test(dia)) return null
  return `${anio}-${mes}-${dia}`
}

function textoFijo(tabla, valor) {
  if (!esTexto(valor)) return RAYA
  return Object.hasOwn(tabla, valor) ? tabla[valor] : valor
}

/** Clase de activo: 'accion' → 'Acción'; 'cetes' → 'CETES'. */
export function textoClase(valor) {
  return textoFijo(VALORES_FIJOS.clase, valor)
}

/** Tipo de transacción: 'compra' → 'Compra'. */
export function textoTipo(valor) {
  return textoFijo(VALORES_FIJOS.tipo, valor)
}

/** Caso de la tasa de un CETES (RF-26b): 'interpolación' → 'calculada entre dos plazos'. */
export function textoCaso(valor) {
  return textoFijo(VALORES_FIJOS.caso, valor)
}

/** Estado de la cuenta: 'activa' → 'Activa'. */
export function textoEstado(valor) {
  return textoFijo(VALORES_FIJOS.estado, valor)
}

/** Registro de consentimiento: 'otorgamiento' → 'Otorgado'; 'revocacion' → 'Revocado'; medio 'web' → 'sitio web'. */
export function textoConsentimiento(valor) {
  return textoFijo(VALORES_FIJOS.consentimiento, valor)
}
