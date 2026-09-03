# Property / Building Information Lookup — Design

**Date:** 2026-09-02
**Status:** Implemented (provider = mock; Norkart provider scaffolded with TODO mappings)
**Scope:** New dedicated step in the customer lead wizard (`/flytteforesporsel/`) that
verifies a Norwegian origin address against Kartverket and retrieves building
information for it through a swappable provider layer.

---

## 1. Decisions (locked)

| Question | Decision |
|---|---|
| Placement in wizard | **New dedicated step 2** ("Din nåværende bolig"). Existing step 1 (fra + til + map) untouched. Steps become 6 total. |
| Which address | **Origin (`fra`) only.** Destination stays a plain address + coordinate. |
| Persistence / trust | **`PropertyLookup` model + opaque token.** Wizard submits only the token; server reloads the row and never trusts hidden JSON. Key values also denormalized onto `MoveLead`. |
| Provider now | **Scaffold Norkart, ship on `mock`.** `NorkartBuildingProvider` has config + auth skeleton + `TODO` field mappings (no invented endpoints/fields). `MockBuildingProvider` is the dev default. |
| Manual override of API-found values | **Included, minimal.** Manual fallback fields double as override inputs; any edit flips `data_source` / `bolig_datakilde` to `"user"`. |

---

## 2. Architecture & file layout

Feature is wizard-owned → lives in `apps/leads/`.

```
apps/leads/property/
    __init__.py
    exceptions.py        # PropertyLookupError hierarchy; ERROR_CODES constants
    client.py            # HttpClient: requests.Session wrapper, timeout, HTTP status -> exception
    kartverket.py        # geonorge address search + re-verify one address by components
    normalizer.py        # normalize_address(hit), normalize_norkart_building(raw)
    unit_codes.py        # parse_bruksenhet_code("H0201") -> {level_type, floor, running_no}
    service.py           # PropertyLookupService(provider).lookup(verified_address) -> normalized dict
    providers/
        __init__.py      # get_provider() factory <- settings.PROPERTY_PROVIDER
        base.py          # BuildingDataProvider ABC: get_building_from_address(address)
        mock.py          # MockBuildingProvider: fixtures house / apartment / missing-data / not-found
        norkart.py       # NorkartBuildingProvider: auth + request skeleton + TODO mappings

apps/leads/api_views.py  # thin: address_search, property_lookup
static/js/property-lookup.js
```

SCSS: a new section in `static/scss/wizard.scss` (comment-banner style, compiled with `sass`).

---

## 3. Backend endpoints

Registered in `apps/leads/urls.py` under `/flytteforesporsel/`.

### `GET api/adresse-sok/?q=<text>`

1. Validate `q`: 3–150 chars. `< 3` → `{"results": []}`. `> 150` → `400`.
2. Per-IP rate limit via `django.core.cache` (same `cache.add` + `cache.incr` pattern as
   `apps/dashboard/views.py` login lockout): ~30 requests / 10 s → `429 RATE_LIMITED`.
3. Response cache keyed `propsearch:<slug(q)>` for 120 s.
4. Proxy `https://ws.geonorge.no/adresser/v1/sok?sok=<q>&treffPerSide=8&fuzzy=true`.
5. Map each hit to only:
   `id, label, secondary_label, street, house_number, house_letter, postal_code,
   postal_city, municipality, municipality_number, latitude, longitude`.
   - `label` = `adressetekst` (e.g. "Storgata 10")
   - `secondary_label` = `"<postnummer> <poststed>"`
   - `id` = `django.core.signing.dumps({kommunenummer, adressekode, nummer, bokstav, gnr, bnr})`
     — opaque signed token; the frontend never parses it.
6. Geonorge failure / timeout / non-JSON → `{"results": []}` (logged, never 500).

### `POST api/eiendom/`  (CSRF-protected)

Body: `{"address_id": "<signed token>"}`. Any `address` object in the body is ignored.

