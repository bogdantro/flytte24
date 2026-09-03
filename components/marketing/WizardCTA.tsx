import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

export function WizardCTA({ className }: { className?: string }) {
  return (
    <aside
      className={cn(
        "rounded-[14px] bg-brand px-7 py-8 text-brand-ink sm:px-10 sm:py-10",
        className,
      )}
    >
      <div className="flex flex-col items-start gap-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xl font-semibold sm:text-2xl">Skal du flytte?</p>
          <p className="mt-2 max-w-md text-sm text-brand-ink/70 sm:text-base">
            Få 3 tilbud gratis fra kvalitetssjekkede flyttebyråer. Uforpliktende
            og ferdig på under to minutter.
          </p>
        </div>
        <Link
          href="/wizard"
          className="inline-flex shrink-0 items-center gap-2 rounded-full bg-brand-ink px-6 py-3.5 text-sm font-medium text-ink transition-colors hover:bg-brand-ink/90"
        >
          Få 3 tilbud gratis
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </aside>
  );
}
