// Ayudantes de la gráfica de valor (RF-11 crit. 2; RNF-02; RD-16).
// Portados de «Gráficos - prototipos (16 oct)/fuente/comun.js» y de la sección 7.3 de la
// recomendación de la biblioteca de gráficos. Todo lo que se lee sale de la cadena de la API
// y de las funciones de formato comunes (las mismas que usa la tarjeta, para que RNF-02 se
// cumpla); aquí no se suma, redondea ni convierte ninguna cifra para mostrarla.
import { conMiles, fecha, pesos } from '../formato/formato.js'

/**
 * Filas para Recharts: `texto` es la cadena de la API y `y` solo decide la altura del punto.
 * Excepción documentada de la regla de cifras (Anexo A; P-62, 5 A): la única conversión a
 * número del cliente es esta altura.
 */
export function puntosGrafica(serie) {
  return serie.map((p) => ({ fecha: p.fecha, texto: p.valor, y: Number(p.valor) }))
}

/**
 * Marca del eje Y (H-5, 2 A). Recibe un valor de la escala de Recharts, no una cifra de la
 * API. Sin notación abreviada: solo se le agrega el separador de miles al texto del valor.
 */
export function marcaEje(v) {
  const s = String(v)
  return /^-?\d+(\.\d+)?$/.test(s) ? conMiles(s) : s
}

/** Etiqueta del punto del corte: «$58,940.88 · 14/10/2026 (corte)». */
export function textoCorte(valor, fechaIso) {
  return `${pesos(valor)} · ${fecha(fechaIso)} (corte)`
}

/** «1 día» o «35 días» para el resumen de la tabla. */
export function textoDias(n) {
  return n === 1 ? '1 día' : `${n} días`
}

/**
 * Resumen visible (y `desc` del SVG) que no calcula nada (4.5.1, reglas de la gráfica).
 * Sin el máximo de la serie (H-5): la API no lo envía.
 */
export function textoResumen({ nombrePortafolio, serie, periodo, fechaCorte }) {
  if (!serie || serie.length === 0) return ''
  const primero = serie[0]
  const ultimo = serie[serie.length - 1]
  const previo = periodo && primero.fecha === periodo.fecha_base ? ' (cierre previo al periodo)' : ''
  const corte = ultimo.fecha === fechaCorte ? ', fecha de corte' : ''
  return (
    `Gráfica de líneas del valor de mercado diario del portafolio «${nombrePortafolio}», en pesos mexicanos, ` +
    `del ${fecha(primero.fecha)}${previo} al ${fecha(ultimo.fecha)}${corte}; ` +
    `empieza en ${pesos(primero.valor)} y termina en ${pesos(ultimo.valor)}.`
  )
}
