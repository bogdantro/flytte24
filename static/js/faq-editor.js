// static/js/faq-editor.js
//
// Turns a single "Spørsmål og svar" textarea into a repeatable
// question/answer editor. The real value lives in a hidden <textarea
// name="faq"> as a JSON array [{"question": "...", "answer": "..."}], which
// the form submits unchanged.
//
// Markup contract:
//   <div class="faq-editor" data-faq-editor>
//     <div data-faq-list></div>
//     <button type="button" data-faq-add>…</button>
//     <textarea name="faq" data-faq-store hidden>…existing value…</textarea>
//   </div>

(function () {
  "use strict";

  document.querySelectorAll("[data-faq-editor]").forEach(init);

  function init(root) {
    var store = root.querySelector("[data-faq-store]");
    var list = root.querySelector("[data-faq-list]");
    var addBtn = root.querySelector("[data-faq-add]");
    if (!store || !list || !addBtn) return;

    var items = parse(store.value);

    addBtn.addEventListener("click", function () {
      items.push({ question: "", answer: "" });
      render();
      var qs = list.querySelectorAll(".faq-editor__q");
      if (qs.length) qs[qs.length - 1].focus();
    });

    render();

    // --------------------------------------------------------------

    function parse(raw) {
      raw = (raw || "").trim();
      if (!raw) return [];
      try {
        var parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          return parsed
            .map(function (x) {
              return {
                question: String((x && (x.question || x.q)) || ""),
                answer: String((x && (x.answer || x.a)) || ""),
              };
            });
        }
      } catch (e) { /* fall through to legacy plain-text parsing */ }

      // Legacy free text: blank-line-separated blocks, first line = question.
      return raw
        .split(/\n\s*\n/)
        .map(function (block) {
          var lines = block.split("\n");
          return { question: (lines.shift() || "").trim(), answer: lines.join("\n").trim() };
        })
        .filter(function (it) { return it.question || it.answer; });
    }

    function serialize() {
      var clean = items
        .map(function (it) {
          return { question: (it.question || "").trim(), answer: (it.answer || "").trim() };
        })
        .filter(function (it) { return it.question || it.answer; });
      store.value = clean.length ? JSON.stringify(clean) : "";
    }

    function render() {
      list.innerHTML = "";

      if (!items.length) {
        var empty = document.createElement("p");
        empty.className = "faq-editor__empty";
        empty.textContent = "Ingen spørsmål lagt til ennå.";
        list.appendChild(empty);
      }

      items.forEach(function (item, index) {
        var row = document.createElement("div");
        row.className = "faq-editor__row";
        row.innerHTML =
          '<div class="faq-editor__num">' + (index + 1) + "</div>" +
          '<div class="faq-editor__fields">' +
          '  <input type="text" class="faq-editor__q" placeholder="Spørsmål">' +
          '  <textarea class="faq-editor__a" rows="2" placeholder="Svar"></textarea>' +
          "</div>" +
          '<button type="button" class="faq-editor__remove" aria-label="Fjern spørsmål"><span data-icon="x"></span></button>';

        var q = row.querySelector(".faq-editor__q");
        var a = row.querySelector(".faq-editor__a");
        q.value = item.question;
        a.value = item.answer;

        q.addEventListener("input", function () { items[index].question = q.value; serialize(); });
        a.addEventListener("input", function () { items[index].answer = a.value; serialize(); });
        row.querySelector(".faq-editor__remove").addEventListener("click", function () {
          items.splice(index, 1);
          render();
          serialize();
        });

        list.appendChild(row);
      });

      if (window.KoblyDashboard && typeof window.KoblyDashboard.hydrateIcons === "function") {
        window.KoblyDashboard.hydrateIcons();
      }
      serialize();
    }
  }
})();
