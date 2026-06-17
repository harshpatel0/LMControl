// js/router.js
// Handles tab/page navigation.
// Pages are divs with class="page" and an id like "page-run".
// Nav items have data-page="run".

import { store } from './store.js';

export function initRouter() {
  document.querySelectorAll('[data-page]').forEach(el => {
    el.addEventListener('click', () => navigate(el.dataset.page));
  });

  // Set initial page
  navigate(store.get('currentPage'));
}

export function navigate(page) {
  // Hide all pages
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

  // Show target page
  const target = document.getElementById(`page-${page}`);
  if (target) target.classList.add('active');

  // Update nav highlight
  document.querySelectorAll('[data-page]').forEach(el => {
    el.classList.toggle('active', el.dataset.page === page);
  });

  store.set('currentPage', page);

  // Update page header title
  const titles = {
    run:      { title: 'Run Task',  subtitle: 'Execute a task using the Kodo orchestrator' },
    settings: { title: 'Settings', subtitle: 'Configure models, orchestrator, and context provider' },
    logs:     { title: 'Logs',     subtitle: 'View the live log stream and history' },
  };

  const info = titles[page];
  if (info) {
    const titleEl    = document.getElementById('page-header-title');
    const subtitleEl = document.getElementById('page-header-subtitle');
    if (titleEl)    titleEl.textContent    = info.title;
    if (subtitleEl) subtitleEl.textContent = info.subtitle;
  }
}
