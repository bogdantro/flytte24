"use client";

import { useEffect } from "react";
import { cn } from "@/lib/utils";

/**
 * Gjenbrukbart fullskjerms-overlay (mobilmeny, kart på mobil, o.l.).
 * Låser bakgrunns-scroll og lukker på Escape.
 */
export function FullscreenOverlay({
  open,
  onClose,
  children,
  className,
  label,
}: {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
  label: string;
}) {
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={label}
      className={cn(
        "wizard-fade-in fixed inset-0 z-[100] flex flex-col bg-bg",
        className,
      )}
    >
      {children}
    </div>
  );
}
