// <Enlace a estado> (Anexo A): un <a href> real que navega sin recargar y marca
// aria-current="page" cuando su ruta es la actual (o, con `seccion`, cuando la actual empieza por ella).
import { navegar, useRuta } from './navegacion.js'

export function Enlace({ a, estado, reemplazar, seccion, actual, children, onClick, ...resto }) {
  const { ruta } = useRuta()
  const destino = a.split('?')[0]
  const esActual = actual ?? (seccion ? ruta === seccion || ruta.startsWith(seccion + '/') : ruta === destino)
  return (
    <a
      href={a}
      aria-current={esActual ? 'page' : undefined}
      onClick={(e) => {
        onClick?.(e)
        if (e.defaultPrevented) return
        if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return
        e.preventDefault()
        navegar(a, { estado, reemplazar })
      }}
      {...resto}
    >
      {children}
    </a>
  )
}

export default Enlace
