// static/js/brreg-lookup.js
//
// Reusable "Firmanavn" -> Brønnøysundregistret (Brreg) company lookup.
// The field is a search box against the free, keyless Enhetsregisteret
// API; picking a match autofills the company's org.nr., employee count,
// website and address block. Used by the become-a-partner wizard
// (pages/about/for-business-partner.html) and the staff dashboard's
// business detail page (dashboard/business_detail.html).
//
// Markup contract — one or more:
//   <div data-brreg-field style="position:relative">
//     <input ... name="company_name" data-brreg-input autocomplete="off">
//     <ul data-brreg-suggestions hidden></ul>
//   </div>
// Fields filled on select, looked up by [name=...] anywhere in the
// document: company_name, company_number, employees, website, address,
// postal_code, city (each skipped if absent or empty in the Brreg record).

(function () {
  "use strict";

  const BRREG_URL = "https://data.brreg.no/enhetsregisteret/api/enheter";

  /** Uppercase place names from Brreg ("OSLO") -> "Oslo". */
  function titleCasePlace(value) {
    return String(value || "")
      .toLowerCase()
      .replace(/(^|[\s\-/])([a-zæøå])/g, (m, sep, ch) => sep + ch.toUpperCase());
  }

  /** Sets one field by name and fires "input" so any gating/validation re-runs. */
  function fillField(name, value) {
    const field = document.querySelector(`[name="${name}"]`);
    if (!field || value == null || value === "") return;
    field.value = value;
    field.dispatchEvent(new Event("input", { bubbles: true }));
  }

  /** Copies one Brreg "enhet" record into the form fields. */
  function applyUnit(unit) {
    fillField("company_name", unit.navn || "");
    fillField("company_number", unit.organisasjonsnummer || "");
    if (unit.antallAnsatte != null) fillField("employees", String(unit.antallAnsatte));
    if (unit.hjemmeside) {
      const site = unit.hjemmeside.trim();
      fillField("website", /^https?:\/\//i.test(site) ? site : `https://${site}`);
    }
    const addr = unit.forretningsadresse || {};
    if (Array.isArray(addr.adresse) && addr.adresse.filter(Boolean).length) {
      fillField("address", addr.adresse.filter(Boolean).join(", "));
    }
    fillField("postal_code", addr.postnummer || "");
    if (addr.poststed) fillField("city", titleCasePlace(addr.poststed));
  }

  function initField(wrapper) {
    const input = wrapper.querySelector("[data-brreg-input]");
    const list = wrapper.querySelector("[data-brreg-suggestions]");
    if (!input || !list) return;

    let debounceTimer = null;
    let abortController = null;
    // Bumped on every search AND on selection — a fetch .then() whose token
    // no longer matches is stale and must not touch the dropdown.
    let searchToken = 0;
    // True only while applyUnit() writes the picked company in: filling
    // [name="company_name"] dispatches "input", which would otherwise
    // re-enter the handler below and reopen the list we just closed.
    let applyingSelection = false;

    const closeList = () => {
      list.hidden = true;
      list.innerHTML = "";
      input.setAttribute("aria-expanded", "false");
    };

    const renderList = (units) => {
      list.innerHTML = "";
      if (!units.length) {
        closeList();
        return;
      }
      units.forEach((unit) => {
        const li = document.createElement("li");
        const button = document.createElement("button");
        button.type = "button";
        const place = titleCasePlace((unit.forretningsadresse || {}).poststed || "");
        button.innerHTML =
          `<span>${unit.navn || ""}</span>` +
          `<span class="address-suggestions__meta brreg-suggestions__meta">Org.nr. ${unit.organisasjonsnummer || "—"}` +
          `${place ? ` · ${place}` : ""}</span>`;
        // mousedown (not click) fires before the input's blur hides the list.
        button.addEventListener("mousedown", (event) => {
          event.preventDefault();
          searchToken++;
          clearTimeout(debounceTimer);
          abortController?.abort();
          applyingSelection = true;
          applyUnit(unit);
          applyingSelection = false;
          closeList();
        });
        li.appendChild(button);
        list.appendChild(li);
      });
      list.hidden = false;
      input.setAttribute("aria-expanded", "true");
    };

    input.setAttribute("autocomplete", "off");
    input.setAttribute("role", "combobox");
    input.setAttribute("aria-autocomplete", "list");
    input.setAttribute("aria-expanded", "false");

    input.addEventListener("input", () => {
      if (applyingSelection) return;
      const query = input.value.trim();
      clearTimeout(debounceTimer);
      abortController?.abort();
      const token = ++searchToken;
      if (query.length < 2) {
        closeList();
        return;
      }
      debounceTimer = setTimeout(() => {
        abortController = new AbortController();
        fetch(`${BRREG_URL}?navn=${encodeURIComponent(query)}&size=8`, { signal: abortController.signal })
          .then((response) => (response.ok ? response.json() : null))
          .then((data) => {
            if (token !== searchToken || !data) return;
            renderList((data._embedded && data._embedded.enheter) || []);
          })
          .catch(() => {
            // Aborted or network/API error — leave every field for manual entry.
          });
      }, 250);
    });

    input.addEventListener("blur", () => {
      clearTimeout(debounceTimer);
      abortController?.abort();
      setTimeout(closeList, 120);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-brreg-field]").forEach(initField);
  });
})();
