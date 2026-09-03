const stats = [
  { value: "5 000+", label: "Forespørsler i året" },
  { value: "70 %", label: "Booking-rate på leads" },
  { value: "0 kr", label: "Oppstartskostnad" },
  { value: "24 t", label: "Snitt responstid" },
];

export function PartnerStats() {
  return (
    <section className="px-6 py-16 sm:px-10 sm:py-20 lg:py-24">
      <div className="mx-auto max-w-6xl">
        <div className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-4">
          {stats.map((s) => (
            <div
              key={s.label}
              className="flex flex-col items-center justify-center rounded-[14px] bg-surface-soft px-5 py-8 text-center ring-1 ring-line sm:px-6 sm:py-10 lg:px-7 lg:py-12"
            >
              <p className="text-4xl font-bold leading-none tracking-tight text-ink sm:text-5xl">
                {s.value}
              </p>
              <p className="mt-4 text-sm text-ink-muted">{s.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
