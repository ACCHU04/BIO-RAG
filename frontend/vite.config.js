import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/query': 'http://localhost:8742',
      '/documents': 'http://localhost:8742',
      '/health': 'http://localhost:8742',
      '/ingest': 'http://localhost:8742',
      '/evaluate': 'http://localhost:8742',
      '/export': 'http://localhost:8742',
      '/incognito': 'http://localhost:8742',
    },
  },
})
