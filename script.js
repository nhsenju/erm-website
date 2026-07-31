(function(){
  "use strict";

  // ====== CONFIG ======
  const WEBHOOK_URL = ""; // <-- incolla qui l'URL webhook (n8n / Make / Zapier / Sheets / CRM)
  window.dataLayer = window.dataLayer || [];
  const dl = (event, payload) => window.dataLayer.push(Object.assign({event}, payload || {}));

  // ====== SESSION / LEAD META (in-memory, niente localStorage) ======
  const qs = new URLSearchParams(location.search);
  const uuid = crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2);
  const sessionId = uuid;
  const meta = {
    lead_uuid: uuid,
    session_id: sessionId,
    landing_url: location.href,
    referrer: document.referrer || "direct",
    utm_source: qs.get("utm_source") || "",
    utm_medium: qs.get("utm_medium") || "",
    utm_campaign: qs.get("utm_campaign") || "",
    utm_content: qs.get("utm_content") || "",
    gclid: qs.get("gclid") || "",
    fbclid: qs.get("fbclid") || "",
    ttclid: qs.get("ttclid") || "",
    msclkid: qs.get("msclkid") || "",
    device: /Mobi/i.test(navigator.userAgent) ? "mobile" : "desktop",
    browser: navigator.userAgent,
    viewport: `${innerWidth}x${innerHeight}`,
    language: navigator.language,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    started_at: new Date().toISOString()
  };
  Object.entries(meta).forEach(([k, v]) => { const el = document.getElementById(k); if (el) el.value = v; });
  dl("page_view", meta);

  // ====== SCROLL / CTA TRACKING ======
  let maxScroll = 0;
  addEventListener("scroll", () => {
    const pct = Math.round((scrollY / (document.body.scrollHeight - innerHeight)) * 100);
    if (pct > maxScroll) { maxScroll = pct; if (maxScroll % 25 === 0) dl("scroll_depth", { percent: maxScroll, lead_uuid: uuid }); }
  }, { passive: true });

  document.querySelectorAll("[data-track]").forEach(el => {
    el.addEventListener("click", () => dl("cta_click", { label: el.dataset.track, lead_uuid: uuid }));
  });

  // ====== WIZARD ======
  const form = document.getElementById("leadForm");
  if (!form) return; // pagina senza form (es. servizi, chi-siamo, contatti)
  const panels = [...form.querySelectorAll(".step-panel")];
  const total = panels.length;
  let step = 1;
  let furthestStep = 1;
  const answers = { cliente: "", servizio: "" };

  const progressBar = document.getElementById("progressBar");
  const btnBack = document.getElementById("btnBack");
  const btnNext = document.getElementById("btnNext");
  const btnSubmit = document.getElementById("btnSubmit");

  function render() {
    panels.forEach(p => p.hidden = Number(p.dataset.step) !== step);
    progressBar.style.width = (step / total * 100) + "%";
    progressBar.closest(".progress").setAttribute("aria-valuenow", step);
    btnBack.hidden = step === 1;
    btnNext.hidden = step === total;
    btnSubmit.hidden = step !== total;
    const panel = panels[step - 1];
    const focusable = panel.querySelector("input,textarea,button");
    if (focusable) focusable.focus({ preventScroll: true });
    dl("step_view", { step, lead_uuid: uuid });
  }

  function setError(id, msg) { const el = document.getElementById("err-" + id); if (el) el.textContent = msg || ""; }

  function validateStep(n) {
    if (n === 1) return !!answers.cliente || (setError("cliente", "Seleziona un'opzione."), false);
    if (n === 2) return !!answers.servizio || (setError("servizio", "Seleziona un'opzione."), false);
    if (n === 3) {
      const v = document.getElementById("descrizione").value.trim();
      setError("descrizione", v ? "" : "Descrivi brevemente il lavoro.");
      return !!v;
    }
    if (n === 4) {
      const v = document.getElementById("indirizzo").value.trim();
      setError("indirizzo", v ? "" : "Indica dove si trova.");
      return !!v;
    }
    if (n === 5) return true; // foto opzionale
    if (n === 6) {
      const nome = document.getElementById("nome").value.trim();
      const tel = document.getElementById("telefono").value.trim();
      const email = document.getElementById("email").value.trim();
      const privacy = document.getElementById("privacy").checked;
      let ok = true;
      if (!nome) { setError("nome", "Inserisci nome e cognome."); ok = false; } else setError("nome", "");
      if (!/^[+\d][\d\s]{6,}$/.test(tel)) { setError("telefono", "Numero di telefono non valido."); ok = false; } else setError("telefono", "");
      if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setError("email", "Email non valida."); ok = false; } else setError("email", "");
      if (!privacy) { setError("privacy", "Devi accettare la privacy policy."); ok = false; } else setError("privacy", "");
      return ok;
    }
    return true;
  }

  form.querySelectorAll(".choice").forEach(btn => {
    btn.addEventListener("click", () => {
      const field = btn.dataset.field;
      answers[field] = btn.dataset.value;
      btn.parentElement.querySelectorAll(".choice").forEach(b => b.classList.remove("is-selected"));
      btn.classList.add("is-selected");
      setError(field, "");
      setTimeout(() => btnNext.click(), 150);
    });
  });

  btnNext.addEventListener("click", () => {
    if (!validateStep(step)) return;
    if (step < total) { step++; furthestStep = Math.max(furthestStep, step); render(); }
  });
  btnBack.addEventListener("click", () => { if (step > 1) { step--; render(); } });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!validateStep(6)) return;
    btnSubmit.disabled = true;
    btnSubmit.textContent = "Invio in corso…";

    const payload = Object.assign({}, meta, {
      cliente: answers.cliente,
      servizio: answers.servizio,
      descrizione: document.getElementById("descrizione").value.trim(),
      indirizzo: document.getElementById("indirizzo").value.trim(),
      nome: document.getElementById("nome").value.trim(),
      telefono: document.getElementById("telefono").value.trim(),
      email: document.getElementById("email").value.trim(),
      compilation_time_s: Math.round((Date.now() - Date.parse(meta.started_at)) / 1000),
      submitted_at: new Date().toISOString()
    });

    // honeypot: se compilato, blocca silenziosamente come "successo" (anti-bot)
    if (document.getElementById("website").value) {
      showSuccess();
      return;
    }

    try {
      // Invio a Netlify Forms (rilevato a build-time dal form statico in index.html)
      const encoded = Object.entries(Object.assign({ "form-name": "preventivo" }, payload))
        .map(([k, v]) => encodeURIComponent(k) + "=" + encodeURIComponent(v))
        .join("&");
      await fetch("/", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: encoded
      });

      // Webhook opzionale duplicato (CRM/n8n/Sheets), non bloccante
      if (WEBHOOK_URL) {
        fetch(WEBHOOK_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        }).catch(() => {});
      }

      dl("generate_lead", payload);
      // Meta Conversion API / Google Ads Enhanced Conversion: inviare server-side con payload.email/telefono hashati.
      showSuccess();
    } catch (err) {
      dl("form_error", { lead_uuid: uuid, message: String(err) });
      btnSubmit.disabled = false;
      btnSubmit.textContent = "Ricevi Preventivo Gratuito";
      alert("Invio non riuscito. Riprova o chiamaci direttamente.");
    }
  });

  function showSuccess() {
    form.hidden = true;
    document.querySelector(".progress").hidden = true;
    document.getElementById("successPanel").hidden = false;
  }

  // ====== DROP-OFF TRACKING ======
  addEventListener("beforeunload", () => {
    if (!document.getElementById("successPanel").hidden) return;
    dl("form_abandon", { last_step: step, lead_uuid: uuid });
  });

  render();
})();
