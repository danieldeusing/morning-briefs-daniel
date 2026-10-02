# Contributing

This is a personal newsletter, generated every morning. Reports of wrong facts,
broken pages and fixes to the site are welcome.

## Reporting

- **A wrong fact in a brief:** open an issue with the date, the language, the
  category and the sentence, and a source that shows the correct fact.
- **A broken page:** open an issue with the URL, the browser and a screenshot.

## Changing the code

`main` cannot be force-pushed or deleted. The static site lives in `public/`, the
editorial specs in `docs/`. The generation task itself runs outside this
repository (see the README), so a clone can change the site and the specs but
cannot produce a brief.

1. Fork the repository and create a branch.
2. Make the change. Keep it small and focused on one thing.
3. Open `public/index.html` in a browser and check the pages you touched.
4. Open the pull request and describe what changed and why.

By contributing you agree that your work is published under the
[MIT License](LICENSE).
