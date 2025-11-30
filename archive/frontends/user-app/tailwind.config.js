/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // SegurifAI Brand Colors
        segurifai: {
          primary: '#1E3A8A',    // Deep Blue
          secondary: '#3B82F6',   // Bright Blue
          accent: '#10B981',      // Green
          dark: '#1F2937',
          light: '#F3F4F6',
        },
        // PAQ Brand Colors
        paq: {
          primary: '#7C3AED',     // Purple
          secondary: '#A855F7',
          accent: '#F59E0B',      // Amber
        },
        // MAWDY Brand Colors
        mawdy: {
          primary: '#DC2626',     // Red
          secondary: '#EF4444',
          accent: '#F97316',      // Orange
          dark: '#991B1B',
        },
      },
    },
  },
  plugins: [],
}
