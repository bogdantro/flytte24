// static/js/inline-edit.js
//
// Staff-only: makes every [data-inline-field] element on a live page
// (currently just the home page — see apps/core/views.py `home` and
// apps/core/templates/core/home.html) directly editable in place, saving
// each field individually via the dashboard's section_inline_update
// endpoint. Only loaded when the logged-in user is staff and viewing a
// page that has a real Page/PageSection row behind it.
//
// Three edit surfaces, in the order they're defined below:
//   1. Plain text (contenteditable spans/headings) — initInlineEdit()
//   2. A CTA's href (can't be contenteditable) — initInlineEditLinks()
//   3. One item inside a list-shaped section's extra_json (a FAQ pair, a
//      testimonial card, a service card, …) — initListItemEditing()
// (2) and (3) both go through the same custom popover component
// (openEditPopover) — never a native prompt()/alert()/confirm().

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

  // ---------------------------------------------------------------
  // Generic custom popover — a small form that appears near whatever
  // trigger opened it. Used by both the CTA-link editor and the list-item
  // editor below instead of window.prompt()/alert()/confirm() anywhere.
  // ---------------------------------------------------------------
  let popoverEl = null;

  /** Builds (once) and returns the single shared popover element, appended to <body>. */
  function getPopover() {
    if (popoverEl) return popoverEl;
    popoverEl = document.createElement("div");
    popoverEl.className = "inline-edit-popover";
    popoverEl.hidden = true;
    document.body.appendChild(popoverEl);
    document.addEventListener("mousedown", (event) => {
      if (!popoverEl.hidden && !popoverEl.contains(event.target) && !event.target.closest("[data-opens-popover]")) {
        closePopover();
      }
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !popoverEl.hidden) closePopover();
    });
    return popoverEl;
  }

  function closePopover() {
    if (popoverEl) popoverEl.hidden = true;
  }

  /**
   * Opens the popover near `triggerEl` with one form field per entry in
   * `fields` ({key, kind: "text"|"textarea"|"image", label, value}), an
   * optional `onDelete` (renders a "Slett" button), and `onSave(values)`
   * called with the text/textarea values on submit — image fields upload
   * immediately on file selection instead (via `onImageUpload(key, file)`),
   * since that's its own round trip rather than part of the saved form.
   */
  function openEditPopover({ triggerEl, title, fields, onSave, onDelete, onImageUpload }) {
    const popover = getPopover();
    popover.innerHTML = "";
    popover.dataset.opensPopover = "true"; // so the outside-click check above doesn't immediately re-close it

    const heading = document.createElement("p");
    heading.className = "inline-edit-popover__title";
    heading.textContent = title;
    popover.appendChild(heading);

    const form = document.createElement("form");
    form.className = "inline-edit-popover__form";
    const inputs = {};

    fields.forEach((field) => {
      const label = document.createElement("label");
      label.className = "inline-edit-popover__field";
      const span = document.createElement("span");
      span.textContent = field.label;
      label.appendChild(span);

      if (field.kind === "textarea") {
        const textarea = document.createElement("textarea");
        textarea.value = field.value || "";
        textarea.rows = 3;
        label.appendChild(textarea);
        inputs[field.key] = textarea;
      } else if (field.kind === "image") {
        if (field.value) {
          const preview = document.createElement("img");
          preview.className = "inline-edit-popover__preview";
          preview.src = field.value.startsWith("/") || field.value.startsWith("http")
            ? field.value
            : `/static/images/home/${field.value}`;
          preview.alt = "";
          label.appendChild(preview);
        }
        const fileInput = document.createElement("input");
        fileInput.type = "file";
        fileInput.accept = "image/*";
        fileInput.addEventListener("change", () => {
          if (fileInput.files && fileInput.files[0] && onImageUpload) {
            onImageUpload(field.key, fileInput.files[0]);
          }
        });
        label.appendChild(fileInput);
      } else {
        const input = document.createElement("input");
        input.type = "text";
        input.value = field.value || "";
        label.appendChild(input);
        inputs[field.key] = input;
      }
      form.appendChild(label);
    });

    const actions = document.createElement("div");
    actions.className = "inline-edit-popover__actions";

    if (onDelete) {
      const deleteBtn = document.createElement("button");
      deleteBtn.type = "button";
      deleteBtn.className = "inline-edit-popover__delete";
      deleteBtn.textContent = "Slett";
      deleteBtn.addEventListener("click", () => {
        onDelete();
        closePopover();
      });
      actions.appendChild(deleteBtn);
    }

    const cancelBtn = document.createElement("button");
    cancelBtn.type = "button";
    cancelBtn.className = "btn-outline";
    cancelBtn.textContent = "Avbryt";
    cancelBtn.addEventListener("click", closePopover);
    actions.appendChild(cancelBtn);

    const saveBtn = document.createElement("button");
    saveBtn.type = "submit";
    saveBtn.className = "btn-primary";
    saveBtn.textContent = "Lagre";
    actions.appendChild(saveBtn);

    form.appendChild(actions);
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const values = {};
      Object.entries(inputs).forEach(([key, el]) => { values[key] = el.value.trim(); });
      onSave(values);
      closePopover();
    });
    popover.appendChild(form);

    popover.hidden = false;
    const triggerRect = triggerEl.getBoundingClientRect();
    const top = window.scrollY + triggerRect.bottom + 8;
    let left = window.scrollX + triggerRect.left;
    const maxLeft = window.scrollX + document.documentElement.clientWidth - popover.offsetWidth - 12;
    left = Math.max(12, Math.min(left, maxLeft));
    popover.style.top = `${top}px`;
    popover.style.left = `${left}px`;

    const firstInput = form.querySelector("input, textarea");
    if (firstInput) firstInput.focus();
  }

  /** Wires up each CTA's small pencil "edit link" button — button_href can't be made
   * contenteditable in place the way a label's text can, so this opens the custom
   * popover instead of a native prompt(), saving through the same per-field endpoint
   * as saveField(). */
  function initInlineEditLinks() {
    document.querySelectorAll(".inline-edit-link-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const sectionId = btn.dataset.inlineSection;
        const field = btn.dataset.inlineField;
        const current = btn.dataset.inlineCurrent || "";

        openEditPopover({
          triggerEl: btn,
          title: "Rediger lenke",
          fields: [{ key: "href", kind: "text", label: "Lenke (f.eks. /flytteforesporsel/)", value: current }],
          onSave: async ({ href }) => {
            if (href === current) return;
            try {
              const response = await fetch(`/dashboard/sider/seksjon/${sectionId}/felt/`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": getCsrfToken() },
                body: JSON.stringify({ field, value: href }),
              });
              const data = response.ok ? await response.json() : { ok: false };
              if (data.ok) {
                btn.dataset.inlineCurrent = href;
                // home.html always renders this button as the <a>'s immediate next
                // sibling (see _inline_edit_link.html's call sites), so update that
                // one anchor's href live rather than waiting for a page reload.
                const anchor = btn.previousElementSibling;
                if (anchor && anchor.tagName === "A") anchor.setAttribute("href", href);
                showSaveFeedback(btn, true);
              } else {
                showSaveFeedback(btn, false);
              }
            } catch {
              showSaveFeedback(btn, false);
            }
          },
        });
      });
    });
  }

  // ---------------------------------------------------------------
  // Per-item editing for a list-shaped section (FAQ pairs, testimonial
  // cards, service cards, stat tiles, city links, how-it-works steps) —
  // every "[data-list-item]" card gets a small pencil + trash overlay in
  // edit mode, and every "[data-list-item-add]" button appends a new
  // default row. See apps/dashboard/views.py LIST_ITEM_FIELD_SPECS for the
  // authoritative per-section-type field list this mirrors.
  // ---------------------------------------------------------------
  const LIST_ITEM_FIELD_SPECS = {
    stats: [{ key: "value", kind: "text", label: "Verdi" }, { key: "label", kind: "text", label: "Etikett" }],
    how_it_works: [
      { key: "title", kind: "text", label: "Tittel" },
      { key: "body", kind: "textarea", label: "Tekst" },
      { key: "image", kind: "image", label: "Illustrasjon" },
    ],
    testimonials: [
      { key: "quote", kind: "textarea", label: "Sitat" },
      { key: "name", kind: "text", label: "Navn" },
      { key: "meta", kind: "text", label: "Undertekst" },
      { key: "image", kind: "image", label: "Bilde" },
    ],
    services: [{ key: "title", kind: "text", label: "Tittel" }, { key: "body", kind: "textarea", label: "Tekst" }],
    cities: [{ key: "name", kind: "text", label: "Bynavn" }, { key: "href", kind: "text", label: "Lenke" }],
    faq: [{ key: "question", kind: "text", label: "Spørsmål" }, { key: "answer", kind: "textarea", label: "Svar" }],
  };

  /** Reads a list-item card's current field values from its own data-field-<key> attributes (set server-side from the actual extra_json values — see home.html). */
  function readItemFields(card, spec) {
    return spec.map((field) => ({ ...field, value: card.dataset[`field${field.key[0].toUpperCase()}${field.key.slice(1)}`] || "" }));
  }

  function initListItemEditing() {
    document.querySelectorAll("[data-list-item]").forEach((card) => {
      const sectionId = card.dataset.inlineSection;
      const sectionType = card.dataset.sectionType;
      const index = Number(card.dataset.itemIndex);
      const spec = LIST_ITEM_FIELD_SPECS[sectionType];
      if (!sectionId || !spec) return;

      const editBtn = card.querySelector("[data-list-item-edit]");
      if (!editBtn) return;

      editBtn.addEventListener("click", () => {
        openEditPopover({
          triggerEl: editBtn,
          title: "Rediger",
          fields: readItemFields(card, spec),
          onDelete: async () => {
            try {
              const response = await fetch(`/dashboard/sider/seksjon/${sectionId}/element/${index}/slett/`, {
                method: "POST",
                headers: { "X-CSRFToken": getCsrfToken() },
              });
              const data = response.ok ? await response.json() : { ok: false };
              if (data.ok) {
                // Indices shift for every later card once this one's gone —
                // simplest correct fix is reloading rather than
                // renumbering every remaining [data-item-index] client-side.
                window.location.reload();
              } else {
                showSaveFeedback(card, false);
              }
            } catch {
              showSaveFeedback(card, false);
            }
          },
          onImageUpload: async (key, file) => {
            const formData = new FormData();
            formData.append("image", file);
            try {
              const response = await fetch(`/dashboard/sider/seksjon/${sectionId}/element/${index}/bilde/`, {
                method: "POST",
                headers: { "X-CSRFToken": getCsrfToken() },
                body: formData,
              });
              const data = response.ok ? await response.json() : { ok: false };
              if (data.ok) {
                card.dataset[`field${key[0].toUpperCase()}${key.slice(1)}`] = data.url;
                const img = card.querySelector("img");
                if (img) img.src = data.url;
                showSaveFeedback(editBtn, true);
                closePopover();
              } else {
                showSaveFeedback(editBtn, false);
              }
            } catch {
              showSaveFeedback(editBtn, false);
            }
          },
          onSave: async (values) => {
            const textValues = {};
            spec.forEach((field) => {
              if (field.kind !== "image" && field.key in values) textValues[field.key] = values[field.key];
            });
            try {
              const response = await fetch(`/dashboard/sider/seksjon/${sectionId}/element/${index}/`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": getCsrfToken() },
                body: JSON.stringify(textValues),
              });
              const data = response.ok ? await response.json() : { ok: false };
              if (data.ok) {
                Object.entries(textValues).forEach(([key, value]) => {
                  card.dataset[`field${key[0].toUpperCase()}${key.slice(1)}`] = value;
                });
                showSaveFeedback(editBtn, true);
                // Simplest correct way to reflect the new text in every place
                // the card displays it (title, body, quote, byline, …)
                // without duplicating each section's own display markup here.
                window.location.reload();
              } else {
                showSaveFeedback(editBtn, false);
              }
            } catch {
              showSaveFeedback(editBtn, false);
            }
          },
        });
      });
    });

    document.querySelectorAll("[data-list-item-add]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const sectionId = btn.dataset.inlineSection;
        try {
          const response = await fetch(`/dashboard/sider/seksjon/${sectionId}/element/legg-til/`, {
            method: "POST",
            headers: { "X-CSRFToken": getCsrfToken() },
          });
          const data = response.ok ? await response.json() : { ok: false };
          if (data.ok) {
            window.location.reload();
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
    initListItemEditing();
    initPageSettingsPanel();
  });
})();
