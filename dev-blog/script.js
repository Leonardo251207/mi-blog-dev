/* ==========================================================
   DevBlog_ — Interacciones y simulación
   ========================================================== */
(() => {
  "use strict";

  const CONTACT_EMAIL = "253425@it2id.upchiapas.edu.mx";

  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Menú móvil ---------- */
  const nav = $(".nav");
  const toggle = $(".nav__toggle");
  if (nav && toggle) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    $$(".nav__links a").forEach((a) =>
      a.addEventListener("click", () => {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      })
    );
  }

  /* ---------- Enlace activo según la sección visible ---------- */
  const navLinks = $$('.nav__links a[href^="#"]');
  if (navLinks.length && "IntersectionObserver" in window) {
    const byId = new Map(navLinks.map((a) => [a.getAttribute("href").slice(1), a]));
    const spy = new IntersectionObserver(
      (entries) =>
        entries.forEach((e) => {
          const link = byId.get(e.target.id);
          if (link && e.isIntersecting) {
            navLinks.forEach((l) => l.classList.remove("is-active"));
            link.classList.add("is-active");
          }
        }),
      { rootMargin: "-45% 0px -50% 0px" }
    );
    byId.forEach((_, id) => {
      const section = document.getElementById(id);
      if (section) spy.observe(section);
    });
  }

  /* ---------- Revelado al hacer scroll ---------- */
  const reveals = $$(".reveal");
  if ("IntersectionObserver" in window && !reduceMotion) {
    const io = new IntersectionObserver(
      (entries) =>
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("is-visible");
            io.unobserve(e.target);
          }
        }),
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add("is-visible"));
  }

  /* ---------- Pestañas genéricas (teclado + ARIA) ---------- */
  $$("[data-tabs]").forEach((group) => {
    const tabs = $$('[role="tab"]', group);
    const panels = $$('[role="tabpanel"]', group);

    const activate = (index, { focus = false, user = false } = {}) => {
      tabs.forEach((tab, i) => {
        const on = i === index;
        tab.setAttribute("aria-selected", String(on));
        tab.tabIndex = on ? 0 : -1;
      });
      panels.forEach((panel, i) => {
        const on = i === index;
        panel.hidden = !on;
        panel.classList.remove("play");
        if (on) {
          void panel.offsetWidth; // reinicia la animación
          panel.classList.add("play");
        }
      });
      if (focus) tabs[index].focus();
      group.dispatchEvent(
        new CustomEvent("tabchange", { detail: { index, panel: panels[index], user } })
      );
    };

    tabs.forEach((tab, i) => {
      tab.addEventListener("click", () => activate(i, { user: true }));
      tab.addEventListener("keydown", (e) => {
        let next = null;
        if (e.key === "ArrowRight") next = (i + 1) % tabs.length;
        else if (e.key === "ArrowLeft") next = (i - 1 + tabs.length) % tabs.length;
        else if (e.key === "Home") next = 0;
        else if (e.key === "End") next = tabs.length - 1;
        if (next !== null) {
          e.preventDefault();
          activate(next, { focus: true, user: true });
        }
      });
    });

    activate(0);
  });

  /* ---------- Copiar prompt ---------- */
  $$("[data-copy]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const source = $(btn.dataset.copy);
      if (!source) return;
      const text = source.textContent.trim();
      try {
        await navigator.clipboard.writeText(text);
      } catch {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.append(ta);
        ta.select();
        document.execCommand("copy");
        ta.remove();
      }
      const label = $(".btn__label", btn);
      const original = label.textContent;
      label.textContent = "¡Copiado!";
      btn.classList.add("is-done");
      setTimeout(() => {
        label.textContent = original;
        btn.classList.remove("is-done");
      }, 1600);
    });
  });

  /* ---------- Comparador antes / después ---------- */
  $$("[data-compare]").forEach((box) => {
    const handle = $(".compare__handle", box);
    let pos = 50;
    let dragging = false;

    const set = (p) => {
      pos = Math.max(0, Math.min(100, p));
      box.style.setProperty("--pos", pos + "%");
      handle.setAttribute("aria-valuenow", String(Math.round(pos)));
    };
    const fromPointer = (e) => {
      const r = box.getBoundingClientRect();
      set(((e.clientX - r.left) / r.width) * 100);
    };

    box.addEventListener("pointerdown", (e) => {
      dragging = true;
      box.setPointerCapture(e.pointerId);
      box.classList.add("is-drag");
      fromPointer(e);
    });
    box.addEventListener("pointermove", (e) => dragging && fromPointer(e));
    const stop = () => {
      dragging = false;
      box.classList.remove("is-drag");
    };
    box.addEventListener("pointerup", stop);
    box.addEventListener("pointercancel", stop);

    handle.addEventListener("keydown", (e) => {
      const step = e.shiftKey ? 10 : 2;
      const map = {
        ArrowLeft: () => set(pos - step),
        ArrowRight: () => set(pos + step),
        Home: () => set(0),
        End: () => set(100),
      };
      if (map[e.key]) {
        e.preventDefault();
        map[e.key]();
      }
    });

    // Pequeño “empujón” la primera vez que aparece, para sugerir que se arrastra
    if (!reduceMotion && "IntersectionObserver" in window) {
      const once = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting) {
            once.disconnect();
            setTimeout(() => set(64), 350);
            setTimeout(() => set(50), 1100);
          }
        },
        { threshold: 0.6 }
      );
      once.observe(box);
    }
    set(50);
  });

  /* ---------- Demo de pronunciación (simulada) ---------- */
  $$("[data-voice-demo]").forEach((stage) => {
    const btn = $(".mic-btn", stage);
    const label = $(".mic-btn__label", btn);
    const captured = $("[data-r-captured]", stage);
    const score = $("[data-r-score]", stage);
    const verdict = $("[data-r-verdict]", stage);
    const match = $("[data-match]", stage);
    const target = $("[data-word]", stage).textContent.trim();

    const IDLE = "Mantener para hablar";
    let startedAt = 0;
    let timer = null;

    const setState = (s) => (stage.dataset.state = s);

    const start = () => {
      if (stage.dataset.state === "listening") return;
      clearTimeout(timer);
      startedAt = performance.now();
      setState("listening");
      label.textContent = "Escuchando...";
      verdict.textContent = "[ ... ]";
      captured.textContent = "...";
      score.textContent = "—";
    };

    const end = () => {
      if (stage.dataset.state !== "listening") return;
      const held = performance.now() - startedAt;
      if (held < 450) {
        setState("idle");
        label.textContent = IDLE;
        verdict.textContent = "[ MANTÉN PRESIONADO Y HABLA ]";
        captured.textContent = "—";
        return;
      }
      setState("analyzing");
      label.textContent = "Analizando...";
      verdict.textContent = "[ ANALIZANDO PRONUNCIACIÓN... ]";
      timer = setTimeout(() => {
        const pct = 90 + Math.floor(Math.random() * 10); // simulación
        captured.textContent = `"${target}"`;
        score.textContent = pct + "%";
        match.textContent = pct + "%_COINCIDENCIA";
        verdict.textContent = "[ ¡PRONUNCIACIÓN CORRECTA! ]";
        label.textContent = IDLE;
        setState("done");
      }, 900);
    };

    btn.addEventListener("pointerdown", (e) => {
      btn.setPointerCapture(e.pointerId);
      start();
    });
    btn.addEventListener("pointerup", end);
    btn.addEventListener("pointercancel", end);
    btn.addEventListener("contextmenu", (e) => e.preventDefault());
    btn.addEventListener("keydown", (e) => {
      if ((e.key === " " || e.key === "Enter") && !e.repeat) {
        e.preventDefault();
        start();
      }
    });
    btn.addEventListener("keyup", (e) => {
      if (e.key === " " || e.key === "Enter") end();
    });
  });

  /* ---------- Matemáticas con voz (SpeechSynthesis) ---------- */
  const mathGroup = $("[data-math]");
  if (mathGroup) {
    const synth = "speechSynthesis" in window ? window.speechSynthesis : null;
    const voiceTags = $$("[data-voice-toggle]", mathGroup);
    let voiceOn = true;

    const speak = (text) => {
      if (!synth || !voiceOn || !text) return;
      synth.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = "es-MX";
      u.rate = 0.95;
      const voice = synth.getVoices().find((v) => v.lang && v.lang.toLowerCase().startsWith("es"));
      if (voice) u.voice = voice;
      synth.speak(u);
    };

    const paintTags = () =>
      voiceTags.forEach((tag) => {
        tag.setAttribute("aria-pressed", String(voiceOn));
        $(".voice-tag__text", tag).textContent = voiceOn
          ? "Retroalimentación de voz activa"
          : "Voz silenciada";
      });

    if (!synth) voiceTags.forEach((t) => (t.hidden = true));

    voiceTags.forEach((tag) =>
      tag.addEventListener("click", () => {
        voiceOn = !voiceOn;
        paintTags();
        if (!voiceOn && synth) synth.cancel();
        else speak($('[role="tabpanel"]:not([hidden])', mathGroup)?.dataset.speak);
      })
    );

    mathGroup.addEventListener("tabchange", (e) => {
      if (e.detail.user) speak(e.detail.panel.dataset.speak);
    });
    paintTags();
  }
  /* ---------- Checklist pre-despliegue ---------- */
  $$("[data-checklist]").forEach((root) => {
    const items = $$('[role="checkbox"]', root);
    const ring = $("[data-ring]", root);
    const pctEl = $("[data-pct]", root);
    const caption = $("[data-caption]", root);

    const update = () => {
      let done = 0;
      items.forEach((item) => {
        const on = item.getAttribute("aria-checked") === "true";
        if (on) done++;
        $(".check__state", item).textContent = on ? "VERIFICADO" : "PENDIENTE";
      });
      const pct = Math.round((done / items.length) * 100);
      ring.style.strokeDashoffset = String(100 - pct);
      pctEl.textContent = pct + "%";
      caption.textContent =
        pct === 100 ? "100% · LISTO PARA PRODUCCIÓN" : `${pct}% · VERIFICACIÓN PENDIENTE`;
    };

    items.forEach((item) =>
      item.addEventListener("click", () => {
        item.setAttribute("aria-checked", String(item.getAttribute("aria-checked") !== "true"));
        update();
      })
    );
    update();
  });

  /* ---------- Consola de producción (simulada) ---------- */
  $$("[data-pipeline]").forEach((root) => {
    const lines = $$(".log__line", root);
    const replay = $("[data-replay]", root);
    let timers = [];

    const reset = () => {
      timers.forEach(clearTimeout);
      timers = [];
      root.classList.remove("is-done");
      lines.forEach((l) => l.classList.remove("is-on"));
    };

    const run = () => {
      reset();
      if (reduceMotion) {
        lines.forEach((l) => l.classList.add("is-on"));
        root.classList.add("is-done");
        return;
      }
      lines.forEach((line, i) => timers.push(setTimeout(() => line.classList.add("is-on"), 400 + i * 650)));
      timers.push(setTimeout(() => root.classList.add("is-done"), 400 + lines.length * 650 + 250));
    };

    replay.addEventListener("click", run);

    if ("IntersectionObserver" in window) {
      const once = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting) {
            once.disconnect();
            run();
          }
        },
        { threshold: 0.35 }
      );
      once.observe(root);
    } else {
      run();
    }
  });
  /* ---------- Botón "Correo": copia la dirección y avisa ---------- */
  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      try {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.setAttribute("readonly", "");
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.append(ta);
        ta.select();
        const ok = document.execCommand("copy");
        ta.remove();
        return ok;
      } catch {
        return false;
      }
    }
  };

  $$("[data-email-link]").forEach((link) => {
    link.href = `mailto:${CONTACT_EMAIL}`; // clic con Ctrl/Cmd o menú contextual abre el programa de correo
    const label = $("#texto-correo", link) || link;
    const original = label.textContent;
    let timer;

    link.addEventListener("click", async (e) => {
      e.preventDefault();
      const copied = await copyToClipboard(CONTACT_EMAIL);
      if (!copied) {
        window.location.href = `mailto:${CONTACT_EMAIL}`; // plan B si el navegador bloquea el portapapeles
        return;
      }
      clearTimeout(timer);
      label.textContent = `¡Copiado! ${CONTACT_EMAIL}`;
      link.classList.add("is-copied");
      timer = setTimeout(() => {
        label.textContent = original;
        link.classList.remove("is-copied");
      }, 2400);
    });
  });
})();
