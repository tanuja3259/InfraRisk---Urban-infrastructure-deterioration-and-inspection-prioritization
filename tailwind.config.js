/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f1c24",
        slateish: "#243642",
        mist: "#e8eef1",
        fog: "#f4f7f8",
        teal: "#0d7377",
        tealdeep: "#095456",
        amber: "#c27a1a",
        critical: "#b42318",
        high: "#c2410c",
        medium: "#a16207",
        low: "#15803d",
      },
      fontFamily: {
        display: ["Instrument Serif", "Georgia", "serif"],
        sans: ["DM Sans", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        soft: "0 12px 40px rgba(15, 28, 36, 0.08)",
      },
    },
  },
  plugins: [],
};
