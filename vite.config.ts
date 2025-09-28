import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

// Force rebuild to break cache
// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  build: {
    // This is a dummy object to force a cache bust on Vercel.
  },
  server: {
    host: "::",
    port: 8080,
  },
  plugins: [react()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
