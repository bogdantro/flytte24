// static/js/lead-map.js
//
// Read-only-or-editable from/to map for a single lead, used on the staff
// dashboard lead detail (dashboard/detail.html, editable) and the business
// portal lead detail (core/accountPages/lead_detail.html, read-only).
//
// Deliberately a small standalone port of static/js/wizard.js's step-1
// desktop map — same CARTO Voyager tiles, same styled from/to pins, dashed
// route line, midpoint Kobly ring and 250m "from" circle — without the
// wizard's step system, address-autocomplete coupling or mobile picker.
//
// Markup contract — one [data-lead-map] element carrying:
//   data-fra / data-fra-lat / data-fra-lon   (lat/lon optional)
//   data-til / data-til-lat / data-til-lon
//   data-editable            present -> pins are draggable and saved
//   data-save-url            POST target for a moved pin (editable only)
// and inside it: [data-map-container], [data-map-chip] (+ -from/-to),
// [data-map-zoom-in], [data-map-zoom-out].

(function () {
  "use strict";

  if (typeof L === "undefined") return;

  const PIN_COLOR_FROM = "#221814";
  const PIN_COLOR_TO = "#3D5507";
  // CARTO raster tiles now require an account API key (window.KOBLY_CARTO_API_KEY,
  // set by the page from settings.CARTO_API_KEY).
  const CARTO_KEY = (typeof window !== "undefined" && window.KOBLY_CARTO_API_KEY) || "";
  const TILE_URL =
    "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png" +
    (CARTO_KEY ? `?key=${encodeURIComponent(CARTO_KEY)}` : "");
  const GEONORGE_SEARCH = "https://ws.geonorge.no/adresser/v1/sok";
  const GEONORGE_POINT = "https://ws.geonorge.no/adresser/v1/punktsok";

  function getCsrfToken() {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  /** Colored circle + white house-pin glyph — identical to the wizard's pins. */
  function pinIcon(color) {
    return L.divIcon({
      className: "",
      html: `<div style="width:36px;height:36px;background:${color};border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,0.3);border:2px solid white"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg></div>`,
      iconSize: [36, 36],
      iconAnchor: [18, 18],
    });
  }

  /** Small white Kobly-ring icon shown at the midpoint of the from/to line. */
  function midpointIcon() {
    return L.divIcon({
      className: "",
      html: `<div style="width:32px;height:32px;background:white;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.18);border:1.5px solid #E6E1D6"><svg width="16" height="16" viewBox="0 0 27 27" fill="none"><circle cx="13.5" cy="13.5" r="11.625" stroke="#221814" stroke-width="3.75"/><path d="M16.5 1.875C12.7075 5.23556 10.5 9.26144 10.5 13.5887C10.5 17.8401 12.6307 21.8006 16.3019 25.125" stroke="#221814" stroke-width="3.75"/></svg></div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });
  }

  /** Forward-geocodes an address string to {lat, lon} via Geonorge, or null. */
  async function geocode(address) {
    if (!address) return null;
    try {
      const url = `${GEONORGE_SEARCH}?sok=${encodeURIComponent(address)}&treffPerSide=1&side=0`;
      const response = await fetch(url);
      if (!response.ok) return null;
      const json = await response.json();
      const hit = (json.adresser || [])[0];
      const point = hit && hit.representasjonspunkt;
      return point ? { lat: point.lat, lon: point.lon } : null;
    } catch {
      return null;
    }
  }

  /** Reverse-geocodes one coordinate to a readable address, or falls back. */
  async function reverseGeocode(lat, lon, fallbackText) {
    try {
      const url = `${GEONORGE_POINT}?radius=200&lat=${lat}&lon=${lon}&treffPerSide=1&side=0`;
      const response = await fetch(url);
      if (!response.ok) return fallbackText;
      const json = await response.json();
      const hit = (json.adresser || [])[0];
      return hit ? `${hit.adressetekst}, ${hit.postnummer} ${hit.poststed}` : fallbackText;
    } catch {
      return fallbackText;
    }
  }

  function numberOrNull(value) {
    const n = parseFloat(value);
    return Number.isFinite(n) ? n : null;
  }

  function initLeadMap(panel) {
    const editable = panel.hasAttribute("data-editable");
    const saveUrl = panel.getAttribute("data-save-url");

    const state = {
      fra: {
        text: panel.dataset.fra || "",
        lat: numberOrNull(panel.dataset.fraLat),
        lon: numberOrNull(panel.dataset.fraLon),
      },
      til: {
        text: panel.dataset.til || "",
        lat: numberOrNull(panel.dataset.tilLat),
        lon: numberOrNull(panel.dataset.tilLon),
      },
    };

    const map = L.map(panel.querySelector("[data-map-container]"), {
      center: [60.5, 10.0],
      zoom: 5,
      zoomControl: false,
      attributionControl: false,
    });
    L.tileLayer(TILE_URL, { maxZoom: 19 }).addTo(map);

    let fromMarker = null;
    let toMarker = null;
    let fromCircle = null;
    let line = null;
    let midpointMarker = null;

    function redrawOverlays(fit) {
      if (fromMarker && toMarker) {
        const a = fromMarker.getLatLng();
        const b = toMarker.getLatLng();
        const latlngs = [a, b];
        if (line) line.setLatLngs(latlngs);
        else line = L.polyline(latlngs, { color: "#221814", weight: 2.5, dashArray: "6 6", opacity: 0.7 }).addTo(map);
        const mid = [(a.lat + b.lat) / 2, (a.lng + b.lng) / 2];
        if (midpointMarker) midpointMarker.setLatLng(mid);
        else midpointMarker = L.marker(mid, { icon: midpointIcon(), interactive: false, zIndexOffset: 500 }).addTo(map);
        if (fit) map.fitBounds(latlngs, { padding: [40, 40], maxZoom: 13 });
      } else if (fromMarker || toMarker) {
        const only = (fromMarker || toMarker).getLatLng();
        if (fit) map.setView(only, 12);
      }
      if (fromMarker) {
        const ll = fromMarker.getLatLng();
        if (fromCircle) fromCircle.setLatLng(ll);
        else fromCircle = L.circle(ll, { radius: 250, color: "#221814", fillColor: "#221814", fillOpacity: 0.08, opacity: 0.25, weight: 1, interactive: false }).addTo(map);
      }
      updateChip();
    }

    function updatePositionsDuringDrag() {
      if (fromMarker && toMarker && line) {
        const a = fromMarker.getLatLng();
        const b = toMarker.getLatLng();
        line.setLatLngs([a, b]);
        if (midpointMarker) midpointMarker.setLatLng([(a.lat + b.lat) / 2, (a.lng + b.lng) / 2]);
      }
      if (fromMarker && fromCircle) fromCircle.setLatLng(fromMarker.getLatLng());
    }

    function updateChip() {
      const chip = panel.querySelector("[data-map-chip]");
      if (!chip) return;
      const fraShort = (state.fra.text || "").split(",")[0].trim();
      const tilShort = (state.til.text || "").split(",")[0].trim();
      if (!fraShort && !tilShort) { chip.hidden = true; return; }
      chip.querySelector("[data-map-chip-from]").textContent = fraShort || "—";
      chip.querySelector("[data-map-chip-to]").textContent = tilShort || "—";
      chip.hidden = false;
    }

    async function persist(which, lat, lon, address) {
      if (!editable || !saveUrl) return;
      const body = new URLSearchParams({ which, lat, lon, address: address || "" });
      try {
        await fetch(saveUrl, {
          method: "POST",
          headers: { "X-CSRFToken": getCsrfToken(), "Content-Type": "application/x-www-form-urlencoded" },
          body: body.toString(),
        });
      } catch {
        // Best-effort — a failed save just means the pin snaps back on reload.
      }
    }

    function setPin(which, lat, lon) {
      const color = which === "fra" ? PIN_COLOR_FROM : PIN_COLOR_TO;
      const existing = which === "fra" ? fromMarker : toMarker;
      if (existing) {
        existing.setLatLng([lat, lon]);
      } else {
        const marker = L.marker([lat, lon], { icon: pinIcon(color), draggable: editable, autoPan: editable }).addTo(map);
        if (editable) {
          marker.on("drag", updatePositionsDuringDrag);
          marker.on("dragend", async () => {
            const ll = marker.getLatLng();
            const address = await reverseGeocode(ll.lat, ll.lng, state[which].text || "Pin plassert i kart");
            state[which].text = address;
            state[which].lat = ll.lat;
            state[which].lon = ll.lng;
            redrawOverlays(true);
            persist(which, ll.lat, ll.lng, address);
          });
        }
        if (which === "fra") fromMarker = marker; else toMarker = marker;
      }
    }

    async function placeInitial(which) {
      let { lat, lon } = state[which];
      if (lat === null || lon === null) {
        const geo = await geocode(state[which].text);
        if (!geo) return;
        lat = geo.lat;
        lon = geo.lon;
        state[which].lat = lat;
        state[which].lon = lon;
        // A geocode-derived coordinate is worth saving so the next visit is instant.
        persist(which, lat, lon, "");
      }
      setPin(which, lat, lon);
    }

    const zoomIn = panel.querySelector("[data-map-zoom-in]");
    const zoomOut = panel.querySelector("[data-map-zoom-out]");
    if (zoomIn) zoomIn.addEventListener("click", () => map.zoomIn());
    if (zoomOut) zoomOut.addEventListener("click", () => map.zoomOut());

    Promise.all([placeInitial("fra"), placeInitial("til")]).then(() => redrawOverlays(true));

    // Leaflet needs a nudge once its container has a real size (cards animate/reflow).
    setTimeout(() => map.invalidateSize(), 120);
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-lead-map]").forEach(initLeadMap);
  });
})();
