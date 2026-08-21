// static/js/dashboard.js
//
// Staff dashboard JS — currently just a confirm dialog in front of the
// delete-lead form, since that action is permanent and irreversible.

(function () {
  "use strict";

  /** Blocks submission of any [data-confirm-delete] form until the user confirms in a native dialog. */
  function initDeleteConfirm() {
    document.querySelectorAll("[data-confirm-delete]").forEach((form) => {
      form.addEventListener("submit", (event) => {
        if (!window.confirm("Slette denne forespørselen permanent? Dette kan ikke angres.")) {
          event.preventDefault();
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", initDeleteConfirm);
})();
