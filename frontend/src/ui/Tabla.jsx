// Tabla de datos (B3; SRS 4.5.1, «Componentes»: table, caption y th con scope).
// Contrato del Anexo A: Tabla({titulo, columnas:[{clave, encabezado, cifra}], filas, pie}).
// - La primera columna es el encabezado de cada fila (th scope="row").
// - Las columnas con `cifra` se alinean a la derecha con números de ancho fijo.
// - Las celdas reciben el texto ya formado (formato.js) o un nodo de React; la tabla no
//   convierte ni suma nada (RNF-02).
// - `pie`: una fila (objeto con las mismas claves) o una lista de filas, en <tfoot>.
// - Opcionales: `vacio` (texto sin filas) e `idFila(fila, i)` para la clave de React.
// La tabla va en una región con desplazamiento propio, alcanzable con el teclado (1.4.10).
import { isValidElement, useId } from 'react'
import './datos.css'

function claveDe(fila, i, idFila) {
  if (idFila) return idFila(fila, i)
  return fila?.id ?? i
}

function Fila({ fila, columnas, celdaPie }) {
  return (
    <tr>
      {columnas.map((c, j) => {
        const clase = c.cifra ? 'cifra' : undefined
        const valor = fila[c.clave]
        if (j === 0) {
          return (
            <th key={c.clave} scope="row" className={clase}>
              {valor}
            </th>
          )
        }
        return (
          <td key={c.clave} className={clase} data-columna={celdaPie ? undefined : c.clave}>
            {valor}
          </td>
        )
      })}
    </tr>
  )
}

export function Tabla({ titulo, columnas = [], filas = [], pie, vacio = 'No hay datos que mostrar.', idFila }) {
  const idTitulo = useId()
  const filasPie = pie == null || isValidElement(pie) ? null : Array.isArray(pie) ? pie : [pie]

  return (
    <div
      className="tabla-region"
      role="region"
      aria-labelledby={titulo ? idTitulo : undefined}
      aria-label={titulo ? undefined : 'Tabla'}
      tabIndex={0}
    >
      <table className="tabla">
        {titulo && <caption id={idTitulo}>{titulo}</caption>}
        <thead>
          <tr>
            {columnas.map((c) => (
              <th key={c.clave} scope="col" className={c.cifra ? 'cifra' : undefined}>
                {c.encabezado}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filas.length === 0 ? (
            <tr>
              <td className="tabla-vacia" colSpan={columnas.length || 1}>
                {vacio}
              </td>
            </tr>
          ) : (
            filas.map((f, i) => <Fila key={claveDe(f, i, idFila)} fila={f} columnas={columnas} />)
          )}
        </tbody>
        {filasPie && filasPie.length > 0 && (
          <tfoot>
            {filasPie.map((f, i) => (
              <Fila key={claveDe(f, i, idFila)} fila={f} columnas={columnas} celdaPie />
            ))}
          </tfoot>
        )}
        {isValidElement(pie) && <tfoot>{pie}</tfoot>}
      </table>
    </div>
  )
}

export default Tabla
