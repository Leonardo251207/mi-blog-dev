/* ==========================================================
   Beacon del colector de métricas (metrics-navigation)
   Carga /v1/beacon.js del servicio en 8000 y le pasa la clave
   pública del sitio "devblog".
   ========================================================== */
(() => {
  "use strict";

  const config = window.DEVBLOG_CONFIG || {};
  if (!config.METRICS_ENABLED || !config.METRICS_KEY) return;

  const base = String(config.METRICS_BASE_URL || "http://127.0.0.1:8000")
    .replace(/\/+$/, "");

  const beacon = document.createElement("script");
  beacon.defer = true;
  beacon.src = `${base}/v1/beacon.js`;
  beacon.setAttribute("data-key", config.METRICS_KEY);
  beacon.setAttribute("data-site", config.METRICS_SITE || "devblog");
  document.head.appendChild(beacon);
})();
