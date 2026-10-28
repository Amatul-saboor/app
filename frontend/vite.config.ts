import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In development the Python API runs separately; proxy /api so the app can use relative URLs
// exactly as it does in production, where frontend and API share one origin.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': 'http://localhost:8000' },
  },
})
