import {
  COLORS,
  SANS,
  button,
  card,
  detailRow,
  emailShell,
  heading,
  paragraph,
  row,
} from "./layout";

import { LEAD } from "./dummy";

/** E-post til flyttebyrå når en ny forespørsel er matchet til dem. */
export const newLeadSubject =
  "Ny flytteforespørsel i Oslo – svar innen 24 timer";

export function newLeadEmail(baseUrl: string): string {
  const leadCard = card(
    [
      detailRow("Flytter fra", LEAD.fraKort),
      detailRow("Flytter til", LEAD.tilKort),
      detailRow("Ønsket dato", LEAD.dato),
      detailRow("Boligtype", LEAD.bolig),
      detailRow("Etasje og heis", LEAD.etasje),
      detailRow("Tilleggstjenester", "Flyttevask, pianotransport", true),
    ].join("\n"),
    `Forespørsel ${LEAD.ref}`,
  );

  const comment = `<table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color:${COLORS.bg}; border-radius:14px;">
                <tr>
                  <td class="kobly-card" style="padding:20px 24px;">
                    <p style="margin:0 0 6px; font-family:${SANS}; font-size:13px; font-weight:600; color:${COLORS.inkMuted};">Kommentar fra kunden</p>
                    <p style="margin:0; font-family:${SANS}; font-size:15px; line-height:1.65; color:${COLORS.ink};">«${LEAD.kommentar}»</p>
                  </td>
                </tr>
              </table>`;

  const reminder = `<table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="border-top:1px solid ${COLORS.line}; padding-top:22px;">
                    <p style="margin:0; font-family:${SANS}; font-size:14px; line-height:1.65; color:${COLORS.inkMuted};">
                      Kunden har fått denne forespørselen ut til <strong style="color:${COLORS.ink};">inntil tre byråer</strong>. Byråene som svarer først, blir som regel også de som får jobben. De fleste kunder velger innen et døgn.
                    </p>
                  </td>
                </tr>
              </table>`;

  const content = [
    row(heading("Du har fått en ny flytteforespørsel"), 36),
    row(
      paragraph(
        "En kunde i Oslo skal flytte i september og passer godt med profilen deres. Her er hovedpunktene:",
        true,
      ),
      16,
    ),
    row(leadCard, 24),
    row(comment, 16),
    row(
      `<div class="kobly-btn">${button("Se forespørsel og gi tilbud", `${baseUrl || "https://kobly.no"}/wizard`)}</div>`,
      28,
    ),
    row(
      paragraph(
        "Fullstendig adresse og kontaktinfo blir tilgjengelig når du åpner forespørselen.",
        true,
      ),
      16,
    ),
    row(reminder, 28),
  ].join("\n");

  return emailShell({
    preheader:
      "3-roms på Grünerløkka skal til Nordstrand 12. september. Flyttevask og pianotransport er ønsket.",
    content,
    baseUrl,
    footerNote:
      "Du får denne e-posten fordi byrået ditt er partner hos Kobly og dekker dette området.",
  });
}
