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

  function safeUrl(value) {
    const raw = String(value || "").trim();
    if (!raw || /^(javascript|vbscript|data):/i.test(raw)) return "";
    return raw;
  }

  function videoEmbed(url) {
    const youtube = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{6,})/i);
    if (youtube) {
      const iframe = document.createElement("iframe");
      iframe.src = `https://www.youtube.com/embed/${youtube[1]}`;
      iframe.title = "Video de YouTube";
      iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
      iframe.allowFullscreen = true;
      iframe.loading = "lazy";
      return iframe;
    }
    const vimeo = url.match(/vimeo\.com\/(?:video\/)?(\d+)/i);
    if (vimeo) {
      const iframe = document.createElement("iframe");
      iframe.src = `https://player.vimeo.com/video/${vimeo[1]}`;
      iframe.title = "Video de Vimeo";
      iframe.allow = "autoplay; fullscreen; picture-in-picture";
      iframe.allowFullscreen = true;
      iframe.loading = "lazy";
      return iframe;
    }
    const video = document.createElement("video");
    video.controls = true;
    video.preload = "metadata";
    video.playsInline = true;
    video.src = url;
    return video;
  }

  function renderVideos(videos, content) {
    const section = document.querySelector("#videos");
    const grid = document.querySelector("[data-blog-video-grid]");
    if (!section || !grid) return;
    const items = Array.isArray(videos) ? videos : [];
    if (!items.length) {
      section.hidden = true;
      return;
    }

    const label = document.querySelector("[data-blog-videos-label]");
    const title = document.querySelector("[data-blog-videos-title]");
    const sectionInfo = content?.sections?.videos || {};
    if (label) label.textContent = sectionInfo.label || "Multimedia";
    if (title) title.textContent = sectionInfo.title || "Videos";

    grid.replaceChildren();
    items.forEach((item) => {
      const url = safeUrl(item.url);
      if (!url) return;
      const card = document.createElement("article");
      card.className = "site-video";
      const media = document.createElement("div");
      const aspect = item.aspect === "9:16" ? "is-9-16" : item.aspect === "1:1" ? "is-1-1" : "is-16-9";
      media.className = `site-video__media ${aspect}`;
      const embed = videoEmbed(url);
      if (embed.tagName === "VIDEO") {
        const poster = safeUrl(item.poster);
        if (poster) embed.poster = poster;
        if (item.captions_url) {
          const track = document.createElement("track");
          track.kind = "captions";
          track.srclang = "es";
          track.label = "Español";
          track.src = safeUrl(item.captions_url);
          track.default = true;
          embed.append(track);
        }
      }
      media.append(embed);
      const body = document.createElement("div");
      body.className = "site-video__body";
      const heading = document.createElement("h3");
      heading.textContent = item.title || "Video";
      body.append(heading);
      if (item.description) {
        const description = document.createElement("p");
        description.textContent = item.description;
        body.append(description);
      }
      if (item.cta_label) {
        const cta = document.createElement("a");
        cta.className = "card__link";
        cta.href = safeUrl(item.cta_url || "#contacto");
        cta.textContent = `${item.cta_label} ↗`;
        body.append(cta);
      }
      card.append(media, body);
      grid.append(card);
    });
    section.hidden = !grid.childNodes.length;
  }

  function applyTheme(theme = {}) {
    const root = document.documentElement;
    if (theme.accent) root.style.setProperty("--green", theme.accent);
    if (theme.background) root.style.setProperty("--bg", theme.background);
    if (theme.surface) {
      root.style.setProperty("--bg-soft", theme.surface);
      root.style.setProperty("--panel", theme.surface);
    }
    if (theme.text) root.style.setProperty("--text", theme.text);
    if (theme.muted) root.style.setProperty("--muted", theme.muted);
    if (theme.body_font) {
      const clean = String(theme.body_font).replace(/^['"]|['"]$/g, "");
      root.style.setProperty("--sans", `'${clean}', system-ui, sans-serif`);
    }
    if (theme.radius !== undefined) {
      root.style.setProperty("--radius", `${Number(theme.radius) || 0}px`);
    }
  }

  API.publicApi
    .getSiteLanding("devblog")
    .then((data) => {
      if (data?.site?.theme) applyTheme(data.site.theme);
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
      renderVideos(data?.content?.videos || [], data?.content || {});
    })
    .catch((error) => {
      console.warn("No se pudo cargar el hero del blog desde el CMS:", error);
    });
})();
