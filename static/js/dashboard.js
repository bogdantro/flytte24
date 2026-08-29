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

  /** In the lead "Tildel til bedrifter" panel, disables each business option
   * in the other two selects once it's picked in one of them, so the same
   * business can't be assigned to a lead twice. Server-side rejects the
   * duplicate too (dashboard:lead_assign_businesses) — this is just so
   * staff see it before submitting rather than after a redirect. */
  function initAssignSelects() {
    const selects = document.querySelectorAll("[data-assign-select]");
    if (!selects.length) return;

    function sync() {
      const chosen = Array.from(selects)
        .map((s) => s.value)
        .filter((v) => v);
      selects.forEach((select) => {
        Array.from(select.options).forEach((option) => {
          if (!option.value) return; // "— Ikke tildelt —" always enabled
          option.disabled = chosen.includes(option.value) && option.value !== select.value;
        });
      });
    }

    selects.forEach((select) => select.addEventListener("change", sync));
    sync();
  }

  /** The lead list's header checkbox ([data-select-all]) toggles every
   * [name=lead_ids] checkbox on the page, so the bulk-action bar can act on
   * "every row currently visible" without checking each one by hand. */
  function initSelectAll() {
    document.querySelectorAll("[data-select-all]").forEach((selectAll) => {
      selectAll.addEventListener("change", () => {
        document.querySelectorAll('input[name="lead_ids"]').forEach((box) => {
          box.checked = selectAll.checked;
        });
      });
    });
  }

  /** [data-copy] buttons copy their value to the clipboard and briefly show
   * confirmation — used for phone/email on the lead detail page so staff
   * don't have to select-and-copy free text by hand. */
  function initCopyButtons() {
    document.querySelectorAll("[data-copy]").forEach((button) => {
      button.addEventListener("click", () => {
        const value = button.getAttribute("data-copy");
        const done = () => {
          const original = button.textContent;
          button.textContent = "Kopiert!";
          button.classList.add("is-copied");
          setTimeout(() => {
            button.textContent = original;
            button.classList.remove("is-copied");
          }, 1500);
        };
        if (navigator.clipboard && window.isSecureContext) {
          navigator.clipboard.writeText(value).then(done).catch(() => {});
        } else {
          // Fallback for non-HTTPS/older browsers: a hidden textarea + execCommand.
          const scratch = document.createElement("textarea");
          scratch.value = value;
          scratch.style.position = "fixed";
          scratch.style.opacity = "0";
          document.body.appendChild(scratch);
          scratch.select();
          try {
            document.execCommand("copy");
            done();
          } catch (err) {
            // Clipboard unavailable — silently no-op rather than throw.
          }
          document.body.removeChild(scratch);
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initIconSprite();
    initDeleteConfirm();
    initAssignSelects();
    initSelectAll();
    initCopyButtons();
  });
})();
