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

  /**
   * Calls the Geonorge address search API and returns its `adresser` array
   * (or [] on any failure, including an intentional `signal` abort — an
   * aborted request must not be treated as "no results" by its caller, so
   * callers check `signal.aborted` themselves rather than trusting an empty
   * array here to mean "user typed a query with zero matches").
   */
  async function searchAddresses(query, signal) {
    try {
      const url = `https://ws.geonorge.no/adresser/v1/sok?sok=${encodeURIComponent(query)}&treffPerSide=8&side=0`;
      const response = await fetch(url, { signal });
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
    // Aborted on every new keystroke's search and on blur, so a slow response
    // from an earlier query can never land after a newer one (or after the
    // field lost focus) and reopen/overwrite the suggestion list.
    let abortController = null;

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
      abortController?.abort();
      const query = input.value.trim();
      if (query.length < 2) {
        list.hidden = true;
        return;
      }
      debounceTimer = setTimeout(async () => {
        abortController = new AbortController();
        const results = await searchAddresses(query, abortController.signal);
        if (abortController.signal.aborted) return;
        renderSuggestions(list, results, selectAddress);
      }, 200);
    });

    input.addEventListener("blur", () => {
      // Cancel both a pending debounce (search hasn't fired yet) and an
      // in-flight request (search already fired) — either one resolving
      // after blur must not be able to reopen the dropdown on a field
      // that's no longer focused.
      clearTimeout(debounceTimer);
      abortController?.abort();
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

  // ---------------------------------------------------------------
  // Desktop map (.map-panel) — Leaflet + free CARTO Voyager tiles.
  // Two draggable pins (from/to), a 250m circle around "from", a dashed
  // line + Kobly ring icon at the midpoint once both pins exist, and
  // "Plasser fra"/"Plasser til" click-to-place toggles (spec §5.5).
  // ---------------------------------------------------------------

  const PIN_COLOR_FROM = "#221814";
  const PIN_COLOR_TO = "#3D5507";
  const TILE_URL = "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png";

  /** Builds a Leaflet divIcon: a colored circle with a white house-pin glyph, matching the reference exactly. */
  function pinIcon(color) {
    return L.divIcon({
      className: "",
      html: `<div style="width:36px;height:36px;background:${color};border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,0.3);border:2px solid white"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg></div>`,
      iconSize: [36, 36],
      iconAnchor: [18, 18],
    });
  }

  /** Builds the small white Kobly-ring icon shown at the midpoint of the from/to line. */
  function midpointIcon() {
    return L.divIcon({
      className: "",
      html: `<div style="width:32px;height:32px;background:white;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.18);border:1.5px solid #E6E1D6"><svg width="16" height="16" viewBox="0 0 27 27" fill="none"><circle cx="13.5" cy="13.5" r="11.625" stroke="#221814" stroke-width="3.75"/><path d="M16.5 1.875C12.7075 5.23556 10.5 9.26144 10.5 13.5887C10.5 17.8401 12.6307 21.8006 16.3019 25.125" stroke="#221814" stroke-width="3.75"/></svg></div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });
  }

  /** Builds and wires up the step-1 desktop map — a page-lifetime singleton, never destroyed/recreated. */
  function initDesktopMap() {
    const panel = document.querySelector(".map-panel");
    if (!panel || typeof L === "undefined") return;

    const initialCenter = window.KOBLY_WIZARD_INITIAL_CENTER;
    const map = L.map(panel.querySelector("[data-map-container]"), {
      center: initialCenter ? [initialCenter.lat, initialCenter.lon] : [60.5, 10.0],
      zoom: initialCenter ? initialCenter.zoom : 5,
      zoomControl: false,
      attributionControl: false,
    });
    L.tileLayer(TILE_URL, { maxZoom: 19 }).addTo(map);

    let fromMarker = null;
    let toMarker = null;
    let fromCircle = null;
    let line = null;
    let midpointMarker = null;
    let placing = null; // "fra" | "til" | null

    /** Redraws the connecting line, midpoint icon, and "from" radius circle from the two markers' current positions. */
    function redrawOverlays() {
      if (fromMarker && toMarker) {
        const a = fromMarker.getLatLng();
        const b = toMarker.getLatLng();
        const latlngs = [a, b];
        if (line) line.setLatLngs(latlngs);
        else line = L.polyline(latlngs, { color: "#221814", weight: 2.5, dashArray: "6 6", opacity: 0.7 }).addTo(map);
        const mid = [(a.lat + b.lat) / 2, (a.lng + b.lng) / 2];
        if (midpointMarker) midpointMarker.setLatLng(mid);
        else midpointMarker = L.marker(mid, { icon: midpointIcon(), interactive: false, zIndexOffset: 500 }).addTo(map);
        map.fitBounds(latlngs, { padding: [40, 40], maxZoom: 13 });
      } else {
        if (line) { line.remove(); line = null; }
        if (midpointMarker) { midpointMarker.remove(); midpointMarker = null; }
      }
      if (fromMarker) {
        const ll = fromMarker.getLatLng();
        if (fromCircle) fromCircle.setLatLng(ll);
        else fromCircle = L.circle(ll, { radius: 250, color: "#221814", fillColor: "#221814", fillOpacity: 0.08, opacity: 0.25, weight: 1, interactive: false }).addTo(map);
      } else if (fromCircle) {
        fromCircle.remove();
        fromCircle = null;
      }
      updateChip();
    }

    /**
     * Live position update for the "drag" event only — moves the line/circle/
     * midpoint to follow the pin without touching the viewport. Kept separate
     * from redrawOverlays() so dragging an already-placed pin doesn't fight
     * the user by re-fitBounds-ing the map on every mouse-move tick; the full
     * redraw (with fitBounds) still runs once, on "dragend".
     */
    function updatePositionsDuringDrag() {
      if (fromMarker && toMarker && line) {
        const a = fromMarker.getLatLng();
        const b = toMarker.getLatLng();
        line.setLatLngs([a, b]);
        if (midpointMarker) midpointMarker.setLatLng([(a.lat + b.lat) / 2, (a.lng + b.lng) / 2]);
      }
      if (fromMarker && fromCircle) {
        fromCircle.setLatLng(fromMarker.getLatLng());
      }
    }

    /** Shows/updates the "Ca. {from} -> {to}" floating chip in the top-left of the map. */
    function updateChip() {
      const chip = panel.querySelector("[data-map-chip]");
      const fraShort = document.querySelector('[name="fra"]').value.split(",")[0]?.trim();
      const tilShort = document.querySelector('[name="til"]').value.split(",")[0]?.trim();
      if (!fraShort && !tilShort) { chip.hidden = true; return; }
      chip.querySelector("[data-map-chip-from]").textContent = fraShort || "—";
      chip.querySelector("[data-map-chip-to]").textContent = tilShort || "—";
      chip.hidden = false;
    }

    /** Places or moves the "fra"/"til" pin at a coordinate, wiring up drag-to-move with reverse geocoding. */
    function setPin(which, lat, lon) {
      const color = which === "fra" ? PIN_COLOR_FROM : PIN_COLOR_TO;
      const existing = which === "fra" ? fromMarker : toMarker;
      if (existing) {
        existing.setLatLng([lat, lon]);
      } else {
        const marker = L.marker([lat, lon], { icon: pinIcon(color), draggable: true, autoPan: true }).addTo(map);
        marker.on("drag", updatePositionsDuringDrag);
        marker.on("dragend", async () => {
          const ll = marker.getLatLng();
          const address = await reverseGeocode(ll.lat, ll.lng, "Pin plassert i kart");
          applyCoordToField(which, ll.lat, ll.lng, address);
        });
        if (which === "fra") fromMarker = marker; else toMarker = marker;
      }
      redrawOverlays();
    }

    /** Writes a coordinate + resolved address into the matching address-field's inputs and repositions its pin. */
    function applyCoordToField(which, lat, lon, address) {
      const fieldEl = document.querySelector(`.address-field[data-address-field="${which}"]`);
      fieldEl.setAddressFromCoord(lat, lon, address);
      setPin(which, lat, lon);
    }

    // Address autocomplete (Task 11) reports coordinate changes here so the map stays in sync.
    KoblyWizard.onCoordChange = (which, lat, lon) => {
      const key = which === "fra" ? "fra" : "til";
      if (lat !== null && lon !== null) setPin(key, lat, lon);
    };

    // Click-to-place ("Plasser fra" / "Plasser til")
    panel.querySelectorAll("[data-place-toggle]").forEach((button) => {
      button.addEventListener("click", () => {
        const which = button.dataset.placeToggle;
        placing = placing === which ? null : which;
        panel.querySelectorAll("[data-place-toggle]").forEach((b) => {
          b.classList.toggle("is-armed", b.dataset.placeToggle === placing);
          b.textContent = b.dataset.placeToggle === placing ? "Klikk på kartet" : (b.dataset.placeToggle === "fra" ? "Plasser fra" : "Plasser til");
        });
      });
    });
    map.on("click", async (event) => {
      if (!placing) return;
      const address = await reverseGeocode(event.latlng.lat, event.latlng.lng, "Pin plassert i kart");
      applyCoordToField(placing, event.latlng.lat, event.latlng.lng, address);
      placing = null;
      panel.querySelectorAll("[data-place-toggle]").forEach((b) => {
        b.classList.remove("is-armed");
        b.textContent = b.dataset.placeToggle === "fra" ? "Plasser fra" : "Plasser til";
      });
    });

    // Zoom buttons
    panel.querySelector("[data-map-zoom-in]").addEventListener("click", () => map.zoomIn());
    panel.querySelector("[data-map-zoom-out]").addEventListener("click", () => map.zoomOut());

    // "Bruk min plassering" — geolocates and places the "fra" pin
    panel.querySelector("[data-map-locate]").addEventListener("click", () => {
      if (!navigator.geolocation) return;
      const button = panel.querySelector("[data-map-locate]");
      button.classList.add("is-locating");
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords;
          const address = await reverseGeocode(latitude, longitude, "Min posisjon");
          applyCoordToField("fra", latitude, longitude, address);
          button.classList.remove("is-locating");
        },
        () => button.classList.remove("is-locating"),
        { enableHighAccuracy: true, timeout: 8000 },
      );
    });

    // Resize fix: Leaflet needs an explicit nudge once its container becomes visible/sized.
    setTimeout(() => map.invalidateSize(), 100);
    KoblyWizard.onStepChange.push((step) => { if (step === 1) map.invalidateSize(); });
  }

  // ---------------------------------------------------------------
  // Mobile map picker overlay (.map-overlay) — fullscreen, fixed center
  // crosshair pin, user pans the map underneath it (spec §5.5 mobile).
  // ---------------------------------------------------------------
  function initMobileMapPicker() {
    const overlay = document.querySelector("[data-map-overlay]");
    if (!overlay || typeof L === "undefined") return;

    let map = null;
    let activeField = null; // "fra" | "til"
    let resolvedAddress = null;
    // Guards against a slower, earlier reverse-geocode (e.g. from a previous
    // pan) landing after a newer one and overwriting it with a stale address
    // that no longer matches the map's current center — the same race Task
    // 11 solved for address search, applied here without needing to touch
    // reverseGeocode()'s signature (Geonorge calls are cheap enough that
    // discarding a stale result is sufficient; no network-level abort needed).
    let lookupSequence = 0;

    /** Reverse-geocodes the map's current center and updates the bottom sheet's address text. */
    async function lookupCenter() {
      const addressEl = overlay.querySelector("[data-map-overlay-address]");
      addressEl.classList.add("is-loading");
      const center = map.getCenter();
      const sequence = ++lookupSequence;
      const address = await reverseGeocode(center.lat, center.lng, "Plassering valgt i kart");
      if (sequence !== lookupSequence) return; // superseded by a newer pan/lookup — discard
      resolvedAddress = address;
      addressEl.textContent = resolvedAddress;
      addressEl.classList.remove("is-loading");
    }

    /** Opens the overlay for the given field ("fra"/"til"), initializing the map centered on any existing pin. */
    function open(which) {
      activeField = which;
      overlay.hidden = false;
      overlay.querySelector("[data-map-overlay-title]").textContent =
        which === "til" ? "Hvor flytter du til?" : "Hvor flytter du fra?";
      document.body.style.overflow = "hidden";

      const latInput = document.querySelector(`[data-coord="${which}_lat"]`);
      const lonInput = document.querySelector(`[data-coord="${which}_lon"]`);
      const hasPin = latInput.value && lonInput.value;
      const start = hasPin
        ? [Number(latInput.value), Number(lonInput.value)]
        : window.KOBLY_WIZARD_INITIAL_CENTER
          ? [window.KOBLY_WIZARD_INITIAL_CENTER.lat, window.KOBLY_WIZARD_INITIAL_CENTER.lon]
          : [59.9139, 10.7522];
      const zoom = hasPin ? 16 : 14;

      map = L.map(overlay.querySelector("[data-map-overlay-container]"), {
        center: start, zoom, zoomControl: false, attributionControl: false,
      });
      L.tileLayer(TILE_URL, { maxZoom: 19 }).addTo(map);
      setTimeout(() => map.invalidateSize(), 50);
      map.on("moveend", lookupCenter);
      lookupCenter();
    }

    /** Tears down the Leaflet instance and hides the overlay. */
    function close() {
      overlay.hidden = true;
      document.body.style.overflow = "";
      if (map) { map.remove(); map = null; }
      resolvedAddress = null;
    }

    /** Confirms the map's current center as the chosen coordinate for the active field. */
    function confirm() {
      if (!map || !activeField) return;
      const center = map.getCenter();
      const fieldEl = document.querySelector(`.address-field[data-address-field="${activeField}"]`);
      fieldEl.setAddressFromCoord(center.lat, center.lng, resolvedAddress || "Plassering valgt i kart");
      document.querySelector(`[data-open-map-picker="${activeField}"]`).classList.add("is-placed");
      document.querySelector(`[data-open-map-picker="${activeField}"] .map-picker-btn__label`).textContent = "Plasseringen valgt · endre i kart";
      // Reuse the desktop map's own pin-placement path so both stay in sync.
      KoblyWizard.onCoordChange && KoblyWizard.onCoordChange(activeField, center.lat, center.lng);
      close();
    }

    document.querySelectorAll("[data-open-map-picker]").forEach((button) => {
      button.addEventListener("click", () => open(button.dataset.openMapPicker));
    });
    overlay.querySelector("[data-map-overlay-close]").addEventListener("click", close);
    overlay.querySelector("[data-map-overlay-confirm]").addEventListener("click", confirm);
    overlay.querySelector("[data-map-overlay-locate]").addEventListener("click", () => {
      if (!navigator.geolocation || !map) return;
      const button = overlay.querySelector("[data-map-overlay-locate]");
      button.classList.add("is-locating");
      navigator.geolocation.getCurrentPosition(
        (position) => {
          map.setView([position.coords.latitude, position.coords.longitude], 16);
          button.classList.remove("is-locating");
        },
        () => button.classList.remove("is-locating"),
        { enableHighAccuracy: true, timeout: 8000 },
      );
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !overlay.hidden) close();
    });
  }

  // ---------------------------------------------------------------
  // Photo upload (step 4) — browsers can't append to a file input's
  // FileList directly, so we keep our own array of File objects and
  // rebuild the input's .files from it via DataTransfer on every change.
  // ---------------------------------------------------------------
  let selectedPhotos = [];

  /** Rebuilds the hidden file input's FileList from the current selectedPhotos array. */
  function syncPhotoInput() {
    const input = document.querySelector("[data-photo-input]");
    const transfer = new DataTransfer();
    selectedPhotos.forEach((file) => transfer.items.add(file));
    input.files = transfer.files;
  }

  /** Redraws the 4-column thumbnail grid (existing photos + the trailing upload tile) from selectedPhotos. */
  function renderPhotoGrid() {
    const grid = document.querySelector("[data-photo-grid]");
    const uploadTile = grid.querySelector(".photo-upload-tile");
    grid.querySelectorAll(".photo-thumb").forEach((el) => el.remove());

    selectedPhotos.forEach((file, index) => {
      const url = URL.createObjectURL(file);
      const thumb = document.createElement("div");
      thumb.className = "photo-thumb";
      thumb.innerHTML = `<img src="${url}" alt=""><button type="button" class="photo-thumb__remove" aria-label="Fjern bilde"><span data-icon="x"></span></button>`;
      thumb.querySelector(".photo-thumb__remove").addEventListener("click", () => {
        selectedPhotos.splice(index, 1);
        syncPhotoInput();
        renderPhotoGrid();
      });
      grid.insertBefore(thumb, uploadTile);
    });

    // The upload tile's icon placeholder was just re-inserted into the DOM
    // context above (it's never removed) but new [data-icon] spans in the
    // freshly-created remove buttons need their SVGs cloned in.
    initIconSprite();
  }

  /** Wires up the file input's change event to append new files to selectedPhotos (spec §5.8: "New files append to the existing array"). */
  function initPhotoUpload() {
    const input = document.querySelector("[data-photo-input]");
    if (!input) return;
    input.addEventListener("change", () => {
      selectedPhotos = selectedPhotos.concat(Array.from(input.files));
      syncPhotoInput();
      renderPhotoGrid();
    });
  }

  // ---------------------------------------------------------------
  // Live summary panel (step 5, desktop) — re-reads the form's current
  // values and re-renders the receipt rows every time anything changes.
  // ---------------------------------------------------------------
  const FLYTTE_TYPE_LABELS = { privat: "Privat flytting", bedrift: "Bedriftsflytting", internasjonal: "Internasjonal" };
  const BOLIGTYPE_LABELS = { leilighet: "Leilighet", rekkehus: "Rekkehus", enebolig: "Enebolig", annet: "Annet" };

  /** Builds one label/value row element for the summary panel. */
  function summaryRow(label, value) {
    const row = document.createElement("div");
    row.className = "summary-panel__row";
    row.innerHTML = `<span class="summary-panel__row-label">${label}</span><span class="summary-panel__row-value"></span>`;
    row.querySelector(".summary-panel__row-value").textContent = value;
    return row;
  }

  /** Reads every wizard field from the DOM and re-renders the step-5 receipt panel (Fra/Til/Flytting/Når/Innhold/Bilder). */
  function updateSummaryPanel() {
    const rows = document.querySelector("[data-summary-rows]");
    if (!rows) return;
    const form = document.querySelector(".wizard-card");
    rows.innerHTML = "";

    const fra = form.querySelector('[name="fra"]').value.trim();
    const til = form.querySelector('[name="til"]').value.trim();
    const flytteType = form.querySelector('[name="flytte_type"]:checked');
    const boligtype = form.querySelector('[name="boligtype"]:checked');
    const dato = form.querySelector('[name="flyttedato"]').value;
    const fleksibel = form.querySelector('[name="fleksibel"]').checked;
    const beskrivelse = form.querySelector('[name="beskrivelse"]').value.trim();

    if (fra) rows.appendChild(summaryRow("Fra", fra));
    if (til) rows.appendChild(summaryRow("Til", til));
    if (flytteType || boligtype) {
      const parts = [flytteType && FLYTTE_TYPE_LABELS[flytteType.value], boligtype && BOLIGTYPE_LABELS[boligtype.value]].filter(Boolean);
      rows.appendChild(summaryRow("Flytting", parts.join(" · ")));
    }
    if (dato || fleksibel) {
      const value = fleksibel ? "Fleksibel dato" : new Date(dato).toLocaleDateString("no-NO", { day: "numeric", month: "long", year: "numeric" });
      rows.appendChild(summaryRow("Når", value));
    }
    if (beskrivelse) rows.appendChild(summaryRow("Innhold", beskrivelse));
    if (selectedPhotos.length > 0) {
      const label = document.createElement("span");
      label.className = "summary-panel__row-label";
      label.textContent = "Bilder";
      const grid = document.createElement("div");
      grid.className = "photo-grid";
      selectedPhotos.forEach((file) => {
        const thumb = document.createElement("div");
        thumb.className = "photo-thumb";
        thumb.innerHTML = `<img src="${URL.createObjectURL(file)}" alt="">`;
        grid.appendChild(thumb);
      });
      const wrapper = document.createElement("div");
      wrapper.className = "summary-panel__row";
      wrapper.appendChild(label);
      wrapper.appendChild(grid);
      rows.appendChild(wrapper);
    }
  }

  /** Entry point — runs everything this task owns once the DOM is ready. */
  function initWizard() {
    initIconSprite();
    initNavigation();
    updateProgressBar();
    updateNavButton();
    initAddressAutocomplete();
    initDesktopMap();
    initMobileMapPicker();
    initPhotoUpload();
    KoblyWizard.onStepChange.push((step) => { if (step === 5) updateSummaryPanel(); });
    document.querySelector(".wizard-card").addEventListener("input", updateSummaryPanel);
    document.querySelector(".wizard-card").addEventListener("change", updateSummaryPanel);
  }

  document.addEventListener("DOMContentLoaded", initWizard);
})();
