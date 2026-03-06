/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brandBg: "#0B1220",
        cardBg: "#111B2E",
        cardSoft: "#172338",
        accent: "#20D9D2",
        accentSoft: "#0EA5A3",
      },
      boxShadow: {
        soft: "0 8px 24px rgba(0, 0, 0, 0.28)",
        glow: "0 0 0 1px rgba(32, 217, 210, 0.25), 0 0 22px rgba(32, 217, 210, 0.18)",
      },
      keyframes: {
        pulseDot: {
          "0%, 100%": { transform: "scale(1)", opacity: "0.9" },
          "50%": { transform: "scale(1.4)", opacity: "0.35" },
        },
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        pulseDot: "pulseDot 1.4s ease-in-out infinite",
        fadeInUp: "fadeInUp 0.35s ease-out",
      },
    },
  },
  plugins: [],
};
