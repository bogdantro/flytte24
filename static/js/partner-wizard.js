// static/js/partner-wizard.js
//
// Vanilla-JS controller for /for-bedrifter/bli-partner/ (the business
// signup wizard). Ported from static/js/wizard.js's generic step-navigation
// pattern (progress bar, Neste/Tilbake, per-step validity gating, step
// slide transitions) — deliberately NOT a reuse of wizard.js wholesale,
// since most of that file is address autocomplete / Leaflet map / custom
// date-picker code that has no equivalent on this form. The one piece of
// wizard.js UI logic this form does need — the photo-upload preview
// pattern — is ported too, trimmed down from "many photos" to "one logo".
//
// Sections, in the order they run:
//   1. Icon sprite wiring
//   2. Step navigation
//   3. Per-step validity checks
//   4. Logo upload (single file) + preview

(function () {
  "use strict";

  const TOTAL_STEPS = 4;
  let currentStep = 1;

  /**
   * Clones the matching <symbol> from the icon sprite into every not-yet-
   * hydrated [data-icon] placeholder. Idempotent on purpose — the logo
   * upload/remove-button icons are hydrated the same way after every
   * add/remove, and re-running this must not duplicate SVGs into any
   * [data-icon] placeholder already hydrated elsewhere on the page.
   */
  function initIconSprite() {
    document.querySelectorAll("[data-icon]").forEach((el) => {
      if (el.querySelector("svg")) return; // already hydrated
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

  /** Returns true if the given step number's required fields are currently filled in correctly. */
  function isStepValid(step) {
    const form = document.querySelector(".wizard-card");
    switch (step) {
      case 1:
        // At least one service selected.
        return form.querySelectorAll('[name="move_type"]:checked').length > 0;
      case 2:
        // At least one city selected.
        return form.querySelectorAll('[name="cities"]:checked').length > 0;
      case 3: {
        const companyName = form.querySelector('[name="company_name"]').value.trim();
        const address = form.querySelector('[name="address"]').value.trim();
        const postalCode = form.querySelector('[name="postal_code"]').value.trim();
        const city = form.querySelector('[name="city"]').value.trim();
        return (
          companyName.length > 0 &&
          address.length > 0 &&
          /^\d{4}$/.test(postalCode) &&
          city.length > 0
        );
      }
      case 4: {
        const firstName = form.querySelector('[name="first_name"]').value.trim();
        const lastName = form.querySelector('[name="last_name"]').value.trim();
        const email = form.querySelector('[name="email"]').value.trim();
        const phone = form.querySelector('[name="phone"]').value.trim();
        // Logo is optional — not part of this step's gating.
        return (
          firstName.length > 0 &&
          lastName.length > 0 &&
          /^\S+@\S+\.\S+$/.test(email) &&
          /^[\d\s+]{8,}$/.test(phone)
        );
      }
      default:
        return false;
    }
  }

  /** Enables/disables the Neste button based on the current step's validity, and swaps its label on the final step. */
  function updateNavButton() {
    const nextBtn = document.querySelector("[data-wizard-next]");
    const nextLabel = document.querySelector("[data-next-label]");
    nextBtn.disabled = !isStepValid(currentStep);
    nextLabel.textContent = currentStep === TOTAL_STEPS ? "Send søknad" : "Neste";
  }

  /** Fills in the completed segments of the 4-part progress bar and the "Steg X av 4" label. */
  function updateProgressBar() {
    document.querySelectorAll(".wizard-progress__segment").forEach((segment, index) => {
      segment.classList.toggle("is-complete", index < currentStep);
    });
    document.querySelector("[data-current-step-label]").textContent = String(currentStep);
  }

  /** Shows the target step's markup and right-column panel, sliding in from the given direction. */
  function showStep(target, direction) {
    document.querySelectorAll(".wizard-step").forEach((el) => {
      const isTarget = Number(el.dataset.step) === target;
      el.classList.toggle("is-active", isTarget);
      el.classList.remove("wizard-step--enter-right", "wizard-step--enter-left");
      if (isTarget) {
        el.classList.add(direction > 0 ? "wizard-step--enter-right" : "wizard-step--enter-left");
      }
    });
    document.querySelectorAll("[data-step-panel]").forEach((el) => {
      el.classList.toggle("is-active", Number(el.dataset.stepPanel) === target);
    });
  }

  /** Navigates to an arbitrary step number, updating every dependent piece of UI. */
  function goToStep(target) {
    const direction = target > currentStep ? 1 : -1;
    currentStep = target;
    showStep(target, direction);
    updateProgressBar();
    updateNavButton();
    document.querySelector("[data-wizard-back]").hidden = currentStep === 1;
  }

  /** Advances one step forward, or submits the form on the final step. */
  function nextStep() {
    if (!isStepValid(currentStep)) return;
    if (currentStep < TOTAL_STEPS) {
      goToStep(currentStep + 1);
    } else {
      // Disable the button immediately so a second click/tap before the page
      // navigates away can't submit the form twice (duplicate signup).
      document.querySelector("[data-wizard-next]").disabled = true;
      document.querySelector(".wizard-card").submit();
    }
  }

  /** Goes back one step. No-op on step 1 (the back button is hidden there anyway). */
  function backStep() {
    if (currentStep > 1) goToStep(currentStep - 1);
  }

  /** Wires up the Neste/Tilbake buttons and re-checks validity as the user types/selects. */
  function initNavigation() {
    document.querySelector("[data-wizard-next]").addEventListener("click", nextStep);
    document.querySelector("[data-wizard-back]").addEventListener("click", backStep);
    // Re-validate on every keystroke/change anywhere in the form, cheap enough
    // for a form this size and far simpler than field-by-field listeners.
    document.querySelector(".wizard-card").addEventListener("input", updateNavButton);
    document.querySelector(".wizard-card").addEventListener("change", updateNavButton);
  }

  // ---------------------------------------------------------------
  // Logo upload (step 4) — same object-URL-preview technique as
  // wizard.js's photo grid, trimmed to a single file: selecting a new
  // file replaces (not appends to) the current selection, and the upload
  // tile hides itself once a logo is chosen (reappearing if it's removed).
  // ---------------------------------------------------------------
  let selectedLogo = null;
  let logoUrl = null; // object URL for the currently selected logo, revoked on replace/remove

  /** Rebuilds the hidden file input's FileList from the current selectedLogo. */
  function syncLogoInput() {
    const input = document.querySelector("[data-logo-input]");
    const transfer = new DataTransfer();
    if (selectedLogo) transfer.items.add(selectedLogo);
    input.files = transfer.files;
  }

  /** Replaces the current logo selection (or clears it, if file is null), revoking the old preview URL. */
  function setLogo(file) {
    if (logoUrl) {
      URL.revokeObjectURL(logoUrl);
      logoUrl = null;
    }
    selectedLogo = file;
    logoUrl = file ? URL.createObjectURL(file) : null;
  }

  /** Redraws the logo tile: a thumbnail + remove button if one is selected, otherwise just the upload tile. */
  function renderLogoGrid() {
    const grid = document.querySelector("[data-logo-grid]");
    const uploadTile = grid.querySelector(".photo-upload-tile");
    grid.querySelectorAll(".photo-thumb").forEach((el) => el.remove());

    if (selectedLogo) {
      const thumb = document.createElement("div");
      thumb.className = "photo-thumb";
      thumb.innerHTML = `<img src="${logoUrl}" alt=""><button type="button" class="photo-thumb__remove" aria-label="Fjern logo"><span data-icon="x"></span></button>`;
      thumb.querySelector(".photo-thumb__remove").addEventListener("click", () => {
        setLogo(null);
        syncLogoInput();
        renderLogoGrid();
      });
      grid.insertBefore(thumb, uploadTile);
      uploadTile.hidden = true; // only one logo allowed — hide the upload tile once one is chosen
    } else {
      uploadTile.hidden = false;
    }

    // The upload tile's own icon placeholder was just re-inserted into the
    // DOM context above (it's never removed) but a new remove button's
    // [data-icon] placeholder needs its SVG cloned in.
    initIconSprite();
  }

  /** Wires up the file input's change event to replace the current logo selection. */
  function initLogoUpload() {
    const input = document.querySelector("[data-logo-input]");
    if (!input) return;
    input.addEventListener("change", () => {
      if (input.files && input.files[0]) {
        setLogo(input.files[0]);
        syncLogoInput();
        renderLogoGrid();
      }
    });
  }

  /** Entry point — runs everything this file owns once the DOM is ready. */
  function initWizard() {
    initIconSprite();
    initNavigation();
    updateProgressBar();
    updateNavButton();
    initLogoUpload();
  }

  document.addEventListener("DOMContentLoaded", initWizard);
})();
