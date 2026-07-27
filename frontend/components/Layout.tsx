import { ReactNode } from "react";
import Nav from "./Nav";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <Nav />
      <main className="flex-1">{children}</main>
      <footer className="border-t border-ink-100 py-10 text-sm text-ink-400">
        <div className="container-page flex flex-col items-center justify-between gap-4 sm:flex-row">
          <p>&copy; {new Date().getFullYear()} PriceWatch. Track any price, never overpay again.</p>
          <p className="text-ink-300">Built for a portfolio demo — Stripe test mode, no real charges.</p>
        </div>
      </footer>
    </div>
  );
}
