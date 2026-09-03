"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Check, Crosshair, LocateFixed, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { FullscreenOverlay } from "@/components/marketing/FullscreenOverlay";

export type Coord = { lat: number; lon: number };

/**
 * Fullskjerms kartvelger for mobil. Nålen står fast midt på skjermen, og
 * brukeren drar kartet under den. Samme overlay-mønster som mobilmenyen.
 */
export function MapPickerOverlay({
  open,
  onClose,
  onConfirm,
  title,
  initialCoord,
  initialCenter,
  reverseGeocode,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: (coord: Coord, address: string) => void;
  title: string;
  initialCoord: Coord | null;
  initialCenter?: { lat: number; lon: number; zoom: number } | null;
  reverseGeocode: (c: Coord) => Promise<string>;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<import("leaflet").Map | null>(null);
  const [address, setAddress] = useState<string | null>(null);
  const [looking, setLooking] = useState(false);
  const [locating, setLocating] = useState(false);

  const lookupCenter = useCallback(async () => {
    const map = mapRef.current;
    if (!map) return;
    const c = map.getCenter();
    setLooking(true);
    const found = await reverseGeocode({ lat: c.lat, lon: c.lng });
    setAddress(found);
    setLooking(false);
  }, [reverseGeocode]);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    let map: import("leaflet").Map | null = null;

    (async () => {
      const L = (await import("leaflet")).default;
      if (cancelled || !containerRef.current) return;

      const start: [number, number] = initialCoord
        ? [initialCoord.lat, initialCoord.lon]
        : initialCenter
          ? [initialCenter.lat, initialCenter.lon]
          : [59.9139, 10.7522];
      // Nær nok til at nålen betyr noe, også når vi bare har et bysentrum.
      const zoom = initialCoord ? 16 : 14;

      map = L.map(containerRef.current, {
        center: start,
        zoom,
        zoomControl: false,
        attributionControl: false,
      });
      L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        { maxZoom: 19 },
      ).addTo(map);
      mapRef.current = map;
      map.invalidateSize();
      map.on("moveend", () => void lookupCenter());
      void lookupCenter();
    })();

    return () => {
      cancelled = true;
      map?.remove();
      mapRef.current = null;
      setAddress(null);
    };
    // initialCoord/initialCenter leses kun ved åpning, med vilje.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, lookupCenter]);

  const useMyLocation = () => {
    if (!navigator.geolocation || locating) return;
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        mapRef.current?.setView(
          [pos.coords.latitude, pos.coords.longitude],
          16,
        );
        setLocating(false);
      },
      () => setLocating(false),
      { enableHighAccuracy: true, timeout: 8000 },
    );
  };

  const confirm = () => {
    const map = mapRef.current;
    if (!map) return;
    const c = map.getCenter();
    onConfirm(
      { lat: c.lat, lon: c.lng },
      address ?? "Plassering valgt i kart",
    );
    onClose();
  };

  return (
    <FullscreenOverlay open={open} onClose={onClose} label={title}>
      <div className="relative flex h-full flex-col">
        <div ref={containerRef} className="absolute inset-0 touch-none" />

        {/* Toppfelt med instruksjon */}
        <div className="relative z-[1000] flex items-start gap-3 bg-gradient-to-b from-bg via-bg/95 to-transparent px-4 pt-4 pb-10">
          <div className="flex-1 rounded-[14px] bg-surface px-4 py-3 shadow-[0_2px_10px_rgba(0,0,0,0.10)]">
            <p className="text-sm font-semibold text-ink">{title}</p>
            <p className="mt-0.5 text-sm text-ink-muted">
              Flytt kartet så nålen står på adressen din
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Lukk kart"
            className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-surface text-ink shadow-[0_2px_10px_rgba(0,0,0,0.10)] transition-colors hover:bg-surface-soft"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Fast nål i midten */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 z-[1000] flex items-center justify-center"
        >
          <span className="relative -translate-y-4">
            <span className="flex h-11 w-11 items-center justify-center rounded-full border-2 border-white bg-brand shadow-[0_3px_10px_rgba(0,0,0,0.35)]">
              <Crosshair className="h-5 w-5 text-brand-ink" />
            </span>
            <span className="absolute left-1/2 top-full h-4 w-0.5 -translate-x-1/2 bg-brand/70" />
            <span className="absolute left-1/2 top-[calc(100%+16px)] h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-brand/40" />
          </span>
        </div>

        {/* Min posisjon */}
        <div className="relative z-[1000] mt-auto flex justify-end px-4 pb-3">
          <button
            type="button"
            onClick={useMyLocation}
            aria-label="Bruk min posisjon"
            className={cn(
              "inline-flex h-11 w-11 items-center justify-center rounded-full bg-surface text-ink shadow-[0_2px_10px_rgba(0,0,0,0.10)] transition-colors hover:bg-surface-soft",
              locating && "animate-pulse",
            )}
          >
            <LocateFixed className="h-5 w-5" />
          </button>
        </div>

        {/* Bekreft-panel */}
        <div className="relative z-[1000] bg-bg px-4 pt-4 pb-[max(1rem,env(safe-area-inset-bottom))] shadow-[0_-4px_20px_rgba(0,0,0,0.08)]">
          <p className="text-xs text-ink-muted">Valgt plassering</p>
          <p
            className={cn(
              "mt-1 min-h-[2.75rem] text-base leading-snug font-medium text-ink",
              looking && "opacity-50",
            )}
          >
            {address ?? "Finner adresse …"}
          </p>
          <button
            type="button"
            onClick={confirm}
            className="mt-3 inline-flex min-h-[52px] w-full items-center justify-center gap-2 rounded-full bg-brand px-6 text-base font-medium text-brand-ink transition-colors hover:bg-brand/90"
          >
            <Check className="h-5 w-5" />
            Bruk denne plasseringen
          </button>
        </div>
      </div>
    </FullscreenOverlay>
  );
}
