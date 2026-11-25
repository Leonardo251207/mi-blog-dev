/* ==========================================================
   Aplica el hero del sitio "devblog" administrado desde el CMS.
   Si la API no responde, conserva el HTML estático de respaldo.
   ========================================================== */
(() => {
  "use strict";

  const API = window.DevBlogAPI;
  if (!API) return;

  const title = document.querySelector("#blog-title");
  const lead = document.querySelector("#blog-lead");
  if (!title && !lead) return;

  API.publicApi
    .getSiteLanding("devblog")
    .then((data) => {
      const hero = data?.content?.hero || {};
      if (title && (hero.first_name || hero.last_name)) {
        title.replaceChildren(
          document.createTextNode(`${hero.first_name || ""} `),
          Object.assign(document.createElement("span"), {
            textContent: hero.last_name || "",
          })
        );
      }
      if (lead && hero.tagline) lead.textContent = hero.tagline;
    })
    .catch((error) => {
      console.warn("No se pudo cargar el hero del blog desde el CMS:", error);
    });
})();
