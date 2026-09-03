// static/js/property-lookup.js
//
// Wizard step 2 — "Fortell oss om boligen". Self-contained; loads after
// wizard.js. Owns only the [data-property-step] subtree.
//
// Flow:
//   accessible address combobox (our own /api/adresse-sok/ proxy)
//     -> verified address selected
//     -> POST /api/eiendom/  (one locked request)
//     -> house | apartment-selector | building-selector | manual fallback | error
//
// The DOM hidden inputs (property_token, selected_unit) + the *_manuell fields
// are the only things the server acts on, and the server re-validates the
// token. This file never trusts its own rendered numbers as the submission.

(function () {
  "use strict";

  var URLS = window.KOBLY_PROPERTY_URLS || {};
  var MIN_QUERY = 3;
  var DEBOUNCE_MS = 300;
  var MAX_RESULTS = 8;

  var root = document.querySelector("[data-property-step]");
  if (!root || !URLS.addressSearch || !URLS.lookup) return;

  // ---- element refs ----
  var input = root.querySelector("[data-property-input]");
  var list = root.querySelector("[data-property-list]");
  var emptyMsg = root.querySelector("[data-property-empty]");
  var searchSpinner = root.querySelector("[data-property-search-spinner]");
  var combobox = root.querySelector("[data-property-combobox]");
  var manualWrap = root.querySelector("[data-property-manual]");
  var manualUnitWrap = root.querySelector("[data-property-manual-unit]");
  var sourceNote = root.querySelector("[data-property-source-note]");
  var tokenInput = root.querySelector("[data-property-token]");
  var selectedUnitInput = root.querySelector("[data-property-selected-unit]");
  // Result card renders inline in the left column (it's content, not a companion image).
  var resultRegion = ensureResultRegion();

  // ---- state ----
  var selectedAddress = null;   // {id, label, secondary_label, ...} chosen from the list
  var suggestions = [];
  var activeIndex = -1;
  var debounceTimer = null;
  var searchController = null;
  var searchSeq = 0;
  var lookupController = null;
  var lookupInFlight = false;
  var lastLookup = null;        // full normalized response of the current address
  var csrfToken = readCsrf();

  // Restore a token that survived a server-side form re-render (validation error
  // on a later step) so the customer doesn't lose their looked-up property.
  if (tokenInput && tokenInput.value) {
    input.value = readServerFra() || input.value;
  }

  // =======================================================================
  // Address combobox
  // =======================================================================

  input.addEventListener("input", function () {
    // Editing after a selection invalidates it (spec: manual edits must not
    // keep a stale verified address).
    if (selectedAddress) invalidateSelection();
    var q = input.value.trim();
    clearTimeout(debounceTimer);
    if (searchController) searchController.abort();
    if (q.length < MIN_QUERY) {
      renderSuggestions([]);
      return;
    }
    debounceTimer = setTimeout(function () { runSearch(q); }, DEBOUNCE_MS);
  });

  input.addEventListener("keydown", function (event) {
    if (!list.hidden && suggestions.length) {
      if (event.key === "ArrowDown") { event.preventDefault(); moveActive(1); return; }
      if (event.key === "ArrowUp") { event.preventDefault(); moveActive(-1); return; }
      if (event.key === "Enter") {
        if (activeIndex >= 0) { event.preventDefault(); choose(suggestions[activeIndex]); return; }
      }
      if (event.key === "Escape") { event.preventDefault(); closeList(); return; }
    }
  });

  input.addEventListener("blur", function () {
    // Delay so a mousedown on an option registers first.
    setTimeout(closeList, 120);
  });

  function runSearch(query) {
    searchController = new AbortController();
    var seq = ++searchSeq;
    setSearchLoading(true);
    fetch(URLS.addressSearch + "?q=" + encodeURIComponent(query), {
      signal: searchController.signal,
      headers: { "Accept": "application/json" },
    })
      .then(function (r) { return r.ok ? r.json() : { results: [] }; })
      .then(function (data) {
        if (seq !== searchSeq) return; // a newer search already ran
        setSearchLoading(false);
        renderSuggestions((data.results || []).slice(0, MAX_RESULTS));
      })
      .catch(function (err) {
        if (err && err.name === "AbortError") return;
        if (seq !== searchSeq) return;
        setSearchLoading(false);
        renderSuggestions([]);
      });
  }

  function renderSuggestions(items) {
    suggestions = items;
    activeIndex = -1;
    list.innerHTML = "";

    if (!items.length) {
      list.hidden = true;
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
      // Only show "no results" once the user has actually typed a real query
      // and we're not mid-typing.
      emptyMsg.hidden = input.value.trim().length < MIN_QUERY;
      return;
    }
    emptyMsg.hidden = true;

    items.forEach(function (item, i) {
      var li = document.createElement("li");
      li.className = "property-suggestions__item";
      li.id = "property-opt-" + i;
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", "false");
      li.innerHTML =
        '<span class="property-suggestions__label"></span>' +
        '<span class="property-suggestions__meta"></span>';
      li.querySelector(".property-suggestions__label").textContent = item.label || "";
      li.querySelector(".property-suggestions__meta").textContent = item.secondary_label || item.municipality || "";
      li.addEventListener("mousedown", function (e) { e.preventDefault(); choose(item); });
      li.addEventListener("mouseenter", function () { setActive(i); });
      list.appendChild(li);
    });
    list.hidden = false;
    input.setAttribute("aria-expanded", "true");
  }

  function moveActive(delta) {
    var next = activeIndex + delta;
    if (next < 0) next = suggestions.length - 1;
    if (next >= suggestions.length) next = 0;
    setActive(next);
  }

  function setActive(i) {
    activeIndex = i;
    Array.prototype.forEach.call(list.children, function (li, idx) {
      var on = idx === i;
      li.classList.toggle("is-active", on);
      li.setAttribute("aria-selected", on ? "true" : "false");
    });
    if (i >= 0) {
      input.setAttribute("aria-activedescendant", "property-opt-" + i);
      list.children[i].scrollIntoView({ block: "nearest" });
    } else {
      input.removeAttribute("aria-activedescendant");
    }
  }

  function closeList() {
    list.hidden = true;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  }

  function setSearchLoading(on) {
    if (searchSpinner) searchSpinner.hidden = !on;
    if (combobox) combobox.classList.toggle("is-loading", on);
  }

  // =======================================================================
  // Selection + building lookup
  // =======================================================================

  function choose(item) {
    selectedAddress = item;
    input.value = item.label + (item.secondary_label ? ", " + item.secondary_label : "");
    closeList();
    emptyMsg.hidden = true;
    combobox.classList.add("is-selected");
    runLookup();
  }

  function invalidateSelection() {
    selectedAddress = null;
    lastLookup = null;
    combobox.classList.remove("is-selected");
    tokenInput.value = "";
    selectedUnitInput.value = "";
    hideManual();
    if (sourceNote) sourceNote.hidden = true;
    resultRegion.innerHTML = "";
    setPropertySummary(null);
  }

  function runLookup(extraBody) {
    if (!selectedAddress || lookupInFlight) return;
    lookupInFlight = true;
    if (lookupController) lookupController.abort();
    lookupController = new AbortController();
    lockControls(true);
    renderLoading();

    var payload = { address_id: selectedAddress.id };
    if (extraBody) Object.assign(payload, extraBody);

    fetch(URLS.lookup, {
      method: "POST",
      signal: lookupController.signal,
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
        "Accept": "application/json",
      },
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json().catch(function () { return { success: false, error: { code: "SERVER_ERROR" } }; }); })
      .then(function (data) { handleLookupResponse(data); })
      .catch(function (err) {
        if (err && err.name === "AbortError") return;
        renderError("Vi klarte ikke å hente boliginformasjon. Sjekk nettforbindelsen og prøv igjen.");
      })
      .finally(function () {
        lookupInFlight = false;
        lockControls(false);
      });
  }

  function handleLookupResponse(data) {
    if (data && data.success) {
      lastLookup = data;
      tokenInput.value = data.token || "";
      selectedUnitInput.value = "";
      if (sourceNote && data.source_note) {
        sourceNote.textContent = data.source_note;
        sourceNote.hidden = false;
      }
      var units = data.units || [];
      if (units.length > 1) {
        renderUnitSelection(data, units);
      } else {
        renderResolved(data, units[0] || null);
      }
      return;
    }

    var code = (data && data.error && data.error.code) || "SERVER_ERROR";
    var message = (data && data.error && data.error.message) || "Noe gikk galt. Prøv igjen.";

    if (code === "MULTIPLE_BUILDINGS" && data.buildings && data.buildings.length) {
      renderBuildingSelection(data.buildings);
      return;
    }
    if (code === "ADDRESS_NOT_FOUND") {
      invalidateSelection();
      renderNotFound(message);
      return;
    }
    if (code === "BUILDING_NOT_FOUND" || code === "PROVIDER_UNAVAILABLE" ||
        code === "PROVIDER_TIMEOUT" || code === "INVALID_PROVIDER_RESPONSE") {
      // Address is fine, building data isn't — offer the manual path, never a dead end.
      tokenInput.value = ""; // no trustworthy lookup to submit
      renderFallback(message);
      return;
    }
    // INVALID_ADDRESS, RATE_LIMITED, SERVER_ERROR
    renderError(message);
  }

  // =======================================================================
  // Rendering
  // =======================================================================

  function renderLoading() {
    hideManual();
    resultRegion.innerHTML =
      '<div class="property-card property-card--loading">' +
        '<p class="property-card__status">Henter informasjon om eiendommen din …</p>' +
        '<div class="property-skeleton"><span></span><span></span><span></span><span></span></div>' +
      '</div>';
  }

  function renderResolved(data, unit) {
    hideManual();
    var b = data.building || {};
    var addr = data.address || {};
    var effectiveBra = unit && unit.bra_m2 != null ? unit.bra_m2 : b.bra_m2;
    var floorLine = unit && unit.floor ? floorLabel(unit.floor) : null;

    var stats = [
      statCard(fmtArea(effectiveBra), "BRA"),
      statCard(fmtNum(b.number_of_floors), "etasjer"),
      statCard(fmtNum(b.construction_year), "byggeår"),
      statCard(b.building_type || "Ikke tilgjengelig", "boligtype"),
    ].join("");

    var unitBadge = unit && unit.unit_number
      ? '<p class="property-card__unit">' + esc(unit.unit_number) +
        (floorLine ? ' · ' + esc(floorLine) : '') + '</p>'
      : "";

    resultRegion.innerHTML =
      '<div class="property-card property-card--found">' +
        '<p class="property-card__badge"><span data-icon="check-circle"></span> Vi fant boligen</p>' +
        '<p class="property-card__address">' + esc(addr.formatted || (selectedAddress && selectedAddress.label) || "") + '</p>' +
        unitBadge +
        '<div class="property-stats">' + stats + '</div>' +
        detailsBlock(data) +
        changeAddressButton() +
      '</div>';
    hydrateIcons();
    setPropertySummary(summaryText(data, unit));
  }

  function renderUnitSelection(data, units) {
    hideManual();
    var rows = units.map(function (u, i) {
      var meta = [];
      if (u.floor) meta.push(floorLabel(u.floor));
      if (u.bra_m2 != null) meta.push(u.bra_m2 + " m²");
      return (
        '<li><button type="button" class="property-unit" data-unit-index="' + i + '">' +
          '<span class="property-unit__code">' + esc(u.unit_number || ("Enhet " + (i + 1))) + '</span>' +
          (meta.length ? '<span class="property-unit__meta">' + esc(meta.join(" · ")) + '</span>' : '') +
          '<span class="property-unit__arrow" data-icon="arrow-right"></span>' +
        '</button></li>'
      );
    }).join("");

    resultRegion.innerHTML =
      '<div class="property-card property-card--units">' +
        '<p class="property-card__badge"><span data-icon="check-circle"></span> Vi fant bygget</p>' +
        '<p class="property-card__address">' + esc((data.address && data.address.formatted) || "") + '</p>' +
        '<p class="property-card__prompt">Vi fant flere boenheter på denne adressen. Velg leiligheten din:</p>' +
        '<ul class="property-units">' + rows + '</ul>' +
        changeAddressButton() +
      '</div>';
    hydrateIcons();

    resultRegion.querySelectorAll("[data-unit-index]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var u = units[Number(btn.dataset.unitIndex)];
        selectedUnitInput.value = u.unit_number || "";
        renderResolved(data, u);
      });
    });
    setPropertySummary(null);
  }

  function renderBuildingSelection(buildings) {
    hideManual();
    var rows = buildings.map(function (bld, i) {
      return (
        '<li><button type="button" class="property-unit" data-building-index="' + i + '">' +
          '<span class="property-unit__code">' + esc(bld.label || bld.type || ("Bygg " + (i + 1))) + '</span>' +
          (bld.type && bld.label !== bld.type ? '<span class="property-unit__meta">' + esc(bld.type) + '</span>' : '') +
          '<span class="property-unit__arrow" data-icon="arrow-right"></span>' +
        '</button></li>'
      );
    }).join("");

    resultRegion.innerHTML =
      '<div class="property-card property-card--units">' +
        '<p class="property-card__badge"><span data-icon="building"></span> Vi fant flere bygg på eiendommen</p>' +
        '<p class="property-card__prompt">Velg riktig bygg:</p>' +
        '<ul class="property-units">' + rows + '</ul>' +
        changeAddressButton() +
      '</div>';
    hydrateIcons();

    resultRegion.querySelectorAll("[data-building-index]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var bld = buildings[Number(btn.dataset.buildingIndex)];
        runLookup({ building_id: bld.id });
      });
    });
  }

  function renderFallback(message) {
    resultRegion.innerHTML =
      '<div class="property-card property-card--fallback">' +
        '<p class="property-card__badge property-card__badge--muted"><span data-icon="check-circle"></span> Adressen er funnet</p>' +
        '<p class="property-card__status">' + esc(message) + '</p>' +
        '<p class="property-card__hint">Du kan fortsatt fortsette — fyll inn opplysningene du kjenner til.</p>' +
        changeAddressButton() +
      '</div>';
    hydrateIcons();
    showManual(true);
    setPropertySummary(manualSummaryText());
  }

  function renderNotFound(message) {
    resultRegion.innerHTML =
      '<div class="property-card property-card--error">' +
        '<p class="property-card__status">' + esc(message) + '</p>' +
      '</div>';
    input.focus();
  }

  function renderError(message) {
    resultRegion.innerHTML =
      '<div class="property-card property-card--error">' +
        '<p class="property-card__status"><span data-icon="alert-triangle"></span> ' + esc(message) + '</p>' +
        '<button type="button" class="property-retry" data-property-retry>Prøv igjen</button>' +
      '</div>';
    hydrateIcons();
    var retry = resultRegion.querySelector("[data-property-retry]");
    if (retry) retry.addEventListener("click", function () { runLookup(); });
  }

  function detailsBlock(data) {
    var b = data.building || {};
    var p = data.property || {};
    var addr = data.address || {};
    var rows = [
      ["Bygningsnummer", b.building_number],
      ["Gårdsnummer", p.gnr],
      ["Bruksnummer", p.bnr],
      ["Kommune", addr.municipality],
      ["Kommunenummer", addr.municipality_number],
      ["Bygningsstatus", b.building_status],
      ["Antall boenheter", b.residential_unit_count],
      ["Heis", b.has_elevator == null ? null : (b.has_elevator ? "Ja" : "Nei")],
    ].filter(function (r) { return r[1] != null && r[1] !== ""; });
    if (!rows.length) return "";
    var body = rows.map(function (r) {
      return '<div class="property-details__row"><dt>' + esc(r[0]) + '</dt><dd>' + esc(String(r[1])) + '</dd></div>';
    }).join("");
    return (
      '<details class="property-details">' +
        '<summary>Se mer informasjon <span data-icon="chevron-down"></span></summary>' +
        '<dl class="property-details__list">' + body + '</dl>' +
      '</details>'
    );
  }

  function changeAddressButton() {
    return '<button type="button" class="property-change" data-property-change>Endre adresse</button>';
  }

  // Delegated — the button is re-rendered often.
  resultRegion.addEventListener("click", function (event) {
    if (event.target.closest("[data-property-change]")) {
      invalidateSelection();
      input.value = "";
      input.focus();
    }
  });

  // =======================================================================
  // Manual fallback fields
  // =======================================================================

  var manualListenersBound = false;
  function showManual(withUnit) {
    if (!manualWrap) return;
    manualWrap.hidden = false;
    if (manualUnitWrap) manualUnitWrap.hidden = !withUnit;
    if (!manualListenersBound) {
      manualWrap.querySelectorAll("input").forEach(function (el) {
        el.addEventListener("input", onManualInput);
      });
      manualListenersBound = true;
    }
  }

  function hideManual() {
    if (!manualWrap || manualWrap.hidden) return;
    manualWrap.hidden = true;
    // Clear the values too — a hidden manual field must not silently submit and
    // flip the lead's data source to "user".
    manualWrap.querySelectorAll("input").forEach(function (el) { el.value = ""; });
  }

  function onManualInput() {
    // A manual correction flips the source; the server records this too.
    setPropertySummary(lastLookup ? summaryText(lastLookup, currentUnit()) : manualSummaryText());
  }

  function currentUnit() {
    if (!lastLookup || !selectedUnitInput.value) return null;
    return (lastLookup.units || []).find(function (u) { return u.unit_number === selectedUnitInput.value; }) || null;
  }

  function manualSummaryText() {
    var parts = [];
    var type = valueOf("bolig_type_manuell");
    var bra = valueOf("bolig_bra_manuell");
    if (type) parts.push(type);
    if (bra) parts.push(bra + " m²");
    return parts.join(" · ") || null;
  }

  function valueOf(name) {
    var el = root.querySelector('[name="' + name + '"]');
    return el ? el.value.trim() : "";
  }

  // =======================================================================
  // helpers
  // =======================================================================

  function lockControls(on) {
    input.disabled = on;
    root.classList.toggle("is-looking-up", on);
  }

  function summaryText(data, unit) {
    var manualType = valueOf("bolig_type_manuell");
    var manualBra = valueOf("bolig_bra_manuell");
    var b = data.building || {};
    var type = manualType || b.building_type;
    var bra = manualBra || (unit && unit.bra_m2 != null ? unit.bra_m2 : b.bra_m2);
    var parts = [];
    if (unit && unit.unit_number) parts.push(unit.unit_number);
    if (type) parts.push(type);
    if (bra) parts.push(bra + " m²");
    return parts.join(" · ") || (data.address && data.address.formatted) || null;
  }

  function setPropertySummary(text) {
    propertySummary = text || null;
  }

  var propertySummary = null;
  if (window.KoblyWizard) {
    window.KoblyWizard.getPropertySummary = function () { return propertySummary; };
  }

  function statCard(value, label) {
    return (
      '<div class="property-stat">' +
        '<span class="property-stat__value">' + esc(String(value)) + '</span>' +
        '<span class="property-stat__label">' + esc(label) + '</span>' +
      '</div>'
    );
  }

  function fmtArea(v) { return v == null || v === "" ? "Ikke tilgjengelig" : (v + " m²"); }
  function fmtNum(v) { return v == null || v === "" ? "Ikke tilgjengelig" : String(v); }

  // "2" -> "2. etasje"; "2. etasje" / "Underetasje" pass through unchanged.
  function floorLabel(v) {
    var s = String(v).trim();
    return /^\d+$/.test(s) ? s + ". etasje" : s;
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function hydrateIcons() {
    // wizard.js owns the sprite cloner; reuse it if present.
    if (window.KoblyWizard && typeof window.KoblyWizard.hydrateIcons === "function") {
      window.KoblyWizard.hydrateIcons();
      return;
    }
    root.querySelectorAll("[data-icon]").forEach(function (el) {
      if (el.querySelector("svg")) return;
      var name = el.getAttribute("data-icon");
      var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("width", "16"); svg.setAttribute("height", "16");
      var use = document.createElementNS("http://www.w3.org/2000/svg", "use");
      use.setAttribute("href", "#icon-" + name);
      svg.appendChild(use);
      el.appendChild(svg);
    });
  }

  function ensureResultRegion() {
    var existing = root.querySelector("[data-property-result]");
    if (existing) return existing;
    var div = document.createElement("div");
    div.className = "property-result";
    div.setAttribute("data-property-result", "");
    div.setAttribute("aria-live", "polite");
    combobox.insertAdjacentElement("afterend", div);
    return div;
  }

  function readCsrf() {
    var el = document.querySelector('[name="csrfmiddlewaretoken"]');
    if (el) return el.value;
    var m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }

  function readServerFra() {
    var fra = document.querySelector('[name="fra"]');
    return fra ? fra.value : "";
  }

  // =======================================================================
  // Prefill from step 1's "fra" address on entering step 2
  // =======================================================================

  var prefilled = false;
  function maybePrefill(step) {
    if (step !== 2 || prefilled || selectedAddress) return;
    var fra = (readServerFra() || "").trim();
    // Looks like "Street 10, 1234 Poststed"?
    if (!/,\s*\d{4}\s+\S/.test(fra)) return;
    prefilled = true;
    input.value = fra;
    var street = fra.split(",")[0].trim();
    runSearch(street.length >= MIN_QUERY ? street : fra);
    // Auto-select an exact match once results land.
    var attempts = 0;
    var poll = setInterval(function () {
      attempts++;
      var exact = suggestions.find(function (s) {
        return (s.label + ", " + s.secondary_label).toLowerCase() === fra.toLowerCase();
      });
      if (exact) { clearInterval(poll); choose(exact); }
      else if (attempts > 12) { clearInterval(poll); }
    }, 250);
  }

  if (window.KoblyWizard && Array.isArray(window.KoblyWizard.onStepChange)) {
    window.KoblyWizard.onStepChange.push(maybePrefill);
  }
})();
