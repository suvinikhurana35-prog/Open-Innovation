import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f4ff',
          100: '#dbe4ff',
          200: '#bac8ff',
          300: '#91a7ff',
          400: '#748ffc',
          500: '#5c7cfa',
          600: '#4c6ef5',
          700: '#4263eb',
          800: '#3b5bdb',
          900: '#364fc7',
        },
        safron: {
          50: '#fff9f0',
          100: '#fff0db',
          200: '#ffe0b8',
          300: '#ffc891',
          400: '#ffa94d',
          500: '#ff922b',
          600: '#fd7e14',
          700: '#e67700',
          800: '#cc6600',
          900: '#a65300',
        },
        green: {
          50: '#f0faf0',
          100: '#d4f5d4',
          200: '#a8eba8',
          300: '#75db75',
          400: '#51c851',
          500: '#2f9e44',
          600: '#1e8b3a',
          700: '#157a32',
          800: '#0f6b2b',
          900: '#0a5c23',
        },
        alert: {
          green: '#2f9e44',
          yellow: '#f59f00',
          red: '#e03131',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        hindi: ['Noto Sans Devanagari', 'sans-serif'],
      },
      fontSize: {
        'hero': ['2.5rem', { lineHeight: '1.2' }],
        'huge': ['3.5rem', { lineHeight: '1.1' }],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}

export default config
