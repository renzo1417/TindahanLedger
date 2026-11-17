/**
 * TindaHan Ledger - Inventory Client-Side Scripts
 * Vertical Slice: static/js/inventory/inventory.js
 */

function sortInventoryRows(mode) {
  const tbody = document.getElementById('inventory-table-body');
  if (!tbody) return;

  const rows = Array.from(tbody.querySelectorAll('tr.inventory-row'));
  if (!rows.length) return;

  rows.sort((a, b) => {
    if (mode === 'low-stock') {
      return Number(a.dataset.stock || 0) - Number(b.dataset.stock || 0);
    }
    if (mode === 'high-margin') {
      return Number(b.dataset.margin || 0) - Number(a.dataset.margin || 0);
    }
    if (mode === 'low-cost') {
      return Number(a.dataset.cost || 0) - Number(b.dataset.cost || 0);
    }
    return Number(a.dataset.index || 0) - Number(b.dataset.index || 0);
  });

  rows.forEach((row) => tbody.appendChild(row));
}

function updateTuboCalculator() {
  const puhunanInput = document.getElementById('calc-puhunan');
  const presyoInput = document.getElementById('calc-presyo');
  const unitsInput = document.getElementById('calc-units');
  const unitTuboEl = document.getElementById('calc-unit-tubo');
  const marginPctEl = document.getElementById('calc-margin-pct');
  const suggestedEl = document.getElementById('calc-suggested-price');

  if (!puhunanInput || !presyoInput || !unitsInput || !unitTuboEl || !marginPctEl || !suggestedEl) {
    return;
  }

  const totalPuhunan = Math.max(0, parseFloat(puhunanInput.value) || 0);
  const sellingPrice = Math.max(0, parseFloat(presyoInput.value) || 0);
  const units = Math.max(1, parseInt(unitsInput.value, 10) || 1);

  const unitCost = totalPuhunan / units;
  const unitTubo = sellingPrice - unitCost;
  const marginPct = unitCost > 0 ? (unitTubo / unitCost) * 100 : 0;
  // Round suggested 20% markup price up to nearest 25 centavos for sari-sari pricing
  const suggestedPrice = Math.ceil(unitCost * 1.2 * 4) / 4;

  const sign = unitTubo >= 0 ? '+' : '-';
  unitTuboEl.textContent = `${sign}₱${Math.abs(unitTubo).toFixed(2)}`;
  unitTuboEl.classList.toggle('positive', unitTubo >= 0);
  unitTuboEl.classList.toggle('negative', unitTubo < 0);

  marginPctEl.textContent = `${marginPct.toFixed(1)}%`;
  suggestedEl.textContent = `₱${suggestedPrice.toFixed(2)}`;
}

document.addEventListener('DOMContentLoaded', () => {
  const sortSelect = document.getElementById('inventory-sort-select');
  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      sortInventoryRows(e.target.value);
    });
  }

  ['calc-puhunan', 'calc-presyo', 'calc-units'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('input', updateTuboCalculator);
    }
  });
  updateTuboCalculator();

  // Focus helper on modal triggers
  window.addEventListener('click', (e) => {
    if (e.target.matches('[onclick*="add-product-modal"]')) {
      setTimeout(() => {
        const input = document.getElementById('id_prod_name');
        if (input) input.focus();
      }, 100);
    }
  });
});
