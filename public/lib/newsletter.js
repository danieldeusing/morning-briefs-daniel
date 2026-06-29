/* Morning Brief — shared interactive behaviour for all newsletters.
 *
 * Loaded by every daily newsletter via <script defer src="../lib/newsletter.js"></script>.
 * Auto-detects interactive components on the page and initialises them. Each component
 * function bails out silently if its target elements aren't present, so loading this
 * lib on a content-only page (e.g. family) is harmless.
 *
 * Component contracts (see _COMPONENTS.md for full HTML):
 *
 *   fx-detail-panel + fx-card-set sparklines
 *     • One <div data-component="fx-detail-panel"> on the page.
 *     • Sparkline canvases:  <canvas id="spark-eurbrl">, <canvas id="spark-usdbrl">, etc.
 *     • Detail-chart canvas: <canvas id="detail-chart">.
 *     • Pair switcher:       <div id="pair-toggle"><button data-pair="eurbrl">…</button>…</div>
 *     • Range switcher:      <div id="range-toggle"><button data-range="W">…</button>…</div>
 *     • Data: <script type="application/json" id="fx-series">{...}</script>
 *       Shape: { "<pair-id>": { "label": "...", "color": "...optional",
 *                                "W": {"labels":[…], "data":[…]},
 *                                "M": {…}, "Y": {…} }, … }
 *     • Requires Chart.js loaded via CDN in <head>.
 *
 *   r-hour-calculator
 *     • <div class="calc" data-component="r-hour-calc"
 *            data-yday="5.85" data-base="6.00" data-eur-per-hour="100">…</div>
 *     • Slider:    <input type="range">
 *     • Output:    <span id="calc-out"> or <span data-out>
 *     • Rate echo: <span class="calc-value"> or <span data-rate>
 *     • Deltas:    <span id="calc-delta-yday">, <span id="calc-delta-base">
 *
 *   benchmark-bar-chart
 *     • <div data-component="benchmark-chart"><div class="bench-chart-wrap"><canvas></canvas></div></div>
 *     • Data: <script type="application/json" id="bench-data">{...}</script>
 *       Shape: { "labels": ["…","…"], "data": [n,n,…], "max": 100 (optional), "unit": " %" (optional) }
 *     • Requires Chart.js.
 *
 *   causal-chain-mermaid
 *     • <pre class="mermaid">graph LR\nA --> B</pre>
 *     • Requires Mermaid loaded via CDN. Auto-init only fires if Mermaid global exists.
 */
