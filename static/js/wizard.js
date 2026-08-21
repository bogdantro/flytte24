// static/js/wizard.js
//
// Vanilla-JS controller for the /wizard page. No framework, no build step.
// The DOM inputs are the source of truth for form data — this file only
// tracks UI-only state (current step, direction, map instances, selected
// photo files) that genuinely can't live in a plain form field.
//
// Sections, in the order they run:
//   1. Icon sprite wiring
//   2. Step navigation (this task)
//   3. Per-step validity checks (this task)
//   4. Address autocomplete (Task 11)
//   5. Maps — desktop panel + mobile picker overlay (Task 12)
//   6. Photo upload + live summary panel (Task 13)

(function () {
  "use strict";

  const TOTAL_STEPS = 5;
  let currentStep = 1;

  /** Clones the matching <symbol> from the icon sprite into every [data-icon] placeholder. */
  function initIconSprite() {
    document.querySelectorAll("[data-icon]").forEach((el) => {
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
      case 1: {
        const fra = form.querySelector('[name="fra"]').value.trim();
        const til = form.querySelector('[name="til"]').value.trim();
        return fra.length > 2 && til.length > 2;
      }
      case 2: {
        const type = form.querySelector('[name="flytte_type"]:checked');
        const bolig = form.querySelector('[name="boligtype"]:checked');
        return Boolean(type) && Boolean(bolig);
      }
      case 3: {
        const date = form.querySelector('[name="flyttedato"]').value;
        const fleksibel = form.querySelector('[name="fleksibel"]').checked;
        return Boolean(date) || fleksibel;
      }
      case 4:
        return true; // always valid — goods/photos step is optional
      case 5: {
        const navn = form.querySelector('[name="navn"]').value.trim();
        const telefon = form.querySelector('[name="telefon"]').value.trim();
        const epost = form.querySelector('[name="epost"]').value.trim();
        return (
          navn.length > 1 &&
          /^[\d\s+]{8,}$/.test(telefon) &&
          /\S+@\S+\.\S+/.test(epost)
        );
      }
      default:
        return false;
    }
  }

  /** Enables/disables the Neste button based on the current step's validity, and swaps its label on step 5. */
  function updateNavButton() {
    const nextBtn = document.querySelector("[data-wizard-next]");
    const nextLabel = document.querySelector("[data-next-label]");
    nextBtn.disabled = !isStepValid(currentStep);
    nextLabel.textContent = currentStep === TOTAL_STEPS ? "Send forespørsel" : "Neste";
  }

  /** Fills in the completed segments of the 5-part progress bar and the "Steg X av 5" label. */
  function updateProgressBar() {
    document.querySelectorAll(".wizard-progress__segment").forEach((segment, index) => {
      segment.classList.toggle("is-complete", index < currentStep - 1);
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
    updateMobileBackground(target);
  }

  /**
   * Crossfades the mobile-only background photo to the one mapped for `step`
   * (spec §5.3): the outgoing photo is copied into the hidden "prev" <img>
   * and revealed, the "current" <img>'s src is swapped and its fade-in
   * animation restarted, then "prev" is hidden again once the 400ms
   * crossfade finishes underneath it.
   */
  function updateMobileBackground(step) {
    const backgrounds = window.KOBLY_MOBILE_BACKGROUNDS;
    const current = document.querySelector("[data-step-bg-current]");
    const prev = document.querySelector("[data-step-bg-prev]");
    if (!backgrounds || !current || !prev) return;
    const nextUrl = backgrounds[step];
    if (!nextUrl || current.getAttribute("src") === nextUrl) return;

    prev.src = current.src;
    prev.hidden = false;

    current.src = nextUrl;
    // Restart the CSS fade-in animation by removing and re-adding its class.
    current.classList.remove("wizard__background-photo--current");
    void current.offsetWidth; // force reflow so the browser notices the class removal
    current.classList.add("wizard__background-photo--current");

    setTimeout(() => { prev.hidden = true; }, 400);
  }

  /** Navigates to an arbitrary step number, updating every dependent piece of UI. */
  function goToStep(target) {
    const direction = target > currentStep ? 1 : -1;
    currentStep = target;
    showStep(target, direction);
    updateProgressBar();
    updateNavButton();
    document.querySelector("[data-wizard-back]").hidden = currentStep === 1;
    // Task 12 hooks into step changes to lazily init the desktop map on step 1
    // and Task 13 hooks in to refresh the live summary panel on step 5 — see
    // KoblyWizard.onStepChange below.
    KoblyWizard.onStepChange.forEach((handler) => handler(currentStep));
  }

  /** Advances one step forward, or submits the form on the final step. */
  function nextStep() {
    if (!isStepValid(currentStep)) return;
    if (currentStep < TOTAL_STEPS) {
      goToStep(currentStep + 1);
    } else {
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

  /**
   * Shared namespace so Tasks 11-13 (appended below in later commits) can
   * register step-change hooks and reuse goToStep without re-querying the DOM.
   */
  window.KoblyWizard = {
    goToStep,
    getCurrentStep: () => currentStep,
    onStepChange: [], // array of function(step) — populated by later sections
  };

  // ---------------------------------------------------------------
  // Address autocomplete — Kartverket's free, keyless Geonorge API
  // (spec §5.13). 200ms debounce, up to 8 results, closes 120ms after
  // blur so a click on a suggestion registers before the list vanishes.
  // ---------------------------------------------------------------

  /** Calls the Geonorge address search API and returns its `adresser` array (or [] on any failure). */
  async function searchAddresses(query) {
    try {
      const url = `https://ws.geonorge.no/adresser/v1/sok?sok=${encodeURIComponent(query)}&treffPerSide=8&side=0`;
      const response = await fetch(url);
      if (!response.ok) return [];
      const json = await response.json();
      return json.adresser || [];
    } catch {
      return [];
    }
  }

  /** Calls the Geonorge reverse-geocode API for one coordinate; falls back to `fallbackText` on failure. */
  async function reverseGeocode(lat, lon, fallbackText) {
    try {
      const url = `https://ws.geonorge.no/adresser/v1/punktsok?radius=200&lat=${lat}&lon=${lon}&treffPerSide=1&side=0`;
      const response = await fetch(url);
      if (!response.ok) return fallbackText;
      const json = await response.json();
      const hit = (json.adresser || [])[0];
      return hit ? `${hit.adressetekst}, ${hit.postnummer} ${hit.poststed}` : fallbackText;
    } catch {
      return fallbackText;
    }
  }

  /** Renders the suggestion <li> list for one address field, wiring up click-to-select on each row. */
  function renderSuggestions(listEl, suggestions, onSelect) {
    listEl.innerHTML = "";
    if (suggestions.length === 0) {
      listEl.hidden = true;
      return;
    }
    suggestions.forEach((address) => {
      const li = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.innerHTML = `<span>${address.adressetekst}</span><span class="address-suggestions__meta">${address.postnummer} ${address.poststed}</span>`;
      // mousedown (not click) fires before the input's blur handler closes the list.
      button.addEventListener("mousedown", (event) => {
        event.preventDefault();
        onSelect(address);
      });
      li.appendChild(button);
      listEl.appendChild(li);
    });
    listEl.hidden = false;
  }

  /** Wires up debounced search + selection for one .address-field element ("fra" or "til"). */
  function initOneAddressField(fieldEl) {
    const key = fieldEl.dataset.addressField; // "fra" | "til"
    const input = fieldEl.querySelector(`[name="${key}"]`);
    const list = fieldEl.querySelector(".address-suggestions");
    const latInput = fieldEl.querySelector(`[data-coord="${key}_lat"]`);
    const lonInput = fieldEl.querySelector(`[data-coord="${key}_lon"]`);
    let debounceTimer = null;

    const selectAddress = (address) => {
      const point = address.representasjonspunkt;
      input.value = `${address.adressetekst}, ${address.postnummer} ${address.poststed}`;
      latInput.value = point ? point.lat : "";
      lonInput.value = point ? point.lon : "";
      list.hidden = true;
      // Task 12's map reads these same hidden inputs to place/move its pin.
      KoblyWizard.onCoordChange && KoblyWizard.onCoordChange(key, point ? point.lat : null, point ? point.lon : null, input.value);
    };

    input.addEventListener("input", () => {
      // Manual typing invalidates any previously attached coordinate (spec §5.5).
      latInput.value = "";
      lonInput.value = "";
      clearTimeout(debounceTimer);
      const query = input.value.trim();
      if (query.length < 2) {
        list.hidden = true;
        return;
      }
      debounceTimer = setTimeout(async () => {
        const results = await searchAddresses(query);
        renderSuggestions(list, results, selectAddress);
      }, 200);
    });

    input.addEventListener("blur", () => {
      setTimeout(() => { list.hidden = true; }, 120);
    });

    // Exposed so Task 12's map (pin drag / click-to-place / geolocation) can
    // push a coordinate + resolved address back into this same field.
    fieldEl.setAddressFromCoord = (lat, lon, address) => {
      input.value = address;
      latInput.value = lat;
      lonInput.value = lon;
    };
  }

  /** Wires up both address fields (fra/til) on step 1. */
  function initAddressAutocomplete() {
    document.querySelectorAll(".address-field").forEach(initOneAddressField);
  }

  /** Entry point — runs everything this task owns once the DOM is ready. */
  function initWizard() {
    initIconSprite();
    initNavigation();
    updateProgressBar();
    updateNavButton();
    initAddressAutocomplete();
  }

  document.addEventListener("DOMContentLoaded", initWizard);
})();
