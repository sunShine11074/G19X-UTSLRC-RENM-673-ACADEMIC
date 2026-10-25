// TopBar del sistema «Proyecto 077 UI»: el h1 de la pantalla (t-display) a la izquierda y, a la
// derecha, ThemeControls y el menú de la persona; las mismas posiciones en todas las pantallas.
// - El h1 recibe el foco al cambiar de pantalla (Plantilla), por eso lleva tabIndex -1.
// - Menú de la persona: botón con el correo (oculto a la vista debajo de 768 px) y su inicial en el
//   avatar; abre «Cuenta» y «Cerrar sesión» (E05; N-06). Se cierra con Esc o al salir de él.
import { faCircleUser, faRightFromBracket } from '@fortawesome/free-solid-svg-icons'
import { useId, useState } from 'react'
import { Enlace } from '../rutas/Enlace.jsx'
import { useSesion } from '../sesion/useSesion.js'
import { ControlesTema } from './ControlesTema.jsx'
import { Icono } from './Icono.jsx'
import { useEmergente } from './useEmergente.js'

function MenuPersona({ correo, cerrarSesion }) {
  const { abierto, setAbierto, cerrar, refBoton, refPanel } = useEmergente()
  const [cerrando, setCerrando] = useState(false)
  const idMenu = useId()

  return (
    <div className="persona">
      <button
        ref={refBoton}
        type="button"
        className="p77-user"
        aria-expanded={abierto ? 'true' : 'false'}
        aria-controls={abierto ? idMenu : undefined}
        onClick={() => setAbierto((v) => !v)}
      >
        <span className="p77-user__nombre">
          <span className="visualmente-oculto">Sesión iniciada como </span>
          {correo}
        </span>
        <span className="p77-avatar p77-avatar--lg" aria-hidden="true">
          {correo.slice(0, 1).toUpperCase()}
        </span>
      </button>
      {abierto && (
        <div ref={refPanel} id={idMenu} className="p77-menu">
          <p className="p77-menu__encabezado">
            Sesión iniciada como <strong>{correo}</strong>
          </p>
          <Enlace a="/cuenta" className="p77-menu__item" onClick={() => cerrar({ devolverFoco: true })}>
            <Icono icono={faCircleUser} />
            Cuenta
          </Enlace>
          <button
            type="button"
            className="p77-menu__item"
            aria-disabled={cerrando ? 'true' : undefined}
            onClick={async () => {
              if (cerrando) return
              setCerrando(true)
              try {
                await cerrarSesion()
              } finally {
                setCerrando(false)
              }
            }}
          >
            <Icono icono={faRightFromBracket} />
            {cerrando ? 'Cerrando sesión…' : 'Cerrar sesión'}
          </button>
        </div>
      )}
    </div>
  )
}

export function BarraSuperior({ titulo, refTitulo, conControles = true }) {
  const { cuenta, cerrar } = useSesion() ?? {}
  return (
    <header className="p77-topbar">
      <h1 ref={refTitulo} tabIndex={-1} className="p77-topbar__title">
        {titulo}
      </h1>
      {conControles && (
        <div className="p77-topbar__actions">
          <ControlesTema />
        </div>
      )}
      {cuenta?.correo && <MenuPersona correo={cuenta.correo} cerrarSesion={cerrar} />}
    </header>
  )
}

export default BarraSuperior
