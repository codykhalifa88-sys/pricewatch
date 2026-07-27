import { useEffect, useState } from "react";
import Head from "next/head";
import { api } from "@/lib/api";

type DiscountCode = {
  id: number;
  store: string;
  code: string;
  description: string | null;
  discount_percent: number | null;
  expires_at: string | null;
  is_verified: boolean;
};

export default function DiscountCodes() {
  const [codes, setCodes] = useState<DiscountCode[]>([]);
  const [stores, setStores] = useState<string[]>([]);
  const [storeFilter, setStoreFilter] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    api<string[]>("/discount-codes/stores").then(setStores);
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    if (storeFilter) params.set("store", storeFilter);
    if (search) params.set("search", search);
    api<DiscountCode[]>(`/discount-codes?${params.toString()}`).then(setCodes);
  }, [storeFilter, search]);

  return (
    <>
      <Head>
        <title>Discount Codes — PriceWatch</title>
      </Head>
      <div className="container-page py-12">
        <h1 className="text-2xl font-bold text-ink-900">Discount codes</h1>
        <p className="mt-1 text-sm text-ink-500">
          Aggregated daily from real retailer coupon pages.
        </p>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <input
            placeholder="Search descriptions..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 rounded-lg border border-ink-200 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
          />
          <select
            value={storeFilter}
            onChange={(e) => setStoreFilter(e.target.value)}
            className="rounded-lg border border-ink-200 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
          >
            <option value="">All stores</option>
            {stores.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        <div className="mt-8 overflow-x-auto rounded-2xl border border-ink-100 shadow-card">
          <table className="w-full text-sm">
            <thead className="bg-ink-50 text-left text-xs uppercase tracking-wide text-ink-500">
              <tr>
                <th className="px-4 py-3">Store</th>
                <th className="px-4 py-3">Offer</th>
                <th className="px-4 py-3">Code</th>
                <th className="px-4 py-3">Discount</th>
                <th className="px-4 py-3">Expires</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-100">
              {codes.map((c) => (
                <tr key={c.id}>
                  <td className="px-4 py-3 font-medium text-ink-900">{c.store}</td>
                  <td className="max-w-md px-4 py-3 text-ink-600">{c.description}</td>
                  <td className="px-4 py-3">
                    <code className="rounded bg-ink-100 px-2 py-0.5 text-xs font-semibold text-ink-800">
                      {c.code}
                    </code>
                  </td>
                  <td className="px-4 py-3 text-brand-700">
                    {c.discount_percent ? `${c.discount_percent}%` : "—"}
                  </td>
                  <td className="px-4 py-3 text-ink-500">{c.expires_at || "—"}</td>
                </tr>
              ))}
              {codes.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-ink-400">
                    No discount codes match your filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <p className="mt-4 text-xs text-ink-400">
          &quot;AUTOMATIC&quot; means the discount applies automatically via the link, no code needed.
          &quot;SEE SITE&quot; means the store reveals the code on their page — we link real, scraped
          offers, not fabricated code strings.
        </p>
      </div>
    </>
  );
}
