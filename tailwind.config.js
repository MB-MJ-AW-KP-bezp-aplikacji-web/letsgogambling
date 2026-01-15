/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './casino/**/templates/**/*.html',
    './static/js/**/*.js'
  ],
  theme: {
    extend: {
      colors: {
        neon: {
          green: '#39ff14',
          gold: '#ffd700',
          purple: '#9333ea',
          pink: '#ff00ff',
        }
      },
      boxShadow: {
        'neon-green': '0 0 5px #39ff14, 0 0 20px #39ff14',
        'neon-gold': '0 0 5px #ffd700, 0 0 20px #ffd700',
        'neon-purple': '0 0 5px #9333ea, 0 0 20px #9333ea',
      }
    }
  },
  plugins: [],
}
