import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { CITY_LIST } from "@/lib/cities";

export function Cities() {
  return (
    <section className="px-6 py-20 sm:px-10 sm:py-28 lg:py-40">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-col text-left">
          <h2 className="text-3xl font-semibold leading-[1.1] text-ink sm:text-[42px]">
            Flytter du i en av disse byene?
          </h2>
          <p className="mt-4 max-w-xl text-base text-ink-muted sm:text-lg">
            Vi har kvalitetssjekkede byråer som tar oppdrag i hele landet. Velg
            byen din for å komme raskere i gang.
          </p>
        </div>
        <ul className="mt-10 grid gap-4 sm:mt-14 md:grid-cols-3 lg:grid-cols-5">
          {CITY_LIST.map((city) => (
            <li key={city.slug}>
              <Link
                href={`/${city.slug}`}
                className="group flex items-center justify-between rounded-[14px] bg-surface-soft px-6 py-5 ring-1 ring-line transition-colors hover:bg-surface-soft/70"
              >
                <span className="text-lg font-medium text-ink">
                  {city.name}
                </span>
                <ArrowUpRight className="h-4 w-4 text-ink/40 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-ink" />
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
