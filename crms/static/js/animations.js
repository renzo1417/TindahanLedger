(() => {
  'use strict';

  const noop = () => {};
  const noopApi = {
    animateDialogOpen: noop,
    animateToast: (el, holdMs = 3900) => {
      if (el) setTimeout(() => el.remove(), holdMs + 300);
    },
    animateSearchResults: noop,
    animatePosTiles: noop,
    animatePosAddFeedback: noop,
    animatePosFlyToBasket: noop,
    animatePosBasketUpdate: noop,
    animatePosPaymentSwitch: noop,
    animateValuePulse: noop,
    animateShake: noop,
    animateRegisterStep: (outEl, inEl, _dir, onSwapped) => {
      if (outEl) outEl.classList.add('form-step-hidden');
      if (inEl) inEl.classList.remove('form-step-hidden');
      if (typeof onSwapped === 'function') onSwapped();
    },
    animateStrengthBar: (fillEl, ratio, color) => {
      if (!fillEl) return;
      fillEl.style.backgroundColor = color;
      fillEl.style.width = `${Math.round(ratio * 100)}%`;
    },
    animateLandingStockOut: () => Promise.resolve(),
    animateLandingStockIn: noop,
    captureLandingStockFlip: () => null,
    playLandingStockFlip: noop
  };

  if (typeof window.gsap === 'undefined') {
    window.TindahanMotion = noopApi;
    return;
  }

  const isEmbeddedPreview = () => {
    try {
      return window.self !== window.top;
    } catch {
      return true;
    }
  };

  const gsap = window.gsap;
  if (!isEmbeddedPreview()) {
    if (window.ScrollTrigger) gsap.registerPlugin(window.ScrollTrigger);
    if (window.Flip) gsap.registerPlugin(window.Flip);
  }

  gsap.defaults({ ease: 'power3.out', duration: 0.36 });

  const prefersReducedMotion = () =>
    window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const cap = (elements, limit = 12) =>
    gsap.utils
      .toArray(elements)
      .filter((el) => el && el.isConnected && el.getClientRects().length > 0)
      .slice(0, limit);

  const findNumericTextNode = (el) => {
    for (const node of el.childNodes) {
      if (node.nodeType === Node.TEXT_NODE && /\d/.test(node.nodeValue || '')) {
        return node;
      }
    }
    return null;
  };

  const animateNumericText = (el, duration = 0.48) => {
    if (!el || prefersReducedMotion() || el.dataset.gsapCounted === '1') return;
    const textNode = findNumericTextNode(el);
    if (!textNode) return;
    const originalText = textNode.nodeValue || '';
    if (originalText.includes('—')) return;
    const match = originalText.match(/^([^\d]*?)([\d,]+(?:\.\d+)?)([^\d]*)$/);
    if (!match) return;

    const [, prefix, numStr, suffix] = match;
    const hasCommas = numStr.includes(',');
    const dotIdx = numStr.indexOf('.');
    const decimals = dotIdx === -1 ? 0 : numStr.length - dotIdx - 1;
    const targetValue = Number(numStr.replace(/,/g, ''));
    if (!Number.isFinite(targetValue) || targetValue === 0) return;

    const formatter = hasCommas
      ? new Intl.NumberFormat('en-US', {
          minimumFractionDigits: decimals,
          maximumFractionDigits: decimals
        })
      : null;

    el.dataset.gsapCounted = '1';
    const counter = { val: 0 };
    gsap.to(counter, {
      val: targetValue,
      duration,
      ease: 'power2.out',
      onUpdate: () => {
        const formatted = formatter ? formatter.format(counter.val) : counter.val.toFixed(decimals);
        textNode.nodeValue = `${prefix}${formatted}${suffix}`;
      },
      onComplete: () => {
        textNode.nodeValue = originalText;
      }
    });
  };

  /* ------------------------------------------------------------------------
     Imperative Interaction Hooks
     ------------------------------------------------------------------------ */

  const animateDialogOpen = (dialog, instant = false) => {
    if (!dialog || instant || prefersReducedMotion()) return;
    gsap.killTweensOf(dialog);
    if (dialog.id === 'basket-dialog' && window.matchMedia('(max-width: 700px)').matches) {
      gsap.fromTo(
        dialog,
        { y: 28, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.26, ease: 'power3.out', clearProps: 'transform,opacity' }
      );
      return;
    }
    if (dialog.id === 'landing-menu') {
      gsap.fromTo(
        dialog,
        { y: -12, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.24, ease: 'power3.out', clearProps: 'transform,opacity' }
      );
      return;
    }
    gsap.fromTo(
      dialog,
      { y: 12, scale: 0.97, opacity: 0 },
      { y: 0, scale: 1, opacity: 1, duration: 0.24, ease: 'power3.out', clearProps: 'transform,opacity' }
    );
  };

  const animateToast = (toastEl, holdMs = 3900) => {
    if (!toastEl) return;
    if (prefersReducedMotion()) {
      setTimeout(() => toastEl.remove(), holdMs + 300);
      return;
    }
    gsap.killTweensOf(toastEl);
    const tl = gsap.timeline();
    tl.fromTo(
      toastEl,
      { y: 14, scale: 0.96, opacity: 0 },
      { y: 0, scale: 1, opacity: 1, duration: 0.26, ease: 'power3.out' }
    ).to(
      toastEl,
      {
        y: 8,
        opacity: 0,
        duration: 0.22,
        ease: 'power2.in',
        onComplete: () => toastEl.remove()
      },
      `+=${holdMs / 1000}`
    );
  };

  const animateSearchResults = (container) => {
    if (!container || prefersReducedMotion()) return;
    const links = cap(container.querySelectorAll('a'), 10);
    if (!links.length) return;
    gsap.fromTo(
      links,
      { y: 6, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.2, stagger: 0.025, ease: 'power2.out', overwrite: true, clearProps: 'transform,opacity' }
    );
  };

  const animatePosTiles = (container) => {
    if (!container || prefersReducedMotion()) return;
    const tiles = cap(container.querySelectorAll('.product-tile'), 12);
    if (!tiles.length) return;
    gsap.fromTo(
      tiles,
      { y: 8, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.22, stagger: 0.02, ease: 'power2.out', overwrite: true, clearProps: 'transform,opacity' }
    );
  };

  const animatePosAddFeedback = (tileEl) => {
    if (!tileEl || prefersReducedMotion()) return;
    const badge = tileEl.querySelector('.add-product');
    if (!badge) return;
    gsap.fromTo(
      badge,
      { scale: 0.86 },
      { scale: 1, duration: 0.22, ease: 'back.out(2)', overwrite: true, clearProps: 'transform' }
    );
  };

  const animatePosFlyToBasket = (sourceTile) => {
    if (!sourceTile || prefersReducedMotion()) return;
    const srcImg = sourceTile.querySelector('.product-art img');
    const isMobile = window.matchMedia && window.matchMedia('(max-width: 700px)').matches;
    const target = isMobile
      ? document.getElementById('open-basket') || document.querySelector('.mobile-basket-bar')
      : document.getElementById('basket-total') || document.getElementById('basket-title');
    if (!srcImg || !target) return;

    const fromRect = srcImg.getBoundingClientRect();
    const toRect = target.getBoundingClientRect();
    if (!fromRect.width || !fromRect.height || !toRect.width || !toRect.height) return;

    const ghost = srcImg.cloneNode(false);
    ghost.setAttribute('aria-hidden', 'true');
    ghost.style.position = 'fixed';
    ghost.style.left = `${fromRect.left}px`;
    ghost.style.top = `${fromRect.top}px`;
    ghost.style.width = `${fromRect.width}px`;
    ghost.style.height = `${fromRect.height}px`;
    ghost.style.pointerEvents = 'none';
    ghost.style.zIndex = '90';
    ghost.style.margin = '0';
    ghost.style.willChange = 'transform, opacity';
    document.body.appendChild(ghost);

    const dx = toRect.left + toRect.width * 0.5 - (fromRect.left + fromRect.width * 0.5);
    const dy = toRect.top + toRect.height * 0.5 - (fromRect.top + fromRect.height * 0.5);
    const arcY = Math.min(0, dy) - 48;

    gsap
      .timeline({
        onComplete: () => {
          ghost.remove();
          gsap
            .timeline()
            .to(target, { scaleX: 1.06, scaleY: 0.94, duration: 0.06, ease: 'power1.out', overwrite: true })
            .to(target, { scaleX: 1, scaleY: 1, duration: 0.16, ease: 'back.out(2)', clearProps: 'transform' });
        }
      })
      .to(ghost, { x: dx, duration: 0.34, ease: 'power2.inOut' }, 0)
      .to(ghost, { y: arcY, duration: 0.15, ease: 'power2.out' }, 0)
      .to(ghost, { y: dy, duration: 0.19, ease: 'power2.in' }, 0.15)
      .to(ghost, { scale: 1.08, duration: 0.14, ease: 'power2.out' }, 0)
      .to(ghost, { scale: 0.38, opacity: 0.2, duration: 0.2, ease: 'power2.in' }, 0.14)
      .to(ghost, { rotation: dx >= 0 ? 14 : -14, duration: 0.34, ease: 'power1.inOut' }, 0);
  };

  const animatePosBasketUpdate = ({ rowEl, isNew, totalEls } = {}) => {
    if (prefersReducedMotion()) return;
    if (rowEl && isNew) {
      gsap.fromTo(
        rowEl,
        { y: -6, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.22, ease: 'power2.out', overwrite: true, clearProps: 'transform,opacity' }
      );
    } else if (rowEl) {
      const amount = rowEl.querySelector('.amount');
      if (amount) {
        gsap.fromTo(
          amount,
          { scale: 1.05 },
          { scale: 1, duration: 0.18, ease: 'power2.out', overwrite: true, clearProps: 'transform' }
        );
      }
    }
    if (Array.isArray(totalEls)) {
      const targets = totalEls.filter(Boolean);
      if (targets.length) {
        gsap.fromTo(
          targets,
          { scale: 1.04 },
          { scale: 1, duration: 0.2, ease: 'power2.out', overwrite: true, clearProps: 'transform' }
        );
      }
    }
  };

  const animatePosPaymentSwitch = (visiblePanel) => {
    if (!visiblePanel || prefersReducedMotion()) return;
    gsap.fromTo(
      visiblePanel,
      { y: 6, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.22, ease: 'power2.out', overwrite: true, clearProps: 'transform,opacity' }
    );
  };

  const animateValuePulse = (el) => {
    if (!el || prefersReducedMotion()) return;
    gsap.fromTo(
      el,
      { scale: 1.04, opacity: 0.72 },
      { scale: 1, opacity: 1, duration: 0.2, ease: 'power2.out', overwrite: true, clearProps: 'transform,opacity' }
    );
  };

  const animateShake = (el) => {
    if (!el || prefersReducedMotion()) return;
    gsap.killTweensOf(el, 'x');
    gsap
      .timeline()
      .to(el, { x: -5, duration: 0.055, ease: 'power1.inOut' })
      .to(el, { x: 5, duration: 0.065, ease: 'power1.inOut' })
      .to(el, { x: -4, duration: 0.06, ease: 'power1.inOut' })
      .to(el, { x: 3, duration: 0.055, ease: 'power1.inOut' })
      .to(el, { x: 0, duration: 0.06, ease: 'power2.out', clearProps: 'transform' });
  };

  const animateRegisterStep = (outEl, inEl, direction = 1, onSwapped, activeDot) => {
    if (!outEl || !inEl) return;
    if (prefersReducedMotion()) {
      outEl.classList.add('form-step-hidden');
      inEl.classList.remove('form-step-hidden');
      if (typeof onSwapped === 'function') onSwapped();
      return;
    }

    gsap.killTweensOf([outEl, inEl]);
    gsap.to(outEl, {
      x: -14 * direction,
      opacity: 0,
      duration: 0.17,
      ease: 'power2.in',
      onComplete: () => {
        outEl.classList.add('form-step-hidden');
        gsap.set(outEl, { clearProps: 'transform,opacity' });
        inEl.classList.remove('form-step-hidden');
        if (typeof onSwapped === 'function') onSwapped();
        gsap.fromTo(
          inEl,
          { x: 14 * direction, opacity: 0 },
          { x: 0, opacity: 1, duration: 0.26, ease: 'power3.out', clearProps: 'transform,opacity' }
        );
        if (activeDot) {
          gsap.fromTo(
            activeDot,
            { scale: 0.94 },
            { scale: 1, duration: 0.22, ease: 'power2.out', clearProps: 'transform' }
          );
        }
      }
    });
  };

  const animateStrengthBar = (fillEl, ratio, color) => {
    if (!fillEl) return;
    const clamped = gsap.utils.clamp(0, 1, Number(ratio) || 0);
    if (prefersReducedMotion() || !document.documentElement.classList.contains('gsap-motion')) {
      fillEl.style.backgroundColor = color;
      if (document.documentElement.classList.contains('gsap-motion')) {
        fillEl.style.transform = `scaleX(${clamped})`;
      } else {
        fillEl.style.width = `${Math.round(clamped * 100)}%`;
      }
      return;
    }
    gsap.to(fillEl, {
      scaleX: clamped,
      backgroundColor: color,
      duration: 0.28,
      ease: 'power2.out',
      overwrite: 'auto'
    });
  };

  const animateLandingStockOut = (panelEl) => {
    if (!panelEl || prefersReducedMotion()) return Promise.resolve();
    return new Promise((resolve) => {
      gsap.to(panelEl, {
        opacity: 0.35,
        y: 6,
        duration: 0.14,
        ease: 'power2.in',
        overwrite: true,
        onComplete: resolve
      });
    });
  };

  const animateLandingStockIn = (sectionEl) => {
    if (!sectionEl) return;
    if (!prefersReducedMotion()) {
      const cards = gsap.utils.toArray(
        sectionEl.querySelectorAll('.fd-149_4352, .fd-149_4378, .fd-149_4396, .fd-149_4417')
      );
      if (cards.length) {
        gsap.fromTo(
          cards,
          { y: 12, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 0.32,
            stagger: 0.055,
            ease: 'power3.out',
            overwrite: true,
            clearProps: 'transform,opacity'
          }
        );
      }
    }
    if (window.ScrollTrigger) {
      window.ScrollTrigger.refresh();
    }
  };

  const tagStockFlipCards = (sectionEl) => {
    if (!sectionEl) return [];
    const cards = [];
    const featured = sectionEl.querySelector('.fd-149_4352');
    if (featured) {
      const name = (featured.querySelector('.fd-149_4366')?.textContent || '').trim();
      const qty = (featured.querySelector('.fd-149_4368')?.textContent || '').replace(/\s*na natitira\s*$/i, '').trim();
      if (name) {
        featured.dataset.flipId = `${name}|${qty}`;
        cards.push(featured);
      }
    }
    const cardA = sectionEl.querySelector('.fd-149_4378');
    if (cardA) {
      const name = (cardA.querySelector('.fd-149_4389')?.textContent || '').trim();
      const qty = (cardA.querySelector('.fd-149_4390')?.textContent || '').trim();
      if (name) {
        cardA.dataset.flipId = `${name}|${qty}`;
        cards.push(cardA);
      }
    }
    const cardB = sectionEl.querySelector('.fd-149_4396');
    if (cardB) {
      const name = (cardB.querySelector('.fd-149_4410')?.textContent || '').trim();
      const qty = (cardB.querySelector('.fd-149_4411')?.textContent || '').trim();
      if (name) {
        cardB.dataset.flipId = `${name}|${qty}`;
        cards.push(cardB);
      }
    }
    return cards;
  };

  const captureLandingStockFlip = (sectionEl) => {
    if (!sectionEl || prefersReducedMotion() || !window.Flip) return null;
    const cards = tagStockFlipCards(sectionEl);
    return cards.length ? window.Flip.getState(cards) : null;
  };

  const playLandingStockFlip = (sectionEl, flipState) => {
    if (!sectionEl) return;
    if (flipState && window.Flip && !prefersReducedMotion()) {
      const newCards = tagStockFlipCards(sectionEl);
      window.Flip.from(flipState, {
        targets: newCards,
        duration: 0.54,
        ease: 'power3.inOut',
        scale: true,
        simple: true,
        prune: true,
        onComplete: () => {
          gsap.set(newCards, { clearProps: 'transform,opacity' });
          if (window.ScrollTrigger) window.ScrollTrigger.refresh();
        }
      });
      const art = sectionEl.querySelector('.fd-149_4357');
      if (art) {
        gsap.fromTo(
          art,
          { rotation: -6, y: 6 },
          { rotation: 0, y: 0, duration: 0.38, ease: 'back.out(1.7)', overwrite: true, clearProps: 'transform' }
        );
      }
      const arrow = sectionEl.querySelector('.fd-149_4374');
      if (arrow) {
        gsap.fromTo(
          arrow,
          { x: -8 },
          { x: 0, duration: 0.32, ease: 'power2.out', overwrite: true, clearProps: 'transform' }
        );
      }
      return;
    }
    animateLandingStockIn(sectionEl);
  };

  window.TindahanMotion = {
    animateDialogOpen,
    animateToast,
    animateSearchResults,
    animatePosTiles,
    animatePosAddFeedback,
    animatePosFlyToBasket,
    animatePosBasketUpdate,
    animatePosPaymentSwitch,
    animateValuePulse,
    animateShake,
    animateRegisterStep,
    animateStrengthBar,
    animateLandingStockOut,
    animateLandingStockIn,
    captureLandingStockFlip,
    playLandingStockFlip
  };

  /* ------------------------------------------------------------------------
     Page Choreographies
     ------------------------------------------------------------------------ */

  const initLanding = (mm) => {
    const page = document.querySelector('.fd-page');
    if (!page) return;

    mm.add(
      {
        motionOk: '(prefers-reduced-motion: no-preference)',
        isDesktop: '(min-width: 1024px)',
        finePointer: '(hover: hover) and (pointer: fine)'
      },
      (context) => {
        const { motionOk, isDesktop, finePointer } = context.conditions;
        if (!motionOk) return;

        const cleanups = [];

        // 1. Hero Entrance Timeline
        const heroTl = gsap.timeline({ defaults: { ease: 'power3.out' } });
        const header = page.querySelector('.fd-149_4204');
        const headlineRows = page.querySelectorAll('.fd-149_4220, .fd-149_4225, .fd-149_4231');
        const talaWord = page.querySelector('.fd-149_4221');
        const pesoBadge = page.querySelector('.fd-149_4222');
        const ayosWord = page.querySelector('.fd-149_4226');
        const boxBadge = page.querySelector('.fd-149_4227');
        const checkBadge = page.querySelector('.fd-149_4233');
        const checkIcon = page.querySelector('.fd-149_4234');
        const heroSub = page.querySelectorAll('.fd-149_4237, .fd-149_4238, .fd-149_4241');
        const browserFrame = page.querySelector('.fd-149_4246');
        const previewNote = page.querySelector('.fd-149_4268');

        const hopPeak = isDesktop ? -34 : -22;
        const hopMid = isDesktop ? -26 : -17;
        const pesoStartX =
          talaWord && pesoBadge
            ? gsap.utils.clamp(
                -320,
                -52,
                talaWord.getBoundingClientRect().left -
                  pesoBadge.getBoundingClientRect().left +
                  pesoBadge.getBoundingClientRect().width * 0.2
              )
            : -160;
        const boxStartX =
          ayosWord && boxBadge
            ? gsap.utils.clamp(
                -320,
                -52,
                ayosWord.getBoundingClientRect().left -
                  boxBadge.getBoundingClientRect().left +
                  boxBadge.getBoundingClientRect().width * 0.2
              )
            : -160;

        if (pesoBadge) {
          gsap.set(pesoBadge, {
            x: pesoStartX,
            y: hopPeak - 14,
            scale: 0.72,
            rotation: -35,
            opacity: 0,
            zIndex: 3
          });
        }
        if (boxBadge) {
          gsap.set(boxBadge, {
            x: boxStartX,
            y: -10,
            rotation: -360,
            scale: 0.78,
            opacity: 0,
            zIndex: 3
          });
        }
        if (checkBadge) {
          gsap.set(checkBadge, {
            y: -26,
            scale: 1.32,
            rotation: -18,
            opacity: 0,
            zIndex: 3
          });
        }
        if (checkIcon) {
          gsap.set(checkIcon, { scale: 0.35, rotation: -20 });
        }

        if (header) {
          heroTl.from(header, { y: -12, opacity: 0, duration: 0.42, clearProps: 'transform,opacity' });
        }
        if (headlineRows.length) {
          heroTl.from(
            headlineRows,
            { y: 20, opacity: 0, duration: 0.45, stagger: 0.08, clearProps: 'transform,opacity' },
            '-=0.26'
          );
        }
        heroTl.addLabel('rowsIn');

        let badgesReady = false;
        const badgesTl = gsap.timeline({
          onComplete: () => {
            badgesReady = true;
          }
        });

        if (pesoBadge) {
          const pesoTl = gsap.timeline();
          pesoTl
            .to(pesoBadge, { x: 0, duration: 0.72, ease: 'power1.out' }, 0)
            .to(pesoBadge, { rotation: 360, duration: 0.72, ease: 'power2.out' }, 0)
            .to(pesoBadge, { opacity: 1, scale: 1, duration: 0.13, ease: 'power2.out' }, 0)
            .to(pesoBadge, { y: -8, duration: 0.15, ease: 'power2.in' }, 0)
            .to(pesoBadge, { scaleX: 1.16, scaleY: 0.84, duration: 0.05, ease: 'power1.out' }, 0.14)
            .to(pesoBadge, { y: hopPeak, scaleX: 0.94, scaleY: 1.06, duration: 0.15, ease: 'power2.out' }, 0.19)
            .to(pesoBadge, { y: -6, scaleX: 1, scaleY: 1, duration: 0.14, ease: 'power2.in' }, 0.34)
            .to(pesoBadge, { scaleX: 1.12, scaleY: 0.88, duration: 0.045, ease: 'power1.out' }, 0.47)
            .to(pesoBadge, { y: hopMid, scaleX: 0.96, scaleY: 1.04, duration: 0.12, ease: 'power2.out' }, 0.515)
            .to(pesoBadge, { y: 0, scaleX: 1.08, scaleY: 0.92, duration: 0.11, ease: 'power2.in' }, 0.635)
            .to(
              pesoBadge,
              { scaleX: 1, scaleY: 1, duration: 0.16, ease: 'back.out(2.2)', clearProps: 'transform,opacity,zIndex' },
              0.745
            );
          badgesTl.add(pesoTl, 0);
        }

        if (boxBadge) {
          const boxTl = gsap.timeline();
          boxTl
            .to(boxBadge, { opacity: 1, scale: 1, duration: 0.16, ease: 'power2.out' }, 0)
            .to(boxBadge, { x: 0, rotation: 0, duration: 0.66, ease: 'power2.out' }, 0)
            .to(boxBadge, { y: -14, duration: 0.14, ease: 'sine.out' }, 0.04)
            .to(boxBadge, { y: -2, duration: 0.14, ease: 'sine.in' }, 0.18)
            .to(boxBadge, { y: -11, duration: 0.14, ease: 'sine.out' }, 0.32)
            .to(boxBadge, { y: 0, duration: 0.16, ease: 'power2.in' }, 0.46)
            .to(boxBadge, { scaleX: 1.12, scaleY: 0.88, duration: 0.06, ease: 'power1.out' }, 0.62)
            .to(
              boxBadge,
              { scaleX: 1, scaleY: 1, duration: 0.18, ease: 'back.out(2)', clearProps: 'transform,opacity,zIndex' },
              0.68
            );
          badgesTl.add(boxTl, 0.24);
        }

        if (checkBadge) {
          const checkTl = gsap.timeline();
          checkTl.to(
            checkBadge,
            { y: 0, scale: 1, rotation: 0, opacity: 1, duration: 0.34, ease: 'back.out(2)', clearProps: 'transform,opacity,zIndex' },
            0
          );
          if (checkIcon) {
            checkTl.to(checkIcon, { scale: 1, rotation: 0, duration: 0.28, ease: 'back.out(2.6)', clearProps: 'transform' }, 0.1);
          }
          badgesTl.add(checkTl, 0.54);
        }

        heroTl.add(badgesTl, headlineRows.length ? 'rowsIn-=0.47' : 0);

        if (heroSub.length) {
          heroTl.from(
            heroSub,
            { y: 14, opacity: 0, duration: 0.4, stagger: 0.06, clearProps: 'transform,opacity' },
            'rowsIn-=0.18'
          );
        }
        if (browserFrame) {
          heroTl.from(
            browserFrame,
            {
              transformPerspective: 1200,
              rotationX: 6,
              y: 26,
              scale: 0.975,
              opacity: 0,
              duration: 0.68,
              ease: 'power3.out',
              clearProps: 'transform,opacity'
            },
            '-=0.24'
          );
        }
        if (previewNote) {
          heroTl.from(
            previewNote,
            { y: 14, opacity: 0, duration: 0.42, clearProps: 'transform,opacity' },
            '<0.12'
          );
        }

        let heroBadgesReady = false;
        const floatingBadges = page.querySelectorAll('.fd-149_4254, .fd-149_4261');
        if (isDesktop && floatingBadges.length) {
          heroTl.from(
            floatingBadges,
            {
              y: 18,
              scale: 0.94,
              opacity: 0,
              duration: 0.44,
              stagger: 0.1,
              clearProps: 'opacity',
              onComplete: () => {
                heroBadgesReady = true;
              }
            },
            '-=0.3'
          );
        }

        // Scroll-driven sections (strictly top-to-bottom DOM order)
        if (window.ScrollTrigger) {
          if (isDesktop && floatingBadges.length) {
            const leftBadge = page.querySelector('.fd-149_4254');
            const rightBadge = page.querySelector('.fd-149_4261');
            const parallaxTl = gsap.timeline({
              scrollTrigger: {
                trigger: '#hero',
                start: 'top top',
                end: 'bottom top',
                scrub: 0.6
              }
            });
            if (leftBadge) parallaxTl.to(leftBadge, { y: -14, ease: 'none', immediateRender: false }, 0);
            if (rightBadge) parallaxTl.to(rightBadge, { y: -22, ease: 'none', immediateRender: false }, 0);

            if (finePointer) {
              const heroSec = page.querySelector('#hero');
              const leftXTo = leftBadge ? gsap.quickTo(leftBadge, 'x', { duration: 0.55, ease: 'power3' }) : null;
              const rightXTo = rightBadge ? gsap.quickTo(rightBadge, 'x', { duration: 0.55, ease: 'power3' }) : null;
              const onHeroMove = (e) => {
                if (!heroBadgesReady || !heroSec) return;
                const rect = heroSec.getBoundingClientRect();
                if (!rect.width) return;
                const nx = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
                if (leftXTo) leftXTo(gsap.utils.clamp(-6, 6, nx * 6));
                if (rightXTo) rightXTo(gsap.utils.clamp(-8, 8, -nx * 8));
              };
              const onHeroLeave = () => {
                if (leftXTo) leftXTo(0);
                if (rightXTo) rightXTo(0);
              };
              if (heroSec) {
                heroSec.addEventListener('mousemove', onHeroMove);
                heroSec.addEventListener('mouseleave', onHeroLeave);
                cleanups.push(() => {
                  heroSec.removeEventListener('mousemove', onHeroMove);
                  heroSec.removeEventListener('mouseleave', onHeroLeave);
                });
              }
            }
          }

          // Hero Pillar Strip
          const pillars = page.querySelectorAll('.fd-149_4270, .fd-149_4277, .fd-149_4284');
          if (pillars.length) {
            gsap.from(pillars, {
              y: 14,
              opacity: 0,
              duration: 0.4,
              stagger: 0.08,
              clearProps: 'transform,opacity',
              scrollTrigger: {
                trigger: '.fd-149_4269',
                start: 'top 88%',
                once: true
              }
            });
          }

          // Section 2: #ledger-demo (Live 3-beat running-balance story + step highlight)
          const ledgerSec = page.querySelector('#ledger-demo');
          if (ledgerSec) {
            const parsePeso = (str) => {
              const m = (str || '').trim().match(/^(-?)\s*₱?\s*([\d,]+(?:\.\d+)?)/);
              return m ? (m[1] === '-' ? -1 : 1) * Number(m[2].replace(/,/g, '')) : NaN;
            };
            const fmtPeso = new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            const slot0 = ledgerSec.querySelector('.fd-149_4306');
            const slot1 = ledgerSec.querySelector('.fd-149_4307');
            const slot2 = ledgerSec.querySelector('.fd-149_4308');
            const balanceBar = ledgerSec.querySelector('.fd-149_4309');
            const balanceEl = ledgerSec.querySelector('.fd-149_4313');
            const step1 = ledgerSec.querySelector('.fd-149_4316');
            const step2 = ledgerSec.querySelector('.fd-149_4322');
            const step3 = ledgerSec.querySelector('.fd-149_4328');
            const step1Dot = ledgerSec.querySelector('.fd-149_4317');
            const step2Dot = ledgerSec.querySelector('.fd-149_4323');
            const step3Dot = ledgerSec.querySelector('.fd-149_4329');

            const originalBalanceText = balanceEl ? balanceEl.textContent : '';
            const amt0 = parsePeso(slot0?.querySelector('div > p:last-child')?.textContent);
            const amt1 = parsePeso(slot1?.querySelector('div > p:last-child')?.textContent);
            const amt2 = parsePeso(slot2?.querySelector('div > p:last-child')?.textContent);
            const finalBalance = parsePeso(originalBalanceText);
            const liveMath =
              Boolean(balanceEl) &&
              Number.isFinite(amt0) &&
              Number.isFinite(amt1) &&
              Number.isFinite(amt2) &&
              Number.isFinite(finalBalance) &&
              Math.abs(amt0 + amt1 + amt2 - finalBalance) < 0.01;

            let ledgerReady = false;
            const ledgerTl = gsap.timeline({
              scrollTrigger: { trigger: ledgerSec, start: 'top 80%', once: true },
              onComplete: () => {
                if (balanceEl && liveMath) balanceEl.textContent = originalBalanceText;
                ledgerReady = true;
              }
            });

            ledgerTl
              .from(ledgerSec.querySelector('.fd-149_4292'), {
                y: 18,
                opacity: 0,
                duration: 0.45,
                clearProps: 'transform,opacity'
              })
              .from(
                ledgerSec.querySelector('.fd-149_4297'),
                { y: 18, opacity: 0, duration: 0.42, clearProps: 'transform,opacity' },
                '-=0.25'
              );

            if (liveMath) {
              const balCounter = { val: 0 };
              const renderBal = () => {
                balanceEl.textContent = `₱${fmtPeso.format(balCounter.val)}`;
              };
              if (step1) {
                ledgerTl.from(step1, { y: 16, opacity: 0, duration: 0.36, clearProps: 'transform,opacity' }, '-=0.2');
              }
              if (step1Dot) {
                ledgerTl.from(step1Dot, { scale: 0.72, opacity: 0, duration: 0.28, ease: 'back.out(1.8)', clearProps: 'transform,opacity' }, '<0.04');
              }
              if (slot0) {
                ledgerTl.from(slot0, { y: 12, opacity: 0, duration: 0.32, clearProps: 'transform,opacity' }, '<0.06');
              }
              ledgerTl.to(balCounter, { val: amt0, duration: 0.32, ease: 'power2.out', onUpdate: renderBal }, '<');
              if (slot1) {
                ledgerTl.from(slot1, { y: 12, opacity: 0, duration: 0.3, clearProps: 'transform,opacity' }, '-=0.06');
              }
              ledgerTl.to(balCounter, { val: amt0 + amt1, duration: 0.3, ease: 'power2.out', onUpdate: renderBal }, '<');

              if (step2) {
                ledgerTl.from(step2, { y: 16, opacity: 0, duration: 0.36, clearProps: 'transform,opacity' }, '-=0.04');
              }
              if (step2Dot) {
                ledgerTl.from(step2Dot, { scale: 0.72, opacity: 0, duration: 0.28, ease: 'back.out(1.8)', clearProps: 'transform,opacity' }, '<0.04');
              }
              if (slot2) {
                ledgerTl.from(slot2, { x: -14, opacity: 0, duration: 0.36, clearProps: 'transform,opacity' }, '<0.06');
              }
              if (balanceBar) {
                ledgerTl.from(balanceBar, { y: 10, opacity: 0, duration: 0.3, clearProps: 'transform,opacity' }, '<');
              }
              ledgerTl.to(
                balCounter,
                {
                  val: finalBalance,
                  duration: 0.45,
                  ease: 'power2.inOut',
                  onUpdate: renderBal,
                  onComplete: () => {
                    balanceEl.textContent = originalBalanceText;
                  }
                },
                '<0.08'
              );
              if (balanceBar) {
                ledgerTl
                  .to(balanceBar, { scale: 1.024, duration: 0.12, ease: 'power1.out' }, '<0.28')
                  .to(balanceBar, { scale: 1, duration: 0.18, ease: 'power2.out', clearProps: 'transform' });
              }
              if (step3) {
                ledgerTl.from(step3, { y: 16, opacity: 0, duration: 0.36, clearProps: 'transform,opacity' }, '-=0.18');
              }
              if (step3Dot) {
                ledgerTl.from(step3Dot, { scale: 0.72, opacity: 0, duration: 0.28, ease: 'back.out(1.8)', clearProps: 'transform,opacity' }, '<0.04');
              }
            } else {
              if (step1) ledgerTl.from(step1, { y: 16, opacity: 0, duration: 0.36, clearProps: 'transform,opacity' }, '-=0.2');
              if (slot0 || slot1) {
                ledgerTl.from([slot0, slot1].filter(Boolean), { y: 12, opacity: 0, duration: 0.34, stagger: 0.08, clearProps: 'transform,opacity' }, '<0.06');
              }
              if (step2) ledgerTl.from(step2, { y: 16, opacity: 0, duration: 0.36, clearProps: 'transform,opacity' }, '-=0.1');
              if (slot2) ledgerTl.from(slot2, { x: -12, opacity: 0, duration: 0.34, clearProps: 'transform,opacity' }, '<0.06');
              if (step3) ledgerTl.from(step3, { y: 16, opacity: 0, duration: 0.36, clearProps: 'transform,opacity' }, '-=0.12');
              if (balanceBar) {
                ledgerTl
                  .from(balanceBar, { y: 10, opacity: 0, duration: 0.34, clearProps: 'transform,opacity' }, '<0.04')
                  .call(() => animateNumericText(balanceEl, 0.55), null, '<');
              }
            }

            // Interactive step highlight (hover on desktop, click toggle everywhere)
            const allLedgerPieces = [slot0, slot1, slot2, balanceBar].filter(Boolean);
            const stepBindings = [
              { el: step1, targets: [slot0, slot1].filter(Boolean) },
              { el: step2, targets: [slot2].filter(Boolean) },
              { el: step3, targets: [balanceBar].filter(Boolean) }
            ].filter((item) => item.el && item.targets.length);

            let activeStepEl = null;
            const highlightTargets = (targets) => {
              allLedgerPieces.forEach((piece) => {
                const matched = targets.includes(piece);
                gsap.to(piece, {
                  opacity: matched ? 1 : 0.48,
                  scale: matched ? 1.016 : 1,
                  duration: 0.2,
                  ease: 'power2.out',
                  overwrite: 'auto'
                });
              });
            };
            const clearHighlight = () => {
              gsap.to(allLedgerPieces, {
                opacity: 1,
                scale: 1,
                duration: 0.2,
                ease: 'power2.out',
                overwrite: 'auto',
                clearProps: 'transform,opacity'
              });
            };

            stepBindings.forEach(({ el, targets }) => {
              if (finePointer) {
                const onEnter = () => {
                  if (!ledgerReady) return;
                  highlightTargets(targets);
                };
                const onLeave = () => {
                  if (!ledgerReady) return;
                  activeStepEl = null;
                  clearHighlight();
                };
                el.addEventListener('mouseenter', onEnter);
                el.addEventListener('mouseleave', onLeave);
                cleanups.push(() => {
                  el.removeEventListener('mouseenter', onEnter);
                  el.removeEventListener('mouseleave', onLeave);
                });
              }
              const onClick = () => {
                if (!ledgerReady) return;
                if (activeStepEl === el) {
                  activeStepEl = null;
                  clearHighlight();
                } else {
                  activeStepEl = el;
                  highlightTargets(targets);
                }
              };
              el.addEventListener('click', onClick);
              cleanups.push(() => el.removeEventListener('click', onClick));
            });
          }

          // Section 3: #inventory-story (Shelf-pull entrance + Flip-ready cards)
          const invSec = page.querySelector('#inventory-story');
          if (invSec) {
            const invTl = gsap.timeline({
              scrollTrigger: { trigger: invSec, start: 'top 80%', once: true }
            });
            const invEmblem = invSec.querySelector('.fd-149_4337');
            const invLeft = invSec.querySelectorAll('.fd-149_4340, .fd-149_4343, .fd-149_4350');
            const invFeatured = invSec.querySelector('.fd-149_4352');
            const invArt = invSec.querySelector('.fd-149_4357');
            const invCountdown = invSec.querySelector('.fd-149_4370');
            const invArrow = invSec.querySelector('.fd-149_4374');
            const invOthers = invSec.querySelectorAll('.fd-149_4378, .fd-149_4396');
            const invExpired = invSec.querySelector('.fd-149_4417');

            if (invEmblem) {
              invTl.from(invEmblem, {
                scale: 0.75,
                rotation: -12,
                opacity: 0,
                duration: 0.36,
                ease: 'back.out(1.8)',
                clearProps: 'transform,opacity'
              });
            }
            if (invLeft.length) {
              invTl.from(
                invLeft,
                { y: 16, opacity: 0, duration: 0.42, stagger: 0.07, clearProps: 'transform,opacity' },
                '<0.08'
              );
            }
            if (invFeatured) {
              invTl.from(
                invFeatured,
                { y: 18, opacity: 0, duration: 0.42, clearProps: 'transform,opacity' },
                '-=0.28'
              );
            }
            if (invArt) {
              invTl.from(
                invArt,
                { y: 12, rotation: -7, opacity: 0, duration: 0.4, ease: 'back.out(1.7)', clearProps: 'transform,opacity' },
                '<0.08'
              );
            }
            if (invCountdown) {
              invTl.call(() => animateNumericText(invCountdown, 0.45), null, '<');
            }
            if (invArrow) {
              invTl.from(invArrow, { x: -10, opacity: 0, duration: 0.3, clearProps: 'transform,opacity' }, '<0.08');
            }
            if (invOthers.length) {
              invTl.from(
                invOthers,
                { y: 16, opacity: 0, duration: 0.38, stagger: 0.08, clearProps: 'transform,opacity' },
                '-=0.22'
              );
            }
            if (invExpired) {
              invTl.from(
                invExpired,
                { x: 18, opacity: 0, duration: 0.38, clearProps: 'transform,opacity' },
                '-=0.2'
              );
            }
          }

          // Section 4: #daily-overview (Source-to-total flow + hover cross-highlight)
          const dailySec = page.querySelector('#daily-overview');
          if (dailySec) {
            let dailyReady = false;
            const dailyTl = gsap.timeline({
              scrollTrigger: { trigger: dailySec, start: 'top 80%', once: true },
              onComplete: () => {
                dailyReady = true;
              }
            });
            const rowCashSale = dailySec.querySelector('.fd-149_4437');
            const rowUtangSale = dailySec.querySelector('.fd-149_4438');
            const rowPayment = dailySec.querySelector('.fd-149_4439');
            const cardSales = dailySec.querySelector('.fd-149_4442');
            const divSales = dailySec.querySelector('.fd-149_4448');
            const valSales = dailySec.querySelector('.fd-149_4447');
            const cardCash = dailySec.querySelector('.fd-149_4451');
            const divCash = dailySec.querySelector('.fd-149_4457');
            const valCash = dailySec.querySelector('.fd-149_4456');
            const dailyNote = dailySec.querySelector('.fd-149_4460');
            const dailyNoteIcon = dailySec.querySelector('.fd-149_4461');

            const pulseRows = (rows) => {
              const list = rows.filter(Boolean);
              if (!list.length) return;
              gsap
                .timeline()
                .to(list, { scale: 1.015, duration: 0.14, ease: 'power1.out', overwrite: 'auto' })
                .to(list, { scale: 1, duration: 0.2, ease: 'power2.out', clearProps: 'transform' });
            };

            dailyTl
              .from(dailySec.querySelector('.fd-149_4425'), {
                y: 18,
                opacity: 0,
                duration: 0.45,
                clearProps: 'transform,opacity'
              })
              .from(
                dailySec.querySelector('.fd-149_4430'),
                { y: 16, opacity: 0, duration: 0.4, clearProps: 'transform,opacity' },
                '-=0.24'
              )
              .from(
                [rowCashSale, rowUtangSale, rowPayment].filter(Boolean),
                { y: 14, opacity: 0, duration: 0.36, stagger: 0.07, clearProps: 'transform,opacity' },
                '-=0.24'
              );

            if (cardSales) {
              dailyTl.from(cardSales, { y: 16, opacity: 0, duration: 0.4, clearProps: 'transform,opacity' }, '-=0.26');
            }
            if (divSales) {
              dailyTl.from(
                divSales,
                { scaleX: 0, transformOrigin: 'left center', duration: 0.4, ease: 'power2.out', clearProps: 'transform' },
                '<0.06'
              );
            }
            if (valSales) {
              dailyTl.call(() => animateNumericText(valSales, 0.5), null, '<');
            }
            dailyTl.call(() => pulseRows([rowCashSale, rowUtangSale]), null, '<0.05');

            if (cardCash) {
              dailyTl.from(cardCash, { y: 16, opacity: 0, duration: 0.4, clearProps: 'transform,opacity' }, '-=0.22');
            }
            if (divCash) {
              dailyTl.from(
                divCash,
                { scaleX: 0, transformOrigin: 'left center', duration: 0.4, ease: 'power2.out', clearProps: 'transform' },
                '<0.06'
              );
            }
            if (valCash) {
              dailyTl.call(() => animateNumericText(valCash, 0.5), null, '<');
            }
            dailyTl.call(() => pulseRows([rowCashSale, rowPayment]), null, '<0.05');

            if (dailyNote) {
              dailyTl.from(dailyNote, { y: 12, opacity: 0, duration: 0.36, clearProps: 'transform,opacity' }, '-=0.14');
            }
            if (dailyNoteIcon) {
              dailyTl.from(
                dailyNoteIcon,
                { scale: 0.6, opacity: 0, duration: 0.3, ease: 'back.out(2)', clearProps: 'transform,opacity' },
                '<0.06'
              );
            }

            if (finePointer && rowCashSale && rowUtangSale && rowPayment) {
              const allRows = [rowCashSale, rowUtangSale, rowPayment];
              const setFocus = (activeRows) => {
                allRows.forEach((row) => {
                  const active = activeRows.includes(row);
                  gsap.to(row, {
                    opacity: active ? 1 : 0.45,
                    scale: active ? 1.015 : 1,
                    duration: 0.2,
                    ease: 'power2.out',
                    overwrite: 'auto'
                  });
                });
              };
              const resetFocus = () => {
                gsap.to(allRows, {
                  opacity: 1,
                  scale: 1,
                  duration: 0.2,
                  ease: 'power2.out',
                  overwrite: 'auto',
                  clearProps: 'transform,opacity'
                });
              };
              const bindSummaryHover = (card, targets) => {
                if (!card) return;
                const onEnter = () => {
                  if (!dailyReady) return;
                  setFocus(targets);
                };
                const onLeave = () => {
                  if (!dailyReady) return;
                  resetFocus();
                };
                card.addEventListener('mouseenter', onEnter);
                card.addEventListener('mouseleave', onLeave);
                cleanups.push(() => {
                  card.removeEventListener('mouseenter', onEnter);
                  card.removeEventListener('mouseleave', onLeave);
                });
              };
              bindSummaryHover(cardSales, [rowCashSale, rowUtangSale]);
              bindSummaryHover(cardCash, [rowCashSale, rowPayment]);
            }
          }

          // Section 5: #tagline (Scroll-scrubbed word illumination, no pinning)
          const taglineSec = page.querySelector('#tagline');
          if (taglineSec) {
            const tagTl = gsap.timeline({
              scrollTrigger: {
                trigger: taglineSec,
                start: 'top 84%',
                end: 'center 52%',
                scrub: 0.5
              }
            });
            tagTl
              .fromTo(
                taglineSec.querySelectorAll('.fd-149_4465, .fd-149_4471'),
                { scaleX: 0, transformOrigin: 'center center' },
                { scaleX: 1, duration: 0.45, ease: 'none' },
                0
              )
              .fromTo(
                taglineSec.querySelector('.fd-149_4466'),
                { scale: 0.8, opacity: 0.2 },
                { scale: 1, opacity: 1, duration: 0.3, ease: 'none' },
                0.05
              )
              .fromTo(
                taglineSec.querySelectorAll('.fd-tagline-line > span'),
                { opacity: 0.16, y: 10 },
                { opacity: 1, y: 0, duration: 0.25, stagger: 0.08, ease: 'none' },
                0.1
              )
              .fromTo(
                taglineSec.querySelector('.fd-149_4470'),
                { opacity: 0.15, y: 8 },
                { opacity: 1, y: 0, duration: 0.28, ease: 'none' },
                0.68
              );
          }

          // Section 6: #faq
          const faqSec = page.querySelector('#faq');
          if (faqSec) {
            const faqTl = gsap.timeline({
              scrollTrigger: { trigger: faqSec, start: 'top 82%', once: true }
            });
            faqTl
              .from(faqSec.querySelector('.fd-149_4474'), {
                y: 16,
                opacity: 0,
                duration: 0.42,
                clearProps: 'transform,opacity'
              })
              .from(
                faqSec.querySelectorAll('details'),
                { y: 14, opacity: 0, duration: 0.36, stagger: 0.055, clearProps: 'transform,opacity' },
                '-=0.24'
              );
          }

          // Section 7: #closing (Stamp bookend)
          const closingSec = page.querySelector('#closing');
          if (closingSec) {
            const closeTl = gsap.timeline({
              scrollTrigger: { trigger: closingSec, start: 'top 84%', once: true }
            });
            const closingStore = closingSec.querySelector('.fd-149_4494');
            const closingRule = closingSec.querySelector('.fd-149_4497');
            const closingRows = closingSec.querySelectorAll('.fd-149_4498, .fd-149_4504, .fd-149_4510');
            const closingStamps = closingSec.querySelectorAll('.fd-149_4499, .fd-149_4505, .fd-149_4511');

            closeTl.from(closingSec.querySelector('.fd-149_4486'), {
              y: 20,
              opacity: 0,
              duration: 0.46,
              clearProps: 'transform,opacity'
            });
            if (closingStore) {
              closeTl.from(
                closingStore,
                { rotation: -12, scale: 0.85, opacity: 0, duration: 0.34, ease: 'back.out(1.8)', clearProps: 'transform,opacity' },
                '-=0.24'
              );
            }
            if (closingRule) {
              closeTl.from(
                closingRule,
                { scaleX: 0, transformOrigin: 'left center', duration: 0.4, ease: 'power2.out', clearProps: 'transform' },
                '<0.05'
              );
            }
            if (closingRows.length) {
              closeTl.from(
                closingRows,
                { y: 10, opacity: 0, duration: 0.32, stagger: 0.09, clearProps: 'transform,opacity' },
                '-=0.2'
              );
            }
            if (closingStamps.length) {
              closeTl.from(
                closingStamps,
                {
                  scale: 0.4,
                  rotation: -20,
                  opacity: 0,
                  duration: 0.3,
                  stagger: 0.09,
                  ease: 'back.out(2.4)',
                  clearProps: 'transform,opacity'
                },
                '<0.04'
              );
            }
            closeTl.from(
              closingSec.querySelector('.fd-149_4516'),
              { opacity: 0, duration: 0.36, clearProps: 'opacity' },
              '-=0.18'
            );
          }

          if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(() => {
              if (window.ScrollTrigger) window.ScrollTrigger.refresh();
            });
          }
        }

        // Interactive FAQ Toggle
        page.querySelectorAll('#faq details').forEach((details) => {
          const onToggle = () => {
            if (!details.open) return;
            const answer = details.querySelector('.fd-faq-answer');
            const minus = details.querySelector('.fd-minus');
            if (answer) {
              gsap.fromTo(
                answer,
                { y: -6, opacity: 0 },
                { y: 0, opacity: 1, duration: 0.24, ease: 'power2.out', overwrite: true, clearProps: 'transform,opacity' }
              );
            }
            if (minus) {
              gsap.fromTo(
                minus,
                { rotation: -90, opacity: 0.5 },
                { rotation: 0, opacity: 1, duration: 0.2, ease: 'power2.out', overwrite: true, clearProps: 'transform,opacity' }
              );
            }
          };
          details.addEventListener('toggle', onToggle);
          cleanups.push(() => details.removeEventListener('toggle', onToggle));
        });

        // Subtle CTA arrow & playful hero badge hover on fine pointer
        if (finePointer) {
          page.querySelectorAll('.fd-action').forEach((btn) => {
            const arrow = btn.querySelector('img');
            if (!arrow) return;
            const onEnter = () => gsap.to(arrow, { x: 2, y: -2, duration: 0.2, ease: 'power2.out', overwrite: true });
            const onLeave = () =>
              gsap.to(arrow, { x: 0, y: 0, duration: 0.2, ease: 'power2.out', overwrite: true, clearProps: 'transform' });
            btn.addEventListener('mouseenter', onEnter);
            btn.addEventListener('mouseleave', onLeave);
            cleanups.push(() => {
              btn.removeEventListener('mouseenter', onEnter);
              btn.removeEventListener('mouseleave', onLeave);
            });
          });

          if (pesoBadge) {
            const onPesoEnter = () => {
              if (!badgesReady || gsap.isTweening(pesoBadge)) return;
              gsap
                .timeline()
                .to(pesoBadge, { y: -10, duration: 0.14, ease: 'power2.out' }, 0)
                .to(pesoBadge, { y: 0, duration: 0.2, ease: 'bounce.out' }, 0.14)
                .to(pesoBadge, { rotation: 360, duration: 0.38, ease: 'power2.out', clearProps: 'transform' }, 0);
            };
            pesoBadge.addEventListener('mouseenter', onPesoEnter);
            cleanups.push(() => pesoBadge.removeEventListener('mouseenter', onPesoEnter));
          }

          if (boxBadge) {
            const onBoxEnter = () => {
              if (!badgesReady || gsap.isTweening(boxBadge)) return;
              gsap
                .timeline()
                .to(boxBadge, { y: -5, rotation: -10, duration: 0.09, ease: 'power2.out' })
                .to(boxBadge, { rotation: 8, duration: 0.09, ease: 'power1.inOut' })
                .to(boxBadge, { rotation: -4, duration: 0.08, ease: 'power1.inOut' })
                .to(boxBadge, { y: 0, rotation: 0, duration: 0.1, ease: 'power2.out', clearProps: 'transform' });
            };
            boxBadge.addEventListener('mouseenter', onBoxEnter);
            cleanups.push(() => boxBadge.removeEventListener('mouseenter', onBoxEnter));
          }

          if (checkBadge) {
            const onCheckEnter = () => {
              if (!badgesReady || gsap.isTweening(checkBadge)) return;
              gsap
                .timeline()
                .to(checkBadge, { scale: 1.15, rotation: -8, duration: 0.12, ease: 'power2.out' })
                .to(checkBadge, { scale: 1, rotation: 0, duration: 0.16, ease: 'back.out(2.2)', clearProps: 'transform' });
            };
            checkBadge.addEventListener('mouseenter', onCheckEnter);
            cleanups.push(() => checkBadge.removeEventListener('mouseenter', onCheckEnter));
          }

          // Subtle magnetic pull (±4px) on primary orange CTA pills
          page.querySelectorAll('.fd-149_4239, .fd-149_4491').forEach((cta) => {
            const xTo = gsap.quickTo(cta, 'x', { duration: 0.32, ease: 'power3.out' });
            const yTo = gsap.quickTo(cta, 'y', { duration: 0.32, ease: 'power3.out' });
            const onMove = (e) => {
              const rect = cta.getBoundingClientRect();
              if (!rect.width || !rect.height) return;
              const nx = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
              const ny = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
              xTo(gsap.utils.clamp(-4, 4, nx * 4));
              yTo(gsap.utils.clamp(-4, 4, ny * 4));
            };
            const onLeave = () => {
              xTo(0);
              yTo(0);
            };
            cta.addEventListener('mousemove', onMove);
            cta.addEventListener('mouseleave', onLeave);
            cleanups.push(() => {
              cta.removeEventListener('mousemove', onMove);
              cta.removeEventListener('mouseleave', onLeave);
            });
          });
        }

        return () => cleanups.forEach((fn) => fn());
      }
    );
  };

  const initAuth = (mm) => {
    const container = document.querySelector('.container-auth');
    if (!container) return;

    mm.add({ motionOk: '(prefers-reduced-motion: no-preference)' }, (context) => {
      if (!context.conditions.motionOk) return;
      const q = gsap.utils.selector(container);
      const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

      const topBar = q('.auth-top-bar');
      const editorial = q('.auth-badge-pill, .auth-hero-title, .auth-hero-desc, .auth-feature-item');
      const card = q('.auth-card-elevated');
      const cardInner = q(
        '.auth-steps, .form-step:not(.form-step-hidden) .form-group, .form-step:not(.form-step-hidden) .auth-submit-wrap, .form-step:not(.form-step-hidden) .form-step-actions, .auth-card-footer'
      );

      if (topBar.length) {
        tl.from(topBar, { y: -8, opacity: 0, duration: 0.32, clearProps: 'transform,opacity' });
      }
      if (editorial.length) {
        tl.from(
          editorial,
          { y: 14, opacity: 0, duration: 0.42, stagger: 0.055, clearProps: 'transform,opacity' },
          topBar.length ? '-=0.18' : 0
        );
      }
      if (card.length) {
        tl.from(
          card,
          { y: 14, scale: 0.985, opacity: 0, duration: 0.44, clearProps: 'transform,opacity' },
          '<0.06'
        );
      }
      if (cardInner.length) {
        tl.from(
          cardInner,
          { y: 8, opacity: 0, duration: 0.28, stagger: 0.04, clearProps: 'transform,opacity' },
          '-=0.26'
        );
      }

      const errorAlert = container.querySelector('.auth-alert-error');
      if (errorAlert) {
        tl.call(() => animateShake(errorAlert), null, '+=0.02');
      }

      const successAlert = container.querySelector('.auth-alert-success');
      if (successAlert) {
        tl.from(successAlert, { y: -6, opacity: 0, duration: 0.28, clearProps: 'transform,opacity' }, '<');
      }
    });
  };

  const initWorkspace = (mm) => {
    const workspace = document.querySelector('.workspace');
    if (!workspace || isEmbeddedPreview()) return;
    const main = document.querySelector('#main-content') || document.querySelector('.workspace-content');
    if (!main) return;

    mm.add({ motionOk: '(prefers-reduced-motion: no-preference)' }, (context) => {
      if (!context.conditions.motionOk) return;

      const q = gsap.utils.selector(main);
      const tl = gsap.timeline({ defaults: { ease: 'power3.out', duration: 0.3 } });

      const headings = cap(q('.back-link, .page-heading'), 6);
      const flashes = cap(q('.flash-list .flash'), 4);
      const heroSurfaces = cap(
        q(
          '.money-overview > *, .customer-balance > *, .two-columns > .metric-card, .two-columns > .attention-card, .summary-strip, .store-identity, .notice'
        ),
        8
      );
      const filters = cap(q('.filter-bar, .filter-tabs, .segment-control, .pos-category-tabs'), 6);
      const receiptPaper = main.querySelector('.receipt-paper');
      const receiptCheck = main.querySelector('.receipt-check');
      const sections = cap(q('.paper-section:not(.receipt-paper), .basket-panel[open]'), 8);
      const rows = cap(
        q('.record-row, .responsive-table tbody tr, .batch-record, .expiry-urgent, .recipient-link, .receipt-line, .mobile-ledger-row'),
        12
      );

      if (headings.length) {
        tl.from(headings, { y: 8, opacity: 0, duration: 0.26, stagger: 0.03, clearProps: 'transform,opacity' });
      }
      if (flashes.length) {
        tl.from(flashes, { y: -8, opacity: 0, duration: 0.26, stagger: 0.04, clearProps: 'transform,opacity' }, '<0.04');
      }
      if (heroSurfaces.length) {
        tl.from(
          heroSurfaces,
          { y: 12, opacity: 0, duration: 0.32, stagger: 0.045, clearProps: 'transform,opacity' },
          '<0.05'
        );
      }
      if (filters.length) {
        tl.from(
          filters,
          { y: 6, opacity: 0, duration: 0.22, stagger: 0.035, clearProps: 'transform,opacity' },
          '<0.06'
        );
      }
      if (receiptPaper) {
        tl.fromTo(
          receiptPaper,
          { clipPath: 'inset(0% 0% 100% 0%)', y: -14, opacity: 0.85 },
          { clipPath: 'inset(0% 0% 0% 0%)', y: 0, opacity: 1, duration: 0.52, ease: 'power3.out', clearProps: 'clipPath,transform,opacity' },
          '<0.04'
        );
        if (receiptCheck) {
          tl.fromTo(
            receiptCheck,
            { scale: 1.4, rotation: -16, opacity: 0 },
            { scale: 1, rotation: 0, opacity: 1, duration: 0.36, ease: 'back.out(2.2)', clearProps: 'transform,opacity' },
            '-=0.22'
          );
        }
      }
      if (sections.length) {
        tl.from(
          sections,
          { y: 12, opacity: 0, duration: 0.32, stagger: 0.05, clearProps: 'transform,opacity' },
          '<0.05'
        );
      }
      if (rows.length) {
        tl.from(
          rows,
          { y: 6, opacity: 0, duration: 0.22, stagger: 0.02, clearProps: 'transform,opacity' },
          '<0.08'
        );
      }

      // Numeric KPI count-ups (cap to first 8 visible KPI elements)
      const numericEls = cap(
        q(
          '.hero-number, .debt-number, .summary-strip strong, .metric-card > strong, .collection-summary > strong, .aside-total > strong, .receipt-paper > .basket-total strong'
        ),
        8
      ).filter((el) => el.id !== 'entry-preview' && el.id !== 'basket-total');

      numericEls.forEach((el) => animateNumericText(el, 0.44));

      // Financial reports <meter> fill animations
      const meters = cap(q('.sales-bar meter'), 6);
      meters.forEach((meter, idx) => {
        const target = Number(meter.getAttribute('value'));
        if (!Number.isFinite(target) || target <= 0) return;
        const proxy = { val: 0 };
        meter.value = 0;
        gsap.to(proxy, {
          val: target,
          duration: 0.56,
          delay: 0.12 + idx * 0.08,
          ease: 'power3.out',
          onUpdate: () => {
            meter.value = proxy.val;
          },
          onComplete: () => {
            meter.value = target;
          }
        });
      });

      // Product hero artwork & store brand mark
      const heroBadges = q('.product-hero-art, .store-identity .brand-mark');
      if (heroBadges.length) {
        gsap.from(heroBadges, {
          scale: 0.9,
          opacity: 0,
          duration: 0.32,
          ease: 'power3.out',
          clearProps: 'transform,opacity'
        });
      }

      // Product detail batch tools <details> expand feedback
      const cleanups = [];
      q('details.batch-tools').forEach((details) => {
        const onToggle = () => {
          if (!details.open) return;
          const actions = details.querySelector('.batch-actions');
          if (actions) {
            gsap.fromTo(
              actions,
              { y: -4, opacity: 0 },
              { y: 0, opacity: 1, duration: 0.18, ease: 'power2.out', overwrite: true, clearProps: 'transform,opacity' }
            );
          }
        };
        details.addEventListener('toggle', onToggle);
        cleanups.push(() => details.removeEventListener('toggle', onToggle));
      });

      return () => cleanups.forEach((fn) => fn());
    });
  };

  document.addEventListener('DOMContentLoaded', () => {
    if (isEmbeddedPreview() && !document.querySelector('.fd-page, .container-auth')) return;
    const mm = gsap.matchMedia();
    initLanding(mm);
    initAuth(mm);
    initWorkspace(mm);
  });
})();
