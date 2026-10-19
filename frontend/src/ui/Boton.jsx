// Boton({variante, esperando, textoEspera}) (Anexo A; 4.5.1, «Botones»).
// variante: 'primario' (por omisión), 'secundario', 'negativo' o 'enlace'; también se
// aceptan 'primaria', 'secundaria' y 'negativa'.
// En espera no se desactiva (el foco no se pierde): marca aria-disabled, muestra
// textoEspera («Guardando…» por omisión) y anula el clic, también el envío del formulario.
import '../estilos/controles.css'

const SINONIMOS = { primaria: 'primario', secundaria: 'secundario', negativa: 'negativo' }

export function Boton({
  variante = 'primario',
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
  const clases = ['boton', `boton--${v}`, className].filter(Boolean).join(' ')
  return (
    <button
      type={type}
      className={clases}
      disabled={disabled}
      aria-disabled={esperando ? 'true' : undefined}
      onClick={(e) => {
        if (esperando) {
          e.preventDefault()
          return
        }
        onClick?.(e)
      }}
      {...resto}
    >
      {esperando ? textoEspera : children}
    </button>
  )
}

export default Boton
