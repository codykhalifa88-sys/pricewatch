import { FormEvent, useState } from "react";
import Head from "next/head";
import { api, ApiError } from "@/lib/api";

type ComparisonResult = {
  store: string;
  name: string;
  price: number;
  currency: string;
  product_url: string;
  active_discount_codes: number;
};

export default function Compare() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ComparisonResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(e: FormEvent) {
    e.preventDefault();
    if (query.trim().length < 2) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api<ComparisonResult[]>(`/search?q=${encodeURIComponent(query)}`);
      setResults(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  const cheapest = results && results.length > 0 ? results[0] : null;

  return (
    <>
      <Head>
        <title>Compare Prices — PriceWatch</title>
      </Head>
      <div className="container-page py-12">
        <h1 className="text-2xl font-bold text-ink-900">Compare prices across stores</h1>
        <p className="mt-1 max-w-xl text-sm text-ink-500">
          Search once — we query every supported store&apos;s real catalog live and
          show you every match, sorted by price.
        </p>

        <form onSubmit={handleSearch} className="mt-6 flex gap-3">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Try “pikachu” or “light”..."
            className="flex-1 rounded-lg border border-ink-200 px-4 py-2.5 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-ink-900 px-6 py-2.5 text-sm font-semibold text-white hover:bg-ink-800 disabled:opacity-50"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </form>

        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

        {results && (
          <div className="mt-8">
            {results.length === 0 ? (
              <p className="text-sm text-ink-500">No live matches found across supported stores.</p>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {results.map((r) => (
                  <a
                    key={`${r.store}-${r.product_url}`}
                    href={r.product_url}
                    target="_blank"
                    rel="noreferrer"
                    className={`rounded-2xl border p-5 shadow-card transition hover:-translate-y-0.5 ${
                      r === cheapest ? "border-brand-400 bg-brand-50" : "border-ink-100 bg-white"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium uppercase tracking-wide text-ink-400">
                        {r.store}
                      </span>
                      {r === cheapest && (
                        <span className="rounded-full bg-brand-600 px-2 py-0.5 text-[10px] font-bold uppercase text-white">
                          Best price
                        </span>
                      )}
                    </div>
                    <h3 className="mt-2 text-sm font-semibold text-ink-900">{r.name}</h3>
                    <p className="mt-3 text-xl font-bold text-ink-900">
                      £{r.price.toFixed(2)}
                    </p>
                    {r.active_discount_codes > 0 ? (
                      <p className="mt-1 text-xs font-medium text-brand-700">
                        {r.active_discount_codes} discount code{r.active_discount_codes > 1 ? "s" : ""} available
                      </p>
                    ) : (
                      <p className="mt-1 text-xs text-ink-400">No active discount codes for this store</p>
                    )}
                  </a>
                ))}
              </div>
            )}
          </div>
        )}

        <p className="mt-10 text-xs text-ink-400">
          Comparison currently covers our two demo stores (books.toscrape.com,
          scrapeme.live) — real, live catalogs, not sample data. A production
          version would add official retailer partner APIs to widen coverage.
        </p>
      </div>
    </>
  );
}
