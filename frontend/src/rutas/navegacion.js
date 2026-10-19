// Enrutador propio (H-2, opción C): History API, sin dependencias.
// navegar(ruta, {reemplazar, estado}) y useRuta() → {ruta, params, consulta, estado} (Anexo A).
// El estado del historial lleva lo que no debe ir en la URL (el correo de N-04 y el destino de N-01 y N-07).
import { useSyncExternalStore } from 'react'

// Tabla de rutas de 4.5.2, en orden: la primera que coincide gana.
export const PATRONES = [
  '/',
  '/sesion',
  '/registro',
  '/aviso-privacidad',
  '/tablero',
  '/portafolios',
  '/portafolios/:id/tablero',
  '/portafolios/:id/posiciones',
  '/portafolios/:id/transacciones',
  '/portafolios/:id/transacciones/nueva',
  '/intermediarios',
  '/catalogo',
  '/cuenta',
]

function coincidir(patron, ruta) {
  const p = patron.split('/')
  const r = ruta.split('/')
  if (p.length !== r.length) return null
  const params = {}
  for (let i = 0; i < p.length; i++) {
    if (p[i].startsWith(':')) {
      if (!/^\d+$/.test(r[i])) return null // los ids de las rutas son enteros
      params[p[i].slice(1)] = r[i]
    } else if (p[i] !== r[i]) {
      return null
    }
  }
  return params
}

export function resolver(ruta) {
  for (const patron of PATRONES) {
    const params = coincidir(patron, ruta)
    if (params) return { patron, params }
  }
  return { patron: null, params: {} }
}

function normalizar(ruta) {
  if (ruta.length > 1 && ruta.endsWith('/')) return ruta.replace(/\/+$/, '')
  return ruta
}

function leer() {
  const ruta = normalizar(window.location.pathname)
  const { patron, params } = resolver(ruta)
  const consulta = Object.fromEntries(new URLSearchParams(window.location.search))
  return {
    ruta,
    patron,
    params,
    consulta,
    busqueda: window.location.search,
    estado: window.history.state ?? null,
  }
}

let actual = leer()
const oyentes = new Set()

function avisar() {
  actual = leer()
  for (const fn of oyentes) fn()
}

window.addEventListener('popstate', avisar)

function suscribir(fn) {
  oyentes.add(fn)
  return () => oyentes.delete(fn)
}

export function navegar(ruta, { reemplazar = false, estado = null } = {}) {
  if (reemplazar) window.history.replaceState(estado, '', ruta)
  else window.history.pushState(estado, '', ruta)
  avisar()
}

export function rutaActual() {
  return actual
}

export function useRuta() {
  return useSyncExternalStore(suscribir, rutaActual)
}

// Arma una ruta con su consulta (solo fechas AAAA-MM-DD e ids; 4.5.2).
export function conConsulta(base, consulta) {
  const partes = Object.entries(consulta ?? {}).filter(([, v]) => v !== undefined && v !== null && v !== '')
  if (partes.length === 0) return base
  return base + '?' + partes.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&')
}
