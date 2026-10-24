(() => {
  'use strict';
  const select = document.querySelector('#site-language');
  let view = 'both';
  try { const saved = localStorage.getItem('ca-ae-language'); if (['both','zh','en'].includes(saved)) view = saved; } catch (_) {}
  function applyLanguage(value) {
    view = value;
    document.documentElement.dataset.view = value;
    document.documentElement.lang = value === 'en' ? 'en' : 'zh-CN';
    if (select) select.value = value;
    for (const guide of document.querySelectorAll('.guide')) guide.dataset.view = value;
    try { localStorage.setItem('ca-ae-language',value); } catch (_) {}
    document.dispatchEvent(new CustomEvent('languagechange',{detail:value}));
  }
  applyLanguage(view);
  if (select) select.addEventListener('change',() => applyLanguage(select.value));
  const path = location.pathname.split('/').pop() || 'index.html';
  for (const a of document.querySelectorAll('.site-links a')) if (a.dataset.page === path) { a.classList.add('is-active'); a.setAttribute('aria-current','page'); }
  const top = document.querySelector('.site-top'), menu = document.querySelector('.site-menu-btn');
  if (menu) menu.addEventListener('click',() => menu.setAttribute('aria-expanded',String(top.classList.toggle('open'))));
  for (const a of document.querySelectorAll('.site-links a')) a.addEventListener('click',() => { top.classList.remove('open'); menu.setAttribute('aria-expanded','false'); });
  for (const b of document.querySelectorAll('[data-close-reveals]')) b.addEventListener('click',() => { for (const d of document.querySelectorAll('.reveal')) d.open = false; });
  let printState = null;
  function restorePrint() {
    if (!printState) return;
    for (const [d,open] of printState) d.open = open;
    document.body.classList.remove('print-solutions'); printState = null;
  }
  for (const b of document.querySelectorAll('[data-print]')) b.addEventListener('click',() => {
    restorePrint();
    printState = [...document.querySelectorAll('.reveal')].map(d => [d,d.open]);
    const solutions = b.dataset.print === 'solutions';
    document.body.classList.toggle('print-solutions',solutions);
    for (const [d] of printState) d.open = solutions;
    window.print();
  });
  window.addEventListener('afterprint',restorePrint);
  // Deep links to question cards keep answers closed. Explicit formula/example links can reveal their enclosing details.
  function revealTarget() {
    if (!location.hash) return;
    let target;
    try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); } catch (_) { return; }
    if (target) for (let parent=target.parentElement;parent;parent=parent.parentElement) if (parent.tagName==='DETAILS') parent.open=true;
  }
  window.addEventListener('hashchange',revealTarget); revealTarget();
})();

