/* ==========================================================
   Configuración del cliente de la API.
   - En local usa los servicios de 127.0.0.1.
   - En GitHub Pages/Vercel usa los servicios públicos de Render.
   Cambia los nombres de Render si tu blueprint usa otros.
   ========================================================== */
(() => {
  "use strict";

  const isLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  const metricsKey = "pk_live_devblog_7f3a9c2e5b1d4a8f9c0e6b2d7a4f1c8e";

  const local = {
    API_BASE_URL: "http://127.0.0.1:8080/api/v1",
    PUBLIC_TOKEN: "public-dev-token",
    METRICS_ENABLED: true,
    METRICS_BASE_URL: "http://127.0.0.1:8000",
    METRICS_KEY: metricsKey,
    METRICS_SITE: "devblog",
    STATIC_GENERATOR_BASE_URL: "http://127.0.0.1:8001",
  };

  const production = {
    API_BASE_URL: "https://devblog-cms-leonardo.onrender.com/api/v1",
    PUBLIC_TOKEN: "pub_live_devblog_2026",
    METRICS_ENABLED: true,
    METRICS_BASE_URL: "https://devblog-metrics-leonardo.onrender.com",
    METRICS_KEY: metricsKey,
    METRICS_SITE: "devblog",
    STATIC_GENERATOR_BASE_URL: "https://devblog-generator-leonardo.onrender.com",
  };

  window.DEVBLOG_CONFIG = isLocal ? local : production;
})();
