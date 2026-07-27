import Head from "next/head";
import Link from "next/link";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";

const TIERS = [
  {
    name: "Free",
    price: "£0",
    period: "forever",
    features: ["Track up to 3 items", "Daily price checks", "Email alerts", "Discount code directory"],
    cta: "Get started free",
  },
  {
    name: "Pro",
    price: "£5",
    period: "/month",
    features: [
      "Unlimited tracked items",
      "Hourly price checks",
      "Email + Telegram alerts",
      "Discount code directory",
      "Priority support",
    ],
    cta: "Upgrade to Pro",
    highlight: true,
  },
];

export default function Pricing() {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleUpgrade() {
    setError(null);
    setLoading(true);
    try {
      const res = await api<{ checkout_url: string }>("/billing/create-checkout-session", {
        method: "POST",
      });
      window.location.href = res.checkout_url;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start checkout — are you logged in?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Head>
        <title>Pricing — PriceWatch</title>
      </Head>
      <div className="container-page py-16">
        <div className="mx-auto max-w-xl text-center">
          <h1 className="text-3xl font-bold text-ink-900">Simple, honest pricing</h1>
          <p className="mt-2 text-ink-500">Start free. Upgrade when you need faster checks and unlimited items.</p>
        </div>

        {error && <p className="mt-6 text-center text-sm text-red-600">{error}</p>}

        <div className="mx-auto mt-12 grid max-w-3xl gap-6 sm:grid-cols-2">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={`rounded-2xl border p-8 shadow-card ${
                tier.highlight ? "border-brand-500 bg-ink-950 text-white" : "border-ink-100 bg-white"
              }`}
            >
              <h2 className={`text-sm font-semibold uppercase tracking-wide ${tier.highlight ? "text-brand-400" : "text-ink-500"}`}>
                {tier.name}
              </h2>
              <p className="mt-2 flex items-baseline gap-1">
                <span className="text-4xl font-bold">{tier.price}</span>
                <span className={tier.highlight ? "text-ink-300" : "text-ink-400"}>{tier.period}</span>
              </p>
              <ul className="mt-6 flex flex-col gap-3 text-sm">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-center gap-2">
                    <span className={tier.highlight ? "text-brand-400" : "text-brand-600"}>✓</span>
                    {f}
                  </li>
                ))}
              </ul>
              {tier.highlight ? (
                <button
                  onClick={handleUpgrade}
                  disabled={loading}
                  className="mt-8 w-full rounded-lg bg-brand-500 px-4 py-2.5 text-sm font-semibold text-ink-950 hover:bg-brand-400 disabled:opacity-50"
                >
                  {loading ? "Redirecting..." : tier.cta}
                </button>
              ) : (
                <Link
                  href="/signup"
                  className="mt-8 block w-full rounded-lg border border-ink-200 px-4 py-2.5 text-center text-sm font-semibold text-ink-700 hover:bg-ink-50"
                >
                  {tier.cta}
                </Link>
              )}
            </div>
          ))}
        </div>
        <p className="mt-8 text-center text-xs text-ink-400">
          Stripe test mode — checkout uses Stripe&apos;s official test card, no real charge.
        </p>
      </div>
    </>
  );
}
