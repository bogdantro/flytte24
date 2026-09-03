import { getAgency } from "@/lib/agencies";

/**
 * Felles dummy-forespørsel for alle e-postmalene, slik at de fire e-postene
 * viser samme flytting fra kvittering til bekreftelse.
 */
export const LEAD = {
  ref: "KOB-2026-4821",
  kunde: "Ingrid",
  fraKort: "Grünerløkka, Oslo (0555)",
  tilKort: "Nordstrand, Oslo (1170)",
  fraFull: "Thorvald Meyers gate 44, 0555 Oslo",
  tilFull: "Ekebergveien 128, 1170 Oslo",
  dato: "Fredag 12. september 2026",
  bolig: "3-roms leilighet, ca. 68 m²",
  etasje: "3. etasje uten heis → 1. etasje med kort bæreavstand",
  tjenester: "Flyttehjelp, flyttevask, pianotransport",
  kommentar:
    "Vi har et eldre piano i stua som må fraktes forsiktig. Ellers er det vanlig innbo. Kan være fleksible på tidspunkt på dagen.",
} as const;

/**
 * Byrået som brukes i tilbuds- og bekreftelses-e-posten.
 * Flyttefoten er valgt fordi logoen finnes som PNG. SVG rendres ikke i de
 * fleste e-postklientene.
 */
export const OFFER_AGENCY = getAgency("flyttefoten")!;

export const OFFER = {
  pris: "14 200 kr",
  prisType: "Fastpris, inkludert mva.",
  omfang: "2 mann og stor flyttebil, ca. 6 timer",
  inkludert: "Bæring, transport, forsikring inntil 1 mill., flyttevask",
  gyldig: "Tilbudet gjelder i 7 dager",
} as const;
