// static/js/coverage-onboarding.js
//
// Popup-driven structured coverage, inside the Dekning section (account
// portal business_edit_profile.html, admin business_detail.html).
//
// The "Byer dere dekker" checkboxes stay the top-level control. Ticking a
// city (Oslo, Bergen, …) opens a popup for that city's region asking which
// nearby places the business also serves and in which direction:
//   ↔  both     — jobs to *and* from the place (two-way)
//   →  pickup   — only jobs that start here (one-way out)
//   ←  dropoff  — only jobs that end here (one-way in)
// A "Hele <region>" master pill ticks/unticks every place in the region.
// The chosen places are listed under the checkboxes as a summary; clicking
// a summary chip reopens that region's popup. Unticking a city drops every
// place in its region.
//
// State -> hidden [data-service-areas-input] as
//   [{"place": "...", "pickup": true, "dropoff": false}, ...]
// and every change dispatches a bubbling "coverage:changed" event so the
// surrounding coverage form (account-portal.js / dashboard.js) saves.
//
// Config: <script type="application/json" data-coverage-config> with
//   { regions: {name: [places...]}, selected: {place: {pickup,dropoff}} }
// (each region's first place is its main city).

(function () {
  "use strict";

  const DIRECTIONS = [
    { key: "both", label: "↔", title: "Til og fra (toveis)", pickup: true, dropoff: true },
    { key: "pickup", label: "→", title: "Kun fra dette stedet (enveis)", pickup: true, dropoff: false },
    { key: "dropoff", label: "←", title: "Kun til dette stedet (enveis)", pickup: false, dropoff: true },
  ];

  function dirOf(entry) {
    if (entry.pickup && entry.dropoff) return "both";
    if (entry.pickup) return "pickup";
    return "dropoff";
  }

  function init(root) {
    const configEl = root.querySelector("[data-coverage-config]");
    const hidden = root.querySelector("[data-service-areas-input]");
    const summary = root.querySelector("[data-coverage-summary]");
    const modal = root.querySelector("[data-coverage-modal]");
    if (!configEl || !hidden || !summary || !modal) return;

    let config;
    try {
      config = JSON.parse(configEl.textContent);
    } catch {
      return;
    }
    const regions = config.regions || {};
    const mainCityToRegion = {};
    Object.entries(regions).forEach(([name, places]) => {
      if (places.length) mainCityToRegion[places[0]] = name;
    });
    const regionOf = (place) => {
      for (const [name, places] of Object.entries(regions)) {
        if (places.includes(place)) return name;
      }
      return null;
    };

    // place -> {pickup, dropoff}
    const selected = new Map(
      Object.entries(config.selected || {}).map(([place, v]) => [
        place,
        { pickup: v.pickup !== false, dropoff: v.dropoff !== false },
      ])
    );

    const form = root.closest("form");
    const cityBoxes = form ? Array.from(form.querySelectorAll('input[name="cities"]')) : [];

    function serialise() {
      const list = [];
      selected.forEach((v, place) => list.push({ place, pickup: v.pickup, dropoff: v.dropoff }));
      hidden.value = JSON.stringify(list);
      root.dispatchEvent(new CustomEvent("coverage:changed", { bubbles: true }));
    }

    function syncCityBoxes() {
      // A city box is ticked iff at least one place in its region is selected.
      cityBoxes.forEach((box) => {
        const region = mainCityToRegion[box.value];
        const places = regions[region] || [];
        box.checked = places.some((p) => selected.has(p));
      });
    }

    function renderSummary() {
      summary.innerHTML = "";
      if (!selected.size) {
        summary.hidden = true;
        return;
      }
      summary.hidden = false;
      // Group by region so the summary reads region-by-region.
      Object.entries(regions).forEach(([region, places]) => {
        const picked = places.filter((p) => selected.has(p));
        if (!picked.length) return;
        const group = document.createElement("div");
        group.className = "coverage-summary__group";
        const label = document.createElement("button");
        label.type = "button";
        label.className = "coverage-summary__region";
        label.textContent = region;
        label.addEventListener("click", () => openModal(region));
        group.appendChild(label);
        picked.forEach((place) => {
          const dir = DIRECTIONS.find((d) => d.key === dirOf(selected.get(place)));
          const chip = document.createElement("button");
          chip.type = "button";
          chip.className = "coverage-summary__chip";
          chip.innerHTML = `${place} <span aria-hidden="true">${dir.label}</span>`;
          chip.title = dir.title;
          chip.addEventListener("click", () => openModal(region));
          group.appendChild(chip);
        });
        summary.appendChild(group);
      });
    }

    // ---- modal ----
    const modalTitle = modal.querySelector("[data-coverage-modal-title]");
    const modalBody = modal.querySelector("[data-coverage-modal-body]");
    let modalRegion = null;

    function renderModalBody() {
      const places = regions[modalRegion] || [];
      modalBody.innerHTML = "";

      const allOn = places.every((p) => selected.has(p));
      const master = document.createElement("button");
      master.type = "button";
      master.className = "coverage-modal__all" + (allOn ? " is-on" : "");
      master.innerHTML = `<span>Hele ${modalRegion}</span><span>${allOn ? "Fjern alle" : "Velg alle"}</span>`;
      master.addEventListener("click", () => {
        if (allOn) places.forEach((p) => selected.delete(p));
        else places.forEach((p) => { if (!selected.has(p)) selected.set(p, { pickup: true, dropoff: true }); });
        serialise();
        renderModalBody();
      });
      modalBody.appendChild(master);

      const list = document.createElement("ul");
      list.className = "coverage-place-list";
      places.forEach((place) => {
        const on = selected.has(place);
        const li = document.createElement("li");
        li.className = "coverage-place-row" + (on ? " is-on" : "");

        const toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "coverage-place-row__toggle";
        toggle.setAttribute("aria-pressed", on ? "true" : "false");
        toggle.innerHTML = `<span class="coverage-place-row__check" aria-hidden="true">${on ? "✓" : ""}</span><span>${place}</span>`;
        toggle.addEventListener("click", () => {
          if (selected.has(place)) selected.delete(place);
          else selected.set(place, { pickup: true, dropoff: true });
          serialise();
          renderModalBody();
        });
        li.appendChild(toggle);

        if (on) {
          const activeKey = dirOf(selected.get(place));
          const dirWrap = document.createElement("div");
          dirWrap.className = "coverage-place-row__dirs";
          DIRECTIONS.forEach((d) => {
            const b = document.createElement("button");
            b.type = "button";
            b.className = "coverage-dir" + (d.key === activeKey ? " is-active" : "");
            b.textContent = d.label;
            b.title = d.title;
            b.setAttribute("aria-label", d.title);
            b.addEventListener("click", () => {
              selected.set(place, { pickup: d.pickup, dropoff: d.dropoff });
              serialise();
              renderModalBody();
            });
            dirWrap.appendChild(b);
          });
          li.appendChild(dirWrap);
        }
        list.appendChild(li);
      });
      modalBody.appendChild(list);
    }

    function openModal(region) {
      modalRegion = region;
      const mainCity = (regions[region] || [])[0] || region;
      modalTitle.textContent = `Hvor jobber dere rundt ${mainCity}?`;
      renderModalBody();
      modal.hidden = false;
      document.body.style.overflow = "hidden";
    }

    function closeModal() {
      modal.hidden = true;
      document.body.style.overflow = "";
      // If the region ended up with nothing selected, untick its city box.
      syncCityBoxes();
      renderSummary();
      serialise();
    }

    modal.querySelectorAll("[data-coverage-modal-close]").forEach((el) =>
      el.addEventListener("click", closeModal)
    );
    const doneBtn = modal.querySelector("[data-coverage-modal-done]");
    if (doneBtn) doneBtn.addEventListener("click", closeModal);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !modal.hidden) closeModal();
    });

    // ---- city checkboxes drive the popups ----
    cityBoxes.forEach((box) => {
      box.addEventListener("change", () => {
        const region = mainCityToRegion[box.value];
        if (!region) return;
        const places = regions[region] || [];
        if (box.checked) {
          if (!selected.has(box.value)) selected.set(box.value, { pickup: true, dropoff: true });
          serialise();
          renderSummary();
          openModal(region);
        } else {
          places.forEach((p) => selected.delete(p));
          serialise();
          renderSummary();
        }
      });
    });

    syncCityBoxes();
    renderSummary();
    serialise();
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-coverage-onboarding]").forEach(init);
  });
})();
