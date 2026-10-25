// Tooltip del sistema «Proyecto 077 UI»: etiqueta breve (t-tooltip) que nombra un control de solo
// ícono al pasar el puntero (tras 300 ms) o al enfocarlo (de inmediato).
// - children(id) recibe el id de la etiqueta, para conectarla con aria-labelledby (si es el nombre)
//   o aria-describedby (si es información extra).
// - Se puede pasar el puntero sobre la etiqueta y Esc la oculta hasta salir del control (1.4.13).
// - lado: 'right' (rail), 'bottom' (encabezado y tarjetas), 'bottom-end' o 'left' (junto al borde
//   derecho) o 'top'.
// - `desactivada` la oculta mientras el control tiene abierto su propio panel.
import { useEffect, useId, useState } from 'react'

export function AyudaEmergente({ texto, lado = 'bottom', desactivada = false, className, children }) {
  const id = useId()
  const [oculto, setOculto] = useState(false)
  const [encima, setEncima] = useState(false)

  // Con el puntero encima, Esc oculta la etiqueta aunque el foco esté en otra parte.
  useEffect(() => {
    if (!encima) return undefined
    const alTeclear = (e) => {
      if (e.key === 'Escape') setOculto(true)
    }
    document.addEventListener('keydown', alTeclear)
    return () => document.removeEventListener('keydown', alTeclear)
  }, [encima])

  return (
    <span
      className={['p77-has-tooltip', className].filter(Boolean).join(' ')}
      data-oculto={oculto || desactivada ? '' : undefined}
      onMouseEnter={() => setEncima(true)}
      onMouseLeave={() => {
        setEncima(false)
        setOculto(false)
      }}
      onBlur={() => setOculto(false)}
      onKeyDown={(e) => {
        if (e.key === 'Escape') setOculto(true)
      }}
    >
      {children(id)}
      <span role="tooltip" id={id} className={`p77-tooltip p77-tooltip--${lado}`}>
        {texto}
      </span>
    </span>
  )
}

export default AyudaEmergente
