const stats = [
  { value: "100%", label: "Gratis og uforpliktende" },
  { value: "1 min", label: "Å fylle ut skjema" },
  { value: "5 000+", label: "Fornøyde kunder" },
  { value: "4.8/5", label: "Gjennomsnittlig vurdering" },
];

export function Stats({ compact = false }: { compact?: boolean }) {
  if (compact) {
    return (
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 sm:gap-3">
        {stats.map((s) => (
          <div
            key={s.label}
            className="flex flex-col items-center justify-center rounded-[14px] bg-surface-soft/85 px-3 py-4 text-center ring-1 ring-line/70 backdrop-blur-md sm:px-4 sm:py-5"
          >
            <p className="text-xl font-medium leading-none tracking-tight text-ink sm:text-2xl lg:text-3xl">
              {s.value}
            </p>
            <p className="mt-2 text-[11px] leading-tight text-ink-muted sm:text-xs">
              {s.label}
            </p>
          </div>
        ))}
      </div>
    );
  }

  return (
    <section className="px-6 py-20 sm:px-10 sm:py-28 lg:py-40">
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