1. `signing.loads(address_id, max_age=86400)` → components. `BadSignature` / `SignatureExpired`
   → `400 {"success": false, "error": {"code": "INVALID_ADDRESS", ...}}`.
2. `kartverket.verify_address(components)` — one exact Geonorge query
   (`kommunenummer`, `gardsnummer`, `bruksnummer`, `adressekode`, `nummer`, `bokstav`).
   0 hits → `ADDRESS_NOT_FOUND`. ≥1 hit → the **verified address** dict.
3. Building lookup cache: `propbuilding:<kommunenr>-<gnr>-<bnr>` for
   `PROPERTY_LOOKUP_CACHE_SECONDS` (skipped when provider is `mock`).
4. `PropertyLookupService(get_provider()).lookup(verified_address)`:
   - `provider.get_building_from_address(verified_address)` → raw provider payload
   - `normalizer.normalize_norkart_building(raw)` (name kept generic in code:
     `normalize_building`) → normalized `building` / `floors` / `units` / `buildings`
   - multiple buildings: prefer the one whose matrikkel matches the verified address;
     if still ambiguous, return `buildings: [{id, label, type}]` and leave `building: null`.
5. Persist `PropertyLookup` row (token = `uuid4().hex`).
6. Return `200 {"success": true, "token": ..., "address": {...}, "property": {...},
   "building": {...}|null, "buildings": [...], "floors": [...], "units": [...]}`.

**Error mapping** — HTTP 200 with `success:false` for all semantic failures, so the
frontend fallback flow is never an HTTP error. Exceptions: `400` (bad request body /
bad signature), `429` (rate limit), `500` (unexpected — generic `SERVER_ERROR`, no
traceback to client).

Internal codes: `INVALID_ADDRESS, ADDRESS_NOT_FOUND, BUILDING_NOT_FOUND,
MULTIPLE_BUILDINGS, PROVIDER_UNAVAILABLE, PROVIDER_TIMEOUT, RATE_LIMITED,
INVALID_PROVIDER_RESPONSE, SERVER_ERROR`.

---

## 4. Normalized structure

Exactly the shape in the feature brief:

```json
{
  "success": true,
  "address": {
    "formatted": "Storgata 10, 2609 Lillehammer",
    "street": "Storgata", "house_number": "10", "house_letter": null,
    "postal_code": "2609", "postal_city": "Lillehammer",
    "municipality": "Lillehammer", "municipality_number": "3405",
    "county": null, "latitude": 61.12, "longitude": 10.46
  },
  "property": { "gnr": null, "bnr": null, "fnr": null, "snr": null },
  "building": {
    "building_number": null, "building_type": null, "building_status": null,
    "construction_year": null, "bra_m2": null, "gross_area_m2": null,
    "number_of_floors": null, "has_elevator": null,
    "residential_unit_count": null
  },
  "buildings": [],
  "floors": [],
  "units": [
    { "unit_id": "...", "unit_number": "H0201", "floor": "2", "bra_m2": 72, "type": "Bolig" }
  ]
}
```

**Never invent data.** Any value the provider does not return is `null`. No derivation of
BRA, construction year, floor count, or unit area unless a documented calculation is
explicitly implemented (none are).

`unit_codes.parse_bruksenhet_code` — documented per Matrikkelforskriften: bruksenhetsnummer
is `<letter><FF><NN>` where letter ∈ {H hoveddel over bakken, L loft, U underetasje,
K kjeller}, `FF` = floor within that level (01–99), `NN` = running number on the floor.
Used **only as a fallback** when the provider gives no explicit floor for a unit.

---

## 5. Data model

`apps/leads/models.py` — one migration.

