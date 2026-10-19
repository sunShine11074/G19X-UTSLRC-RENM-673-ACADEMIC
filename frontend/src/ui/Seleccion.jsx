// Select, Radio y Casilla (Anexo A; 4.5.1, «Componentes»).
// El control recibe data-recorrido = id, salvo que se pase `recorrido`.
import { MensajeCampo } from './Campo.jsx'
import '../estilos/controles.css'

function idsDescripcion(id, ayuda, error) {
  const ids = [ayuda ? `${id}-ayuda` : null, error ? `${id}-error` : null].filter(Boolean)
  return ids.length ? ids.join(' ') : undefined
}

// Select({id, etiqueta, ayuda, error, opciones, marcador, children, ...}):
// opciones = [{valor, texto, deshabilitada}] o, si se prefiere, <option> como children.
// marcador agrega una primera opción vacía (value="") con ese texto.
export function Select({
  id,
  etiqueta,
  ayuda,
  error,
  opciones,
  marcador,
  recorrido,
  claseContenedor,
  children,
  ...resto
}) {
  return (
    <div className={['campo', claseContenedor].filter(Boolean).join(' ')}>
      <label htmlFor={id} className="campo__etiqueta">
        {etiqueta}
      </label>
      {ayuda && (
        <p id={`${id}-ayuda`} className="campo__ayuda">
          {ayuda}
        </p>
      )}
      <select
        id={id}
        name={id}
        data-recorrido={recorrido ?? id}
        className="campo__control campo__control--select"
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={idsDescripcion(id, ayuda, error)}
        {...resto}
      >
        {marcador !== undefined && <option value="">{marcador}</option>}
        {opciones
          ? opciones.map((o) => (
              <option key={String(o.valor)} value={o.valor} disabled={o.deshabilitada}>
                {o.texto}
              </option>
            ))
          : children}
      </select>
      <MensajeCampo id={id} error={error} />
    </div>
  )
}

// Radio:
// - Grupo: Radio({id, etiqueta, opciones:[{valor, texto}], valor, alCambiar, error, ayuda, nombre})
//   dibuja un fieldset con su leyenda (role radiogroup implícito); el fieldset lleva
//   data-recorrido = id y cada opción data-recorrido = `${id}-${valor}`.
// - Suelto: Radio({id, nombre, etiqueta, checked, onChange, ...}) dibuja un solo radio.
export function Radio({
  id,
  nombre,
  etiqueta,
  opciones,
  valor,
  alCambiar,
  error,
  ayuda,
  recorrido,
  claseContenedor,
  ...resto
}) {
  const marca = recorrido ?? id
  if (opciones) {
    return (
      <fieldset
        id={id}
        data-recorrido={marca}
        className={['campo', 'grupo-opciones', claseContenedor].filter(Boolean).join(' ')}
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={idsDescripcion(id, ayuda, error)}
      >
        <legend className="campo__etiqueta">{etiqueta}</legend>
        {ayuda && (
          <p id={`${id}-ayuda`} className="campo__ayuda">
            {ayuda}
          </p>
        )}
        <div className="grupo-opciones__lista">
          {opciones.map((o) => {
            const idOpcion = `${id}-${o.valor}`
            return (
              <div className="opcion" key={String(o.valor)}>
                <input
                  type="radio"
                  id={idOpcion}
                  name={nombre ?? id}
                  value={o.valor}
                  data-recorrido={`${marca}-${o.valor}`}
                  checked={valor === o.valor}
                  onChange={() => alCambiar?.(o.valor)}
                  {...resto}
                />
                <label htmlFor={idOpcion}>{o.texto}</label>
              </div>
            )
          })}
        </div>
        <MensajeCampo id={id} error={error} />
      </fieldset>
    )
  }
  return (
    <div className={['opcion', claseContenedor].filter(Boolean).join(' ')}>
      <input type="radio" id={id} name={nombre} data-recorrido={marca} {...resto} />
      <label htmlFor={id}>{etiqueta}</label>
    </div>
  )
}

// Casilla({id, etiqueta, marcada, alCambiar, error}): sin marcar si `marcada` es falso
// (RF-12 crit. 1). La etiqueta amplía el objetivo de clic (2.5.8).
export function Casilla({ id, etiqueta, marcada, alCambiar, error, ayuda, recorrido, claseContenedor, ...resto }) {
  return (
    <div className={['casilla', claseContenedor].filter(Boolean).join(' ')}>
      <div className="casilla__fila">
        <input
          type="checkbox"
          id={id}
          name={id}
          data-recorrido={recorrido ?? id}
          checked={!!marcada}
          onChange={(e) => alCambiar?.(e.target.checked)}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={idsDescripcion(id, ayuda, error)}
          {...resto}
        />
        <label htmlFor={id}>{etiqueta}</label>
      </div>
      {ayuda && (
        <p id={`${id}-ayuda`} className="campo__ayuda">
          {ayuda}
        </p>
      )}
      <MensajeCampo id={id} error={error} />
    </div>
  )
}

export default Select
