// static/js/business-add-preview.js
//
// Live preview card for the "Ny bedrift" page (dashboard/business_add.html).
// Reads the create form on every input/change and re-renders the sticky
// card on the right. Nothing here is submitted — it's a mirror of what the
// business will look like once created.

(function () {
  "use strict";

  var form = document.querySelector("[data-business-form]");
  var card = document.querySelector("[data-business-preview]");
  if (!form || !card) return;

  var el = {
    name: card.querySelector("[data-preview-name]"),
    meta: card.querySelector("[data-preview-meta]"),
    initials: card.querySelector("[data-preview-initials]"),
    logoWrap: card.querySelector("[data-preview-logo-wrap]"),
    logo: card.querySelector("[data-preview-logo]"),
    logoFallback: card.querySelector("[data-preview-logo-fallback]"),
    citiesWrap: card.querySelector("[data-preview-cities-wrap]"),
    cities: card.querySelector("[data-preview-cities]"),
    servicesWrap: card.querySelector("[data-preview-services-wrap]"),
    services: card.querySelector("[data-preview-services]"),
    areasWrap: card.querySelector("[data-preview-areas-wrap]"),
    areas: card.querySelector("[data-preview-areas]"),
    about: card.querySelector("[data-preview-about]"),
    contact: card.querySelector("[data-preview-contact]"),
    priority: card.querySelector("[data-preview-priority]"),
    cap: card.querySelector("[data-preview-cap]"),
  };

  function val(name) {
    var node = form.querySelector('[name="' + name + '"]');
    return node ? node.value.trim() : "";
  }

  function checkedValues(name) {
    return Array.prototype.map.call(
      form.querySelectorAll('[name="' + name + '"]:checked'),
      function (n) { return n.value; }
    );
  }

  function chip(text) {
    var span = document.createElement("span");
    span.className = "business-preview__chip";
    span.textContent = text;
    return span;
  }

  function renderChips(container, wrap, values) {
    container.innerHTML = "";
    if (!values.length) { wrap.hidden = true; return; }
    values.forEach(function (v) { container.appendChild(chip(v)); });
    wrap.hidden = false;
  }

  function initials(nameText) {
    var parts = nameText.replace(/\b(AS|ASA|ANS|DA|BA)\b/gi, "").trim().split(/\s+/).filter(Boolean);
    if (!parts.length) return "B";
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }

  function render() {
    var name = val("company_name");
    el.name.textContent = name || "Bedriftsnavn";
    el.name.classList.toggle("is-placeholder", !name);
    el.initials.textContent = initials(name);

    var city = val("city");
    var postal = val("postal_code");
    var metaParts = [];
    if (val("address")) metaParts.push(val("address"));
    if (postal || city) metaParts.push((postal + " " + city).trim());
    el.meta.textContent = metaParts.join(" · ");
    el.meta.hidden = metaParts.length === 0;

    renderChips(el.cities, el.citiesWrap, checkedValues("cities"));
    renderChips(el.services, el.servicesWrap, checkedValues("move_type"));

    // Structured coverage places (the ↔/→/← popup) — shown as a plain summary.
    var areas = [];
    try {
      var raw = JSON.parse(val("service_areas") || "[]");
      areas = raw.map(function (a) {
        var arrow = a.pickup && a.dropoff ? "↔" : a.pickup ? "→" : "←";
        return a.place + " " + arrow;
      });
    } catch (e) { areas = []; }
    if (areas.length) {
      el.areas.textContent = areas.join(" · ");
      el.areasWrap.hidden = false;
    } else {
      el.areasWrap.hidden = true;
    }

    var about = val("about_us");
    if (about) {
      el.about.textContent = about.length > 220 ? about.slice(0, 220) + "…" : about;
      el.about.hidden = false;
    } else {
      el.about.hidden = true;
    }

    var contactLines = [];
    if (val("phone")) contactLines.push(val("phone"));
    if (val("email")) contactLines.push(val("email"));
    if (val("website")) contactLines.push(val("website").replace(/^https?:\/\//, ""));
    el.contact.innerHTML = "";
    contactLines.forEach(function (line) {
      var p = document.createElement("p");
      p.textContent = line;
      el.contact.appendChild(p);
    });
    el.contact.hidden = contactLines.length === 0;

    var priority = val("priority_score") || "0";
    el.priority.textContent = "Prioritet " + priority;

    var cap = val("leads_per_day");
    if (cap) {
      el.cap.textContent = "Maks " + cap + " leads/dag";
      el.cap.hidden = false;
    } else {
      el.cap.hidden = true;
    }
  }

  // Logo: read the chosen file and show it.
  var logoInput = form.querySelector('input[type="file"]');
  if (logoInput) {
    logoInput.addEventListener("change", function () {
      var file = logoInput.files && logoInput.files[0];
      if (!file || !/^image\//.test(file.type)) {
        el.logoWrap.hidden = true;
        el.logoFallback.hidden = false;
        return;
      }
      var reader = new FileReader();
      reader.onload = function () {
        el.logo.src = reader.result;
        el.logoWrap.hidden = false;
        el.logoFallback.hidden = true;
      };
      reader.readAsDataURL(file);
    });
  }

  form.addEventListener("input", render);
  form.addEventListener("change", render);
  // coverage-onboarding.js dispatches this when the ↔/→/← places change.
  form.addEventListener("coverage:changed", render);
  document.addEventListener("DOMContentLoaded", render);
  render();
})();