```python
class PropertyLookup(models.Model):
    token                = CharField(max_length=32, unique=True, editable=False)
    provider             = CharField(max_length=20)
    verified_address     = JSONField()                       # Kartverket-verified origin address
    normalized           = JSONField()                       # {address, property, building, buildings, floors, units}
    selected_unit_number = CharField(max_length=20, blank=True, default="")
    data_source          = CharField(max_length=10, default="api")   # "api" | "user"
    manual_overrides     = JSONField(default=dict, blank=True)
    created_at           = DateTimeField(auto_now_add=True)
```

`MoveLead` gains (all nullable / blank — a lead with no property data is still valid):

```
property_lookup  FK(PropertyLookup, null, SET_NULL, related_name="leads")
bolig_adresse    CharField                 # verified formatted origin address
bolig_type       CharField
bolig_bra_m2     PositiveIntegerField(null)
bolig_byggeaar   PositiveIntegerField(null)
bolig_etasjer    PositiveIntegerField(null)
bolig_enhet      CharField                 # e.g. "H0201"
bolig_datakilde  CharField                 # "api" | "user" | ""
bolig_gnr        CharField
bolig_bnr        CharField
```

---

## 6. WizardForm + view

- New step 2 has **no gate** — `isStepValid(2)` is always `true`; the user can always continue.
- `WizardForm` adds optional fields: `property_token`, `selected_unit`,
  `bolig_type_manuell`, `bolig_bra_manuell` (IntegerField), `bolig_etasjer_manuell`
  (IntegerField), `bolig_enhet_manuell`.
- `wizard` view, after `form.is_valid()`:
  1. Pop the property/manual keys out of `cleaned_data`.
  2. `lead = MoveLead.objects.create(**cleaned_data)` (unchanged for the real MoveLead fields).
  3. Resolve property data:
     - `property_token` present → `PropertyLookup.objects.filter(token=...).first()`;
       validate `selected_unit` is one of the stored `normalized["units"][*]["unit_number"]`
       (ignore if not); set `lead.property_lookup`, copy denormalized `bolig_*` from the
       effective (unit-level if a unit is selected, else building-level) values;
       `bolig_datakilde = lookup.data_source`.
     - else manual fields non-empty → copy them, `bolig_datakilde = "user"`.
     - else → leave blank.
  4. `lead.save(update_fields=[...])`.
- Manual override: if a `property_token` is present **and** any manual field is non-empty,
  the manual value wins for that field and `bolig_datakilde = "user"`; also persisted to
  `PropertyLookup.manual_overrides` + `data_source="user"` for auditability.

---

## 7. Frontend

### Step renumber

`wizard.html` / `wizard.js`: insert step 2, shift old 2–5 → 3–6.
Touch points: `data-total-steps="6"`; 6 × `.wizard-progress__segment`; "Steg X av 6";
`data-step` on `<section>`s; `data-step-panel` on right-column panels;
`KOBLY_MOBILE_BACKGROUNDS` keys 1–6 (new step 2 reuses an existing wizard image);
`wizard.js` `TOTAL_STEPS = 6`, `isStepValid` switch (`case 2: return true;` + renumber),
`FIELD_TO_STEP` map.

### `static/js/property-lookup.js`

Self-contained; loaded after `wizard.js` on `wizard.html`. Owns step 2 only.

- **Accessible combobox** against our own `/api/adresse-sok/` proxy:
  `role="combobox"`, `aria-expanded`, `aria-controls`, `aria-activedescendant`;
  `role="listbox"` / `role="option"`; ArrowUp/Down/Enter/Escape/Tab;
  300 ms debounce; `AbortController` + monotonic sequence guard against stale responses;
  min 3 chars; ≤ 8 results; empty state "Ingen adresser funnet"; loading state.
- `selectedAddress` state object. **Editing the input after a selection invalidates it**
  (result cleared, hidden `property_token` cleared) until another result is chosen.
- On select → **one** locked `POST /api/eiendom/` — controls disabled while in flight,
  `AbortController` supersede, `lookupInFlight` guard so repeated clicks send one request.
