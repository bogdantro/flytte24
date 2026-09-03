// static/js/upload-tile.js
//
// Turns a
//   <label class="upload-tile" data-upload-tile>
//     <span data-icon="upload"></span><span class="upload-tile__label">Velg bilde</span>
//     <input type="file" accept="image/*" ...>
//   </label>
// into a styled drop-tile with a live thumbnail — the same "no native
// Choose File button" treatment the wizard forms use. The <input> stays
// the real control the surrounding <form> submits; it is only visually
// hidden by CSS.

(function () {
  "use strict";

  function init(tile) {
    const input = tile.querySelector('input[type="file"]');
    if (!input) return;

    input.addEventListener("change", () => {
      const file = input.files && input.files[0];
      if (!file) return;

      let preview = tile.querySelector("[data-upload-tile-preview]");
      if (!preview) {
        preview = document.createElement("img");
        preview.setAttribute("data-upload-tile-preview", "");
        preview.alt = "";
        tile.prepend(preview);
      }
      preview.src = URL.createObjectURL(file);
      tile.classList.add("has-file");

      const label = tile.querySelector(".upload-tile__label");
      if (label) label.textContent = file.name;
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-upload-tile]").forEach(init);
  });
})();
