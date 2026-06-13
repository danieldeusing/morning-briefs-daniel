/* responsive-spacing-check — measurement probe.
 *
 * Paste this whole IIFE into mcp__Claude_Preview__preview_eval's `expression`
 * AFTER navigating the preview to a category page on :8090. It measures every
 * element matching SELECTOR and reports the box metrics that matter for spacing
 * / sizing / overflow review, plus a page-level horizontal-overflow flag.
 *
 * Set SELECTOR before pasting (or wrap-and-call with your own). Returns a JSON
 * object; collect one per (breakpoint × category) and feed the array to
 * tabulate.py.
 *
 * Why these fields: spacing review needs the GAP between siblings (marginTop of
 * each element after the first), the element's own box (width/height), its
 * font-size (the #30 timeline-vs-bullets case), and whether the page overflows
 * horizontally (the mobile #41 case). Computed values, not source — that's what
 * the user actually sees.
 */
(() => {
  const SELECTOR = "REPLACE_ME";          // e.g. ".col > section.news-item"
  const els = [...document.querySelectorAll(SELECTOR)];
  const round = (n) => Math.round(n * 100) / 100;
  const pxnum = (s) => round(parseFloat(s) || 0);

  const rows = els.slice(0, 12).map((el, i) => {
    const cs = getComputedStyle(el);
    const b = el.getBoundingClientRect();
    // Gap to the previous matching sibling's bottom (only meaningful when laid
    // out in normal block flow; for grid tracks this is the row gap proxy).
    let gapToPrev = null;
    if (i > 0) {
      const prev = els[i - 1].getBoundingClientRect();
      gapToPrev = Math.round(b.top - prev.bottom);
    }
    return {
      i,
      w: Math.round(b.width),
      h: Math.round(b.height),
      fontSizePx: pxnum(cs.fontSize),
      marginTop: pxnum(cs.marginTop),
      marginBottom: pxnum(cs.marginBottom),
      gapToPrev,
    };
  });

  return {
    url: location.href,
    port: location.port,
    innerW: window.innerWidth,
    selector: SELECTOR,
    matched: els.length,
    overflowX: document.documentElement.scrollWidth > window.innerWidth
      ? document.documentElement.scrollWidth - window.innerWidth
      : 0,                                 // px of horizontal overflow (0 = none)
    rows,
  };
})()
