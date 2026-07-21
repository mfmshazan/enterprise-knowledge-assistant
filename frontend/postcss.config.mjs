/** Tailwind CSS v4 is wired in through its dedicated PostCSS plugin.
 *  v4 is CSS-first: theme/config lives in globals.css, not a JS config file. */
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
