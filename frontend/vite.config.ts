import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      // Voice library endpoints are already prefixed with /api/v1 on the backend.
      // Do NOT rewrite this prefix.
      '/api/v1': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/outputs': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
