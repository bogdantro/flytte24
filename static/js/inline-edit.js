// static/js/inline-edit.js
//
// Staff-only: makes every [data-inline-field] element on a live page
// (currently just the home page — see apps/core/views.py `home` and
// apps/core/templates/core/home.html) directly editable in place, saving
// each field individually via the dashboard's section_inline_update
// endpoint. Only loaded when the logged-in user is staff and viewing a
// page that has a real Page/PageSection row behind it.

(function () {
  "use strict";

  /** Reads the csrftoken cookie Django sets (forced via get_token() in the home() view, since this page has no <form> of its own). */
  function getCsrfToken() {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  /** Briefly shows a small "Lagret"/"Kunne ikke lagre" pill next to the edited element. */
  function showSaveFeedback(el, ok) {
    const pill = document.createElement("span");
    pill.className = "inline-edit-feedback" + (ok ? "" : " inline-edit-feedback--error");
    pill.textContent = ok ? "Lagret" : "Kunne ikke lagre";
    el.insertAdjacentElement("afterend", pill);
    requestAnimationFrame(() => pill.classList.add("is-visible"));
    setTimeout(() => {
      pill.classList.remove("is-visible");
      setTimeout(() => pill.remove(), 200);
    }, 1400);
  }

  /** POSTs one field's new value to the dashboard, showing save feedback either way. */
  async function saveField(el) {
    const sectionId = el.dataset.inlineSection;
    const field = el.dataset.inlineField;
    const value = el.innerText.trim();

    if (!sectionId) {
      showSaveFeedback(el, false);
      return;
    }

    try {
      const response = await fetch(`/dashboard/sider/seksjon/${sectionId}/felt/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({ field, value }),
      });
      const data = response.ok ? await response.json() : { ok: false };
      showSaveFeedback(el, Boolean(data.ok));
    } catch {
      showSaveFeedback(el, false);
    }
  }

  /** Wires up blur-to-save and Enter-to-blur on every editable field. Single-line fields (everything except body_text) submit on Enter instead of inserting a newline. */
  function initInlineEdit() {
    document.querySelectorAll("[data-inline-field]").forEach((el) => {
      let lastSaved = el.innerText.trim();

      el.addEventListener("blur", () => {
        const current = el.innerText.trim();
        if (current === lastSaved) return; // nothing changed, skip the round trip
        lastSaved = current;
        saveField(el);
      });

      if (el.dataset.inlineField !== "body_text") {
        el.addEventListener("keydown", (event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            el.blur();
          }
        });
      }
    });
  }

  document.addEventListener("DOMContentLoaded", initInlineEdit);
})();
