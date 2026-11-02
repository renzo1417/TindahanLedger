/* Local, fictional demonstrations. Presentation never writes to a server. */
(() => {
  'use strict';
  const root = document.querySelector('.landing-body');
  if (!root) return;

  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  const desktop = '(min-width: 1024px) and (min-height: 700px)';
  const finePointer = '(hover: hover) and (pointer: fine)';
  const header = root.querySelector('.lp-header');
  const ledger = root.querySelector('.lp-ledger');
  const payment = root.querySelector('#demo-payment');
  const receipt = root.querySelector('.lp-receipt');
  const balance = root.querySelector('#demo-balance');
  const recordButton = root.querySelector('#record-payment');
  const stageButtons = [...root.querySelectorAll('[data-stage]')];
  const itemButtons = [...root.querySelectorAll('[data-item]')];
  const extraRows = root.querySelector('.lp-extra-rows');
  const batchList = root.querySelector('.lp-stock-list');
  const expiredItems = root.querySelector('.lp-expired-items');
  const batches = [...batchList.querySelectorAll('[data-batch]')];
  const dayInput = root.querySelector('#stock-days');
  const dayFlow = root.querySelector('.lp-day-flow');
  const BASE_ITEMS = [250, 100];
  const PAYMENT = 150;
  const state = { stage: 'utang', manual: false, order: 'expiry', extras: [], offset: 0 };
  const stageData = {
    utang: { paid: false, caption: 'Bawat utang, may sariling tala.' },
    bayad: { paid: true, caption: 'Bayad na ₱150. Bawas agad sa balanse.' },
    balance: { paid: true, caption: 'Bawat bayad, malinaw ang natitira.' }
  };
  let controller;
  let media;
  let lenis;
  let lenisTick;
  let observer;
  let refreshFrame;
  let flipAnimation;
  let gsapReady = false;
  let introductionPlayed = false;
  let suspended = true;
  let pendingHashAlignment = false;

  const peso = value => `₱${value.toFixed(2)}`;
  const animating = () => gsapReady && !reduce.matches;

  /* ---------- Ledger: one state owner, GSAP animates toward it ---------- */

  function ledgerFigures(stage) {
    const paid = stageData[stage].paid;
    const items = [...BASE_ITEMS, ...state.extras.map(key => Number(itemButtons.find(b => b.dataset.item === key).dataset.amount))];
    const total = items.reduce((sum, value) => sum + value, 0);
    const owed = paid ? total - PAYMENT : total;
    const equation = paid ? `${peso(total)} − ${peso(PAYMENT)} = ${peso(owed)}` : `${items.map(peso).join(' + ')} = ${peso(total)}`;
    let caption = stageData[stage].caption;
    if (state.extras.length) caption = paid ? 'Bawas ang bayad, kasama ang bagong pinamili.' : 'Bawat dagdag na pinamili, kita agad sa balanse.';
    return { paid, owed, equation, caption };
  }

  function clearLedgerMotion() {
    if (!gsapReady) return;
    window.gsap.killTweensOf([payment, receipt, balance]);
    window.gsap.set([payment, receipt, balance], { clearProps: 'opacity,transform,clipPath' });
  }

  function takeManualControl() {
    state.manual = true;
    if (!gsapReady) return;
    const entry = window.ScrollTrigger?.getById('landing-ledger-entry')?.animation;
    if (entry) entry.progress(1);
  }

  function renderLedger(stage, { manual = false, animate = false, announce = false } = {}) {
    const wasPaid = stageData[state.stage].paid;
    const previousAmount = balance.textContent;
    clearLedgerMotion();
    state.stage = stage;
    if (manual) takeManualControl();
    const figures = ledgerFigures(stage);
    ledger.dataset.ledgerStage = stage;
    payment.setAttribute('aria-hidden', String(!figures.paid));
    payment.hidden = !figures.paid;
    root.querySelector('#demo-payment-empty').hidden = figures.paid;
    receipt.classList.toggle('is-unpaid', !figures.paid);
    balance.textContent = peso(figures.owed);
    root.querySelector('#demo-equation').textContent = figures.equation;
    root.querySelector('#demo-caption').textContent = figures.caption;
    root.querySelector('#demo-mode').textContent = state.manual ? 'Ikaw ang may kontrol. Reset para magsimula.' : 'Sample ledger · Demo only';
    stageButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.stage === stage)));
    recordButton.disabled = figures.paid;
    recordButton.replaceChildren(document.createTextNode(figures.paid ? 'Sample payment recorded ✓' : 'Record sample ₱150 payment ↗'));
    if (animate && animating()) {
      const { gsap } = window;
      if (figures.paid && !wasPaid) {
        gsap.from(payment, { y: 6, opacity: 0, duration: 0.26, ease: 'ledger-out' });
        // The slip prints downward out of the register.
        gsap.fromTo(receipt, { clipPath: 'inset(0 0 100% 0)', y: -10 }, { clipPath: 'inset(0 0 0% 0)', y: 0, duration: 0.5, ease: 'ledger-out' });
      }
      if (balance.textContent !== previousAmount) {
        gsap.fromTo(balance, { yPercent: 38, opacity: 0 }, { yPercent: 0, opacity: 1, duration: 0.32, ease: 'ledger-out' });
      }
    }
    if (announce) root.querySelector('#demo-status').textContent = `${figures.caption} Natitirang utang: ${balance.textContent}.`;
  }

  function buildExtraRow(button) {
    const row = document.createElement('div');
    row.className = 'lp-ledger-row lp-extra';
    row.dataset.extra = button.dataset.item;
    const text = document.createElement('div');
    const name = document.createElement('strong');
    name.textContent = button.dataset.name;
    const tag = document.createElement('span');
    tag.className = 'lp-extra-tag';
    tag.textContent = 'BAGO';
    name.append(tag);
    const detail = document.createElement('span');
    detail.textContent = button.dataset.detail;
    text.append(name, detail);
    const amount = document.createElement('span');
    amount.textContent = peso(Number(button.dataset.amount));
    row.append(text, amount);
    return row;
  }

  function toggleItem(button) {
    const key = button.dataset.item;
    const index = state.extras.indexOf(key);
    if (index === -1) {
      state.extras.push(key);
      const row = buildExtraRow(button);
      extraRows.append(row);
      if (animating()) window.gsap.from(row, { height: 0, minHeight: 0, paddingTop: 0, paddingBottom: 0, opacity: 0, duration: 0.34, ease: 'ledger-out', clearProps: 'all' });
    } else {
      state.extras.splice(index, 1);
      const row = extraRows.querySelector(`[data-extra="${key}"]`);
      if (row && animating()) {
        delete row.dataset.extra;
        window.gsap.to(row, { height: 0, minHeight: 0, paddingTop: 0, paddingBottom: 0, opacity: 0, duration: 0.24, ease: 'ledger-out', onComplete: () => row.remove() });
      } else if (row) row.remove();
    }
    button.setAttribute('aria-pressed', String(index === -1));
    renderLedger(state.stage, { manual: true, animate: true, announce: true });
  }

  function resetLedger() {
    state.manual = false;
    state.extras = [];
    if (gsapReady) window.gsap.killTweensOf(extraRows.children);
    extraRows.replaceChildren();
    itemButtons.forEach(button => button.setAttribute('aria-pressed', 'false'));
    renderLedger('utang', { announce: true });
  }

  /* ---------- Stock: simulated days move batches between shelf and segregation ---------- */

  function renderStock({ animate = true, announce = false } = {}) {
    if (flipAnimation) { flipAnimation.progress(1).kill(); flipAnimation = null; }
    const flip = animate && animating() && window.Flip ? window.Flip.getState(batches) : null;
    const remaining = batch => Number(batch.dataset.days) - state.offset;
    const sellable = batches.filter(batch => remaining(batch) > 0).sort((a, b) => state.order === 'expiry'
      ? remaining(a) - remaining(b)
      : Number(a.dataset.arrival) - Number(b.dataset.arrival));
    const expired = batches.filter(batch => remaining(batch) <= 0);
    const soonest = [...sellable].sort((a, b) => remaining(a) - remaining(b))[0];
    const priority = soonest && remaining(soonest) <= 7 ? soonest : null;
    sellable.forEach(batch => batchList.appendChild(batch));
    expired.forEach(batch => expiredItems.appendChild(batch));
    batches.forEach(batch => {
      const days = remaining(batch);
      const isExpired = days <= 0;
      batch.classList.toggle('is-expired', isExpired);
      batch.classList.toggle('lp-batch-priority', batch === priority);
      batch.querySelector('[data-days-label]').textContent = isExpired ? 'Expired na' : `${days} araw pa`;
      const status = batch.querySelector('.lp-batch-status');
      if (isExpired) status.textContent = 'Huwag ibenta';
      else if (batch === priority) {
        status.textContent = 'Unahing ibenta ';
        const arrow = document.createElement('span');
        arrow.setAttribute('aria-hidden', 'true');
        arrow.textContent = '↗';
        status.append(arrow);
      } else status.textContent = 'Susunod';
    });
    root.querySelectorAll('[data-stock-order]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.stockOrder === state.order)));
    if (dayInput) {
      dayInput.value = String(state.offset);
      dayInput.style.setProperty('--fill', `${(state.offset / Number(dayInput.max)) * 100}%`);
      root.querySelector('#stock-days-output').textContent = state.offset ? `+${state.offset} araw` : 'Ngayon';
    }
    let caption = state.order === 'expiry' ? 'Nakaayos mula sa pinakamaagang expiry.' : 'Nakaayos ayon sa pagdating ng mga batch.';
    if (state.offset) caption += ` Pagkalipas ng ${state.offset} araw${expired.length ? `, ${expired.length} batch ang naihiwalay` : ''}.`;
    root.querySelector('#stock-caption').textContent = caption;
    if (announce) root.querySelector('#stock-status').textContent = `${caption} Ang expired na stock ay hiwalay at hindi ibinebenta.`;
    if (flip) {
      flipAnimation = window.Flip.from(flip, {
        duration: 0.42, ease: 'ledger-move', scale: false, nested: true,
        onComplete: () => { flipAnimation = null; scheduleRefresh(); }
      });
    } else scheduleRefresh();
  }

  function sortStock(order) {
    state.order = order;
    renderStock({ announce: true });
  }

  /* ---------- Daily tape: focus a transaction to trace where it lands ---------- */

  function focusTransaction(type) {
    if (type) dayFlow.dataset.focus = type;
    else delete dayFlow.dataset.focus;
  }

  /* ---------- Lifecycle helpers ---------- */

  function scheduleRefresh() {
    cancelAnimationFrame(refreshFrame);
    refreshFrame = requestAnimationFrame(() => {
      if (!suspended && gsapReady) window.ScrollTrigger.refresh();
      if (!suspended && pendingHashAlignment) {
        pendingHashAlignment = false;
        const target = anchorTarget(window.location.hash);
        if (target) scrollToTarget(target, false);
      }
    });
  }

  function stopSmoothScroll() {
    if (lenisTick && window.gsap) window.gsap.ticker.remove(lenisTick);
    if (lenis) lenis.destroy();
    lenis = null;
    lenisTick = null;
  }

  function revealHeading(element, hero = false) {
    const gsap = window.gsap;
    if (!window.SplitText) {
      return gsap.from(element, { y: 14, opacity: 0, duration: 0.55, ease: 'ledger-out', scrollTrigger: hero ? undefined : { trigger: element, start: 'top 90%', once: true } });
    }
    window.SplitText.create(element, {
      type: 'lines', mask: 'lines', autoSplit: true, aria: 'auto',
      onSplit(split) {
        const animation = gsap.from(split.lines, {
          yPercent: 105, duration: 0.62, stagger: hero ? 0.08 : 0.06,
          ease: 'ledger-out',
          scrollTrigger: hero ? undefined : { trigger: element, start: 'top 90%', once: true },
          onComplete: () => { gsap.set(split.lines, { clearProps: 'transform' }); }
        });
        if (hero && introductionPlayed) animation.progress(1);
        return animation;
      }
    });
  }

  /* ---------- Scenes ---------- */

  function setupHero(conditions) {
    const { gsap } = window;
    const figure = root.querySelector('.lp-product-preview');
    const windowFrame = root.querySelector('.lp-preview-window');
    const heroReceipt = root.querySelector('.lp-hero-receipt');
    const heroExpiry = root.querySelector('.lp-hero-expiry');
    if (!introductionPlayed && window.scrollY < 100 && !window.location.hash) {
      revealHeading(root.querySelector('[data-hero-heading]'), true);
      gsap.timeline({ id: 'landing-hero-intro', defaults: { ease: 'ledger-out' } })
        .from('.lp-hero-enter', { y: 14, opacity: 0, duration: 0.5, stagger: 0.08 }, 0)
        .from('.lp-preview-image-wrap', { clipPath: 'inset(0 0 100% 0)', duration: 0.85, ease: 'ledger-move' }, 0.05)
        .from(heroReceipt, { clipPath: 'inset(0 0 100% 0)', y: -14, duration: 0.6 }, 0.55)
        .from(heroExpiry, { x: -22, opacity: 0, duration: 0.55 }, 0.7);
      introductionPlayed = true;
    }
    if (!(conditions.desktop && conditions.fine)) return () => {};
    // Depth layers: the window tilts, artefacts drift at different distances.
    const tiltX = gsap.quickTo(windowFrame, 'rotationX', { duration: 0.6, ease: 'power3.out' });
    const tiltY = gsap.quickTo(windowFrame, 'rotationY', { duration: 0.6, ease: 'power3.out' });
    const receiptX = gsap.quickTo(heroReceipt, 'x', { duration: 0.7, ease: 'power3.out' });
    const receiptY = gsap.quickTo(heroReceipt, 'y', { duration: 0.7, ease: 'power3.out' });
    const expiryX = gsap.quickTo(heroExpiry, 'x', { duration: 0.8, ease: 'power3.out' });
    const expiryY = gsap.quickTo(heroExpiry, 'y', { duration: 0.8, ease: 'power3.out' });
    function move(event) {
      const bounds = figure.getBoundingClientRect();
      const px = gsap.utils.clamp(-1, 1, ((event.clientX - bounds.left) / bounds.width) * 2 - 1);
      const py = gsap.utils.clamp(-1, 1, ((event.clientY - bounds.top) / bounds.height) * 2 - 1);
      tiltY(px * 3.5); tiltX(-py * 2.5);
      receiptX(px * 14); receiptY(py * 10);
      expiryX(px * -10); expiryY(py * -8);
    }
    function leave() { tiltX(0); tiltY(0); receiptX(0); receiptY(0); expiryX(0); expiryY(0); }
    figure.addEventListener('pointermove', move);
    figure.addEventListener('pointerleave', leave);
    return () => {
      figure.removeEventListener('pointermove', move);
      figure.removeEventListener('pointerleave', leave);
      gsap.set([windowFrame, heroReceipt, heroExpiry], { clearProps: 'transform' });
    };
  }

  function setupLedger(conditions) {
    const { gsap } = window;
    revealHeading(root.querySelector('#ledger-title'));
    const scene = root.querySelector('.lp-ledger-scene');
    const purchases = [...root.querySelectorAll('.lp-purchase')];
    const rule = root.querySelector('.lp-balance-rule');
    gsap.timeline({ scrollTrigger: { id: 'landing-ledger-entry', trigger: scene, start: 'top 88%', once: true } })
      .from(ledger, { y: 18, duration: 0.6, ease: 'ledger-out' })
      .from(purchases, { x: -10, duration: 0.42, stagger: 0.07, ease: 'ledger-out' }, 0.1)
      .from(rule, { scaleY: 0, duration: 0.5, ease: 'ledger-out' }, 0.22)
      .from('.lp-ledger-add button', { y: 8, opacity: 0, duration: 0.36, stagger: 0.05, ease: 'ledger-out' }, 0.3);
    if (!conditions.desktop) return () => {};
    const progression = { value: 0 };
    let lastStage = null;
    gsap.timeline({
      scrollTrigger: {
        id: 'landing-ledger',
        trigger: '.lp-ledger-pin',
        start: () => `top top+=${header.offsetHeight + 48}`,
        end: () => `+=${Math.max(640, Math.round(window.innerHeight * 0.9))}`,
        scrub: 0.25,
        invalidateOnRefresh: true
      }
    }).to(progression, {
      value: 1, duration: 1, ease: 'none',
      onUpdate() {
        const next = progression.value < 0.35 ? 'utang' : progression.value < 0.55 ? 'bayad' : 'balance';
        if (next !== lastStage) {
          lastStage = next;
          if (!state.manual) renderLedger(next, { animate: true });
        }
      }
    });
    return () => { gsap.set([ledger, ...purchases, rule], { clearProps: 'opacity,transform,clipPath' }); };
  }

  function setupStock(conditions) {
    const { gsap } = window;
    revealHeading(root.querySelector('#stock-title'));
    const backdrop = root.querySelector('.lp-stock-backdrop');
    const stage = root.querySelector('.lp-stock-stage');
    // The ink surface opens to the viewport edges with a clip, never a stretch.
    let bleed = { left: 0, right: 0 };
    function measure() {
      gsap.set(backdrop, { left: 0, right: 0 });
      const bounds = stage.getBoundingClientRect();
      bleed = { left: bounds.left, right: document.documentElement.clientWidth - bounds.right };
      gsap.set(backdrop, { left: -bleed.left, right: -bleed.right });
    }
    measure();
    const closed = () => `inset(0px ${bleed.right}px 0px ${bleed.left}px round 10px)`;
    gsap.timeline({
      scrollTrigger: {
        id: 'landing-stock-backdrop', trigger: stage,
        start: 'top 85%', end: 'bottom 20%', scrub: 0.3,
        invalidateOnRefresh: true, onRefreshInit: measure
      }
    })
      .fromTo(backdrop, { clipPath: closed }, { clipPath: 'inset(0px 0px 0px 0px round 0px)', duration: 0.3, ease: 'none' })
      .to(backdrop, { clipPath: 'inset(0px 0px 0px 0px round 0px)', duration: 0.4, ease: 'none' })
      .to(backdrop, { clipPath: closed, duration: 0.3, ease: 'none' });
    gsap.timeline({ scrollTrigger: { id: 'landing-stock-assembly', trigger: '.lp-stock-toolbar', start: 'top 90%', once: true }, defaults: { ease: 'ledger-out' } })
      .from('.lp-stock-toolbar', { y: 12, opacity: 0, duration: 0.5 })
      .from('.lp-stock-time', { y: 12, opacity: 0, duration: 0.5 }, 0.08)
      .from('.lp-shelf-art img', { y: conditions.desktop ? 24 : 16, rotation: index => index % 2 ? 5 : -5, opacity: 0, duration: 0.65, stagger: 0.09 }, 0.16)
      .from('.lp-shelf-rule', { scaleX: 0, transformOrigin: 'left', duration: 0.55, stagger: 0.09 }, 0.16)
      .from('.lp-expired-art', { x: -10, opacity: 0, duration: 0.45 }, 0.4);
    return () => { gsap.set(backdrop, { clearProps: 'left,right,clipPath' }); };
  }

  function setupDaily() {
    const { gsap } = window;
    revealHeading(root.querySelector('#daily-title'));
    const timeline = gsap.timeline({ scrollTrigger: { id: 'landing-daily', trigger: '.lp-day-scene', start: 'top 86%', once: true }, defaults: { ease: 'ledger-out' } });
    timeline.from('.lp-tape', { clipPath: 'inset(0 0 100% 0)', duration: 0.85, ease: 'ledger-move' }, 0)
      .from('.lp-tape-row', { y: 12, opacity: 0, duration: 0.45, stagger: 0.09, clearProps: 'opacity,transform' }, 0.18)
      .from('.lp-day-total', { y: 16, opacity: 0, duration: 0.55, stagger: 0.12, clearProps: 'opacity,transform' }, 0.55)
      .from('.lp-day-settlement', { y: 20, opacity: 0, duration: 0.55 }, 0.95);
    if (window.DrawSVGPlugin) timeline.fromTo('.lp-flow-lines path', { drawSVG: '0%' }, {
      drawSVG: '100%', duration: 0.85, stagger: 0.15, ease: 'ledger-move',
      onComplete: () => gsap.set('.lp-flow-lines path', { clearProps: 'strokeDashoffset,strokeDasharray' })
    }, 0.7);
  }

  function setupClosing() {
    const { gsap } = window;
    revealHeading(root.querySelector('#faq-title'));
    gsap.from('.lp-faq-list details', { y: 12, opacity: 0, duration: 0.45, stagger: 0.07, ease: 'ledger-out', scrollTrigger: { id: 'landing-faq', trigger: '.lp-faq-list', start: 'top 90%', once: true } });
    revealHeading(root.querySelector('#closing-title'));
    gsap.timeline({ scrollTrigger: { id: 'landing-closing', trigger: '.lp-closing-inner', start: 'top 90%', once: true }, defaults: { ease: 'ledger-out' } })
      .from('.lp-closing-mark', { x: 28, rotation: -8, opacity: 0, duration: 0.8 })
      .from('.lp-closing-actions', { y: 12, opacity: 0, duration: 0.52 }, 0.18);
  }

  function revealFocusedControl(event) {
    if (!gsapReady) return;
    // Keyboard focus takes precedence over any entrance hiding a live control.
    const scenes = [
      ['.lp-hero-actions', 'landing-hero-intro'],
      ['#ledger-demo', 'landing-ledger-entry'],
      ['#inventory-story', 'landing-stock-assembly'],
      ['#daily-overview', 'landing-daily'],
      ['#faq', 'landing-faq'],
      ['.lp-closing-actions', 'landing-closing']
    ];
    for (const [selector, id] of scenes) {
      if (!event.target.closest(selector)) continue;
      const animation = window.ScrollTrigger.getById(id)?.animation || window.gsap.getById(id);
      if (animation) animation.progress(1);
    }
  }

  function buildMotion() {
    const { gsap, ScrollTrigger } = window;
    if (!gsap || !ScrollTrigger) return;
    gsap.registerPlugin(ScrollTrigger);
    for (const name of ['SplitText', 'Flip', 'DrawSVGPlugin', 'CustomEase']) {
      if (window[name]) gsap.registerPlugin(window[name]);
    }
    const styles = getComputedStyle(root);
    if (window.CustomEase) {
      const bezier = token => styles.getPropertyValue(token).trim().replace('cubic-bezier(', '').replace(')', '');
      window.CustomEase.create('ledger-out', bezier('--ease-out'));
      window.CustomEase.create('ledger-move', bezier('--ease-in-out'));
    } else {
      gsap.registerEase('ledger-out', gsap.parseEase('power3.out'));
      gsap.registerEase('ledger-move', gsap.parseEase('power3.inOut'));
    }
    gsapReady = true;
    media = gsap.matchMedia();
    media.add({ desktop, fine: finePointer, reduce: '(prefers-reduced-motion: reduce)' }, context => {
      const conditions = context.conditions;
      root.dataset.motion = conditions.reduce ? 'reduced' : 'full';
      if (conditions.reduce) {
        renderLedger(state.stage);
        return;
      }
      const cleanups = [];
      cleanups.push(setupHero(conditions));
      cleanups.push(setupLedger(conditions));
      cleanups.push(setupStock(conditions));
      setupDaily();
      setupClosing();
      if (conditions.fine) {
        root.querySelectorAll('[data-magnetic]').forEach(button => {
          const content = button.firstElementChild;
          const x = gsap.quickTo(content, 'x', { duration: 0.2, ease: 'ledger-out' });
          const y = gsap.quickTo(content, 'y', { duration: 0.2, ease: 'ledger-out' });
          function move(event) {
            const bounds = button.getBoundingClientRect();
            x(gsap.utils.clamp(-4, 4, (event.clientX - bounds.left - bounds.width / 2) * 0.08));
            y(gsap.utils.clamp(-4, 4, (event.clientY - bounds.top - bounds.height / 2) * 0.08));
          }
          function leave() { x(0); y(0); }
          button.addEventListener('pointermove', move);
          button.addEventListener('pointerleave', leave);
          button.addEventListener('blur', leave);
          cleanups.push(() => {
            button.removeEventListener('pointermove', move);
            button.removeEventListener('pointerleave', leave);
            button.removeEventListener('blur', leave);
            gsap.killTweensOf(content);
            gsap.set(content, { clearProps: 'transform' });
          });
        });
      }
      if (conditions.desktop && conditions.fine && window.Lenis) {
        lenis = new window.Lenis({ autoRaf: false, lerp: 0.1, smoothWheel: true, syncTouch: false });
        lenis.on('scroll', ScrollTrigger.update);
        lenisTick = time => lenis.raf(time * 1000);
        gsap.ticker.add(lenisTick);
        gsap.ticker.lagSmoothing(0);
      }
      scheduleRefresh();
      return () => {
        cleanups.forEach(cleanup => cleanup());
        stopSmoothScroll();
        if (flipAnimation) { flipAnimation.progress(1).kill(); flipAnimation = null; }
        clearLedgerMotion();
      };
    });
  }

  function anchorTarget(hash) {
    if (!hash) return null;
    try { return document.getElementById(decodeURIComponent(hash.slice(1))); }
    catch { return null; }
  }

  function scrollToTarget(target, focus, smooth = false) {
    const complete = () => {
      if (!focus) return;
      if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
      target.focus({ preventScroll: true });
    };
    const offset = header.offsetHeight + 24;
    const destination = target.getBoundingClientRect().top + window.scrollY - offset;
    // Numeric targets avoid applying CSS scroll-margin/padding a second time.
    if (lenis) lenis.scrollTo(destination, { duration: 0.65, immediate: !smooth, onComplete: complete });
    else { window.scrollTo({ top: destination, behavior: 'instant' }); complete(); }
  }

  function navigateToAnchor(event) {
    const anchor = event.target.closest('a[href^="#"]');
    if (!anchor || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const target = anchorTarget(anchor.getAttribute('href'));
    if (!target) return;
    event.preventDefault();
    const hash = anchor.getAttribute('href');
    if (window.location.hash !== hash) history.pushState(null, '', hash);
    scrollToTarget(target, true, true);
  }

  function suspend() {
    if (suspended) return;
    suspended = true;
    controller.abort();
    if (observer) observer.disconnect();
    cancelAnimationFrame(refreshFrame);
    if (media) media.revert();
    media = null;
    stopSmoothScroll();
    gsapReady = false;
    delete root.dataset.motionReady;
  }

  function start(restored = false) {
    if (!suspended) return;
    suspended = false;
    controller = new AbortController();
    const options = { signal: controller.signal };
    stageButtons.forEach(button => button.addEventListener('click', () => renderLedger(button.dataset.stage, { manual: true, animate: true, announce: true }), options));
    itemButtons.forEach(button => button.addEventListener('click', () => toggleItem(button), options));
    recordButton.addEventListener('click', () => {
      if (stageData[state.stage].paid) return;
      renderLedger('bayad', { manual: true, animate: true, announce: true });
    }, options);
    root.querySelector('#reset-ledger').addEventListener('click', resetLedger, options);
    root.querySelectorAll('[data-stock-order]').forEach(button => button.addEventListener('click', () => sortStock(button.dataset.stockOrder), options));
    if (dayInput) {
      dayInput.addEventListener('input', () => {
        const next = Number(dayInput.value);
        if (next === state.offset) return;
        state.offset = next;
        renderStock();
      }, options);
      dayInput.addEventListener('change', () => renderStock({ animate: false, announce: true }), options);
    }
    root.querySelectorAll('.lp-tape-row').forEach(row => {
      row.addEventListener('pointerenter', () => focusTransaction(row.dataset.transaction), options);
      row.addEventListener('focus', () => focusTransaction(row.dataset.transaction), options);
      row.addEventListener('click', () => focusTransaction(row.dataset.transaction), options);
    });
    dayFlow.addEventListener('pointerleave', event => { if (event.pointerType === 'mouse') focusTransaction(null); }, options);
    dayFlow.addEventListener('focusout', event => { if (!dayFlow.contains(event.relatedTarget)) focusTransaction(null); }, options);
    root.addEventListener('click', navigateToAnchor, options);
    root.addEventListener('focusin', revealFocusedControl, options);
    window.addEventListener('popstate', () => { pendingHashAlignment = Boolean(window.location.hash); scheduleRefresh(); }, options);
    reduce.addEventListener('change', () => renderLedger(state.stage), options);
    root.querySelectorAll('details').forEach(details => details.addEventListener('toggle', scheduleRefresh, options));
    document.addEventListener('visibilitychange', () => {
      if (!gsapReady) return;
      if (document.hidden) clearLedgerMotion();
      else scheduleRefresh();
    }, options);
    root.querySelector('.lp-preview-image-wrap img').addEventListener('load', scheduleRefresh, options);
    if ('IntersectionObserver' in window) {
      observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;
          root.querySelectorAll('.lp-nav a').forEach(anchor => {
            if (anchor.hash === `#${entry.target.id}`) anchor.setAttribute('aria-current', 'location');
            else anchor.removeAttribute('aria-current');
          });
        });
      }, { rootMargin: '-15% 0px -65% 0px', threshold: 0 });
      root.querySelectorAll('.lp-hero,#ledger-demo,#inventory-story,#daily-overview,#faq,.lp-closing').forEach(section => observer.observe(section));
    }
    renderLedger(state.stage);
    renderStock({ animate: false });
    root.querySelectorAll('.lp-stage-controls,.lp-ledger-actions,.lp-ledger-add,.lp-stock-controls,.lp-stock-time,.lp-day-hint').forEach(element => { element.hidden = false; });
    try {
      buildMotion();
    } catch (error) {
      // The page remains usable even if an animation plugin fails to initialize.
      if (media) media.revert();
      media = null;
      stopSmoothScroll();
      gsapReady = false;
      root.dataset.motion = 'fallback';
      console.warn('Landing motion unavailable; using the accessible static presentation.', error);
    }
    root.dataset.motionReady = 'true';
    if (!restored) pendingHashAlignment = Boolean(window.location.hash);
    if (document.fonts) document.fonts.ready.then(() => {
      if (!restored) pendingHashAlignment = Boolean(window.location.hash);
      scheduleRefresh();
    });
    scheduleRefresh();
  }

  window.addEventListener('pagehide', suspend);
  window.addEventListener('pageshow', event => { if (event.persisted) { start(true); scheduleRefresh(); } });
  start();
})();
