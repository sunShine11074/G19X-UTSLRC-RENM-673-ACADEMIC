// Procedencia de una valuación (B4 → P-E; RF-26b; RF-31 crit. 2 y 3; RF-07 crit. 3; H-6).
// Contrato del Anexo A: Procedencia({valuacion, deDemostracion}).
//
// `valuacion` es la Valuacion de E19 o E20, tal como llega:
// - {tipo: 'precio_cierre', precio, fecha_dato, fuente}
// - {tipo: 'estimacion_cetes', dias_por_vencer, caso, tasa_aplicada, precio_estimado, tasas_usadas, fuente}
// `deDemostracion` marca el precio con la etiqueta «Datos de demostración»; si no se pasa, se
// toma de la fuente. Solo presenta texto de la API con formato.js: no calcula nada (RNF-02).
// El nombre del instrumento lo pone quien la usa.
import { dias, fecha, pesos, tasa, textoCaso } from '../formato/formato.js'
import { MENSAJES } from '../textos/textos.js'
import { LineaFuente } from '../ui/Avisos.jsx'
import { EtiquetaDemo } from '../ui/EtiquetaDemo.jsx'
import './procedencia.css'

function TasaUsada({ t }) {
  const plazo = dias(t.plazo_nominal)
  const efectivo = t.plazo_efectivo && t.plazo_efectivo !== t.plazo_nominal ? ` (plazo efectivo de ${dias(t.plazo_efectivo)})` : ''
  return (
    <li>
      Tasa de {plazo}
      {efectivo} colocada el {fecha(t.fecha_colocacion)}: <span className="cifra">{tasa(t.valor)}</span>
    </li>
  )
}

function ProcedenciaCetes({ v, demo }) {
  const tasas = Array.isArray(v.tasas_usadas) ? v.tasas_usadas : []
  return (
    <div className="procedencia procedencia--cetes">
      <p className="procedencia__dato">
        Precio estimado: <span className="cifra">{pesos(v.precio_estimado)}</span>{' '}
        <span className="procedencia__estimado">{MENSAJES.estimado}</span>
        {demo && (
          <>
            {' '}
            <EtiquetaDemo />
          </>
        )}
      </p>
      <p className="procedencia__dato">
        Tasa aplicada: <span className="cifra">{tasa(v.tasa_aplicada)}</span>, {textoCaso(v.caso)}; vence en{' '}
        <span className="cifra">{dias(v.dias_por_vencer)}</span>
      </p>
      {tasas.length > 0 && (
        <ul className="procedencia__tasas">
          {tasas.map((t) => (
            <TasaUsada key={`${t.plazo_nominal}-${t.fecha_colocacion}`} t={t} />
          ))}
        </ul>
      )}
      <LineaFuente fuente={v.fuente} />
    </div>
  )
}

function ProcedenciaCierre({ v, demo }) {
  return (
    <div className="procedencia procedencia--cierre">
      <p className="procedencia__dato">
        Cierre: <span className="cifra">{pesos(v.precio)}</span> del {fecha(v.fecha_dato)}
        {demo && (
          <>
            {' '}
            <EtiquetaDemo />
          </>
        )}
      </p>
      <LineaFuente fuente={v.fuente} />
    </div>
  )
}

export function Procedencia({ valuacion, deDemostracion }) {
  if (!valuacion) return null
  const demo = deDemostracion ?? valuacion.fuente?.de_demostracion === true
  if (valuacion.tipo === 'estimacion_cetes') return <ProcedenciaCetes v={valuacion} demo={demo} />
  if (valuacion.tipo === 'precio_cierre') return <ProcedenciaCierre v={valuacion} demo={demo} />
  return null
}

export default Procedencia
