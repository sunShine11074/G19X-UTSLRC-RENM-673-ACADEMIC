// MenuPrincipal: el NavRail del sistema «Proyecto 077 UI» (4.5.2, «Menú principal»).
// - Rail negro con el logo (enlace al tablero), los 6 destinos principales y, abajo, Aviso de
//   privacidad y Cuenta sin círculo; siempre en el mismo orden (3.2.3). Cada destino es un enlace
//   con URL propia, ícono de Font Awesome y Tooltip a la derecha que es su nombre accesible.
// - La pantalla actual lleva aria-current="page" y se pinta en rail-accent (1.4.1: además del
//   color, el Tooltip y el h1 dicen dónde se está). Transacciones se marca en V-06 y en V-07.
// - Debajo de 768 px el rail es una barra inferior con 4 destinos y «Más», que abre la lista de
//   los demás con su texto.
// - El portafolio activo es el de la ruta; si no, el que guarda la sesión; si no, el primero de la
//   lista. Sin portafolios, Tablero, Posiciones y Transacciones llevan a V-08.
// - El correo de la cuenta y «Cerrar sesión» están en el menú de la persona (BarraSuperior; E05; N-06).
import {
  faArrowRightArrowLeft,
  faBriefcase,
  faBuildingColumns,
  faChartPie,
  faEllipsis,
  faCircleUser,
  faHouse,
  faShieldHalved,
  faTableList,
} from '@fortawesome/free-solid-svg-icons'
import { useId } from 'react'
import { listarPortafolios } from '../api/operaciones.js'
import { useConsulta } from '../api/useConsulta.js'
import logo from '../assets/logo-077.png'
import { Enlace } from '../rutas/Enlace.jsx'
import { useRuta } from '../rutas/navegacion.js'
import { useSesion } from '../sesion/useSesion.js'
import { AyudaEmergente } from './AyudaEmergente.jsx'
import { Icono } from './Icono.jsx'
import { useEmergente } from './useEmergente.js'

// En la barra inferior caben los primeros 4 destinos principales; el resto va en «Más».
const EN_BARRA = 4

function Destino({ el, actual, sencillo }) {
  return (
    <AyudaEmergente texto={el.texto} lado="right">
      {(id) => (
        <Enlace
          a={el.a}
          actual={actual}
          className={sencillo ? 'p77-rail__item p77-rail__item--plain' : 'p77-rail__item'}
          aria-labelledby={id}
        >
          <Icono icono={el.icono} />
        </Enlace>
      )}
    </AyudaEmergente>
  )
}

function Mas({ elementos, pantalla }) {
  const { abierto, setAbierto, cerrar, refBoton, refPanel } = useEmergente()
  const idLista = useId()
  const dentro = elementos.some((el) => el.pantallas.includes(pantalla))
  return (
    <div className="rail__mas">
      <AyudaEmergente texto="Más" lado="right" desactivada={abierto}>
        {(id) => (
          <button
            ref={refBoton}
            type="button"
            className="p77-rail__item"
            aria-labelledby={id}
            aria-expanded={abierto ? 'true' : 'false'}
            aria-controls={abierto ? idLista : undefined}
            data-actual={dentro ? '' : undefined}
            onClick={() => setAbierto((v) => !v)}
          >
            <Icono icono={faEllipsis} />
          </button>
        )}
      </AyudaEmergente>
      {abierto && (
        <ul ref={refPanel} id={idLista} className="p77-menu">
          {elementos.map((el) => (
            <li key={el.texto}>
              <Enlace
                a={el.a}
                actual={el.pantallas.includes(pantalla)}
                className="p77-menu__item"
                onClick={() => cerrar({ devolverFoco: true })}
              >
                <Icono icono={el.icono} />
                {el.texto}
              </Enlace>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function MenuPrincipal({ pantalla }) {
  const { cuenta, portafolioActivo } = useSesion()
  const { params } = useRuta()

  const idRuta = params?.id ?? null
  const idSesion = portafolioActivo ?? null
  // Solo se consulta la lista, con sesión, si ni la ruta ni la sesión dicen cuál es el activo.
  const necesitaLista = !!cuenta && !idRuta && !idSesion
  const lista = useConsulta(() => (necesitaLista ? listarPortafolios() : null), [necesitaLista])
  const primero = Array.isArray(lista.datos) && lista.datos.length > 0 ? String(lista.datos[0].id) : null
  const idActivo = idRuta ?? idSesion ?? primero
  const sinPortafolios = necesitaLista && Array.isArray(lista.datos) && lista.datos.length === 0

  const delPortafolio = (seccion) => (idActivo && !sinPortafolios ? `/portafolios/${idActivo}/${seccion}` : '/portafolios')
  const tablero = sinPortafolios ? '/portafolios' : '/tablero'

  const principales = [
    { texto: 'Tablero', icono: faHouse, a: tablero, pantallas: ['V-04'] },
    { texto: 'Posiciones', icono: faChartPie, a: delPortafolio('posiciones'), pantallas: ['V-05'] },
    { texto: 'Transacciones', icono: faArrowRightArrowLeft, a: delPortafolio('transacciones'), pantallas: ['V-06', 'V-07'] },
    { texto: 'Portafolios', icono: faBriefcase, a: '/portafolios', pantallas: ['V-08'] },
    { texto: 'Intermediarios', icono: faBuildingColumns, a: '/intermediarios', pantallas: ['V-09'] },
    { texto: 'Catálogo', icono: faTableList, a: '/catalogo', pantallas: ['V-10'] },
  ]
  const utilidades = [
    { texto: 'Aviso de privacidad', icono: faShieldHalved, a: '/aviso-privacidad', pantallas: ['V-03'] },
    { texto: 'Cuenta', icono: faCircleUser, a: '/cuenta', pantallas: ['V-11'] },
  ]

  return (
    <nav className="p77-rail" aria-label="Menú principal">
      <Enlace a={tablero} actual={false} className="p77-rail__logo-enlace">
        <img className="p77-rail__logo" src={logo} width="44" height="44" alt="Proyecto 077, ir al tablero" />
      </Enlace>
      <ul className="p77-rail__list">
        {principales.map((el, i) => (
          <li key={el.texto} className={i >= EN_BARRA ? 'rail__solo-escritorio' : undefined}>
            <Destino el={el} actual={el.pantallas.includes(pantalla)} />
          </li>
        ))}
        <li className="rail__mas-elemento">
          <Mas elementos={[...principales.slice(EN_BARRA), ...utilidades]} pantalla={pantalla} />
        </li>
      </ul>
      <div className="p77-rail__spacer" />
      <ul className="p77-rail__list rail__utilidades">
        {utilidades.map((el) => (
          <li key={el.texto}>
            <Destino el={el} actual={el.pantallas.includes(pantalla)} sencillo />
          </li>
        ))}
      </ul>
    </nav>
  )
}

export default MenuPrincipal
