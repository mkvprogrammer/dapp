import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  // Docker Compose: API на 8001; локальный uvicorn — 8000 (VITE_DEV_API_TARGET=http://127.0.0.1:8000)
  const apiTarget = env.VITE_DEV_API_TARGET || 'http://127.0.0.1:8001';

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/api': { target: apiTarget, changeOrigin: true },
        '/health': { target: apiTarget, changeOrigin: true },
        '/uploads': { target: apiTarget, changeOrigin: true },
        '/docs': { target: apiTarget, changeOrigin: true },
      },
    },
  };
});
