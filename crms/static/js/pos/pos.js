document.addEventListener('DOMContentLoaded', () => {
  const terminal = document.getElementById('pos-terminal'); if (!terminal) return;
  const catalog = JSON.parse(document.getElementById('pos-catalog-data').textContent);
  const byId = new Map(catalog.map(product => [product.id, product]));
  const cart = new Map(), storageKey = `tindahan-basket-${terminal.dataset.storeId}`;
  let token = terminal.dataset.token, pending = null, busy = false;
  try {
    const saved = JSON.parse(sessionStorage.getItem(storageKey) || 'null');
    if (saved) { token = saved.token || token; pending = saved.pending || null; (saved.items || []).forEach(item => { if (byId.has(item.product_id) && Number.isInteger(item.quantity) && item.quantity > 0) cart.set(item.product_id, item.quantity); }); }
  } catch { /* A malformed local basket never changes saved sales. */ }
  const save = () => { try { sessionStorage.setItem(storageKey, JSON.stringify({ token, items: Array.from(cart, ([product_id, quantity]) => ({ product_id, quantity })), pending })); } catch { /* The terminal remains usable without session storage. */ } };
  const formatter = new Intl.NumberFormat('en-PH', { style: 'currency', currency: 'PHP' });
  const cents = value => Math.round(Number(value || 0) * 100);
  const peso = value => formatter.format(value / 100);
  const total = () => Array.from(cart).reduce((sum, [id, quantity]) => sum + cents(byId.get(id).price) * quantity, 0);
  const basket = document.getElementById('basket-dialog'), small = matchMedia('(max-width:700px)');
  const layoutBasket = () => { if (basket.open) basket.close(); if (!small.matches) basket.setAttribute('open', ''); };
  layoutBasket(); small.addEventListener('change', layoutBasket);
  document.getElementById('open-basket').addEventListener('click', () => { if (!basket.open) basket.showModal(); });
  const errorBox = document.getElementById('checkout-error'), checkoutButton = document.getElementById('checkout-button');
  const cash = document.getElementById('cash-tendered');
  const change = () => { document.getElementById('change-amount').textContent = peso(Math.max(0, cents(cash.value) - total())); };
  const element = (tag, className, text) => { const node = document.createElement(tag); if (className) node.className = className; if (text !== undefined) node.textContent = text; return node; };
  const setQuantity = (id, delta) => {
    if (busy || pending) { errorBox.textContent = 'Retry the interrupted checkout before changing this basket.'; return; }
    const quantity = (cart.get(id) || 0) + delta;
    if (quantity > byId.get(id).stock) { window.showToast('No more sellable stock available for this product.'); return; }
    if (quantity <= 0) cart.delete(id); else cart.set(id, quantity);
    errorBox.textContent = ''; save(); renderBasket();
  };
  function renderBasket() {
    const host = document.getElementById('basket-items'); host.replaceChildren();
    cart.forEach((quantity, id) => {
      const product = byId.get(id), row = element('div', 'basket-row'), description = element('div');
      description.append(element('strong', '', product.name), element('small', '', `${peso(cents(product.price))} × ${quantity}`));
      const controls = element('div', 'quantity-controls');
      for (const delta of [-1, 1]) { const button = element('button', '', delta < 0 ? '−' : '+'); button.type = 'button'; button.setAttribute('aria-label', `${delta < 0 ? 'Remove one' : 'Add one'} ${product.name}`); button.disabled = busy || Boolean(pending); button.addEventListener('click', () => setQuantity(id, delta)); controls.append(button); if (delta < 0) controls.append(element('span', '', quantity)); }
      const value = element('div', 'basket-row-value');
      value.append(element('strong', 'amount', peso(cents(product.price) * quantity)), controls);
      row.append(description, value); host.append(row);
    });
    document.getElementById('basket-empty').hidden = cart.size > 0;
    document.getElementById('basket-count').textContent = Array.from(cart.values()).reduce((a, b) => a + b, 0);
    document.getElementById('basket-summary').textContent = `${Array.from(cart.values()).reduce((a, b) => a + b, 0)} items · ${cart.size} products`;
    document.getElementById('mobile-basket-total').textContent = peso(total());
    document.getElementById('mobile-basket-items').textContent = `${Array.from(cart.values()).reduce((a, b) => a + b, 0)} items in basket`;
    document.getElementById('basket-total').textContent = peso(total());
    checkoutButton.disabled = busy || !cart.size;
    checkoutButton.textContent = busy ? 'Saving sale…' : pending ? 'Retry checkout' : 'Complete sale';
    cash.disabled = busy || Boolean(pending);
    document.querySelectorAll('#checkout-form select,#checkout-form input[type="radio"],#checkout-form input[type="date"]').forEach(input => { input.disabled = busy || Boolean(pending); });
    change();
  }
  function renderCatalog() {
    const query = document.getElementById('pos-search').value.toLowerCase(), category = document.getElementById('pos-category').value;
    const products = catalog.filter(p => (!category || p.category === category) && `${p.name} ${p.sku}`.toLowerCase().includes(query));
    const host = document.getElementById('pos-products'); host.replaceChildren();
    document.getElementById('catalog-count').textContent = `${products.length} product${products.length === 1 ? '' : 's'} · sellable stock only`;
    products.forEach(product => {
      const button = element('button', 'product-tile');
      button.type = 'button'; button.disabled = product.stock <= 0 || cents(product.price) <= 0;
      button.setAttribute('aria-label', `Add ${product.name}, ${peso(cents(product.price))}`);
      const art = element('span', 'product-art'), image = element('img', 'ui-icon');
      image.src = product.image || terminal.dataset.productIcon; image.alt = ''; image.width = 48; image.height = 58; art.append(image);
      const add = element('span', 'add-product'), plus = element('img', 'ui-icon');
      plus.src = terminal.dataset.plusIcon; plus.alt = ''; plus.width = 20; plus.height = 20; add.append(plus);
      button.append(art, element('span', 'product-name', product.name), element('span', 'product-category', product.category), element('span', 'product-price', peso(cents(product.price))), element('span', 'product-stock', `${product.stock} ${product.unit} available`), add);
      button.addEventListener('click', () => setQuantity(product.id, 1)); host.append(button);
    });
    if (!products.length) host.append(element('p', 'quiet-empty', 'No products match. Add inventory or change your search.'));
  }
  document.getElementById('pos-search').addEventListener('input', renderCatalog);
  document.getElementById('pos-category').addEventListener('change', renderCatalog);
  document.querySelectorAll('[data-pos-category]').forEach(button => button.addEventListener('click', () => {
    document.getElementById('pos-category').value = button.dataset.posCategory;
    document.querySelectorAll('[data-pos-category]').forEach(tab => tab.setAttribute('aria-pressed', String(tab === button)));
    renderCatalog();
  }));
  cash.addEventListener('input', change);
  document.getElementById('exact-amount').addEventListener('click', () => { if (!pending && !busy) { cash.value = (total() / 100).toFixed(2); change(); } });
  document.getElementById('clear-basket').addEventListener('click', () => { if (pending || busy) { errorBox.textContent = 'Retry the interrupted checkout before clearing this basket.'; return; } cart.clear(); cash.value = ''; save(); renderBasket(); });
  function paymentMode() { const credit = document.querySelector('[name="payment_method"]:checked').value === 'Utang'; document.getElementById('cash-fields').hidden = credit; document.getElementById('credit-fields').hidden = !credit; }
  document.querySelectorAll('[name="payment_method"]').forEach(input => input.addEventListener('change', paymentMode));
  if (pending) { document.querySelector(`[name="payment_method"][value="${pending.payment_method === 'Utang' ? 'Utang' : 'Cash'}"]`).checked = true; cash.value = pending.cash_tendered; document.getElementById('pos-customer').value = pending.customer_id || ''; document.getElementById('pos-due-date').value = pending.due_date || ''; errorBox.textContent = 'An interrupted checkout is ready to retry. Its token prevents duplicate sales.'; }
  document.getElementById('checkout-form').addEventListener('submit', async event => {
    event.preventDefault(); if (busy || !cart.size) return;
    const payload = pending || { token, payment_method: document.querySelector('[name="payment_method"]:checked').value,
      cash_tendered: cash.value || '0', customer_id: document.getElementById('pos-customer').value,
      due_date: document.getElementById('pos-due-date').value,
      items: Array.from(cart, ([product_id, quantity]) => ({ product_id, quantity })) };
    pending = payload; busy = true; save(); renderBasket(); errorBox.textContent = '';
    let completed = false;
    try {
      const response = await fetch(terminal.dataset.checkoutUrl, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json', 'X-CSRFToken': document.querySelector('#checkout-form [name="csrfmiddlewaretoken"]').value }, body: JSON.stringify(payload) });
      if (response.status >= 500) throw new Error('Connection interrupted. Retry this checkout; it will not create a duplicate sale.');
      if (response.redirected) throw new Error('Your session ended. Sign in again, then return to retry this basket.');
      const data = await response.json();
      if (!response.ok) { pending = null; throw new Error(data.error || 'The sale was not saved. Review the basket and try again.'); }
      try { sessionStorage.removeItem(storageKey); } catch { /* No saved basket. */ }
      completed = true;
      window.location.assign(data.receipt_url);
    } catch (error) { errorBox.textContent = error.message || 'Connection interrupted. Retry this checkout.'; }
    finally { busy = false; if (!completed) { save(); renderBasket(); } }
  });
  paymentMode(); renderCatalog(); renderBasket();
});
