/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#333F32',
        secondary: '#333F32',
        accent: '#526349',
        surface: '#FFFFFF',
        'surface-container-lowest': '#FFFFFF',
        'surface-container-low': '#F5F5EF',
        'surface-container-highest': '#E8EAE1',
        'surface-variant': '#E1E2DB',
        'primary-container': '#242723',
        'primary-fixed': '#EFF2E9',
        'secondary-container': '#EFF2E9',
        'on-background': '#242723',
        'on-surface': '#242723',
        'on-surface-variant': '#6E716A',
        'on-primary-container': '#6E716A',
        'on-secondary': '#FFFFFF',
        'on-error': '#FFFFFF',
        'on-tertiary-container': '#526349',
        'tertiary-fixed': '#EFF2E9',
        'tertiary-fixed-dim': '#C3CEB0',
        outline: '#969D8C',
        'outline-variant': '#E1E2DB',
        neutral: '#242723', // Gray-800
        'base-100': '#FFFFFF',
        'base-200': '#FAF9F6', // Gray-100
        'base-300': '#E1E2DB', // Gray-200
      },
      fontFamily: {
        sans: ['Inter', 'PingFang SC', 'Microsoft YaHei', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
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
    darkTheme: 'light',
    themes: [
      {
        light: {
          ...require("daisyui/src/theming/themes")["light"],
          primary: "#333F32",
          secondary: "#333F32",
          accent: "#526349",
          "base-100": "#ffffff",
          "base-200": "#faf9f6",
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
