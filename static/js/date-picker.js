// static/js/date-picker.js
//
// Standalone custom calendar-modal date picker — a generic port of
// static/js/wizard.js's initDatePicker(), without the wizard's "fleksibel"
// toggle / Neste-button coupling, so it can be reused on any page that
// wants the all-Norwegian calendar instead of the browser's locale-dependent
// native <input type="date">.
//
// Markup contract:
//   <div class="date-field" data-date-picker>
//     <button type="button" class="date-field__trigger field-input" data-date-picker-trigger>
//       <span data-date-picker-label>Velg dato</span><span data-icon="calendar"></span>
//     </button>
//     <input type="hidden" name="..." data-date-input value="YYYY-MM-DD">
//   </div>
// plus ONE shared overlay per page (leads/_date_overlay.html):
//   [data-date-overlay] > [data-date-overlay-backdrop|-prev|-next|-close|
//                          -month|-weekdays|-grid|-time|-hours|-minutes|-confirm]
//
// data-min-today  on a [data-date-picker] disables past days.
// data-with-time  adds an HH:MM row; the hidden value becomes
//                 "YYYY-MM-DDTHH:MM" instead of "YYYY-MM-DD".

(function () {
  "use strict";

  function toIsoDate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  }

  function parseValue(raw) {
    if (!raw) return { date: null, hours: 9, minutes: 0 };
    const [datePart, timePart] = raw.split("T");
    const [y, m, d] = datePart.split("-").map(Number);
    const date = y && m && d ? new Date(y, m - 1, d) : null;
    let hours = 9;
    let minutes = 0;
    if (timePart) {
      const [h, mi] = timePart.split(":").map(Number);
      if (Number.isFinite(h)) hours = h;
      if (Number.isFinite(mi)) minutes = mi;
    }
    return { date, hours, minutes };
  }

  function pad2(n) {
    return String(n).padStart(2, "0");
  }

  function initDatePickers() {
    const overlay = document.querySelector("[data-date-overlay]");
    if (!overlay) return;
    const fields = document.querySelectorAll("[data-date-picker]");
    if (!fields.length) return;

    let viewDate = new Date();
    let selectedDate = null;
    let activeField = null;

    const grid = overlay.querySelector("[data-date-overlay-grid]");
    const monthLabel = overlay.querySelector("[data-date-overlay-month]");
    const confirmBtn = overlay.querySelector("[data-date-overlay-confirm]");
    const timeRow = overlay.querySelector("[data-date-overlay-time]");
    const hoursInput = overlay.querySelector("[data-date-overlay-hours]");
    const minutesInput = overlay.querySelector("[data-date-overlay-minutes]");

    const withTime = (field) => field && field.hasAttribute("data-with-time");

    function refreshTriggerLabel(field) {
      const hidden = field.querySelector("[data-date-input]");
      const label = field.querySelector("[data-date-picker-label]");
      const { date, hours, minutes } = parseValue(hidden.value);
      if (!date) {
        label.textContent = "Velg dato";
        return;
      }
      let text = date.toLocaleDateString("no-NO", { day: "numeric", month: "long", year: "numeric" });
      if (withTime(field) && hidden.value.includes("T")) {
        text += ` ${pad2(hours)}:${pad2(minutes)}`;
      }
      label.textContent = text;
    }

    function renderWeekdays() {
      const weekdaysEl = overlay.querySelector("[data-date-overlay-weekdays]");
      if (weekdaysEl.childElementCount > 0) return;
      const monday = new Date(1970, 0, 5); // a Monday
      for (let i = 0; i < 7; i++) {
        const d = new Date(monday);
        d.setDate(monday.getDate() + i);
        const cell = document.createElement("span");
        cell.textContent = d.toLocaleDateString("no-NO", { weekday: "short" });
        weekdaysEl.appendChild(cell);
      }
    }

    function renderGrid() {
      monthLabel.textContent = viewDate.toLocaleDateString("no-NO", { month: "long", year: "numeric" });
      grid.innerHTML = "";

      const year = viewDate.getFullYear();
      const month = viewDate.getMonth();
      const firstWeekday = (new Date(year, month, 1).getDay() + 6) % 7; // Monday-first
      const daysInMonth = new Date(year, month + 1, 0).getDate();
      for (let i = 0; i < firstWeekday; i++) grid.appendChild(document.createElement("span"));

      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const minToday = activeField && activeField.hasAttribute("data-min-today");

      for (let day = 1; day <= daysInMonth; day++) {
        const cellDate = new Date(year, month, day);
        const button = document.createElement("button");
        button.type = "button";
        button.className = "date-overlay__day";
        button.textContent = String(day);
        if (minToday && cellDate < today) button.disabled = true;
        if (toIsoDate(cellDate) === toIsoDate(today)) button.classList.add("is-today");
        if (selectedDate && toIsoDate(cellDate) === toIsoDate(selectedDate)) button.classList.add("is-selected");
        button.addEventListener("click", () => {
          selectedDate = cellDate;
          confirmBtn.disabled = false;
          renderGrid();
        });
        grid.appendChild(button);
      }
    }

    function open(field) {
      activeField = field;
      const hidden = field.querySelector("[data-date-input]");
      const { date, hours, minutes } = parseValue(hidden.value);
      selectedDate = date;
      const base = selectedDate || new Date();
      viewDate = new Date(base.getFullYear(), base.getMonth(), 1);

      const hasTime = withTime(field);
      if (timeRow) timeRow.hidden = !hasTime;
      if (hasTime && hoursInput && minutesInput) {
        hoursInput.value = pad2(hours);
        minutesInput.value = pad2(minutes);
      }

      renderWeekdays();
      renderGrid();
      confirmBtn.disabled = !selectedDate;
      overlay.hidden = false;
      document.body.style.overflow = "hidden";
    }

    function close() {
      overlay.hidden = true;
      document.body.style.overflow = "";
      activeField = null;
    }

    fields.forEach((field) => {
      field.querySelector("[data-date-picker-trigger]").addEventListener("click", () => open(field));
      refreshTriggerLabel(field);
    });

    overlay.querySelector("[data-date-overlay-close]").addEventListener("click", close);
    overlay.querySelector("[data-date-overlay-backdrop]").addEventListener("click", close);
    overlay.querySelector("[data-date-overlay-prev]").addEventListener("click", () => {
      viewDate.setMonth(viewDate.getMonth() - 1);
      renderGrid();
    });
    overlay.querySelector("[data-date-overlay-next]").addEventListener("click", () => {
      viewDate.setMonth(viewDate.getMonth() + 1);
      renderGrid();
    });
    confirmBtn.addEventListener("click", () => {
      if (!selectedDate || !activeField) return;
      const hidden = activeField.querySelector("[data-date-input]");
      let value = toIsoDate(selectedDate);
      if (withTime(activeField) && hoursInput && minutesInput) {
        const h = Math.min(23, Math.max(0, parseInt(hoursInput.value, 10) || 0));
        const mi = Math.min(59, Math.max(0, parseInt(minutesInput.value, 10) || 0));
        value += `T${pad2(h)}:${pad2(mi)}`;
      }
      hidden.value = value;
      hidden.dispatchEvent(new Event("input", { bubbles: true }));
      refreshTriggerLabel(activeField);
      close();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !overlay.hidden) close();
    });
  }

  document.addEventListener("DOMContentLoaded", initDatePickers);
})();
