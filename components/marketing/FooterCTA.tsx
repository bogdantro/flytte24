import { PostnummerInput } from "./PostnummerInput";

export function FooterCTA() {
  return (
    <section className="px-6 py-20 sm:px-10 sm:py-28 lg:py-40">
      <div className="mx-auto max-w-6xl">
        <div className="mx-auto flex max-w-3xl flex-col items-center text-center">
          <h2 className="text-4xl font-semibold text-ink sm:text-[56px] sm:leading-[1.05]">
            Klar for å flytte?
          </h2>
          <PostnummerInput className="mt-8 sm:mt-10" />
        </div>
      </div>
    </section>
  );
}
