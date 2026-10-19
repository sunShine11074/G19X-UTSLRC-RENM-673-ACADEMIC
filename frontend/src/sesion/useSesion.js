// Contexto de la sesión y useSesion() (Anexo A):
// {cuenta, cargando, iniciar, cerrar, refrescar, portafolioActivo, fijarPortafolioActivo}.
// El portafolio activo vive en memoria (H-2; el sessionStorage quedó en el nivel 1 de recorte).
import { createContext, useContext } from 'react'

export const ContextoSesion = createContext(null)

export function useSesion() {
  const valor = useContext(ContextoSesion)
  if (!valor) throw new Error('useSesion necesita SesionProvider.')
  return valor
}

export default useSesion
