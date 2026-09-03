"use client";

import Image from "next/image";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowRight,
  Check,
  Info,
  MapPin,
  Send,
  Upload,
  X,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Logo } from "@/components/marketing/Logo";
import { MapPickerOverlay } from "@/components/wizard/MapPickerOverlay";
import { CITIES, type CityKey } from "@/lib/cities";

const WIZARD_IMAGES: Record<number, string> = {
  1: "/images/R1-09476-0023-kopi.jpg",
  2: "/images/R1-07829-0034.jpg",
  3: "/images/rull3_26.jpg",
  4: "/images/R1-09476-0028.jpg",
};

/**
 * Bakgrunnsbilde per steg på mobil, hentet fra samme optimaliserte sett som
 * desktop bruker. To bevisste avvik:
 *
 * - Steg 1 (kart) og steg 5 (oppsummering) har ikke stemningsbilde på desktop,
 *   og får det rolige fellesbildet i stedet for et steg-spesifikt motiv.
 * - Steg 4 sitt desktop-bilde har snitt-lyshet 39 av 255. Bak scrimen blir det
 *   nesten sort, så mobil bruker steg 1-bildet, som ellers er ubrukt her.
 */
const MOBILE_BACKGROUNDS: Record<number, string> = {
  1: "/images/boxes-and-plants.jpg",
  2: WIZARD_IMAGES[2],
  3: WIZARD_IMAGES[3],
  4: WIZARD_IMAGES[1],
  5: "/images/boxes-and-plants.jpg",
};

type FlytteType = "privat" | "bedrift" | "internasjonal";
type Boligtype = "leilighet" | "rekkehus" | "enebolig" | "annet";

type Coord = { lat: number; lon: number };

async function reverseGeocodeAddress(
  c: Coord,
  fallback = "Pin plassert i kart",
): Promise<string> {
  try {
    const res = await fetch(
      `https://ws.geonorge.no/adresser/v1/punktsok?radius=200&lat=${c.lat}&lon=${c.lon}&treffPerSide=1&side=0`,
    );
    if (!res.ok) return fallback;
    const json = (await res.json()) as {
      adresser?: {
        adressetekst: string;
        postnummer: string;
        poststed: string;
      }[];
    };
    const a = json.adresser?.[0];
    return a
      ? `${a.adressetekst}, ${a.postnummer} ${a.poststed}`
      : fallback;
  } catch {
    return fallback;
  }
}

type WizardData = {
  flytteType: FlytteType | "";
  fra: string;
  fraCoord: Coord | null;
  til: string;
  tilCoord: Coord | null;
  boligtype: Boligtype | "";
  flyttedato: string;
  fleksibel: boolean;
  beskrivelse: string;
  bilder: File[];
  navn: string;
  telefon: string;
  epost: string;
};

const TOTAL_STEPS = 5;

export default function WizardPage() {
  return (
    <Suspense fallback={null}>
      <WizardPageInner />
    </Suspense>
  );
}

