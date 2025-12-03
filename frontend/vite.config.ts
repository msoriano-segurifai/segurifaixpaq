import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Use /static/ base path so Django can serve assets via WhiteNoise
  base: '/static/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
  server: {
    port: 3000,
    proxy: {
      // Proxy /api/* requests to Django backend on port 8000
      // Example: /api/auth/login -> http://localhost:8000/api/auth/login
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
