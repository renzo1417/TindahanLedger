/**
 * TindaHan Ledger - Register Feature Client Scripts
 * Vertical Slice: static/js/register/register.js
 */

// Multi-step form navigation
function goToStep2() {
  const storeName = document.getElementById('id_reg_store_name');
  const ownerName = document.getElementById('id_reg_owner_name');
  const phone = document.getElementById('id_reg_phone');
  
  let valid = true;
  
  [storeName, ownerName, phone].forEach(input => {
    if (!input) return;
    if (!input.value.trim()) {
      input.classList.add('form-control-error');
      valid = false;
    } else {
      input.classList.remove('form-control-error');
    }
  });
  
  if (!valid) {
    const card = document.getElementById('register-card');
    if (card) {
      card.classList.add('anim-shake');
      setTimeout(() => card.classList.remove('anim-shake'), 500);
    }
    return;
  }
  
  const step1 = document.getElementById('step-1');
  const step2 = document.getElementById('step-2');
  const step1Dot = document.getElementById('step-1-dot');
  const step2Dot = document.getElementById('step-2-dot');
  const pwInput = document.getElementById('id_reg_password');

  if (step1 && step2) {
    step1.classList.add('form-step-exit');
    setTimeout(() => {
      step1.classList.add('form-step-hidden');
      step1.classList.remove('form-step-exit');
      step2.classList.remove('form-step-hidden');
      step2.classList.add('form-step-enter');
      if (step1Dot) {
        step1Dot.classList.remove('active');
        step1Dot.classList.add('completed');
      }
      if (step2Dot) {
        step2Dot.classList.add('active');
      }
      if (pwInput) pwInput.focus();
      setTimeout(() => step2.classList.remove('form-step-enter'), 300);
    }, 200);
  }
}

