/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        body: ["var(--font-body)", "system-ui", "sans-serif"],
      },
      colors: {
        // warm paper surfaces
        paper: "#FAF6EC",
        cream: "#FFFDF7",
        sand: "#F2EAD7",
        bark: "#EDE3CC",
        // ink / text
        ink: {
          DEFAULT: "#2B2A24",
          soft: "#5C5749",
          faint: "#8A8470",
        },
        line: {
          DEFAULT: "#E6DCC4",
          soft: "#EFE7D5",
          strong: "#D8CBAC",
        },
        // forest = primary (nature, health, growth)
        forest: {
          50: "#EEF4ED",
          100: "#D9E7D7",
          200: "#B2CDAE",
          300: "#7FAE7C",
          400: "#549159",
          500: "#3E8B5C",
          600: "#2C7048",
          700: "#1E5436",
          800: "#163E29",
        },
        // honey = accent (bees)
        honey: {
          50: "#FCF3E1",
          100: "#F8E5BE",
          200: "#F2CD86",
          300: "#EDB857",
          400: "#E8A33D",
          500: "#D98A1F",
          600: "#B86F15",
        },
        // organic signal colors
        moss: "#6E8B5A",
        clay: "#BC4B2E",
        amberwarn: "#C98A1E",
      },
      borderRadius: {
        xl: "0.9rem",
        "2xl": "1.25rem",
        "3xl": "1.75rem",
      },
      boxShadow: {
        soft: "0 1px 2px rgba(60,50,30,0.04), 0 6px 20px -8px rgba(60,50,30,0.12)",
        lift: "0 4px 8px -2px rgba(60,50,30,0.08), 0 18px 40px -12px rgba(60,50,30,0.18)",
        ring: "0 0 0 1px rgba(230,220,196,0.9)",
        inset: "inset 0 1px 0 rgba(255,255,255,0.6)",
      },
      backgroundImage: {
        // soft sage honeycomb watermark
        comb:
          "url(\"data:image/svg+xml,%3Csvg width='48' height='84' viewBox='0 0 48 84' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M24 56L0 42L0 14L24 0L48 14L48 42L24 56L24 84' fill='none' stroke='%232C7048' stroke-opacity='0.08' stroke-width='1.2'/%3E%3Cpath d='M24 0L24 28L0 42L0 70L24 84L48 70L48 42L24 28' fill='none' stroke='%232C7048' stroke-opacity='0.08' stroke-width='1.2'/%3E%3C/svg%3E\")",
        // faint paper grain
        grain:
          "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/%3E%3C/svg%3E\")",
      },
      keyframes: {
        "drift": {
          "0%, 100%": { transform: "translateY(0) rotate(0deg)" },
          "50%": { transform: "translateY(-14px) rotate(4deg)" },
        },
        "drift-slow": {
          "0%, 100%": { transform: "translateY(0) rotate(0deg)" },
          "50%": { transform: "translateY(18px) rotate(-5deg)" },
        },
        "sway": {
          "0%, 100%": { transform: "rotate(-3deg)" },
          "50%": { transform: "rotate(3deg)" },
        },
        "pulse-soft": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        "rise": {
          from: { opacity: "0", transform: "translateY(16px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        drift: "drift 9s ease-in-out infinite",
        "drift-slow": "drift-slow 13s ease-in-out infinite",
        sway: "sway 6s ease-in-out infinite",
        "pulse-soft": "pulse-soft 2.6s ease-in-out infinite",
        rise: "rise 0.7s cubic-bezier(0.22,1,0.36,1) both",
      },
    },
  },
  plugins: [],
};
