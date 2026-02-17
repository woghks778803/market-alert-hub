import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import vuetify from "vite-plugin-vuetify"
import { fileURLToPath, URL } from "node:url"

export default defineConfig({
  plugins: [vue(), vuetify({ autoImport: true }),],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8080", changeOrigin: true },
      "/admin-api": { target: "http://localhost:8080", changeOrigin: true },
    },
    // WS/파일업로드 이슈 주석 유지
    // watch: { usePolling: true }
  },
})
