import Image from "next/image";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { AGENCIES } from "@/lib/agencies";

export function Trust() {
  return (
    <section className="px-6 py-20 sm:px-10 sm:py-28 lg:py-40">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-col text-left">
          <h2 className="text-3xl font-semibold leading-[1.1] text-balance text-ink sm:text-[42px]">
            Norges smarteste tilbudstjeneste
          </h2>
          <p className="mt-4 max-w-xl text-base text-ink-muted sm:text-lg">
            Kobly flytter ikke selv — vi samler byråene som gjør det best, og
            kobler deg med tre som passer akkurat din flytting.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Link
              href="/wizard"
              className="inline-flex items-center gap-2 rounded-full bg-brand px-5 py-3 text-sm font-medium text-brand-ink transition-colors hover:bg-brand/90"
            >
              Få 3 tilbud gratis
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/byraer"
              className="inline-flex items-center rounded-full px-5 py-3 text-sm font-medium text-ink ring-1 ring-line transition-colors hover:bg-ink/5"
            >
              Møt byråene
            </Link>
          </div>
        </div>
        <div className="mt-12 flex flex-wrap items-center justify-start gap-x-10 gap-y-6 sm:mt-16 sm:gap-x-14">
          {AGENCIES.map((agency) => (
            <Link key={agency.slug} href={`/byraer/${agency.slug}`}>
              <Image
                src={agency.logo}
                alt={agency.name}
                width={400}
                height={140}
                quality={100}
                unoptimized
                className="h-10 w-auto object-contain opacity-80 transition-opacity hover:opacity-100 sm:h-11"
                style={
                  agency.logoBlendMultiply
                    ? { mixBlendMode: "multiply" }
                    : undefined
                }
              />
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
