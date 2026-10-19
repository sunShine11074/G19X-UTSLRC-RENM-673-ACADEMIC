// No encontrado (B3; SRS 4.5.2, V-12 y N-08; RF-02 crit. 2; RNF-03).
// Contrato del Anexo A: NoEncontrado({mensaje}).
// Muestra el mensaje tal como llega (p. ej. «No existe el portafolio.», el mismo para lo ajeno
// y lo inexistente) y enlaza a Portafolios o, sin sesión, a Inicio de sesión.
// El h1 lo pone la plantilla de la pantalla que lo usa.
import { Enlace } from '../rutas/Enlace.jsx'
import { useSesion } from '../sesion/useSesion.js'
import { MENSAJES } from '../textos/textos.js'
import './datos.css'

export function NoEncontrado({ mensaje = MENSAJES.paginaInexistente }) {
  const { cuenta } = useSesion() ?? {}
  return (
    <div className="no-encontrado" data-recorrido="no-encontrado">
      <p className="no-encontrado-mensaje">{mensaje}</p>
      <p>
        {cuenta ? (
          <Enlace a="/portafolios">{MENSAJES.irAPortafolios}</Enlace>
        ) : (
          <Enlace a="/sesion">{MENSAJES.irAInicioSesion}</Enlace>
        )}
      </p>
    </div>
  )
}

export default NoEncontrado
