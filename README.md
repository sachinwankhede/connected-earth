# Connected Earth

A map of ecosystems and who eats whom. Static site, built by `npm run build` (the built files are not committed); visit https://sachinwankhede.github.io/connected-earth/ (published with GitHub Pages).

## Local browser tests

Install the locked Node dependencies and Playwright's matching Chromium once:

```sh
npm ci
npx playwright install chromium
```

Build the site before running browser tests, which use the generated files:

```sh
npm run build
node --test tests/photohold.test.mjs
```

Run the full browser suite with `npm test`. If using a system Chromium instead of Playwright's managed browser, set `CHROMIUM_PATH` to its executable path when running the tests.
