"use strict";

// Translations: strings live in /static/locales/<code>.json. A value is either a
// string or, for countable texts, {one, other} picked with Intl.PluralRules.
// Placeholders look like {name}. Missing keys fall back to English.

const I18N = (() => {
  const LANGUAGES = ["en", "fr", "pt-PT"];
  const DEFAULT = "en";

  // Inline SVG flags: Windows can't display flag emoji.
  const FLAGS = {
    en: `<svg class="flag" viewBox="0 0 60 30" preserveAspectRatio="none" aria-hidden="true">
      <clipPath id="flag-uk-clip"><path d="M30,15h30v15zv15h-30zh-30v-15zv-15h30z"/></clipPath>
      <path d="M0,0v30h60v-30z" fill="#012169"/>
      <path d="M0,0 60,30M60,0 0,30" stroke="#fff" stroke-width="6"/>
      <path d="M0,0 60,30M60,0 0,30" clip-path="url(#flag-uk-clip)" stroke="#C8102E" stroke-width="4"/>
      <path d="M30,0v30M0,15h60" stroke="#fff" stroke-width="10"/>
      <path d="M30,0v30M0,15h60" stroke="#C8102E" stroke-width="6"/>
    </svg>`,
    fr: `<svg class="flag" viewBox="0 0 3 2" preserveAspectRatio="none" aria-hidden="true">
      <path d="M0 0h1v2H0z" fill="#0055A4"/>
      <path d="M1 0h1v2H1z" fill="#fff"/>
      <path d="M2 0h1v2H2z" fill="#EF4135"/>
    </svg>`,
    "pt-PT": `<svg class="flag" viewBox="0 0 600 400" preserveAspectRatio="none" aria-hidden="true">
      <path d="M0 0h240v400H0z" fill="#046A38"/>
      <path d="M240 0h360v400H240z" fill="#DA291C"/>
      <circle cx="240" cy="200" r="78" fill="none" stroke="#FFE900" stroke-width="18"/>
      <path d="M198 148h84v66a42 42 0 0 1-84 0z" fill="#fff"/>
      <path d="M212 162h56v50a28 28 0 0 1-56 0z" fill="#DA291C"/>
      <path d="M232 178h16v40h-16zM220 190h40v16h-40z" fill="#003399"/>
    </svg>`,
  };

  const dictionaries = {};
  let lang = DEFAULT;
  const listeners = [];

  function detect() {
    try {
      const saved = localStorage.getItem("lang");
      if (LANGUAGES.includes(saved)) return saved;
    } catch { /* storage unavailable */ }
    for (const pref of navigator.languages || [navigator.language || ""]) {
      const p = pref.toLowerCase();
      if (p.startsWith("fr")) return "fr";
      if (p.startsWith("pt")) return "pt-PT";
      if (p.startsWith("en")) return "en";
    }
    return DEFAULT;
  }

  async function init() {
    await Promise.all(LANGUAGES.map(async (code) => {
      const res = await fetch(`/static/locales/${code}.json`);
      dictionaries[code] = res.ok ? await res.json() : {};
    }));
    setLanguage(detect(), false);
  }

  function setLanguage(code, remember = true) {
    lang = LANGUAGES.includes(code) ? code : DEFAULT;
    document.documentElement.lang = lang;
    if (remember) {
      try { localStorage.setItem("lang", lang); } catch { /* storage unavailable */ }
    }
    apply();
    listeners.forEach((fn) => fn(lang));
  }

  function lookup(key, code = lang) {
    return dictionaries[code]?.[key] ?? dictionaries[DEFAULT]?.[key];
  }

  function has(key) {
    return lookup(key) !== undefined;
  }

  function t(key, params = {}) {
    let value = lookup(key) ?? key;
    if (typeof value === "object") {
      const category = new Intl.PluralRules(lang).select(Number(params.n ?? 0));
      value = value[category] ?? value.other;
    }
    return value.replace(/\{(\w+)\}/g, (m, name) => (name in params ? String(params[name]) : m));
  }

  // Fill elements marked with data-i18n (text) and data-i18n-title (tooltip).
  // Unknown keys keep the English text already written in the HTML.
  function apply(root = document) {
    for (const el of root.querySelectorAll("[data-i18n]")) {
      if (has(el.dataset.i18n)) el.textContent = t(el.dataset.i18n);
    }
    for (const el of root.querySelectorAll("[data-i18n-title]")) {
      if (has(el.dataset.i18nTitle)) el.title = t(el.dataset.i18nTitle);
    }
  }

  return {
    LANGUAGES,
    FLAGS,
    init,
    setLanguage,
    get lang() { return lang; },
    nameOf: (code) => lookup("lang.name", code),
    onChange: (fn) => listeners.push(fn),
    has,
    t,
    apply,
  };
})();

const t = I18N.t;
