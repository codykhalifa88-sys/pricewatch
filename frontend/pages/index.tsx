import Link from "next/link";
import Head from "next/head";

const FEATURES = [
  {
    title: "Track any supported product",
    body: "Paste a product URL, set your target price. We check it on a schedule and record every price we see.",
  },
  {
    title: "Compare prices across stores",
    body: "Search once, see real listings from every supported store side by side, sorted by price.",
  },
  {
    title: "Get notified the moment it drops",
    body: "Email and Telegram alerts fire as soon as a tracked item hits your target — not once a week.",
  },
  {
    title: "Real discount codes, aggregated daily",
    body: "A searchable directory of active coupon codes, refreshed from real retailer coupon pages every day.",
  },
];

export default function Home() {
  return (
    <>
      <Head>
        <title>PriceWatch — Track any price, never overpay again</title>
        <meta
          name="description"
          content="Track product prices, compare them across stores, and get notified the moment a price drops below your target."
        />
      </Head>

      <section className="border-b border-ink-100 bg-gradient-to-b from-brand-50/60 to-white">
        <div className="container-page flex flex-col items-center gap-8 py-24 text-center">
          <span className="rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-brand-700">
            Now tracking real, live prices
          </span>
          <h1 className="max-w-3xl text-balance text-5xl font-bold tracking-tight text-ink-900 sm:text-6xl">
            Track any price.
            <br />
            <span className="text-brand-600">Never overpay again.</span>
          </h1>
          <p className="max-w-xl text-balance text-lg text-ink-500">
            Set a target price, and PriceWatch checks it for you — on a schedule,
            forever. The moment it drops, you&apos;ll know. Compare prices across
            stores and stack real discount codes on top.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Link
              href="/signup"
              className="rounded-lg bg-ink-900 px-6 py-3 text-sm font-semibold text-white shadow-card hover:bg-ink-800"
            >
              Start tracking — it&apos;s free
            </Link>
            <Link
              href="/compare"
              className="rounded-lg border border-ink-200 bg-white px-6 py-3 text-sm font-semibold text-ink-700 hover:bg-ink-50"
            >
              Try the price comparison
            </Link>
          </div>
          <p className="text-xs text-ink-400">
            Free tier: 3 tracked items, daily checks. No credit card required.
          </p>
        </div>
      </section>

      <section className="container-page py-20">
        <div className="grid gap-6 sm:grid-cols-2">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="rounded-2xl border border-ink-100 bg-white p-6 shadow-card"
            >
              <h3 className="text-base font-semibold text-ink-900">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-500">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-ink-100 bg-ink-950 py-20 text-white">
        <div className="container-page flex flex-col items-center gap-6 text-center">
          <h2 className="text-3xl font-bold tracking-tight">
            Set your price. We&apos;ll watch it.
          </h2>
          <p className="max-w-md text-ink-300">
            Free to start. Upgrade to Pro for unlimited items, hourly checks,
            and priority alerts.
          </p>
          <Link
            href="/signup"
            className="rounded-lg bg-brand-500 px-6 py-3 text-sm font-semibold text-ink-950 hover:bg-brand-400"
          >
            Create your free account
          </Link>
        </div>
      </section>
    </>
  );
}
