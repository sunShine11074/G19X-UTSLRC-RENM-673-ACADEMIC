// Tabla alterna de la gráfica (4.5.1; criterios 1.1.1 y 2.1.1): la serie completa con las
// cadenas de la API. La celda del valor de la última fila lleva data-recorrido="ultima-fila"
// (Anexo A; RNF-02): contiene solo la cifra, para compararla como texto con la tarjeta y la
// etiqueta del corte.
// La tabla va en una región con desplazamiento propio, alcanzable con el teclado (1.4.10), y las
// fechas sueltas en Google Sans Code, como las cifras.
import { fecha, pesos } from '../formato/formato.js'
import { textoDias } from './serie.js'

export function TablaSerie({ serie, fechaCorte, nombrePortafolio }) {
  if (!serie || serie.length === 0) return null
  const ultimo = serie.length - 1
  return (
    <details className="grafica-tabla">
      <summary>Ver los datos de la gráfica como tabla ({textoDias(serie.length)})</summary>
      <div className="grafica-tabla__region" role="region" aria-label="Datos de la gráfica" tabIndex={0}>
        <table>
          <caption>
            Valor de mercado diario del portafolio «{nombrePortafolio}» (MXN)
          </caption>
          <thead>
            <tr>
              <th scope="col">Fecha</th>
              <th scope="col" className="cifra">
                Valor (MXN)
              </th>
            </tr>
          </thead>
          <tbody>
            {serie.map((p, i) => {
              const esCorte = p.fecha === fechaCorte
              return (
                <tr key={p.fecha} className={esCorte ? 'grafica-fila-corte' : undefined}>
                  <th scope="row">
                    <span className="fecha-suelta">{fecha(p.fecha)}</span>
                    {esCorte ? ' (corte)' : ''}
                  </th>
                  <td className="cifra" data-recorrido={i === ultimo ? 'ultima-fila' : undefined}>
                    {pesos(p.valor)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </details>
  )
}

export default TablaSerie
