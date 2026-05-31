import { defineConfig } from "@apps-in-toss/web-framework/config";

export default defineConfig({
  appName: "picky-menu",
  brand: {
    displayName: "Picky 메뉴추천",
    primaryColor: "#3182F6",
    icon: "/picky-sausage.png",
  },
  web: {
    host: "localhost",
    port: 5173,
    commands: {
      dev: "vite dev",
      build: "vite build",
    },
  },
  permissions: [],
  outdir: "dist",
  webViewProps: {
    type: "partner",
  },
});
