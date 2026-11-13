import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
  build: {
    // Keep the production UI inside the Python package so the FastAPI process
    // can serve it without a separate Vite server.
    outDir: '../src/kicad_tools_app/static',
    emptyOutDir: true,
  },
})
