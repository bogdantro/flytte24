// static/js/site.js
//
// Site-wide marketing-page JS (everything except /wizard/, which has its
// own wizard.js). Header mobile menu, header scroll state, FAQ accordion,
// and the postal-code box's redirect-into-the-wizard behavior.

(function () {
  "use strict";

  /** Clones the matching <symbol> from the icon sprite into every not-yet-hydrated [data-icon] placeholder. */
  function initIconSprite() {
    document.querySelectorAll("[data-icon]").forEach((el) => {
      if (el.querySelector("svg")) return;
      const name = el.getAttribute("data-icon");
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("width", "16");
      svg.setAttribute("height", "16");
      const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
      use.setAttribute("href", `#icon-${name}`);
      svg.appendChild(use);
      el.appendChild(svg);
    });
  }

  /** Wires up the header's "Meny" button to show/hide the links list on mobile. */
  function initSiteHeader() {
    const toggle = document.querySelector("[data-site-header-toggle]");
    const links = document.querySelector("[data-site-header-links]");
    if (!toggle || !links) return;

    toggle.addEventListener("click", () => {
      const isOpen = links.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(isOpen));
    });

    // A link click navigates away anyway, but closing first avoids a flash
    // of the open menu if the destination page is served from cache.
    links.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        links.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  /** Toggles .is-scrolled on the header past an 8px scroll threshold (spec §4.1). */
  function initHeaderScrollState() {
    const header = document.querySelector("[data-site-header]");
    if (!header) return;

    const update = () => {
      header.classList.toggle("is-scrolled", window.scrollY > 8);
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
  }

  /** Wires up every [data-faq] accordion on the page — single-open-at-a-time, Plus/Minus icon swap. */
  function initFaqAccordions() {
    document.querySelectorAll("[data-faq]").forEach((faq) => {
      const items = Array.from(faq.querySelectorAll("[data-faq-item]"));
      items.forEach((item) => {
        const button = item.querySelector("[data-faq-trigger]");
        button.addEventListener("click", () => {
          const isOpen = item.classList.contains("is-open");
          items.forEach((other) => other.classList.remove("is-open"));
          if (!isOpen) item.classList.add("is-open");
        });
      });
    });
  }

  /** Wires up every [data-postnummer-form] to validate a 4-digit postal code and
   * redirect into the wizard via the server-side resolver (apps.leads.views
   * start_from_postal_code), which looks the code up against Kartverket's
   * address registry and pre-fills "Fra adresse" with a real area name
   * (e.g. "1170 Oslo") instead of the bare digits when it can. */
  function initPostnummerForms() {
    document.querySelectorAll("[data-postnummer-form]").forEach((form) => {
      const input = form.querySelector("[data-postnummer-input]");
      const error = form.querySelector("[data-postnummer-error]");

      form.addEventListener("submit", (event) => {
        event.preventDefault();
        const value = input.value.trim();
        const isValid = /^\d{4}$/.test(value);
        error.hidden = isValid;
        if (!isValid) return;
        window.location.href = `/flytteforesporsel/start-fra-postnummer/${encodeURIComponent(value)}/`;
      });

      // Digits only, capped at 4 — matches the reference's onChange filter.
      input.addEventListener("input", () => {
        input.value = input.value.replace(/\D/g, "").slice(0, 4);
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initIconSprite();
    initSiteHeader();
    initHeaderScrollState();
    initFaqAccordions();
    initPostnummerForms();
  });
})();