(function () {
  // Resolution-independent zoom (mirrors pagr): scale the whole layout up past a
  // 1920px reference. Only when the brief is viewed STANDALONE — inside the dashboard
  // iframe the parent already zooms, so skip to avoid double-scaling.
  if (window.self === window.top) {
    const applyZoom = () => {
      document.documentElement.style.zoom = String(Math.max(1, window.innerWidth / 1920));
    };
    applyZoom();
    window.addEventListener('resize', applyZoom);
  }

  /* ──────────────────────────────────────────────────────────────────
     Component registry — Strategy pattern.
     Each interactive component registers an init() function. On
     DOMContentLoaded the bootstrap loop iterates the registry and
     calls each one. Initialisers are individually responsible for
     detecting their own DOM targets (and returning silently if
     nothing matches), so the loop is order-independent except for
     hard cases like Chart defaults — see chart-defaults below.
     ────────────────────────────────────────────────────────────────── */
  const componentRegistry = [];
  function registerComponent(name, init) {
    componentRegistry.push({ name, init });
  }

  function cssColors() {
    const s = getComputedStyle(document.documentElement);
    return {
      fg:      s.getPropertyValue('--fg').trim(),
      muted:   s.getPropertyValue('--muted-ink').trim(),
      rule:    s.getPropertyValue('--rule').trim(),
      accent:  s.getPropertyValue('--cat-accent').trim(),
      accent2: s.getPropertyValue('--cat-accent-2').trim(),
      warn:    s.getPropertyValue('--warn').trim(),
      good:    s.getPropertyValue('--good').trim(),
    };
  }

  const fmt = (n, d = 2) => Number(n).toFixed(d).replace('.', ',');

  /* ──────────────────────────────────────────────────────────────────
     Shared i18n for interactive-UI chrome (voice-reader controls, image
     lightbox). The page language drives the labels so EN/PT/ES newsletters
     don't surface German controls. Derived from <html lang> at call time
     (de | en-US | pt-BR | es-MX → de | en | pt | es). NOTE: this covers the
     control CHROME only; the voice-SELECTION logic (which voice is spoken)
     is still German-only — see pickVoice/populateVoiceSelect.
     ────────────────────────────────────────────────────────────────── */
  function pageLang() {
    const l = (document.documentElement.lang || 'de').toLowerCase();
    if (l.startsWith('en')) return 'en';
    if (l.startsWith('pt')) return 'pt';
    if (l.startsWith('es')) return 'es';
    return 'de';
  }
  const UI_STRINGS = {
    de: { readStop: 'Vorlesen stoppen', pause: 'Pause', resume: 'Weiterlesen',
          sectionReadAria: 'Sektion vorlesen', sectionReadTitle: 'Diese Sektion vorlesen',
          readAll: 'Ganzen Newsletter vorlesen', print: 'Drucken', pauseResume: 'Pause / Weiter', stop: 'Stop',
          voice: 'Stimme', voiceChoose: 'Stimme wählen', rate: 'Geschwindigkeit',
          menuToggle: 'Vorlese-Menü ein-/ausblenden', menu: 'Vorlese-Menü',
          zoomIn: 'Vergrößert anzeigen', zoomedView: 'Vergrößerte Ansicht', diagram: 'Diagramm', close: 'Schließen',
          voiceLangGroup: 'Deutsch', voiceOtherGroup: 'Andere Sprachen', noVoiceShort: '⚠️ keine DE-Stimme', noVoiceHelp: 'Keine deutsche Stimme installiert. macOS: Systemeinstellungen → Bedienungshilfen → Gesprochene Inhalte → Systemstimme → Stimmen verwalten → Deutsch.', sourcesLabel: 'Quellen',
          rangeW: 'Letzte Woche (täglich)', rangeM: 'Letzten 30 Tage', rangeY: 'Letzte 12 Monate' },
    en: { readStop: 'Stop reading', pause: 'Pause', resume: 'Resume',
          sectionReadAria: 'Read section', sectionReadTitle: 'Read this section aloud',
          readAll: 'Read whole newsletter', print: 'Print', pauseResume: 'Pause / Resume', stop: 'Stop',
          voice: 'Voice', voiceChoose: 'Choose voice', rate: 'Speed',
          menuToggle: 'Toggle read-aloud menu', menu: 'Read-aloud menu',
          zoomIn: 'Enlarge', zoomedView: 'Enlarged view', diagram: 'Diagram', close: 'Close',
          voiceLangGroup: 'English', voiceOtherGroup: 'Other languages', noVoiceShort: '⚠️ no English voice', noVoiceHelp: 'No English voice installed. macOS: System Settings → Accessibility → Spoken Content → System Voice → Manage Voices → English.', sourcesLabel: 'Sources',
          rangeW: 'Last week (daily)', rangeM: 'Last 30 days', rangeY: 'Last 12 months' },
    pt: { readStop: 'Parar leitura', pause: 'Pausar', resume: 'Continuar',
          sectionReadAria: 'Ler seção', sectionReadTitle: 'Ler esta seção em voz alta',
          readAll: 'Ler boletim inteiro', print: 'Imprimir', pauseResume: 'Pausar / Continuar', stop: 'Parar',
          voice: 'Voz', voiceChoose: 'Escolher voz', rate: 'Velocidade',
          menuToggle: 'Mostrar/ocultar menu de leitura', menu: 'Menu de leitura',
          zoomIn: 'Ampliar', zoomedView: 'Visualização ampliada', diagram: 'Diagrama', close: 'Fechar',
          voiceLangGroup: 'Português', voiceOtherGroup: 'Outros idiomas', noVoiceShort: '⚠️ sem voz PT', noVoiceHelp: 'Nenhuma voz em português instalada. macOS: Ajustes do Sistema → Acessibilidade → Conteúdo Falado → Voz do Sistema → Gerenciar Vozes → Português.', sourcesLabel: 'Fontes',
          rangeW: 'Última semana (diário)', rangeM: 'Últimos 30 dias', rangeY: 'Últimos 12 meses' },
    es: { readStop: 'Detener lectura', pause: 'Pausar', resume: 'Continuar',
          sectionReadAria: 'Leer sección', sectionReadTitle: 'Leer esta sección en voz alta',
          readAll: 'Leer todo el boletín', print: 'Imprimir', pauseResume: 'Pausar / Continuar', stop: 'Detener',
          voice: 'Voz', voiceChoose: 'Elegir voz', rate: 'Velocidad',
          menuToggle: 'Mostrar/ocultar menú de lectura', menu: 'Menú de lectura',
          zoomIn: 'Ampliar', zoomedView: 'Vista ampliada', diagram: 'Diagrama', close: 'Cerrar',
          voiceLangGroup: 'Español', voiceOtherGroup: 'Otros idiomas', noVoiceShort: '⚠️ sin voz ES', noVoiceHelp: 'No hay voz en español instalada. macOS: Configuración del Sistema → Accesibilidad → Contenido Hablado → Voz del Sistema → Administrar Voces → Español.', sourcesLabel: 'Fuentes',
          rangeW: 'Última semana (diario)', rangeM: 'Últimos 30 días', rangeY: 'Últimos 12 meses' },
  };
  function ui(key) { return (UI_STRINGS[pageLang()] || UI_STRINGS.de)[key]; }

  // Per-language preferred voice-name fragments (priority order), shared by the
  // voice-reader and the per-word speak buttons. ES targets Mexican Spanish
  // (es-MX): prefer Paulina/Juan/Google MX before other LatAm Spanish, with
  // Castilian (Mónica) only as a last resort.
  const VOICE_PREFS = {
    'de':    ['Google Deutsch', 'Anna', 'Markus', 'Petra'],
    'en':    ['Google US English', 'Samantha', 'Alex'],
    'pt-BR': ['Google português do Brasil', 'Luciana', 'Felipe'],
    'pt':    ['Google português do Brasil', 'Luciana'],
    'es-MX': ['Google español de México', 'Paulina', 'Juan', 'Google US Spanish', 'Mónica'],
    'es':    ['Google español de México', 'Paulina', 'Juan', 'Google US Spanish', 'Mónica'],
  };

  function parseJsonScript(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); }
    catch (e) { console.warn('Invalid JSON in #' + id, e); return null; }
  }

  function configureChartDefaults() {
    const C = cssColors();
    Chart.defaults.color = C.muted;
    Chart.defaults.borderColor = C.rule;
    Chart.defaults.font.family = '"JetBrains Mono Variable", "JetBrains Mono", "Menlo", monospace';
    Chart.defaults.font.size = 10;
  }

  function initFxPanel() {
    const SERIES = parseJsonScript('fx-series');
    if (!SERIES) return;
    const C = cssColors();
    const defaultColors = { eurbrl: C.warn, usdbrl: C.accent, dxy: C.accent2 };
    Object.keys(SERIES).forEach(k => {
      if (!SERIES[k].color) SERIES[k].color = defaultColors[k] || C.accent;
    });

    // Sparklines
    const sparks = {};
    Object.keys(SERIES).forEach(key => {
      const ctx = document.getElementById('spark-' + key);
      if (!ctx) return;
      const s = SERIES[key];
      const initial = s.W || s.M || s.Y;
      if (!initial) return;
      sparks[key] = new Chart(ctx, {
        type: 'line',
        data: { labels: initial.labels, datasets: [{
          data: initial.data, borderColor: s.color, backgroundColor: s.color + '22',
          borderWidth: 1.5, pointRadius: 0, fill: true, tension: 0.35
        }] },
        options: { responsive: true, maintainAspectRatio: false, animation: false,
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          scales: { x: { display: false }, y: { display: false } } }
      });
    });

    // Detail chart
    const detailCanvas = document.getElementById('detail-chart');
    if (!detailCanvas) return;
    const firstPair = Object.keys(SERIES)[0];
    let currentPair = firstPair, currentRange = 'W';

    const detail = new Chart(detailCanvas, {
      type: 'line',
      data: { labels: SERIES[firstPair].W.labels, datasets: [{
        label: SERIES[firstPair].label,
        data: SERIES[firstPair].W.data,
        borderColor: SERIES[firstPair].color,
        backgroundColor: SERIES[firstPair].color + '20',
        borderWidth: 2, pointRadius: 3, pointHoverRadius: 5,
        pointBackgroundColor: SERIES[firstPair].color, fill: true, tension: 0.3,
      }] },
      options: {
        responsive: true, maintainAspectRatio: false, animation: { duration: 250 },
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: c => c.dataset.label + ': ' + fmt(c.parsed.y, c.dataset.label === 'DXY' ? 1 : 3) } }
        },
        scales: {
          y: { grid: { color: C.rule }, ticks: { callback: v => typeof v === 'number' ? fmt(v) : v } },
          x: { grid: { display: false } }
        }
      }
    });

    function rerender() {
      const s = SERIES[currentPair];
      const series = s[currentRange];
      if (!series) return;
      detail.data.labels = series.labels;
      detail.data.datasets[0].data = series.data;
      detail.data.datasets[0].label = s.label;
      detail.data.datasets[0].borderColor = s.color;
      detail.data.datasets[0].backgroundColor = s.color + '20';
      detail.data.datasets[0].pointBackgroundColor = s.color;
      detail.update();
      const labelEl = document.getElementById('detail-pair-label');
      if (labelEl) labelEl.textContent = s.label;
      const subEl = document.getElementById('detail-sub');
      if (subEl) {
        subEl.textContent = ui(currentRange === 'W' ? 'rangeW' : currentRange === 'M' ? 'rangeM' : 'rangeY') + '.';
      }
    }

    document.querySelectorAll('#pair-toggle button').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#pair-toggle button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentPair = btn.dataset.pair;
        rerender();
      });
    });
    document.querySelectorAll('#range-toggle button').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#range-toggle button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentRange = btn.dataset.range;
        Object.keys(sparks).forEach(k => {
          const s = SERIES[k][currentRange];
          if (!s) return;
          sparks[k].data.labels = s.labels;
          sparks[k].data.datasets[0].data = s.data;
          sparks[k].update();
        });
        rerender();
      });
    });
  }

  function initBenchmarkChart() {
    const wrap = document.querySelector('[data-component="benchmark-chart"]');
    if (!wrap) return;
    const canvas = wrap.querySelector('canvas');
    const data = parseJsonScript('bench-data');
    if (!canvas || !data) return;
    const C = cssColors();
    new Chart(canvas, {
      type: 'bar',
      data: { labels: data.labels, datasets: [{ data: data.data, backgroundColor: C.accent + '88', borderRadius: 4 }] },
      options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: { beginAtZero: true, max: data.max || 100, ticks: { callback: v => v + (data.unit || ' %') } } } }
    });
  }

  function initRHourCalc() {
    const calc = document.querySelector('[data-component="r-hour-calc"]');
    if (!calc) return;
    const range  = calc.querySelector('input[type="range"]');
    const out    = calc.querySelector('#calc-out')        || calc.querySelector('[data-out]');
    const rateEl = calc.querySelector('.calc-value')      || calc.querySelector('[data-rate]');
    const dYday  = calc.querySelector('#calc-delta-yday') || calc.querySelector('[data-delta-yday]');
    const dBase  = calc.querySelector('#calc-delta-base') || calc.querySelector('[data-delta-base]');
    if (!range) return;
    const eurPerHour = parseFloat(calc.dataset.eurPerHour || '100');
    const yday       = parseFloat(calc.dataset.yday       || '0');
    const base       = parseFloat(calc.dataset.base       || '6.00');

    function update() {
      const r = parseFloat(range.value);
      if (out)    out.textContent    = 'R$' + fmt(eurPerHour * r);
      if (rateEl) rateEl.textContent = fmt(r, 3);
      const dy = (r - yday) * eurPerHour;
      const db = (r - base) * eurPerHour;
      if (dYday) {
        dYday.textContent = (dy >= 0 ? '+' : '−') + 'R$' + fmt(Math.abs(dy)) + '/h';
        dYday.className = 'calc-delta ' + (dy >= 0 ? 'good' : 'bad');
      }
      if (dBase) {
        dBase.textContent = (db >= 0 ? '+' : '−') + 'R$' + fmt(Math.abs(db)) + '/h';
        dBase.className = 'calc-delta ' + (db >= 0 ? 'good' : 'bad');
      }
    }
    range.addEventListener('input', update);
    update();
  }

  /* ──────────────────────────────────────────────────────────────────
     Footnotes — convert inline (cited) external links inside prose into
     [N] superscripts that jump to a "Quellen" block at the bottom of
     each section / news-item. Also absorbs the existing .src / .source
     / .citation block-level citations so each section ends with a
     single unified footer instead of two competing patterns.

     Skipped contexts (links stay inline):
       .tldr             — scan bullets, intentionally clickable inline
       .timeline         — Wochenausblick events stay inline
       .eli5, .callout   — short explainer boxes, keep linked terms inline
       .footnotes        — never reprocess already-generated footer
       .pro-con          — small comparison panels
     ────────────────────────────────────────────────────────────────── */

  function initFootnotes() {
    const SKIP = '.tldr, .timeline, .eli5, .callout, .footnotes, .pro-con';
    // Containers that get their own footnote pool. Top-level <section>s in
    // <main> are the primary unit; .news-item articles inside them get their
    // own footnotes too (so each "story" carries its own Quellen block).
    const TARGETS = 'main section, main article.news-item';
    let sectionIdx = 0;

    document.querySelectorAll(TARGETS).forEach(target => {
      if (target.matches(SKIP) || target.closest(SKIP)) return;
      // Idempotent — skip if already processed (function may run twice via bootstrap retry).
      if (target.querySelector(':scope > .footnotes')) return;

      sectionIdx++;
      const refs = [];
      const urlToNum = new Map();

      function getOrAddRef(url, label) {
        if (urlToNum.has(url)) return urlToNum.get(url);
        const n = refs.length + 1;
        urlToNum.set(url, n);
        refs.push({ url, label: label || url });
        return n;
      }

      // 1. Inline external links in <p> elements — replace with [N] markers.
      target.querySelectorAll('p a[href^="http"]').forEach(a => {
        if (a.closest(SKIP)) return;
        // If this <a> belongs to a nested target, it'll be processed in that
        // target's own iteration — skip here to avoid double-numbering.
        const owner = a.closest(TARGETS);
        if (owner !== target) return;

        const url = a.href;
        const label = (a.textContent || '').trim() || url;
        const n = getOrAddRef(url, label);

        const sup = document.createElement('sup');
        sup.className = 'footnote-ref';
        sup.innerHTML = '<a href="#fn-s' + sectionIdx + '-' + n + '">' + n + '</a>';
        replaceWithStrippedParens(a, sup);
      });

      // 2. Block-level citation containers — absorb into the same footnote pool, then hide.
      target.querySelectorAll('.src, .source, .citation').forEach(srcEl => {
        if (srcEl.closest(SKIP)) return;
        const owner = srcEl.closest(TARGETS);
        if (owner !== target) return;
        srcEl.querySelectorAll('a[href^="http"]').forEach(a => {
          getOrAddRef(a.href, (a.textContent || '').trim());
        });
        srcEl.style.display = 'none';
      });

      if (refs.length === 0) return;

      // Build the unified sources footer (label localised per page language).
      const footer = document.createElement('div');
      footer.className = 'footnotes';
      let html = '<div class="footnotes-label">' + ui('sourcesLabel') + '</div><ol>';
      refs.forEach((r, i) => {
        html += '<li id="fn-s' + sectionIdx + '-' + (i + 1) + '">'
              + '<a href="' + escapeAttr(r.url) + '" rel="noopener">'
              + escapeHtml(r.label) + '</a></li>';
      });
      html += '</ol>';
      footer.innerHTML = html;
      target.appendChild(footer);
    });
  }

  // Replace an inline <a> with its <sup> superscript, optionally stripping
  // a single surrounding pair of parens. The common cite pattern in this
  // codebase is " (<a>cftc.gov, 15.05</a>)" — without stripping you'd be
  // left with "( [1] )" which reads worse than the original.
  function replaceWithStrippedParens(a, sup) {
    const prev = a.previousSibling;
    const next = a.nextSibling;
    const prevText = prev && prev.nodeType === Node.TEXT_NODE ? prev.textContent : '';
    const nextText = next && next.nodeType === Node.TEXT_NODE ? next.textContent : '';
    if (/\(\s*$/.test(prevText) && /^\s*\)/.test(nextText)) {
      prev.textContent = prevText.replace(/\s*\(\s*$/, ' ');
      a.replaceWith(sup);
      next.textContent = nextText.replace(/^\s*\)\s*/, ' ');
      return;
    }
    a.replaceWith(sup);
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
  }
  function escapeAttr(s) { return escapeHtml(s); }

  /* ──────────────────────────────────────────────────────────────────
     Voice reader — uses Web Speech API (no CDN, browser-native).
     Adds a 🔊 button to every <h2> in <main> (and the TL;DR h2),
     plus a floating bottom-right control panel with pause/stop/speed.
     ────────────────────────────────────────────────────────────────── */

  function initVoiceReader() {
    if (!('speechSynthesis' in window) || !('SpeechSynthesisUtterance' in window)) return;

    const synth = window.speechSynthesis;
    let chunks = [];           // [{el, text}]
    let chunkIndex = 0;
    let voice = null;
    let activeSection = null;
    let isReadingAll = false;  // true while reading from masthead through every section
    let isPaused = false;      // user-toggled pause flag — survives synth.cancel()
    let currentCharIndex = 0;  // latest character offset within the current chunk's text,
                               // updated by the boundary event. Resume picks up from here
                               // by speaking text.substring(currentCharIndex).

    // Sentence-segmenter — Intl.Segmenter handles German abbreviation cases correctly
    // (z. B., u. a., Dr., Hr., etc.) that a naive `[.!?]` regex would split wrongly.
    // Falls back to a simple regex when the API isn't available.
    function splitIntoSentences(text) {
      try {
        if (typeof Intl !== 'undefined' && Intl.Segmenter) {
          const seg = new Intl.Segmenter('de-DE', { granularity: 'sentence' });
          const out = [];
          for (const s of seg.segment(text)) {
            const t = s.segment.replace(/\s+/g, ' ').trim();
            if (t) out.push(t);
          }
          return out.length ? out : [text];
        }
      } catch (_) { /* fall through */ }
      // Fallback: split on sentence-terminator followed by whitespace + uppercase/quote/digit.
      const parts = text.split(/(?<=[.!?])\s+(?=[A-ZÄÖÜ"„'(0-9])/);
      return parts.map(p => p.trim()).filter(Boolean);
    }

    // Saved voice preference (per-browser via localStorage)
    let savedVoiceName = null;
    try { savedVoiceName = localStorage.getItem('mb-voice'); } catch (e) { /* private mode */ }

    function pickVoice() {
      const voices = synth.getVoices();
      if (!voices.length) return;
      const pl = pageLang();
      // 1. User-saved preference wins — but only if it matches the page language, so a
      //    German voice chosen on a DE page isn't reused to read an EN/PT/ES page.
      if (savedVoiceName) {
        const saved = voices.find(v => v.name === savedVoiceName);
        if (saved && saved.lang.toLowerCase().startsWith(pl)) { voice = saved; return; }
      }
      // 2. Prefer the page language's high-quality voices, then any voice in that language.
      //    Leave `voice` null if none exists — the browser then uses its own default.
      const prefs = VOICE_PREFS[pl] || [];
      voice = prefs.map(name => voices.find(v => v.name.includes(name))).find(Boolean)
           || voices.find(v => v.lang.toLowerCase().startsWith(pl))
           || null;
    }

    function populateVoiceSelect() {
      const sel = document.querySelector('.voice-reader-panel [data-vr="voice"]');
      if (!sel) return;
      const voices = synth.getVoices();
      if (!voices.length) return;

      const pl = pageLang();
      const inPageLang = v => v.lang.toLowerCase().startsWith(pl);
      // Sort: page-language voices first, then by language code + name.
      const sorted = voices.slice().sort((a, b) => {
        const s = (inPageLang(a) ? 0 : 1) - (inPageLang(b) ? 0 : 1);
        return s || a.lang.localeCompare(b.lang) || a.name.localeCompare(b.name);
      });

      sel.innerHTML = '';
      let groupPage = null, groupOther = null;
      sorted.forEach(v => {
        let parent;
        if (inPageLang(v)) {
          if (!groupPage) {
            groupPage = document.createElement('optgroup');
            groupPage.label = ui('voiceLangGroup');
            sel.appendChild(groupPage);
          }
          parent = groupPage;
        } else {
          if (!groupOther) {
            groupOther = document.createElement('optgroup');
            groupOther.label = ui('voiceOtherGroup');
            sel.appendChild(groupOther);
          }
          parent = groupOther;
        }
        const opt = document.createElement('option');
        opt.value = v.name;
        opt.textContent = `${v.name} (${v.lang})`;
        parent.appendChild(opt);
      });

      // Set selected value after appending (more reliable than opt.selected = true)
      if (voice) sel.value = voice.name;

      // If no voice exists for the page language, warn in the status area.
      const status = document.querySelector('.voice-reader-panel .vr-status');
      if (status && !groupPage) {
        status.textContent = ui('noVoiceShort');
        status.title = ui('noVoiceHelp');
      }
    }

    function onVoiceChange(e) {
      const voices = synth.getVoices();
      const picked = voices.find(v => v.name === e.target.value);
      if (!picked) return;
      voice = picked;
      try { localStorage.setItem('mb-voice', picked.name); } catch (_) {}
      // If currently speaking, swap voice on the next chunk (current utterance finishes its line).
    }

    pickVoice();
    synth.addEventListener('voiceschanged', () => {
      pickVoice();
      populateVoiceSelect();
    });

    function getRate() {
      // IMPORTANT: target the rate select specifically. The panel also contains a voice select,
      // and a plain '.voice-reader-panel select' query grabs the FIRST one — which (since the
      // voice picker was added) is the voice dropdown. parseFloat('Anna') → NaN → utt.rate
      // throws TypeError → speech never starts. Always select by data-vr attribute.
      const sel = document.querySelector('.voice-reader-panel select[data-vr="rate"]');
      const r = sel ? parseFloat(sel.value) : 1.0;
      return Number.isFinite(r) && r > 0 ? r : 1.0;
    }

    function clearHighlight() {
      document.querySelectorAll('.voice-reading-now').forEach(el => el.classList.remove('voice-reading-now'));
    }

    function updateStatus() {
      const status = document.querySelector('.voice-reader-panel .vr-status');
      if (!status) return;
      if (chunks.length === 0) {
        status.textContent = '';
      } else if (synth.paused) {
        status.textContent = `${chunkIndex + 1}/${chunks.length} ⏸`;
      } else if (synth.speaking) {
        status.textContent = `${chunkIndex + 1}/${chunks.length}`;
      } else {
        status.textContent = '';
      }
    }

    function speakChunk(startOffset) {
      if (chunkIndex >= chunks.length) { stopReading(); return; }
      clearHighlight();
      const { el, text } = chunks[chunkIndex];
      el.classList.add('voice-reading-now');

      // startOffset > 0 means we're resuming mid-paragraph after a pause.
      const offset = (typeof startOffset === 'number' && startOffset > 0 && startOffset < text.length) ? startOffset : 0;
      const textToSpeak = offset > 0 ? text.substring(offset) : text;
      currentCharIndex = offset;

      const utt = new SpeechSynthesisUtterance(textToSpeak);
      // IMPORTANT: utt.lang must match utt.voice.lang or some browsers silently drop the utterance.
      if (voice) {
        utt.voice = voice;
        utt.lang  = voice.lang;
      }
      utt.rate   = getRate();
      utt.volume = 1;
      utt.pitch  = 1;

      // Track the engine's character position so pause+resume can continue from where it left off.
      // Note: e.charIndex is relative to the utterance text we passed in (already substring'd),
      // so we add `offset` to map back to the original chunk text.
      utt.onboundary = (e) => {
        if (e && (e.name === 'word' || e.name === 'sentence') && typeof e.charIndex === 'number') {
          currentCharIndex = offset + e.charIndex;
        }
      };

      let advanced = false;
      const advance = () => {
        if (advanced) return;
        advanced = true;
        // If the user paused mid-utterance, synth.cancel() fires onend — but we must NOT
        // auto-advance to the next chunk. Wait for the user's resume click instead.
        if (isPaused) return;
        chunkIndex++;
        currentCharIndex = 0;  // next chunk always starts from the beginning
        speakChunk();
      };
      utt.onend = advance;
      utt.onerror = (e) => {
        try { console.warn('[voice] speech error chunk', chunkIndex + 1, '/', chunks.length, ':', (e && e.error) || e); } catch (_) {}
        advance();
      };

      // Defensive: if a previous session left the queue paused, unstick it before queuing.
      if (synth.paused) synth.resume();

      synth.speak(utt);
      updateStatus();
    }

    function pushSentenceChunks(list, el, fullText) {
      // Split each element's text into sentence-level chunks so pause/resume granularity
      // is at most one sentence instead of one paragraph. Multiple chunks can share the
      // same `el` — the visual highlight on the element doesn't flicker since clearHighlight
      // + re-add happen in the same JS frame.
      const sentences = splitIntoSentences(fullText);
      sentences.forEach(s => { if (s) list.push({ el, text: s }); });
    }

    // Read the element's text content but strip out elements that shouldn't
    // be spoken aloud — the section's own 🔊 button, footnote markers like
    // "[1]", and the bottom "Quellen" list (those are already linked refs,
    // reading them out loud is just noise).
    function readableText(el) {
      const clone = el.cloneNode(true);
      clone.querySelectorAll('.read-btn, .footnote-ref, .footnotes, code, pre, script, style')
           .forEach(n => n.remove());
      return (clone.textContent || '').replace(/\s+/g, ' ').trim();
    }

    function gatherChunks(nodes) {
      const list = [];
      nodes.forEach(node => {
        const inlineTextEls = node.matches && node.matches('h2, h3, p, li, .lead, .masthead-title');
        if (inlineTextEls) {
          const t = readableText(node);
          if (t) pushSentenceChunks(list, node, t);
          return;
        }
        node.querySelectorAll && node.querySelectorAll('h2, h3, p, li, .lead').forEach(el => {
          if (el.closest('.voice-reader-panel, code, pre, script, style, .read-btn, .footnotes')) return;
          // Skip the TL;DR section entirely — voice reader is intentionally disabled there.
          if (el.closest('.tldr')) return;
          const t = readableText(el);
          if (t) pushSentenceChunks(list, el, t);
        });
      });
      return list;
    }

    function readNodes(nodes) {
      stopReading();
      chunks = gatherChunks(nodes);
      if (chunks.length === 0) return;
      chunkIndex = 0;
      document.body.classList.add('voice-reading');
      // Tiny delay: cancel() right above + immediate speak() is a documented Chrome/Safari race
      // where speak() queues but never starts. Letting the engine settle for 80ms reliably avoids it.
      setTimeout(speakChunk, 80);
    }

    function readSection(h2) {
      // stopReading() runs inside readNodes() — that's where the *previous* active section's
      // state gets cleared. Set the new active section AFTER that, then mark it visually.
      const nodes = [h2];
      let el = h2.nextElementSibling;
      while (el && el.tagName !== 'H2') {
        nodes.push(el);
        el = el.nextElementSibling;
      }
      readNodes(nodes);
      activeSection = h2;
      h2.classList.add('section-reading');
      const btn = h2.querySelector('.read-btn');
      if (btn) {
        btn.classList.add('is-reading');
        btn.textContent = '⏹';
        btn.title = ui('readStop');
        btn.setAttribute('aria-label', ui('readStop'));
      }
      // Auto-open the panel so the user has pause/stop available without hunting.
      const panel = document.querySelector('.voice-reader-panel');
      if (panel) panel.classList.add('open');
    }

    function readAll() {
      // Prefer the authored voice-summary block when present. That block is
      // structured for spoken delivery — continuous narrative, no h2/h3
      // titles, no chips, no inline "[7]" refs — so it reads as a coherent
      // story rather than a stutter of headlines. If no summary is authored,
      // fall back to walking visible page content.
      const summary = document.querySelector('.voice-summary');
      const nodes = [];
      if (summary && summary.querySelector('p, li')) {
        nodes.push(summary);
      } else {
        const main = document.querySelector('main.shell, main');
        const mastheadTitle = document.querySelector('.masthead-title');
        if (mastheadTitle) nodes.push(mastheadTitle);
        if (main) nodes.push(main); else nodes.push(document.body);
      }
      activeSection = null;
      readNodes(nodes);
      // Mark "read-all" mode on
      isReadingAll = true;
      const readAllBtn = document.querySelector('.read-all-btn');
      if (readAllBtn) {
        readAllBtn.classList.add('is-reading');
        readAllBtn.textContent = '⏹';
        readAllBtn.title = ui('readStop');
        readAllBtn.setAttribute('aria-label', ui('readStop'));
      }
      // Auto-open the panel so pause/stop are accessible.
      const panel = document.querySelector('.voice-reader-panel');
      if (panel) panel.classList.add('open');
    }

    function pauseResume() {
      // We deliberately do NOT use synth.pause() / synth.resume() — Chrome has a long-standing
      // bug where resume() leaves the audio queue silent. Instead:
      //   pause  = synth.cancel() + isPaused=true  (advance handler bails out;
      //                                              currentCharIndex preserves position)
      //   resume = speakChunk(currentCharIndex)   (continues from the boundary just spoken)
      //
      // For voices that fire boundary events (most local voices like Anna/Markus on macOS):
      //   resume picks up at the last word/sentence boundary — essentially seamless.
      // For voices that don't fire boundary events (some network voices):
      //   currentCharIndex stays at 0 and resume restarts the current paragraph — graceful
      //   degradation, no error.
      const pauseBtn = document.querySelector('.voice-reader-panel button[data-vr="pause"]');
      if (isPaused) {
        isPaused = false;
        document.body.classList.remove('voice-paused');
        if (pauseBtn) {
          pauseBtn.textContent = '⏸';
          pauseBtn.title = ui('pause');
          pauseBtn.setAttribute('aria-label', ui('pause'));
        }
        speakChunk(currentCharIndex);
      } else if (chunks.length > 0 && chunkIndex < chunks.length) {
        isPaused = true;
        document.body.classList.add('voice-paused');
        if (pauseBtn) {
          pauseBtn.textContent = '▶';
          pauseBtn.title = ui('resume');
          pauseBtn.setAttribute('aria-label', ui('resume'));
        }
        synth.cancel();
        // currentCharIndex was kept up-to-date by the boundary handler; don't touch it.
      }
      updateStatus();
    }

    function stopReading() {
      synth.cancel();
      clearHighlight();
      isPaused = false;
      currentCharIndex = 0;
      // Restore the previously-active section's visual state (h2 + button icon).
      if (activeSection) {
        activeSection.classList.remove('section-reading');
        const btn = activeSection.querySelector('.read-btn');
        if (btn) {
          btn.classList.remove('is-reading');
          btn.textContent = '🔊';
          btn.title = ui('sectionReadTitle');
          btn.setAttribute('aria-label', ui('sectionReadAria'));
        }
      }
      // Restore the read-all button if it was active.
      if (isReadingAll) {
        const readAllBtn = document.querySelector('.read-all-btn');
        if (readAllBtn) {
          readAllBtn.classList.remove('is-reading');
          readAllBtn.textContent = '🔊';
          readAllBtn.title = ui('readAll');
          readAllBtn.setAttribute('aria-label', ui('readAll'));
        }
        isReadingAll = false;
      }
      chunks = [];
      chunkIndex = 0;
      activeSection = null;
      document.body.classList.remove('voice-reading');
      document.body.classList.remove('voice-paused');
      // Reset the pause button back to its default ⏸ in case we were stopped while paused.
      const pauseBtn = document.querySelector('.voice-reader-panel button[data-vr="pause"]');
      if (pauseBtn) {
        pauseBtn.textContent = '⏸';
        pauseBtn.title = ui('pause');
        pauseBtn.setAttribute('aria-label', ui('pause'));
      }
      updateStatus();
      // Panel does NOT auto-close. User closes it manually via the 🔊 toggle.
    }

    function addSectionButtons() {
      // Voice reader is intentionally excluded from TL;DR sections — the TL;DR is a
      // scan strip with single-bullet items, not narrative prose worth listening to.
      // Reading a body section will still cover all its content (paragraphs, lists, etc.).
      document.querySelectorAll('main h2').forEach(h2 => {
        if (h2.closest('.tldr')) return;
        if (h2.querySelector('.read-btn')) return;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'read-btn';
        btn.setAttribute('aria-label', ui('sectionReadAria'));
        btn.title = ui('sectionReadTitle');
        btn.textContent = '🔊';
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          // Toggle: clicking the currently-reading section's button stops reading.
          if (activeSection === h2) {
            stopReading();
          } else {
            readSection(h2);
          }
        });
        h2.appendChild(btn);
      });
    }

    // Inject a 🔊 button into the masthead (top-right). Click reads the whole newsletter from
    // the masthead title onwards. Toggle: clicking while read-all is active stops reading.
    function addReadAllButton() {
      const masthead = document.querySelector('.masthead');
      if (!masthead) return;
      if (masthead.querySelector('.read-all-btn')) return;
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'read-btn read-all-btn';
      btn.setAttribute('aria-label', ui('readAll'));
      btn.title = ui('readAll');
      btn.textContent = '🔊';
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (isReadingAll) {
          stopReading();
        } else {
          readAll();
        }
      });
      masthead.appendChild(btn);
    }

    // Inject a 🖨 print button into the masthead next to the 🔊 button. Inside the
    // dashboard (iframe) it routes to the dashboard's broadsheet print of THIS
    // brief; standalone (opened in its own tab) it just prints the page, which
    // has its own @media print styles.
    function addPrintButton() {
      const masthead = document.querySelector('.masthead');
      if (!masthead) return;
      if (masthead.querySelector('.print-btn')) return;
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'read-btn print-btn';
      btn.setAttribute('aria-label', ui('print'));
      btn.title = ui('print');
      btn.textContent = '🖨';
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        try {
          if (window.parent !== window && typeof window.parent.mbPrintCurrent === 'function') {
            window.parent.mbPrintCurrent();
            return;
          }
        } catch (_) { /* cross-origin parent — fall through to native print */ }
        window.print();
      });
      masthead.appendChild(btn);
    }

    function buildPanel() {
      if (document.querySelector('.voice-reader-panel')) return;
      const panel = document.createElement('div');
      panel.className = 'voice-reader-panel';
      // Collapsed by default: only the ⚙ toggle is visible. Click it to expand the settings
      // panel (voice / speed / pause / stop). Expanding does NOT start reading; reading is
      // triggered only by the per-section 🔊 buttons next to each h2. The panel auto-opens
      // when a section starts reading so pause/stop are accessible.
      // DOM order: controls first, toggle last. Panel is `position:fixed; right:1rem;` so
      // it grows leftward — placing the toggle last keeps it visually pinned at the right edge
      // both when collapsed and when expanded.
      panel.innerHTML = [
        '<div class="vr-controls">',
        `<button data-vr="pause"  type="button" aria-label="${ui('pauseResume')}" title="${ui('pauseResume')}">⏸</button>`,
        `<button data-vr="stop"   type="button" aria-label="${ui('stop')}" title="${ui('stop')}">⏹</button>`,
        `<select data-vr="voice"  aria-label="${ui('voice')}" title="${ui('voiceChoose')}"></select>`,
        `<select data-vr="rate"   aria-label="${ui('rate')}" title="${ui('rate')}">`,
        '<option value="0.85">0.85×</option>',
        '<option value="1" selected>1.0×</option>',
        '<option value="1.15">1.15×</option>',
        '<option value="1.3">1.3×</option>',
        '<option value="1.5">1.5×</option>',
        '</select>',
        '<span class="vr-status"></span>',
        '</div>',
        `<button data-vr="toggle" type="button" aria-label="${ui('menuToggle')}" title="${ui('menu')}">🔊</button>`
      ].join('');
      document.body.appendChild(panel);
      panel.querySelector('[data-vr="toggle"]').onclick = () => panel.classList.toggle('open');
      panel.querySelector('[data-vr="pause"]').onclick  = pauseResume;
      panel.querySelector('[data-vr="stop"]').onclick   = stopReading;
      panel.querySelector('[data-vr="voice"]').onchange = onVoiceChange;
      // Populate voice list (voices may load async — voiceschanged handler also re-runs this)
      populateVoiceSelect();
    }

    // Removed: 12-second pause+resume "heartbeat". It was meant to defeat Chrome's
    // ~15s utterance cut-off, but it could fire near the start of playback and leave
    // the engine in a weird state where the first utterance never produces audio.
    // If long .lead or scenario-block utterances do get cut off, we'll switch to
    // sentence-level chunking instead.

    addSectionButtons();
    addReadAllButton();
    addPrintButton();
    buildPanel();
  }

  /* Ensure all links open in a new browser tab. Newsletter HTML files are iframe-embedded
     by the dashboard, and most external sites refuse to render inside iframes
     (X-Frame-Options / CSP). A <base target="_blank"> in <head> redirects every unmarked
     <a> to a new tab. New template files already ship with this; this function patches
     older files that don't. */
  function ensureLinksOpenExternally() {
    let base = document.querySelector('head > base[target]');
    if (!base) {
      base = document.createElement('base');
      base.target = '_blank';
      document.head.insertBefore(base, document.head.firstChild);
    } else if (!base.getAttribute('target')) {
      base.setAttribute('target', '_blank');
    }
    // Belt-and-suspenders: also add rel="noopener" on http(s) anchors to prevent
    // window.opener references and to follow current security best practice.
    document.querySelectorAll('a[href^="http"]').forEach(a => {
      if (!a.getAttribute('rel')) a.setAttribute('rel', 'noopener noreferrer');
    });
  }

  /* ──────────────────────────────────────────────────────────────────
     jobs-board — full-width paginated listings, sorted by fit score.
     Renders one row per listing from the inline jobs-listings JSON
     payload, with a fit badge and a collapsible scoring breakdown, and
     paginates at data-page-size. See docs/COMPONENTS.md (jobs-board) for
     the payload schema.

     The routine ships an empty container; the rows + pager are injected:
       <section class="jobs-board" data-component="jobs-board" data-page-size="20">
       </section>
     ────────────────────────────────────────────────────────────────── */
  const JOBS_UI = {
    de: { prev: 'Zurück', next: 'Weiter', page: 'Seite', of: 'von',
          count: 'Einträge', fit: 'Match', why: '— Begründung' },
    en: { prev: 'Prev', next: 'Next', page: 'Page', of: 'of',
          count: 'listings', fit: 'Fit', why: '— why' },
    pt: { prev: 'Anterior', next: 'Próximo', page: 'Página', of: 'de',
          count: 'vagas', fit: 'Match', why: '— motivo' },
    es: { prev: 'Anterior', next: 'Siguiente', page: 'Página', of: 'de',
          count: 'vacantes', fit: 'Match', why: '— motivo' },
  };
  function jui(key) { return (JOBS_UI[pageLang()] || JOBS_UI.de)[key]; }

  // role_type → track class (drives the left stripe). The routine ships
  // role_type ∈ freelance|employee|intriguing; freelance is the twiceD
  // contract track.
  const JOB_TRACK = { freelance: 'twiced', employee: 'employee', intriguing: 'intriguing' };

  function initJobsBoard() {
    // Container is <section class="jobs-board" data-component="jobs-board">;
    // bind off data-component so it's class-name agnostic.
    const board = document.querySelector('[data-component="jobs-board"]');
    if (!board || board.dataset.jobsBound) return;
    board.dataset.jobsBound = '1';

    // Listings come from an inline JSON payload (same pattern as fx-series).
    const payload = parseJsonScript('jobs-listings');
    const listings = payload && Array.isArray(payload.listings) ? payload.listings.slice() : [];
    if (!listings.length) return;

    // Default order: fit_score desc, stable on the routine's array order.
    listings.forEach((l, i) => { l._ord = i; });
    listings.sort((a, b) => (b.fit_score || 0) - (a.fit_score || 0) || a._ord - b._ord);

    const pageSize = Math.max(1, parseInt(board.dataset.pageSize, 10) || 20);
    let page = 0;
    const pageCount = Math.ceil(listings.length / pageSize);

    // Build the list container (replace any placeholder content).
    const list = document.createElement('ol');
    list.className = 'jobs-list';

    // Render one <li> per listing (fit badge injected, not hand-written markup).
    const itemEls = listings.map(job => buildItem(job));

    function buildItem(job) {
      const li = document.createElement('li');
      li.className = 'job';
      if (job.id) li.dataset.id = job.id;
      li.dataset.track = JOB_TRACK[job.role_type] || 'employee';

      const main = document.createElement('div');
      main.className = 'job-main';

      // Fit badge (float right inside job-main).
      const fit = parseInt(job.fit_score, 10);
      if (!isNaN(fit)) {
        const badge = document.createElement('span');
        badge.className = 'job-fit';
        badge.textContent = fit + '%';
        badge.title = jui('fit') + ' ' + fit + '%';
        main.appendChild(badge);
      }

      const h3 = document.createElement('h3');
      h3.className = 'job-title';
      h3.textContent = job.title || '';
      main.appendChild(h3);

      const meta = document.createElement('div');
      meta.className = 'job-meta';
      const metaBits = [job.company, job.location, job.salary_range].filter(Boolean);
      // Company in normal weight, salary emphasised.
      meta.textContent = metaBits.join(' · ');
      main.appendChild(meta);

      if (Array.isArray(job.tags) && job.tags.length) {
        const tagWrap = document.createElement('div');
        tagWrap.className = 'job-tags';
        job.tags.forEach(t => {
          const chip = document.createElement('span');
          chip.className = 'chip';
          chip.textContent = t;
          tagWrap.appendChild(chip);
        });
        main.appendChild(tagWrap);
      }

      // Source link + date.
      if (job.url) {
        const src = document.createElement('a');
        src.className = 'job-src';
        src.href = job.url;
        src.textContent = job.source || job.url;
        main.appendChild(src);
      }
      if (job.date_posted && job.date_posted !== 'n/a') {
        const d = document.createElement('span');
        d.className = 'job-date';
        d.textContent = job.date_posted;
        main.appendChild(d);
      }

      // fit_reason → collapsible scoring breakdown.
      if (job.fit_reason) {
        const det = document.createElement('details');
        det.className = 'job-reason';
        const sum = document.createElement('summary');
        sum.textContent = jui('fit') + ' ' + (isNaN(fit) ? '' : fit + '% ') + jui('why');
        det.appendChild(sum);
        const p = document.createElement('p');
        p.textContent = job.fit_reason;
        det.appendChild(p);
        main.appendChild(det);
      }

      li.appendChild(main);
      return li;
    }

    // ── Pagination ──
    const pager = document.createElement('div');
    pager.className = 'jobs-pager';
    const prevBtn = document.createElement('button');
    prevBtn.type = 'button'; prevBtn.className = 'jobs-page-btn'; prevBtn.textContent = '← ' + jui('prev');
    const nextBtn = document.createElement('button');
    nextBtn.type = 'button'; nextBtn.className = 'jobs-page-btn'; nextBtn.textContent = jui('next') + ' →';
    const status = document.createElement('span');
    status.className = 'jobs-page-status';
    prevBtn.addEventListener('click', () => { if (page > 0) { page--; render(); } });
    nextBtn.addEventListener('click', () => { if (page < pageCount - 1) { page++; render(); } });
    pager.append(prevBtn, status, nextBtn);

    // ── Meta line (listing count) ──
    const metaBar = document.createElement('div');
    metaBar.className = 'jobs-meta';
    const countEl = document.createElement('span');
    countEl.className = 'jobs-count';
    countEl.textContent = listings.length + ' ' + jui('count');
    metaBar.append(countEl);

    function render() {
      const start = page * pageSize;
      const end = start + pageSize;
      itemEls.forEach((li, i) => { li.hidden = i < start || i >= end; });
      status.textContent = jui('page') + ' ' + (page + 1) + ' ' + jui('of') + ' ' + pageCount;
      prevBtn.disabled = page === 0;
      nextBtn.disabled = page === pageCount - 1;
      if (board.dataset.painted) board.scrollIntoView({ block: 'start', behavior: 'smooth' });
      board.dataset.painted = '1';
    }

    // Assemble: meta, list, pager. Clear any placeholder, then mount.
    itemEls.forEach(li => list.appendChild(li));
    board.textContent = '';
    board.appendChild(metaBar);
    board.appendChild(list);
    if (pageCount > 1) board.appendChild(pager);
    render();
  }

  /* ──────────────────────────────────────────────────────────────────
     Register components. Order matters only for chart-defaults (must
     run before any Chart strategy) — otherwise each strategy is
     fully independent and bails out silently if its targets aren't
     on the page.
     ────────────────────────────────────────────────────────────────── */
  registerComponent('ensure-external-links', ensureLinksOpenExternally);

  registerComponent('chart-defaults', () => {
    if (typeof Chart === 'undefined') return;
    configureChartDefaults();
  });

  registerComponent('fx-panel', () => {
    if (typeof Chart === 'undefined') return;
    initFxPanel();
  });

  registerComponent('benchmark-chart', () => {
    if (typeof Chart === 'undefined') return;
    initBenchmarkChart();
  });

  registerComponent('r-hour-calc', initRHourCalc);

  registerComponent('mermaid', () => {
    if (typeof mermaid === 'undefined') return;
    mermaid.initialize({
      startOnLoad: true,
      theme: ['green','mono'].includes(document.documentElement.dataset.theme) ? 'dark' : 'default'
    });
  });

  // Footnotes runs BEFORE voice-reader so the [N] superscripts exist in the
  // DOM by the time gatherChunks reads textContent (which the readableText
  // helper then strips out, so the markers aren't read aloud).
  registerComponent('footnotes', initFootnotes);

  registerComponent('voice-reader', initVoiceReader);

  /* ──────────────────────────────────────────────────────────────────
     Image lightbox — every visual artefact on the page (inline <img>,
     Mermaid SVG, Chart.js canvas) gets click-to-zoom. Clones the node
     into a fixed-position overlay sized to fit the viewport. Click on
     the backdrop or press Escape to dismiss. Honours reduced-motion.
     ────────────────────────────────────────────────────────────────── */
  function initImageLightbox() {
    const main = document.querySelector('main.shell, main') || document.body;
    if (!main) return;

    const targets = main.querySelectorAll(
      'img, ' +
      'pre.mermaid svg, ' +
      '.detail-chart-wrap canvas, ' +
      '.bench-chart-wrap canvas, ' +
      '.fx-spark-wrap canvas'
    );
    if (!targets.length) return;

    targets.forEach(el => {
      // Skip elements already wired (re-init guard) or sat inside a button.
      if (el.dataset.lightboxBound === '1') return;
      if (el.closest('button')) return;
      el.dataset.lightboxBound = '1';
      el.style.cursor = 'zoom-in';
      el.setAttribute('role', el.tagName === 'IMG' ? 'button' : el.getAttribute('role') || 'button');
      el.setAttribute('tabindex', '0');
      el.setAttribute('aria-label', el.getAttribute('aria-label') || ui('zoomIn'));
      const open = () => openLightbox(el);
      el.addEventListener('click', open);
      el.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); }
      });
    });
  }

  function openLightbox(source) {
    if (document.querySelector('.mb-lightbox')) return;

    const overlay = document.createElement('div');
    overlay.className = 'mb-lightbox';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', ui('zoomedView'));
    overlay.tabIndex = -1;

    // Clone the source so the live page keeps its layout. For canvases,
    // copy the rendered bitmap into an <img> (canvases can't be cloned
    // with their drawn content via DOM).
    let viewer;
    if (source.tagName === 'CANVAS') {
      viewer = document.createElement('img');
      try { viewer.src = source.toDataURL('image/png'); }
      catch (_) { viewer.src = ''; }
      viewer.alt = source.getAttribute('aria-label') || ui('diagram');
    } else {
      viewer = source.cloneNode(true);
      // SVG: ensure intrinsic sizing so the overlay can scale it.
      if (viewer.tagName === 'svg' || viewer.tagName === 'SVG') {
        viewer.removeAttribute('width');
        viewer.removeAttribute('height');
        viewer.style.maxWidth = '100%';
        viewer.style.maxHeight = '100%';
        viewer.style.width = 'auto';
        viewer.style.height = 'auto';
      }
    }
    viewer.classList.add('mb-lightbox-viewer');

    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'mb-lightbox-close';
    closeBtn.setAttribute('aria-label', ui('close'));
    closeBtn.textContent = '✕';

    overlay.appendChild(viewer);
    overlay.appendChild(closeBtn);
    document.body.appendChild(overlay);

    const previouslyFocused = document.activeElement;
    overlay.focus({ preventScroll: true });

    function close() {
      overlay.remove();
      document.removeEventListener('keydown', onKey);
      if (previouslyFocused && previouslyFocused.focus) previouslyFocused.focus({ preventScroll: true });
    }
    function onKey(e) { if (e.key === 'Escape') { e.preventDefault(); close(); } }

    overlay.addEventListener('click', (e) => {
      if (e.target === overlay || e.target === closeBtn) close();
    });
    closeBtn.addEventListener('click', close);
    document.addEventListener('keydown', onKey);
  }

  registerComponent('image-lightbox', () => {
    initImageLightbox();
    // Mermaid renders asynchronously after its init runs — wait a tick
    // and re-scan so SVGs that didn't exist yet get wired too.
    setTimeout(initImageLightbox, 400);
    setTimeout(initImageLightbox, 1500);
  });

  /* ──────────────────────────────────────────────────────────────────
     Speak-buttons — per-word voice playback for the Learn-Language
     newsletter. Wires every <button class="speak" data-speak="…"
     data-lang="de|en|pt-BR|es">🔊</button> to speechSynthesis.

     Voice selection prefers Google voices (best clarity in Chrome) and
     falls back to any voice whose `lang` attribute prefix-matches the
     button's data-lang. Voice list is async in Chrome, so we register
     a voiceschanged listener that re-queries on demand.
     ────────────────────────────────────────────────────────────────── */
  function initSpeakButtons() {
    if (!('speechSynthesis' in window) || !('SpeechSynthesisUtterance' in window)) return;
    const buttons = document.querySelectorAll('.speak[data-speak][data-lang]');
    if (!buttons.length) return;
    const synth = window.speechSynthesis;

    // VOICE_PREFS is defined at module scope (shared with the voice-reader).
    function pickVoiceFor(lang) {
      const voices = synth.getVoices();
      if (!voices.length) return null;
      const prefs = VOICE_PREFS[lang] || [];
      for (const name of prefs) {
        const hit = voices.find(v => v.name.includes(name));
        if (hit) return hit;
      }
      // Fallback by lang tag prefix (e.g. "pt-BR" -> any pt voice).
      const langTag = lang.toLowerCase();
      const exact = voices.find(v => v.lang.toLowerCase() === langTag);
      if (exact) return exact;
      const prefix = langTag.split('-')[0];
      return voices.find(v => v.lang.toLowerCase().startsWith(prefix)) || null;
    }

    function speak(text, lang, btn) {
      if (!text) return;
      // Cancel any in-flight utterance — single-token playback model.
      try { synth.cancel(); } catch (_) {}
      document.querySelectorAll('.speak.is-speaking').forEach(b => b.classList.remove('is-speaking'));
      const utt = new SpeechSynthesisUtterance(text);
      utt.lang = lang;
      const v = pickVoiceFor(lang);
      if (v) utt.voice = v;
      utt.rate = 0.92;
      utt.onstart = () => btn && btn.classList.add('is-speaking');
      utt.onend   = () => btn && btn.classList.remove('is-speaking');
      utt.onerror = () => btn && btn.classList.remove('is-speaking');
      synth.speak(utt);
    }

    buttons.forEach(btn => {
      if (btn.dataset.speakBound) return;
      btn.dataset.speakBound = '1';
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        speak(btn.dataset.speak, btn.dataset.lang, btn);
      });
    });

    // Voice list arrives async in Chrome — no action needed beyond
    // re-querying on each click, which pickVoiceFor() already does.
    if (typeof synth.onvoiceschanged !== 'undefined') {
      synth.addEventListener('voiceschanged', () => { /* picked lazily on next click */ });
    }
  }

  registerComponent('speak-buttons', initSpeakButtons);
  registerComponent('jobs-board', initJobsBoard);

  /* Single dispatcher. Each strategy is wrapped in try/catch so a
     failure in one component never prevents the others from
     initialising. */
  function bootstrap() {
    for (const { name, init } of componentRegistry) {
      try { init(); }
      catch (err) { console.warn('[morning-brief] ' + name + ' failed:', err); }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
})();
