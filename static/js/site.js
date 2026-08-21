// static/js/site.js
//
// Site-wide marketing-page JS (everything except /wizard/, which has its
// own wizard.js). Currently just the header's mobile menu toggle.

(function () {
  "use strict";

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

  document.addEventListener("DOMContentLoaded", initSiteHeader);
})();
