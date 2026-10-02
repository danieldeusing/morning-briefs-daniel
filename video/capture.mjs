// Screenshots the live site for the README tour: the dashboard with a brief open and
// the newest English edition of every category the live site's manifest lists.
import { mkdirSync, writeFileSync } from "node:fs";
import { chromium } from "playwright-core";

const SITE = "https://briefs.danieldeusing.de";
const OUT = new URL("./public/shots/", import.meta.url).pathname;
const MAX_H = 2400; // the tour shows the top of each brief: masthead, TL;DR, timeline, first sections

const manifest = await (await fetch(`${SITE}/manifest.json`)).json();
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ channel: "chrome" });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
await page.addInitScript(() => localStorage.setItem("mb-lang", "en"));

const open = async (url) => {
  await page.goto(url, { waitUntil: "networkidle" });
  // The CRT scanlines (~3px lines) turn to moiré once the tour is scaled down, and
  // baked into a scrolling capture they change every pixel of every GIF frame.
  await page.addStyleTag({ content: "html { --scanline-opacity: 0 !important; }" });
  await page.waitForTimeout(1500); // the masthead's one-off rise animation
};

await open(`${SITE}/#economy/latest`);
await page.screenshot({ path: `${OUT}dashboard.png` });

const shots = [];
for (const { id, latest } of manifest.categories) {
  await page.setViewportSize({ width: 1280, height: 720 });
  await open(`${SITE}/${id}/en/${latest}.html`);
  const height = Math.min(MAX_H, await page.evaluate(() => document.documentElement.scrollHeight));
  // A tall viewport rather than fullPage: fixed UI (the read-aloud button) stays at
  // the bottom edge instead of being painted halfway down the capture.
  await page.setViewportSize({ width: 1280, height });
  await page.screenshot({ path: `${OUT}${id}.png` });
  shots.push({ id, date: latest, file: `shots/${id}.png`, height });
}

await browser.close();
writeFileSync(`${OUT}index.json`, JSON.stringify(shots, null, 2) + "\n");
