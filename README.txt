KOBLY REBUILD — COMPANION FILES
================================

This folder is meant to travel alongside kobly-full-site-spec.pdf. The PDF explains
WHAT everything is and HOW it behaves; these are the actual source files and assets
it references, so you have real content to copy from instead of retyping from the
PDF's summaries/tables.

WHAT'S HERE

public/images/
    Every photo, illustration PNG, and agency logo referenced anywhere in the PDF
    (backgrounds, step art, testimonial photos, agency logos, blog images, etc.).
    File names match exactly what the PDF cites, e.g. "boxes-and-plants.jpg",
    "R1-09476-0023-kopi.jpg", "loeftlogo.svg".

app/fonts/
    Moderat-Regular.otf and Moderat-Semibold.otf — the local/proprietary font used
    as the site's default sans-serif (PDF section 3.2). Crimson Pro and Syne are
    NOT here because they're free Google Fonts, easy to re-source directly.

lib/*.ts
    The actual TypeScript data — NOT summaries. This is the full, verbatim content
    the PDF's data-catalog tables (section 13) only excerpted:
      cities.ts       - the 5 city records with lat/lon/zoom (PDF 13.1)
      districts.ts    - all 14 Oslo district write-ups, full paragraphs (PDF 13.2)
      agencies.ts     - all 4 agencies, full "about us" copy + all 16 reviews (PDF 13.3)
      blog.ts         - all 3 full blog articles, block by block (PDF 13.4)
      utils.ts        - small date-formatting helper referenced by several pages
      emails/*.ts     - the 4 finished transactional email templates (PDF section 12),
                        plus their shared layout/component builders and dummy data.
                        These are plain functions returning HTML strings — no React —
                        so they port to Django/Python close to line-for-line.

app/wizard/, components/wizard/
    The actual source of the priority-one lead form (PDF section 5): page.tsx (the
    whole 5-step wizard), MapPickerOverlay.tsx (mobile map picker), plus two UNUSED
    leftover files (Illustration.tsx, RadioCard.tsx) that the PDF's section 15
    explicitly flags as orphaned — don't treat their presence here as "this is used,
    port it too."

components/marketing/, components/ui/
    Every reusable piece the PDF's sections 4 and 6-11 describe (Header, Footer,
    MobileMenu, HeroCard, PostnummerInput, FAQ, Stats, the partner/* and agency/*
    subfolders, etc.) plus the base shadcn Button primitive.

WHAT'S DELIBERATELY NOT HERE

- The marketing PAGE files (app/(marketing)/**/page.tsx) themselves aren't included —
  the PDF's per-page sections (6-11) already describe their structure and content
  in full, and they're thin wrappers that just assemble the components above in
  order. If you want them anyway, ask for them explicitly.
- No node_modules, no build config, no Next.js routing/framework files — this is a
  content + design + component reference, not a runnable app. It's meant to be read
  and translated into Django/HTML/SCSS/vanilla JS, not deployed as-is.

READ THE PDF FIRST. It tells you which of these files matters for which part of the
build, in priority order (wizard form first, then the marketing shell, then the rest).
