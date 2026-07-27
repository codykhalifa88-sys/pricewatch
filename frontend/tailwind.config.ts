import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        ink: {
          50: "#f7f7f8",
          100: "#eeeef0",
          200: "#d7d7dc",
          300: "#b3b3bc",
          400: "#8a8a97",
          500: "#6b6b78",
          600: "#54545f",
          700: "#43434b",
          800: "#2b2b31",
          900: "#18181c",
          950: "#0b0b0e",
        },
        brand: {
          50: "#ecfdf5",
          100: "#d1fae5",
          200: "#a7f3d0",
          300: "#6ee7b7",
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
          800: "#065f46",
          900: "#064e3b",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(11,11,14,0.04), 0 8px 24px -8px rgba(11,11,14,0.12)",
      },
    },
  },
  plugins: [],
};
export default config;
