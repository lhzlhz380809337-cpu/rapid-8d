import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { tmpdir } from "node:os";
import { join } from "node:path";


export default defineConfig({
  plugins: [vue()],
  // Keep generated Vite caches outside the source tree. This also works when
  // node_modules is a Windows junction to the external runtime directory.
  cacheDir: process.env.R8D_VITE_CACHE_DIR || join(tmpdir(), "Rapid8D-vite-cache"),
  server: {
    host: "127.0.0.1",
    port: 18080,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:18723",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
