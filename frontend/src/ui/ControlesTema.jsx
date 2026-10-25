// ThemeControls del sistema «Proyecto 077 UI»: selector del color de acento y cambio de modo
// claro/oscuro; juntos fijan data-theme en <html> (tema.js guarda la elección).
// - Selector: botón con el punto del acento (aria-expanded) que abre un grupo de 4 muestras
//   (role="radiogroup"). Al abrir, el foco va a la muestra elegida; las flechas cambian el acento,
//   Enter o un clic lo confirman y cierran, y Esc cierra y devuelve el foco al botón.
// - La muestra lima sobre surface-control en modo claro tiene contraste bajo (1.3:1): cada muestra
//   lleva su nombre en aria-label y en Tooltip, y la elegida, un anillo en ink.
// - Modo: botón role="switch" «Modo oscuro»; muestra el sol en claro y la luna en oscuro.
import { faMoon, faSun } from '@fortawesome/free-solid-svg-icons'
import { useEffect, useId, useRef } from 'react'
import { ACENTOS, useTema } from '../tema/tema.js'
import { AyudaEmergente } from './AyudaEmergente.jsx'
import { Icono } from './Icono.jsx'
import { useEmergente } from './useEmergente.js'

const TECLAS_ANTERIOR = ['ArrowUp', 'ArrowLeft']
const TECLAS_SIGUIENTE = ['ArrowDown', 'ArrowRight']

function SelectorAcento() {
  const { acento, fijarAcento } = useTema()
  const { abierto, setAbierto, cerrar, refBoton, refPanel } = useEmergente()
  const idPanel = useId()
  const muestras = useRef({})
  const nombre = ACENTOS.find((a) => a.id === acento)?.nombre ?? ''

  // Al abrir, el foco entra a la muestra elegida (Tab entra a la seleccionada).
  useEffect(() => {
    if (abierto) muestras.current[acento]?.focus()
    // Solo al abrir; al cambiar con las flechas el foco ya se movió.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [abierto])

  function alTeclear(e, i) {
    let siguiente = null
    if (TECLAS_ANTERIOR.includes(e.key)) siguiente = (i - 1 + ACENTOS.length) % ACENTOS.length
    else if (TECLAS_SIGUIENTE.includes(e.key)) siguiente = (i + 1) % ACENTOS.length
    else if (e.key === 'Home') siguiente = 0
    else if (e.key === 'End') siguiente = ACENTOS.length - 1
    else if (e.key === 'Enter') {
      e.preventDefault()
      cerrar({ devolverFoco: true })
      return
    }
    if (siguiente === null) return
    e.preventDefault()
    const id = ACENTOS[siguiente].id
    fijarAcento(id)
    muestras.current[id]?.focus()
  }

  return (
    <div className="p77-theme__accent">
      <AyudaEmergente texto="Color de acento" desactivada={abierto}>
        {(idAyuda) => (
          <button
            ref={refBoton}
            type="button"
            className="p77-icon-btn"
            aria-label={`Color de acento: ${nombre}`}
            aria-describedby={idAyuda}
            aria-expanded={abierto ? 'true' : 'false'}
            aria-controls={abierto ? idPanel : undefined}
            onClick={() => setAbierto((v) => !v)}
          >
            <span className="p77-icon-btn__dot" />
          </button>
        )}
      </AyudaEmergente>
      {abierto && (
        <div ref={refPanel} id={idPanel} className="p77-swatches" role="radiogroup" aria-label="Color de acento">
          {ACENTOS.map((a, i) => (
            <AyudaEmergente key={a.id} texto={a.nombre} lado="left">
              {() => (
                <button
                  ref={(nodo) => {
                    muestras.current[a.id] = nodo
                  }}
                  type="button"
                  role="radio"
                  aria-checked={a.id === acento ? 'true' : 'false'}
                  aria-label={a.nombre}
                  tabIndex={a.id === acento ? 0 : -1}
                  className={`p77-swatch p77-swatch--${a.id}`}
                  onClick={() => {
                    fijarAcento(a.id)
                    cerrar({ devolverFoco: true })
                  }}
                  onKeyDown={(e) => alTeclear(e, i)}
                />
              )}
            </AyudaEmergente>
          ))}
        </div>
      )}
    </div>
  )
}

function CambioModo() {
  const { modo, fijarModo } = useTema()
  const oscuro = modo === 'dark'
  return (
    <AyudaEmergente texto="Modo oscuro" lado="bottom-end">
      {() => (
        <button
          type="button"
          role="switch"
          aria-checked={oscuro ? 'true' : 'false'}
          aria-label="Modo oscuro"
          className="p77-icon-btn"
          onClick={() => fijarModo(oscuro ? 'light' : 'dark')}
        >
          <Icono icono={oscuro ? faMoon : faSun} />
        </button>
      )}
    </AyudaEmergente>
  )
}

export function ControlesTema() {
  return (
    <div className="p77-theme">
      <SelectorAcento />
      <CambioModo />
    </div>
  )
}

export default ControlesTema
