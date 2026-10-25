import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

/**
 * The dev server proxies the API rather than hard-coding its address, so the
 * app never knows whether it is talking to a container or a laptop.
 */
/** The app always calls `/api` on its own origin; this is where that goes. */
const API_PROXY = {
  "/api": {
    target: process.env.MURFULU_API_URL ?? "http://localhost:8010",
    changeOrigin: true,
    rewrite: (path: string) => path.replace(/^\/api/, ""),
  },
};

export default defineConfig({
  plugins: [react()],
  server: { host: true, port: 5173, proxy: API_PROXY },
  // `vite preview` serves the built app, and the layout tests run against it,
  // so it needs the same proxy or every request would 404.
  preview: { proxy: API_PROXY },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    css: true,
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
