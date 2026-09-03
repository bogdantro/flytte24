import { newLeadEmail, newLeadSubject } from "./new-lead";
import { receiptEmail, receiptSubject } from "./receipt";
import { offerEmail, offerSubject } from "./offer";
import {
  bookingConfirmedEmail,
  bookingConfirmedSubject,
} from "./booking-confirmed";

export type EmailTemplate = {
  id: string;
  /** Navn i forhåndsvisningen. */
  name: string;
  /** Hvem e-posten går til og når den utløses. */
  context: string;
  subject: string;
  render: (baseUrl: string) => string;
};

/** Rekkefølgen følger kundereisen. */
export const EMAIL_TEMPLATES: EmailTemplate[] = [
  {
    id: "receipt",
    name: "Kvittering på forespørsel",
    context: "Til kunde · rett etter innsendt wizard",
    subject: receiptSubject,
    render: receiptEmail,
  },
  {
    id: "new-lead",
    name: "Ny flytteforespørsel",
    context: "Til byrå · når en forespørsel matches til dem",
    subject: newLeadSubject,
    render: newLeadEmail,
  },
  {
    id: "offer",
    name: "Nytt tilbud mottatt",
    context: "Til kunde · når et byrå har sendt tilbud",
    subject: offerSubject,
    render: offerEmail,
  },
  {
    id: "booking-confirmed",
    name: "Flytting bekreftet",
    context: "Til kunde · når kunden har valgt byrå",
    subject: bookingConfirmedSubject,
    render: bookingConfirmedEmail,
  },
];

export function getEmailTemplate(id: string): EmailTemplate | undefined {
  return EMAIL_TEMPLATES.find((t) => t.id === id);
}
