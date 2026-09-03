# /for-bedrifter/ page build report

Date: 2026-08-22

## What was built

Filled in the previously-blank `apps/core/templates/pages/about/for-business.html` template
(rendered by the existing `for_business` view, no view changes needed) with the full Norwegian
marketing copy for the "For flyttebyråer" partner page, in six sections:

1. **Hero** — eyebrow, H1, subline, two CTAs (`#bli-partner` primary, `#hvordan` outline).
2. **Stats** — 4 cards, reusing the home page's `.stats`/`.stat` pattern verbatim (no new SCSS).
3. **Value props** — heading + 2×2 (desktop) / 1-col (mobile) icon-card grid. New SCSS:
   `.value-props`/`.value-props__title`/`.value-props__grid` and `.value-card` (icon circle,
   title, body) in both `base.scss` media blocks.
4. **How it works** (`id="hvordan"`) — reuses home's `.how-it-works`/`.step-card` markup and CSS
   exactly (3 numbered cards), just without the `.step-card__art` illustration image, since none
   was supplied for this content.
5. **FAQ** — reuses home's `.faq`/`.faq-item` accordion markup byte-for-byte in shape
   (`data-faq`, `data-faq-item`, `data-faq-trigger`, `aria-expanded`), so `site.js`'s existing
   `initFaqAccordions()` wires it up with no JS changes.
6. **Final CTA** (`id="bli-partner"`) — new `.partner-cta`/`.partner-cta__card` dark brand-colored
   card (modeled on `.site-footer__card`'s visual treatment), with an H2, body copy, and a
   "Send søknad" button.

### Deliberate deviation from the reference (as instructed)

The reference Next.js site links the final CTA button to a bare
`mailto:` address for the partner team. This Django port already has a real signup form + backend
at `/for-bedrifter/bli-partner/` (`for_business_partner` in `apps/core/views.py`, which creates a
`Bedrift_info` row on POST), so the button links there instead. This is called out in a one-line
HTML comment directly above the `<a>` tag in the template — worded to describe the deviation
without literally spelling out the mailto address, since the new test asserts that string is
*absent* from the rendered page (an HTML comment counts as "on the page" for `assertNotContains`,
so the comment text itself had to avoid the literal substring).

### New icons

Added `icon-filter`, `icon-wallet`, `icon-check-circle`, `icon-sparkles` to
`apps/core/templates/core/_icon_sprite.html`, matching the sprite's existing style (24×24,
`stroke="currentColor"`, `stroke-width="2"`, simple line icons approximating the equivalent
Lucide icons).

### SCSS

All new rules were added to **both** the mobile (`max-width: 1049px`) and desktop
(`min-width: 1050px`) blocks in `static/scss/base.scss`, using only existing design tokens
(`$brand`, `$brandInk`, `$surfaceSoft`, `$line`, `$ink`, `$inkMuted`, `$accentLime`, `$radiusCard`,
`$radiusPill`, `$fontSerif`) — no hardcoded colors were introduced. New selectors:
`.for-bedrifter-hero__title`, `.for-bedrifter-hero__subline`, `.for-bedrifter-hero__ctas`
(added alongside the existing "blog & agencies simple hero" comment block, renamed to include
for-bedrifter), `.value-props`/`.value-props__title`/`.value-props__grid`, `.value-card` (+ its
`__icon`/`__title`/`__body` children), `.partner-cta`/`.partner-cta__card` (+ `__title`/`__body`/
`__button`). Compiled via `sass static/scss/base.scss static/scss/base.css --style=expanded
--no-source-map` with no errors.

## Tests added

`apps/core/tests.py` — new `ForBusinessPageTests` class:
- `test_page_200_with_h1` — page returns 200 and contains the exact H1 text.
- `test_page_contains_a_faq_question` — contains at least one FAQ question.
- `test_cta_links_to_real_signup_form_not_a_mailto` — asserts `href="/for-bedrifter/bli-partner/"`
  is present **and** the literal string `mailto:partner@kobly.no` is absent anywhere on the page
  (this is the detail most likely to get silently reverted back to the reference's mailto:
  placeholder, so both sides are asserted explicitly).

## Verification performed

1. `manage.py test apps.core -v 2` → **24 tests, all green** (21 pre-existing + 3 new).
2. `manage.py test apps.pages apps.dashboard apps.leads apps.store apps.userprofile -v 0` →
   **112 tests, all green, unchanged** — confirms nothing else broke.
3. Started `manage.py runserver` on `127.0.0.1:8765` and curled:
   - `GET /for-bedrifter/` → `200`, contains the H1 text, contains `<div class="faq" data-faq>`
     with 5× `data-faq-item` and 5× `data-faq-trigger` (matching home.html's FAQ markup shape
     exactly, so `initFaqAccordions()` picks it up with no new JS), contains
     `href="/for-bedrifter/bli-partner/"`, and does **not** contain `mailto:partner@kobly.no`.
   - `GET /` → `200`, nav still contains
     `<a href="/for-bedrifter/" class="site-header__link">For flyttebyråer</a>` — confirmed
     already correctly pointing here (not re-touched).
4. Dev server process stopped after verification.

## Files touched (and committed)

- `apps/core/templates/pages/about/for-business.html` (new content)
- `apps/core/templates/core/_icon_sprite.html` (4 new icon symbols)
- `apps/core/tests.py` (new `ForBusinessPageTests` class, appended)
- `static/scss/base.scss` (new rules in both media blocks)
- `static/scss/base.css` (recompiled output)

Per instructions, `static/scss/base.css.map` and all other pre-existing uncommitted/untracked
changes in the working tree were left untouched and not committed.
