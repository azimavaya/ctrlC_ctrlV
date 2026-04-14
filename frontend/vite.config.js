// Bring in helper function to define Vite config for React
import { defineConfig } from "vite";
// Bring in the React plugin for Vite
import react from "@vitejs/plugin-react";

// Define the Vite config
export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 3000,
    proxy: {
      "/api": {
        target: "http://backend:5000",
        changeOrigin: true,
      },
    },
  },
});
