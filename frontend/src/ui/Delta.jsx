// Delta del sistema «Proyecto 077 UI»: una ganancia o una pérdida con color (positive o negative,
// fijos: no cambian con el acento), flecha y signo o palabra, para que nunca dependa solo del color
// (H-7 reabierto el 24 oct: el resultado no realizado y las variaciones llevan color).
// - La dirección y el signo salen de direccion.js, que solo lee el texto de la API (RNF-02).
// - Delta({cifra, plano, palabras, children}): `cifra` es el texto de la API que decide la
//   dirección; muestra `children` (la cifra ya formada) o, con `palabras`, la palabra de la
//   dirección ({sube, baja, igual}). `plano` quita el fondo (celdas de tabla).
import { faCaretDown, faCaretUp, faMinus } from '@fortawesome/free-solid-svg-icons'
import { conSigno, direccion } from './direccion.js'
import { Icono } from './Icono.jsx'

const VARIANTES = { sube: 'up', baja: 'down', igual: 'flat' }
const ICONOS = { sube: faCaretUp, baja: faCaretDown, igual: faMinus }

export function Delta({ cifra, plano = false, palabras, children }) {
  const d = direccion(cifra)
  const clases = ['p77-delta', `p77-delta--${VARIANTES[d]}`, plano && 'p77-delta--plain', palabras && 'p77-delta--palabra']
    .filter(Boolean)
    .join(' ')
  return (
    <span className={clases}>
      <Icono icono={ICONOS[d]} />
      {palabras ? palabras[d] : conSigno(children, cifra)}
    </span>
  )
}

export default Delta
