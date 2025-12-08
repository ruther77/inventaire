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
          25: '#f5faff',
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
          950: '#001a36',
        },
        slate: {
          950: '#040714',
        },
      },
      boxShadow: {
        soft: '0 15px 30px rgba(15, 23, 42, 0.12)',
        'soft-sm': '0 8px 16px rgba(15, 23, 42, 0.08)',
        'soft-lg': '0 20px 40px rgba(15, 23, 42, 0.15)',
        'inner-soft': 'inset 0 2px 4px rgba(15, 23, 42, 0.06)',
        glow: '0 0 20px rgba(29, 131, 255, 0.3)',
        'glow-lg': '0 0 40px rgba(29, 131, 255, 0.4)',
      },
      borderRadius: {
        '4xl': '2rem',
      },
      animation: {
        'fade-in': 'fade-in 200ms ease-out',
        'fade-out': 'fade-out 150ms ease-in',
        'slide-up': 'slide-up 200ms ease-out',
        'slide-down': 'slide-down 200ms ease-out',
        'scale-in': 'scale-in 200ms ease-out',
        'scale-out': 'scale-out 150ms ease-in',
        shimmer: 'shimmer 1.5s ease-in-out infinite',
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'fade-out': {
          from: { opacity: '1' },
          to: { opacity: '0' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-down': {
          from: { opacity: '0', transform: 'translateY(-8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'scale-in': {
          from: { opacity: '0', transform: 'scale(0.95)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
        'scale-out': {
          from: { opacity: '1', transform: 'scale(1)' },
          to: { opacity: '0', transform: 'scale(0.95)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' },
        },
      },
      transitionTimingFunction: {
        spring: 'cubic-bezier(0.16, 1, 0.3, 1)',
        bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      },
      transitionDuration: {
        0: '0ms',
        25: '25ms',
        75: '75ms',
        250: '250ms',
        400: '400ms',
      },
      zIndex: {
        60: '60',
        70: '70',
        80: '80',
        90: '90',
        100: '100',
      },
      spacing: {
        '4.5': '1.125rem',
        '5.5': '1.375rem',
        '18': '4.5rem',
        '22': '5.5rem',
      },
      minHeight: {
        touch: '44px',
        'touch-sm': '36px',
        'touch-lg': '48px',
      },
      minWidth: {
        touch: '44px',
        'touch-sm': '36px',
        'touch-lg': '48px',
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
};
