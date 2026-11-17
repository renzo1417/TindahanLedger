/* Local, fictional demonstrations matching recreated landing page. Zero server writes. */
(() => {
  'use strict';

  const root = document.querySelector('.landing-body');
  if (!root) return;

  const peso = (val) => `₱${Number(val).toFixed(2)}`;

  /* ---------------- 1. Interactive Split Ledger Window ---------------- */
  const sukiDirectory = {
    rosa: {
      name: 'Aling Rosa',
      avatar: 'R',
      sub: 'Suki sa kanto · Blk 4 Lot 9 · Interactive demo',
      baseItems: [
        { time: '08:30 AM', product: 'Bigas', detail: '5 kg Dinorado', amount: 250 },
        { time: '08:30 AM', product: 'Mga pinamili', detail: 'Sardinas at sabon', amount: 100 },
      ],
      paymentAmount: 150,
      interactive: true,
    },
    maria: {
      name: 'Maria Santos',
      avatar: 'M',
      sub: 'Suki sa kanto · 12 days overdue · Sample view',
      baseItems: [
        { time: 'Oct 28', product: 'Bigas & Groceries', detail: '10 kg Sinandomeng + delata', amount: 1650 },
        { time: 'Nov 02', product: 'Paninda sa kusina', detail: 'Mantika, toyo, kape', amount: 900 },
      ],
      paymentAmount: 200,
      interactive: false,
    },
    pedro: {
      name: 'Pedro Reyes',
      avatar: 'P',
      sub: 'Purok 2 · Active suki · Sample view',
      baseItems: [
        { time: 'Nov 04', product: 'Softdrinks & Ice', detail: '2 cases + yelo', amount: 1200 },
        { time: 'Nov 08', product: 'Cigarettes & Snacks', detail: 'Assorted packs', amount: 600 },
      ],
      paymentAmount: 0,
      interactive: false,
    },
  };

  const ledgerState = {
    activeSuki: 'rosa',
    paid: true,
    extras: [],
    filter: 'all',
    search: '',
  };

  const sukiButtons = [...root.querySelectorAll('[data-suki]')];
  const filterTabs = [...root.querySelectorAll('[data-suki-filter]')];
  const searchInput = root.querySelector('#lp-suki-search');
  const toggleBayadBtn = root.querySelector('#toggle-bayad-state');
  const recordPaymentBtn = root.querySelector('#record-payment');
  const itemChips = [...root.querySelectorAll('[data-item]')];
  const resetBtn = root.querySelector('#reset-ledger');

  function getRosaTotals() {
    const baseTotal = 350;
    const extraTotal = ledgerState.extras.reduce((sum, key) => {
      const chip = itemChips.find((c) => c.dataset.item === key);
      return sum + (chip ? Number(chip.dataset.amount) : 0);
    }, 0);
    const total = baseTotal + extraTotal;
    const paidAmt = ledgerState.paid ? 150 : 0;
    const owed = Math.max(0, total - paidAmt);
    return { total, paidAmt, owed };
  }

  function renderSukiList() {
    const { owed: rosaOwed } = getRosaTotals();
    const rosaAmtEl = root.querySelector('#sidebar-rosa-amt');
    const totalUtangEl = root.querySelector('#sidebar-total-utang');
    if (rosaAmtEl) rosaAmtEl.textContent = peso(rosaOwed);
    if (totalUtangEl) totalUtangEl.textContent = peso(rosaOwed + 2350 + 1800);

    const query = ledgerState.search.trim().toLowerCase();
    sukiButtons.forEach((btn) => {
      const id = btn.dataset.suki;
      const status = btn.dataset.status;
      const name = sukiDirectory[id].name.toLowerCase();
      const matchesFilter = ledgerState.filter === 'all' || status === ledgerState.filter;
      const matchesQuery = !query || name.includes(query);
      btn.hidden = !(matchesFilter && matchesQuery);
      btn.classList.toggle('active', id === ledgerState.activeSuki);
    });
  }

  function renderActiveLedger() {
    const profile = sukiDirectory[ledgerState.activeSuki];
    if (!profile) return;

    const setEl = (sel, text) => {
      const el = root.querySelector(sel);
      if (el) el.textContent = text;
    };

    setEl('#lw-active-avatar', profile.avatar);
    setEl('#lw-active-name', profile.name);
    setEl('#lw-active-sub', profile.sub);

    const rowsContainer = root.querySelector('#lw-rows-container');
    const quickAddWrap = root.querySelector('#lw-quick-add');

    let total = 0;
    let paidAmt = 0;
    let owed = 0;
    let extraRowsHtml = '';

    if (profile.interactive) {
      const totals = getRosaTotals();
      total = totals.total;
      paidAmt = totals.paidAmt;
      owed = totals.owed;
      extraRowsHtml = ledgerState.extras
        .map((key) => {
          const chip = itemChips.find((c) => c.dataset.item === key);
          if (!chip) return '';
          return `
            <div class="lp-lw-row">
              <span class="lp-lw-time">Bagong tala</span>
              <strong>${chip.dataset.name}</strong>
              <span>${chip.dataset.detail}</span>
              <span class="lp-lw-num">${peso(Number(chip.dataset.amount))}</span>
              <span class="lp-lw-num">Utang</span>
            </div>
          `;
        })
        .join('');
    } else {
      total = profile.baseItems.reduce((sum, row) => sum + row.amount, 0);
      paidAmt = profile.paymentAmount;
      owed = Math.max(0, total - paidAmt);
    }

    if (rowsContainer) {
      const baseHtml = profile.baseItems
        .map(
          (row) => `
          <div class="lp-lw-row">
            <span class="lp-lw-time">${row.time}</span>
            <strong>${row.product}</strong>
            <span>${row.detail}</span>
            <span class="lp-lw-num">${peso(row.amount)}</span>
            <span class="lp-lw-num">Utang</span>
          </div>
        `
        )
        .join('');

      const showPaidRow = profile.interactive ? ledgerState.paid : paidAmt > 0;
      const paidHtml = showPaidRow
        ? `
          <div class="lp-lw-row is-paid-row" id="demo-payment">
            <span class="lp-lw-time">04:45 PM</span>
            <strong>✓ Bayad ni ${profile.name.split(' ').pop()}</strong>
            <span>Natanggap ngayong araw</span>
            <span class="lp-lw-num">−${peso(paidAmt)}</span>
            <span class="lp-lw-num">Recorded</span>
          </div>
        `
        : `
          <div class="lp-lw-row" id="demo-payment">
            <span class="lp-lw-time">—</span>
            <strong>Wala pang bayad</strong>
            <span>Buong utang pa ang nakatala</span>
            <span class="lp-lw-num">₱0.00</span>
            <span class="lp-lw-num">Pending</span>
          </div>
        `;

      rowsContainer.innerHTML = `${baseHtml}<div class="lp-extra-rows">${extraRowsHtml}</div>${paidHtml}`;
    }

    setEl('#demo-total-owed', peso(total));
    setEl('#demo-paid-amt', paidAmt > 0 ? `−${peso(paidAmt)}` : '₱0.00');
    setEl('#demo-balance', peso(owed));
    setEl(
      '#demo-equation',
      paidAmt > 0 ? `${peso(total)} − ${peso(paidAmt)} = ${peso(owed)}` : `Walang bayad · ${peso(owed)}`
    );

    if (quickAddWrap) quickAddWrap.style.visibility = profile.interactive ? 'visible' : 'hidden';
    if (toggleBayadBtn) toggleBayadBtn.disabled = !profile.interactive;
    if (recordPaymentBtn) {
      recordPaymentBtn.disabled = !profile.interactive || ledgerState.paid;
      recordPaymentBtn.textContent = profile.interactive
        ? ledgerState.paid
          ? 'Bayad Recorded ✓'
          : 'Record ₱150 Bayad'
        : 'Sample View Only';
    }

    const caption = profile.interactive
      ? ledgerState.paid
        ? 'Bawat bayad, malinaw ang natitira.'
        : 'Wala pang bayad — buong halaga ang utang.'
      : `Preview lamang para kay ${profile.name}. Piliin si Aling Rosa para sa interactive demo.`;
    setEl('#demo-caption', caption);

    renderSukiList();
  }

  sukiButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      ledgerState.activeSuki = btn.dataset.suki;
      renderActiveLedger();
    });
  });

  filterTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      ledgerState.filter = tab.dataset.sukiFilter;
      filterTabs.forEach((t) => t.classList.toggle('active', t === tab));
      renderSukiList();
    });
  });

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      ledgerState.search = searchInput.value;
      renderSukiList();
    });
  }

  if (toggleBayadBtn) {
    toggleBayadBtn.addEventListener('click', () => {
      if (ledgerState.activeSuki !== 'rosa') return;
      ledgerState.paid = !ledgerState.paid;
      renderActiveLedger();
    });
  }

  if (recordPaymentBtn) {
    recordPaymentBtn.addEventListener('click', () => {
      if (ledgerState.activeSuki !== 'rosa') return;
      ledgerState.paid = true;
      renderActiveLedger();
    });
  }

  itemChips.forEach((chip) => {
    chip.addEventListener('click', () => {
      if (ledgerState.activeSuki !== 'rosa') {
        ledgerState.activeSuki = 'rosa';
      }
      const key = chip.dataset.item;
      const idx = ledgerState.extras.indexOf(key);
      if (idx >= 0) {
        ledgerState.extras.splice(idx, 1);
        chip.setAttribute('aria-pressed', 'false');
      } else {
        ledgerState.extras.push(key);
        chip.setAttribute('aria-pressed', 'true');
      }
      renderActiveLedger();
    });
  });

  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      ledgerState.activeSuki = 'rosa';
      ledgerState.paid = true;
      ledgerState.extras = [];
      itemChips.forEach((c) => c.setAttribute('aria-pressed', 'false'));
      renderActiveLedger();
    });
  }

  /* ---------------- 2. Dark FIFO Stock Priority & Time Slider ---------------- */
  const stockCardsWrap = root.querySelector('#lp-stock-cards');
  const stockOrderBtns = [...root.querySelectorAll('[data-stock-order]')];
  const daySlider = root.querySelector('#stock-days');
  const dayOutput = root.querySelector('#stock-days-output');
  let stockOrder = 'expiry';
  let dayOffset = 0;

  function renderStockCards() {
    if (!stockCardsWrap) return;
    const sellableCards = [...stockCardsWrap.querySelectorAll('article[data-batch]')];
    const segregationBox = stockCardsWrap.querySelector('.lp-segregation-box');

    if (dayOutput) {
      dayOutput.textContent = dayOffset === 0 ? 'Ngayon' : `+${dayOffset} araw`;
    }

    sellableCards.forEach((card) => {
      const baseDays = Number(card.dataset.days || 0);
      const remaining = baseDays - dayOffset;
      const numEl = card.querySelector('[data-days-num]');
      const badgeEl = card.querySelector('[data-batch-badge]');

      if (numEl) {
        numEl.textContent = remaining <= 0 ? 'Expired!' : `${remaining} araw`;
      }
      const urgent = remaining <= 7;
      card.classList.toggle('is-priority', urgent);
      if (badgeEl) {
        if (remaining <= 0) {
          badgeEl.textContent = 'Expired na';
          badgeEl.className = 'lp-sc-badge lp-sc-badge-orange';
        } else if (urgent) {
          badgeEl.textContent = 'Unahing Ibenta';
          badgeEl.className = 'lp-sc-badge lp-sc-badge-orange';
        } else if (remaining >= 45) {
          badgeEl.textContent = 'Ligtas';
          badgeEl.className = 'lp-sc-badge lp-sc-badge-green';
        } else {
          badgeEl.textContent = 'Fresh';
          badgeEl.className = 'lp-sc-badge lp-sc-badge-muted';
        }
      }
    });

    sellableCards.sort((a, b) => {
      if (stockOrder === 'arrival') {
        return Number(a.dataset.arrival || 0) - Number(b.dataset.arrival || 0);
      }
      return Number(a.dataset.days || 0) - Number(b.dataset.days || 0);
    });

    sellableCards.forEach((card) => stockCardsWrap.appendChild(card));
    if (segregationBox) stockCardsWrap.appendChild(segregationBox);
  }

  stockOrderBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      stockOrder = btn.dataset.stockOrder;
      stockOrderBtns.forEach((b) => b.setAttribute('aria-pressed', String(b === btn)));
      renderStockCards();
    });
  });

  if (daySlider) {
    daySlider.addEventListener('input', () => {
      dayOffset = Number(daySlider.value);
      renderStockCards();
    });
  }

  /* ---------------- 3. Daily Overview Sales vs Cash Focus ---------------- */
  const tapeRows = [...root.querySelectorAll('.lp-tape-row')];
  const salesTotalCard = root.querySelector('[data-total="sales"]');
  const cashTotalCard = root.querySelector('[data-total="cash"]');

  function focusTapeTransaction(type) {
    tapeRows.forEach((row) => row.classList.toggle('is-active', row.dataset.transaction === type));
    if (salesTotalCard) {
      salesTotalCard.classList.toggle('is-highlighted', type === 'cash' || type === 'credit');
    }
    if (cashTotalCard) {
      cashTotalCard.classList.toggle('is-highlighted', type === 'cash' || type === 'payment');
    }
  }

  tapeRows.forEach((row) => {
    const type = row.dataset.transaction;
    row.addEventListener('mouseenter', () => focusTapeTransaction(type));
    row.addEventListener('focus', () => focusTapeTransaction(type));
    row.addEventListener('click', () => focusTapeTransaction(type));
  });

  const tapeList = root.querySelector('.lp-tape-list');
  if (tapeList) {
    tapeList.addEventListener('mouseleave', () => focusTapeTransaction(null));
  }

  renderActiveLedger();
  renderStockCards();
})();
