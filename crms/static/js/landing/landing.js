const previews = document.querySelectorAll('.fd-dashboard');
previews.forEach(element => {
  const resize = () => element.style.setProperty('--preview-scale', String(element.clientWidth / 1440));
  resize();
  new ResizeObserver(resize).observe(element);
});
document.querySelectorAll('[data-stock-order]').forEach(button => {
  const selected = new URL(location.href).searchParams.get('order') || 'expiry';
  button.setAttribute('aria-pressed', String(button.dataset.stockOrder === selected));
  button.addEventListener('click', () => {
    const url = new URL(location.href);
    url.searchParams.set('order', button.dataset.stockOrder);
    url.hash = 'inventory-story';
    location.assign(url);
  });
});
const menu = document.getElementById('landing-menu');
document.querySelector('[data-open-menu]')?.addEventListener('click', () => menu.showModal());
document.querySelector('[data-close-menu]')?.addEventListener('click', () => menu.close());
menu?.querySelectorAll('a').forEach(link => link.addEventListener('click', () => menu.close()));
