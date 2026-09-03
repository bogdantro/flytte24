import {
  COLORS,
  SANS,
  card,
  detailRow,
  emailShell,
  heading,
  paragraph,
  row,
} from "./layout";
import { LEAD, OFFER, OFFER_AGENCY } from "./dummy";

/** E-post C: kunden har valgt byrå, og flyttingen er bekreftet. */
export const bookingConfirmedSubject = `Flyttingen din er bekreftet med ${OFFER_AGENCY.name}`;

export function bookingConfirmedEmail(baseUrl: string): string {
  const confirmation = card(
    [
      detailRow("Flyttebyrå", `${OFFER_AGENCY.name} · ${OFFER.pris} fastpris`),
      detailRow("Dato", LEAD.dato),
      detailRow("Fra", LEAD.fraFull),
      detailRow("Til", LEAD.tilFull),
      detailRow(
        "Kontaktperson",
        `${OFFER_AGENCY.contact.name}, ${OFFER_AGENCY.contact.role} · ${OFFER_AGENCY.contact.phone}`,
        true,
      ),
    ].join("\n"),
    `Bekreftelse ${LEAD.ref}`,
  );

  const next = `<table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color:${COLORS.bg}; border-radius:14px;">
                <tr>
                  <td class="kobly-card" style="padding:22px 24px;">
                    <p style="margin:0 0 6px; font-family:${SANS}; font-size:15px; font-weight:600; line-height:1.5; color:${COLORS.ink};">Hva skjer nå?</p>
                    <p style="margin:0; font-family:${SANS}; font-size:15px; line-height:1.65; color:${COLORS.ink};">
                      ${OFFER_AGENCY.contact.name} hos ${OFFER_AGENCY.name} tar kontakt i god tid før flyttedagen for å avklare detaljene: oppmøtetidspunkt, parkering, heis og hva som skal pakkes. Har du spørsmål før det, kan du ringe direkte på ${OFFER_AGENCY.contact.phone}.
                    </p>
                  </td>
                </tr>
              </table>`;

  const extra = `<table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="border-top:1px solid ${COLORS.line}; padding-top:22px;">
                    <p style="margin:0; font-family:${SANS}; font-size:14px; line-height:1.65; color:${COLORS.inkMuted};">
                      Trenger du flyttevask også?
                      <a href="${baseUrl || "https://kobly.no"}/wizard" style="color:${COLORS.ink}; text-decoration:underline;">Få tilbud her</a>
                    </p>
                  </td>
                </tr>
              </table>`;

  const content = [
    row(heading("Flyttingen din er bekreftet"), 36),
    row(
      paragraph(
        `Hei ${LEAD.kunde}! Alt er i orden, og ${OFFER_AGENCY.name} har satt av dagen til deg. Vi krysser fingrene for fint vær 12. september.`,
        true,
      ),
      16,
    ),
    row(confirmation, 24),
    row(next, 16),
    row(
      paragraph(
        "Takk for at du brukte Kobly. Vi hører gjerne hvordan det gikk når flyttingen er unnagjort.",
        true,
      ),
      28,
    ),
    row(extra, 24),
  ].join("\n");

  return emailShell({
    preheader: `${OFFER_AGENCY.name} tar kontakt før flyttedagen 12. september.`,
    content,
    baseUrl,
    footerNote: `Du får denne e-posten fordi du bekreftet et tilbud via Kobly (${LEAD.ref}).`,
  });
}
