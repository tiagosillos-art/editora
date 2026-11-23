const catalog = document.querySelector('.cover-grid');
const filters = Array.from(document.querySelectorAll('.catalog-tools [data-filter]'));
const resultCount = document.querySelector('#catalog-result-count');

function filterCatalog(selected) {
  const filter = selected.dataset.filter;
  filters.forEach(button => {
    const active = button === selected;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  let visible = 0;
  catalog.querySelectorAll('.book-card').forEach(card => {
    const matches = filter === 'todos' || (card.dataset.category || '').split(' ').includes(filter) ||
      (filter === 'impresso' && card.hasAttribute('data-impresso'));
    card.hidden = !matches;
    if (matches) visible += 1;
  });
  if (resultCount) resultCount.textContent = visible === 1 ? '1 título' : `${visible} títulos`;
}

if (catalog) {
  const params = new URLSearchParams(location.search);
  const theme = params.get('formato') === 'impresso' ? 'impresso' : params.get('tema');
  const initialFilter = filters.find(button => button.dataset.filter === theme) || filters[0];
  if (initialFilter) filterCatalog(initialFilter);

  filters.forEach(button => button.addEventListener('click', () => {
    filterCatalog(button);
    const url = new URL(location.href);
    const filter = button.dataset.filter;
    url.searchParams.delete('tema');
    url.searchParams.delete('formato');
    if (filter === 'impresso') url.searchParams.set('formato', 'impresso');
    else if (filter !== 'todos') url.searchParams.set('tema', filter);
    history.replaceState(history.state, '', url);
  }));
}
