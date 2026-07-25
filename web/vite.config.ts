import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// LAIR backend runs on 8000 (uvicorn main:app --reload); proxying here
// means the browser only ever talks to the Vite origin, so no CORS
// changes are needed on the FastAPI side.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/v1': 'http://127.0.0.1:8000',
      '/route': 'http://127.0.0.1:8000',
      '/models': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/benchmarks': 'http://127.0.0.1:8000',
    },
  },
})
