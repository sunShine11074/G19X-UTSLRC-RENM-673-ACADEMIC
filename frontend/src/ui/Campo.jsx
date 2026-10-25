// Campo, CampoFecha y CampoContrasena (Anexo A; 4.5.1, «Componentes»).
// - La etiqueta es visible y está asociada, arriba del control; la ayuda y el error van debajo
//   (TextField del sistema «Proyecto 077 UI») y se enlazan con aria-describedby; el error lleva
//   texto e ícono (1.4.1; 3.3.1).
// - El <input> recibe data-recorrido = id, salvo que se pase `recorrido`.
// - Lo demás (value, onChange, type, autoComplete…) pasa al <input>.
import { faTriangleExclamation } from '@fortawesome/free-solid-svg-icons'
import { useState } from 'react'
import { aIso, fecha } from '../formato/formato.js'
import '../estilos/controles.css'
import { Icono } from './Icono.jsx'

function idsDescripcion(id, ayuda, error, extra) {
  const ids = [ayuda ? `${id}-ayuda` : null, error ? `${id}-error` : null, extra].filter(Boolean)
  return ids.length ? ids.join(' ') : undefined
}

export function MensajeCampo({ id, error }) {
  if (!error) return null
  return (
    <p id={`${id}-error`} className="campo__error">
      <Icono icono={faTriangleExclamation} />
      <span>{error}</span>
    </p>
  )
}

export function Campo({ id, etiqueta, ayuda, error, recorrido, claseContenedor, className, ...resto }) {
  return (
    <div className={['campo', claseContenedor].filter(Boolean).join(' ')}>
      <label htmlFor={id} className="campo__etiqueta">
        {etiqueta}
      </label>
      <input
        id={id}
        name={id}
        data-recorrido={recorrido ?? id}
        className={['campo__control', className].filter(Boolean).join(' ')}
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={idsDescripcion(id, ayuda, error)}
        {...resto}
      />
      {ayuda && (
        <p id={`${id}-ayuda`} className="campo__ayuda">
          {ayuda}
        </p>
      )}
      <MensajeCampo id={id} error={error} />
    </div>
  )
}

// Fecha en texto DD/MM/AAAA, sin calendario (4.5.1: el DateInput de CDS sin calendario).
// valorIso: 'AAAA-MM-DD' o el texto que el usuario lleva escrito.
// alCambiar(valor): recibe 'AAAA-MM-DD' cuando el texto es una fecha completa
// (DD/MM/AAAA, D/M/AAAA o AAAA-MM-DD) y, mientras no, el texto tal cual, para que la
// API lo rechace con su motivo. No usa Date: solo reordena el texto (RD-15).
const RE_ISO = /^\d{4}-\d{2}-\d{2}$/

function aTexto(valor) {
  if (!valor) return ''
  return RE_ISO.test(valor) ? fecha(valor) : valor
}

function aValor(texto) {
  return aIso(texto) ?? texto
}

export function CampoFecha({ id, etiqueta, valorIso, alCambiar, ayuda, error, recorrido, claseContenedor, ...resto }) {
  return (
    <div className={['campo', 'campo--fecha', claseContenedor].filter(Boolean).join(' ')}>
      <label htmlFor={id} className="campo__etiqueta">
        {etiqueta}
      </label>
      <input
        id={id}
        name={id}
        type="text"
        autoComplete="off"
        spellCheck="false"
        maxLength={10}
        data-recorrido={recorrido ?? id}
        className="campo__control"
        value={aTexto(valorIso)}
        onChange={(e) => alCambiar?.(aValor(e.target.value))}
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={idsDescripcion(id, true, error)}
        {...resto}
      />
      <p id={`${id}-ayuda`} className="campo__ayuda">
        DD/MM/AAAA{ayuda ? <> · {ayuda}</> : null}
      </p>
      <MensajeCampo id={id} error={error} />
    </div>
  )
}

// Contraseña con el botón «Mostrar contraseña» (RF-01; 3.3.8: se puede pegar y autocompletar).
export function CampoContrasena({
  id,
  etiqueta = 'Contraseña',
  ayuda,
  error,
  recorrido,
  claseContenedor,
  autoComplete = 'current-password',
  ...resto
}) {
  const [visible, setVisible] = useState(false)
  return (
    <div className={['campo', 'campo--contrasena', claseContenedor].filter(Boolean).join(' ')}>
      <label htmlFor={id} className="campo__etiqueta">
        {etiqueta}
      </label>
      <div className="campo__con-boton">
        <input
          id={id}
          name={id}
          type={visible ? 'text' : 'password'}
          autoComplete={autoComplete}
          autoCapitalize="none"
          spellCheck="false"
          data-recorrido={recorrido ?? id}
          className="campo__control"
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={idsDescripcion(id, ayuda, error)}
          {...resto}
        />
        <button
          type="button"
          className="p77-btn p77-btn--secondary campo__boton"
          aria-pressed={visible ? 'true' : 'false'}
          aria-controls={id}
          onClick={() => setVisible((v) => !v)}
        >
          Mostrar contraseña
        </button>
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

export default Campo
