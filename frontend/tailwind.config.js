/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [ "./src/**/*.{js,ts,jsx,tsx,mdx}" ],
  theme: {
    extend: {
      colors: {
        'background': '#F8F9FA',
        'text-primary': '#212529',
        'accent': {
          DEFAULT: '#00796B', // Teal
          'hover': '#00695C',
          'text': '#FFFFFF',
        },
        'container': '#FFFFFF',
        'border': '#E9ECEF',
        'assistant-bubble': '#F1F3F5',
      },
      boxShadow: {
        'soft': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
      }
    },
  },
  plugins: [ require('@tailwindcss/forms') ],
};
