// static/js/dashboard.js
//
// Staff dashboard JS — sidebar icon hydration, and a confirm dialog in
// front of every permanent-delete form across the dashboard.

(function () {
  "use strict";

  /** Clones the matching <symbol> from _icon_sprite.html into every [data-icon] placeholder. Idempotent, same pattern as wizard.js/site.js. */
  function initIconSprite() {
    document.querySelectorAll("[data-icon]").forEach((el) => {
      if (el.querySelector("svg")) return; // already hydrated
      const name = el.getAttribute("data-icon");
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("width", "18");
      svg.setAttribute("height", "18");
      const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
      use.setAttribute("href", `#icon-${name}`);
      svg.appendChild(use);
      el.appendChild(svg);
    });
  }

  /** Blocks submission of any [data-confirm-delete] form until the user confirms in a native dialog. */
  function initDeleteConfirm() {
    document.querySelectorAll("[data-confirm-delete]").forEach((form) => {
      form.addEventListener("submit", (event) => {
        if (!window.confirm("Slette dette permanent? Dette kan ikke angres.")) {
          event.preventDefault();
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initIconSprite();
    initDeleteConfirm();
  });
})();
