/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1768C4',
        secondary: '#1768C4',
        accent: '#13867D',
        surface: '#FFFFFF',
        'surface-container-lowest': '#FFFFFF',
        'surface-container-low': '#F5F7FA',
        'surface-container-highest': '#E8EDF4',
        'surface-variant': '#DFE5EC',
        'primary-container': '#203C61',
        'primary-fixed': '#EDF4FF',
        'secondary-container': '#EDF4FF',
        'on-background': '#1D2939',
        'on-surface': '#1D2939',
        'on-surface-variant': '#667085',
        'on-primary-container': '#586577',
        'on-secondary': '#FFFFFF',
        'on-error': '#FFFFFF',
        'on-tertiary-container': '#2A6B66',
        'tertiary-fixed': '#E8F5F2',
        'tertiary-fixed-dim': '#A7CEC7',
        outline: '#8996A8',
        'outline-variant': '#DFE5EC',
        neutral: '#1F2937', // Gray-800
        'base-100': '#FFFFFF',
        'base-200': '#F3F4F6', // Gray-100
        'base-300': '#E5E7EB', // Gray-200
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.8s ease-out forwards',
        'fade-in-down': 'fadeInDown 0.8s ease-out forwards',
        'fade-in': 'fadeIn 1s ease-out forwards',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInDown: {
          '0%': { opacity: '0', transform: 'translateY(-20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
      boxShadow: {
        'glass': '0 4px 30px rgba(0, 0, 0, 0.1)',
        'glow': '0 0 15px rgba(59, 130, 246, 0.5)',
      },
    },
  },
  plugins: [require('daisyui')],
  daisyui: {
    themes: [
      {
        light: {
          ...require("daisyui/src/theming/themes")["light"],
          primary: "#1768C4",
          secondary: "#1768C4",
          accent: "#13867D",
          "base-100": "#ffffff",
          "base-200": "#f3f4f6",
        },
        dark: {
          ...require("daisyui/src/theming/themes")["dark"],
          primary: "#60A5FA",
          secondary: "#34D399",
          accent: "#A78BFA",
          "base-100": "#1f2937",
          "base-200": "#111827",
        },
      },
    ],
  },
}
