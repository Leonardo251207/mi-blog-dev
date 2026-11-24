/* ==========================================================
   Editor enriquecido del CMS
   - Portada, bloques Markdown, vista dividida, tipografía, SEO,
     índice y exportación Markdown/JSON.
   - Los metadatos editoriales se guardan en localStorage; el CMS
     conserva título, slug, etiquetas y contenido Markdown.
   ========================================================== */
(() => {
  "use strict";

  const $ = (selector, ctx = document) => ctx.querySelector(selector);
  const $$ = (selector, ctx = document) => [...ctx.querySelectorAll(selector)];

  const form = $("#draft-form");
  if (!form || !$("#editor-workspace")) return;

  const META_KEY = "devblog_editor_meta_v1";

  const titleInput = $("#f-title");
  const slugInput = $("#f-slug");
  const contentInput = $("#f-content");
  const statusPill = $("#editor-status-pill");
  const saveLabel = $("#editor-save-label");
  const statsEl = $("#editor-stats");
  const preview = $("#preview");
  const previewEmpty = $("#preview-empty");
  const previewStats = $("#preview-stats");
  const previewViewport = $("#preview-viewport");
  const workspace = $("#editor-workspace");
  const grid = $("#blog-grid");

  const coverUrl = $("#f-cover-url");
  const coverFile = $("#f-cover-file");
  const coverClear = $("#f-cover-clear");
  const coverPreview = $("#cover-preview");

  const statusInput = $("#f-status");
  const categoryInput = $("#f-category");
  const authorInput = $("#f-author");
  const dateInput = $("#f-date");
  const seoTitle = $("#f-seo-title");
  const seoDesc = $("#f-seo-desc");
  const seoTitleCount = $("#seo-title-count");
  const seoDescCount = $("#seo-desc-count");
  const seoPreviewTitle = $("#seo-preview-title");
  const seoPreviewDesc = $("#seo-preview-desc");
  const seoPreviewUrl = $("#seo-preview-url");

  const fontHeading = $("#f-font-heading");
  const fontBody = $("#f-font-body");
  const fontCode = $("#f-font-code");
  const fontSize = $("#f-font-size");
  const lineHeight = $("#f-line-height");

  const tocList = $("#editor-toc-list");

  const exportModal = $("#editor-export-modal");
  const exportContent = $("#export-content");
  const exportMd = $("#export-mode-md");
  const exportJson = $("#export-mode-json");

  const state = {
    mode: "idle",
    id: null,
    meta: null,
    viewMode: "split",
    focus: false,
    exportMode: "md",
    saveTimer: null,
  };

  // ------------------------------------------------------------- metadatos
  function readStore() {
    try {
      return JSON.parse(localStorage.getItem(META_KEY) || "{}");
    } catch {
      return {};
    }
  }

  function writeStore(store) {
    try {
      localStorage.setItem(META_KEY, JSON.stringify(store));
    } catch {
      // Ignorar cuota
    }
  }

  function keyFor(id = state.id) {
    return id ? `id:${id}` : "new";
  }

  function defaultMeta(data = {}) {
    const content = data.content || contentInput.value || "";
    return {
      status: state.mode === "post" ? "published" : "draft",
      category: "",
      author: "Leonardo Nucamendi",
      date: data.published_at ? String(data.published_at).slice(0, 10) : "",
      cover: "",
      seoTitle: data.title || titleInput.value || "",
      seoDesc: content
        .replace(/[#*_>`\-\[\]()!]/g, " ")
        .replace(/\s+/g, " ")
        .trim()
        .slice(0, 160),
      typography: {
        heading: "Manrope",
        body: "Manrope",
        code: "'JetBrains Mono'",
        size: 16,
        lineHeight: 1.7,
      },
    };
  }

  function loadMeta(data = {}) {
    const key = keyFor();
    const store = readStore();
    const stored = store[key] || null;
    const base = defaultMeta(data);
    state.meta = {
      ...base,
      ...(stored || {}),
      typography: { ...base.typography, ...(stored?.typography || {}) },
    };
    // Un artículo publicado siempre se muestra como publicado.
    if (state.mode === "post") state.meta.status = "published";
    fillMetaFields();
  }

  function persistMeta() {
    if (!state.meta) return;
    state.meta = {
      status: statusInput.value,
      category: categoryInput.value.trim(),
      author: authorInput.value.trim(),
      date: dateInput.value,
      cover: coverUrl.value.trim(),
      seoTitle: seoTitle.value.trim(),
      seoDesc: seoDesc.value.trim(),
      typography: {
        heading: fontHeading.value,
        body: fontBody.value,
        code: fontCode.value,
        size: Number(fontSize.value) || 16,
        lineHeight: Number(lineHeight.value) || 1.7,
      },
    };
    const store = readStore();
    store[keyFor()] = state.meta;
    writeStore(store);
    markSaved();
  }

  function schedulePersist() {
    if (state.saveTimer) clearTimeout(state.saveTimer);
    saveLabel.textContent = "○ Guardando…";
    saveLabel.classList.remove("is-saved");
    saveLabel.classList.add("is-saving");
    state.saveTimer = setTimeout(() => {
      persistMeta();
      state.saveTimer = null;
    }, 320);
  }

  function markSaved() {
    const now = new Date().toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" });
    saveLabel.textContent = `● Guardado ${now}`;
    saveLabel.classList.remove("is-saving");
    saveLabel.classList.add("is-saved");
  }

  function fillMetaFields() {
    const meta = state.meta || defaultMeta();
    statusInput.value = meta.status || "draft";
    categoryInput.value = meta.category || "";
    authorInput.value = meta.author || "";
    dateInput.value = meta.date || "";
    coverUrl.value = meta.cover || "";
    seoTitle.value = meta.seoTitle || titleInput.value || "";
    seoDesc.value = meta.seoDesc || "";
    fontHeading.value = meta.typography?.heading || "Manrope";
    fontBody.value = meta.typography?.body || "Manrope";
    fontCode.value = meta.typography?.code || "'JetBrains Mono'";
    fontSize.value = meta.typography?.size || 16;
    lineHeight.value = meta.typography?.lineHeight || 1.7;
    renderStatus();
    renderCover();
    renderSeo();
    renderTypography();
  }

  // -------------------------------------------------------------- portada
  function renderCover() {
    if (!coverPreview) return;
    const value = coverUrl.value.trim();
    coverPreview.replaceChildren();
    if (value) {
      const img = document.createElement("img");
      img.src = value;
      img.alt = "Portada del artículo";
      img.onerror = () => {
        coverPreview.replaceChildren(document.createTextNode("No se pudo cargar la portada"));
      };
      coverPreview.append(img);
    } else {
      const span = document.createElement("span");
      span.textContent = "Sin portada";
      coverPreview.append(span);
    }
  }

  function setCover(value) {
    coverUrl.value = value;
    renderCover();
    schedulePersist();
    renderPreview();
  }

  // ------------------------------------------------------------- tipografía
  function quoteFont(value) {
    const clean = String(value || "Manrope").replace(/^['"]|['"]$/g, "");
    return `'${clean}'`;
  }

  function renderTypography() {
    const heading = fontHeading.value || "Manrope";
    const body = fontBody.value || "Manrope";
    const code = fontCode.value || "'JetBrains Mono'";
    preview.style.setProperty("--preview-heading-font", `${quoteFont(heading)}, sans-serif`);
    preview.style.setProperty("--preview-body-font", `${quoteFont(body)}, sans-serif`);
    preview.style.setProperty("--preview-code-font", `${quoteFont(code)}, monospace`);
    preview.style.setProperty("--preview-font-size", `${Number(fontSize.value) || 16}px`);
    preview.style.setProperty("--preview-line-height", String(Number(lineHeight.value) || 1.7));
    renderPreview();
  }

  // ------------------------------------------------------------------ SEO
  function renderSeo() {
    const title = seoTitle.value.trim() || titleInput.value.trim() || "Título del artículo";
    const desc = seoDesc.value.trim() || "Descripción del artículo para buscadores.";
    const slug = slugInput.value.trim() || "slug-del-articulo";
    if (seoTitleCount) seoTitleCount.textContent = `${seoTitle.value.length}/60`;
    if (seoDescCount) seoDescCount.textContent = `${seoDesc.value.length}/160`;
    if (seoPreviewTitle) seoPreviewTitle.textContent = title;
    if (seoPreviewDesc) seoPreviewDesc.textContent = desc;
    if (seoPreviewUrl) seoPreviewUrl.textContent = `mi-blog-dev.vercel.app › articulo › ${slug}`;
  }

  // ----------------------------------------------------------- estadísticas
  function computeStats() {
    const content = contentInput.value.trim();
    const words = content ? content.split(/\s+/).filter(Boolean).length : 0;
    const read = Math.max(1, Math.ceil(words / 200));
    const blocks = content ? content.split(/\n{2,}/).filter((block) => block.trim()).length : 0;
    return { words, read, blocks };
  }

  function renderStats() {
    const stats = computeStats();
    if (statsEl) statsEl.textContent = `${stats.words} palabras · ${stats.read} min`;
    if (previewStats) previewStats.textContent = `${stats.blocks} bloques · ${stats.words} palabras`;
  }

  // -------------------------------------------------------------- preview
  function stripMarkdown(value) {
    return String(value || "")
      .replace(/```[\s\S]*?```/g, " ")
      .replace(/`[^`]*`/g, " ")
      .replace(/[#>*_\-\[\]()!]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function renderPreview() {
    if (!preview) return;
    const content = contentInput.value.trim();
    const title = titleInput.value.trim();

    if (!title && !content) {
      preview.replaceChildren();
      if (previewEmpty) previewEmpty.hidden = false;
      renderToc([]);
      return;
    }
    if (previewEmpty) previewEmpty.hidden = true;

    const fragment = document.createDocumentFragment();
    const header = document.createElement("header");
    header.className = "editor-preview__header";

    if (coverUrl.value.trim()) {
      const cover = document.createElement("img");
      cover.className = "editor-preview__cover";
      cover.src = coverUrl.value.trim();
      cover.alt = "Portada del artículo";
      header.append(cover);
    }

    const meta = document.createElement("p");
    meta.className = "editor-preview__meta";
    const category = categoryInput.value.trim() || "Artículo";
    const date = dateInput.value
      ? new Date(`${dateInput.value}T12:00:00`).toLocaleDateString("es-MX", {
          day: "2-digit",
          month: "short",
          year: "numeric",
        })
      : "";
    const reading = computeStats().read;
    meta.textContent = [category, date, `${reading} min de lectura`].filter(Boolean).join(" · ");
    header.append(meta);

    const h1 = document.createElement("h1");
    h1.textContent = title || "Título del artículo";
    header.append(h1);

    const tags = tagsArray();
    if (tags.length) {
      const tagWrap = document.createElement("div");
      tagWrap.className = "editor-preview__tags";
      tags.forEach((tag) => {
        const chip = document.createElement("span");
        chip.textContent = tag;
        tagWrap.append(chip);
      });
      header.append(tagWrap);
    }

    fragment.append(header);

    const body = document.createElement("div");
    if (content && window.DevBlogMarkdown?.render) {
      body.innerHTML = window.DevBlogMarkdown.render(content);
    } else {
      const p = document.createElement("p");
      p.textContent = content || "Escribe el contenido del artículo en Markdown.";
      body.append(p);
    }
    fragment.append(body);

    preview.replaceChildren(fragment);
    assignHeadingIds();
    renderToc();
  }

  function tagsArray() {
    return ($("#f-tags")?.value || "")
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);
  }

  function assignHeadingIds() {
    $$("#preview h2, #preview h3").forEach((heading, index) => {
      heading.id = `preview-heading-${index}`;
    });
  }

  function extractHeadings() {
    const headings = [];
    const regex = /^(#{2,3})\s+(.+)$/gm;
    let match;
    while ((match = regex.exec(contentInput.value))) {
      headings.push({
        level: match[1].length,
        text: match[2].replace(/[*_`]/g, "").trim(),
      });
    }
    return headings;
  }

  function renderToc(headings = extractHeadings()) {
    if (!tocList) return;
    tocList.replaceChildren();
    if (!headings.length) {
      const li = document.createElement("li");
      li.textContent = "Sin encabezados H2/H3.";
      li.className = "editor-pro__hint";
      tocList.append(li);
      return;
    }
    headings.forEach((heading, index) => {
      const li = document.createElement("li");
      li.dataset.level = String(heading.level);
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = heading.text;
      button.addEventListener("click", () => {
        const target = document.getElementById(`preview-heading-${index}`);
        target?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
      li.append(button);
      tocList.append(li);
    });
  }

  // -------------------------------------------------------------- estado
  function renderStatus() {
    const status = statusInput.value || "draft";
    const labels = { draft: "Borrador", review: "En revisión", published: "Publicado" };
    statusPill.dataset.status = status;
    statusPill.textContent = labels[status] || "Borrador";
  }

  function setViewMode(mode) {
    state.viewMode = mode;
    workspace.classList.toggle("is-split", mode === "split");
    workspace.classList.toggle("is-preview-only", mode === "preview");
    workspace.classList.toggle("is-edit-only", mode === "edit");
    $("#editor-view-split").classList.toggle("is-active", mode === "split");
    $("#editor-view-preview").classList.toggle("is-active", mode === "preview");
    $("#editor-view-edit").classList.toggle("is-active", mode === "edit");
    if (preview) preview.hidden = mode === "edit";
    if (previewEmpty) previewEmpty.hidden = Boolean(contentInput.value.trim() || titleInput.value.trim());
    if (mode !== "edit") renderPreview();
  }

  function setMode(mode, id) {
    state.mode = mode || "idle";
    state.id = id || null;
    const editing = mode === "new" || mode === "draft" || mode === "post";
    if (editing && !state.focus) {
      state.focus = true;
      grid?.classList.add("is-focus");
      const focusBtn = $("#editor-focus");
      if (focusBtn) focusBtn.textContent = "Ver lista";
    }
    if (!editing) {
      state.focus = false;
      grid?.classList.remove("is-focus");
      const focusBtn = $("#editor-focus");
      if (focusBtn) focusBtn.textContent = "Enfoque";
    }
    const editable = mode === "new" || mode === "draft";
    [
      statusInput,
      categoryInput,
      authorInput,
      dateInput,
      coverUrl,
      coverFile,
      coverClear,
      seoTitle,
      seoDesc,
      fontHeading,
      fontBody,
      fontCode,
      fontSize,
      lineHeight,
    ].forEach((input) => {
      if (input) input.disabled = !editable;
    });
    $$(".editor-pro__toolbar button").forEach((button) => {
      button.disabled = !editable;
    });
    if (mode === "post" && state.meta) {
      statusInput.value = "published";
      renderStatus();
    }
    setViewMode(state.viewMode);
    renderPreview();
    renderStats();
  }

  function load({ mode, id, data }) {
    state.mode = mode || state.mode;
    state.id = id || null;
    loadMeta(data || {});
    renderPreview();
    renderStats();
    markSaved();
    setMode(state.mode, state.id);
  }

  function clear() {
    state.mode = "idle";
    state.id = null;
    state.meta = defaultMeta({});
    if (coverFile) coverFile.value = "";
    fillMetaFields();
    renderCover();
    renderPreview();
    renderStats();
  }

  function saved(id) {
    const oldKey = keyFor();
    if (id && !state.id) {
      state.id = id;
      const store = readStore();
      if (store[oldKey]) {
        store[keyFor(id)] = store[oldKey];
        delete store[oldKey];
        writeStore(store);
      }
    }
    persistMeta();
  }

  // ------------------------------------------------------------- toolbar
  function insertBlock(type) {
    const snippets = {
      paragraph: "\n\n",
      h2: "\n\n## ",
      h3: "\n\n### ",
      code: "\n\n```js\n\n```\n",
      callout: "\n\n> **Nota:** ",
      list: "\n\n- ",
      quote: "\n\n> ",
      image: "\n\n![Descripción de la imagen](https://)",
      divider: "\n\n---\n",
    };
    const snippet = snippets[type];
    if (!snippet) return;
    const start = contentInput.selectionStart ?? contentInput.value.length;
    const end = contentInput.selectionEnd ?? start;
    contentInput.setRangeText(snippet, start, end, "end");
    contentInput.focus();
    contentInput.dispatchEvent(new Event("input", { bubbles: true }));
  }

  // ------------------------------------------------------------- exportar
  function buildMarkdown() {
    const tags = tagsArray().join(", ");
    const front = [
      "---",
      `title: "${(titleInput.value || "").replace(/"/g, '\\"')}"`,
      `slug: "${slugInput.value || ""}"`,
      `status: "${statusInput.value || "draft"}"`,
      `category: "${categoryInput.value || ""}"`,
      `author: "${authorInput.value || ""}"`,
      `date: "${dateInput.value || ""}"`,
      `tags: [${tags}]`,
      `cover: "${coverUrl.value || ""}"`,
      `seo_title: "${seoTitle.value || ""}"`,
      `seo_description: "${(seoDesc.value || "").replace(/"/g, '\\"')}"`,
      "---",
      "",
      contentInput.value || "",
    ];
    return front.join("\n");
  }

  function buildJson() {
    return JSON.stringify(
      {
        title: titleInput.value,
        slug: slugInput.value,
        tags: tagsArray(),
        status: statusInput.value,
        category: categoryInput.value,
        author: authorInput.value,
        date: dateInput.value,
        cover: coverUrl.value,
        seo: { title: seoTitle.value, description: seoDesc.value },
        typography: {
          heading: fontHeading.value,
          body: fontBody.value,
          code: fontCode.value,
          size: Number(fontSize.value) || 16,
          lineHeight: Number(lineHeight.value) || 1.7,
        },
        content: contentInput.value,
        stats: computeStats(),
      },
      null,
      2
    );
  }

  function renderExport() {
    if (!exportContent) return;
    exportContent.textContent = state.exportMode === "json" ? buildJson() : buildMarkdown();
    exportMd.classList.toggle("is-active", state.exportMode === "md");
    exportJson.classList.toggle("is-active", state.exportMode === "json");
  }

  function openExport() {
    renderExport();
    exportModal.hidden = false;
  }

  function closeExport() {
    exportModal.hidden = true;
  }

  async function copyExport() {
    const text = exportContent.textContent || "";
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const area = document.createElement("textarea");
      area.value = text;
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.append(area);
      area.select();
      document.execCommand("copy");
      area.remove();
    }
    saveLabel.textContent = "● Exportado al portapapeles";
  }

  function downloadExport() {
    const isJson = state.exportMode === "json";
    const text = exportContent.textContent || "";
    const slug = slugInput.value.trim() || "articulo";
    const blob = new Blob([text], { type: isJson ? "application/json;charset=utf-8" : "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${slug}.${isJson ? "json" : "md"}`;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  }

  // ------------------------------------------------------------- eventos
  function bind() {
    previewViewport?.addEventListener("change", () => {
      const value = previewViewport.value;
      preview.style.setProperty("--preview-width", value === "auto" ? "100%" : `${value}px`);
    });

    $("#editor-view-split")?.addEventListener("click", () => setViewMode("split"));
    $("#editor-view-preview")?.addEventListener("click", () => setViewMode("preview"));
    $("#editor-view-edit")?.addEventListener("click", () => setViewMode("edit"));

    $("#editor-focus")?.addEventListener("click", () => {
      state.focus = !state.focus;
      grid?.classList.toggle("is-focus", state.focus);
      $("#editor-focus").textContent = state.focus ? "Ver lista" : "Enfoque";
    });

    $$(".editor-pro__toolbar button").forEach((button) => {
      button.addEventListener("click", () => insertBlock(button.dataset.block));
    });

    $$(".editor-pro__inspector-tabs button").forEach((button) => {
      button.addEventListener("click", () => {
        const target = button.dataset.inspector;
        $$(".editor-pro__inspector-tabs button").forEach((item) => {
          item.classList.toggle("is-active", item === button);
        });
        $$("[data-inspector-panel]").forEach((panel) => {
          panel.hidden = panel.dataset.inspectorPanel !== target;
        });
      });
    });

    [statusInput, categoryInput, authorInput, dateInput, coverUrl, seoTitle, seoDesc, fontHeading, fontBody, fontCode, fontSize, lineHeight].forEach((input) => {
      input?.addEventListener("input", () => {
        schedulePersist();
        if (input === statusInput) renderStatus();
        if (input === coverUrl) renderCover();
        if (input === seoTitle || input === seoDesc) renderSeo();
        if ([fontHeading, fontBody, fontCode, fontSize, lineHeight].includes(input)) renderTypography();
        renderPreview();
      });
      input?.addEventListener("change", () => {
        schedulePersist();
        if (input === statusInput) renderStatus();
        if (input === coverUrl) renderCover();
        if (input === seoTitle || input === seoDesc) renderSeo();
        if ([fontHeading, fontBody, fontCode, fontSize, lineHeight].includes(input)) renderTypography();
        renderPreview();
      });
    });

    coverFile?.addEventListener("change", () => {
      const file = coverFile.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => setCover(String(reader.result || ""));
      reader.readAsDataURL(file);
    });

    coverClear?.addEventListener("click", () => {
      coverFile.value = "";
      setCover("");
    });

    ["input", "change"].forEach((eventName) => {
      titleInput.addEventListener(eventName, () => {
        renderPreview();
        renderSeo();
        schedulePersist();
      });
      slugInput.addEventListener(eventName, () => {
        renderSeo();
        schedulePersist();
      });
      contentInput.addEventListener(eventName, () => {
        renderPreview();
        renderStats();
        schedulePersist();
      });
      $("#f-tags")?.addEventListener(eventName, () => {
        renderPreview();
        schedulePersist();
      });
    });

    $("#editor-export")?.addEventListener("click", openExport);
    $("#export-close")?.addEventListener("click", closeExport);
    exportModal?.addEventListener("click", (event) => {
      if (event.target === exportModal) closeExport();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeExport();
    });
    exportMd?.addEventListener("click", () => {
      state.exportMode = "md";
      renderExport();
    });
    exportJson?.addEventListener("click", () => {
      state.exportMode = "json";
      renderExport();
    });
    $("#export-copy")?.addEventListener("click", copyExport);
    $("#export-download")?.addEventListener("click", downloadExport);

    document.addEventListener("keydown", (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        const saveButton = $("#save-draft");
        if (saveButton && !saveButton.disabled) form.requestSubmit();
      }
    });

    window.addEventListener("beforeunload", () => {
      if (state.saveTimer) {
        clearTimeout(state.saveTimer);
        persistMeta();
      }
    });
  }

  // La vista previa la controla este módulo, no el botón antiguo.
  bind();
  clear();

  window.DevBlogEditorPro = { load, clear, setMode, saved, setViewMode };
})();
