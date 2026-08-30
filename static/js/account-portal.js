// static/js/account-portal.js
//
// Business account portal (apps/userprofile/templates/core/accountPages/*.html):
//   1. Custom file-upload previews (logo + gallery add tile) — the native
//      <input type="file"> stays functionally in charge (still what the
//      surrounding <form> submits), just visually hidden and wrapped in a
//      <label> so clicking the styled tile opens the OS file picker, with
//      a live blob-URL preview swapped in on selection.
//   2. The "Dekning" (coverage) pill-button grid — saved instantly via
//      fetch() on every click, no submit/reload, matching the become-a-
//      partner wizard's own pill-button look exactly (same wizard.css
//      classes) but wired to apps.userprofile.views.update_business_coverage
//      instead of a multi-step form.

(function () {
  "use strict";

  function getCsrfToken() {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  /** Briefly shows a small "Lagret"/"Kunne ikke lagre" pill next to `el`. */
  function showSaveFeedback(el, ok) {
    const pill = document.createElement("span");
    pill.className = "portal-save-feedback" + (ok ? "" : " portal-save-feedback--error");
    pill.textContent = ok ? "Lagret" : "Kunne ikke lagre";
    el.insertAdjacentElement("afterend", pill);
    requestAnimationFrame(() => pill.classList.add("is-visible"));
    setTimeout(() => {
      pill.classList.remove("is-visible");
      setTimeout(() => pill.remove(), 200);
    }, 1400);
  }

  /** Wires up every [data-upload-tile] — swaps in a live preview <img> the moment a file is chosen. */
  function initUploadPreviews() {
    document.querySelectorAll("[data-upload-tile]").forEach((tile) => {
      const input = tile.querySelector("input[type=file]");
      if (!input) return;

      input.addEventListener("change", () => {
        const file = input.files && input.files[0];
        if (!file) return;

        const url = URL.createObjectURL(file);
        let preview = tile.querySelector("[data-upload-preview]");
        if (!preview) {
          preview = document.createElement("img");
          preview.setAttribute("data-upload-preview", "");
          tile.prepend(preview);
        }
        preview.src = url;
        tile.classList.add("has-preview");
      });
    });
  }

  /** Wires up the Dekning pill-button grids to save on every toggle, no submit/reload. */
  function initCoverageAjaxSave() {
    const form = document.querySelector("[data-coverage-form]");
    if (!form) return;
    const feedbackAnchor = form.querySelector("[data-coverage-feedback-anchor]");

    form.addEventListener("change", async (event) => {
      if (!event.target.matches('input[type="checkbox"]')) return;

      const formData = new FormData(form);
      try {
        const response = await fetch(form.dataset.coverageForm, {
          method: "POST",
          headers: { "X-CSRFToken": getCsrfToken() },
          body: formData,
        });
        const data = response.ok ? await response.json() : { ok: false };
        showSaveFeedback(feedbackAnchor, Boolean(data.ok));
      } catch {
        showSaveFeedback(feedbackAnchor, false);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initUploadPreviews();
    initCoverageAjaxSave();
  });
})();
