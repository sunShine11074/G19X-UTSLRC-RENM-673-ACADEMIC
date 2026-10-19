// Mensajes de estado y estado sin datos (B3; SRS 4.5.1, «Componentes»; RF-11 crit. 3; 4.1.3).
// Contrato del Anexo A: MensajeEstado y EstadoSinDatos({fechaCorte, idPortafolio}).
import { navegar } from '../rutas/navegacion.js'
import { MENSAJES } from '../textos/textos.js'
import { Boton } from './Boton.jsx'
import './datos.css'

/**
 * Región viva que anuncia el resultado de una acción sin mover el foco (4.1.3).
 * Se deja siempre montada (aunque vacía) para que el lector de pantalla anuncie el cambio.
 * tipo 'error' usa role="alert"; los demás, role="status". Sin animación (2.2.2).
 */
export function MensajeEstado({ tipo, children, ...resto }) {
  const esError = tipo === 'error'
  return (
    <p
      className={esError ? 'mensaje-estado mensaje-estado--error' : 'mensaje-estado'}
      role={esError ? 'alert' : 'status'}
      data-tipo={tipo}
      {...resto}
    >
      {children}
    </p>
  )
}

/**
 * Estado sin datos del tablero (RF-11 crit. 3): el portafolio no tiene transacciones hasta el
 * corte. `fechaCorte` llega como AAAA-MM-DD; el botón lleva a V-07 del portafolio (N-13).
 */
export function EstadoSinDatos({ fechaCorte, idPortafolio }) {
  return (
    <div className="estado-sin-datos" role="status">
      <p>
        {fechaCorte ? MENSAJES.sinDatos(fechaCorte) : 'Este portafolio no tiene transacciones.'}
      </p>
      {idPortafolio != null && (
        <Boton variante="primaria" onClick={() => navegar(`/portafolios/${idPortafolio}/transacciones/nueva`)}>
          {MENSAJES.registrarTransaccion}
        </Boton>
      )}
    </div>
  )
}
