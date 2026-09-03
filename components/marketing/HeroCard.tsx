import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

function KoblyMark({ className }: { className?: string }) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 27 27"
      fill="none"
      aria-hidden
      className={className}
    >
      <circle cx="13.5" cy="13.5" r="11.625" stroke="currentColor" strokeWidth="3.75" />
      <path
        d="M16.5 1.875C12.7075 5.23556 10.5 9.26144 10.5 13.5887C10.5 17.8401 12.6307 21.8006 16.3019 25.125"
        stroke="currentColor"
        strokeWidth="3.75"
      />
    </svg>
  );
}

function HeroIcons({ endVisual }: { endVisual?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-center gap-2.5">
      <span className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-brand text-brand-ink">
        <KoblyMark className="h-5 w-5" />
      </span>
      <span className="flex items-center gap-1">
        <span className="h-1.5 w-1.5 rounded-full bg-ink/25" />
        <span className="h-1.5 w-1.5 rounded-full bg-ink/25" />
        <span className="h-1.5 w-1.5 rounded-full bg-ink/25" />
      </span>
      {endVisual ?? (
        <span className="inline-flex h-12 w-12 items-center justify-center rounded-[14px] bg-accent-lime">
        <svg width="28" height="28" viewBox="0 0 42 42" fill="none" aria-hidden>
          <path
            d="M20.6 33.27V20.74M20.6 20.74 9.69 14.48M20.6 20.74l10.91-6.26M14.96 11.06l11.27 6.45M19.35 32.93c.38.22.81.34 1.25.34s.87-.12 1.25-.34l8.77-5.01c.38-.22.7-.54.92-.92.22-.38.34-.81.34-1.25V15.73c0-.44-.12-.87-.34-1.25-.22-.38-.54-.7-.92-.92l-8.77-5.01c-.38-.22-.81-.34-1.25-.34s-.87.12-1.25.34l-8.77 5.01c-.38.22-.7.54-.92.92-.22.38-.34.81-.34 1.25v10.02c0 .44.12.87.34 1.25.22.38.54.7.92.92l8.77 5.01Z"
            stroke="#3D5507"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          </svg>
        </span>
      )}
    </div>
  );
}

export function HeroCard({
  title = "La firmaene konkurrere om deg",
  body = "Vi kobler deg med 3 håndplukkede, kvalitetssjekkede byråer i ditt område.",
  href = "/wizard",
  cta = "Få 3 tilbud gratis",
  endVisual,
}: {
  /** Send null når ikonraden allerede sier hva kortet gjelder. */
  title?: string | null;
  body?: string;
  href?: string;
  cta?: string;
  /** Erstatter esken til høyre i ikonraden, f.eks. med et byrås logo. */
  endVisual?: React.ReactNode;
}) {
  return (
    <div className="mx-auto w-full max-w-[400px] rounded-[14px] bg-surface-soft p-6 lg:p-7 shadow-[0_1px_2px_rgba(0,0,0,0.03),0_12px_32px_-16px_rgba(0,0,0,0.10)] ring-1 ring-black/[0.04]">
      <HeroIcons endVisual={endVisual} />
      {title ? (
        <h2 className="mt-7 text-center text-xl font-medium tracking-tight text-ink lg:text-2xl">
          {title}
        </h2>
      ) : null}
      <p
        className={cn(
          "text-center text-sm leading-relaxed text-ink-muted",
          title ? "mt-3" : "mt-7",
        )}
      >
        {body}
      </p>
      <Link
        href={href}
        className="mt-7 inline-flex w-full items-center justify-center gap-2 rounded-full bg-brand px-6 py-4 text-center text-base font-medium leading-snug text-brand-ink transition-colors hover:bg-brand/90"
      >
        {cta}
        <ArrowRight className="h-4 w-4" />
      </Link>
    </div>
  );
}
