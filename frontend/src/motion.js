// Teal Trust motion: scroll reveal (staggered) + stat count-up.
// Wired once from App; a MutationObserver picks up SPA route changes.
const SELECTOR = '.hero, .card, .form, .filters, .row-card, .seller-hero, .chat, .stat-row > div, .section, .dash-head';

export function initMotion() {
  if (typeof window === 'undefined') return () => {};
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const io = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (!e.isIntersecting) continue;
      io.unobserve(e.target);
      e.target.classList.add('in');
      if (e.target.matches('.stat-row > div')) countUp(e.target.querySelector('strong'));
    }
  }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });

  const stagger = (root) => {
    const els = [...root.querySelectorAll(SELECTOR)].filter(
      (el) => !el.classList.contains('reveal') && !el.classList.contains('in')
    );
    els.forEach((el) => {
      const sibs = [...el.parentElement.children].filter(
        (c) => c.matches && c.matches(SELECTOR)
      );
      const idx = Math.max(0, sibs.indexOf(el));
      el.style.transitionDelay = `${Math.min(idx, 5) * 90}ms`;
      if (!reduced) el.classList.add('reveal');
      else el.classList.add('in');
      io.observe(el);
    });
  };

  const scope = document.querySelector('main.container') || document.body;
  stagger(document);
  const mo = new MutationObserver(() => stagger(document));
  mo.observe(scope, { childList: true, subtree: true });
  return () => { io.disconnect(); mo.disconnect(); };
}

function countUp(el) {
  if (!el || el.dataset.counted) return;
  el.dataset.counted = '1';
  const raw = el.textContent || '';
  const m = raw.match(/^(-?[^0-9]*)([0-9][0-9,]*(\.[0-9]+)?)(.*)$/);
  if (!m || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const [, prefix, numStr, decPart, suffix] = m;
  const target = parseFloat(numStr.replace(/,/g, ''));
  const decimals = decPart ? decPart.length - 1 : 0;
  if (!isFinite(target)) return;
  const t0 = performance.now();
  const dur = 900;
  const tick = (t) => {
    const p = Math.min(1, (t - t0) / dur);
    const eased = 1 - Math.pow(1 - p, 3);
    const val = target * eased;
    el.textContent = prefix + val.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }) + suffix;
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}
