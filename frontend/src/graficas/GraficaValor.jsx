// Gráfica de evolución del valor (RF-11 crit. 2; RNF-02; 4.5.1, «Reglas de la gráfica»).
// Portada del prototipo de Recharts 3.10.1 («Gráficos - prototipos (16 oct)/fuente/recharts.js»)
// y de las secciones 7.2 y 7.3 de la recomendación. Todo lo que se lee (información emergente,
// etiqueta del corte, resumen y tabla) sale de la cadena de la API; la altura `y` es la única
// conversión a número (excepción del Anexo A). Sin animación (isAnimationActive={false}).
import { useId } from 'react'
import { CartesianGrid, Line, LineChart, ReferenceDot, Tooltip, XAxis, YAxis } from 'recharts'
import { fecha, fechaCorta, pesos } from '../formato/formato.js'
import { EtiquetaDemo } from '../ui/EtiquetaDemo.jsx'
import { ResumenGrafica } from './ResumenGrafica.jsx'
import { TablaSerie } from './TablaSerie.jsx'
import { marcaEje, puntosGrafica, textoResumen } from './serie.js'
import './grafica.css'

// Etiqueta del punto del corte: texto SVG con halo del color de fondo, como en el prototipo.
// Su texto completo es «$58,940.88 · 14/10/2026 (corte)», el mismo que arma textoCorte() de
// serie.js; data-recorrido="etiqueta-corte" va en la parte que contiene solo la cifra (RNF-02).
// Va en el margen superior de 44 px, alineada a la derecha con el punto y unida a él con una
// guía, para que nunca tape la línea (4.5.1: fuera del área de trazado).
const ALTO_ETIQUETA = 16
function EtiquetaCorte({ viewBox, valor, fechaIso }) {
  if (!viewBox) return null
  const cx = viewBox.x + (viewBox.width ?? 0) / 2
  const cy = viewBox.y + (viewBox.height ?? 0) / 2
  const halo = { stroke: 'var(--bg)', strokeWidth: 4, paintOrder: 'stroke', strokeLinejoin: 'round' }
  return (
    <g pointerEvents="none">
      {cy - 10 > ALTO_ETIQUETA + 8 && (
        <line
          x1={cx}
          y1={ALTO_ETIQUETA + 6}
          x2={cx}
          y2={cy - 10}
          stroke="var(--fgMuted)"
          strokeWidth={1}
          strokeDasharray="2 3"
        />
      )}
      <text
        x={cx + 6}
        y={ALTO_ETIQUETA}
        textAnchor="end"
        fontSize={13}
        fill="var(--fg)"
        {...halo}
      >
        <tspan fontWeight={600} data-recorrido="etiqueta-corte">
          {pesos(valor)}
        </tspan>
        <tspan fill="var(--fgMuted)">{` · ${fecha(fechaIso)} (corte)`}</tspan>
      </text>
    </g>
  )
}

// Contrato del Anexo A, más `deDemostracion` (opcional): pone la etiqueta «Datos de
// demostración» junto al título de la gráfica (H-6, una por bloque).
export function GraficaValor({ serie, fechaCorte, valorAlCorte, nombrePortafolio, periodo, deDemostracion }) {
  const idTitulo = useId()
  if (!serie || serie.length === 0) {
    return <p className="grafica-vacia">No hay datos de la serie para el periodo.</p>
  }
  const datos = puntosGrafica(serie)
  const corte = datos.find((p) => p.fecha === fechaCorte)
  const distinto = corte && valorAlCorte != null && corte.texto !== valorAlCorte
  const resumen = textoResumen({ nombrePortafolio, serie, periodo, fechaCorte })

  return (
    <section className="grafica-valor" aria-labelledby={idTitulo}>
      <div className="grafica-encabezado">
        <h2 id={idTitulo} className="grafica-titulo">
          Valor de mercado del portafolio
        </h2>
        {deDemostracion && <EtiquetaDemo />}
      </div>
      <p className="grafica-meta">
        Pesos mexicanos (MXN)
        {periodo ? ` · Del ${fecha(periodo.inicio)} al ${fecha(periodo.fin)}` : ''}
        {` · Fecha de corte ${fecha(fechaCorte)}`}
      </p>
      {!corte && (
        <p className="grafica-alerta" role="alert">
          La serie no incluye la fecha de corte.
        </p>
      )}
      {distinto && (
        <p className="grafica-alerta" role="alert">
          El valor al corte no coincide con el último punto de la serie.
        </p>
      )}
      <ResumenGrafica nombrePortafolio={nombrePortafolio} serie={serie} periodo={periodo} fechaCorte={fechaCorte} />
      <div className="grafica-marco">
        <div className="grafica">
          <LineChart
            responsive
            data={datos}
            style={{ width: '100%', height: '100%' }}
            margin={{ top: 44, right: 16, bottom: 4, left: 0 }}
            title={`Valor de mercado del portafolio «${nombrePortafolio}» (MXN)`}
            desc={resumen}
          >
            <CartesianGrid vertical={false} stroke="var(--bgLine)" />
            <XAxis
              dataKey="fecha"
              type="category"
              interval="preserveStartEnd"
              minTickGap={18}
              tickFormatter={(v) => (typeof v === 'string' ? fechaCorta(v) : String(v))}
              tick={{ fill: 'var(--fgMuted)', fontSize: 12 }}
              stroke="var(--bgLineHeavy)"
              tickLine={false}
            />
            <YAxis
              width="auto"
              domain={['auto', 'auto']}
              tickFormatter={marcaEje}
              tick={{ fill: 'var(--fgMuted)', fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              isAnimationActive={false}
              labelFormatter={(etiqueta, carga) => {
                const f = carga?.[0]?.payload?.fecha ?? String(etiqueta)
                return fecha(f) + (f === fechaCorte ? ' (corte)' : '')
              }}
              formatter={(_valor, _nombre, item) => [`${pesos(item.payload.texto)} MXN`, 'Valor']}
              separator=": "
              contentStyle={{
                backgroundColor: 'var(--bgElevation2)',
                borderColor: 'var(--bgLineHeavy)',
                color: 'var(--fg)',
                fontSize: 13,
              }}
              labelStyle={{ color: 'var(--fg)', fontWeight: 600 }}
              itemStyle={{ color: 'var(--fg)' }}
              cursor={{ stroke: 'var(--bgLineHeavy)' }}
            />
            <Line
              type="linear"
              dataKey="y"
              name="Valor de mercado"
              stroke="var(--serie-1)"
              strokeWidth={2}
              dot={{ r: 2.5, fill: 'var(--serie-1)', stroke: 'none' }}
              activeDot={{ r: 6, fill: 'var(--serie-1)', stroke: 'var(--bg)', strokeWidth: 2 }}
              isAnimationActive={false}
            />
            {corte && (
              <ReferenceDot
                x={corte.fecha}
                y={corte.y}
                r={6}
                fill="var(--serie-1)"
                stroke="var(--bg)"
                strokeWidth={2}
                label={<EtiquetaCorte valor={corte.texto} fechaIso={corte.fecha} />}
              />
            )}
          </LineChart>
        </div>
      </div>
      <TablaSerie serie={serie} fechaCorte={fechaCorte} nombrePortafolio={nombrePortafolio} />
    </section>
  )
}

export default GraficaValor
