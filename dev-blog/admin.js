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
  if (metricsLink) metricsLink.href = `${metricsBase}/v1/query`;
  if (generatorLink) generatorLink.href = `${STATIC_GENERATOR_BASE_URL}/docs`;

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
  }

  function clearForm() {
    titleInput.value = "";
    slugInput.value = "";
    tagsInput.value = "";
    contentInput.value = "";
    preview.replaceChildren();
    staticResult.hidden = true;
    staticResult.replaceChildren();
  }

  function fillForm(data) {
    titleInput.value = data.title || "";
    slugInput.value = data.slug || "";
    tagsInput.value = Array.isArray(data.tags) ? data.tags.join(", ") : "";
    contentInput.value = data.content || "";
    preview.replaceChildren();
    staticResult.hidden = true;
    staticResult.replaceChildren();
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
        setMode("draft");
        setStatus(`Borrador creado: ${created.slug}`, "ok");
      } else {
        const updated = await adminApi.updateDraft(token, currentId, data);
        slugInput.value = updated.slug;
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
      setStatus("Conectado. Elige un borrador o crea uno nuevo.", "ok");
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

  // Al abrir la página: reconectar si ya hay token en esta pestaña.
  if (token) {
    tokenInput.value = token;
    connect(token);
  } else {
    setMode("idle");
  }
})();
