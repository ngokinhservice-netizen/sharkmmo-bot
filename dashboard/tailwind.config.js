/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        shark: {
          navy: "#07111F",
          bg: "#0B1220",
          card: "#0F1A2E",
          cardHover: "#16233B",
          border: "#1E2D4A",
          blue: "#00B8FF",
          cyan: "#00E5FF",
          text: "#F8FAFC",
          muted: "#94A3B8",
          dark: "#050B14"
        }
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        'glow-cyan': '0 0 25px -5px rgba(0, 229, 255, 0.25)',
        'glow-blue': '0 0 25px -5px rgba(0, 184, 255, 0.25)',
      }
    },
  },
  plugins: [],
}
