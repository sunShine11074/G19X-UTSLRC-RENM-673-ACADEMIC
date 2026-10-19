// SesionProvider (Anexo A). El navegador no puede leer la cookie (HttpOnly), así que el
// estado de la sesión sale de E06: 200 con sesión, 401 sin ella (N-01).
import { useCallback, useEffect, useMemo, useState } from 'react'
import { alTerminarSesion } from '../api/cliente.js'
import { cerrarSesion, iniciarSesion, verCuenta } from '../api/operaciones.js'
import { navegar, rutaActual } from '../rutas/navegacion.js'
import { MENSAJES } from '../textos/textos.js'
import { ContextoSesion } from './useSesion.js'

export function SesionProvider({ children }) {
  const [cuenta, setCuenta] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [portafolioActivo, setPortafolioActivo] = useState(null)

  const refrescar = useCallback(async () => {
    try {
      const c = await verCuenta({ sin401: true })
      setCuenta(c)
      return c
    } catch (e) {
      if (e?.estado === 401) {
        setCuenta(null)
        return null
      }
      throw e
    } finally {
      setCargando(false)
    }
  }, [])

  // N-01: al cargar, E06 dice si hay sesión.
  useEffect(() => {
    let vigente = true
    verCuenta({ sin401: true })
      .then(
        (c) => vigente && setCuenta(c),
        () => vigente && setCuenta(null),
      )
      .finally(() => vigente && setCargando(false))
    return () => {
      vigente = false
    }
  }, [])

  // N-07: una operación con sesión respondió 401 (sesión vencida, revocada o clave cambiada).
  useEffect(
    () =>
      alTerminarSesion(() => {
        setCuenta(null)
        setPortafolioActivo(null)
        const { ruta, busqueda } = rutaActual()
        if (ruta !== '/sesion') {
          navegar('/sesion', {
            reemplazar: true,
            estado: { destino: ruta + busqueda, mensaje: MENSAJES.sesionTerminada ?? 'Inicia sesión para continuar.' },
          })
        }
      }),
    [],
  )

  const iniciar = useCallback(
    async (correo, contrasena) => {
      await iniciarSesion({ correo, contrasena })
      return refrescar()
    },
    [refrescar],
  )

  const cerrar = useCallback(async ({ mensaje } = {}) => {
    try {
      await cerrarSesion()
    } finally {
      setCuenta(null)
      setPortafolioActivo(null)
      navegar('/sesion', {
        reemplazar: true,
        estado: { mensaje: mensaje ?? MENSAJES.sesionCerrada ?? 'Cerraste tu sesión.' },
      })
    }
  }, [])

  // Para la revocación (N-09): la API ya borró la cookie; solo se descarta lo guardado.
  const olvidar = useCallback(() => {
    setCuenta(null)
    setPortafolioActivo(null)
  }, [])

  const fijarPortafolioActivo = useCallback((id) => {
    setPortafolioActivo(id === null || id === undefined ? null : String(id))
  }, [])

  const valor = useMemo(
    () => ({ cuenta, cargando, iniciar, cerrar, refrescar, olvidar, portafolioActivo, fijarPortafolioActivo }),
    [cuenta, cargando, iniciar, cerrar, refrescar, olvidar, portafolioActivo, fijarPortafolioActivo],
  )

  return <ContextoSesion.Provider value={valor}>{children}</ContextoSesion.Provider>
}

export default SesionProvider
