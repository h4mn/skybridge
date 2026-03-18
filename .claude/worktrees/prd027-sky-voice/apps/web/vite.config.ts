import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // Resolve aliases (@/* → src/*)
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  // Base URL com /web/ explícito (modo absolute)
  base: '/web/',

  server: {
    port: 5173,
    strictPort: true,
    host: true,
    // Proxy para API backend (evita CORS durante desenvolvimento)
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true, // Habilita WebSocket/SSE
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/discover': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/webhooks': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/observability': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          // Separa bibliotecas pesadas
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'bootstrap-vendor': ['react-bootstrap', 'bootstrap'],
          'query-vendor': ['@tanstack/react-query', 'axios'],
        },
      },
    },
  },

  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'react-bootstrap', 'axios'],
  },
})
