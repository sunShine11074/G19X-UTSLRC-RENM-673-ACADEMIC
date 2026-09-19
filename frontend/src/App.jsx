import { useEffect, useState } from 'react'
import './App.css'

const API = 'http://localhost:8000'

function App() {
  const [filas, setFilas] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API}/api/ping`)
      .then((r) => {
        if (!r.ok) throw new Error(`La API respondió ${r.status}`)
        return r.json()
      })
      .then(setFilas)
      .catch((e) => setError(e.message))
  }, [])

  return (
    <main>
      <p className="eyebrow">Proyecto 077 · prueba de extremo a extremo</p>
      <h1>PostgreSQL → FastAPI → navegador</h1>

      {error && (
        <div className="error">
          <strong>No se pudo leer la API.</strong> {error}
          <p>Revisa que el backend esté corriendo en {API}</p>
        </div>
      )}

      {!filas && !error && (
        <p className="cargando">Consultando la base de datos…</p>
      )}

      {filas && (
        <>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Mensaje</th>
                <th className="num">Monto</th>
                <th>Registrado</th>
              </tr>
            </thead>
            <tbody>
              {filas.map((f) => (
                <tr key={f.id}>
                  <td>{f.id}</td>
                  <td>{f.mensaje}</td>
                  <td className="num">{f.monto}</td>
                  <td>{new Date(f.creado_en).toLocaleString('es-MX')}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="nota">
            Los montos llegan como cadena de texto, no como número. Así un{' '}
            <code>numeric(20,4)</code> conserva sus decimales exactos desde la
            base de datos hasta la pantalla, sin pasar por punto flotante.
          </p>
        </>
      )}
    </main>
  )
}

export default App
