import Image from "next/image";
import { Stats } from "./Stats";

const baseTiles = [
  "/images/travis-fish-2qZZu8lWDZo-unsplash.jpg",
  "/images/dina-badamshina-j7vbBmTHmjY-unsplash.jpg",
  "/images/lawrence-krowdeed-2vTqgr6sXsI-unsplash.jpg",
  "/images/R1-09131-0032.JPG",
  "/images/foto__2.jpg",
];

// Duplisér nok ganger til at "halve" tracken er bredere enn viewport,
// slik at translateX(-50%) gir et sømløst loop.
const tiles = Array.from({ length: 4 }, () => baseTiles).flat();

export function ImageStrip() {
  return (
    <section className="pb-20 sm:pb-28 lg:pb-32">
      <div className="marquee-mask overflow-hidden">
        <div className="marquee-track flex gap-4 sm:gap-5">
          {tiles.map((src, i) => (
            <div
              key={i}
              className="relative aspect-[4/5] h-[340px] shrink-0 overflow-hidden rounded-[14px] sm:h-[440px] lg:h-[540px]"
            >
              <Image
                src={src}
                alt=""
                aria-hidden
                fill
                sizes="(min-width: 1024px) 430px, (min-width: 640px) 350px, 270px"
                className="object-cover"
                priority={i < 3}
              />
            </div>
          ))}
        </div>
      </div>
      <div className="mt-10 px-6 sm:mt-14 sm:px-10 lg:mt-16">
        <div className="mx-auto max-w-5xl">
          <Stats compact />
        </div>
      </div>
    </section>
  );
}
