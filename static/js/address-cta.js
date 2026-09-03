// static/js/address-cta.js
//
// The marketing-page "Hvor skal du flytte fra?" CTA — an address search
// box (Kartverket / Geonorge, the same free keyless API as the lead
// wizard's address autocomplete). Picking a suggestion, or submitting a
// typed value, sends the visitor into the wizard at
//   /flytteforesporsel/?fra=<address>
// where apps.leads.views.wizard drops it straight into "Fra adresse".
//
// Markup contract — one or more:
//   <form data-address-cta novalidate>
//     <div class="address-cta__row">
//       <div class="address-cta__field">
//         <input type="text" data-address-cta-input ...>
//         <ul class="address-cta__suggestions" data-address-cta-suggestions hidden></ul>
//       </div>
//       <button type="submit">…</button>
//     </div>
//     <p class="address-cta__error" data-address-cta-error hidden>…</p>
//   </form>

(function () {
  "use strict";

  const GEONORGE = "https://ws.geonorge.no/adresser/v1/sok";

  async function search(query, signal) {
    try {
      const url = `${GEONORGE}?sok=${encodeURIComponent(query)}&treffPerSide=6&side=0`;
      const response = await fetch(url, { signal });
      if (!response.ok) return [];
      const json = await response.json();
      return json.adresser || [];
    } catch {
      return [];
    }
  }

  function go(value) {
    window.location.href = `/flytteforesporsel/?fra=${encodeURIComponent(value)}`;
  }

  function initForm(form) {
    const input = form.querySelector("[data-address-cta-input]");
    const list = form.querySelector("[data-address-cta-suggestions]");
    const error = form.querySelector("[data-address-cta-error]");
    if (!input || !list) return;

    let debounceTimer = null;
    let abortController = null;
    let token = 0;
    let picking = false; // programmatic value write from a suggestion click

    const close = () => {
      list.hidden = true;
      list.innerHTML = "";
      input.setAttribute("aria-expanded", "false");
    };

    const render = (addresses) => {
      list.innerHTML = "";
      if (!addresses.length) {
        close();
        return;
      }
      addresses.forEach((addr) => {
        const li = document.createElement("li");
        const button = document.createElement("button");
        button.type = "button";
        const full = `${addr.adressetekst}, ${addr.postnummer} ${addr.poststed}`;
        button.innerHTML =
          `<span>${addr.adressetekst}</span>` +
          `<span class="address-cta__meta">${addr.postnummer} ${addr.poststed}</span>`;
        // mousedown fires before the input's blur handler closes the list.
        button.addEventListener("mousedown", (event) => {
          event.preventDefault();
          token++;
          clearTimeout(debounceTimer);
          abortController?.abort();
          picking = true;
          input.value = full;
          picking = false;
          close();
          if (error) error.hidden = true;
          go(full);
        });
        li.appendChild(button);
        list.appendChild(li);
      });
      list.hidden = false;
      input.setAttribute("aria-expanded", "true");
    };

    input.addEventListener("input", () => {
      if (picking) return;
      const query = input.value.trim();
      clearTimeout(debounceTimer);
      abortController?.abort();
      const mine = ++token;
      if (query.length < 3) {
        close();
        return;
      }
      debounceTimer = setTimeout(async () => {
        abortController = new AbortController();
        const results = await search(query, abortController.signal);
        if (mine !== token) return;
        render(results);
      }, 200);
    });

    input.addEventListener("blur", () => {
      clearTimeout(debounceTimer);
      abortController?.abort();
      setTimeout(close, 120);
    });

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const value = input.value.trim();
      if (value.length < 3) {
        if (error) error.hidden = false;
        return;
      }
      if (error) error.hidden = true;
      go(value);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-address-cta]").forEach(initForm);
  });
})();
