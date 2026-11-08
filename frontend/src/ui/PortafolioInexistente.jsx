// PortafolioInexistente: V-12 para un portafolio ajeno o inexistente (SRS 4.5.2, N-08; RF-02 crit. 2;
// RNF-03). Lo usan las pantallas con :id en la ruta (V-04, V-05, V-06 y V-07) en lugar de su
// contenido, cuando la API responde el 404 del portafolio (esPortafolioInexistente).
// - El portafolio deja de ser el activo, para que el menú no vuelva a llevar a él.
// - Se ve igual en las cuatro rutas: «No encontrado» como h1, pantalla V-12 y el mismo texto para
//   lo ajeno y lo inexistente, «No existe el portafolio.».
import { useEffect } from 'react'
import { useSesion } from '../sesion/useSesion.js'
import { MENSAJES } from '../textos/textos.js'
import { NoEncontrado } from './NoEncontrado.jsx'
import { Plantilla } from './Plantilla.jsx'

export function PortafolioInexistente() {
  const { fijarPortafolioActivo } = useSesion()
  useEffect(() => {
    fijarPortafolioActivo?.(null)
  }, [fijarPortafolioActivo])

  return (
    <Plantilla titulo="No encontrado" pantalla="V-12" listo>
      <NoEncontrado mensaje={MENSAJES.portafolioInexistente} />
    </Plantilla>
  )
}

export default PortafolioInexistente
