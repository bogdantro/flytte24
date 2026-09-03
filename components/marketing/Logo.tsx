import { cn } from "@/lib/utils";

export function Logo({
  className,
  tone = "ink",
}: {
  className?: string;
  tone?: "ink" | "brand-ink";
}) {
  const isOnDark = tone === "brand-ink";
  const stroke = isOnDark ? "#F4F1EA" : "#232323";
  const text = isOnDark ? "text-brand-ink" : "text-ink";
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <svg
        width="22"
        height="22"
        viewBox="0 0 27 27"
        fill="none"
        aria-hidden="true"
        className="shrink-0"
      >
        <circle cx="13.5" cy="13.5" r="11.625" stroke={stroke} strokeWidth="3.75" />
        <path
          d="M16.5 1.875C12.7075 5.23556 10.5 9.26144 10.5 13.5887C10.5 17.8401 12.6307 21.8006 16.3019 25.125"
          stroke={stroke}
          strokeWidth="3.75"
        />
      </svg>
      <span className={cn("text-lg font-bold tracking-tight", text)}>
        Kobly
      </span>
    </span>
  );
}
