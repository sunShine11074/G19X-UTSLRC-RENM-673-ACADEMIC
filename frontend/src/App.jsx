import { useEffect, useState } from 'react'
import './App.css'

const API = 'http://localhost:8000'

function App() {
  const [estado, setEstado] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API}/health`)
      .then((r) => {
        if (!r.ok) throw new Error(`La API respondió ${r.status}`)
        return r.json()
      })
      .then((d) => setEstado(d.estado))
      .catch((e) => setError(e.message))
  }, [])

  return (
    <main>
      <p className="eyebrow">Proyecto 077 · prueba de conexión</p>
      <h1>FastAPI → navegador</h1>

      {error && (
        <div className="error">
          <strong>No se pudo leer la API.</strong> {error}
          <p>Revisa que el backend esté corriendo en {API}</p>
        </div>
      )}

      {!estado && !error && <p className="cargando">Consultando la API…</p>}

      {estado && (
        <p className="nota">
          La API responde (<code>{estado}</code>). La prueba de la tabla{' '}
          <code>ping</code> terminó: el esquema real se crea con{' '}
          <code>backend/02_crear_esquema.sql</code>.
        </p>
      )}
    </main>
  )
}

export default App
