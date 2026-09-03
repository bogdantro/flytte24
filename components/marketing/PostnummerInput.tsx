"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowRight, Search } from "lucide-react";
import { cn } from "@/lib/utils";

type Variant = "light" | "onDark";
type Layout = "inline" | "stack";

export function PostnummerInput({
  variant = "light",
  layout = "inline",
  showIcon = false,
  className,
  placeholder = "Ditt postnummer",
  cta = "Få 3 tilbud gratis",
}: {
  variant?: Variant;
  layout?: Layout;
  showIcon?: boolean;
  className?: string;
  placeholder?: string;
  cta?: string;
}) {
  const router = useRouter();
  const [value, setValue] = useState("");
  const [touched, setTouched] = useState(false);

  const valid = /^\d{4}$/.test(value);
  const showError = touched && value.length > 0 && !valid;

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (!valid) return;
    router.push(`/wizard?fra=${value}`);
  };

  const isOnDark = variant === "onDark";

  return (
    <form
      onSubmit={onSubmit}
      className={cn("w-full max-w-md", className)}
      noValidate
    >
      <div
        className={cn(
          "flex gap-2",
          layout === "inline" ? "flex-row items-center" : "flex-col",
        )}
      >
        <div
          className={cn(
            "flex items-center gap-3 rounded-full px-5 py-3 transition-colors",
            layout === "inline" ? "flex-1" : "w-full",
            isOnDark
              ? "bg-white/10 text-brand-ink ring-1 ring-white/15 focus-within:ring-white/30"
              : "bg-surface text-ink ring-1 ring-line focus-within:ring-ink/20",
          )}
        >
          {showIcon ? (
            <Search
              className={cn(
                "h-5 w-5 shrink-0",
                isOnDark ? "text-brand-ink/60" : "text-ink-muted",
              )}
              strokeWidth={1.6}
              aria-hidden
            />
          ) : null}
          <input
            type="text"
            inputMode="numeric"
            pattern="\d{4}"
            maxLength={4}
            value={value}
            onChange={(e) => setValue(e.target.value.replace(/\D/g, ""))}
            onBlur={() => setTouched(true)}
            placeholder={placeholder}
            aria-label="Postnummer"
            aria-invalid={showError || undefined}
            className={cn(
              "w-full bg-transparent text-base outline-none",
              isOnDark
                ? "placeholder:text-brand-ink/50"
                : "placeholder:text-ink-muted/70",
            )}
          />
        </div>
        <button
          type="submit"
          className={cn(
            "group inline-flex items-center justify-center gap-2 rounded-full px-5 py-3.5 text-sm font-medium transition-colors sm:px-6 sm:text-base",
            layout === "inline" ? "shrink-0" : "w-full",
            isOnDark
              ? "bg-brand-ink text-brand hover:bg-white"
              : "bg-brand text-brand-ink hover:bg-brand/90",
          )}
        >
          {cta}
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
        </button>
      </div>
      {showError ? (
        <p
          className={cn(
            "mt-2 text-sm",
            isOnDark ? "text-brand-ink/80" : "text-ink-muted",
          )}
          role="alert"
        >
          Skriv inn et gyldig postnummer (4 siffer).
        </p>
      ) : null}
    </form>
  );
}
