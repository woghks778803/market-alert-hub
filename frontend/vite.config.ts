import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')

  return {
    plugins: [vue(), vuetify({ autoImport: true })],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    // 운영에서 동작 x
    server: {
      port: 5173,
      host: true,
      // WS/파일업로드 이슈 주석 유지
      // watch: { usePolling: true }
      // Origin 헤더를 프록시 대상 서버 기준으로 바꿔주는 옵션
      proxy: {
        '/api': { target: env.VITE_DEV_HTTP_PROXY, changeOrigin: true },
        '/admin-api': { target: env.VITE_DEV_HTTP_PROXY, changeOrigin: true },
        '/ws': { target: env.VITE_DEV_WS_PROXY, changeOrigin: true, ws: true },
      },
      allowedHosts: env.VITE_DEV_ALLOWED_HOST
        ? [env.VITE_DEV_ALLOWED_HOST]
        : [],
    },
  }
})
