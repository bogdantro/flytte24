import { Star } from "lucide-react";
import { cn } from "@/lib/utils";

export function Stars({
  rating,
  className,
  size = "sm",
}: {
  rating: number;
  className?: string;
  size?: "sm" | "md";
}) {
  const rounded = Math.round(rating);
  return (
    <span
      className={cn("inline-flex items-center gap-0.5", className)}
      aria-label={`${rating.toFixed(1).replace(".", ",")} av 5 stjerner`}
    >
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          aria-hidden
          className={cn(
            size === "sm" ? "h-3.5 w-3.5" : "h-4 w-4",
            i <= rounded ? "fill-ink text-ink" : "fill-none text-ink/25",
          )}
        />
      ))}
    </span>
  );
}
