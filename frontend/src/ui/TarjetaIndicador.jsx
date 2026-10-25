// Tarjeta de indicador (B3; SRS 4.5.1, «Componentes»; RF-11 crit. 1; RNF-07) con Card + Stat del
// sistema «Proyecto 077 UI». Contrato del Anexo A: TarjetaIndicador({titulo, valor, unidad, fecha}).
// - Nombre como h3; cifra (Google Sans Code, en ink), unidad y fecha o periodo juntos y en ese
//   orden (1.3.1).
// - `valor` llega ya formado (formato.js); la tarjeta no lo toca (RNF-02).
// - `data-recorrido` (p. ej. "tarjeta-valor") se pone en el elemento de la cifra, para que el
//   guion de AC-04 lea exactamente la misma cadena que la etiqueta del corte y la tabla.
// - Opcionales: `principal` (la cifra principal de la pantalla, en t-num-display), `delta` (una
//   Delta debajo de la cifra) y `children` (líneas propias del indicador, p. ej. «Del pico del …»).
import './datos.css'

export function TarjetaIndicador({
  titulo,
  valor,
  unidad,
  fecha,
  principal = false,
  delta,
  className,
  children,
  'data-recorrido': recorrido,
  ...resto
}) {
  return (
    <section className={['p77-card', 'tarjeta-indicador', className].filter(Boolean).join(' ')} {...resto}>
      <h3 className="p77-stat__label">{titulo}</h3>
      <p className={principal ? 'p77-stat__value p77-stat__value--display' : 'p77-stat__value'}>
        <span className="cifra" data-recorrido={recorrido}>
          {valor}
        </span>
        {unidad && <span className="p77-stat__unidad">{unidad}</span>}
      </p>
      {delta}
      {fecha && <p className="tarjeta-fecha">{fecha}</p>}
      {children}
    </section>
  )
}

export default TarjetaIndicador
