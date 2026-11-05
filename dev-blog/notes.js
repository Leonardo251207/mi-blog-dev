/* ==========================================================
   Portada: carga las publicaciones desde la API.
   Si la API no está disponible, conserva las tarjetas estáticas
   que ya vienen en index.html (fallback).
   ========================================================== */
(() => {
  "use strict";

  const grid = document.querySelector("[data-notes-grid]");
  if (!grid || !window.DevBlogAPI) return;

  const fallbackMarkup = grid.innerHTML;
  const { publicApi } = window.DevBlogAPI;

  const dateFormatter = new Intl.DateTimeFormat("es-MX", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

  function formatDate(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "" : dateFormatter.format(date);
  }

  function card(post, index) {
    const link = document.createElement("a");
    link.className = "card note is-visible";
    link.href = `articulo.html?slug=${encodeURIComponent(post.slug)}`;
    link.style.setProperty("--d", `${index * 0.08}s`);
    link.setAttribute("aria-label", `Leer ${post.title}`);

    const art = document.createElement("div");
    art.className = "art art--dots";
    art.setAttribute("aria-hidden", "true");
    art.innerHTML = `
      <svg viewBox="0 0 270 158" preserveAspectRatio="xMidYMid slice">
        <rect x="32" y="30" width="206" height="14" class="dim"/>
        <line class="bar" x1="32" y1="62" x2="238" y2="62"/>
        <line class="dim" x1="32" y1="78" x2="190" y2="78"/>
        <line class="dim" x1="32" y1="92" x2="150" y2="92"/>
        <line class="dim" x1="32" y1="106" x2="210" y2="106"/>
        <line class="dim" x1="32" y1="120" x2="172" y2="120"/>
      </svg>`;

    const body = document.createElement("div");
    body.className = "card__body";

    const meta = document.createElement("div");
    meta.className = "note__meta";

    const tag = document.createElement("span");
    tag.className = "note__tag";
    tag.textContent = (post.tags && post.tags[0] ? post.tags[0] : "NOTA").toUpperCase();

    const time = document.createElement("span");
    time.className = "note__time";
    time.textContent = `${post.reading_time_min} MIN`;

    meta.append(tag, time);

    const title = document.createElement("h3");
    title.textContent = post.title;

    const description = document.createElement("p");
    const published = formatDate(post.published_at);
    description.textContent = published
      ? `Publicado el ${published} · ${post.reading_time_min} min de lectura.`
      : `${post.reading_time_min} min de lectura.`;

    const more = document.createElement("span");
    more.className = "card__link";
    more.innerHTML = 'Leer más <span aria-hidden="true">→</span>';

    body.append(meta, title, description, more);
    link.append(art, body);
    return link;
  }

  function emptyState() {
    const message = document.createElement("p");
    message.className = "notes__fallback";
    message.textContent =
      "Todavía no hay publicaciones. Entra a admin.html para crear la primera.";
    grid.replaceChildren(message);
  }

  function fallback() {
    grid.innerHTML = fallbackMarkup;
    // Los elementos restaurados no pasaron por el IntersectionObserver de script.js.
    grid.querySelectorAll(".reveal").forEach((element) => element.classList.add("is-visible"));
    const notice = document.createElement("p");
    notice.className = "notes__fallback";
    notice.textContent =
      "Mostrando contenido local: la API no está disponible en este momento.";
    grid.after(notice);
  }

  async function load() {
    try {
      const page = await publicApi.listPosts({ limit: 6 });
      if (!page.items.length) {
        emptyState();
        return;
      }
      grid.replaceChildren(...page.items.map(card));
    } catch (error) {
      console.warn("No se pudo cargar el listado desde la API:", error);
      fallback();
    }
  }

  load();
})();
