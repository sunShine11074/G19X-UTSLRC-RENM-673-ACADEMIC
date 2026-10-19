import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Dos modos (plan del 18 oct, H-3 y P-68):
// - por omisión: el entorno real, http://localhost:5173 → API 127.0.0.1:8000;
// - «temporal»: el entorno de desarrollo, http://127.0.0.1:5174 → API 127.0.0.1:8001.
// El proxy no usa changeOrigin, así que el Origin del navegador llega intacto
// a la comprobación de origen de la API. strictPort hace que un puerto ocupado
// falle en vez de cambiar de puerto.
// https://vite.dev/config/
export default defineConfig(({ mode }) =>
  mode === 'temporal'
    ? {
        plugins: [react()],
        cacheDir: 'node_modules/.vite-temporal',
        server: {
          host: '127.0.0.1',
          port: 5174,
          strictPort: true,
          hmr: { overlay: false },
          proxy: { '/api': 'http://127.0.0.1:8001' },
        },
      }
    : {
        plugins: [react()],
        server: {
          port: 5173,
          strictPort: true,
          proxy: { '/api': 'http://127.0.0.1:8000' },
        },
      },
)
