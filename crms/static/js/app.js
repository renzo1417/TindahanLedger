/* Shared controls. Native dialogs provide focus containment and focus restoration. */
window.openModal = (id, instant = false) => { const dialog = document.getElementById(id); if (dialog && !dialog.open) { dialog.dataset.instant = String(instant); dialog.showModal(); window.TindahanMotion?.animateDialogOpen(dialog, instant); } };
window.closeModal = id => document.getElementById(id)?.close();
window.showToast = message => {
  const host = document.getElementById('global-toast-container');
  if (!host) return;
  const toast = document.createElement('div'); toast.className = 'app-toast'; toast.textContent = message;
  host.append(toast);
  if (window.TindahanMotion?.animateToast) window.TindahanMotion.animateToast(toast, 3900);
  else setTimeout(() => toast.remove(), 4200);
};
window.copyTextToClipboard = async (text, message = 'Message copied.') => {
  try { await navigator.clipboard.writeText(text); window.showToast(message); }
  catch { window.showToast('Clipboard unavailable. Select the message and copy it manually.'); }
};
window.togglePassword = (id, button) => {
  const input = document.getElementById(id); if (!input) return;
  input.type = input.type === 'password' ? 'text' : 'password';
  button?.setAttribute('aria-pressed', String(input.type === 'text'));
  button?.querySelector('.eye-open')?.style.setProperty('display', input.type === 'text' ? 'none' : 'block');
  button?.querySelector('.eye-closed')?.style.setProperty('display', input.type === 'text' ? 'block' : 'none');
};
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('dialog[data-auto-open]').forEach(dialog => { dialog.showModal(); window.TindahanMotion?.animateDialogOpen(dialog, false); });
  document.querySelectorAll('[data-modal]').forEach(button => button.addEventListener('click', event => window.openModal(button.dataset.modal, event.detail === 0)));
  document.querySelectorAll('[data-close-dialog]').forEach(button => button.addEventListener('click', () => button.closest('dialog').close()));
  document.querySelectorAll('dialog').forEach(dialog => dialog.addEventListener('click', event => {
    if (event.target !== dialog || !dialog.matches(':modal')) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  }));
  document.querySelectorAll('[data-copy-target]').forEach(button => button.addEventListener('click', () => window.copyTextToClipboard(document.getElementById(button.dataset.copyTarget).value)));
  document.querySelectorAll('[data-print]').forEach(button => button.addEventListener('click', () => window.print()));
  document.addEventListener('keydown', event => {
    if (event.key === 'Tab') {
      const modal = document.querySelector('dialog:modal');
      if (modal) {
        const controls = Array.from(modal.querySelectorAll('a[href],button:not(:disabled),input:not(:disabled):not([type="hidden"]),select:not(:disabled),textarea:not(:disabled),[tabindex="0"]')).filter(node => node.getClientRects().length);
        const first = controls[0], last = controls.at(-1);
        if (controls.length && (event.shiftKey && document.activeElement === first || !event.shiftKey && document.activeElement === last)) { event.preventDefault(); (event.shiftKey ? last : first).focus(); }
      }
    }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k' && document.getElementById('search-modal')) {
      event.preventDefault(); const dialog = document.getElementById('search-modal'); dialog.open ? dialog.close() : window.openModal('search-modal', true);
    }
  });
  document.querySelectorAll('.workspace form:not(#checkout-form)').forEach(form => form.addEventListener('submit', () => {
    if (!form.checkValidity()) return;
    form.querySelectorAll('button[type="submit"]').forEach(button => { button.disabled = true; button.dataset.busy = 'true'; button.setAttribute('aria-busy', 'true'); });
  }));
  window.addEventListener('pageshow', () => document.querySelectorAll('[data-busy]').forEach(button => { button.disabled = false; button.removeAttribute('aria-busy'); delete button.dataset.busy; }));
  const input = document.getElementById('global-search-input'), results = document.getElementById('global-search-results');
  let timer, controller;
  input?.addEventListener('input', () => {
    clearTimeout(timer); controller?.abort();
    const query = input.value.trim(); results.replaceChildren();
    if (!query) { results.textContent = 'Start typing to find a customer or product.'; return; }
    timer = setTimeout(async () => {
      controller = new AbortController(); results.textContent = 'Searching…';
      try {
        const response = await fetch(`${input.dataset.searchUrl}?q=${encodeURIComponent(query)}`, { signal: controller.signal, headers: { Accept: 'application/json' } });
        if (!response.ok) throw new Error();
        const data = await response.json(); results.replaceChildren();
        if (!data.results.length) results.textContent = 'No customers or products match.';
        data.results.forEach(item => { const link = document.createElement('a'), name = document.createElement('strong'), detail = document.createElement('small'); link.href = item.url; name.textContent = item.label; detail.textContent = item.detail; link.append(name, detail); results.append(link); });
        window.TindahanMotion?.animateSearchResults(results);
      } catch (error) { if (error.name !== 'AbortError') results.textContent = 'Search is unavailable. Please try again.'; }
    }, 220);
  });
  const entry = document.getElementById('ledger-entry-form');
  if (entry) {
    const customer = document.getElementById('entry-customer'), amount = entry.querySelector('[name="amount"]');
    const preview = document.getElementById('entry-preview'), note = document.getElementById('entry-preview-note');
    const format = new Intl.NumberFormat('en-PH', { style: 'currency', currency: 'PHP' });
    let previewInitialized = false, lastPreview = '';
    const updatePreview = () => {
      const selected = customer.selectedOptions[0];
      if (!selected?.value || !amount.value) { preview.textContent = '—'; note.textContent = 'Choose a customer and enter an amount.'; lastPreview = preview.textContent; return; }
      const balance = Math.round(Number(selected.dataset.balance) * 100), entered = Math.round(Number(amount.value) * 100);
      if (!Number.isFinite(entered) || entered < 0) { preview.textContent = '—'; note.textContent = 'Enter a valid amount.'; lastPreview = preview.textContent; return; }
      const payment = entry.dataset.kind === 'bayad';
      if (payment) amount.max = (balance / 100).toFixed(2);
      const remaining = payment ? balance - entered : balance + entered;
      preview.textContent = format.format(remaining / 100);
      note.textContent = payment && remaining < 0 ? 'The payment exceeds this customer’s balance.' : `${format.format(balance / 100)} ${payment ? '−' : '+'} ${format.format(entered / 100)} · preview only`;
      if (previewInitialized && preview.textContent !== lastPreview) window.TindahanMotion?.animateValuePulse(preview);
      lastPreview = preview.textContent;
    };
    customer.addEventListener('change', updatePreview); amount.addEventListener('input', updatePreview); updatePreview(); previewInitialized = true;
  }
});
