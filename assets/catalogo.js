const catalog = document.querySelector('.cover-grid');
const filters = document.querySelectorAll('.catalog-tools [data-filter]');

function filterCatalog(selected) {
  const filter = selected.dataset.filter;
  filters.forEach(button => {
    const active = button === selected;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  catalog.querySelectorAll('.book-card').forEach(card => {
    const matches = filter === 'todos' || card.dataset.category === filter ||
      (filter === 'impresso' && card.hasAttribute('data-impresso'));
    card.hidden = !matches;
  });
}

if (catalog) {
  filters.forEach(button => button.addEventListener('click', () => filterCatalog(button)));
  const printFilter = document.querySelector('.catalog-tools [data-filter="impresso"]');
  if (printFilter && new URLSearchParams(location.search).get('formato') === 'impresso') {
    filterCatalog(printFilter);
  }
}
