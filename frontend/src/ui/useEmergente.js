// Estado de un panel emergente (menú de la persona, «Más» del rail, selector de acento).
// Se cierra con Esc (y el foco vuelve al botón), al hacer clic fuera o cuando el foco sale del
// botón y del panel. Al elegir algo del panel, cerrar({ devolverFoco: true }) devuelve el foco al
// botón; si además se navega, la pantalla nueva lo lleva a su h1.
// useEmergente() → { abierto, setAbierto, cerrar, refBoton, refPanel }.
import { useCallback, useEffect, useRef, useState } from 'react'

export function useEmergente() {
  const [abierto, setAbierto] = useState(false)
  const refBoton = useRef(null)
  const refPanel = useRef(null)

  const cerrar = useCallback(({ devolverFoco = false } = {}) => {
    setAbierto(false)
    if (devolverFoco) refBoton.current?.focus()
  }, [])

  useEffect(() => {
    if (!abierto) return undefined
    const dentro = (nodo) => refPanel.current?.contains(nodo) || refBoton.current?.contains(nodo)
    // Un clic en una parte del panel que no recibe el foco (o en un botón, en Safari) lo manda al
    // ancestro enfocable más cercano (<main tabIndex=-1>): eso no es salir del panel. El clic fuera
    // ya lo cierra alApuntar.
    const esAncestro = (nodo) =>
      nodo instanceof Node && (nodo.contains(refPanel.current) || nodo.contains(refBoton.current))
    const alApuntar = (e) => {
      if (!dentro(e.target)) cerrar()
    }
    const alEnfocar = (e) => {
      if (!dentro(e.target) && !esAncestro(e.target)) cerrar()
    }
    const alTeclear = (e) => {
      if (e.key === 'Escape') cerrar({ devolverFoco: true })
    }
    document.addEventListener('pointerdown', alApuntar)
    document.addEventListener('focusin', alEnfocar)
    document.addEventListener('keydown', alTeclear)
    return () => {
      document.removeEventListener('pointerdown', alApuntar)
      document.removeEventListener('focusin', alEnfocar)
      document.removeEventListener('keydown', alTeclear)
    }
  }, [abierto, cerrar])

  return { abierto, setAbierto, cerrar, refBoton, refPanel }
}
