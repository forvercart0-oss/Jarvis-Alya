/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        jarvis: {
          cyan: '#00f0ff',
          blue: '#0077ff',
          purple: '#5500ff',
          dark: '#050a14',
          panel: 'rgba(5, 15, 30, 0.85)',
          'panel-strong': 'rgba(5, 15, 30, 0.95)',
        },
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 8s linear infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'scan': 'scan 8s linear infinite',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px #00f0ff, 0 0 20px #00f0ff' },
          '100%': { boxShadow: '0 0 20px #00f0ff, 0 0 40px #00f0ff' },
        },
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
      },
    },
  },
  plugins: [],
}
