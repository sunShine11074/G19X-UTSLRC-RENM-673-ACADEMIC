// Raíz del cliente web: rutas de 4.5.2 con el enrutador propio (H-2), guardas N-01 y N-02,
// y cada pantalla con React.lazy dentro de su propio LimiteError (plan del 18 oct, «Aislamiento de errores»).
import { lazy, Suspense, useEffect } from 'react'
import { listarPortafolios } from './api/operaciones.js'
import { LimiteError } from './rutas/LimiteError.jsx'
import { navegar, useRuta } from './rutas/navegacion.js'
import { SesionProvider } from './sesion/SesionProvider.jsx'
import { useSesion } from './sesion/useSesion.js'

const V01 = lazy(() => import('./pantallas/V01InicioSesion.jsx'))
const V02 = lazy(() => import('./pantallas/V02Registro.jsx'))
const V03 = lazy(() => import('./pantallas/V03AvisoPrivacidad.jsx'))
const V04 = lazy(() => import('./pantallas/V04Tablero.jsx'))
const V05 = lazy(() => import('./pantallas/V05Posiciones.jsx'))
const V06 = lazy(() => import('./pantallas/V06Transacciones.jsx'))
const V07 = lazy(() => import('./pantallas/V07RegistrarTransaccion.jsx'))
const V08 = lazy(() => import('./pantallas/V08Portafolios.jsx'))
const V09 = lazy(() => import('./pantallas/V09Intermediarios.jsx'))
const V10 = lazy(() => import('./pantallas/V10Catalogo.jsx'))
const V11 = lazy(() => import('./pantallas/V11Cuenta.jsx'))
const V12 = lazy(() => import('./pantallas/V12NoEncontrado.jsx'))

// sesion: 'si' exige sesión; 'no' es solo sin sesión (con sesión lleva a /tablero, N-01); 'ambas'.
const RUTAS = {
  '/sesion': { Pantalla: V01, sesion: 'no' },
  '/registro': { Pantalla: V02, sesion: 'no' },
  '/aviso-privacidad': { Pantalla: V03, sesion: 'ambas' },
  '/portafolios/:id/tablero': { Pantalla: V04, sesion: 'si' },
  '/portafolios/:id/posiciones': { Pantalla: V05, sesion: 'si' },
  '/portafolios/:id/transacciones': { Pantalla: V06, sesion: 'si' },
  '/portafolios/:id/transacciones/nueva': { Pantalla: V07, sesion: 'si' },
  '/portafolios': { Pantalla: V08, sesion: 'si' },
  '/intermediarios': { Pantalla: V09, sesion: 'si' },
  '/catalogo': { Pantalla: V10, sesion: 'si' },
  '/cuenta': { Pantalla: V11, sesion: 'si' },
}

function Cargando() {
  return (
    <p className="cargando-ruta" role="status">
      Cargando…
    </p>
  )
}

function Redirigir({ a, estado }) {
  useEffect(() => {
    navegar(a, { reemplazar: true, estado })
  }, [a, estado])
  return <Cargando />
}

// N-02: /tablero lleva al tablero del portafolio activo; sin portafolios, a V-08.
function AbrirTablero() {
  const { portafolioActivo, fijarPortafolioActivo } = useSesion()
  useEffect(() => {
    let vigente = true
    listarPortafolios()
      .then((lista) => {
        if (!vigente) return
        if (!lista || lista.length === 0) {
          navegar('/portafolios', { reemplazar: true })
          return
        }
        const activo = lista.find((p) => String(p.id) === portafolioActivo) ?? lista[0]
        fijarPortafolioActivo(activo.id)
        navegar(`/portafolios/${activo.id}/tablero`, { reemplazar: true })
      })
      .catch(() => {
        if (vigente) navegar('/portafolios', { reemplazar: true })
      })
    return () => {
      vigente = false
    }
  }, [portafolioActivo, fijarPortafolioActivo])
  return <Cargando />
}

function Rutas() {
  const { ruta, busqueda, patron, params, estado } = useRuta()
  const { cuenta, cargando, fijarPortafolioActivo } = useSesion()
  const conSesion = !!cuenta

  // Una ruta con :id fija el portafolio activo (vive en memoria; H-2).
  useEffect(() => {
    if (conSesion && params.id) fijarPortafolioActivo(params.id)
  }, [conSesion, params.id, fijarPortafolioActivo])

  if (cargando) return <Cargando />

  // N-01
  if (ruta === '/') return <Redirigir a={conSesion ? '/tablero' : '/sesion'} />
  if (ruta === '/tablero') {
    if (!conSesion) return <Redirigir a="/sesion" estado={{ destino: '/tablero' }} />
    return <AbrirTablero />
  }

  let Pantalla = null
  let regla = 'ambas'
  if (patron && RUTAS[patron]) {
    Pantalla = RUTAS[patron].Pantalla
    regla = RUTAS[patron].sesion
  } else {
    Pantalla = V12
  }

  if (regla === 'si' && !conSesion) {
    return <Redirigir a="/sesion" estado={{ destino: ruta + busqueda }} />
  }
  // N-01 y N-05: con sesión, /sesion y /registro llevan al destino guardado o a /tablero.
  if (regla === 'no' && conSesion) {
    const destino = typeof estado?.destino === 'string' && estado.destino.startsWith('/') ? estado.destino : '/tablero'
    return <Redirigir a={destino} />
  }

  return (
    <LimiteError key={patron ?? 'no-encontrado'} clave={ruta}>
      <Suspense fallback={<Cargando />}>
        <Pantalla key={ruta} />
      </Suspense>
    </LimiteError>
  )
}

export default function App() {
  return (
    <SesionProvider>
      <Rutas />
    </SesionProvider>
  )
}
