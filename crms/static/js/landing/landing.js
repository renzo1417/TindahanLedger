const previews = document.querySelectorAll('.fd-dashboard');
previews.forEach(element => {
  const resize = () => element.style.setProperty('--preview-scale', String(element.clientWidth / 1440));
  resize();
  new ResizeObserver(resize).observe(element);
});

const bindStockOrderControls = (root = document) => {
  const section = document.getElementById('inventory-story');
  const selected = new URL(location.href).searchParams.get('order') === 'arrival' ? 'arrival' : 'expiry';
  root.querySelectorAll('[data-stock-order]').forEach(button => {
    button.setAttribute('aria-pressed', String(button.dataset.stockOrder === selected));
    button.addEventListener('click', async () => {
      const nextOrder = button.dataset.stockOrder === 'arrival' ? 'arrival' : 'expiry';
      if (button.getAttribute('aria-pressed') === 'true') return;
      const url = new URL(location.href);
      url.searchParams.set('order', nextOrder);
      url.hash = 'inventory-story';
      if (!section || typeof fetch !== 'function') {
        location.assign(url);
        return;
      }
      try {
        const useFlip = Boolean(window.Flip && window.TindahanMotion?.captureLandingStockFlip);
        const outPromise = useFlip
          ? Promise.resolve()
          : window.TindahanMotion?.animateLandingStockOut(section.querySelector('.fd-149_4351'));
        const [response] = await Promise.all([
          fetch(url.toString(), { headers: { 'X-Requested-With': 'fetch' } }),
          outPromise
        ]);
        if (!response.ok) throw new Error('Failed to load stock order');
        const html = await response.text();
        const doc = new DOMParser().parseFromString(html, 'text/html');
        const nextSection = doc.getElementById('inventory-story');
        if (!nextSection) throw new Error('Missing inventory section');
        const flipState = useFlip ? window.TindahanMotion.captureLandingStockFlip(section) : null;
        section.innerHTML = nextSection.innerHTML;
        history.replaceState(null, '', url.toString());
        bindStockOrderControls(section);
        if (window.TindahanMotion?.playLandingStockFlip) {
          window.TindahanMotion.playLandingStockFlip(section, flipState);
        } else {
          window.TindahanMotion?.animateLandingStockIn(section);
        }
      } catch {
        location.assign(url);
      }
    });
  });
};
bindStockOrderControls();

const menu = document.getElementById('landing-menu');
document.querySelector('[data-open-menu]')?.addEventListener('click', () => {
  menu.showModal();
  window.TindahanMotion?.animateDialogOpen(menu, false);
});
document.querySelector('[data-close-menu]')?.addEventListener('click', () => menu.close());
menu?.querySelectorAll('a').forEach(link => link.addEventListener('click', () => menu.close()));
