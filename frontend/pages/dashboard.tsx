import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import Link from "next/link";
import { api, ApiError, getToken } from "@/lib/api";
import PriceChart, { PricePoint } from "@/components/PriceChart";

type TrackedItem = {
  id: number;
  product_url: string;
  product_name: string | null;
  store: string;
  target_price: number;
  current_price: number | null;
  is_active: boolean;
  created_at: string;
};

type CurrentUser = {
  id: number;
  email: string;
  subscription_tier: string;
};

export default function Dashboard() {
  const router = useRouter();
  const [items, setItems] = useState<TrackedItem[] | null>(null);
  const [stores, setStores] = useState<string[]>([]);
  const [histories, setHistories] = useState<Record<number, PricePoint[]>>({});
  const [error, setError] = useState<string | null>(null);

  const [user, setUser] = useState<CurrentUser | null>(null);
  const [portalLoading, setPortalLoading] = useState(false);
  const [portalError, setPortalError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [productUrl, setProductUrl] = useState("");
  const [store, setStore] = useState("");
  const [targetPrice, setTargetPrice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    loadItems();
    api<string[]>("/items/supported-stores").then((s) => {
      setStores(s);
      if (s.length) setStore(s[0]);
    });
    api<CurrentUser>("/auth/me").then(setUser);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- run once on mount only
  }, []);

  async function handleManageSubscription() {
    setPortalError(null);
    setPortalLoading(true);
    try {
      const res = await api<{ portal_url: string }>("/billing/create-portal-session", { method: "POST" });
      window.location.href = res.portal_url;
    } catch (err) {
      setPortalError(err instanceof ApiError ? err.message : "Could not open the billing portal");
    } finally {
      setPortalLoading(false);
    }
  }

  async function loadItems() {
    try {
      const data = await api<TrackedItem[]>("/items");
      setItems(data);
      data.forEach((item) => {
        api<PricePoint[]>(`/items/${item.id}/history`).then((h) =>
          setHistories((prev) => ({ ...prev, [item.id]: h }))
        );
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load items");
    }
  }

  async function handleAddItem(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      await api("/items", {
        method: "POST",
        body: JSON.stringify({ product_url: productUrl, store, target_price: parseFloat(targetPrice) }),
      });
      setProductUrl("");
      setTargetPrice("");
      setShowForm(false);
      loadItems();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to add item");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    await api(`/items/${id}`, { method: "DELETE" });
    loadItems();
  }

  return (
    <>
      <Head>
        <title>Dashboard — PriceWatch</title>
      </Head>
      <div className="container-page py-12">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-ink-900">Your tracked items</h1>
            <p className="mt-1 text-sm text-ink-500">
              Current vs. target price, and price history for each item.
            </p>
          </div>
          <button
            onClick={() => setShowForm((s) => !s)}
            className="rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700"
          >
            {showForm ? "Cancel" : "+ Add item"}
          </button>
        </div>

        {user && (
          <div className="mt-4 flex items-center gap-3 text-sm">
            <span
              className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                user.subscription_tier === "pro" ? "bg-brand-100 text-brand-700" : "bg-ink-100 text-ink-600"
              }`}
            >
              {user.subscription_tier === "pro" ? "Pro" : "Free tier"}
            </span>
            {user.subscription_tier === "pro" ? (
              <button
                onClick={handleManageSubscription}
                disabled={portalLoading}
                className="text-sm font-medium text-brand-600 hover:text-brand-700 disabled:opacity-50"
              >
                {portalLoading ? "Opening…" : "Manage subscription"}
              </button>
            ) : (
              <Link href="/pricing" className="text-sm font-medium text-brand-600 hover:text-brand-700">
                Upgrade to Pro
              </Link>
            )}
            {portalError && <span className="text-sm text-red-600">{portalError}</span>}
          </div>
        )}

        {showForm && (
          <form
            onSubmit={handleAddItem}
            className="mt-6 flex flex-col gap-4 rounded-2xl border border-ink-100 bg-white p-6 shadow-card sm:flex-row sm:items-end"
          >
            <label className="flex flex-1 flex-col gap-1 text-sm font-medium text-ink-700">
              Product URL
              <input
                required
                placeholder="https://scrapeme.live/shop/Pikachu/"
                value={productUrl}
                onChange={(e) => setProductUrl(e.target.value)}
                className="rounded-lg border border-ink-200 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
              />
            </label>
            <label className="flex flex-col gap-1 text-sm font-medium text-ink-700">
              Store
              <select
                value={store}
                onChange={(e) => setStore(e.target.value)}
                className="rounded-lg border border-ink-200 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
              >
                {stores.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex w-32 flex-col gap-1 text-sm font-medium text-ink-700">
              Target price
              <input
                required
                type="number"
                step="0.01"
                min="0.01"
                value={targetPrice}
                onChange={(e) => setTargetPrice(e.target.value)}
                className="rounded-lg border border-ink-200 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
              />
            </label>
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-ink-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-ink-800 disabled:opacity-50"
            >
              {submitting ? "Adding..." : "Track it"}
            </button>
            {formError && <p className="text-sm text-red-600 sm:basis-full">{formError}</p>}
          </form>
        )}

        {error && <p className="mt-6 text-sm text-red-600">{error}</p>}

        <div className="mt-8 grid gap-6 sm:grid-cols-2">
          {items?.length === 0 && (
            <p className="text-sm text-ink-500">
              Nothing tracked yet. Add your first item above.
            </p>
          )}
          {items?.map((item) => {
            const belowTarget = item.current_price !== null && item.current_price <= item.target_price;
            return (
              <div key={item.id} className="rounded-2xl border border-ink-100 bg-white p-6 shadow-card">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wide text-ink-400">{item.store}</p>
                    <h3 className="mt-0.5 text-sm font-semibold text-ink-900">
                      {item.product_name || item.product_url}
                    </h3>
                  </div>
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="text-xs font-medium text-ink-400 hover:text-red-600"
                  >
                    Remove
                  </button>
                </div>

                <div className="mt-4 flex items-baseline gap-4">
                  <div>
                    <p className="text-xs text-ink-400">Current</p>
                    <p className={`text-lg font-bold ${belowTarget ? "text-brand-600" : "text-ink-900"}`}>
                      {item.current_price !== null ? `£${item.current_price.toFixed(2)}` : "—"}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-ink-400">Target</p>
                    <p className="text-sm font-medium text-ink-600">£{item.target_price.toFixed(2)}</p>
                  </div>
                  {belowTarget && (
                    <span className="ml-auto rounded-full bg-brand-100 px-2.5 py-1 text-xs font-semibold text-brand-700">
                      Target hit!
                    </span>
                  )}
                </div>

                <div className="mt-4">
                  <PriceChart data={histories[item.id] || []} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}
