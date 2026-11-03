import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(import.meta.dirname, './src') },
  },
  // Solo en Docker (docker-compose.yml): los archivos montados desde Windows no emiten eventos.
  server: { watch: process.env.VITE_USE_POLLING === '1' ? { usePolling: true } : undefined },
})
