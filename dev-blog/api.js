/* ==========================================================
   Cliente de la API del CMS y renderizador Markdown
   - Sitio público: listado, artículo por slug y registro de vista.
   - Consola: borradores, publicación, métricas y borrado.
   - El token de consola lo escribe el usuario en admin.html y se
     guarda solo en sessionStorage.
   ========================================================== */
(() => {
  "use strict";

  const config = window.DEVBLOG_CONFIG || {};
  const API_BASE_URL = String(config.API_BASE_URL || "http://127.0.0.1:8000/api/v1")
    .replace(/\/+$/, "");
  const PUBLIC_TOKEN = config.PUBLIC_TOKEN || "public-dev-token";

  class ApiError extends Error {
    constructor(status, payload) {
      const error = (payload && payload.error) || {};
      super(error.message || `Error HTTP ${status}`);
      this.name = "ApiError";
      this.status = status;
      this.code = error.code || "HTTP_ERROR";
      this.field = error.field || null;
      this.payload = payload || null;
    }
  }

  function newIdempotencyKey() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      return window.crypto.randomUUID();
    }
    return `key-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }

  async function request(path, options = {}) {
    const {
      method = "GET",
      body,
      token = PUBLIC_TOKEN,
      headers = {},
      idempotencyKey,
      cache,
    } = options;

    const requestHeaders = { Accept: "application/json", ...headers };
    if (token) requestHeaders.Authorization = `Bearer ${token}`;
    if (body !== undefined) requestHeaders["Content-Type"] = "application/json";
    if (idempotencyKey) requestHeaders["Idempotency-Key"] = idempotencyKey;

    let response;
    try {
      response = await fetch(`${API_BASE_URL}${path}`, {
        method,
        headers: requestHeaders,
        body: body !== undefined ? JSON.stringify(body) : undefined,
        ...(cache ? { cache } : {}),
      });
    } catch (cause) {
      throw new ApiError(0, {
        error: {
          code: "NETWORK_ERROR",
          message: "No se pudo conectar con la API. ¿Está uvicorn en marcha?",
        },
      });
    }

    if (response.status === 204) return null;

    const text = await response.text();
    let payload = null;
    if (text) {
      try {
        payload = JSON.parse(text);
      } catch {
        payload = null;
      }
    }

    if (!response.ok) {
      throw new ApiError(response.status, payload || {
        error: { code: "HTTP_ERROR", message: `Error HTTP ${response.status}` },
      });
    }
    return payload;
  }

  function pageQuery({ limit = 20, cursor, tag } = {}) {
    const params = new URLSearchParams();
    params.set("limit", String(limit));
    if (cursor) params.set("cursor", cursor);
    if (tag) params.set("tag", tag);
    return params.toString();
  }

  const publicApi = {
    // La portada prioriza mostrar el estado actual (por ejemplo, un artículo
    // recién publicado). La API sigue enviando ETag/Cache-Control para otros
    // clientes; aquí se decide no usar la caché del navegador.
    listPosts: (options = {}) => request(`/posts?${pageQuery(options)}`, {
      cache: "no-store",
    }),
    getPostBySlug: (slug) => request(`/posts/slug/${encodeURIComponent(slug)}`),
    registerView: (postId) => request(`/posts/${encodeURIComponent(postId)}/views`, {
      method: "POST",
    }),
  };

  const adminApi = {
    // Las lecturas de la consola deben ver siempre el estado actual. La API
    // marca /posts como cacheable para el sitio público; el panel usa
    // `cache: "no-store"` para saltarse esa caché sin cambiar el contrato.
    listDrafts: (token, options = {}) => request(`/drafts?${pageQuery(options)}`, {
      token,
      cache: "no-store",
    }),
    getDraft: (token, postId) => request(`/drafts/${encodeURIComponent(postId)}`, {
      token,
      cache: "no-store",
    }),
    createDraft: (token, data) => request("/drafts", {
      method: "POST",
      token,
      body: data,
      idempotencyKey: newIdempotencyKey(),
    }),
    updateDraft: (token, postId, data) => request(`/drafts/${encodeURIComponent(postId)}`, {
      method: "PUT",
      token,
      body: data,
    }),
    deleteDraft: (token, postId) => request(`/drafts/${encodeURIComponent(postId)}`, {
      method: "DELETE",
      token,
    }),
    publishDraft: (token, postId) => request(`/drafts/${encodeURIComponent(postId)}/publish`, {
      method: "POST",
      token,
      idempotencyKey: newIdempotencyKey(),
    }),
    listPosts: (token, options = {}) => request(`/posts?${pageQuery(options)}`, {
      token,
      cache: "no-store",
    }),
    getPost: (token, postId) => request(`/posts/${encodeURIComponent(postId)}`, {
      token,
      cache: "no-store",
    }),
    getMetrics: (token, postId) => request(`/posts/${encodeURIComponent(postId)}/metrics`, {
      token,
      cache: "no-store",
    }),
    deletePost: (token, postId) => request(`/posts/${encodeURIComponent(postId)}?confirm=true`, {
      method: "DELETE",
      token,
    }),
  };

  // ---------------------------------------------------------------- Markdown
  const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));

  const safeUrl = (url) => {
    const value = String(url || "").trim();
    if (/^(javascript|data|vbscript):/i.test(value)) return "#";
    return value || "#";
  };

  function inline(text) {
    const codeSpans = [];
    let value = String(text).replace(/`([^`]+)`/g, (_, code) => {
      codeSpans.push(`<code>${escapeHtml(code)}</code>`);
      return `\u0000CODE${codeSpans.length - 1}\u0000`;
    });

    value = escapeHtml(value);

    // Imágenes y enlaces. El texto ya está escapado, así que las comillas son &quot;.
    value = value.replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, (_, alt, src) => {
      const safe = safeUrl(src);
      return `<img src="${safe}" alt="${alt}" loading="lazy">`;
    });
    value = value.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_, label, href) => {
      const safe = safeUrl(href);
      const external = /^https?:/i.test(safe);
      const attrs = external ? ' target="_blank" rel="noopener noreferrer"' : "";
      return `<a href="${safe}"${attrs}>${label}</a>`;
    });

    value = value.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    value = value.replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>");
    value = value.replace(/(^|[^_])_([^_]+)_/g, "$1<em>$2</em>");
    value = value.replace(/ {2,}\n/g, "<br>");

    return value.replace(/\u0000CODE(\d+)\u0000/g, (_, index) => codeSpans[Number(index)]);
  }

  function renderMarkdown(markdown) {
    const lines = String(markdown || "").replace(/\r\n?/g, "\n").split("\n");
    const html = [];
    let index = 0;
    let paragraph = [];
    let list = null;

    const flushParagraph = () => {
      if (paragraph.length) {
        html.push(`<p>${inline(paragraph.join("\n"))}</p>`);
        paragraph = [];
      }
    };
    const flushList = () => {
      if (list) {
        const items = list.items.map((item) => `<li>${inline(item)}</li>`).join("");
        html.push(`<${list.type}>${items}</${list.type}>`);
        list = null;
      }
    };

    while (index < lines.length) {
      const line = lines[index];

      const fence = line.match(/^```(\w+)?\s*$/);
      if (fence) {
        flushParagraph();
        flushList();
        const language = fence[1] || "";
        const code = [];
        index += 1;
        while (index < lines.length && !/^```\s*$/.test(lines[index])) {
          code.push(lines[index]);
          index += 1;
        }
        index += 1;
        const className = language ? ` class="language-${escapeHtml(language)}"` : "";
        html.push(`<pre><code${className}>${escapeHtml(code.join("\n"))}</code></pre>`);
        continue;
      }

      const heading = line.match(/^(#{1,6})\s+(.*)$/);
      if (heading) {
        flushParagraph();
        flushList();
        const level = heading[1].length;
        html.push(`<h${level}>${inline(heading[2].trim())}</h${level}>`);
        index += 1;
        continue;
      }

      if (/^\s*(---|\*\*\*|___)\s*$/.test(line)) {
        flushParagraph();
        flushList();
        html.push("<hr>");
        index += 1;
        continue;
      }

      if (/^>\s?/.test(line)) {
        flushParagraph();
        flushList();
        const quote = [];
        while (index < lines.length && /^>\s?/.test(lines[index])) {
          quote.push(lines[index].replace(/^>\s?/, ""));
          index += 1;
        }
        html.push(`<blockquote>${renderMarkdown(quote.join("\n"))}</blockquote>`);
        continue;
      }

      const listItem = line.match(/^\s*([-*+]|\d+\.)\s+(.*)$/);
      if (listItem) {
        flushParagraph();
        const type = /^\d+\.$/.test(listItem[1]) ? "ol" : "ul";
        if (list && list.type !== type) flushList();
        if (!list) list = { type, items: [] };
        list.items.push(listItem[2]);
        index += 1;
        continue;
      }

      if (!line.trim()) {
        flushParagraph();
        flushList();
        index += 1;
        continue;
      }

      flushList();
      paragraph.push(line.trim());
      index += 1;
    }

    flushParagraph();
    flushList();
    return html.join("\n");
  }

  window.DevBlogAPI = {
    ApiError,
    request,
    publicApi,
    adminApi,
    newIdempotencyKey,
    config: { API_BASE_URL, PUBLIC_TOKEN },
  };
  window.DevBlogMarkdown = { render: renderMarkdown };
})();