function goToStep1() {
  const step1 = document.getElementById('step-1');
  const step2 = document.getElementById('step-2');
  const step1Dot = document.getElementById('step-1-dot');
  const step2Dot = document.getElementById('step-2-dot');

  if (step1 && step2) {
    step2.classList.add('form-step-exit');
    setTimeout(() => {
      step2.classList.add('form-step-hidden');
      step2.classList.remove('form-step-exit');
      step1.classList.remove('form-step-hidden');
      step1.classList.add('form-step-enter');
      if (step2Dot) step2Dot.classList.remove('active');
      if (step1Dot) {
        step1Dot.classList.remove('completed');
        step1Dot.classList.add('active');
      }
      setTimeout(() => step1.classList.remove('form-step-enter'), 300);
    }, 200);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const regCard = document.getElementById('register-card');
  const pwInput = document.getElementById('id_reg_password');
  const confirmInput = document.getElementById('id_reg_confirm_password');
  const strengthFill = document.getElementById('strength-fill');
  const strengthLabel = document.getElementById('strength-label');
  const matchIndicator = document.getElementById('password-match');
  const charCountEl = document.getElementById('char-count');
  const ruleHint = document.getElementById('password-rule-hint');
  const ruleIcon = document.getElementById('rule-len-icon');
  const form = document.getElementById('register-form');
  const pwErrorContainer = document.getElementById('password-error-container');
  const confirmErrorContainer = document.getElementById('confirm-password-error-container');

  // If server-side validation reported step 2 errors, show step 2 automatically
  if (regCard && regCard.dataset.hasStep2Errors === 'true') {
    const step1 = document.getElementById('step-1');
    const step2 = document.getElementById('step-2');
    const step1Dot = document.getElementById('step-1-dot');
    const step2Dot = document.getElementById('step-2-dot');
    if (step1 && step2) {
      step1.classList.add('form-step-hidden');
      step2.classList.remove('form-step-hidden');
      if (step1Dot) {
        step1Dot.classList.remove('active');
        step1Dot.classList.add('completed');
      }
      if (step2Dot) step2Dot.classList.add('active');
    }
  }

  // Live input handlers
  if (pwInput) {
    pwInput.addEventListener('input', () => {
      const val = pwInput.value;
      
      // Live char counter
      if (charCountEl) {
        charCountEl.textContent = val.length;
      }

      // 8-character rule check
      if (val.length >= 8) {
        if (ruleHint) ruleHint.classList.add('rule-met');
        if (ruleIcon) {
          ruleIcon.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
        }
        pwInput.classList.remove('form-control-error');
        const clientErr = document.getElementById('client-pw-len-error');
        if (clientErr) clientErr.remove();
      } else {
        if (ruleHint) ruleHint.classList.remove('rule-met');
        if (ruleIcon) {
          ruleIcon.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle></svg>`;
        }
      }

      // Password strength calculation
      let score = 0;
      if (val.length >= 8) score++;
      if (val.length >= 12) score++;
      if (/[A-Z]/.test(val)) score++;
      if (/[0-9]/.test(val)) score++;
      if (/[^A-Za-z0-9]/.test(val)) score++;
      
      const levels = [
        { width: '0%', color: 'transparent', label: '' },
        { width: '20%', color: '#a3301e', label: 'Too weak' },
        { width: '40%', color: '#be491c', label: 'Weak' },
        { width: '60%', color: '#eb733c', label: 'Fair' },
        { width: '80%', color: '#16674f', label: 'Strong' },
        { width: '100%', color: '#0f523e', label: 'Very strong' },
      ];
      
      const level = val.length === 0 ? levels[0] : levels[Math.min(score, 5)];
      if (strengthFill) {
        strengthFill.style.width = level.width;
        strengthFill.style.backgroundColor = level.color;
      }
      if (strengthLabel) {
        strengthLabel.textContent = level.label;
        strengthLabel.style.color = level.color;
      }
      
      updateMatch();
    });
  }
  
  if (confirmInput) {
    confirmInput.addEventListener('input', () => {
      updateMatch();
      if (confirmInput.value === (pwInput ? pwInput.value : '')) {
        confirmInput.classList.remove('form-control-error');
        const clientMatchErr = document.getElementById('client-match-error');
        if (clientMatchErr) clientMatchErr.remove();
      }
    });
  }
  
  function updateMatch() {
    if (!confirmInput || !pwInput || !matchIndicator) return;
    const pw = pwInput.value;
    const confirm = confirmInput.value;
    
    if (confirm.length > 0 && pw === confirm) {
      matchIndicator.style.display = 'flex';
      matchIndicator.classList.add('match-success');
      matchIndicator.classList.remove('match-fail');
      const span = matchIndicator.querySelector('span');
      if (span) span.textContent = 'Passwords match';
      confirmInput.classList.remove('form-control-error');
    } else if (confirm.length > 0 && pw !== confirm) {
      matchIndicator.style.display = 'flex';
      matchIndicator.classList.add('match-fail');
      matchIndicator.classList.remove('match-success');
      const span = matchIndicator.querySelector('span');
      if (span) span.textContent = 'Passwords do not match';
    } else {
      matchIndicator.style.display = 'none';
    }
  }

  // Pre-populate state if inputs are prefilled
  if (pwInput && pwInput.value) {
    pwInput.dispatchEvent(new Event('input'));
  }

  // Form submit client-side validation
  if (form) {
    form.addEventListener('submit', (e) => {
      let hasError = false;

      const oldLenErr = document.getElementById('client-pw-len-error');
      if (oldLenErr) oldLenErr.remove();
      const oldMatchErr = document.getElementById('client-match-error');
      if (oldMatchErr) oldMatchErr.remove();

      const pw = pwInput ? pwInput.value : '';
      const confirm = confirmInput ? confirmInput.value : '';

      // Check password length rule (< 8 chars)
      if (!pw || pw.length < 8) {
        e.preventDefault();
        hasError = true;
        if (pwInput) pwInput.classList.add('form-control-error');
        
        const errEl = document.createElement('p');
        errEl.id = 'client-pw-len-error';
        errEl.className = 'form-error-text anim-shake';
        errEl.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg> Password must be at least 8 characters long (${pw.length}/8 entered). Please add more characters.`;
        
        if (pwErrorContainer) {
          pwErrorContainer.innerHTML = '';
          pwErrorContainer.appendChild(errEl);
        }
        if (pwInput) pwInput.focus();
      }

      // Check confirm password match
      if (pw.length >= 8 && (!confirm || pw !== confirm)) {
        e.preventDefault();
        hasError = true;
        if (confirmInput) confirmInput.classList.add('form-control-error');

        const matchErrEl = document.createElement('p');
        matchErrEl.id = 'client-match-error';
        matchErrEl.className = 'form-error-text anim-shake';
        const msg = !confirm ? 'Please confirm your password.' : 'Passwords do not match.';
        matchErrEl.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg> ${msg}`;

        if (confirmErrorContainer) {
          confirmErrorContainer.innerHTML = '';
          confirmErrorContainer.appendChild(matchErrEl);
        }
        if (!hasError && confirmInput) confirmInput.focus();
      }

      if (hasError) {
        if (regCard) {
          regCard.classList.add('anim-shake');
          setTimeout(() => regCard.classList.remove('anim-shake'), 500);
        }
        return false;
      }
    });
  }
});
