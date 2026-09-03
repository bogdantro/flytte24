/**
 * Delt layout for alle Kobly-e-poster.
 *
 * E-postklient-trygt: tabellbasert, inline CSS, maks 600 px, systemfonter,
 * ingen ekstern CSS og ingen JS. Alle templates i lib/emails/ bygger på denne.
 *
 * `baseUrl` gjør bilder absolutte i den ferdige templaten. I nettleser-
 * forhåndsvisningen sendes tom streng, slik at bildene lastes fra samme origin.
 */

export const COLORS = {
  bg: "#f4f1ea",
  surface: "#ffffff",
  surfaceSoft: "#faf9f6",
  ink: "#1a1a1a",
  inkMuted: "#5c5c5c",
  line: "#e6e1d6",
  brand: "#221814",
  brandInk: "#faf9f6",
  lime: "#d6e8a8",
} as const;

export const SANS =
  "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
export const SERIF = "Georgia, 'Times New Roman', Times, serif";

export type EmailShellOptions = {
  /** Vises som forhåndsvisningstekst i innboksen, rett etter emnefeltet. */
  preheader: string;
  /** Ferdig HTML for innholdsområdet (typisk flere <tr>-rader). */
  content: string;
  baseUrl: string;
  /** Footer-linje som forklarer hvorfor mottakeren fikk e-posten. */
  footerNote: string;
};

/** Primærknapp. Tabellbasert så den også holder i Outlook. */
export function button(label: string, href: string): string {
  return `<table role="presentation" border="0" cellpadding="0" cellspacing="0" style="border-collapse:separate;">
                <tr>
                  <td align="center" bgcolor="${COLORS.brand}" style="border-radius:999px;">
                    <a href="${href}" style="display:inline-block; padding:16px 32px; font-family:${SANS}; font-size:16px; font-weight:600; line-height:1; color:${COLORS.brandInk}; text-decoration:none; border-radius:999px;">${label}</a>
                  </td>
                </tr>
              </table>`;
}

/** Én rad med etikett og verdi inne i et informasjonskort. */
export function detailRow(
  label: string,
  value: string,
  isLast = false,
): string {
  const border = isLast ? "" : `border-bottom:1px solid ${COLORS.line};`;
  return `<tr>
                      <td style="padding:14px 0; ${border}">
                        <p style="margin:0; font-family:${SANS}; font-size:13px; line-height:1.4; color:${COLORS.inkMuted};">${label}</p>
                        <p style="margin:4px 0 0; font-family:${SANS}; font-size:16px; line-height:1.5; font-weight:600; color:${COLORS.ink};">${value}</p>
                      </td>
                    </tr>`;
}

/** Kort med lys bakgrunn og ramme — brukes til lead-info, tilbud og kvittering. */
export function card(inner: string, title?: string): string {
  const heading = title
    ? `<p style="margin:0 0 4px; font-family:${SANS}; font-size:13px; font-weight:600; letter-spacing:0.02em; color:${COLORS.inkMuted};">${title}</p>`
    : "";
  return `<table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color:${COLORS.surfaceSoft}; border:1px solid ${COLORS.line}; border-radius:14px;">
                <tr>
                  <td style="padding:22px 24px;">
                    ${heading}
                    <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">
                      ${inner}
                    </table>
                  </td>
                </tr>
              </table>`;
}

/** Innholdsrad med standard sidemarg. */
export function row(inner: string, paddingTop = 0): string {
  return `<tr>
            <td class="kobly-pad" style="padding:${paddingTop}px 32px 0;">
              ${inner}
            </td>
          </tr>`;
}

/** Nummerert liste som forklarer hva som skjer videre. */
export function stepsList(steps: string[]): string {
  const items = steps
    .map(
      (step, i) => `<tr>
                      <td width="34" valign="top" style="padding:0 0 ${i === steps.length - 1 ? 0 : 16}px;">
                        <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                          <tr>
                            <td width="26" height="26" align="center" valign="middle" bgcolor="${COLORS.lime}" style="width:26px; height:26px; border-radius:13px; font-family:${SANS}; font-size:13px; font-weight:600; color:${COLORS.ink};">${i + 1}</td>
                          </tr>
                        </table>
                      </td>
                      <td valign="top" style="padding:0 0 ${i === steps.length - 1 ? 0 : 16}px;">
                        <p style="margin:2px 0 0; font-family:${SANS}; font-size:15px; line-height:1.6; color:${COLORS.ink};">${step}</p>
                      </td>
                    </tr>`,
    )
    .join("\n");
  return `<table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">${items}</table>`;
}

