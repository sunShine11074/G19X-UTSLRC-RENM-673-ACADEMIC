// Tarjeta de indicador (B3; SRS 4.5.1, «Componentes»; RF-11 crit. 1; RNF-07).
// Contrato del Anexo A: TarjetaIndicador({titulo, valor, unidad, fecha}).
// - Nombre como h3; cifra, unidad y fecha o periodo juntos y en ese orden (1.3.1).
// - `valor` llega ya formado (formato.js); la tarjeta no lo toca (RNF-02).
// - `data-recorrido` (p. ej. "tarjeta-valor") se pone en el elemento de la cifra, para que el
//   guion de AC-04 lea exactamente la misma cadena que la etiqueta del corte y la tabla.
// - `children` agrega líneas propias del indicador (p. ej. «Del pico del … al valle del …»).
import './datos.css'

export function TarjetaIndicador({ titulo, valor, unidad, fecha, children, 'data-recorrido': recorrido, ...resto }) {
  return (
    <section className="tarjeta-indicador" {...resto}>
      <h3>{titulo}</h3>
      <p className="tarjeta-cifra">
        <span className="cifra" data-recorrido={recorrido}>
          {valor}
        </span>
        {unidad && <span className="tarjeta-unidad">{unidad}</span>}
      </p>
      {fecha && <p className="tarjeta-fecha">{fecha}</p>}
      {children}
    </section>
  )
}

export default TarjetaIndicador
