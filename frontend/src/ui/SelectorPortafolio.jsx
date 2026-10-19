// Selector de portafolio (B3; SRS 4.5.1, «Selector de portafolio, periodo y corte»; N-16; X-06).
// Contrato del Anexo A: SelectorPortafolio({idActual, alCambiar}).
// - Consulta E12 y lista solo los portafolios del usuario, sin opción «Todos» (X-06).
// - alCambiar recibe el id entero tal como lo dio la API (sin convertir texto a número).
//   La pantalla decide cuándo aplicarlo (con «Consultar», 3.2.2).
// - Opcionales: `id` (por omisión "portafolio-activo"; el <select> lo recibe también como
//   data-recorrido), `etiqueta` y `portafolios` (lista ya consultada, para no repetir E12).
import { listarPortafolios } from '../api/operaciones.js'
import { useConsulta } from '../api/useConsulta.js'
import '../estilos/controles.css'
import './datos.css'

export function SelectorPortafolio({ idActual, alCambiar, id = 'portafolio-activo', etiqueta = 'Portafolio', portafolios }) {
  const consulta = useConsulta(() => (portafolios ? Promise.resolve(portafolios) : listarPortafolios()), [portafolios])
  const lista = portafolios ?? consulta.datos ?? []
  const valor = idActual == null ? '' : String(idActual)

  function cambiar(e) {
    const elegido = lista.find((p) => String(p.id) === e.target.value)
    if (elegido) alCambiar?.(elegido.id)
  }

  return (
    <div className="campo selector-portafolio">
      <label className="campo__etiqueta" htmlFor={id}>
        {etiqueta}
      </label>
      <select
        className="campo__control campo__control--select"
        id={id}
        name={id}
        data-recorrido={id}
        value={valor}
        onChange={cambiar}
        disabled={!portafolios && consulta.cargando && lista.length === 0}
      >
        {valor === '' && <option value="">Elige un portafolio</option>}
        {valor !== '' && !lista.some((p) => String(p.id) === valor) && <option value={valor}>…</option>}
        {lista.map((p) => (
          <option key={p.id} value={String(p.id)}>
            {p.nombre}
          </option>
        ))}
      </select>
      {consulta.error && !portafolios && (
        <p className="linea-fuente" role="alert">
          {consulta.error.mensaje ?? 'No se pudo consultar la lista de portafolios.'}
        </p>
      )}
    </div>
  )
}

export default SelectorPortafolio
