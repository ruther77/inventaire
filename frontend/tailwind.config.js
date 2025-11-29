/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Inter var"', 'Inter', 'system-ui', 'sans-serif'],
        display: ['"Sora"', 'Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        brand: {
          50: '#eef7ff',
          100: '#d9edff',
          200: '#aed6ff',
          300: '#7dbdff',
          400: '#479fff',
          500: '#1d83ff',
          600: '#006be5',
          700: '#0056b3',
          800: '#004083',
          900: '#002a55',
        },
        slate: {
          950: '#040714',
        },
      },
      boxShadow: {
        soft: '0 15px 30px rgba(15, 23, 42, 0.12)',
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
};
