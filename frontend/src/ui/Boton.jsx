// Boton({variante, chico, icono, esperando, textoEspera}) (Anexo A) con el Button del sistema
// «Proyecto 077 UI»: píldora de 48 px (36 px con `chico`, para tablas y encabezados de tarjeta).
// variante: 'primario' (por omisión; action), 'secundario', 'acento', 'negativo' o 'enlace';
// también se aceptan 'primaria', 'secundaria' y 'negativa'. El sistema no pinta botones con
// negative (ese color es solo de pérdidas y errores): 'negativo' se ve como el principal y su
// texto dice la acción («Eliminar», «Revocar»).
// `icono`: un ícono de Font Awesome Solid a la izquierda, decorativo.
// En espera no se desactiva (el foco no se pierde): marca aria-disabled y aria-busy, muestra
// textoEspera («Guardando…» por omisión) y anula el clic, también el envío del formulario.
import { Icono } from './Icono.jsx'

const SINONIMOS = { primaria: 'primario', secundaria: 'secundario', negativa: 'negativo' }
const CLASES = {
  primario: 'p77-btn',
  negativo: 'p77-btn',
  secundario: 'p77-btn p77-btn--secondary',
  acento: 'p77-btn p77-btn--accent',
  enlace: 'p77-btn p77-btn--link',
}

export function Boton({
  variante = 'primario',
  chico = false,
  icono,
  esperando = false,
  textoEspera = 'Guardando…',
  type = 'button',
  className,
  onClick,
  disabled,
  children,
  ...resto
}) {
  const v = SINONIMOS[variante] ?? variante
  const clases = [CLASES[v] ?? CLASES.primario, chico && 'p77-btn--sm', className].filter(Boolean).join(' ')
  return (
    <button
      type={type}
      className={clases}
      disabled={disabled}
      aria-disabled={esperando ? 'true' : undefined}
      aria-busy={esperando ? 'true' : undefined}
      onClick={(e) => {
        if (esperando) {
          e.preventDefault()
          return
        }
        onClick?.(e)
      }}
      {...resto}
    >
      {icono && !esperando && <Icono icono={icono} />}
      {esperando ? textoEspera : children}
    </button>
  )
}

export default Boton
