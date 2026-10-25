// Ícono de Font Awesome Free 7, estilo solid (sistema «Proyecto 077 UI», «Iconografía»).
// - Siempre decorativo (aria-hidden): el nombre accesible lo lleva el control o el texto de al lado.
// - El tamaño sale del contenedor (size-icon, size-icon-sm) y el color, de `color`.
// - El CSS de Font Awesome entra con el paquete, no en tiempo de ejecución (sin estilos en línea).
// Íconos de Font Awesome Free: CC BY 4.0; código: MIT (https://fontawesome.com/license/free).
import { config } from '@fortawesome/fontawesome-svg-core'
import { faTriangleExclamation } from '@fortawesome/free-solid-svg-icons'
import '@fortawesome/fontawesome-svg-core/styles.css'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'

config.autoAddCss = false

export function Icono({ icono, className }) {
  return <FontAwesomeIcon icon={icono} className={className} aria-hidden="true" focusable="false" />
}

// Triángulo de los mensajes de error (sistema, «Iconografía»): acompaña al texto, nunca lo sustituye.
export function IconoError() {
  return <Icono icono={faTriangleExclamation} className="icono-error" />
}

export default Icono
