import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    const hasApiBase = Boolean(env.VITE_API_BASE_URL);
    const voiceLibTarget = (env.VITE_VOICE_LIBRARY_BASE_URL || '').replace(/\/$/, '');
    const voiceChangerTarget = (env.VITE_VOICE_CHANGER_BASE_URL || '').replace(/\/$/, '');
    return {
      server: {
        port: 3000,
        host: '0.0.0.0',
        proxy:
          (!hasApiBase || Boolean(voiceLibTarget))
            ? {
                // Voice library can be proxied to main site to avoid browser CORS.
                // Example: VITE_VOICE_LIBRARY_BASE_URL=https://noiz.ai
                '/api/v1/voice-library': {
                  target: voiceLibTarget || 'http://127.0.0.1:8000',
                  changeOrigin: true,
                  secure: true,
                },

                ...(voiceChangerTarget
                  ? {
                      // Voice changer can be proxied to main site to avoid browser CORS.
                      // Example: VITE_VOICE_CHANGER_BASE_URL=https://<main-site-api-host>
                      '/voice-changer': {
                        target: voiceChangerTarget,
                        changeOrigin: true,
                        secure: true,
                      },
                      '/outputs': {
                        target: voiceChangerTarget,
                        changeOrigin: true,
                        secure: true,
                      },
                    }
                  : {}),

                // Local backend proxies (dev default)
                ...(hasApiBase
                  ? {}
                  : {
                      '/voice-changer': {
                        target: 'http://127.0.0.1:8000',
                        changeOrigin: true,
                      },
                      '/outputs': {
                        target: 'http://127.0.0.1:8000',
                        changeOrigin: true,
                      },
                      '/api': {
                        target: 'http://127.0.0.1:8000',
                        changeOrigin: true,
                      },
                      '/healthz': {
                        target: 'http://127.0.0.1:8000',
                        changeOrigin: true,
                      },
                    }),
              }
            : undefined,
      },
      plugins: [react()],
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      }
    };
});
