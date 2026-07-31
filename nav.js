(function () {
  "use strict";
  const header = document.getElementById("siteHeader");
  const toggle = document.getElementById("navToggle");
  const list = document.getElementById("navList");
  if (!header || !toggle || !list) return;

  function close() {
    header.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Apri menu");
  }
  function open() {
    header.classList.add("is-open");
    toggle.setAttribute("aria-expanded", "true");
    toggle.setAttribute("aria-label", "Chiudi menu");
  }

  toggle.addEventListener("click", () => {
    header.classList.contains("is-open") ? close() : open();
  });

  list.querySelectorAll("a").forEach((a) => a.addEventListener("click", close));

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") close();
  });
})();
