/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#171717',
        paper: '#faf9f6',
        michelin: '#c8102e',
        brass: '#b68b2f',
      },
      boxShadow: {
        panel: '0 12px 40px rgba(23, 23, 23, 0.08)',
      },
    },
  },
  plugins: [],
};
