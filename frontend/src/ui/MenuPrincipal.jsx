// MenuPrincipal (4.5.2, «Menú principal»; 4.5.1, «Navegación»).
// - Los 8 elementos, siempre en el mismo orden (3.2.3), como lista visible (el menú
//   desplegable por debajo de 1280 px quedó en el nivel 1 de recorte).
// - La pantalla actual lleva aria-current="page", fondo bgPrimaryWash y una barra de
//   3 px en bgPrimary (1.4.1; 1.3.1). Transacciones se marca en V-06 y en V-07.
// - El portafolio activo es el de la ruta; si no, el que guarda la sesión; si no, el
//   primero de la lista. Sin portafolios, Tablero, Posiciones y Transacciones llevan a V-08.
// - Al pie, el correo de la cuenta y «Cerrar sesión» (E05; N-06).
import { useState } from 'react'
import { listarPortafolios } from '../api/operaciones.js'
import { useConsulta } from '../api/useConsulta.js'
import { Enlace } from '../rutas/Enlace.jsx'
import { useRuta } from '../rutas/navegacion.js'
import { useSesion } from '../sesion/useSesion.js'
import '../estilos/controles.css'
import '../estilos/plantilla.css'

export function MenuPrincipal({ pantalla }) {
  const { cuenta, cerrar, portafolioActivo } = useSesion()
  const { params } = useRuta()
  const [cerrando, setCerrando] = useState(false)

  const idRuta = params?.id ?? null
  const idSesion = portafolioActivo ?? null
  // Solo se consulta la lista, con sesión, si ni la ruta ni la sesión dicen cuál es el activo.
  const necesitaLista = !!cuenta && !idRuta && !idSesion
  const lista = useConsulta(() => (necesitaLista ? listarPortafolios() : null), [necesitaLista])
  const primero = Array.isArray(lista.datos) && lista.datos.length > 0 ? String(lista.datos[0].id) : null
  const idActivo = idRuta ?? idSesion ?? primero
  const sinPortafolios = necesitaLista && Array.isArray(lista.datos) && lista.datos.length === 0

  const delPortafolio = (seccion) => (idActivo && !sinPortafolios ? `/portafolios/${idActivo}/${seccion}` : '/portafolios')

  const elementos = [
    { texto: 'Tablero', a: sinPortafolios ? '/portafolios' : '/tablero', pantallas: ['V-04'] },
    { texto: 'Posiciones', a: delPortafolio('posiciones'), pantallas: ['V-05'] },
    { texto: 'Transacciones', a: delPortafolio('transacciones'), pantallas: ['V-06', 'V-07'] },
    { texto: 'Portafolios', a: '/portafolios', pantallas: ['V-08'] },
    { texto: 'Intermediarios', a: '/intermediarios', pantallas: ['V-09'] },
    { texto: 'Catálogo', a: '/catalogo', pantallas: ['V-10'] },
    { texto: 'Cuenta', a: '/cuenta', pantallas: ['V-11'] },
    { texto: 'Aviso de privacidad', a: '/aviso-privacidad', pantallas: ['V-03'] },
  ]

  return (
    <nav className="menu" aria-label="Menú principal">
      <ul className="menu__lista">
        {elementos.map((el) => (
          <li key={el.texto}>
            <Enlace a={el.a} actual={el.pantallas.includes(pantalla)} className="menu__enlace">
              {el.texto}
            </Enlace>
          </li>
        ))}
      </ul>
      <div className="menu__pie">
        {cuenta?.correo && (
          <p className="menu__correo">
            <span className="visualmente-oculto">Sesión iniciada como </span>
            {cuenta.correo}
          </p>
        )}
        <button
          type="button"
          className="boton boton--secundario menu__cerrar"
          aria-disabled={cerrando ? 'true' : undefined}
          onClick={async () => {
            if (cerrando) return
            setCerrando(true)
            try {
              await cerrar()
            } finally {
              setCerrando(false)
            }
          }}
        >
          {cerrando ? 'Cerrando sesión…' : 'Cerrar sesión'}
        </button>
      </div>
    </nav>
  )
}

export default MenuPrincipal
