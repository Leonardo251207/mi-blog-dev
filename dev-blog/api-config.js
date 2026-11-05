/* ==========================================================
   Configuración del cliente de la API
   Cambia estos valores al desplegar el blog o reutilizar la API
   en otro proyecto.
   ========================================================== */
window.DEVBLOG_CONFIG = {
  // URL base de la API del CMS (sin barra final). En local:
  // CMS en 8080 para coexistir con Métricas (8000) y Generador (8001).
  API_BASE_URL: "http://127.0.0.1:8080/api/v1",

  // Servicios del ecosistema del profesor.
  METRICS_ENABLED: true,
  METRICS_BASE_URL: "http://127.0.0.1:8000",
  METRICS_KEY: "pk_live_devblog_0000000000000000000000000000",
  METRICS_SITE: "devblog",
  STATIC_GENERATOR_BASE_URL: "http://127.0.0.1:8001",

  // Token de solo lectura del Sitio Web Público.
  // Es visible en el navegador: nunca uses aquí el token de la consola.
  PUBLIC_TOKEN: "public-dev-token",
};
