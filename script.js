(function () {
  "use strict";

  // ============================================================
  // CONFIG
  // ============================================================

  window.dataLayer = window.dataLayer || [];

  const dl = (event, payload) => {
    window.dataLayer.push(
      Object.assign(
        {
          event: event
        },
        payload || {}
      )
    );
  };

  // ============================================================
  // SESSION / LEAD META
  // ============================================================

  const qs = new URLSearchParams(location.search);

  const uuid =
    crypto && crypto.randomUUID
      ? crypto.randomUUID()
      : String(Date.now()) + Math.random().toString(16).slice(2);

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
    viewport: innerWidth + "x" + innerHeight,
    language: navigator.language,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    started_at: new Date().toISOString()
  };

  Object.entries(meta).forEach(([key, value]) => {
    const element = document.getElementById(key);

    if (element) {
      element.value = value;
    }
  });

  dl("page_view", meta);

  // ============================================================
  // SCROLL TRACKING
  // ============================================================

  let maxScroll = 0;

  addEventListener(
    "scroll",
    () => {
      const denominator = document.body.scrollHeight - innerHeight;

      if (denominator <= 0) {
        return;
      }

      const percent = Math.round((scrollY / denominator) * 100);

      if (percent > maxScroll) {
        maxScroll = percent;

        if (maxScroll % 25 === 0) {
          dl("scroll_depth", {
            percent: maxScroll,
            lead_uuid: uuid
          });
        }
      }
    },
    {
      passive: true
    }
  );

  // ============================================================
  // CTA TRACKING
  // ============================================================

  document.querySelectorAll("[data-track]").forEach((element) => {
    element.addEventListener("click", () => {
      dl("cta_click", {
        label: element.dataset.track,
        lead_uuid: uuid
      });
    });
  });

  // ============================================================
  // WIZARD
  // ============================================================

  const form = document.getElementById("leadForm");

  if (!form) {
    return;
  }

  const panels = [
    ...form.querySelectorAll(".step-panel")
  ];

  const total = panels.length;

  let step = 1;
  let furthestStep = 1;

  const answers = {
    cliente: "",
    servizio: ""
  };

  const progressBar =
    document.getElementById("progressBar");

  const btnBack =
    document.getElementById("btnBack");

  const btnNext =
    document.getElementById("btnNext");

  const btnSubmit =
    document.getElementById("btnSubmit");

  const successPanel =
    document.getElementById("successPanel");

  if (
    !progressBar ||
    !btnBack ||
    !btnNext ||
    !btnSubmit
  ) {
    console.error(
      "Wizard ERMETES: elementi pulsante/progress mancanti."
    );

    return;
  }

  // ============================================================
  // HELPERS
  // ============================================================

  function getValue(id) {
    const element = document.getElementById(id);

    return element
      ? element.value.trim()
      : "";
  }

  function setError(id, message) {
    const error = document.getElementById(
      "err-" + id
    );

    if (error) {
      error.textContent = message || "";
    }

    const field = document.getElementById(id);

    if (field) {
      if (message) {
        field.setAttribute(
          "aria-invalid",
          "true"
        );
      } else {
        field.removeAttribute(
          "aria-invalid"
        );
      }
    }
  }

  function clearStepErrors(n) {
    const panel = panels[n - 1];

    if (!panel) {
      return;
    }

    panel
      .querySelectorAll(".err")
      .forEach((element) => {
        element.textContent = "";
      });

    panel
      .querySelectorAll("[aria-invalid]")
      .forEach((element) => {
        element.removeAttribute(
          "aria-invalid"
        );
      });
  }

  function focusFirstInvalid(panel) {
    if (!panel) {
      return;
    }

    const invalid = panel.querySelector(
      '[aria-invalid="true"]'
    );

    if (invalid) {
      invalid.focus({
        preventScroll: true
      });
    }
  }

  function normalizeSpaces(value) {
    return value
      .replace(/\s+/g, " ")
      .trim();
  }

  // ============================================================
  // VALIDAZIONE GENERALE
  // ============================================================

  function validateName(value) {
    const normalized =
      normalizeSpaces(value);

    if (!normalized) {
      return "Inserisci nome e cognome.";
    }

    if (normalized.length < 5) {
      return "Inserisci nome e cognome completi.";
    }

    if (normalized.length > 80) {
      return "Il nome è troppo lungo.";
    }

    const words = normalized.split(" ");

    if (words.length < 2) {
      return "Inserisci nome e cognome.";
    }

    if (!/^[A-Za-zÀ-ÖØ-öø-ÿ'’-]+(?:\s+[A-Za-zÀ-ÖØ-öø-ÿ'’-]+)+$/.test(normalized)) {
      return "Usa un nome e cognome validi.";
    }

    return "";
  }

  function validatePhone(value) {
    const normalized =
      value.replace(/[()\-.]/g, " ").replace(/\s+/g, " ").trim();

    if (!normalized) {
      return "Inserisci il numero di telefono.";
    }

    if (!/^\+?[\d\s]{7,20}$/.test(normalized)) {
      return "Inserisci un numero di telefono valido.";
    }

    const digits =
      normalized.replace(/\D/g, "");

    if (digits.length < 7) {
      return "Il numero di telefono è troppo corto.";
    }

    if (digits.length > 15) {
      return "Il numero di telefono è troppo lungo.";
    }

    return "";
  }

  function validateEmail(value) {
    if (!value) {
      return "";
    }

    if (value.length > 254) {
      return "L'email è troppo lunga.";
    }

    if (/\s/.test(value)) {
      return "L'email non può contenere spazi.";
    }

    const emailPattern =
      /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

    if (!emailPattern.test(value)) {
      return "Inserisci un indirizzo email valido.";
    }

    const parts = value.split("@");

    if (
      parts.length !== 2 ||
      !parts[0] ||
      !parts[1]
    ) {
      return "Inserisci un indirizzo email valido.";
    }

    if (
      parts[0].startsWith(".") ||
      parts[0].endsWith(".") ||
      parts[0].includes("..")
    ) {
      return "Inserisci un indirizzo email valido.";
    }

    if (
      parts[1].startsWith(".") ||
      parts[1].endsWith(".") ||
      parts[1].includes("..")
    ) {
      return "Inserisci un indirizzo email valido.";
    }

    return "";
  }

  function validateDescription(value) {
    const normalized =
      normalizeSpaces(value);

    if (!normalized) {
      return "Descrivi brevemente il lavoro.";
    }

    if (normalized.length < 10) {
      return "Descrivi il lavoro con qualche dettaglio in più.";
    }

    if (normalized.length > 1000) {
      return "La descrizione è troppo lunga.";
    }

    const letters =
      normalized.match(/[A-Za-zÀ-ÖØ-öø-ÿ]/g);

    if (!letters || letters.length < 5) {
      return "Inserisci una descrizione reale del lavoro.";
    }

    return "";
  }

  function validateAddress(value) {
    const normalized =
      normalizeSpaces(value);

    if (!normalized) {
      return "Indica dove si trova.";
    }

    if (normalized.length < 5) {
      return "Inserisci un indirizzo più completo.";
    }

    if (normalized.length > 200) {
      return "L'indirizzo è troppo lungo.";
    }

    const letters =
      normalized.match(/[A-Za-zÀ-ÖØ-öø-ÿ]/g);

    if (!letters || letters.length < 3) {
      return "Inserisci un indirizzo valido.";
    }

    return "";
  }

  function validatePhoto() {
    const photo =
      document.getElementById("foto");

    if (!photo || !photo.files || !photo.files.length) {
      return "";
    }

    const file = photo.files[0];

    if (!file.type.startsWith("image/")) {
      return "Seleziona un'immagine valida.";
    }

    const maxSize =
      10 * 1024 * 1024;

    if (file.size > maxSize) {
      return "La foto deve essere inferiore a 10 MB.";
    }

    return "";
  }

  // ============================================================
  // VALIDAZIONE STEP
  // ============================================================

  function validateStep(n) {
    clearStepErrors(n);

    if (n === 1) {
      if (!answers.cliente) {
        setError(
          "cliente",
          "Seleziona un'opzione."
        );

        return false;
      }

      return true;
    }

    if (n === 2) {
      if (!answers.servizio) {
        setError(
          "servizio",
          "Seleziona il servizio che ti serve."
        );

        return false;
      }

      return true;
    }

    if (n === 3) {
      const value =
        getValue("descrizione");

      const error =
        validateDescription(value);

      setError(
        "descrizione",
        error
      );

      return !error;
    }

    if (n === 4) {
      const value =
        getValue("indirizzo");

      const error =
        validateAddress(value);

      setError(
        "indirizzo",
        error
      );

      return !error;
    }

    if (n === 5) {
      const error =
        validatePhoto();

      if (error) {
        const photo =
          document.getElementById("foto");

        if (photo) {
          photo.setAttribute(
            "aria-invalid",
            "true"
          );

          photo.focus({
            preventScroll: true
          });
        }
      }

      return !error;
    }

    if (n === 6) {
      let ok = true;

      const nome =
        getValue("nome");

      const telefono =
        getValue("telefono");

      const email =
        getValue("email");

      const privacy =
        document.getElementById("privacy");

      const nameError =
        validateName(nome);

      if (nameError) {
        setError(
          "nome",
          nameError
        );

        ok = false;
      }

      const phoneError =
        validatePhone(telefono);

      if (phoneError) {
        setError(
          "telefono",
          phoneError
        );

        ok = false;
      }

      const emailError =
        validateEmail(email);

      if (emailError) {
        setError(
          "email",
          emailError
        );

        ok = false;
      }

      if (!privacy || !privacy.checked) {
        setError(
          "privacy",
          "Devi accettare la privacy policy."
        );

        ok = false;
      }

      return ok;
    }

    return true;
  }

  // ============================================================
  // STATO CTA
  // ============================================================

  function updateSubmitState() {
  if (step !== total) {
    btnNext.hidden = false;
    btnSubmit.hidden = true;
    return;
  }

  const nome = document.getElementById("nome").value.trim();
  const tel = document.getElementById("telefono").value.trim();
  const privacy = document.getElementById("privacy").checked;

  const validPhone = /^[+\d][\d\s().-]{6,}$/.test(tel);
  const complete = nome.length >= 2 && validPhone && privacy;

  // Ultimo step: Continua sempre nascosto
  btnNext.hidden = true;

  // Mostra Ricevi Preventivo solo quando il form è completo
  btnSubmit.hidden = !complete;
}

  // ============================================================
  // RENDER
  // ============================================================

  function render() {
    panels.forEach((panel) => {
      panel.hidden =
        Number(panel.dataset.step) !== step;
    });

    progressBar.style.width =
      (step / total * 100) + "%";

    const progress =
      progressBar.closest(".progress");

    if (progress) {
      progress.setAttribute(
        "aria-valuenow",
        step
      );
    }

    btnBack.hidden =
      step === 1;

    updateSubmitState();

    const panel =
      panels[step - 1];

    if (panel) {
      const focusable =
        panel.querySelector(
          "input, textarea, button"
        );

      if (focusable) {
        focusable.focus({
          preventScroll: true
        });
      }
    }

    dl("step_view", {
      step: step,
      lead_uuid: uuid
    });
  }

  // ============================================================
  // SCELTE STEP 1 / 2
  // ============================================================

  form.querySelectorAll(".choice").forEach((button) => {
    button.addEventListener("click", () => {
      const field =
        button.dataset.field;

      const value =
        button.dataset.value;

      if (!field || !value) {
        return;
      }

      answers[field] = value;

      const group =
        button.parentElement;

      if (group) {
        group
          .querySelectorAll(".choice")
          .forEach((other) => {
            other.classList.remove(
              "is-selected"
            );
          });
      }

      button.classList.add(
        "is-selected"
      );

      setError(
        field,
        ""
      );

      setTimeout(() => {
        if (step < total) {
          btnNext.click();
        }
      }, 150);
    });
  });

  // ============================================================
  // CONTINUA
  // ============================================================

  btnNext.addEventListener(
    "click",
    () => {
      if (!validateStep(step)) {
        focusFirstInvalid(
          panels[step - 1]
        );

        dl("validation_error", {
          step: step,
          lead_uuid: uuid
        });

        return;
      }

      if (step < total) {
        step++;

        furthestStep =
          Math.max(
            furthestStep,
            step
          );

        render();
      }
    }
  );

  // ============================================================
  // INDIETRO
  // ============================================================

  btnBack.addEventListener(
    "click",
    () => {
      if (step > 1) {
        step--;

        render();
      }
    }
  );

  // ============================================================
  // LIVE VALIDATION
  // ============================================================

  const nome =
    document.getElementById("nome");

  const telefono =
    document.getElementById("telefono");

  const email =
    document.getElementById("email");

  const privacy =
    document.getElementById("privacy");

  const descrizione =
    document.getElementById("descrizione");

  const indirizzo =
    document.getElementById("indirizzo");

  const foto =
    document.getElementById("foto");

  if (nome) {
    nome.addEventListener(
      "input",
      () => {
        const value =
          nome.value.trim();

        if (!value) {
          setError(
            "nome",
            ""
          );
        } else {
          setError(
            "nome",
            validateName(value)
          );
        }

        updateSubmitState();
      }
    );

    nome.addEventListener(
      "blur",
      () => {
        setError(
          "nome",
          validateName(
            nome.value.trim()
          )
        );

        updateSubmitState();
      }
    );
  }

  if (telefono) {
    telefono.addEventListener(
      "input",
      () => {
        const value =
          telefono.value.trim();

        if (!value) {
          setError(
            "telefono",
            ""
          );
        } else {
          setError(
            "telefono",
            validatePhone(value)
          );
        }

        updateSubmitState();
      }
    );

    telefono.addEventListener(
      "blur",
      () => {
        setError(
          "telefono",
          validatePhone(
            telefono.value.trim()
          )
        );

        updateSubmitState();
      }
    );
  }

  if (email) {
    email.addEventListener(
      "input",
      () => {
        const value =
          email.value.trim();

        if (!value) {
          setError(
            "email",
            ""
          );
        } else {
          setError(
            "email",
            validateEmail(value)
          );
        }

        updateSubmitState();
      }
    );

    email.addEventListener(
      "blur",
      () => {
        setError(
          "email",
          validateEmail(
            email.value.trim()
          )
        );

        updateSubmitState();
      }
    );
  }

  if (privacy) {
    privacy.addEventListener(
      "change",
      () => {
        setError(
          "privacy",
          privacy.checked
            ? ""
            : "Devi accettare la privacy policy."
        );

        updateSubmitState();
      }
    );
  }

  if (descrizione) {
    descrizione.addEventListener(
      "blur",
      () => {
        if (step !== 3) {
          return;
        }

        setError(
          "descrizione",
          validateDescription(
            descrizione.value
          )
        );
      }
    );
  }

  if (indirizzo) {
    indirizzo.addEventListener(
      "blur",
      () => {
        if (step !== 4) {
          return;
        }

        setError(
          "indirizzo",
          validateAddress(
            indirizzo.value
          )
        );
      }
    );
  }

  if (foto) {
    foto.addEventListener(
      "change",
      () => {
        const error =
          validatePhoto();

        if (error) {
          foto.setAttribute(
            "aria-invalid",
            "true"
          );
        } else {
          foto.removeAttribute(
            "aria-invalid"
          );
        }
      }
    );
  }

  // ============================================================
  // SUBMIT
  // ============================================================

  form.addEventListener(
    "submit",
    async (event) => {
      event.preventDefault();

      if (step !== total) {
        return;
      }

      if (!validateStep(6)) {
        updateSubmitState();

        focusFirstInvalid(
          panels[total - 1]
        );

        dl("validation_error", {
          step: 6,
          lead_uuid: uuid
        });

        return;
      }

      // Honeypot
      const website =
        document.getElementById("website");

      if (
        website &&
        website.value.trim()
      ) {
        showSuccess();
        return;
      }

      btnSubmit.disabled = true;
      btnSubmit.textContent =
        "Invio in corso…";

      const payload =
        Object.assign(
          {},
          meta,
          {
            cliente:
              answers.cliente,

            servizio:
              answers.servizio,

            descrizione:
              getValue("descrizione"),

            indirizzo:
              getValue("indirizzo"),

            nome:
              getValue("nome"),

            telefono:
              getValue("telefono"),

            email:
              getValue("email"),

            compilation_time_s:
              Math.round(
                (
                  Date.now() -
                  Date.parse(
                    meta.started_at
                  )
                ) / 1000
              ),

            submitted_at:
              new Date().toISOString()
          }
        );

      try {
        const formData =
          Object.assign(
            {
              "form-name":
                "preventivo"
            },
            payload
          );

        const encoded =
          Object.entries(formData)
            .map(
              ([key, value]) =>
                encodeURIComponent(key) +
                "=" +
                encodeURIComponent(
                  value == null
                    ? ""
                    : value
                )
            )
            .join("&");

        const response =
          await fetch(
            "/",
            {
              method: "POST",
              headers: {
                "Content-Type":
                  "application/x-www-form-urlencoded"
              },
              body: encoded
            }
          );

        if (!response.ok) {
          throw new Error(
            "Netlify Forms HTTP " +
              response.status
          );
        }

        // ========================================================
        // TRACKING LEAD
        // ========================================================

        dl(
          "generate_lead",
          payload
        );

        // ========================================================
        // SUCCESS
        // ========================================================

        showSuccess();

      } catch (error) {
        dl(
          "form_error",
          {
            lead_uuid: uuid,
            message: String(error)
          }
        );

        btnSubmit.disabled = false;

        btnSubmit.textContent =
          "Ricevi Preventivo Gratuito";

        btnSubmit.setAttribute(
          "aria-disabled",
          "false"
        );

        alert(
          "Invio non riuscito. Riprova o contattaci direttamente."
        );
      }
    }
  );

  // ============================================================
  // SUCCESS PANEL
  // ============================================================

  function showSuccess() {
    form.hidden = true;

    const progress =
      document.querySelector(
        ".progress"
      );

    if (progress) {
      progress.hidden = true;
    }

    if (successPanel) {
      successPanel.hidden = false;

      successPanel.scrollIntoView({
        behavior: "smooth",
        block: "center"
      });
    }
  }

  // ============================================================
  // DROP-OFF TRACKING
  // ============================================================

  addEventListener(
    "beforeunload",
    () => {
      if (
        successPanel &&
        !successPanel.hidden
      ) {
        return;
      }

      dl(
        "form_abandon",
        {
          last_step: step,
          furthest_step:
            furthestStep,
          lead_uuid: uuid
        }
      );
    }
  );

  // ============================================================
  // INITIAL RENDER
  // ============================================================

  render();
})();