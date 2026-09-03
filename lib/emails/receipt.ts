import {
  COLORS,
  SANS,
  card,
  detailRow,
  emailShell,
  heading,
  paragraph,
  row,
  stepsList,
} from "./layout";
import { LEAD } from "./dummy";

/** E-post A: kvittering til kunden rett etter innsendt forespørsel. */
export const receiptSubject = "Vi har mottatt flytteforespørselen din";

export function receiptEmail(baseUrl: string): string {
  const summary = card(
    [
      detailRow("Flytter fra", LEAD.fraKort),
      detailRow("Flytter til", LEAD.tilKort),
      detailRow("Ønsket dato", LEAD.dato),
      detailRow("Boligtype", LEAD.bolig),
      detailRow("Tjenester du har valgt", LEAD.tjenester, true),
    ].join("\n"),
    `Forespørsel ${LEAD.ref}`,
  );

  const steps = stepsList([
    "Vi matcher deg med 3 kvalitetssjekkede byråer som passer flyttingen din.",
    "Byråene kontakter deg med tilbud innen 24 timer.",
    "Du sammenligner og velger. Helt uforpliktende.",
  ]);

  const closing = `<table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="border-top:1px solid ${COLORS.line}; padding-top:22px;">
                    <p style="margin:0; font-family:${SANS}; font-size:14px; line-height:1.65; color:${COLORS.inkMuted};">
                      Du trenger ikke gjøre noe nå. Vil du endre noe i forespørselen, er det bare å svare på denne e-posten, så ordner vi det.
                    </p>
                  </td>
                </tr>
              </table>`;

  const content = [
    row(heading("Takk, vi har mottatt forespørselen din"), 36),
    row(
      paragraph(
        `Hei ${LEAD.kunde}! Forespørselen din er registrert, og vi er allerede i gang med å finne byråer som passer. Her er det du sendte inn:`,
        true,
      ),
      16,
    ),
    row(summary, 24),
    row(
      `<p style="margin:0; font-family:${SANS}; font-size:16px; font-weight:600; line-height:1.5; color:${COLORS.ink};">Slik går vi frem</p>`,
      32,
    ),
    row(steps, 18),
    row(closing, 28),
  ].join("\n");

  return emailShell({
    preheader:
      "Vi matcher deg med tre kvalitetssjekkede byråer. Du hører fra dem innen 24 timer.",
    content,
    baseUrl,
    footerNote:
      "Du får denne e-posten fordi du sendte inn en flytteforespørsel på kobly.no.",
  });
}
