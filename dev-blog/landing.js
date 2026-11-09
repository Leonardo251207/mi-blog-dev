/* ==========================================================
   Landing dinámica
   - Pide el contenido publicado al CMS y actualiza la portada.
   - Si la API no responde, deja intacto el HTML estático (fallback).
   - La publicidad se pinta solo si está activa y tiene contenido.
   ========================================================== */
(() => {
  "use strict";

  const API = window.DevBlogAPI;
  if (!API || !API.publicApi) return;

  const $ = (selector, ctx = document) => ctx.querySelector(selector);
  const $$ = (selector, ctx = document) => [...ctx.querySelectorAll(selector)];

  function getPath(source, path) {
    return String(path || "")
      .split(".")
      .reduce((value, key) => (value == null ? undefined : value[key]), source);
  }

  function setText(selector, value) {
    if (value === undefined || value === null) return;
    const element = $(selector);
    if (element) element.textContent = String(value);
  }

  function safeHref(value, { image = false } = {}) {
    const raw = String(value || "").trim();
    if (!raw) return "";
    if (image && /^data:image\//i.test(raw)) return raw;
    if (/^(javascript|vbscript|data):/i.test(raw)) return "#";
    return raw;
  }

  function applyText(content) {
    $$("[data-landing]").forEach((element) => {
      const value = getPath(content, element.dataset.landing);
      if (value !== undefined && value !== null) element.textContent = String(value);
    });
  }

  function applyLinks(content) {
    $$("[data-landing-href]").forEach((element) => {
      const value = getPath(content, element.dataset.landingHref);
      if (typeof value === "string" && value.trim()) {
        element.href = safeHref(value);
        if (/^https?:/i.test(value)) {
          element.target = "_blank";
          element.rel = "noopener noreferrer";
        }
      }
    });

    $$("[data-landing-src]").forEach((element) => {
      const value = getPath(content, element.dataset.landingSrc);
      if (typeof value === "string" && value.trim()) {
        element.src = safeHref(value, { image: true });
      }
    });
  }

  function applyName(content) {
    const heading = $("[data-landing-name]");
    if (!heading || !content.hero) return;
    heading.replaceChildren(
      document.createTextNode(content.hero.first_name || ""),
      document.createTextNode(" ")
    );
    const last = document.createElement("span");
    last.textContent = content.hero.last_name || "";
    heading.append(last);

    const photo = $("[data-landing-src='hero.photo_url']");
    if (photo) {
      const fullName = [content.hero.first_name, content.hero.last_name]
        .filter(Boolean)
        .join(" ");
      photo.alt = `Foto de ${fullName}`;
    }
  }

  function applyEmail(content) {
    $$("[data-landing-email]").forEach((element) => {
      const value = getPath(content, element.dataset.landingEmail);
      if (typeof value !== "string" || !value.trim()) return;
      element.dataset.email = value.trim();
      element.href = `mailto:${value.trim()}`;
      element.dispatchEvent(new CustomEvent("devblog:email"));
    });
  }

  function renderTechnologies(technologies) {
    const list = $("[data-landing-tech]");
    if (!list || !Array.isArray(technologies) || !technologies.length) return;

    const fragment = document.createDocumentFragment();
    technologies.forEach((tech) => {
      const item = document.createElement("li");
      const icon = document.createElement("span");
      icon.className = "tech__icon";
      icon.style.setProperty("--c", tech.color || "var(--green)");
      icon.setAttribute("aria-hidden", "true");
      icon.textContent = tech.icon || String(tech.name || "").slice(0, 2).toUpperCase();

      item.append(icon, document.createTextNode(tech.name || ""));
      fragment.append(item);
    });
    list.replaceChildren(fragment);
  }

  function artClass(kind) {
    if (kind === "green") return "art art--glow-green";
    if (kind === "purple") return "art art--glow-purple";
    return "art art--dots";
  }

  function updateProject(card, project) {
    const body = card.querySelector(".card__body");
    if (!body) return;

    const badge = body.querySelector(".badge");
    if (badge) badge.textContent = project.badge || "";

    const title = body.querySelector("h3");
    if (title) title.textContent = project.title || "";

    const description = body.querySelector("p");
    if (description) description.textContent = project.description || "";

    const link = body.querySelector(".card__link");
    if (link) link.textContent = project.link_label || "";

    const art = card.querySelector(".art");
    if (art) art.className = artClass(project.art);

    if (card.tagName === "A") {
      if (project.url) {
        card.href = safeHref(project.url);
        card.target = "_blank";
        card.rel = "noopener noreferrer";
      } else {
        card.removeAttribute("href");
        card.removeAttribute("target");
        card.removeAttribute("rel");
      }
    }
  }

  function renderProjects(projects) {
    const grid = $("[data-landing-projects]");
    if (!grid || !Array.isArray(projects) || !projects.length) return;

    let cards = $$("[data-landing-project]", grid);
    const template = cards[0] ? cards[0].cloneNode(true) : null;

    while (cards.length > projects.length) {
      cards[cards.length - 1].remove();
      cards = $$("[data-landing-project]", grid);
    }
    while (template && cards.length < projects.length) {
      const clone = template.cloneNode(true);
      $$("[id]", clone).forEach((element) => element.removeAttribute("id"));
      grid.append(clone);
      cards = $$("[data-landing-project]", grid);
    }

    cards.forEach((card, index) => updateProject(card, projects[index]));
  }

  function updateCertification(card, certification) {
    const body = card.querySelector(".card__body");
    if (!body) return;

    const issuer = body.querySelector(".cert__issuer");
    if (issuer) issuer.textContent = certification.issuer || "";

    const title = body.querySelector("h3");
    if (title) title.textContent = certification.title || "";

    const tag = card.querySelector(".cert__tag");
    if (tag) tag.textContent = certification.tag || "";

    const art = card.querySelector(".cert__art");
    if (art && certification.color) art.style.setProperty("--c", certification.color);

    if (card.tagName === "A") {
      if (certification.url) {
        card.href = safeHref(certification.url);
        card.target = "_blank";
        card.rel = "noopener";
      } else {
        card.removeAttribute("href");
        card.removeAttribute("target");
        card.removeAttribute("rel");
      }
    }
  }

  function renderCertifications(certifications) {
    const grid = $("[data-landing-certifications]");
    if (!grid || !Array.isArray(certifications) || !certifications.length) return;

    let cards = $$("[data-landing-cert]", grid);
    const template = cards[0] ? cards[0].cloneNode(true) : null;

    while (cards.length > certifications.length) {
      cards[cards.length - 1].remove();
      cards = $$("[data-landing-cert]", grid);
    }
    while (template && cards.length < certifications.length) {
      const clone = template.cloneNode(true);
      $$("[id]", clone).forEach((element) => element.removeAttribute("id"));
      grid.append(clone);
      cards = $$("[data-landing-cert]", grid);
    }

    cards.forEach((card, index) => updateCertification(card, certifications[index]));
  }

  function renderAd(ad) {
    const section = $("[data-landing-ad]");
    if (!section) return;
    if (!ad || ad.active === false) {
      section.hidden = true;
      return;
    }

    const card = $("[data-ad-card]", section);
    if (!card) return;

    card.className = `ad ad--${ad.layout || "banner"}`;
    card.classList.toggle("ad--con-media", Boolean(ad.image_url));
    const theme = ad.theme || {};
    card.style.setProperty("--ad-bg", theme.background || "#0b1110");
    card.style.setProperty("--ad-text", theme.text || "#eef5f1");
    card.style.setProperty("--ad-accent", theme.accent || "#3df0a8");

    setText("[data-ad-title]", ad.title || "Publicidad");
    const subtitle = $("[data-ad-subtitle]", section);
    if (subtitle) {
      subtitle.textContent = ad.subtitle || "";
      subtitle.hidden = !ad.subtitle;
    }
    const body = $("[data-ad-text]", section);
    if (body) {
      body.textContent = ad.body || "";
      body.hidden = !ad.body;
    }

    const media = $("[data-ad-media]", section);
    const image = $("[data-ad-image]", section);
    if (media && image) {
      if (ad.image_url) {
        image.src = safeHref(ad.image_url, { image: true });
        image.alt = ad.title || "Publicidad";
        media.hidden = false;
      } else {
        image.removeAttribute("src");
        media.hidden = true;
      }
    }

    const cta = $("[data-ad-cta]", section);
    if (cta) {
      if (ad.cta_label) {
        cta.textContent = ad.cta_label;
        cta.href = safeHref(ad.cta_url || "#contacto");
        cta.hidden = false;
        if (/^https?:/i.test(ad.cta_url || "")) {
          cta.target = "_blank";
          cta.rel = "noopener noreferrer";
        }
      } else {
        cta.hidden = true;
      }
    }

    section.hidden = false;
  }

  async function load() {
    try {
      const data = await API.publicApi.getLanding();
      const content = data.content || {};
      applyText(content);
      applyLinks(content);
      applyName(content);
      applyEmail(content);
      renderTechnologies(content.technologies);
      renderProjects(content.projects);
      renderCertifications(content.certifications);
      renderAd(data.ad);
    } catch (error) {
      // El HTML estático sigue siendo la fuente de respaldo.
      console.warn("No se pudo cargar la landing desde el CMS:", error);
    }
  }

  load();
})();
