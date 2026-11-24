/* Reintento de despliegue de GitHub Pages */
/* ==========================================================
   Dashboard analÃ­tico del CMS
   - Usa el trÃ¡fico real del colector (a travÃ©s del backend).
   - Usa las vistas reales de cada artÃ­culo del CMS.
   - Adapta el panel del profesor a la estÃ©tica DevBlog_.
   ========================================================== */
(() => {
  "use strict";

  const API = window.DevBlogAPI;
  if (!API) return;

  const { adminApi } = API;
  const $ = (selector, ctx = document) => ctx.querySelector(selector);
  const $$ = (selector, ctx = document) => [...ctx.querySelectorAll(selector)];

  const panel = $("#panel-dashboard");
  if (!panel) return;

  const SITES_KEY = "devblog_dashboard_sites_v1";
  const PERIOD_KEY = "devblog_dashboard_period_v1";
  const SITE_KEY = "devblog_dashboard_site_v1";

  const DEFAULT_SITES = [
    {
      id: "blog",
      name: "DevBlog_",
      hosts: ["mi-blog-dev.vercel.app", "leonardo251207.github.io"],
      color: "#3df0a8",
      kind: "blog",
    },
    {
      id: "landing",
      name: "Portafolio",
      hosts: ["mi-landing-devblog.vercel.app"],
      color: "#3de4ff",
      kind: "landing",
    },
  ];

  const PERIODS = {
    "1d": { days: 1, grano: "HORA", label: "Ãšltimo dÃ­a (24 h)" },
    "1w": { days: 7, grano: "DIA", label: "Ãšltima semana (7 dÃ­as)" },
    "2w": { days: 14, grano: "DIA", label: "Ãšltimas 2 semanas (14 dÃ­as)" },
    "1m": { days: 30, grano: "DIA", label: "Ãšltimo mes (30 dÃ­as)" },
    "3m": { days: 90, grano: "DIA", label: "Ãšltimos 3 meses (90 dÃ­as)" },
    "1y": { days: 365, grano: "DIA", label: "Ãšltimo aÃ±o (365 dÃ­as)" },
  };

  const PALETTE = ["#3df0a8", "#3de4ff", "#b48cff", "#5b8cff", "#ffd23f", "#ffb066"];

  const numberFmt = new Intl.NumberFormat("es-MX");
  const dateFmt = new Intl.DateTimeFormat("es-MX", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

  const state = {
    token: "",
    period: localStorage.getItem(PERIOD_KEY) || "1w",
    site: localStorage.getItem(SITE_KEY) || "all",
    histMode: "posts",
    pieMode: "sites",
    pieStyle: "pie",
    search: "",
    limit: 10,
    sites: loadSites(),
    metrics: null,
    metricsError: null,
    posts: [],
    loading: false,
    loadedForToken: "",
  };

  if (!PERIODS[state.period]) state.period = "1w";

  // ------------------------------------------------------------- utilidades
  function loadSites() {
    try {
      const raw = localStorage.getItem(SITES_KEY);
      const stored = raw ? JSON.parse(raw) : null;
      if (Array.isArray(stored) && stored.length) return stored;
    } catch {
      // Ignorar almacenamiento corrupto
    }
    return DEFAULT_SITES.map((site) => ({ ...site, hosts: [...site.hosts] }));
  }

  function saveSites() {
    try {
      localStorage.setItem(SITES_KEY, JSON.stringify(state.sites));
    } catch {
      // Ignorar cuota
    }
  }

  function hostKey(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/^https?:\/\//, "")
      .replace(/\/.*$/, "");
  }

  function currentToken() {
    return sessionStorage.getItem("devblog_console_token") || "";
  }

  function setStatus(message, kind = "info") {
    const el = $("#dash-status");
    if (!el) return;
    el.textContent = message;
    el.dataset.kind = kind;
  }

  function setLoading(loading) {
    state.loading = loading;
    panel.classList.toggle("dash__loading", loading);
    const refresh = $("#dash-refresh");
    if (refresh) refresh.disabled = loading;
  }

  function empty(text) {
    const p = document.createElement("p");
    p.className = "dash__empty";
    p.textContent = text;
    return p;
  }

  function pct(part, total) {
    return total > 0 ? (part / total) * 100 : 0;
  }

  function siteOfHost(host) {
    const key = hostKey(host);
    return state.sites.find((site) =>
      (site.hosts || []).some((candidate) => hostKey(candidate) === key)
    );
  }

  function siteColor(host, index = 0) {
    const site = siteOfHost(host);
    return site?.color || PALETTE[index % PALETTE.length];
  }

  function siteStats() {
    const metrics = state.metrics;
    const hostRows = Array.isArray(metrics?.por_host) ? metrics.por_host : [];
    const totalPv = Number(metrics?.pageviews) || 0;
    const totalSessions = Number(metrics?.sesiones) || 0;
    const totalUnique = Number(metrics?.visitantes_unicos) || 0;

    return state.sites.map((site) => {
      const hosts = (site.hosts || []).map(hostKey);
      const pv = hostRows
        .filter((row) => hosts.includes(hostKey(row.clave)))
        .reduce((sum, row) => sum + (Number(row.valor) || 0), 0);
      const share = totalPv > 0 ? pv / totalPv : 0;
      return {
        ...site,
        pageviews: pv,
        sessions: Math.round(totalSessions * share),
        unique: Math.round(totalUnique * share),
        share,
        posts: state.posts.length,
      };
    });
  }

  function averageReading() {
    if (!state.posts.length) return 0;
    const total = state.posts.reduce((sum, post) => sum + (Number(post.reading_time_min) || 0), 0);
    return total / state.posts.length;
  }

  function selectedSite() {
    if (state.site === "all") return null;
    return state.sites.find((site) => site.id === state.site) || null;
  }

  function scopeLabel() {
    const site = selectedSite();
    return `${site ? site.name : "Todos los sitios"} Â· ${PERIODS[state.period].label}`;
  }

  function downloadFile(content, filename, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.rel = "noopener";
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  }

  function kpi(label, value, hint = "", tone = "") {
    const box = document.createElement("div");
    box.className = "dash__kpi";
    const labelEl = document.createElement("span");
    labelEl.textContent = label;
    const valueEl = document.createElement("strong");
    valueEl.textContent = value;
    box.append(labelEl, valueEl);
    if (hint) {
      const hintEl = document.createElement("small");
      hintEl.textContent = hint;
      if (tone) hintEl.className = `is-${tone}`;
      box.append(hintEl);
    }
    return box;
  }

  // --------------------------------------------------------------- carga
  async function loadDashboard({ force = false, refreshPosts = false } = {}) {
    const token = currentToken();
    if (!token) {
      setStatus("Conecta la consola para consultar el dashboard.", "info");
      return;
    }
    if (state.loading) return;
    if (!force && state.loadedForToken === token && state.metrics) {
      renderAll();
      return;
    }

    state.token = token;
    setLoading(true);
    setStatus("Consultando trÃ¡fico y publicacionesâ€¦", "info");

    const period = PERIODS[state.period];
    const metricsPromise = adminApi
      .getMetricsOverview(token, { days: period.days, grano: period.grano })
      .then((data) => ({ data, error: null }))
      .catch((error) => ({ data: null, error }));

    const onlyRefreshPosts = !refreshPosts && state.posts.length > 0 && state.loadedForToken === token;
    const postsPromise = onlyRefreshPosts
      ? Promise.resolve({ page: null, error: null })
      : adminApi
          .listPosts(token, { limit: 24 })
          .then((page) => ({ page, error: null }))
          .catch((error) => ({ page: null, error }));

    const [metricsResult, postsResult] = await Promise.all([metricsPromise, postsPromise]);

    state.metrics = metricsResult.data;
    state.metricsError = metricsResult.error;

    if (postsResult.page?.items?.length) {
      const posts = postsResult.page.items;
      state.posts = await Promise.all(
        posts.map(async (post) => {
          try {
            const metrics = await adminApi.getMetrics(token, post.post_id);
            return { ...post, views_total: Number(metrics?.views_total) || 0 };
          } catch {
            return { ...post, views_total: 0 };
          }
        })
      );
    } else if (!onlyRefreshPosts && !state.posts.length) {
      state.posts = [];
    }

    state.loadedForToken = token;
    setLoading(false);

    if (state.metricsError) {
      setStatus(
        `No se pudieron consultar las mÃ©tricas: ${state.metricsError.message || "servicio no disponible"}. Se muestran las vistas del CMS.`,
        "error"
      );
    } else if (state.metrics && state.metrics.disponible === false) {
      setStatus(
        `MÃ©tricas no disponibles: ${state.metrics.error || "el colector no respondiÃ³"}. Se muestran las vistas del CMS.`,
        "error"
      );
    } else {
      setStatus(`Datos de ${scopeLabel()}.`, "ok");
    }

    renderAll();
  }

  // --------------------------------------------------------------- render
  function renderSiteSelector() {
    const select = $("#dash-site");
    if (!select) return;
    const current = state.site;
    select.replaceChildren();

    const all = document.createElement("option");
    all.value = "all";
    all.textContent = `Todos los sitios (${state.sites.length})`;
    select.append(all);

    for (const site of state.sites) {
      const option = document.createElement("option");
      option.value = site.id;
      option.textContent = `${site.name} (${(site.hosts || [])[0] || "sin host"})`;
      select.append(option);
    }

    if (![...select.options].some((option) => option.value === current)) {
      state.site = "all";
      localStorage.setItem(SITE_KEY, state.site);
    }
    select.value = state.site;
  }

  function renderPeriods() {
    $$("[data-period]").forEach((button) => {
      button.classList.toggle("is-active", button.dataset.period === state.period);
      button.setAttribute("aria-pressed", String(button.dataset.period === state.period));
    });
    const scope = $("#dash-scope");
    if (scope) scope.textContent = scopeLabel();
  }

  function renderSummary() {
    const metrics = state.metrics || {};
    const totalPv = Number(metrics.pageviews) || 0;
    const totalUnique = Number(metrics.visitantes_unicos) || 0;
    const totalSessions = Number(metrics.sesiones) || 0;
    const site = selectedSite();
    const stats = siteStats();
    const focus = site || [...stats].sort((a, b) => b.pageviews - a.pageviews)[0] || null;
    const reading = averageReading();

    const kpis = $("#dash-kpis");
    if (kpis) {
      kpis.replaceChildren(
        kpi("Pageviews", numberFmt.format(totalPv), "TrÃ¡fico total del sitio"),
        kpi("Visitantes Ãºnicos", numberFmt.format(totalUnique), "Lectores distintos"),
        kpi("Sesiones", numberFmt.format(totalSessions), "Sesiones registradas"),
        kpi(
          "Lectura promedio",
          reading ? `${reading.toFixed(1)} min` : "â€”",
          `${state.posts.length} artÃ­culos publicados`
        )
      );
    }

    const summaryScope = $("#dash-summary-scope");
    if (summaryScope) summaryScope.textContent = `${state.sites.length} sitios Â· ${state.posts.length} entradas`;

    const focusName = $("#dash-focus-name");
    const focusHost = $("#dash-focus-host");
    const focusKpis = $("#dash-focus-kpis");
    if (focusName) focusName.textContent = focus ? focus.name : "Sin trÃ¡fico";
    if (focusHost) focusHost.textContent = focus ? (focus.hosts || [])[0] || "" : "";

    if (focusKpis) {
      focusKpis.replaceChildren(
        kpi("Pageviews", numberFmt.format(focus?.pageviews || 0), "En el periodo"),
        kpi("Visitantes", numberFmt.format(focus?.unique || 0), "Estimado por proporciÃ³n"),
        kpi(
          "ProporciÃ³n",
          `${pct(focus?.pageviews || 0, totalPv).toFixed(1)}%`,
          "Del trÃ¡fico total"
        ),
        kpi(
          "Entradas",
          numberFmt.format(focus?.kind === "landing" ? 0 : state.posts.length),
          focus?.kind === "landing" ? "Sitio sin blog" : "Publicaciones activas"
        )
      );
    }
  }

  function renderHistogram() {
    const container = $("#dash-histogram");
    if (!container) return;
    container.replaceChildren();

    const stats = siteStats();
    let items = [];
    if (state.histMode === "sites") {
      items = stats
        .map((site) => ({
          label: site.name,
          sub: (site.hosts || [])[0] || "",
          value: site.pageviews,
          color: site.color,
        }))
        .sort((a, b) => b.value - a.value);
    } else {
      items = state.posts
        .slice()
        .sort((a, b) => (b.views_total || 0) - (a.views_total || 0))
        .slice(0, 8)
        .map((post) => ({
          label: post.title,
          sub: `${post.reading_time_min || 0} min`,
          value: Number(post.views_total) || 0,
          color: "#3df0a8",
        }));
    }

    if (!items.length) {
      container.append(empty("Sin datos para graficar en este periodo."));
      return;
    }

    const max = Math.max(...items.map((item) => item.value), 1);
    items.forEach((item, index) => {
      const wrap = document.createElement("div");
      wrap.className = `dash__hist-item${index % 2 ? " is-alt" : ""}`;
      wrap.title = `${item.label}: ${numberFmt.format(item.value)}`;

      const value = document.createElement("span");
      value.className = "dash__hist-value";
      value.textContent = numberFmt.format(item.value);

      const track = document.createElement("span");
      track.className = "dash__hist-track";
      const fill = document.createElement("i");
      fill.className = "dash__hist-fill";
      fill.style.height = `${Math.max(2, (item.value / max) * 100)}%`;
      fill.style.background = `linear-gradient(180deg, ${item.color}, rgba(61,240,168,0.25))`;
      track.append(fill);

      const label = document.createElement("span");
      label.className = "dash__hist-label";
      label.textContent = item.label;
      const sub = document.createElement("small");
      sub.textContent = item.sub;
      label.append(sub);

      wrap.append(value, track, label);
      container.append(wrap);
    });
  }

  function renderPie() {
    const wrap = $("#dash-pie");
    const legend = $("#dash-pie-legend");
    if (!wrap || !legend) return;

    const metrics = state.metrics || {};
    let rows = [];
    if (state.pieMode === "routes") {
      rows = (metrics.por_ruta || []).map((row) => ({
        name: row.clave || "/",
        value: Number(row.valor) || 0,
      }));
    } else if (state.pieMode === "hosts") {
      const byHost = new Map();
      (metrics.por_host || []).forEach((row) => {
        const key = hostKey(row.clave);
        byHost.set(key, (byHost.get(key) || 0) + (Number(row.valor) || 0));
      });
      rows = [...byHost.entries()].map(([host, value]) => ({
        name: host,
        value,
        color: siteColor(host),
      }));
    } else {
      const bySite = new Map();
      (metrics.por_host || []).forEach((row) => {
        const site = siteOfHost(row.clave);
        const key = site?.id || hostKey(row.clave);
        const current = bySite.get(key) || {
          name: site?.name || row.clave,
          value: 0,
          color: site?.color || PALETTE[bySite.size % PALETTE.length],
        };
        current.value += Number(row.valor) || 0;
        bySite.set(key, current);
      });
      rows = [...bySite.values()];
    }

    rows = rows.filter((row) => row.value > 0).sort((a, b) => b.value - a.value);
    const total = rows.reduce((sum, row) => sum + row.value, 0);

    if (!rows.length || total === 0) {
      wrap.style.setProperty("--pie", "conic-gradient(var(--line) 0 100%)");
      wrap.classList.toggle("is-donut", state.pieStyle === "donut");
      legend.replaceChildren();
      const li = document.createElement("li");
      li.textContent = "Sin trÃ¡fico en el periodo.";
      legend.append(li);
      return;
    }

    let cursor = 0;
    const segments = rows.map((row, index) => {
      const color = row.color || PALETTE[index % PALETTE.length];
      const share = row.value / total;
      const start = cursor * 360;
      cursor += share;
      const end = cursor * 360;
      return `${color} ${start.toFixed(2)}deg ${end.toFixed(2)}deg`;
    });

    wrap.style.setProperty("--pie", `conic-gradient(${segments.join(", ")})`);
    wrap.classList.toggle("is-donut", state.pieStyle === "donut");
    wrap.setAttribute("aria-label", `DistribuciÃ³n de trÃ¡fico: ${rows.length} segmentos`);

    legend.replaceChildren();
    rows.forEach((row, index) => {
      const color = row.color || PALETTE[index % PALETTE.length];
      const li = document.createElement("li");
      const dot = document.createElement("i");
      dot.style.background = color;
      const name = document.createElement("span");
      name.textContent = row.name;
      const value = document.createElement("strong");
      value.textContent = `${numberFmt.format(row.value)} Â· ${pct(row.value, total).toFixed(1)}%`;
      li.append(dot, name, value);
      legend.append(li);
    });
  }

  function renderRanking() {
    const body = $("#dash-ranking-body");
    if (!body) return;
    body.replaceChildren();

    const query = state.search.trim().toLowerCase();
    const rows = state.posts
      .filter((post) => {
        if (!query) return true;
        const haystack = [post.title, post.slug, ...(post.tags || [])].join(" ").toLowerCase();
        return haystack.includes(query);
      })
      .sort((a, b) => (b.views_total || 0) - (a.views_total || 0))
      .slice(0, state.limit);

    const sub = $("#dash-ranking-sub");
    if (sub) {
      sub.textContent = `${scopeLabel()} Â· ${rows.length} de ${state.posts.length} entradas`;
    }

    if (!rows.length) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 7;
      td.append(empty("No hay artÃ­culos que coincidan con la bÃºsqueda."));
      tr.append(td);
      body.append(tr);
      return;
    }

    const max = Math.max(...rows.map((post) => Number(post.views_total) || 0), 1);
    const average =
      rows.reduce((sum, post) => sum + (Number(post.views_total) || 0), 0) / Math.max(rows.length, 1);

    rows.forEach((post, index) => {
      const tr = document.createElement("tr");

      const rank = document.createElement("td");
      rank.textContent = String(index + 1).padStart(2, "0");

      const titleCell = document.createElement("td");
      const title = document.createElement("span");
      title.className = "dash__post-title";
      title.textContent = post.title;
      const slug = document.createElement("span");
      slug.className = "dash__post-slug";
      slug.textContent = `/${post.slug}`;
      titleCell.append(title, slug);

      const tagsCell = document.createElement("td");
      (post.tags || []).slice(0, 2).forEach((tag) => {
        const chip = document.createElement("span");
        chip.className = "dash__chip";
        chip.textContent = tag;
        tagsCell.append(chip, document.createTextNode(" "));
      });
      if (!post.tags?.length) tagsCell.textContent = "â€”";

      const viewsCell = document.createElement("td");
      const viewsWrap = document.createElement("span");
      viewsWrap.className = "dash__views";
      const bar = document.createElement("span");
      bar.className = "dash__views-bar";
      const fill = document.createElement("i");
      const viewsValue = Number(post.views_total) || 0;
      fill.style.width = `${Math.max(2, (viewsValue / max) * 100)}%`;
      bar.append(fill);
      const value = document.createElement("span");
      value.textContent = numberFmt.format(viewsValue);
      viewsWrap.append(bar, value);
      viewsCell.append(viewsWrap);

      const trendCell = document.createElement("td");
      const delta = average > 0 ? ((viewsValue - average) / average) * 100 : 0;
      trendCell.className = delta >= 0 ? "dash__trend is-pos" : "dash__trend is-neg";
      trendCell.textContent = `${delta >= 0 ? "+" : ""}${delta.toFixed(0)}%`;
      trendCell.title = "Vistas frente al promedio de los artÃ­culos mostrados";

      const readingCell = document.createElement("td");
      readingCell.textContent = `${post.reading_time_min || 0} min`;

      const dateCell = document.createElement("td");
      const date = post.published_at ? new Date(post.published_at) : null;
      dateCell.textContent = date && !Number.isNaN(date.getTime()) ? dateFmt.format(date) : "â€”";

      tr.append(rank, titleCell, tagsCell, viewsCell, trendCell, readingCell, dateCell);
      body.append(tr);
    });
  }

  function renderAll() {
    renderSiteSelector();
    renderPeriods();
    renderSummary();
    renderHistogram();
    renderPie();
    renderRanking();
  }

  // -------------------------------------------------------------- eventos
  function bind() {
    $$("[data-period]").forEach((button) => {
      button.addEventListener("click", () => {
        state.period = button.dataset.period;
        localStorage.setItem(PERIOD_KEY, state.period);
        loadDashboard({ force: true });
      });
    });

    $("#dash-site")?.addEventListener("change", (event) => {
      state.site = event.target.value;
      localStorage.setItem(SITE_KEY, state.site);
      renderAll();
    });

    $("#dash-refresh")?.addEventListener("click", () => loadDashboard({ force: true, refreshPosts: true }));

    $("#dash-export")?.addEventListener("click", () => {
      const rows = state.posts
        .slice()
        .sort((a, b) => (b.views_total || 0) - (a.views_total || 0));
      const header = ["titulo", "slug", "etiquetas", "vistas", "lectura_min", "publicado"];
      const lines = rows.map((post) => [
        post.title,
        post.slug,
        (post.tags || []).join("|"),
        post.views_total || 0,
        post.reading_time_min || 0,
        post.published_at || "",
      ]);
      const csv = [header, ...lines]
        .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","))
        .join("\r\n");
      downloadFile(`\uFEFF${csv}`, `devblog-ranking-${state.period}.csv`, "text/csv;charset=utf-8");
      setStatus("Reporte CSV exportado.", "ok");
    });

    $("#dash-search")?.addEventListener("input", (event) => {
      state.search = event.target.value;
      renderRanking();
    });

    $("#dash-limit")?.addEventListener("change", (event) => {
      state.limit = Number(event.target.value) || 10;
      renderRanking();
    });

    $$("[data-hist-mode]").forEach((button) => {
      button.addEventListener("click", () => {
        state.histMode = button.dataset.histMode;
        $$("[data-hist-mode]").forEach((item) => {
          item.classList.toggle("is-active", item === button);
        });
        renderHistogram();
      });
    });

    $$("[data-pie-mode]").forEach((button) => {
      button.addEventListener("click", () => {
        state.pieMode = button.dataset.pieMode;
        $$("[data-pie-mode]").forEach((item) => {
          item.classList.toggle("is-active", item === button);
        });
        renderPie();
      });
    });

    $$("[data-pie-style]").forEach((button) => {
      button.addEventListener("click", () => {
        state.pieStyle = button.dataset.pieStyle;
        $$("[data-pie-style]").forEach((item) => {
          item.classList.toggle("is-active", item === button);
        });
        renderPie();
      });
    });

    const modal = $("#site-modal");
    const form = $("#site-form");
    const nameInput = $("#site-name");
    const hostInput = $("#site-host");
    const colorInput = $("#site-color");

    $("#dash-add-site")?.addEventListener("click", () => {
      modal.hidden = false;
      setTimeout(() => nameInput?.focus(), 40);
    });

    $("#site-cancel")?.addEventListener("click", () => {
      modal.hidden = true;
    });

    modal?.addEventListener("click", (event) => {
      if (event.target === modal) modal.hidden = true;
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !modal?.hidden) modal.hidden = true;
    });

    form?.addEventListener("submit", (event) => {
      event.preventDefault();
      const name = String(nameInput.value || "").trim();
      const hosts = String(hostInput.value || "")
        .split(",")
        .map(hostKey)
        .filter(Boolean);
      if (!name || !hosts.length) {
        setStatus("Escribe un nombre y al menos un dominio.", "error");
        return;
      }
      const newSite = {
        id: `site-${Date.now()}`,
        name,
        hosts,
        color: colorInput.value || PALETTE[state.sites.length % PALETTE.length],
        kind: "custom",
      };
      state.sites.push(newSite);
      saveSites();
      state.site = newSite.id;
      localStorage.setItem(SITE_KEY, state.site);
      modal.hidden = true;
      form.reset();
      colorInput.value = "#3df0a8";
      renderSiteSelector();
      setStatus(`Sitio "${name}" agregado.`, "ok");
      state.loadedForToken = "";
      loadDashboard({ force: true, refreshPosts: true });
    });

    document.addEventListener("devblog:tab", (event) => {
      if (event.detail?.name === "dashboard") {
        loadDashboard();
      }
    });
  }

  bind();
  renderSiteSelector();
  renderPeriods();

  // Si la consola ya estÃ¡ conectada y el usuario abre el dashboard desde el hash,
  // el evento de pestaÃ±a se encarga; tambiÃ©n dejamos una carga diferida.
  if (currentToken() && !panel.hidden) {
    loadDashboard();
  }
})();

