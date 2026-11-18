import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#1C2230',
        muted: '#5E6676',
        rule: '#E3E5EA',
        shelf: '#F4F5F7',
        pine: { DEFAULT: '#145C57', dark: '#0E4642', soft: '#E3EFEE' },
        // Highlighter yellow: used only for cited passages
        mark: { DEFAULT: '#FFE58A', edge: '#E8C547' },
        alert: '#B42318',
      },
      fontFamily: {
        sans: ['var(--font-ui)', 'system-ui', 'sans-serif'],
        serif: ['var(--font-read)', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
};

export default config;
