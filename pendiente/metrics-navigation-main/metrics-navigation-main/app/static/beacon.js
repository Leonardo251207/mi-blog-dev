(function () {
  "use strict";

  var script = document.currentScript;
  if (!script) {
    var scripts = document.querySelectorAll("script[data-key]");
    script = scripts.length ? scripts[scripts.length - 1] : null;
  }
  if (!script) return;

  var key = script.getAttribute("data-key");
  if (!key) return;
  if (location.protocol !== "http:" && location.protocol !== "https:") return;
  if (
    navigator.doNotTrack === "1" ||
    window.doNotTrack === "1" ||
    navigator.globalPrivacyControl === true
  ) {
    return;
  }

  var site = script.getAttribute("data-site") || "auto";
  var endpoint = script.getAttribute("data-endpoint");
  if (!endpoint) {
    try {
      endpoint = new URL("/v1/collect", script.src).href;
    } catch (error) {
      return;
    }
  }

  var sample = parseFloat(script.getAttribute("data-sample") || "1");
  if (!(sample >= 1) && Math.random() > sample) return;
  var debug = script.getAttribute("data-debug") === "true";

  function uuid() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      return window.crypto.randomUUID();
    }
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
      var r = (Math.random() * 16) | 0;
      var v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  function leer(store, clave) {
    try {
      return store.getItem(clave);
    } catch (error) {
      return null;
    }
  }

  function guardar(store, clave, valor) {
    try {
      store.setItem(clave, valor);
    } catch (error) {
      /* modo privado o almacenamiento lleno */
    }
  }

  var dia = new Date().toISOString().slice(0, 10);
  var claveVisitante = "mcr_vid_" + dia;
  var visitante = leer(window.localStorage, claveVisitante);
  if (!visitante) {
    visitante = uuid();
    guardar(window.localStorage, claveVisitante, visitante);
  }
  try {
    for (var i = window.localStorage.length - 1; i >= 0; i--) {
      var nombre = window.localStorage.key(i);
      if (nombre && nombre.indexOf("mcr_vid_") === 0 && nombre !== claveVisitante) {
        window.localStorage.removeItem(nombre);
      }
    }
  } catch (error) {
    /* sin acceso al almacenamiento */
  }

  var sesion = leer(window.sessionStorage, "mcr_sid");
  if (!sesion) {
    sesion = uuid();
    guardar(window.sessionStorage, "mcr_sid", sesion);
  }

  function utm() {
    var salida = {};
    try {
      var params = new URLSearchParams(location.search);
      [
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
      ].forEach(function (clave) {
        var valor = params.get(clave);
        if (valor) salida[clave] = valor.slice(0, 200);
      });
    } catch (error) {
      /* URLSearchParams no disponible */
    }
    return salida;
  }

  var vitales = {};
  if ("PerformanceObserver" in window) {
    try {
      new PerformanceObserver(function (lista) {
        var entradas = lista.getEntries();
        var ultima = entradas[entradas.length - 1];
        if (ultima) vitales.lcp = Math.round(ultima.startTime);
      }).observe({ type: "largest-contentful-paint", buffered: true });
    } catch (error) {
      /* sin soporte LCP */
    }
    try {
      var cls = 0;
      new PerformanceObserver(function (lista) {
        lista.getEntries().forEach(function (entrada) {
          if (!entrada.hadRecentInput) cls += entrada.value;
        });
        vitales.cls = Math.round(cls * 10000) / 10000;
      }).observe({ type: "layout-shift", buffered: true });
    } catch (error) {
      /* sin soporte CLS */
    }
  }

  var maxScroll = 0;
  function medirScroll() {
    var doc = document.documentElement;
    var altura = Math.max(
      doc.scrollHeight,
      document.body ? document.body.scrollHeight : 0
    );
    var visible = window.innerHeight || doc.clientHeight || 0;
    var recorrible = Math.max(1, altura - visible);
    var posicion = window.scrollY || doc.scrollTop || 0;
    var porcentaje = posicion / recorrible;
    if (porcentaje > maxScroll) maxScroll = Math.min(1, Math.max(0, porcentaje));
  }
  window.addEventListener("scroll", medirScroll, { passive: true });
  medirScroll();

  function enviar(tipo, extra) {
    var evento = {
      id: uuid(),
      type: tipo,
      ts: new Date().toISOString(),
      path: location.pathname,
      host: location.host,
      referrer: document.referrer || null,
      session: sesion,
      visitor: visitante,
      screen: window.screen
        ? window.screen.width + "x" + window.screen.height
        : null,
      language: navigator.language || null,
      utm: utm(),
    };
    if (extra) {
      for (var propiedad in extra) {
        if (Object.prototype.hasOwnProperty.call(extra, propiedad)) {
          evento[propiedad] = extra[propiedad];
        }
      }
    }

    var cuerpo = JSON.stringify({ key: key, site: site, events: [evento] });
    if (debug && window.console) console.debug("[mcr]", evento);

    if (navigator.sendBeacon) {
      try {
        var blob = new Blob([cuerpo], { type: "application/json" });
        if (navigator.sendBeacon(endpoint, blob)) return;
      } catch (error) {
        /* cae a fetch */
      }
    }
    try {
      fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: cuerpo,
        keepalive: true,
        mode: "cors",
        credentials: "omit",
      }).catch(function () {});
    } catch (error) {
      /* sin red */
    }
  }

  var inicio = Date.now();
  var engagementEnviado = false;
  function engagement() {
    if (engagementEnviado) return;
    engagementEnviado = true;
    var duracion = Math.max(0, Math.round((Date.now() - inicio) / 1000));
    enviar("ENGAGEMENT", {
      durationMs: duracion * 1000,
      scroll: maxScroll,
      vitals: vitales,
    });
  }

  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") engagement();
  });
  window.addEventListener("pagehide", engagement);

  enviar("PAGEVIEW");
})();
