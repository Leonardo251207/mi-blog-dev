/* ==========================================================
   Consola de administración del CMS
   - El token se escribe en la página y se guarda en sessionStorage.
   - Nunca se incluye el token de consola en api-config.js.
   ========================================================== */
(() => {
  "use strict";

  const API = window.DevBlogAPI;
  if (!API) {
    console.error("No se cargó api.js");
    return;
  }
  const { adminApi, ApiError } = API;

  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector, ctx = document) => [...ctx.querySelectorAll(selector)];

  const authPanel = $("#auth-panel");
  const authForm = $("#auth-form");
  const tokenInput = $("#token");
  const authStatus = $("#auth-status");
  const workspace = $("#workspace");
  const logoutBtn = $("#logout");
  const apiUrlEl = $("#api-url");
  const healthLink = $("#health-link");

  const editorFields = $("#editor-fields");
  const titleInput = $("#f-title");
  const slugInput = $("#f-slug");
  const tagsInput = $("#f-tags");
  const contentInput = $("#f-content");

  const saveBtn = $("#save-draft");
  const publishBtn = $("#publish-draft");
  const deleteDraftBtn = $("#delete-draft");
  const deletePostBtn = $("#delete-post");
  const previewBtn = $("#toggle-preview");
  const preview = $("#preview");
  const metrics = $("#metrics");
  const staticResult = $("#static-result");
  const generateStaticBtn = $("#generate-static");
  const statusEl = $("#workspace-status");

  const STATIC_GENERATOR_BASE_URL = String(
    (window.DEVBLOG_CONFIG && window.DEVBLOG_CONFIG.STATIC_GENERATOR_BASE_URL) ||
      "http://127.0.0.1:8001"
  ).replace(/\/+$/, "");

  const draftsList = $("#drafts-list");
  const postsList = $("#posts-list");
  const moreDraftsBtn = $("#more-drafts");
  const morePostsBtn = $("#more-posts");

  let token = sessionStorage.getItem("devblog_console_token") || "";
  let mode = "idle";            // idle | new | draft | post
  let currentId = null;
  let draftsCursor = null;
  let postsCursor = null;
  let previewVisible = false;

  const dateFormatter = new Intl.DateTimeFormat("es-MX", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  // ------------------------------------------------------------- utilidades
  apiUrlEl.textContent = API.config.API_BASE_URL;
  healthLink.href = new URL("/health", API.config.API_BASE_URL).href;

  const config = window.DEVBLOG_CONFIG || {};
  const metricsBase = String(config.METRICS_BASE_URL || "http://127.0.0.1:8000")
    .replace(/\/+$/, "");
  const metricsLink = $("#metrics-link");
  const generatorLink = $("#generator-link");
  const landingLink = $("#landing-link");
  if (metricsLink) metricsLink.href = `${metricsBase}/v1/query`;
  if (generatorLink) generatorLink.href = `${STATIC_GENERATOR_BASE_URL}/docs`;
  if (landingLink && config.LANDING_BASE_URL) {
    landingLink.href = `${String(config.LANDING_BASE_URL).replace(/\/+$/, "")}/`;
  }

  function formatDate(value) {
    if (!value) return "—";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "—" : dateFormatter.format(date);
  }

  function setStatus(message, kind = "info", target = statusEl) {
    target.textContent = message;
    target.dataset.kind = kind;
  }

  function setAuthStatus(message, kind = "info") {
    setStatus(message, kind, authStatus);
  }

  function setMode(next) {
    mode = next;
    const editable = next === "new" || next === "draft";

    // El fieldset NO se deshabilita: si se deshabilita, también se bloquean
    // los botones de acción (por ejemplo, "Eliminar publicación"). Se
    // deshabilitan solo los campos de texto.
    editorFields.disabled = false;
    titleInput.disabled = !editable;
    slugInput.disabled = !editable;
    tagsInput.disabled = !editable;
    contentInput.disabled = !editable;

    saveBtn.disabled = !editable;
    publishBtn.disabled = next !== "draft";
    deleteDraftBtn.disabled = next !== "draft";
    deletePostBtn.hidden = next !== "post";
    deletePostBtn.disabled = next !== "post";
    generateStaticBtn.disabled = next !== "draft" && next !== "post";
    previewBtn.disabled = next === "idle";

    preview.hidden = true;
    previewVisible = false;
    previewBtn.textContent = "Vista previa";
    window.DevBlogEditorPro?.setMode(next, currentId);
  }

  function clearForm() {
    titleInput.value = "";
    slugInput.value = "";
    tagsInput.value = "";
    contentInput.value = "";
    preview.replaceChildren();
    staticResult.hidden = true;
    staticResult.replaceChildren();
    window.DevBlogEditorPro?.clear();
  }

  function fillForm(data) {
    titleInput.value = data.title || "";
    slugInput.value = data.slug || "";
    tagsInput.value = Array.isArray(data.tags) ? data.tags.join(", ") : "";
    contentInput.value = data.content || "";
    preview.replaceChildren();
    staticResult.hidden = true;
    staticResult.replaceChildren();
    window.DevBlogEditorPro?.load({ mode, id: currentId, data });
  }

  function readForm() {
    const title = titleInput.value.trim();
    const slug = slugInput.value.trim();
    const content = contentInput.value;
    const tags = tagsInput.value
      .split(",")
      .map((tag) => tag.trim().toLowerCase().replace(/\s+/g, "-"))
      .filter(Boolean);

    const data = { title, content, tags };
    if (slug) data.slug = slug;
    return data;
  }

  function handleError(error, target = statusEl) {
    console.error(error);
    let message;
    if (error instanceof ApiError) {
      message = `${error.code}: ${error.message}`;
      if (error.field) message += ` (campo: ${error.field})`;
    } else {
      message = `Error inesperado: ${error.message || error}`;
    }
    setStatus(message, "error", target);

    if (error instanceof ApiError && (error.status === 401 || error.status === 403) && target !== authStatus) {
      sessionStorage.removeItem("devblog_console_token");
      token = "";
      authPanel.hidden = false;
      workspace.hidden = true;
      logoutBtn.hidden = true;
      setMode("idle");
      clearForm();
      setAuthStatus("El token ya no es válido. Vuelve a conectar.", "error");
    }
  }

  function emptyItem(text) {
    const li = document.createElement("li");
    li.className = "admin__empty";
    li.textContent = text;
    return li;
  }

  function listItem(kind, item) {
    const li = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "admin__item";

    const title = document.createElement("strong");
    title.textContent = item.title;

    const meta = document.createElement("small");
    meta.textContent = kind === "draft"
      ? `${item.slug} · ${formatDate(item.updated_at)}`
      : `${item.reading_time_min} min · ${formatDate(item.published_at)}`;

    button.append(title, meta);
    button.addEventListener("click", () => {
      if (kind === "draft") openDraft(item.post_id);
      else openPost(item.post_id);
    });
    li.append(button);
    return li;
  }

  // --------------------------------------------------------------- listados
  async function loadDrafts({ reset = true } = {}) {
    if (reset) {
      draftsCursor = null;
      draftsList.replaceChildren();
    }
    try {
      const page = await adminApi.listDrafts(token, { limit: 50, cursor: draftsCursor });
      draftsCursor = page.next_cursor || null;
      if (reset && !page.items.length) {
        draftsList.append(emptyItem("Sin borradores."));
      }
      for (const item of page.items) draftsList.append(listItem("draft", item));
      moreDraftsBtn.hidden = !draftsCursor;
    } catch (error) {
      handleError(error);
    }
  }

  async function loadPosts({ reset = true } = {}) {
    if (reset) {
      postsCursor = null;
      postsList.replaceChildren();
    }
    try {
      const page = await adminApi.listPosts(token, { limit: 50, cursor: postsCursor });
      postsCursor = page.next_cursor || null;
      if (reset && !page.items.length) {
        postsList.append(emptyItem("Sin publicaciones."));
      }
      for (const item of page.items) postsList.append(listItem("post", item));
      morePostsBtn.hidden = !postsCursor;
    } catch (error) {
      handleError(error);
    }
  }

  async function refreshLists() {
    await Promise.all([loadDrafts({ reset: true }), loadPosts({ reset: true })]);
  }

  // ---------------------------------------------------------------- detalle
  async function openDraft(postId) {
    try {
      const draft = await adminApi.getDraft(token, postId);
      currentId = postId;
      fillForm(draft);
      metrics.hidden = true;
      metrics.replaceChildren();
      setMode("draft");
      setStatus(`Borrador cargado: ${draft.slug}`, "info");
      titleInput.focus();
    } catch (error) {
      handleError(error);
    }
  }

  async function openPost(postId) {
    try {
      const post = await adminApi.getPost(token, postId);
      currentId = postId;
      fillForm(post);
      setMode("post");
      setStatus(`Publicación cargada: ${post.slug}`, "info");
      const data = await adminApi.getMetrics(token, postId);
      showMetrics(data);
    } catch (error) {
      handleError(error);
    }
  }

  function metricBox(label, value) {
    const box = document.createElement("div");
    box.className = "admin__metric";
    const caption = document.createElement("span");
    caption.textContent = label;
    const strong = document.createElement("strong");
    strong.textContent = value;
    box.append(caption, strong);
    return box;
  }

  function showMetrics(data) {
    metrics.replaceChildren(
      metricBox("Vistas", String(data.views_total)),
      metricBox("Lectura", `${data.reading_time_min} min`),
      metricBox("Publicado", formatDate(data.published_at))
    );
    metrics.hidden = false;
  }

  function showStaticResult(data) {
    const checksum = data.checksum_sha256 || "";
    staticResult.replaceChildren(
      metricBox("Estado", data.status || "—"),
      metricBox("Motor", data.engine || "—"),
      metricBox("SHA-256", checksum ? `${checksum.slice(0, 16)}…` : "—")
    );
    if (data.output_url) {
      const link = document.createElement("a");
      link.className = "btn btn--ghost";
      link.href = `${STATIC_GENERATOR_BASE_URL}${data.output_url}`;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = "Abrir HTML generado →";
      staticResult.append(link);
    }
    staticResult.hidden = false;
  }

  // Convierte el Markdown del CMS en los bloques que espera el generador.
  function markdownToBlocks(markdown) {
    const lines = String(markdown || "").replace(/\r\n?/g, "\n").split("\n");
    const blocks = [];
    let paragraph = [];
    let order = 0;

    const push = (blockType, contentPayload) => {
      order += 1;
      blocks.push({
        block_id: `blk-${order}`,
        block_type: blockType,
        order_index: order,
        content_payload: contentPayload,
      });
    };
    const flush = () => {
      if (paragraph.length) {
        push("PARAGRAPH", { text: paragraph.join("\n") });
        paragraph = [];
      }
    };

    for (let index = 0; index < lines.length; index += 1) {
      const line = lines[index];

      const fence = line.match(/^```(\w+)?\s*$/);
      if (fence) {
        flush();
        const language = fence[1] || "";
        const code = [];
        index += 1;
        while (index < lines.length && !/^```\s*$/.test(lines[index])) {
          code.push(lines[index]);
          index += 1;
        }
        push("CODE", { language, code: code.join("\n") });
        continue;
      }

      const heading = line.match(/^(#{1,6})\s+(.*)$/);
      if (heading) {
        flush();
        push("HEADING", { level: heading[1].length, text: heading[2].trim() });
        continue;
      }

      if (/^>\s?/.test(line)) {
        flush();
        push("QUOTE", { text: line.replace(/^>\s?/, ""), author: "" });
        continue;
      }

      const image = line.match(/^\s*!\[([^\]]*)\]\(([^)\s]+)\)\s*$/);
      if (image) {
        flush();
        push("IMAGE", { caption: image[1], url: image[2] });
        continue;
      }

      if (!line.trim()) {
        flush();
        continue;
      }
      paragraph.push(line.trim());
    }
    flush();

    if (!blocks.length) {
      push("PARAGRAPH", { text: "Sin contenido." });
    }
    return blocks;
  }

  async function generateStatic() {
    if (!currentId || (mode !== "draft" && mode !== "post")) return;

    const data = readForm();
    const slug = data.slug;
    if (!slug) {
      setStatus("El borrador necesita un slug antes de generar el HTML.", "error");
      return;
    }

    const payload = {
      page_id: `devblog-${slug}`,
      document_id: currentId,
      slug,
      content_type: "DEV_BLOG",
      engine_hint: "astro",
      frozen_template: { engine: "astro" },
      metadata_values: {
        title: data.title,
        tags: data.tags,
        source: "DevBlog CMS",
      },
      canvas_blocks: markdownToBlocks(data.content),
      async_mode: false,
    };

    try {
      generateStaticBtn.disabled = true;
      setStatus("Generando HTML estático…", "info");
      const response = await fetch(`${STATIC_GENERATOR_BASE_URL}/api/v1/pages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(result.detail || `El generador respondió ${response.status}`);
      }
      showStaticResult(result);
      setStatus(
        `HTML generado con ${result.engine || "el motor"} y checksum ${String(
          result.checksum_sha256 || ""
        ).slice(0, 12)}…`,
        "ok"
      );
    } catch (error) {
      console.error(error);
      setStatus(`No se pudo generar el HTML: ${error.message}`, "error");
    } finally {
      if (mode === "draft" || mode === "post") generateStaticBtn.disabled = false;
    }
  }

  // ---------------------------------------------------------------- acciones
  function newDraft() {
    currentId = null;
    clearForm();
    metrics.hidden = true;
    metrics.replaceChildren();
    setMode("new");
    setStatus("Nuevo borrador: escribe el título y el contenido, después guárdalo.", "info");
    titleInput.focus();
  }

  async function saveDraft(event) {
    event.preventDefault();
    if (mode !== "new" && mode !== "draft") return;

    const data = readForm();
    if (data.title.length < 5) {
      setStatus("El título debe tener al menos 5 caracteres.", "error");
      return;
    }
    if (!data.content.trim()) {
      setStatus("El contenido no puede estar vacío.", "error");
      return;
    }

    try {
      saveBtn.disabled = true;
      if (mode === "new") {
        const created = await adminApi.createDraft(token, data);
        currentId = created.post_id;
        slugInput.value = created.slug;
        window.DevBlogEditorPro?.saved(created.post_id);
        setMode("draft");
        setStatus(`Borrador creado: ${created.slug}`, "ok");
      } else {
        const updated = await adminApi.updateDraft(token, currentId, data);
        slugInput.value = updated.slug;
        window.DevBlogEditorPro?.saved(currentId);
        setStatus(`Borrador actualizado: ${updated.slug}`, "ok");
      }
      await loadDrafts({ reset: true });
    } catch (error) {
      handleError(error);
    } finally {
      if (mode === "new" || mode === "draft") saveBtn.disabled = false;
    }
  }

  async function publishCurrent() {
    if (mode !== "draft" || !currentId) return;
    if (!window.confirm("¿Publicar este borrador? Después ya no podrá editarse.")) return;

    try {
      publishBtn.disabled = true;
      const result = await adminApi.publishDraft(token, currentId);
      setStatus(`Publicado en ${result.url}`, "ok");
      currentId = null;
      clearForm();
      metrics.hidden = true;
      setMode("idle");
      await refreshLists();
    } catch (error) {
      handleError(error);
    } finally {
      if (mode === "draft") publishBtn.disabled = false;
    }
  }

  async function deleteCurrentDraft() {
    if (mode !== "draft" || !currentId) return;
    if (!window.confirm("¿Eliminar este borrador? No se puede deshacer.")) return;

    try {
      deleteDraftBtn.disabled = true;
      await adminApi.deleteDraft(token, currentId);
      currentId = null;
      clearForm();
      setMode("idle");
      setStatus("Borrador eliminado.", "ok");
      await loadDrafts({ reset: true });
    } catch (error) {
      handleError(error);
    } finally {
      if (mode === "draft") deleteDraftBtn.disabled = false;
    }
  }

  async function deleteCurrentPost() {
    if (mode !== "post" || !currentId) return;
    if (!window.confirm("¿Eliminar esta publicación y sus vistas? Es irreversible.")) return;

    try {
      deletePostBtn.disabled = true;
      await adminApi.deletePost(token, currentId);
      currentId = null;
      clearForm();
      metrics.hidden = true;
      setMode("idle");
      setStatus("Publicación eliminada.", "ok");
      await refreshLists();
    } catch (error) {
      handleError(error);
    } finally {
      if (mode === "post") deletePostBtn.disabled = false;
    }
  }

  // ---------------------------------------------------------------- conexión
  async function connect(value) {
    token = String(value || "").trim();
    if (!token) {
      setAuthStatus("Escribe el token de la consola.", "error");
      return;
    }

    setAuthStatus("Comprobando token…", "info");
    try {
      await adminApi.listDrafts(token, { limit: 1 });
      sessionStorage.setItem("devblog_console_token", token);
      authPanel.hidden = true;
      workspace.hidden = false;
      logoutBtn.hidden = false;
      setMode("idle");
      clearForm();
      await refreshLists();
      await loadSites();
      activateTab("dashboard");
      loadLanding();
      loadAds();
      setStatus("Conectado. Revisa el dashboard, administra sitios o edita una landing.", "ok");
    } catch (error) {
      sessionStorage.removeItem("devblog_console_token");
      token = "";
      authPanel.hidden = false;
      workspace.hidden = true;
      logoutBtn.hidden = true;
      handleError(error, authStatus);
    }
  }

  function logout() {
    sessionStorage.removeItem("devblog_console_token");
    token = "";
    currentId = null;
    setMode("idle");
    clearForm();
    draftsList.replaceChildren();
    postsList.replaceChildren();
    metrics.hidden = true;
    metrics.replaceChildren();
    landingContent = null;
    ads = [];
    resetAdForm();
    renderCollection("technologies", []);
    renderCollection("projects", []);
    renderCollection("certifications", []);
    const kpis = $("#metrics-kpis");
    if (kpis) kpis.replaceChildren();
    const routes = $("#metrics-routes");
    if (routes) routes.replaceChildren(emptyTableRow("Sin datos."));
    const serie = $("#metrics-serie");
    if (serie) serie.replaceChildren(emptyParagraph("Sin datos."));
    activateTab("blog");
    authPanel.hidden = false;
    workspace.hidden = true;
    logoutBtn.hidden = true;
    tokenInput.value = "";
    setAuthStatus("Sesión cerrada.", "info");
  }

  // ------------------------------------------------------------- escuchas
  authForm.addEventListener("submit", (event) => {
    event.preventDefault();
    connect(tokenInput.value);
  });
  logoutBtn.addEventListener("click", logout);

  $("#new-draft").addEventListener("click", newDraft);
  $("#refresh-drafts").addEventListener("click", () => loadDrafts({ reset: true }));
  $("#refresh-posts").addEventListener("click", () => loadPosts({ reset: true }));
  moreDraftsBtn.addEventListener("click", () => loadDrafts({ reset: false }));
  morePostsBtn.addEventListener("click", () => loadPosts({ reset: false }));

  $("#draft-form").addEventListener("submit", saveDraft);
  publishBtn.addEventListener("click", publishCurrent);
  deleteDraftBtn.addEventListener("click", deleteCurrentDraft);
  deletePostBtn.addEventListener("click", deleteCurrentPost);
  generateStaticBtn.addEventListener("click", generateStatic);

  previewBtn.addEventListener("click", () => {
    previewVisible = !previewVisible;
    preview.hidden = !previewVisible;
    previewBtn.textContent = previewVisible ? "Ocultar vista previa" : "Vista previa";
    if (previewVisible) {
      preview.innerHTML = window.DevBlogMarkdown.render(contentInput.value);
    }
  });

  contentInput.addEventListener("input", () => {
    if (previewVisible) {
      preview.innerHTML = window.DevBlogMarkdown.render(contentInput.value);
    }
  });

  // ================================================================
  //  Pestañas: Blog · Landing y publicidad · Métricas
  // ================================================================
  const TAB_PANELS = {
    dashboard: $("#panel-dashboard"),
    sites: $("#panel-sites"),
    blog: $("#panel-blog"),
    landing: $("#panel-landing"),
    metrics: $("#panel-metrics"),
  };

  function activateTab(name) {
    const target = TAB_PANELS[name] ? name : "blog";
    $$(".admin__tab").forEach((tab) => {
      const active = tab.dataset.tab === target;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
    });
    Object.entries(TAB_PANELS).forEach(([key, panel]) => {
      if (panel) panel.hidden = key !== target;
    });
    if (target === "metrics") loadMetrics();
    if (target === "landing") {
      if (!landingContent) loadLanding();
      if (!ads.length) loadAds();
    }
    if (target === "sites") {
      if (!sites.length) loadSites();
      else renderSites();
    }
    document.dispatchEvent(new CustomEvent("devblog:tab", { detail: { name: target } }));
  }

  // ================================================================
  //  Landing editable (borrador + publicación)
  // ================================================================
  const landingForm = $("#landing-form");
  const landingStatus = $("#landing-status");
  const landingMeta = $("#landing-meta");
  const landingSite = $("#landing-site");
  const saveLandingBtn = $("#save-landing");
  const publishLandingBtn = $("#publish-landing");
  const refreshLandingBtn = $("#refresh-landing");
  const landingFields = $$("[data-landing-field]");
  const sitesGrid = $("#sites-grid");
  const sitesStatus = $("#sites-status");

  let landingContent = null;
  let sites = [];
  let currentSiteId = "portfolio";
  let editingSiteId = null;

  const COLLECTION_CONFIG = {
    technologies: {
      container: "#tech-editor",
      fields: [
        { key: "name", label: "Nombre", maxLength: 40, required: true },
        { key: "icon", label: "Icono (máx. 8)", maxLength: 8 },
        { key: "color", label: "Color CSS", maxLength: 40, default: "var(--green)" },
      ],
    },
    projects: {
      container: "#project-editor",
      fields: [
        { key: "title", label: "Título", maxLength: 120, required: true },
        { key: "badge", label: "Etiqueta", maxLength: 40 },
        { key: "description", label: "Descripción", maxLength: 400 },
        { key: "url", label: "Enlace", maxLength: 500 },
        { key: "link_label", label: "Texto del enlace", maxLength: 60 },
        {
          key: "art",
          label: "Ilustración",
          type: "select",
          options: [
            ["dots", "Puntos"],
            ["green", "Brillo verde"],
            ["purple", "Brillo morado"],
          ],
          default: "dots",
        },
      ],
    },
    certifications: {
      container: "#cert-editor",
      fields: [
        { key: "issuer", label: "Emisor", maxLength: 120 },
        { key: "title", label: "Título", maxLength: 160, required: true },
        { key: "url", label: "Enlace", maxLength: 500 },
        { key: "tag", label: "Etiqueta", maxLength: 40 },
        { key: "color", label: "Color CSS", maxLength: 40, default: "var(--green)" },
      ],
    },
    videos: {
      container: "#video-editor",
      fields: [
        { key: "title", label: "Título", maxLength: 120, required: true },
        { key: "description", label: "Descripción", maxLength: 400 },
        { key: "url", label: "URL del video (MP4, WebM, YouTube o Vimeo)", maxLength: 1000, required: true },
        { key: "poster", label: "Póster (URL)", maxLength: 1000 },
        { key: "captions_url", label: "Subtítulos (VTT)", maxLength: 1000 },
        { key: "cta_label", label: "Texto del CTA", maxLength: 60 },
        { key: "cta_url", label: "Enlace del CTA", maxLength: 500 },
        {
          key: "aspect",
          label: "Aspecto",
          type: "select",
          options: [["16:9", "16:9"], ["9:16", "9:16"], ["1:1", "1:1"]],
          default: "16:9",
        },
      ],
    },
  };

  function getPath(source, path) {
    return String(path || "")
      .split(".")
      .reduce((value, key) => (value == null ? undefined : value[key]), source);
  }

  function setPath(target, path, value) {
    const keys = String(path || "").split(".");
    let node = target;
    keys.forEach((key, index) => {
      if (index === keys.length - 1) {
        node[key] = value;
        return;
      }
      if (typeof node[key] !== "object" || node[key] === null) node[key] = {};
      node = node[key];
    });
  }

  function cloneJson(value) {
    return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
  }

  function emptyParagraph(text) {
    const p = document.createElement("p");
    p.className = "admin__empty";
    p.textContent = text;
    return p;
  }

  function emptyTableRow(text) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 2;
    td.textContent = text;
    tr.append(td);
    return tr;
  }

  function collectionRow(collection, item = {}) {
    const config = COLLECTION_CONFIG[collection];
    const row = document.createElement("div");
    row.className = "admin__collection-item";

    for (const field of config.fields) {
      const label = document.createElement("label");
      label.textContent = field.label;

      let control;
      if (field.type === "select") {
        control = document.createElement("select");
        for (const [value, text] of field.options) {
          const option = document.createElement("option");
          option.value = value;
          option.textContent = text;
          control.append(option);
        }
      } else {
        control = document.createElement("input");
        control.type = "text";
        if (field.maxLength) control.maxLength = field.maxLength;
        if (field.required) control.required = true;
      }
      control.dataset.key = field.key;
      control.value = item[field.key] ?? field.default ?? "";
      label.append(control);
      row.append(label);
    }

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "btn btn--ghost danger admin__remove";
    remove.textContent = "Quitar";
    remove.addEventListener("click", () => {
      row.remove();
      const container = row.parentElement;
      if (container && !container.querySelector(".admin__collection-item")) {
        renderCollection(collection, []);
      }
    });
    row.append(remove);
    return row;
  }

  function renderCollection(collection, items = []) {
    const config = COLLECTION_CONFIG[collection];
    const container = $(config.container);
    if (!container) return;
    container.replaceChildren();
    if (!Array.isArray(items) || !items.length) {
      container.append(emptyParagraph("Sin elementos. Usa + para añadir."));
      return;
    }
    for (const item of items) container.append(collectionRow(collection, item));
  }

  function addCollectionRow(collection) {
    const config = COLLECTION_CONFIG[collection];
    const container = $(config.container);
    if (!container) return;
    const empty = container.querySelector(".admin__collection-empty");
    if (empty) empty.remove();
    const row = collectionRow(collection, {});
    container.append(row);
    const first = row.querySelector("input, select");
    if (first) first.focus();
  }

  function readCollection(collection) {
    const config = COLLECTION_CONFIG[collection];
    const container = $(config.container);
    if (!container) return [];
    const primary = config.fields[0].key;
    return $$(".admin__collection-item", container)
      .map((row) => {
        const item = {};
        for (const field of config.fields) {
          const control = row.querySelector(`[data-key="${field.key}"]`);
          item[field.key] = control ? String(control.value || "").trim() : "";
        }
        return item;
      })
      .filter((item) => item[primary]);
  }

  function fillLanding(content) {
    for (const input of landingFields) {
      const value = getPath(content, input.dataset.landingField);
      input.value = value === undefined || value === null ? "" : String(value);
    }
    renderCollection("technologies", content.technologies || []);
    renderCollection("projects", content.projects || []);
    renderCollection("certifications", content.certifications || []);
    renderCollection("videos", content.videos || []);
  }

  function readLanding() {
    const content = cloneJson(landingContent) || {};
    for (const input of landingFields) {
      setPath(content, input.dataset.landingField, input.value.trim());
    }
    content.technologies = readCollection("technologies");
    content.projects = readCollection("projects");
    content.certifications = readCollection("certifications");
    content.videos = readCollection("videos");
    return content;
  }

  function updateLandingMeta(data) {
    if (!landingMeta) return;
    const updated = formatDate(data.updated_at);
    const published = data.published_at ? formatDate(data.published_at) : "nunca";
    landingMeta.textContent = `Borrador: ${updated} · Publicado: ${published} · ${
      data.has_published ? "hay versión pública" : "sin publicar"
    }`;
  }

  // ------------------------------------------------------------- sitios
  const SITE_PRESETS = {
    "tech-terminal": { accent: "#3df0a8", bg: "#050807", surface: "#0b1110", text: "#eef5f1", heading: "Manrope", body: "Manrope", radius: 0 },
    "editorial-minimal": { accent: "#3de4ff", bg: "#050807", surface: "#0b1110", text: "#eef5f1", heading: "Manrope", body: "Manrope", radius: 8 },
    "modern-magazine": { accent: "#b48cff", bg: "#050807", surface: "#0b1110", text: "#eef5f1", heading: "Manrope", body: "Georgia", radius: 12 },
    "clean-docs": { accent: "#5b8cff", bg: "#050807", surface: "#0b1110", text: "#eef5f1", heading: "Inter", body: "Inter", radius: 6 },
  };

  function siteKindLabel(kind) {
    return {
      portfolio: "Portafolio",
      project: "Proyecto",
      blog: "Blog",
      client: "Cliente",
    }[kind] || kind;
  }

  function siteUrl(site) {
    const domain = String(site?.domain || "").trim();
    if (!domain) return "";
    return /^https?:\/\//i.test(domain) ? domain : `https://${domain}`;
  }

  function populateSiteSelect() {
    if (!landingSite) return;
    landingSite.replaceChildren();
    for (const site of sites) {
      const option = document.createElement("option");
      option.value = site.site_id;
      option.textContent = `${site.name} · ${siteKindLabel(site.kind)}`;
      landingSite.append(option);
    }
    if (!sites.some((site) => site.site_id === currentSiteId)) {
      currentSiteId = sites[0]?.site_id || "portfolio";
    }
    landingSite.value = currentSiteId;
  }

  function renderSites() {
    if (!sitesGrid) return;
    sitesGrid.replaceChildren();
    if (!sites.length) {
      sitesGrid.append(emptyParagraph("No hay sitios. Crea el primero con «+ Nuevo sitio»."));
      return;
    }

    for (const site of sites) {
      const card = document.createElement("article");
      card.className = "site-card";
      card.style.setProperty("--site-accent", site.theme?.accent || "var(--green)");

      const head = document.createElement("div");
      head.className = "site-card__head";
      const titleWrap = document.createElement("div");
      const h3 = document.createElement("h3");
      h3.textContent = site.name;
      const id = document.createElement("span");
      id.className = "site-card__id";
      id.textContent = `/${site.site_id}`;
      titleWrap.append(h3, id);
      const status = document.createElement("span");
      status.className = `site-badge site-badge--${site.status}`;
      status.textContent = site.status === "active" ? "Activo" : site.status === "draft" ? "Borrador" : "Archivado";
      head.append(titleWrap, status);

      const badges = document.createElement("div");
      badges.className = "site-card__badges";
      const kind = document.createElement("span");
      kind.className = `site-badge site-badge--${site.kind}`;
      kind.textContent = siteKindLabel(site.kind);
      const preset = document.createElement("span");
      preset.className = "site-badge";
      preset.textContent = site.theme?.preset || "tech-terminal";
      badges.append(kind, preset);

      const domain = document.createElement("p");
      domain.className = "site-card__domain";
      domain.textContent = site.domain || "Sin dominio configurado";

      const description = document.createElement("p");
      description.className = "site-card__description";
      description.textContent = site.description || "Sin descripción.";

      const theme = document.createElement("div");
      theme.className = "site-card__theme";
      for (const color of [site.theme?.accent, site.theme?.background, site.theme?.surface, site.theme?.text]) {
        if (!color) continue;
        const dot = document.createElement("i");
        dot.style.background = color;
        theme.append(dot);
      }
      const themeText = document.createElement("span");
      themeText.textContent = `${site.theme?.heading_font || "Manrope"} / ${site.theme?.body_font || "Manrope"}`;
      theme.append(themeText);

      const actions = document.createElement("div");
      actions.className = "site-card__actions";

      const editLanding = document.createElement("button");
      editLanding.type = "button";
      editLanding.className = "btn btn--solid";
      editLanding.textContent = "Editar landing";
      editLanding.addEventListener("click", () => {
        currentSiteId = site.site_id;
        populateSiteSelect();
        landingContent = null;
        activateTab("landing");
      });

      const open = document.createElement("a");
      open.className = "btn btn--ghost";
      open.textContent = "Abrir ↗";
      const url = siteUrl(site);
      if (url) {
        open.href = url;
        open.target = "_blank";
        open.rel = "noopener noreferrer";
      } else {
        open.setAttribute("aria-disabled", "true");
        open.style.pointerEvents = "none";
        open.style.opacity = "0.45";
      }

      const edit = document.createElement("button");
      edit.type = "button";
      edit.className = "btn btn--ghost";
      edit.textContent = "Editar sitio";
      edit.addEventListener("click", () => openSiteEditor(site));

      actions.append(editLanding, open, edit);

      if (!["portfolio", "devblog"].includes(site.site_id)) {
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "btn btn--ghost danger";
        remove.textContent = "Eliminar";
        remove.addEventListener("click", async () => {
          if (!window.confirm(`¿Eliminar el sitio "${site.name}" y su landing?`)) return;
          try {
            await adminApi.deleteSite(token, site.site_id);
            if (currentSiteId === site.site_id) {
              currentSiteId = "portfolio";
              landingContent = null;
            }
            setStatus(`Sitio "${site.name}" eliminado.`, "ok", sitesStatus);
            await loadSites();
          } catch (error) {
            handleError(error, sitesStatus);
          }
        });
        actions.append(remove);
      }

      card.append(head, badges, domain, description, theme, actions);
      sitesGrid.append(card);
    }
  }

  async function loadSites() {
    if (!token) return;
    try {
      setStatus("Cargando sitios…", "info", sitesStatus);
      sites = await adminApi.listSites(token);
      populateSiteSelect();
      renderSites();
      setStatus(`${sites.length} sitios administrables.`, "ok", sitesStatus);
    } catch (error) {
      handleError(error, sitesStatus);
    }
  }

  function applySitePreset() {
    const preset = $("#site-editor-preset")?.value || "tech-terminal";
    const value = SITE_PRESETS[preset] || SITE_PRESETS["tech-terminal"];
    $("#site-editor-accent").value = value.accent;
    $("#site-editor-bg").value = value.bg;
    $("#site-editor-surface").value = value.surface;
    $("#site-editor-text").value = value.text;
    $("#site-editor-heading-font").value = value.heading;
    $("#site-editor-body-font").value = value.body;
    $("#site-editor-radius").value = String(value.radius);
  }

  function openSiteEditor(site = null) {
    editingSiteId = site?.site_id || null;
    $("#site-editor-title").textContent = site ? "Editar sitio" : "Nuevo sitio";
    $("#site-editor-id").value = site?.site_id || "";
    $("#site-editor-id").disabled = Boolean(site);
    $("#site-editor-name").value = site?.name || "";
    $("#site-editor-kind").value = site?.kind || "client";
    $("#site-editor-status").value = site?.status || "active";
    $("#site-editor-domain").value = site?.domain || "";
    $("#site-editor-description").value = site?.description || "";
    const theme = site?.theme || {};
    $("#site-editor-preset").value = theme.preset || "tech-terminal";
    $("#site-editor-accent").value = theme.accent || "#3df0a8";
    $("#site-editor-bg").value = theme.background || "#050807";
    $("#site-editor-surface").value = theme.surface || "#0b1110";
    $("#site-editor-text").value = theme.text || "#eef5f1";
    $("#site-editor-heading-font").value = theme.heading_font || "Manrope";
    $("#site-editor-body-font").value = theme.body_font || "Manrope";
    $("#site-editor-radius").value = String(theme.radius ?? 0);
    const modal = $("#site-editor-modal");
    modal.hidden = false;
    setTimeout(() => $("#site-editor-name")?.focus(), 40);
  }

  function closeSiteEditor() {
    const modal = $("#site-editor-modal");
    if (modal) modal.hidden = true;
    editingSiteId = null;
  }

  function readSiteForm() {
    return {
      name: $("#site-editor-name").value.trim(),
      kind: $("#site-editor-kind").value,
      domain: $("#site-editor-domain").value.trim(),
      description: $("#site-editor-description").value.trim(),
      status: $("#site-editor-status").value,
      theme: {
        preset: $("#site-editor-preset").value,
        accent: $("#site-editor-accent").value,
        background: $("#site-editor-bg").value,
        surface: $("#site-editor-surface").value,
        text: $("#site-editor-text").value,
        muted: "#8c9c95",
        heading_font: $("#site-editor-heading-font").value.trim() || "Manrope",
        body_font: $("#site-editor-body-font").value.trim() || "Manrope",
        radius: Number($("#site-editor-radius").value) || 0,
      },
    };
  }

  async function submitSiteEditor(event) {
    event.preventDefault();
    if (!token) return;
    const payload = readSiteForm();
    if (!payload.name) {
      setStatus("El sitio necesita un nombre.", "error", sitesStatus);
      return;
    }
    try {
      if (editingSiteId) {
        await adminApi.updateSite(token, editingSiteId, payload);
        setStatus(`Sitio "${payload.name}" actualizado.`, "ok", sitesStatus);
      } else {
        const siteId = $("#site-editor-id").value.trim();
        if (!siteId) {
          setStatus("El slug del sitio es obligatorio.", "error", sitesStatus);
          return;
        }
        const created = await adminApi.createSite(token, { site_id: siteId, ...payload });
        currentSiteId = created.site_id;
        landingContent = null;
        setStatus(`Sitio "${payload.name}" creado con su landing base.`, "ok", sitesStatus);
      }
      closeSiteEditor();
      await loadSites();
    } catch (error) {
      handleError(error, sitesStatus);
    }
  }

  // ------------------------------------------------------------- landing
  async function loadLanding() {
    if (!token) return;
    try {
      setStatus(`Cargando landing de ${currentSiteId}…`, "info", landingStatus);
      const data = await adminApi.getSiteLandingDraft(token, currentSiteId);
      landingContent = data.content || {};
      fillLanding(landingContent);
      updateLandingMeta(data);
      setStatus(`Borrador de ${currentSiteId} cargado.`, "ok", landingStatus);
    } catch (error) {
      handleError(error, landingStatus);
    }
  }

  async function saveLanding() {
    if (!token) return;
    try {
      saveLandingBtn.disabled = true;
      setStatus("Guardando borrador…", "info", landingStatus);
      const data = await adminApi.saveSiteLandingDraft(token, currentSiteId, readLanding());
      landingContent = data.content || {};
      updateLandingMeta(data);
      setStatus(
        `Borrador de ${currentSiteId} guardado. El sitio público no cambia hasta publicar.`,
        "ok",
        landingStatus
      );
    } catch (error) {
      handleError(error, landingStatus);
    } finally {
      saveLandingBtn.disabled = false;
    }
  }

  async function publishLanding() {
    if (!token) return;
    if (!window.confirm(`¿Guardar y publicar la landing de ${currentSiteId}?`)) return;
    try {
      publishLandingBtn.disabled = true;
      setStatus("Guardando y publicando la landing…", "info", landingStatus);
      await adminApi.saveSiteLandingDraft(token, currentSiteId, readLanding());
      const data = await adminApi.publishSiteLanding(token, currentSiteId);
      landingContent = data.content || landingContent;
      fillLanding(landingContent);
      updateLandingMeta(data);
      setStatus(`Landing de ${currentSiteId} publicada.`, "ok", landingStatus);
    } catch (error) {
      handleError(error, landingStatus);
    } finally {
      publishLandingBtn.disabled = false;
    }
  }

  // ================================================================
  //  Publicidad (CRUD + vista previa del diseño)
  // ================================================================
  const adsList = $("#ads-list");
  const adsStatus = $("#ads-status");
  const adForm = $("#ad-form");
  const adFields = $("#ad-fields");
  const adIdInput = $("#ad-id");
  const adTitle = $("#ad-title");
  const adSubtitle = $("#ad-subtitle");
  const adBody = $("#ad-body");
  const adCtaLabel = $("#ad-cta-label");
  const adCtaUrl = $("#ad-cta-url");
  const adImage = $("#ad-image");
  const adLayout = $("#ad-layout");
  const adBg = $("#ad-bg");
  const adText = $("#ad-text");
  const adAccent = $("#ad-accent");
  const adActive = $("#ad-active");
  const saveAdBtn = $("#save-ad");
  const deleteAdBtn = $("#delete-ad");
  const newAdBtn = $("#new-ad");
  const refreshAdsBtn = $("#refresh-ads");
  const adPreview = $("#ad-preview");
  const adPreviewMedia = $("#ad-preview-media");
  const adPreviewImage = $("#ad-preview-image");
  const adPreviewSubtitle = $("#ad-preview-subtitle");
  const adPreviewTitle = $("#ad-preview-title");
  const adPreviewText = $("#ad-preview-text");
  const adPreviewCta = $("#ad-preview-cta");

  let ads = [];
  let currentAdId = null;

  function safeUrl(value, { image = false } = {}) {
    const raw = String(value || "").trim();
    if (!raw) return "";
    if (image && /^data:image\//i.test(raw)) return raw;
    if (/^(javascript|vbscript|data):/i.test(raw)) return "#";
    return raw;
  }

  function renderAds() {
    adsList.replaceChildren();
    if (!ads.length) {
      adsList.append(emptyItem("Sin publicidades."));
      return;
    }
    for (const ad of ads) {
      const li = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "admin__item";
      button.dataset.adId = ad.ad_id;

      const title = document.createElement("strong");
      title.textContent = ad.title;
      const meta = document.createElement("small");
      meta.textContent = `${ad.layout} · ${ad.active ? "activa" : "inactiva"}`;

      button.append(title, meta);
      button.addEventListener("click", () => openAd(ad.ad_id));
      li.append(button);
      adsList.append(li);
    }
  }

  function resetAdForm() {
    currentAdId = null;
    if (adForm) adForm.reset();
    if (adIdInput) adIdInput.value = "";
    if (adFields) adFields.disabled = true;
    if (saveAdBtn) saveAdBtn.disabled = true;
    if (deleteAdBtn) deleteAdBtn.disabled = true;
    updateAdPreview();
  }

  function openAd(adId) {
    const ad = ads.find((item) => item.ad_id === adId);
    if (!ad) return;
    currentAdId = ad.ad_id;
    adIdInput.value = ad.ad_id;
    adTitle.value = ad.title || "";
    adSubtitle.value = ad.subtitle || "";
    adBody.value = ad.body || "";
    adCtaLabel.value = ad.cta_label || "";
    adCtaUrl.value = ad.cta_url || "";
    adImage.value = ad.image_url || "";
    adLayout.value = ad.layout || "banner";
    const theme = ad.theme || {};
    adBg.value = theme.background || "#0b1110";
    adText.value = theme.text || "#eef5f1";
    adAccent.value = theme.accent || "#3df0a8";
    adActive.checked = ad.active !== false;

    adFields.disabled = false;
    saveAdBtn.disabled = false;
    deleteAdBtn.disabled = false;
    updateAdPreview();
    setStatus(`Editando: ${ad.title}`, "info", adsStatus);
  }

  function newAd() {
    resetAdForm();
    adFields.disabled = false;
    saveAdBtn.disabled = false;
    deleteAdBtn.disabled = true;
    updateAdPreview();
    setStatus("Nueva publicidad: completa el diseño y guarda.", "info", adsStatus);
    adTitle.focus();
  }

  function readAdForm() {
    return {
      title: adTitle.value.trim(),
      subtitle: adSubtitle.value.trim(),
      body: adBody.value.trim(),
      cta_label: adCtaLabel.value.trim(),
      cta_url: adCtaUrl.value.trim(),
      image_url: adImage.value.trim(),
      layout: adLayout.value,
      theme: {
        background: adBg.value,
        text: adText.value,
        accent: adAccent.value,
      },
      active: adActive.checked,
    };
  }

  function updateAdPreview() {
    if (!adPreview) return;
    const data = readAdForm();
    const image = safeUrl(data.image_url, { image: true });
    adPreview.className = `ad admin__ad-preview ad--${data.layout || "banner"}`;
    adPreview.classList.toggle("ad--con-media", Boolean(image) && image !== "#");
    adPreview.style.setProperty("--ad-bg", data.theme.background || "#0b1110");
    adPreview.style.setProperty("--ad-text", data.theme.text || "#eef5f1");
    adPreview.style.setProperty("--ad-accent", data.theme.accent || "#3df0a8");

    adPreviewTitle.textContent = data.title || "Título del anuncio";
    adPreviewSubtitle.textContent = data.subtitle;
    adPreviewSubtitle.hidden = !data.subtitle;
    adPreviewText.textContent = data.body;
    adPreviewText.hidden = !data.body;

    adPreviewCta.textContent = data.cta_label;
    adPreviewCta.hidden = !data.cta_label;

    if (image) {
      adPreviewImage.src = image;
      adPreviewImage.alt = data.title || "Publicidad";
    } else {
      adPreviewImage.removeAttribute("src");
      adPreviewImage.alt = "";
    }
    adPreviewMedia.hidden = !image || image === "#";
  }

  async function loadAds() {
    if (!token) return;
    try {
      setStatus("Cargando publicidades…", "info", adsStatus);
      ads = await adminApi.listAds(token);
      renderAds();
      if (!ads.length) {
        resetAdForm();
        setStatus("Sin publicidades. Crea una nueva.", "info", adsStatus);
        return;
      }
      if (!currentAdId || !ads.some((ad) => ad.ad_id === currentAdId)) {
        openAd(ads[0].ad_id);
      } else {
        setStatus(`${ads.length} publicidad(es).`, "ok", adsStatus);
      }
    } catch (error) {
      handleError(error, adsStatus);
    }
  }

  async function saveAd(event) {
    event.preventDefault();
    if (!token) return;
    const data = readAdForm();
    if (data.title.length < 3) {
      setStatus("El título de la publicidad debe tener al menos 3 caracteres.", "error", adsStatus);
      return;
    }
    try {
      saveAdBtn.disabled = true;
      const wasNew = !currentAdId;
      const saved = currentAdId
        ? await adminApi.updateAd(token, currentAdId, data)
        : await adminApi.createAd(token, data);
      await loadAds();
      openAd(saved.ad_id);
      setStatus(wasNew ? "Publicidad creada." : "Publicidad actualizada.", "ok", adsStatus);
    } catch (error) {
      handleError(error, adsStatus);
    } finally {
      saveAdBtn.disabled = adFields.disabled;
    }
  }

  async function deleteCurrentAd() {
    if (!currentAdId) return;
    if (!window.confirm("¿Eliminar esta publicidad? No se puede deshacer.")) return;
    try {
      deleteAdBtn.disabled = true;
      await adminApi.deleteAd(token, currentAdId);
      currentAdId = null;
      resetAdForm();
      await loadAds();
      setStatus("Publicidad eliminada.", "ok", adsStatus);
    } catch (error) {
      handleError(error, adsStatus);
    } finally {
      if (currentAdId) deleteAdBtn.disabled = false;
    }
  }

  // ================================================================
  //  Métricas del sitio (resumen consultado por el backend)
  // ================================================================
  const metricsStatus = $("#metrics-status");
  const metricsKpis = $("#metrics-kpis");
  const metricsRoutes = $("#metrics-routes");
  const metricsSerie = $("#metrics-serie");
  const metricsDays = $("#metrics-days");
  const metricsGrano = $("#metrics-grano");
  const refreshMetricsBtn = $("#refresh-metrics");

  let metricsLoading = false;

  const shortDate = new Intl.DateTimeFormat("es-MX", { day: "2-digit", month: "short" });
  const shortTime = new Intl.DateTimeFormat("es-MX", { hour: "2-digit", minute: "2-digit" });

  function seriesLabel(value, grano) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return grano === "HORA" ? shortTime.format(date) : shortDate.format(date);
  }

  function renderMetrics(data) {
    metricsKpis.replaceChildren(
      metricBox("Pageviews", String(data.pageviews ?? 0)),
      metricBox("Sesiones", String(data.sesiones ?? 0)),
      metricBox("Visitantes únicos", String(data.visitantes_unicos ?? 0)),
      metricBox("Sitio", data.sitio || "—"),
      metricBox("Periodo", `${metricsDays.value} días`),
      metricBox("Grano", data.grano || metricsGrano.value)
    );

    if (data.disponible) {
      setStatus(
        `Datos de ${formatDate(data.desde)} a ${formatDate(data.hasta)}`,
        "ok",
        metricsStatus
      );
    } else {
      setStatus(
        `Métricas no disponibles: ${data.error || "el servicio no respondió"}`,
        "error",
        metricsStatus
      );
    }

    const routes = Array.isArray(data.por_ruta) ? data.por_ruta : [];
    metricsRoutes.replaceChildren();
    if (!routes.length) {
      metricsRoutes.append(emptyTableRow("Sin tráfico registrado en el periodo."));
    } else {
      for (const row of routes.slice(0, 20)) {
        const tr = document.createElement("tr");
        const route = document.createElement("td");
        route.textContent = row.clave || "/";
        const value = document.createElement("td");
        value.textContent = String(row.valor ?? 0);
        tr.append(route, value);
        metricsRoutes.append(tr);
      }
    }

    const serie = Array.isArray(data.serie) ? data.serie : [];
    metricsSerie.replaceChildren();
    if (!serie.length) {
      metricsSerie.append(emptyParagraph("Sin datos en el periodo."));
    } else {
      const points = serie.slice(-60);
      const max = Math.max(...points.map((point) => Number(point.pageviews) || 0), 1);
      for (const point of points) {
        const row = document.createElement("div");
        row.className = "admin__bar-row";

        const label = document.createElement("span");
        label.textContent = seriesLabel(point.cubo, data.grano || metricsGrano.value);
        label.title = formatDate(point.cubo);

        const bar = document.createElement("span");
        bar.className = "admin__bar";
        const fill = document.createElement("i");
        const pv = Number(point.pageviews) || 0;
        fill.style.width = `${Math.max(2, (pv / max) * 100)}%`;
        bar.append(fill);

        const value = document.createElement("span");
        value.textContent = String(pv);
        value.title = `${pv} pageviews · ${Number(point.sesiones) || 0} sesiones`;

        row.append(label, bar, value);
        metricsSerie.append(row);
      }
    }
  }

  async function loadMetrics() {
    if (!token || metricsLoading) return;
    metricsLoading = true;
    refreshMetricsBtn.disabled = true;
    setStatus("Consultando métricas…", "info", metricsStatus);
    try {
      const data = await adminApi.getMetricsOverview(token, {
        days: Number(metricsDays.value),
        grano: metricsGrano.value,
      });
      renderMetrics(data);
    } catch (error) {
      handleError(error, metricsStatus);
    } finally {
      metricsLoading = false;
      refreshMetricsBtn.disabled = false;
    }
  }

  // ================================================================
  //  Escuchas de las nuevas secciones
  // ================================================================
  $$(".admin__tab").forEach((tab) => {
    tab.addEventListener("click", () => activateTab(tab.dataset.tab));
  });

  landingForm.addEventListener("submit", (event) => {
    event.preventDefault();
    saveLanding();
  });
  saveLandingBtn.addEventListener("click", saveLanding);
  publishLandingBtn.addEventListener("click", publishLanding);
  refreshLandingBtn.addEventListener("click", loadLanding);

  $("#add-tech").addEventListener("click", () => addCollectionRow("technologies"));
  $("#add-project").addEventListener("click", () => addCollectionRow("projects"));
  $("#add-cert").addEventListener("click", () => addCollectionRow("certifications"));
  $("#add-video").addEventListener("click", () => addCollectionRow("videos"));

  landingSite.addEventListener("change", () => {
    currentSiteId = landingSite.value || "portfolio";
    landingContent = null;
    loadLanding();
  });

  $("#new-site").addEventListener("click", () => openSiteEditor());
  $("#site-editor-cancel").addEventListener("click", closeSiteEditor);
  $("#site-editor-form").addEventListener("submit", submitSiteEditor);
  $("#site-editor-preset").addEventListener("change", applySitePreset);
  $("#site-editor-modal").addEventListener("click", (event) => {
    if (event.target === event.currentTarget) closeSiteEditor();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !$("#site-editor-modal").hidden) closeSiteEditor();
  });

  newAdBtn.addEventListener("click", newAd);
  refreshAdsBtn.addEventListener("click", loadAds);
  adForm.addEventListener("submit", saveAd);
  deleteAdBtn.addEventListener("click", deleteCurrentAd);
  adForm.addEventListener("input", updateAdPreview);
  adForm.addEventListener("change", updateAdPreview);

  refreshMetricsBtn.addEventListener("click", loadMetrics);
  metricsDays.addEventListener("change", loadMetrics);
  metricsGrano.addEventListener("change", loadMetrics);

  resetAdForm();

  // Al abrir la página: reconectar si ya hay token en esta pestaña.
  if (token) {
    tokenInput.value = token;
    connect(token);
  } else {
    setMode("idle");
  }
})();
