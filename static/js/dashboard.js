// static/js/dashboard.js
//
// Staff dashboard JS — sidebar icon hydration, a confirm dialog in front of
// every permanent-delete form, and the business detail page's "Dekning"
// pill grid (saved over AJAX on every toggle).

(function () {
  "use strict";

  /** Reads Django's CSRF cookie for the fetch() header. */
  function getCsrfToken() {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

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
        document.querySelectorAll('input[name="lead_ids"], input[name="business"]').forEach((box) => {
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

  /** Business detail "Dekning" grid: saves cities/services the instant a
   * pill is toggled, via dashboard:business_update_coverage, with no
   * submit/reload — the staff-side twin of the account portal's own
   * coverage section (static/js/account-portal.js initCoverageAjaxSave). */
  function initCoverageAjaxSave() {
    const form = document.querySelector("[data-coverage-form]");
    if (!form) return;
    const anchor = form.querySelector("[data-coverage-feedback-anchor]");

    const showFeedback = (ok) => {
      if (!anchor) return;
      anchor.textContent = ok ? "Lagret" : "Kunne ikke lagre";
      anchor.classList.toggle("is-error", !ok);
      anchor.classList.add("is-visible");
      clearTimeout(showFeedback._timer);
      showFeedback._timer = setTimeout(() => anchor.classList.remove("is-visible"), 1600);
    };

    // Abort any still-in-flight save before starting the next one, so two
    // overlapping toggles can't resolve out of order and write a stale
    // snapshot back over the newer one.
    let inFlight = null;

    const save = async () => {
      if (inFlight) inFlight.abort();
      const controller = new AbortController();
      inFlight = controller;

      const body = new FormData(form);
      const areasInput = form.querySelector("[data-service-areas-input]");
      if (areasInput) body.set("service_areas", areasInput.value || "[]");
      try {
        const response = await fetch(form.dataset.coverageForm, {
          method: "POST",
          headers: { "X-CSRFToken": getCsrfToken() },
          body,
          signal: controller.signal,
        });
        const data = response.ok ? await response.json() : { ok: false };
        showFeedback(Boolean(data.ok));
      } catch (err) {
        if (err.name === "AbortError") return; // superseded by a newer toggle
        showFeedback(false);
      } finally {
        if (inFlight === controller) inFlight = null;
      }
    };

    form.addEventListener("change", (event) => {
      if (event.target.matches('input[type="checkbox"]')) save();
    });
    // The structured-areas widget (coverage-onboarding.js) fires this.
    form.addEventListener("coverage:changed", save);
  }

  /** The "Egendefinert" invoice-range button stays disabled until both the
   *  from and to dates are picked (they're custom pickers writing hidden
   *  inputs — a plain `required` on a hidden input blocks submit silently). */
  function initInvoiceRangeForm() {
    document.querySelectorAll("[data-invoice-range-form]").forEach((form) => {
      const submit = form.querySelector("[data-invoice-range-submit]");
      const from = form.querySelector('[name="from"]');
      const to = form.querySelector('[name="to"]');
      if (!submit || !from || !to) return;
      const sync = () => { submit.disabled = !(from.value && to.value); };
      form.addEventListener("input", sync);
      form.addEventListener("change", sync);
      sync();
    });
  }

  // Exposed so add-on scripts (faq-editor.js, …) can hydrate [data-icon]
  // placeholders they inject after load.
  window.KoblyDashboard = { hydrateIcons: initIconSprite };

  document.addEventListener("DOMContentLoaded", () => {
    initIconSprite();
    initDeleteConfirm();
    initAssignSelects();
    initSelectAll();
    initCopyButtons();
    initCoverageAjaxSave();
    initInvoiceRangeForm();
  });
})();
