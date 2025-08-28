import { defineConfig } from 'vite'

export default defineConfig({
  root: 'templates',
  publicDir: '../static',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: 'index.html'
      }
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  css: {
    postcss: {
      plugins: []
    }
  }
})