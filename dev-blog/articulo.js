/* ==========================================================
   Página de artículo dinámica: lee ?slug=... desde la API,
   renderiza Markdown y registra una vista.
   ========================================================== */
(() => {
  "use strict";

  const API = window.DevBlogAPI;
  const Markdown = window.DevBlogMarkdown;
  const params = new URLSearchParams(window.location.search);
  const slug = (params.get("slug") || "").trim();

  const statusEl = document.querySelector("#article-status");
  const titleEl = document.querySelector("#article-title");
  const bylineEl = document.querySelector("#article-byline");
  const stateEl = document.querySelector("#article-state");
  const bodyEl = document.querySelector("#article-body");
  const tagsEl = document.querySelector("#article-tags");
  const actionsEl = document.querySelector("#article-actions");
  const legacyLink = document.querySelector("#legacy-link");

  const LEGACY_PAGES = {
    "despliega-tu-web-gratis-en-vercel": "articulo-vercel.html",
    "prompts-de-ia-para-dominar-cpp": "articulo-cpp.html",
    "reconocimiento-de-voz-en-apps-moviles": "articulo-voz.html",
  };

  const dateFormatter = new Intl.DateTimeFormat("es-MX", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });

  let viewRegistered = false;

  function setStatus(label) {
    const dot = document.createElement("i");
    statusEl.replaceChildren(dot, document.createTextNode(`[ ${label} ]`));
  }

  function setTitle(title) {
    const words = String(title).split(/\s+/);
    const last = words.pop() || "";
    const prefix = words.length ? `${words.join(" ")} ` : "";
    const accent = document.createElement("span");
    accent.textContent = last;
    titleEl.replaceChildren(document.createTextNode(prefix), accent);
  }

  function showState(message, { error = false, retry = false } = {}) {
    stateEl.hidden = false;
    stateEl.classList.toggle("article-state--error", error);
    stateEl.replaceChildren(document.createTextNode(message));
    if (retry) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "btn btn--ghost";
      button.textContent = "Reintentar";
      button.addEventListener("click", () => load());
      stateEl.append(document.createElement("br"), button);
    }
  }

  function formatDate(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "" : dateFormatter.format(date);
  }

  function renderTags(tags) {
    tagsEl.replaceChildren();
    if (!tags || !tags.length) {
      tagsEl.hidden = true;
      return;
    }
    for (const tag of tags) {
      const item = document.createElement("span");
      item.className = "article-tag";
      item.textContent = `#${tag}`;
      tagsEl.append(item);
    }
    tagsEl.hidden = false;
  }

  async function load() {
    if (!API || !Markdown) {
      showState("No se pudo cargar el cliente de la API.", { error: true });
      return;
    }
    if (!slug) {
      setStatus("SIN ARTÍCULO");
      setTitle("Artículo no especificado");
      showState("Falta el parámetro ?slug= en la URL.", { error: true });
      return;
    }

    setStatus("CARGANDO");
    setTitle("Cargando artículo…");
    bylineEl.textContent = "";
    stateEl.hidden = false;
    stateEl.classList.remove("article-state--error");
    stateEl.textContent = "Cargando artículo…";
    bodyEl.hidden = true;
    tagsEl.hidden = true;
    actionsEl.hidden = true;

    try {
      const post = await API.publicApi.getPostBySlug(slug);
      document.title = `${post.title} — DevBlog_`;

      const description = document.querySelector('meta[name="description"]');
      if (description) {
        description.setAttribute(
          "content",
          post.content.replace(/[#*`>_\-\[\]]/g, " ").replace(/\s+/g, " ").trim().slice(0, 155)
        );
      }

      const label = post.tags && post.tags.length
        ? post.tags.join(" / ").toUpperCase()
        : "NOTA";
      setStatus(label);
      setTitle(post.title);

      const published = formatDate(post.published_at);
      bylineEl.textContent = [
        "Por Leonardo Nucamendi",
        `${post.reading_time_min} min de lectura`,
        published,
      ].filter(Boolean).join(" • ");

      bodyEl.innerHTML = Markdown.render(post.content);
      bodyEl.hidden = false;
      renderTags(post.tags);

      const legacy = LEGACY_PAGES[post.slug];
      if (legacy) {
        legacyLink.href = legacy;
        legacyLink.hidden = false;
      } else {
        legacyLink.hidden = true;
        legacyLink.removeAttribute("href");
      }
      actionsEl.hidden = false;
      stateEl.hidden = true;

      if (!viewRegistered) {
        viewRegistered = true;
        API.publicApi.registerView(post.post_id).catch((error) => {
          console.warn("No se pudo registrar la vista:", error);
        });
      }
    } catch (error) {
      if (error && error.status === 404) {
        // Un 404 es un resultado esperado (artículo borrado o inexistente).
        setStatus("NO ENCONTRADO");
        setTitle("Artículo no encontrado");
        bylineEl.textContent = "";
        showState("Este artículo no existe o fue eliminado.", { error: true });
      } else {
        console.error(error);
        setStatus("ERROR DE CONEXIÓN");
        setTitle("No se pudo cargar el artículo");
        bylineEl.textContent = "";
        showState(
          "No se pudo conectar con la API. Comprueba que uvicorn esté en marcha y vuelve a intentarlo.",
          { error: true, retry: true }
        );
      }
    }
  }

  load();
})();
