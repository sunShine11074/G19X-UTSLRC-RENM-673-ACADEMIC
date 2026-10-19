// Resumen textual visible de la gráfica (4.5.1; criterio 1.1.1). No calcula nada.
import { textoResumen } from './serie.js'

export function ResumenGrafica({ id, nombrePortafolio, serie, periodo, fechaCorte }) {
  const texto = textoResumen({ nombrePortafolio, serie, periodo, fechaCorte })
  if (!texto) return null
  return (
    <p id={id} className="grafica-resumen">
      {texto}
    </p>
  )
}

export default ResumenGrafica
