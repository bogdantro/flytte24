import {
  COLORS,
  SANS,
  agencyCard,
  button,
  card,
  detailRow,
  emailShell,
  heading,
  paragraph,
  row,
} from "./layout";
import { LEAD, OFFER, OFFER_AGENCY } from "./dummy";
import { formatRating } from "@/lib/agencies";

/** E-post B: kunden har fått et tilbud fra et av byråene. */
export const offerSubject = `Du har fått et tilbud fra ${OFFER_AGENCY.name}`;

export function offerEmail(baseUrl: string): string {
  const agency = agencyCard({
    name: OFFER_AGENCY.name,
    logo: OFFER_AGENCY.logo,
    rating: formatRating(OFFER_AGENCY.rating),
    reviewCount: OFFER_AGENCY.reviewCount,
    jobs: OFFER_AGENCY.jobsCompleted,
    baseUrl,
  });

  const price = `<table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color:${COLORS.bg}; border-radius:14px;">
                <tr>
                  <td class="kobly-card" style="padding:22px 24px;">
                    <p style="margin:0; font-family:${SANS}; font-size:13px; line-height:1.4; color:${COLORS.inkMuted};">Prisestimat</p>
                    <p style="margin:4px 0 0; font-family:${SANS}; font-size:30px; font-weight:600; line-height:1.2; color:${COLORS.ink};">${OFFER.pris}</p>
                    <p style="margin:4px 0 0; font-family:${SANS}; font-size:14px; line-height:1.5; color:${COLORS.inkMuted};">${OFFER.prisType}</p>
                  </td>
                </tr>
              </table>`;

  const details = card(
    [
      detailRow("Omfang", OFFER.omfang),
      detailRow("Inkludert", OFFER.inkludert),
      detailRow("Flyttedato", LEAD.dato),
      detailRow("Gyldighet", OFFER.gyldig, true),
    ].join("\n"),
  );

  const hint = `<table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="border-top:1px solid ${COLORS.line}; padding-top:22px;">
                    <p style="margin:0; font-family:${SANS}; font-size:14px; line-height:1.65; color:${COLORS.inkMuted};">
                      Du kan få <strong style="color:${COLORS.ink};">inntil 3 tilbud</strong> på denne flyttingen. Vent gjerne til du har flere før du bestemmer deg, så ser du hva som faktisk er en god pris.
                    </p>
                  </td>
                </tr>
              </table>`;

  const content = [
    row(heading(`${OFFER_AGENCY.name} har sendt deg et tilbud`), 36),
    row(
      paragraph(
        `Hei ${LEAD.kunde}! Det første tilbudet på flyttingen din er klart. Her er hovedpunktene:`,
        true,
      ),
      16,
    ),
    row(agency, 24),
    row(price, 16),
    row(details, 16),
    row(
      `<div class="kobly-btn">${button("Se tilbudet", `${baseUrl || "https://kobly.no"}/wizard`)}</div>`,
      28,
    ),
    row(hint, 28),
  ].join("\n");

  return emailShell({
    preheader: `${OFFER.pris} for flyttingen 12. september. Se hva som er inkludert.`,
    content,
    baseUrl,
    footerNote: `Du får denne e-posten fordi du ba om tilbud på flytting via Kobly (${LEAD.ref}).`,
  });
}