- Render states:
  - **loading** — skeleton card, "Henter informasjon om eiendommen din…"
  - **house** (`units.length <= 1`) — 4 stat cards (BRA / etasjer / byggeår / boligtype),
    each showing "Ikke tilgjengelig" when `null`; `Se mer informasjon` expander
    (bygningsnummer, gnr, bnr, kommune, kommunenummer).
  - **apartment** (`units.length > 1`) — "Vi fant flere boenheter…", list of `Hxxxx`
    buttons (`2. etasje · 72 m²` only when that data exists). Pick → hidden
    `selected_unit`, re-render showing unit-level values where present, building-level
    otherwise.
  - **multiple buildings** (`buildings.length > 1`) — "Vi fant flere bygg…" picker
    (Hovedhus / Garasje / Anneks by label).
  - **fallback** (`BUILDING_NOT_FOUND` / `PROVIDER_*`) — "Adressen ble funnet, men vi
    kunne ikke hente fullstendig informasjon…", reveals the manual fields; Neste stays enabled.
  - **error** (`INVALID_ADDRESS` / network) — compact message + "Prøv igjen".
  - **address not found** — "Vi fant ikke adressen. Kontroller gatenavn og husnummer…",
    input stays available.
- **"Endre adresse"** — clears `selectedAddress`, result, selected unit, errors, hidden
  fields; no reload.
- **Prefill** — on entering step 2 (`KoblyWizard.onStepChange`), if step 1's `fra` is a
  full address (`"street nr, 1234 Poststed"` and coords set), auto-search it and
  auto-select an exact top match; else show the empty combobox.
- Writes hidden `property_token` + `selected_unit`; contributes a "Din bolig" row to
  step 6's receipt panel.
- Secondary line: *"Eiendomsinformasjon hentet fra offentlige registre. Opplysningene
  kan avvike fra dagens faktiske forhold."*

### SCSS (`wizard.scss` new section)

`.property-step`, `.property-combobox`, `.property-suggestions`, `.property-card`,
`.property-stats` / `.property-stat`, `.property-units` / `.property-unit`,
`.property-buildings`, `.property-details`, `.property-manual`, `.property-loading`
(reuse existing skeleton/spinner idiom), `.property-error`, `.property-source-note`.
150–250 ms transitions. Responsive at the existing `@media (max-width: 1049px)` /
`(min-width: 1050px)` breakpoints; step-2 result flows inline under the fields on mobile
(same pattern as step-1 map / step-6 receipt); ≥ 44 px touch targets; text wraps;
no horizontal overflow at 320 px.

Icons: add any missing symbols to `apps/leads/templates/leads/_icon_sprite.html`
(`building`, `check-circle`, `chevron-down`).

---

## 8. Settings / environment

Inside the existing `if DEBUG == True:` block in `demo/settings.py`, near `CARTO_API_KEY`:

```python
PROPERTY_PROVIDER              = os.environ.get("PROPERTY_PROVIDER", "mock")   # "mock" | "norkart"
NORKART_API_URL               = os.environ.get("NORKART_API_URL", "")
NORKART_API_KEY               = os.environ.get("NORKART_API_KEY", "")
NORKART_API_SECRET            = os.environ.get("NORKART_API_SECRET", "")
NORKART_API_TIMEOUT           = int(os.environ.get("NORKART_API_TIMEOUT", "8"))
PROPERTY_LOOKUP_CACHE_SECONDS = int(os.environ.get("PROPERTY_LOOKUP_CACHE_SECONDS", "21600"))
```

`providers.get_provider()`:
- `"mock"` → `MockBuildingProvider`; logs a `warning` every time it is used (this settings
  file has no production branch, so mock must be loud rather than silent).
- `"norkart"` → `NorkartBuildingProvider`; raises `PropertyProviderMisconfigured`
  (logged) if `NORKART_API_URL` or `NORKART_API_KEY` is empty.
