// ResumenError({errores:[{campo, mensaje}]}) (Anexo A; 4.5.1, «Mensaje de error del formulario»).
// - Resumen sobre el formulario, con role="alert", que recibe el foco cada vez que
//   llega una lista nueva (3.3.1; 4.1.3). data-recorrido="resumen-error".
// - `campo` es el id del control en la página: si existe, el motivo es un enlace que
//   lleva el foco a ese control. Sin `campo`, el motivo va solo en el resumen (H-8).
// - Nunca muestra el nombre del campo de la API, solo el mensaje.
import { faTriangleExclamation } from '@fortawesome/free-solid-svg-icons'
import { useEffect, useRef } from 'react'
import '../estilos/controles.css'
import { Icono } from './Icono.jsx'

export function ResumenError({ errores, titulo }) {
  const ref = useRef(null)
  const hay = Array.isArray(errores) && errores.length > 0

  useEffect(() => {
    if (hay && ref.current) ref.current.focus()
  }, [errores, hay])

  if (!hay) return null
  const encabezado = titulo ?? (errores.length === 1 ? 'No se pudo completar' : 'Revisa lo siguiente')
  return (
    <div ref={ref} role="alert" tabIndex={-1} className="resumen-error" data-recorrido="resumen-error">
      <p className="resumen-error__titulo">
        <span className="resumen-error__icono">
          <Icono icono={faTriangleExclamation} />
        </span>
        {encabezado}
      </p>
      <ul className="resumen-error__lista">
        {errores.map((e, i) => (
          <li key={`${e.campo ?? ''}-${i}`}>
            {e.campo ? (
              <a
                href={`#${e.campo}`}
                onClick={(ev) => {
                  const destino = document.getElementById(e.campo)
                  if (!destino) return
                  ev.preventDefault()
                  destino.focus()
                }}
              >
                {e.mensaje}
              </a>
            ) : (
              e.mensaje
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default ResumenError
