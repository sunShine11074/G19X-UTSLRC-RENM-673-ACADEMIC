// Tema de la interfaz (sistema «Proyecto 077 UI», ThemeControls): data-theme="<modo>-<acento>" en <html>.
// - Primera visita: el modo sigue a prefers-color-scheme (también si cambia después) y el acento es lima.
// - Lo que la persona elige se guarda en localStorage (p77-mode, p77-accent) y lo aplica
//   public/tema-inicial.js antes del primer pintado. Si el almacenamiento falla, el tema vale solo
//   para esta visita.
// useTema() → { modo, acento, fijarModo, fijarAcento }.
import { useSyncExternalStore } from 'react'

export const MODOS = ['light', 'dark']
export const ACENTOS = [
  { id: 'lime', nombre: 'Lima' },
  { id: 'blue', nombre: 'Azul' },
  { id: 'red', nombre: 'Rojo' },
  { id: 'purple', nombre: 'Morado' },
]
const CLAVE_MODO = 'p77-mode'
const CLAVE_ACENTO = 'p77-accent'

function leerGuardado(clave, validos) {
  try {
    const v = window.localStorage.getItem(clave)
    return validos.includes(v) ? v : null
  } catch {
    return null
  }
}

function guardar(clave, valor) {
  try {
    window.localStorage.setItem(clave, valor)
  } catch {
    // Sin almacenamiento (ventana privada, sitio bloqueado): el tema vale solo para esta visita.
  }
}

const oscuro = window.matchMedia?.('(prefers-color-scheme: dark)')
const modoDelSistema = () => (oscuro?.matches ? 'dark' : 'light')

let actual = {
  modo: leerGuardado(CLAVE_MODO, MODOS) ?? modoDelSistema(),
  acento: leerGuardado(CLAVE_ACENTO, ACENTOS.map((a) => a.id)) ?? 'lime',
}
// La elección vale para la visita aunque no se pueda guardar.
let modoElegido = leerGuardado(CLAVE_MODO, MODOS) !== null
const oyentes = new Set()
let finTransicion = null

function aplicar(siguiente, { animar }) {
  actual = siguiente
  const raiz = document.documentElement
  // Los colores pasan en duration-base solo cuando la persona cambia el tema (base.css).
  if (animar) {
    raiz.classList.add('cambiando-tema')
    clearTimeout(finTransicion)
    finTransicion = setTimeout(() => raiz.classList.remove('cambiando-tema'), 300)
  }
  raiz.dataset.theme = `${actual.modo}-${actual.acento}`
  for (const fn of oyentes) fn()
}

aplicar(actual, { animar: false })

// Mientras la persona no elija un modo, el modo sigue al del sistema operativo.
oscuro?.addEventListener?.('change', () => {
  if (modoElegido) return
  const guardado = leerGuardado(CLAVE_MODO, MODOS) // otra pestaña pudo guardar un modo
  if (guardado) modoElegido = true
  aplicar({ ...actual, modo: guardado ?? modoDelSistema() }, { animar: true })
})

// Las pestañas abiertas aplican lo que guarda otra (e.key es null si se borró todo el almacenamiento).
window.addEventListener('storage', (e) => {
  if (e.key !== null && e.key !== CLAVE_MODO && e.key !== CLAVE_ACENTO) return
  const modo = leerGuardado(CLAVE_MODO, MODOS)
  if (modo) modoElegido = true
  aplicar(
    {
      modo: modo ?? (modoElegido ? actual.modo : modoDelSistema()),
      acento: leerGuardado(CLAVE_ACENTO, ACENTOS.map((a) => a.id)) ?? actual.acento,
    },
    { animar: false },
  )
})

export function fijarModo(modo) {
  if (!MODOS.includes(modo)) return
  modoElegido = true
  guardar(CLAVE_MODO, modo)
  aplicar({ ...actual, modo }, { animar: true })
}

export function fijarAcento(acento) {
  if (!ACENTOS.some((a) => a.id === acento)) return
  guardar(CLAVE_ACENTO, acento)
  aplicar({ ...actual, acento }, { animar: true })
}

function suscribir(fn) {
  oyentes.add(fn)
  return () => oyentes.delete(fn)
}

const leer = () => actual

export function useTema() {
  const { modo, acento } = useSyncExternalStore(suscribir, leer)
  return { modo, acento, fijarModo, fijarAcento }
}
