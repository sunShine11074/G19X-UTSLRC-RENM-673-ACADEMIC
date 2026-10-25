// Etiqueta «Datos de demostración» (B3; RF-07 crit. 3; RF-04 crit. 3; RF-31 crit. 3; H-6).
// Texto e ícono, no solo color (1.4.1); en warning sobre warning-soft; no se puede cerrar.
// Va en la misma celda o el mismo encabezado que la cifra que marca.
import { faFlask } from '@fortawesome/free-solid-svg-icons'
import './datos.css'
import { Icono } from './Icono.jsx'

export function EtiquetaDemo() {
  return (
    <span className="etiqueta-demo">
      <Icono icono={faFlask} />
      Datos de demostración
    </span>
  )
}

export default EtiquetaDemo
