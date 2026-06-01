/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#ffffff",
        foreground: "#1e293b", // slate-800
        primary: "#f59e0b", // amber-500
        healthy: "#10b981", // emerald-500
        danger: "#f43f5e", // rose-500
        muted: "#64748b", // slate-500
        surface: "rgba(255, 255, 255, 0.6)",
      },
      backgroundImage: {
        'geometric-pattern': "url('/pattern.svg')",
      }
    },
  },
  plugins: [],
};
