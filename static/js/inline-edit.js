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
  function showSaveFeedback(el, ok, message) {
    const pill = document.createElement("span");
    pill.className = "inline-edit-feedback" + (ok ? "" : " inline-edit-feedback--error");
    pill.textContent = message || (ok ? "Lagret" : "Kunne ikke lagre");
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
      // data-inline-section renders empty when this section_type has no
      // matching PageSection row for the current page (a dict-key miss
      // resolves to "" in the template) — distinct from a real save
      // failure, so say so plainly instead of the generic error, which
      // used to contradict the page's own "lagres automatisk" banner with
      // no explanation of why this one field never actually saved.
      showSaveFeedback(el, false, "Denne seksjonen finnes ikke ennå");
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

  /** Wires up each CTA's small pencil "edit link" button — button_href can't be made
   * contenteditable in place the way a label's text can, so this prompts for the new
   * URL instead and saves it through the same per-field endpoint as saveField(). */
  function initInlineEditLinks() {
    document.querySelectorAll(".inline-edit-link-btn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const sectionId = btn.dataset.inlineSection;
        const field = btn.dataset.inlineField;
        const current = btn.dataset.inlineCurrent || "";
        const next = window.prompt("Lenke (f.eks. /flytteforesporsel/):", current);
        if (next === null || next.trim() === current) return; // cancelled or unchanged

        try {
          const response = await fetch(`/dashboard/sider/seksjon/${sectionId}/felt/`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify({ field, value: next.trim() }),
          });
          const data = response.ok ? await response.json() : { ok: false };
          if (data.ok) {
            btn.dataset.inlineCurrent = next.trim();
            // home.html always renders this button as the <a>'s immediate next
            // sibling (see _inline_edit_link.html's call sites), so update that
            // one anchor's href live rather than waiting for a page reload.
            const anchor = btn.previousElementSibling;
            if (anchor && anchor.tagName === "A") anchor.setAttribute("href", next.trim());
            showSaveFeedback(btn, true);
          } else {
            showSaveFeedback(btn, false);
          }
        } catch {
          showSaveFeedback(btn, false);
        }
      });
    });
  }

  /** Wires up the "Sideinnstillinger" slide-over panel — title/SEO fields, which have no on-page visual spot to be contenteditable in place. */
  function initPageSettingsPanel() {
    const panel = document.querySelector("[data-page-settings-panel]");
    const openBtn = document.querySelector("[data-page-settings-open]");
    if (!panel || !openBtn) return;

    const closeBtn = panel.querySelector("[data-page-settings-close]");
    const saveBtn = panel.querySelector("[data-page-settings-save]");
    const feedback = panel.querySelector("[data-page-settings-feedback]");
    const pageId = panel.dataset.pageId;

    openBtn.addEventListener("click", () => { panel.hidden = false; });
    closeBtn.addEventListener("click", () => { panel.hidden = true; });

    saveBtn.addEventListener("click", async () => {
      const fields = {};
      panel.querySelectorAll("[data-page-field]").forEach((input) => {
        fields[input.dataset.pageField] = input.value.trim();
      });

      feedback.textContent = "Lagrer …";
      try {
        const response = await fetch(`/dashboard/sider/${pageId}/metadata/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
          },
          body: JSON.stringify(fields),
        });
        const data = response.ok ? await response.json() : { ok: false };
        feedback.textContent = data.ok ? "Lagret" : "Kunne ikke lagre";
      } catch {
        feedback.textContent = "Kunne ikke lagre";
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initInlineEdit();
    initInlineEditLinks();
    initPageSettingsPanel();
  });
})();
