import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { DISTRICTS } from "@/lib/districts";

/**
 * Lenker til alle Oslos bydeler. Brukes på Oslo-siden og nederst på hver
 * bydelsside, så den interne lenkestrukturen henger sammen begge veier.
 */
export function DistrictList({
  currentSlug,
  title = "Vi hjelper deg i hele Oslo",
  intro = "Velg bydelen din for å se hva som er verdt å vite når du skal flytte akkurat der.",
}: {
  currentSlug?: string;
  title?: string;
  intro?: string;
}) {
  const districts = DISTRICTS.filter((d) => d.slug !== currentSlug);

  return (
    <section className="px-6 py-20 sm:px-10 sm:py-28 lg:py-32">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-col text-left">
          <h2 className="text-3xl font-semibold leading-[1.1] text-ink sm:text-[42px]">
            {title}
          </h2>
          <p className="mt-4 max-w-xl text-base text-ink-muted sm:text-lg">
            {intro}
          </p>
        </div>
        <ul className="mt-10 grid gap-3 sm:mt-14 sm:grid-cols-2 lg:grid-cols-3">
          {districts.map((district) => (
            <li key={district.slug}>
              <Link
                href={`/oslo/${district.slug}`}
                className="group flex items-center justify-between gap-3 rounded-[14px] bg-surface-soft px-5 py-4 ring-1 ring-line transition-colors hover:bg-surface-soft/60"
              >
                <span className="text-base font-medium text-ink">
                  {district.name}
                </span>
                <ArrowUpRight className="h-4 w-4 shrink-0 text-ink/30 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-ink" />
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
