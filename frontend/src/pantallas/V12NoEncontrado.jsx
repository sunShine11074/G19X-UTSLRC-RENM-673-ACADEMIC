// V-12 No encontrado (ruta desconocida; RF-02 crit. 2; RNF-03; 4.5.2).
// Con sesión y sin ella: «No existe esta página.» y un enlace a Portafolios o, sin sesión,
// a Inicio de sesión. El portafolio ajeno o inexistente lo muestra V-04 (y las demás
// pantallas con :id) con NoEncontrado y «No existe el portafolio.» (N-08).
import { useSesion } from '../sesion/useSesion.js'
import { MENSAJES } from '../textos/textos.js'
import { NoEncontrado } from '../ui/NoEncontrado.jsx'
import { Plantilla, PlantillaPublica } from '../ui/Plantilla.jsx'
import './cuentas.css'

export default function V12NoEncontrado() {
  const { cuenta } = useSesion()
  const Marco = cuenta ? Plantilla : PlantillaPublica
  return (
    <Marco titulo="No encontrado" pantalla="V-12" listo>
      <NoEncontrado mensaje={MENSAJES.paginaInexistente} />
    </Marco>
  )
}