- unknown value → `PropertyProviderMisconfigured`.

No new pip packages — `requests` is already a dependency.

**Credentials never reach the browser** — all Norkart calls are server-side; keys live only
in env vars; nothing Norkart-related is exposed in any template or JS.

**What the operator must supply for real Norkart:** `NORKART_API_URL`, `NORKART_API_KEY`,
`NORKART_API_SECRET` (if their auth uses one), and the Norkart **Bygning API response
documentation / a sample payload** so `normalize_building` TODO mappings and the
`norkart.py` auth header can be completed. Until then keep `PROPERTY_PROVIDER=mock`.

---

## 9. Security / privacy

- Server-side validation of every input; frontend values never trusted (signed address
  token + server re-verification + `PropertyLookup` reload at submit).
- Input length caps (`q` ≤ 150; manual fields bounded).
- Per-IP rate limiting on both endpoints via the existing cache.
- `requests` timeouts on every external call (`8 s` default); all HTTP status codes and
  malformed JSON handled; an external failure never 500s the Django request.
- No verbose error traces to the client; technical detail logged server-side only.
- Logs never include auth headers, keys, or secrets. Minimal personal data logged.
- **No owner / occupant data** is requested, stored, or displayed even if a provider
  returns it — the normalizer only ever reads address / property / building / unit fields.
- Raw provider responses are **not** persisted — only the normalized structure.

---

## 10. Testing (`apps/leads/`, run on system Python 3.12)

- `unit_codes`: `H0201`→floor 2; `U0101`, `K0101`, `L0301`; malformed → `None`.
- `normalizer`: house payload → normalized; apartment payload → units; missing fields →
  `null` (asserted, never invented); malformed → `InvalidProviderResponse`.
- `providers.get_provider`: mock returns Mock; norkart without creds raises.
- `MockBuildingProvider`: house / apartment / not-found / missing-data fixtures.
- `address_search`: normal; `< 3` chars → empty; `æ ø å`; zero results; `429` when
  rate-limited; second identical call served from cache (network mock asserted called once);
  Geonorge error → `{"results": []}`.
- `property_lookup`: house → result + `PropertyLookup` row; apartment → `units`;
  bad signature → `400 INVALID_ADDRESS`; address gone → `ADDRESS_NOT_FOUND`;
  provider timeout → `PROVIDER_TIMEOUT`; provider 401 → `PROVIDER_UNAVAILABLE`;
  provider 500 → `PROVIDER_UNAVAILABLE`; malformed provider JSON →
  `INVALID_PROVIDER_RESPONSE`; missing CSRF → 403; duplicate POST → still one coherent row.
- `WizardForm`: valid `property_token` resolves; manual-only resolves with
  `data_source="user"`; neither → form still valid.
- `wizard` POST: `MoveLead` created with `property_lookup` FK + denormalized `bolig_*`;
  `selected_unit` not in stored units → ignored; existing step-count assertions updated.
- Full existing `apps.leads` + wizard suites stay green.

---

## 11. Implementation order

1. `property/exceptions.py`, `property/client.py`, `property/unit_codes.py` (+ tests)
2. `property/normalizer.py` (+ tests)
3. `property/providers/` — base, mock, norkart skeleton, factory (+ tests)
4. `property/kartverket.py`, `property/service.py` (+ tests)
5. `demo/settings.py` additions
6. `PropertyLookup` model + `MoveLead` fields + migration
7. `apps/leads/api_views.py` + urls (+ endpoint tests)
8. `WizardForm` + `wizard` view changes (+ tests)
9. `wizard.html` step renumber + new step 2 markup + hidden fields + icon sprite
10. `wizard.js` renumber (`TOTAL_STEPS`, `isStepValid`, `FIELD_TO_STEP`, backgrounds)
11. `static/js/property-lookup.js`
12. `wizard.scss` section + compile
13. Full `apps.leads` test run + manual flow check (mock provider)
```
