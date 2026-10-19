// Diálogos modales sobre <dialog>.showModal() (B3; SRS 4.5.1, «Confirmación expresa»;
// RF-03 crit. 3; RF-12 crit. 3; 2.1.2; 2.4.3; 4.1.2).
// Contrato del Anexo A:
//   DialogoConfirmacion({abierto, titulo, textoConfirmar, negativo, alConfirmar, alCancelar})
//   DialogoFormulario({abierto, titulo, alEnviar, alCancelar})
//   DialogoInformativo({abierto, titulo, alCerrar})
// Sus botones llevan data-recorrido="confirmar" y "cancelar" (en el informativo, «Cerrar»
// lleva "cancelar").
// Comportamiento:
// - El estado lo lleva la pantalla con `abierto`; el diálogo solo lo refleja.
// - Al abrir, el foco entra al diálogo (primer control: el campo, o «Cancelar» si no hay campo)
//   y no sale mientras está abierto (lo garantiza showModal).
// - Esc cancela: se intercepta el evento `cancel` y se llama alCancelar (o alCerrar).
// - Al cerrar, el foco vuelve al elemento que tenía el foco al abrir (el botón que lo abrió);
//   si ya no existe (p. ej. se eliminó su fila), pasa al h1 de la pantalla.
// - El contenido solo se monta mientras está abierto, para que los id de sus campos no se
//   repitan entre diálogos de la misma pantalla.
// Opcionales: `children` (cuerpo), `error` (motivo general dentro del diálogo), `esperando`
// y `textoEspera` (botón de confirmar en espera) y `textoCancelar`.
import { useEffect, useId, useRef } from 'react'
import { Boton } from './Boton.jsx'
import './datos.css'

function enfocarRespaldo() {
  const h1 = document.querySelector('main h1')
  if (!h1) return
  if (!h1.hasAttribute('tabindex')) h1.setAttribute('tabindex', '-1')
  h1.focus()
}

function devolverFoco(elemento) {
  if (elemento && elemento.isConnected && typeof elemento.focus === 'function' && elemento !== document.body) {
    elemento.focus()
  } else {
    enfocarRespaldo()
  }
}

function useDialogoModal(abierto, alCancelar, enfocarTitulo = false) {
  const ref = useRef(null)
  const origen = useRef(null)
  const abiertoRef = useRef(abierto)
  const cancelarRef = useRef(alCancelar)

  useEffect(() => {
    abiertoRef.current = abierto
    cancelarRef.current = alCancelar
  })

  useEffect(() => {
    const d = ref.current
    if (!d) return
    if (abierto && !d.open) {
      origen.current = document.activeElement
      d.showModal()
      // En el informativo, el foco va al título para leer desde el principio.
      if (enfocarTitulo) d.querySelector('h2')?.focus()
    } else if (!abierto && d.open) {
      d.close()
      const anterior = origen.current
      origen.current = null
      devolverFoco(anterior)
    }
  }, [abierto, enfocarTitulo])

  // Si la pantalla desmonta el diálogo abierto, se cierra y devuelve el foco.
  useEffect(() => {
    const d = ref.current
    return () => {
      if (d?.open) {
        d.close()
        devolverFoco(origen.current)
      }
    }
  }, [])

  const alCancelarNativo = (e) => {
    e.preventDefault() // Esc: la pantalla decide cerrar con `abierto`
    cancelarRef.current?.()
  }

  // Si el navegador cerró el diálogo por su cuenta (p. ej. Esc repetido), se trata como cancelar.
  const alCerrarNativo = () => {
    if (abiertoRef.current) {
      const anterior = origen.current
      origen.current = null
      cancelarRef.current?.()
      devolverFoco(anterior)
    }
  }

  return { ref, alCancelarNativo, alCerrarNativo }
}

function ErrorDialogo({ error }) {
  if (!error) return null
  return (
    <p className="dialogo-error" role="alert">
      {error}
    </p>
  )
}

export function DialogoConfirmacion({
  abierto,
  titulo,
  textoConfirmar = 'Confirmar',
  textoCancelar = 'Cancelar',
  negativo = false,
  alConfirmar,
  alCancelar,
  esperando = false,
  textoEspera = 'Guardando…',
  error,
  children,
}) {
  const idTitulo = useId()
  const { ref, alCancelarNativo, alCerrarNativo } = useDialogoModal(abierto, alCancelar)
  return (
    <dialog
      ref={ref}
      className="dialogo"
      aria-labelledby={idTitulo}
      onCancel={alCancelarNativo}
      onClose={alCerrarNativo}
    >
      {abierto && (
        <>
          <h2 id={idTitulo}>{titulo}</h2>
          <div className="dialogo-cuerpo">{children}</div>
          <ErrorDialogo error={error} />
          <div className="dialogo-botones">
            <Boton variante="secundaria" data-recorrido="cancelar" onClick={() => alCancelar?.()}>
              {textoCancelar}
            </Boton>
            <Boton
              variante={negativo ? 'negativa' : 'primaria'}
              data-recorrido="confirmar"
              esperando={esperando}
              textoEspera={textoEspera}
              onClick={() => alConfirmar?.()}
            >
              {textoConfirmar}
            </Boton>
          </div>
        </>
      )}
    </dialog>
  )
}

export function DialogoFormulario({
  abierto,
  titulo,
  alEnviar,
  alCancelar,
  textoConfirmar = 'Guardar',
  textoCancelar = 'Cancelar',
  negativo = false,
  esperando = false,
  textoEspera = 'Guardando…',
  error,
  children,
}) {
  const idTitulo = useId()
  const { ref, alCancelarNativo, alCerrarNativo } = useDialogoModal(abierto, alCancelar)
  return (
    <dialog
      ref={ref}
      className="dialogo"
      aria-labelledby={idTitulo}
      onCancel={alCancelarNativo}
      onClose={alCerrarNativo}
    >
      {abierto && (
        <form
          noValidate
          onSubmit={(e) => {
            e.preventDefault()
            if (!esperando) alEnviar?.(e)
          }}
        >
          <h2 id={idTitulo}>{titulo}</h2>
          <div className="dialogo-cuerpo">{children}</div>
          <ErrorDialogo error={error} />
          <div className="dialogo-botones">
            <Boton variante="secundaria" data-recorrido="cancelar" onClick={() => alCancelar?.()}>
              {textoCancelar}
            </Boton>
            <Boton
              type="submit"
              variante={negativo ? 'negativa' : 'primaria'}
              data-recorrido="confirmar"
              esperando={esperando}
              textoEspera={textoEspera}
            >
              {textoConfirmar}
            </Boton>
          </div>
        </form>
      )}
    </dialog>
  )
}

export function DialogoInformativo({ abierto, titulo, alCerrar, textoCerrar = 'Cerrar', children }) {
  const idTitulo = useId()
  const { ref, alCancelarNativo, alCerrarNativo } = useDialogoModal(abierto, alCerrar, true)
  return (
    <dialog
      ref={ref}
      className="dialogo"
      aria-labelledby={idTitulo}
      onCancel={alCancelarNativo}
      onClose={alCerrarNativo}
    >
      {abierto && (
        <>
          <h2 id={idTitulo} tabIndex={-1}>
            {titulo}
          </h2>
          <div className="dialogo-cuerpo">{children}</div>
          <div className="dialogo-botones">
            <Boton variante="secundaria" data-recorrido="cancelar" onClick={() => alCerrar?.()}>
              {textoCerrar}
            </Boton>
          </div>
        </>
      )}
    </dialog>
  )
}