function WizardPageInner() {
  const params = useSearchParams();
  const fraFraUrl = params.get("fra") ?? "";
  const byFraUrl = params.get("by") as CityKey | null;
  const initialCenter = byFraUrl && CITIES[byFraUrl] ? CITIES[byFraUrl] : null;

  const [step, setStep] = useState(1);
  const [direction, setDirection] = useState<1 | -1>(1);
  const [submitted, setSubmitted] = useState(false);
  const [data, setData] = useState<WizardData>({
    flytteType: "",
    fra: fraFraUrl,
    fraCoord: null,
    til: "",
    tilCoord: null,
    boligtype: "",
    flyttedato: "",
    fleksibel: false,
    beskrivelse: "",
    bilder: [],
    navn: "",
    telefon: "",
    epost: "",
  });

  const update = <K extends keyof WizardData>(key: K, value: WizardData[K]) =>
    setData((d) => ({ ...d, [key]: value }));

  const valid = useMemo(() => {
    switch (step) {
      case 1:
        return data.fra.trim().length > 2 && data.til.trim().length > 2;
      case 2:
        return Boolean(data.flytteType) && Boolean(data.boligtype);
      case 3:
        return data.fleksibel || Boolean(data.flyttedato);
      case 4:
        return true;
      case 5:
        return (
          data.navn.trim().length > 1 &&
          /^[\d\s+]{8,}$/.test(data.telefon) &&
          /\S+@\S+\.\S+/.test(data.epost)
        );
      default:
        return false;
    }
  }, [step, data]);

  const goTo = (target: number) => {
    setDirection(target > step ? 1 : -1);
    setStep(target);
  };
  const next = () => {
    if (!valid) return;
    if (step < TOTAL_STEPS) goTo(step + 1);
    else submit();
  };
  const back = () => {
    if (step > 1) goTo(step - 1);
  };

  const submit = () => {
    console.log("Wizard submitted:", data);
    setSubmitted(true);
  };

  // Mobilbakgrunnen krysstoner: forrige bilde blir liggende til det nye har tonet inn.
  const mobileBackground = MOBILE_BACKGROUNDS[step];
  const prevBackgroundRef = useRef(mobileBackground);
  const [fadingOut, setFadingOut] = useState<string | null>(null);

  useEffect(() => {
    if (prevBackgroundRef.current === mobileBackground) return;
    setFadingOut(prevBackgroundRef.current);
    prevBackgroundRef.current = mobileBackground;
    const timer = setTimeout(() => setFadingOut(null), 400);
    return () => clearTimeout(timer);
  }, [mobileBackground]);

  if (submitted) return <ThankYou />;

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center overflow-y-auto bg-bg">
      {/* Bakgrunn — desktop: fast bilde med lys overlay (uendret) */}
      <div className="absolute inset-0 hidden lg:block" aria-hidden>
        <Image
          src="/images/boxes-and-plants.jpg"
          alt=""
          fill
          priority
          className="object-cover"
        />
        <div className="absolute inset-0 bg-bg/85" />
      </div>

      {/* Bakgrunn — mobil: stegets bilde med scrim, myk crossfade ved bytte */}
      <div className="absolute inset-0 lg:hidden" aria-hidden>
        {fadingOut ? (
          <Image
            src={fadingOut}
            alt=""
            fill
            sizes="100vw"
            className="object-cover object-center"
          />
        ) : null}
        <Image
          key={mobileBackground}
          src={mobileBackground}
          alt=""
          fill
          priority
          sizes="100vw"
          className="wizard-fade-in object-cover object-center"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/75 via-black/55 to-black/70" />
      </div>

      {/* Logo øverst — absolutt på desktop, i flyten på mobil */}
      <Link
        href="/"
        aria-label="Kobly hjem"
        className="absolute left-1/2 top-7 z-10 hidden -translate-x-1/2 lg:block"
      >
        <Logo />
      </Link>

      {/* Logo over kortet — kun mobil. Selve steget ligger inne i kortet. */}
      <div className="relative z-10 w-full px-6 pt-8 pb-2 lg:hidden">
        <Link href="/" aria-label="Kobly hjem" className="inline-block">
          <Logo tone="brand-ink" />
        </Link>
      </div>

      {/* Kort */}
      <div
        className={cn(
          "relative z-10 my-4 flex w-[calc(100%-3rem)] max-w-[1060px] flex-col rounded-[14px] bg-surface-soft shadow-[0_20px_60px_rgba(0,0,0,0.28),0_4px_16px_rgba(0,0,0,0.10)]",
          "sm:my-6 lg:min-h-[640px]",
        )}
      >
        <div className="flex flex-1 flex-col lg:flex-row">
          {/* Venstre kolonne — innhold */}
          <div className="relative flex flex-1 flex-col p-6 pb-24 sm:p-9 sm:pb-24 lg:flex-[0_0_58%] lg:p-11 lg:pb-24">
            {/* Segmenter */}
            <div className="mb-5 flex gap-1">
              {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    "h-0.5 flex-1 rounded-full transition-colors duration-300",
                    i < step ? "bg-ink" : "bg-ink/10",
                  )}
                />
              ))}
            </div>

            {/* Animert steg-innhold */}
            <div
              key={step}
              className={cn(
                "flex flex-1 flex-col gap-3.5",
                direction > 0 ? "wizard-slide-right" : "wizard-slide-left",
              )}
            >
              <span className="text-sm text-ink/45">
                Steg {step} av {TOTAL_STEPS}
              </span>

              {step === 1 && (
                <StepAdresse
                  fra={data.fra}
                  til={data.til}
                  fraCoord={data.fraCoord}
                  tilCoord={data.tilCoord}
                  initialCenter={initialCenter}
                  onFra={(v, coord) => {
                    update("fra", v);
                    if (coord !== undefined) update("fraCoord", coord);
                  }}
                  onTil={(v, coord) => {
                    update("til", v);
                    if (coord !== undefined) update("tilCoord", coord);
                  }}
                />
              )}
              {step === 2 && (
                <StepType
                  flytteType={data.flytteType}
                  boligtype={data.boligtype}
                  onFlytteType={(v) => update("flytteType", v)}
                  onBoligtype={(v) => update("boligtype", v)}
                />
              )}
              {step === 3 && (
                <StepDato
                  date={data.flyttedato}
                  fleksibel={data.fleksibel}
                  onDate={(v) => update("flyttedato", v)}
                  onFleksibel={(v) => update("fleksibel", v)}
                />
              )}
              {step === 4 && (
                <StepGods
                  beskrivelse={data.beskrivelse}
                  bilder={data.bilder}
                  onBeskrivelse={(v) => update("beskrivelse", v)}
                  onBilderChange={(v) => update("bilder", v)}
                />
              )}
              {step === 5 && (
                <StepKontakt
                  navn={data.navn}
                  telefon={data.telefon}
                  epost={data.epost}
                  onNavn={(v) => update("navn", v)}
                  onTelefon={(v) => update("telefon", v)}
                  onEpost={(v) => update("epost", v)}
                />
              )}
            </div>

            {/* Bunn-nav */}
            <div className="absolute right-6 bottom-6 left-6 flex items-center justify-between sm:right-9 sm:bottom-7 sm:left-9 lg:right-11 lg:left-11">
              {step > 1 ? (
                <button
                  type="button"
                  onClick={back}
                  className="text-sm text-ink/40 transition-colors hover:text-ink/70"
                >
                  Tilbake
                </button>
              ) : (
                <span />
              )}
              <button
                type="button"
                onClick={next}
                disabled={!valid}
                className={cn(
                  "inline-flex items-center gap-2 rounded-lg px-7 py-2.5 text-sm font-medium transition-colors",
                  valid
                    ? "bg-brand text-brand-ink hover:bg-brand/90"
                    : "cursor-not-allowed bg-ink/10 text-ink/30",
                )}
              >
                {step === TOTAL_STEPS ? "Send forespørsel" : "Neste"}
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          {/* Høyre kolonne — bilde eller kvittering */}
          <div className="hidden p-4 pl-0 lg:flex lg:flex-1">
            <div
              key={`art-${step}`}
              className="wizard-fade-in relative flex-1 overflow-hidden rounded-[14px] bg-bg"
            >
              {step === 1 ? (
                <MapPanel
                  from={data.fraCoord}
                  to={data.tilCoord}
                  fromLabel={data.fra}
                  toLabel={data.til}
                  initialCenter={initialCenter}
                  onPlaceFrom={(c, addr) => {
                    update("fraCoord", c);
                    update("fra", addr);
                  }}
                  onPlaceTo={(c, addr) => {
                    update("tilCoord", c);
                    update("til", addr);
                  }}
                />
              ) : step === TOTAL_STEPS ? (
                <Summary data={data} />
              ) : (
                <Image
                  src={WIZARD_IMAGES[step]}
                  alt=""
                  aria-hidden
                  fill
                  sizes="(min-width: 1024px) 40vw, 0px"
                  className="object-cover"
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function MapPanel({
  from,
  to,
  fromLabel,
  toLabel,
  initialCenter,
  onPlaceFrom,
  onPlaceTo,
}: {
  from: Coord | null;
  to: Coord | null;
  fromLabel?: string;
  toLabel?: string;
  initialCenter?: { lat: number; lon: number; zoom: number } | null;
  onPlaceFrom: (c: Coord, address: string) => void;
  onPlaceTo: (c: Coord, address: string) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<import("leaflet").Map | null>(null);
  const fromMarkerRef = useRef<import("leaflet").Marker | null>(null);
  const toMarkerRef = useRef<import("leaflet").Marker | null>(null);
  const fromCircleRef = useRef<import("leaflet").Circle | null>(null);
  const lineRef = useRef<import("leaflet").Polyline | null>(null);
  const midpointMarkerRef = useRef<import("leaflet").Marker | null>(null);
  const [placing, setPlacing] = useState<"from" | "to" | null>(null);
  const [locating, setLocating] = useState(false);

  const useMyLocation = () => {
    if (!navigator.geolocation || locating) return;
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const c = { lat: pos.coords.latitude, lon: pos.coords.longitude };
        const address = await reverseGeocodeAddress(c, "Min posisjon");
        onPlaceFrom(c, address);
        setLocating(false);
      },
      () => setLocating(false),
      { enableHighAccuracy: true, timeout: 8000 },
    );
  };

  useEffect(() => {
    let cancelled = false;
    let observer: ResizeObserver | null = null;

    const initMap = async () => {
      const L = (await import("leaflet")).default;
      if (cancelled || !containerRef.current || mapRef.current) return;
      const map = L.map(containerRef.current, {
        center: initialCenter
          ? [initialCenter.lat, initialCenter.lon]
          : [60.5, 10.0],
        zoom: initialCenter ? initialCenter.zoom : 5,
        zoomControl: false,
        attributionControl: false,
      });
      L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        { maxZoom: 19 },
      ).addTo(map);
      mapRef.current = map;
      map.invalidateSize();
    };

    const el = containerRef.current;
    if (!el) return;

    observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const { width, height } = entry.contentRect;
      if (width > 0 && height > 0) {
        if (!mapRef.current) {
          void initMap();
        } else {
          mapRef.current.invalidateSize();
        }
      }
    });
    observer.observe(el);

    if (el.clientWidth > 0 && el.clientHeight > 0) {
      void initMap();
    }

    return () => {
      cancelled = true;
      observer?.disconnect();
      mapRef.current?.remove();
      mapRef.current = null;
      fromMarkerRef.current = null;
      toMarkerRef.current = null;
      fromCircleRef.current = null;
      lineRef.current = null;
      midpointMarkerRef.current = null;
    };
  }, []);

  // Map click handler for placing mode
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !placing) return;
    const handler = async (e: { latlng: { lat: number; lng: number } }) => {
      const c = { lat: e.latlng.lat, lon: e.latlng.lng };
      const address = await reverseGeocodeAddress(c);
      if (placing === "from") onPlaceFrom(c, address);
      else onPlaceTo(c, address);
      setPlacing(null);
    };
    map.on("click", handler);
    const container = containerRef.current?.querySelector<HTMLElement>(
      ".leaflet-container",
    );
    container?.classList.add("placing-mode");
    return () => {
      map.off("click", handler);
      container?.classList.remove("placing-mode");
    };
  }, [placing, onPlaceFrom, onPlaceTo]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const L = (await import("leaflet")).default;
      const map = mapRef.current;
      if (cancelled || !map) return;

      const pinIcon = (color: string) =>
        L.divIcon({
          className: "",
          html: `<div style="width:36px;height:36px;background:${color};border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,0.3);border:2px solid white"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg></div>`,
          iconSize: [36, 36],
          iconAnchor: [18, 18],
        });

      const koblyMidpointIcon = L.divIcon({
        className: "",
        html: `<div style="width:32px;height:32px;background:white;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.18);border:1.5px solid #E6E1D6"><svg width="16" height="16" viewBox="0 0 27 27" fill="none"><circle cx="13.5" cy="13.5" r="11.625" stroke="#221814" stroke-width="3.75"/><path d="M16.5 1.875C12.7075 5.23556 10.5 9.26144 10.5 13.5887C10.5 17.8401 12.6307 21.8006 16.3019 25.125" stroke="#221814" stroke-width="3.75"/></svg></div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      });

      const updateOverlays = () => {
        const fromM = fromMarkerRef.current;
        const toM = toMarkerRef.current;
        if (fromM && toM && lineRef.current) {
          const fromLL = fromM.getLatLng();
          const toLL = toM.getLatLng();
          lineRef.current.setLatLngs([fromLL, toLL]);
          if (midpointMarkerRef.current) {
            midpointMarkerRef.current.setLatLng([
              (fromLL.lat + toLL.lat) / 2,
              (fromLL.lng + toLL.lng) / 2,
            ]);
          }
        }
        if (fromM && fromCircleRef.current) {
          const ll = fromM.getLatLng();
          fromCircleRef.current.setLatLng([ll.lat, ll.lng]);
        }
      };

      const setPin = (
        ref: React.MutableRefObject<import("leaflet").Marker | null>,
        coord: Coord | null,
        color: string,
        onMove: (c: Coord, address: string) => void,
      ) => {
        if (coord) {
          if (ref.current) {
            ref.current.setLatLng([coord.lat, coord.lon]);
          } else {
            const marker = L.marker([coord.lat, coord.lon], {
              icon: pinIcon(color),
              draggable: true,
              autoPan: true,
            }).addTo(map);
            marker.on("drag", updateOverlays);
            marker.on("dragend", async () => {
              const ll = marker.getLatLng();
              const newCoord = { lat: ll.lat, lon: ll.lng };
              const address = await reverseGeocodeAddress(newCoord);
              onMove(newCoord, address);
            });
            ref.current = marker;
          }
        } else if (ref.current) {
          ref.current.remove();
          ref.current = null;
        }
      };

      setPin(fromMarkerRef, from, "#221814", onPlaceFrom);
      setPin(toMarkerRef, to, "#3D5507", onPlaceTo);

      if (from) {
        if (fromCircleRef.current) {
          fromCircleRef.current.setLatLng([from.lat, from.lon]);
        } else {
          fromCircleRef.current = L.circle([from.lat, from.lon], {
            radius: 250,
            color: "#221814",
            fillColor: "#221814",
            fillOpacity: 0.08,
            opacity: 0.25,
            weight: 1,
            interactive: false,
          }).addTo(map);
        }
      } else if (fromCircleRef.current) {
        fromCircleRef.current.remove();
        fromCircleRef.current = null;
      }

      if (from && to) {
        const latlngs: [number, number][] = [
          [from.lat, from.lon],
          [to.lat, to.lon],
        ];
        if (lineRef.current) {
          lineRef.current.setLatLngs(latlngs);
        } else {
          lineRef.current = L.polyline(latlngs, {
            color: "#221814",
            weight: 2.5,
            dashArray: "6 6",
            opacity: 0.7,
          }).addTo(map);
        }
        const midLatLng: [number, number] = [
          (from.lat + to.lat) / 2,
          (from.lon + to.lon) / 2,
        ];
        if (midpointMarkerRef.current) {
          midpointMarkerRef.current.setLatLng(midLatLng);
        } else {
          midpointMarkerRef.current = L.marker(midLatLng, {
            icon: koblyMidpointIcon,
            interactive: false,
            zIndexOffset: 500,
          }).addTo(map);
        }
        map.fitBounds(latlngs, { padding: [40, 40], maxZoom: 13 });
      } else {
        if (lineRef.current) {
          lineRef.current.remove();
          lineRef.current = null;
        }
        if (midpointMarkerRef.current) {
          midpointMarkerRef.current.remove();
          midpointMarkerRef.current = null;
        }
        if (from && !to) map.setView([from.lat, from.lon], 13);
        else if (to && !from) map.setView([to.lat, to.lon], 13);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [from, to]);

  const shortLabel = (s?: string) => {
    if (!s) return null;
    const parts = s.split(",");
    return parts[0]?.trim() || s;
  };
  const fromShort = shortLabel(fromLabel);
  const toShort = shortLabel(toLabel);

  return (
    <>
      <div ref={containerRef} className="absolute inset-0" />

      {fromShort || toShort ? (
        <div className="absolute top-3 left-3 z-[1000] inline-flex items-center gap-2 rounded-[10px] bg-white/95 px-3 py-2 text-xs text-ink shadow-[0_1px_4px_rgba(0,0,0,0.12)] backdrop-blur">
          <span className="text-ink/45">Ca.</span>
          <span className="max-w-[110px] truncate font-medium">
            {fromShort ?? "—"}
          </span>
          <ArrowRight className="h-3 w-3 text-ink/30" />
          <span className="max-w-[110px] truncate font-medium">
            {toShort ?? "—"}
          </span>
        </div>
      ) : null}

      <div className="absolute top-3 right-3 z-[1000] flex flex-col gap-1">
        <button
          type="button"
          onClick={() => mapRef.current?.zoomIn()}
          aria-label="Zoom inn"
          className="inline-flex h-9 w-9 items-center justify-center rounded-[8px] bg-white text-ink/70 shadow-[0_1px_4px_rgba(0,0,0,0.15)] transition-colors hover:bg-[#F7F6F3]"
        >
          <ZoomIn className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={() => mapRef.current?.zoomOut()}
          aria-label="Zoom ut"
          className="inline-flex h-9 w-9 items-center justify-center rounded-[8px] bg-white text-ink/70 shadow-[0_1px_4px_rgba(0,0,0,0.15)] transition-colors hover:bg-[#F7F6F3]"
        >
          <ZoomOut className="h-4 w-4" />
        </button>
      </div>

      <div className="absolute bottom-3 left-3 z-[1000]">
        <button
          type="button"
          onClick={useMyLocation}
          disabled={locating}
          aria-label="Bruk min plassering"
          title="Bruk min plassering"
          className={cn(
            "inline-flex h-9 w-9 items-center justify-center rounded-[8px] bg-white text-ink/70 shadow-[0_1px_4px_rgba(0,0,0,0.15)] transition-colors hover:bg-[#F7F6F3]",
            locating && "animate-pulse",
          )}
        >
          <Send className="h-4 w-4" />
        </button>
      </div>

      <div className="absolute bottom-3 left-1/2 z-[1000] flex -translate-x-1/2 gap-2">
        <button
          type="button"
          onClick={() => setPlacing(placing === "from" ? null : "from")}
          className={cn(
            "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border border-white/70 px-4 py-2 text-xs font-medium shadow-[0_1px_4px_rgba(0,0,0,0.12)] backdrop-blur transition-colors",
            placing === "from"
              ? "bg-brand text-brand-ink"
              : "bg-white/95 text-ink hover:bg-white",
          )}
        >
          {placing === "from" ? "Klikk på kartet" : "Plasser fra"}
        </button>
        <button
          type="button"
          onClick={() => setPlacing(placing === "to" ? null : "to")}
          className={cn(
            "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border border-white/70 px-4 py-2 text-xs font-medium shadow-[0_1px_4px_rgba(0,0,0,0.12)] backdrop-blur transition-colors",
            placing === "to"
              ? "bg-brand text-brand-ink"
              : "bg-white/95 text-ink hover:bg-white",
          )}
        >
          {placing === "to" ? "Klikk på kartet" : "Plasser til"}
        </button>
      </div>
      <div className="group absolute right-3 bottom-3 z-[1000]">
        <button
          type="button"
          aria-label="Kart-attribusjon"
          className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-white/85 text-ink/60 backdrop-blur transition-colors hover:bg-white"
        >
          <Info className="h-3.5 w-3.5" />
        </button>
        <div className="pointer-events-none absolute right-0 bottom-full mb-2 hidden rounded-[6px] bg-white/95 px-2.5 py-1.5 text-[11px] whitespace-nowrap text-ink/70 shadow-md group-hover:block">
          © Leaflet · © CARTO · © OpenStreetMap
        </div>
      </div>
    </>
  );
}

function StepHeader({
  title,
  subtitle,
}: {
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="flex flex-col gap-3.5">
      <h1 className="m-0 font-serif text-3xl font-medium leading-[1.15] tracking-[-0.01em] text-ink sm:text-4xl lg:text-[2.75rem]">
        {title}
      </h1>
      {subtitle ? (
        <p className="-mt-1 text-sm text-ink/40">{subtitle}</p>
      ) : null}
    </div>
  );
}

function PillButton({
  selected,
  onClick,
  children,
}: {
  selected: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center justify-center rounded-[14px] border-[1.5px] px-4 py-4 text-sm transition-colors",
        selected
          ? "border-brand bg-brand text-brand-ink"
          : "border-transparent bg-[#F3EEE3] text-ink/60 hover:bg-[#E8E0D0]",
      )}
    >
      {children}
    </button>
  );
}

function BlockCard({
  selected,
  title,
  description,
  onSelect,
}: {
  selected: boolean;
  title: string;
  description?: string;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "flex w-full items-start gap-4 rounded-[14px] border-[1.5px] p-5 text-left transition-colors",
        selected
          ? "border-brand bg-[#EDE5D8]"
          : "border-transparent bg-[#F3EEE3] hover:bg-[#E8E0D0]",
      )}
    >
      <span
        className={cn(
          "mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-[1.5px] transition-colors",
          selected ? "border-brand bg-brand" : "border-ink/20",
        )}
      >
        {selected ? <Check className="h-3 w-3 text-brand-ink" /> : null}
      </span>
      <span className="flex-1">
        <span className="block text-base font-medium text-ink">{title}</span>
        {description ? (
          <span className="mt-0.5 block text-sm text-ink/50">{description}</span>
        ) : null}
      </span>
    </button>
  );
}

function StepAdresse({
  fra,
  til,
  fraCoord,
  tilCoord,
  initialCenter,
  onFra,
  onTil,
}: {
  fra: string;
  til: string;
  fraCoord: Coord | null;
  tilCoord: Coord | null;
  initialCenter?: { lat: number; lon: number; zoom: number } | null;
  onFra: (v: string, coord?: Coord | null) => void;
  onTil: (v: string, coord?: Coord | null) => void;
}) {
  // Kartvelgeren finnes bare på mobil. På desktop ligger kartet i høyre kolonne.
  const [picker, setPicker] = useState<"fra" | "til" | null>(null);

  const handleUseMyLocation = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const c = { lat: pos.coords.latitude, lon: pos.coords.longitude };
        const address = await reverseGeocodeAddress(c, "Min posisjon");
        onFra(address, c);
      },
      undefined,
      { enableHighAccuracy: true, timeout: 8000 },
    );
  };

  return (
    <>
      <StepHeader
        title="Hvor skal du flytte?"
        subtitle="Skriv inn fra-adresse og til-adresse"
      />
      <div className="mt-4 flex flex-col gap-3.5">
        <div>
          <AddressField
            label="Fra adresse"
            value={fra}
            onChange={onFra}
            placeholder="F.eks. Kongens gate 1, 0153 Oslo"
            onUseMyLocation={handleUseMyLocation}
          />
          <MapPickerButton
            onClick={() => setPicker("fra")}
            placed={Boolean(fraCoord)}
          />
        </div>
        <div>
          <AddressField
            label="Til adresse"
            value={til}
            onChange={onTil}
            placeholder="F.eks. Storgata 14, 0184 Oslo"
          />
          <MapPickerButton
            onClick={() => setPicker("til")}
            placed={Boolean(tilCoord)}
          />
        </div>
      </div>

      <MapPickerOverlay
        open={picker !== null}
        onClose={() => setPicker(null)}
        title={
          picker === "til" ? "Hvor flytter du til?" : "Hvor flytter du fra?"
        }
        initialCoord={picker === "til" ? tilCoord : fraCoord}
        initialCenter={initialCenter}
        reverseGeocode={(c) => reverseGeocodeAddress(c)}
        onConfirm={(coord, address) => {
          if (picker === "til") onTil(address, coord);
          else onFra(address, coord);
        }}
      />
    </>
  );
}

/** «Plasser i kart» under adressefeltet. Kun mobil. */
function MapPickerButton({
  onClick,
  placed,
}: {
  onClick: () => void;
  placed: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "mt-2 inline-flex min-h-[44px] items-center gap-2 rounded-full px-4 text-sm font-medium transition-colors lg:hidden",
        placed
          ? "bg-accent-lime/40 text-ink ring-1 ring-ink/10"
          : "bg-ink/5 text-ink hover:bg-ink/10",
      )}
    >
      {placed ? (
        <>
          <Check className="h-4 w-4 shrink-0" />
          Plassering valgt · endre i kart
        </>
      ) : (
        <>
          <MapPin className="h-4 w-4 shrink-0" />
          Plasser i kart
        </>
      )}
    </button>
  );
}

function StepType({
  flytteType,
  boligtype,
  onFlytteType,
  onBoligtype,
}: {
  flytteType: WizardData["flytteType"];
  boligtype: WizardData["boligtype"];
  onFlytteType: (v: FlytteType) => void;
  onBoligtype: (v: Boligtype) => void;
}) {
  return (
    <>
      <StepHeader title="Hva slags flytting er det?" />
      <div className="mt-4 flex flex-col gap-5">
        <div>
          <p className="mb-2 text-sm text-ink/50">Type</p>
          <div className="grid grid-cols-3 gap-2">
            <PillButton
              selected={flytteType === "privat"}
              onClick={() => onFlytteType("privat")}
            >
              Privat
            </PillButton>
            <PillButton
              selected={flytteType === "bedrift"}
              onClick={() => onFlytteType("bedrift")}
            >
              Bedrift
            </PillButton>
            <PillButton
              selected={flytteType === "internasjonal"}
              onClick={() => onFlytteType("internasjonal")}
            >
              Internasjonal
            </PillButton>
          </div>
        </div>
        <div>
          <p className="mb-2 text-sm text-ink/50">Størrelse</p>
          <div className="grid grid-cols-2 gap-2">
            <PillButton
              selected={boligtype === "leilighet"}
              onClick={() => onBoligtype("leilighet")}
            >
              Leilighet
            </PillButton>
            <PillButton
              selected={boligtype === "rekkehus"}
              onClick={() => onBoligtype("rekkehus")}
            >
              Rekkehus
            </PillButton>
            <PillButton
              selected={boligtype === "enebolig"}
              onClick={() => onBoligtype("enebolig")}
            >
              Enebolig
            </PillButton>
            <PillButton
              selected={boligtype === "annet"}
              onClick={() => onBoligtype("annet")}
            >
              Annet
            </PillButton>
          </div>
        </div>
      </div>
    </>
  );
}

type Adresseforslag = {
  adressetekst: string;
  postnummer: string;
  poststed: string;
  representasjonspunkt?: { lat: number; lon: number };
};

function AddressField({
  label,
  value,
  onChange,
  placeholder,
  onUseMyLocation,
}: {
  label: string;
  value: string;
  onChange: (v: string, coord?: Coord | null) => void;
  placeholder?: string;
  onUseMyLocation?: () => void;
}) {
  const [forslag, setForslag] = useState<Adresseforslag[]>([]);
  const [focused, setFocused] = useState(false);
  const [justSelected, setJustSelected] = useState(false);

  useEffect(() => {
    if (justSelected) {
      setJustSelected(false);
      return;
    }
    if (!focused || value.trim().length < 2) {
      setForslag([]);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(
          `https://ws.geonorge.no/adresser/v1/sok?sok=${encodeURIComponent(value)}&treffPerSide=8&side=0`,
          { signal: controller.signal },
        );
        if (!res.ok) return;
        const json = (await res.json()) as { adresser?: Adresseforslag[] };
        setForslag(json.adresser ?? []);
      } catch {
        // Ignorer abort/nettverksfeil
      }
    }, 200);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [value, focused, justSelected]);

  const velg = (a: Adresseforslag) => {
    const coord = a.representasjonspunkt
      ? { lat: a.representasjonspunkt.lat, lon: a.representasjonspunkt.lon }
      : null;
    onChange(`${a.adressetekst}, ${a.postnummer} ${a.poststed}`, coord);
    setForslag([]);
    setJustSelected(true);
  };

  const visForslag =
    focused && (forslag.length > 0 || Boolean(onUseMyLocation));

  return (
    <div className="relative">
      <label className="block">
        <span className="mb-1.5 block text-sm text-ink/50">
          {label}
        </span>
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value, null)}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 120)}
          placeholder={placeholder}
          autoComplete="off"
          className="w-full rounded-[14px] border-[1.5px] border-ink/10 bg-[#F7F5F1] px-4 py-3.5 text-sm text-ink outline-none transition-colors focus:border-brand"
        />
      </label>
      {visForslag ? (
        <ul className="absolute top-full right-0 left-0 z-50 mt-1 max-h-72 overflow-y-auto rounded-[14px] border border-ink/10 bg-surface shadow-lg">
          {onUseMyLocation ? (
            <li>
              <button
                type="button"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => {
                  onUseMyLocation();
                  setFocused(false);
                }}
                className="flex w-full items-center gap-2 px-4 py-3 text-left text-sm text-ink transition-colors hover:bg-[#F3EEE3]"
              >
                <MapPin className="h-4 w-4 text-ink/60" />
                Bruk min plassering
              </button>
            </li>
          ) : null}
          {forslag.map((a, i) => (
            <li key={`${a.adressetekst}-${a.postnummer}-${i}`}>
              <button
                type="button"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => velg(a)}
                className="flex w-full flex-col items-start gap-0.5 px-4 py-3 text-left text-sm transition-colors hover:bg-[#F3EEE3]"
              >
                <span className="text-ink">{a.adressetekst}</span>
                <span className="text-xs text-ink/50">
                  {a.postnummer} {a.poststed}
                </span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function StepDato({
  date,
  fleksibel,
  onDate,
  onFleksibel,
}: {
  date: string;
  fleksibel: boolean;
  onDate: (v: string) => void;
  onFleksibel: (v: boolean) => void;
}) {
  return (
    <>
      <StepHeader
        title="Når skal du flytte?"
        subtitle="Velg en dato eller la oss vite om du er fleksibel"
      />
      <div className="mt-2 flex flex-col gap-4">
        <label className="block">
          <span className="mb-1.5 block text-sm text-ink/50">
            Ønsket flyttedato
          </span>
          <input
            type="date"
            value={date}
            onChange={(e) => {
              onDate(e.target.value);
              if (e.target.value) onFleksibel(false);
            }}
            disabled={fleksibel}
            className={cn(
              "w-full rounded-[14px] border-[1.5px] border-ink/10 bg-[#F7F5F1] px-4 py-3.5 text-sm text-ink outline-none transition-colors focus:border-brand",
              fleksibel && "opacity-50",
            )}
          />
        </label>
        <button
          type="button"
          onClick={() => {
            onFleksibel(!fleksibel);
            if (!fleksibel) onDate("");
          }}
          className={cn(
            "inline-flex items-center gap-3 self-start rounded-full border-[1.5px] border-dashed px-6 py-3 text-sm transition-colors",
            fleksibel
              ? "border-solid border-brand bg-[#EDE5D8] text-ink"
              : "border-ink/20 text-ink/60 hover:border-ink/40",
          )}
        >
          <span
            className={cn(
              "inline-flex h-5 w-5 items-center justify-center rounded-full border-[1.5px] transition-colors",
              fleksibel ? "border-brand bg-brand" : "border-ink/20",
            )}
          >
            {fleksibel ? <Check className="h-3 w-3 text-brand-ink" /> : null}
          </span>
          Jeg er fleksibel på datoen
        </button>
      </div>
    </>
  );
}

function StepGods({
  beskrivelse,
  bilder,
  onBeskrivelse,
  onBilderChange,
}: {
  beskrivelse: string;
  bilder: File[];
  onBeskrivelse: (v: string) => void;
  onBilderChange: (v: File[]) => void;
}) {
  const previews = useMemo(
    () => bilder.map((f) => URL.createObjectURL(f)),
    [bilder],
  );
  useEffect(
    () => () => previews.forEach((url) => URL.revokeObjectURL(url)),
    [previews],
  );

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    onBilderChange([...bilder, ...Array.from(files)]);
  };

  const removeAt = (i: number) =>
    onBilderChange(bilder.filter((_, idx) => idx !== i));

  return (
    <>
      <StepHeader
        title="Hva skal du flytte?"
        subtitle="Legg til bilder eller en beskrivelse av tingene dine."
      />
      <div className="mt-4 flex flex-col gap-6">
        <label className="block">
          <span className="mb-2 block text-base font-medium text-ink">
            Beskrivelse
          </span>
          <textarea
            value={beskrivelse}
            onChange={(e) => onBeskrivelse(e.target.value)}
            placeholder="F.eks. 3-seters sofa, stort spisebord, 2 senger, 10 esker..."
            rows={4}
            className="w-full resize-none rounded-[14px] border-[1.5px] border-ink/10 bg-[#F7F5F1] px-4 py-3.5 text-sm text-ink outline-none transition-colors focus:border-brand"
          />
        </label>
        <div>
          <p className="mb-1 text-base font-medium text-ink">Bilder</p>
          <p className="mb-3 text-sm text-ink/50">
            Legg ved bilder av tingene dine for et mer presist tilbud.
          </p>
          <div className="grid grid-cols-4 gap-2">
            {previews.map((url, i) => (
              <div
                key={url}
                className="relative aspect-square overflow-hidden rounded-[14px]"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={url}
                  alt=""
                  className="h-full w-full object-cover"
                />
                <button
                  type="button"
                  onClick={() => removeAt(i)}
                  aria-label="Fjern bilde"
                  className="absolute top-1 right-1 inline-flex h-5 w-5 items-center justify-center rounded-full bg-ink/70 text-white transition-colors hover:bg-ink"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
            <label className="flex aspect-square cursor-pointer flex-col items-center justify-center gap-1.5 rounded-[14px] border-[1.5px] border-dashed border-ink/20 bg-[#F7F5F1] text-xs text-ink/60 transition-colors hover:border-ink/40">
              <Upload className="h-4 w-4" />
              <span>Last opp</span>
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={(e) => handleFiles(e.target.files)}
                className="hidden"
              />
            </label>
          </div>
        </div>
      </div>
    </>
  );
}

function StepKontakt({
  navn,
  telefon,
  epost,
  onNavn,
  onTelefon,
  onEpost,
}: {
  navn: string;
  telefon: string;
  epost: string;
  onNavn: (v: string) => void;
  onTelefon: (v: string) => void;
  onEpost: (v: string) => void;
}) {
  return (
    <>
      <StepHeader
        title="La oss ta kontakt"
        subtitle="Vi kobler deg med tre byråer. Du hører fra dem innen 24 timer."
      />
      <div className="mt-2 grid gap-3.5 sm:grid-cols-2">
        <TextField
          label="Navn"
          value={navn}
          onChange={onNavn}
          placeholder="Ola Nordmann"
        />
        <TextField
          label="Telefon"
          value={telefon}
          onChange={onTelefon}
          placeholder="+47 000 00 000"
          inputMode="tel"
        />
        <div className="sm:col-span-2">
          <TextField
            label="E-post"
            value={epost}
            onChange={onEpost}
            placeholder="ola@eksempel.no"
            type="email"
          />
        </div>
      </div>
    </>
  );
}

function TextField({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
  inputMode,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  inputMode?: "text" | "tel" | "email" | "numeric";
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm text-ink/50">
        {label}
      </span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        inputMode={inputMode}
        className="w-full rounded-[14px] border-[1.5px] border-ink/10 bg-[#F7F5F1] px-4 py-3.5 text-sm text-ink outline-none transition-colors focus:border-brand"
      />
    </label>
  );
}

function Summary({ data }: { data: WizardData }) {
  const typeLabel: Record<FlytteType, string> = {
    privat: "Privat flytting",
    bedrift: "Bedriftsflytting",
    internasjonal: "Internasjonal",
  };
  const boligLabel: Record<Boligtype, string> = {
    leilighet: "Leilighet",
    rekkehus: "Rekkehus",
    enebolig: "Enebolig",
    annet: "Annet",
  };
  const formattedDate = data.flyttedato
    ? new Date(data.flyttedato).toLocaleDateString("no-NO", {
        day: "numeric",
        month: "long",
        year: "numeric",
      })
    : null;
  const previews = useMemo(
    () => data.bilder.map((f) => URL.createObjectURL(f)),
    [data.bilder],
  );
  useEffect(
    () => () => previews.forEach((url) => URL.revokeObjectURL(url)),
    [previews],
  );

  return (
    <div className="flex h-full flex-col p-8 lg:p-9">
      <span className="text-sm text-ink/45">
        Kvittering
      </span>
      <h3 className="mt-2 font-serif text-2xl font-medium leading-tight text-ink">
        Din forespørsel
      </h3>
      <p className="mt-2 text-sm text-ink/50">
        Vi sender denne til tre kvalitetssjekkede byråer i ditt område.
      </p>

      <div className="mt-7 flex flex-col gap-5">
        {data.fra ? <SummaryRow label="Fra" value={data.fra} /> : null}
        {data.til ? <SummaryRow label="Til" value={data.til} /> : null}
        {data.flytteType || data.boligtype ? (
          <SummaryRow
            label="Flytting"
            value={[
              data.flytteType ? typeLabel[data.flytteType] : null,
              data.boligtype ? boligLabel[data.boligtype] : null,
            ]
              .filter(Boolean)
              .join(" · ")}
          />
        ) : null}
        {formattedDate || data.fleksibel ? (
          <SummaryRow
            label="Når"
            value={data.fleksibel ? "Fleksibel dato" : (formattedDate ?? "")}
          />
        ) : null}
        {data.beskrivelse.trim() ? (
          <SummaryRow label="Innhold" value={data.beskrivelse.trim()} />
        ) : null}
        {data.bilder.length > 0 ? (
          <div className="flex flex-col gap-2">
            <span className="text-sm text-ink/50">Bilder</span>
            <div className="grid grid-cols-4 gap-1.5">
              {previews.map((url) => (
                <div
                  key={url}
                  className="relative aspect-square overflow-hidden rounded-[10px]"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={url}
                    alt=""
                    className="h-full w-full object-cover"
                  />
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-sm text-ink/50">{label}</span>
      <span className="text-sm leading-snug text-ink">{value}</span>
    </div>
  );
}

function ThankYou() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-bg px-6 py-10">
      {/* Samme bakgrunnsbilde som wizarden, men mørklagt */}
      <div className="absolute inset-0" aria-hidden>
        <Image
          src="/images/boxes-and-plants.jpg"
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover"
        />
        <div className="absolute inset-0 bg-black/65" />
      </div>

      <div className="wizard-fade-in relative z-10 w-full max-w-[520px] rounded-[14px] bg-surface-soft px-7 py-10 text-center shadow-[0_24px_60px_rgba(0,0,0,0.35)] sm:px-10 sm:py-12">
        <RoutingIllustration />
        <h1 className="mt-9 font-serif text-3xl font-medium leading-[1.1] text-ink sm:text-4xl">
          Forespørselen er sendt!
        </h1>
        <p className="mt-4 text-base leading-relaxed text-ink-muted">
          Vi har nå sendt forespørselen din til tre kvalitetssjekkede byråer i
          ditt område. Du mottar tilbud på e-post innen kort tid.
        </p>
        <Link
          href="/"
          className="mt-9 inline-flex w-full items-center justify-center rounded-full bg-brand px-6 py-4 text-base font-medium text-brand-ink transition-colors hover:bg-brand/90"
        >
          Tilbake til forsiden
        </Link>
      </div>
    </div>
  );
}

/** Kobly til venstre, tre byråer til høyre. Viser at forespørselen rutes videre. */
function RoutingIllustration() {
  return (
    <div className="flex items-center justify-center gap-3">
      <span className="inline-flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-brand text-brand-ink">
        <svg width="24" height="24" viewBox="0 0 27 27" fill="none" aria-hidden>
          <circle
            cx="13.5"
            cy="13.5"
            r="11.625"
            stroke="currentColor"
            strokeWidth="3.75"
          />
          <path
            d="M16.5 1.875C12.7075 5.23556 10.5 9.26144 10.5 13.5887C10.5 17.8401 12.6307 21.8006 16.3019 25.125"
            stroke="currentColor"
            strokeWidth="3.75"
          />
        </svg>
      </span>

      <span aria-hidden className="flex shrink-0 items-center gap-1">
        <span className="h-1.5 w-1.5 rounded-full bg-ink/25" />
        <span className="h-1.5 w-1.5 rounded-full bg-ink/25" />
        <span className="h-1.5 w-1.5 rounded-full bg-ink/25" />
      </span>

      <span className="flex items-center gap-2">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="success-circle inline-flex h-12 w-12 items-center justify-center rounded-[12px] bg-accent-lime"
            style={{ animationDelay: `${120 + i * 110}ms` }}
          >
            <svg width="26" height="26" viewBox="0 0 42 42" fill="none" aria-hidden>
              <path
                d="M20.6 33.27V20.74M20.6 20.74 9.69 14.48M20.6 20.74l10.91-6.26M14.96 11.06l11.27 6.45M19.35 32.93c.38.22.81.34 1.25.34s.87-.12 1.25-.34l8.77-5.01c.38-.22.7-.54.92-.92.22-.38.34-.81.34-1.25V15.73c0-.44-.12-.87-.34-1.25-.22-.38-.54-.7-.92-.92l-8.77-5.01c-.38-.22-.81-.34-1.25-.34s-.87.12-1.25.34l-8.77 5.01c-.38.22-.7.54-.92.92-.22.38-.34.81-.34 1.25v10.02c0 .44.12.87.34 1.25.22.38.54.7.92.92l8.77 5.01Z"
                stroke="#3D5507"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
        ))}
      </span>
    </div>
  );
}

