import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { clearToken, getToken } from "@/lib/api";

export default function Nav() {
  const router = useRouter();
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    setLoggedIn(!!getToken());
  }, [router.pathname]);

  function logout() {
    clearToken();
    router.push("/");
  }

  return (
    <header className="sticky top-0 z-30 border-b border-ink-100 bg-white/80 backdrop-blur">
      <div className="container-page flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-semibold text-ink-900">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white">
            P
          </span>
          PriceWatch
        </Link>

        <nav className="hidden items-center gap-8 text-sm font-medium text-ink-600 md:flex">
          <Link href="/compare" className="hover:text-ink-900">Compare Prices</Link>
          <Link href="/discount-codes" className="hover:text-ink-900">Discount Codes</Link>
          <Link href="/pricing" className="hover:text-ink-900">Pricing</Link>
        </nav>

        <div className="flex items-center gap-3">
          {loggedIn ? (
            <>
              <Link
                href="/dashboard"
                className="text-sm font-medium text-ink-600 hover:text-ink-900"
              >
                Dashboard
              </Link>
              <button
                onClick={logout}
                className="rounded-lg border border-ink-200 px-3 py-1.5 text-sm font-medium text-ink-700 hover:bg-ink-50"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="text-sm font-medium text-ink-600 hover:text-ink-900"
              >
                Log in
              </Link>
              <Link
                href="/signup"
                className="rounded-lg bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-800"
              >
                Get started
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
