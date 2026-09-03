"use client";

import { cn } from "@/lib/utils";

export function RadioCard({
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
      role="radio"
      aria-checked={selected}
      onClick={onSelect}
      className={cn(
        "group flex w-full items-start gap-4 rounded-xl bg-surface p-5 text-left transition-all",
        "ring-1",
        selected
          ? "ring-2 ring-brand"
          : "ring-line hover:ring-ink/20",
      )}
    >
      <span
        className={cn(
          "mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full transition-colors",
          selected ? "bg-brand" : "ring-1 ring-line",
        )}
      >
        {selected ? (
          <span className="h-2 w-2 rounded-full bg-brand-ink" />
        ) : null}
      </span>
      <span className="flex-1">
        <span className="block text-base font-semibold text-ink">{title}</span>
        {description ? (
          <span className="mt-0.5 block text-sm text-ink-muted">
            {description}
          </span>
        ) : null}
      </span>
    </button>
  );
}