/** Byråkort med logo, navn, rating og antall jobber. */
export function agencyCard({
  name,
  logo,
  rating,
  reviewCount,
  jobs,
  baseUrl,
}: {
  name: string;
  logo: string;
  rating: string;
  reviewCount: number;
  jobs: number;
  baseUrl: string;
}): string {
  return `<table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color:${COLORS.surfaceSoft}; border:1px solid ${COLORS.line}; border-radius:14px;">
                <tr>
                  <td class="kobly-card" style="padding:22px 24px;">
                    <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">
                      <tr>
                        <td valign="middle" style="padding-bottom:14px;">
                          <img src="${baseUrl}${logo}" height="30" alt="${name}" style="display:block; height:30px; width:auto; max-width:150px;" />
                        </td>
                      </tr>
                      <tr>
                        <td>
                          <p style="margin:0; font-family:${SANS}; font-size:18px; font-weight:600; line-height:1.3; color:${COLORS.ink};">${name}</p>
                          <p style="margin:6px 0 0; font-family:${SANS}; font-size:14px; line-height:1.5; color:${COLORS.inkMuted};">
                            <span style="color:${COLORS.ink}; font-weight:600;">${rating} ★</span> av ${reviewCount} kunder · ${jobs} jobber utført
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>`;
}

export function heading(text: string): string {
  return `<h1 style="margin:0; font-family:${SERIF}; font-size:28px; line-height:1.2; font-weight:normal; color:${COLORS.ink};">${text}</h1>`;
}

export function paragraph(text: string, muted = false): string {
  return `<p style="margin:0; font-family:${SANS}; font-size:16px; line-height:1.65; color:${muted ? COLORS.inkMuted : COLORS.ink};">${text}</p>`;
}

export function emailShell({
  preheader,
  content,
  baseUrl,
  footerNote,
}: EmailShellOptions): string {
  const logo = `${baseUrl}/images/kobly-logo-email.png`;

  return `<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="nb">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="x-apple-disable-message-reformatting" />
<title>Kobly</title>
<!--[if mso]>
<style type="text/css">body, table, td, a { font-family: Arial, Helvetica, sans-serif !important; }</style>
<![endif]-->
<style type="text/css">
  body { margin:0; padding:0; width:100% !important; }
  img { border:0; outline:none; text-decoration:none; -ms-interpolation-mode:bicubic; }
  a { color:${COLORS.ink}; }
  @media only screen and (max-width: 480px) {
    .kobly-pad { padding-left:20px !important; padding-right:20px !important; }
    .kobly-card { padding-left:18px !important; padding-right:18px !important; }
    .kobly-h1 { font-size:24px !important; }
    .kobly-btn a { display:block !important; text-align:center !important; }
  }
</style>
</head>
<body style="margin:0; padding:0; background-color:${COLORS.bg};">
  <div style="display:none; max-height:0; overflow:hidden; opacity:0; mso-hide:all;">${preheader}</div>
  <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color:${COLORS.bg};">
    <tr>
      <td align="center" style="padding:24px 12px 40px;">
        <table role="presentation" width="600" border="0" cellpadding="0" cellspacing="0" style="width:100%; max-width:600px;">

          <!-- Logo, sentrert over innholdsboksen -->
          <tr>
            <td class="kobly-pad" align="center" style="padding:16px 32px 24px; text-align:center;">
              <a href="${baseUrl || "https://kobly.no"}/" style="text-decoration:none;">
                <img src="${logo}" width="121" height="36" alt="Kobly" style="display:block; width:121px; height:36px; margin:0 auto;" />
              </a>
            </td>
          </tr>

          <!-- Innhold -->
          <tr>
            <td style="background-color:${COLORS.surface}; border:1px solid ${COLORS.line}; border-radius:14px;">
              <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">
                ${content}
                <tr><td style="height:36px; line-height:36px; font-size:0;">&nbsp;</td></tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td class="kobly-pad" style="padding:28px 32px 0;">
              <p style="margin:0; font-family:${SANS}; font-size:13px; line-height:1.6; color:${COLORS.inkMuted};">
                ${footerNote}
              </p>
              <p style="margin:14px 0 0; font-family:${SANS}; font-size:13px; line-height:1.6; color:${COLORS.inkMuted};">
                Kobly AS · Torggata 15, 0181 Oslo<br />
                <a href="mailto:hei@kobly.no" style="color:${COLORS.inkMuted}; text-decoration:underline;">hei@kobly.no</a> · 21 09 88 00
              </p>
              <p style="margin:14px 0 0; font-family:${SANS}; font-size:13px; line-height:1.6; color:${COLORS.inkMuted};">
                <a href="#avmelding" style="color:${COLORS.inkMuted}; text-decoration:underline;">Meld av varsler</a>
                &nbsp;·&nbsp;
                <a href="#personvern" style="color:${COLORS.inkMuted}; text-decoration:underline;">Personvern</a>
                &nbsp;·&nbsp;
                <a href="${baseUrl || "https://kobly.no"}/" style="color:${COLORS.inkMuted}; text-decoration:underline;">kobly.no</a>
              </p>
              <p style="margin:18px 0 0; font-family:${SANS}; font-size:12px; line-height:1.6; color:#8a8a8a;">
                © 2026 Kobly AS
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>`;
}
