// useConsulta(fn, deps) → {datos, error, cargando, recargar} (Anexo A).
// Ejecuta fn() al montar y cada vez que cambian deps (valores simples: ids y fechas) o se
// llama recargar(). La respuesta de una consulta anterior que llega tarde se descarta.
// Mientras carga, `datos` conserva la respuesta anterior; las pantallas usan `cargando`
// para no marcar data-listo.
import { useCallback, useEffect, useRef, useState } from 'react'

export function useConsulta(fn, deps = []) {
  const [vuelta, setVuelta] = useState(0)
  const clave = JSON.stringify([...deps, vuelta])
  const [resultado, setResultado] = useState({ clave: null, datos: null, error: null })
  const fnRef = useRef(fn)

  useEffect(() => {
    fnRef.current = fn
  })

  useEffect(() => {
    let vigente = true
    Promise.resolve()
      .then(() => fnRef.current())
      .then(
        (datos) => {
          if (vigente) setResultado({ clave, datos, error: null })
        },
        (error) => {
          if (vigente) setResultado({ clave, datos: null, error })
        },
      )
    return () => {
      vigente = false
    }
  }, [clave])

  const recargar = useCallback(() => setVuelta((v) => v + 1), [])
  const cargando = resultado.clave !== clave
  return { datos: resultado.datos, error: cargando ? null : resultado.error, cargando, recargar }
}

export default useConsulta
