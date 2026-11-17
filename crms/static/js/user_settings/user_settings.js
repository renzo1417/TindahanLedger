/**
 * TindaHan Ledger - User Settings Client Scripts
 * Vertical Slice: static/js/user_settings/user_settings.js
 */

const SETTINGS_DEFAULTS = {
  default_credit_limit: '3000',
  overdue_grace_days: '7',
  reminder_threshold_days: '3',
  expiry_window_days: '7',
  low_stock_threshold: '10',
  block_over_limit: true,
  auto_fifo_sort: true,
  sound_effects_enabled: true,
  auto_sms_reminders: true,
  daily_summary_report: true,
};

function setDirtyState(isDirty) {
  const pill = document.getElementById('settings-dirty-pill');
  const text = document.getElementById('settings-dirty-text');
  if (!pill || !text) return;

  pill.classList.toggle('is-dirty', isDirty);
  text.textContent = isDirty ? 'Unsaved adjustments' : 'All rules synced';
}

function updateSmsPreview() {
  const storeInput = document.getElementById('id_store_name');
  const gcashInput = document.getElementById('id_gcash_number');
  const reminderDaysInput = document.getElementById('id_reminder_days');
  const smsToggle = document.getElementById('id_auto_sms_reminders');

  const previewCard = document.getElementById('sms-preview-card');
  const previewText = document.getElementById('sms-preview-text');
  const previewState = document.getElementById('sms-preview-state');
  const previewChars = document.getElementById('sms-preview-chars');
  if (!previewCard || !previewText) return;

  const storeName = (storeInput?.value || '').trim() || 'TindaHan Ledger';
  const gcashNumber = (gcashInput?.value || '').trim() || '09XX-XXX-XXXX';
  const reminderDays = (reminderDaysInput?.value || '3').trim();
  const enabled = smsToggle ? smsToggle.checked : true;

  const message =
    `Magandang araw po! Paalala mula sa ${storeName}: may nakatalang balanse sa inyong utang matapos ang ${reminderDays} araw na paalala window. Maaaring mag-abot sa tindahan o mag-GCash sa ${gcashNumber}. Salamat po.`;

  previewText.textContent = message;
  previewCard.classList.toggle('is-disabled', !enabled);
  if (previewState) {
    previewState.textContent = enabled ? 'Status: Auto-draft enabled' : 'Status: Auto-draft paused';
  }
  if (previewChars) {
    previewChars.textContent = `${message.length} chars`;
  }
}

function copySmsPreview() {
  const previewText = document.getElementById('sms-preview-text');
  if (!previewText) return;
  const text = previewText.textContent;

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      showToast('Tagalog SMS paalala draft copied.', 'copy');
    });
    return;
  }

  const textarea = document.createElement('textarea');
  textarea.value = text;
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand('copy');
  document.body.removeChild(textarea);
  showToast('Tagalog SMS paalala draft copied.', 'copy');
}

function saveSettings() {
  setDirtyState(false);
  updateSmsPreview();
  showToast('Store & ledger settings saved successfully!', 'check');
}

function resetSettingsDefaults() {
  if (!confirm('Reset all ledger and alert rules to standard store defaults?')) {
    return;
  }

  const form = document.getElementById('settings-form');
  if (form) {
    Object.entries(SETTINGS_DEFAULTS).forEach(([name, value]) => {
      const field = form.elements.namedItem(name);
      if (!field) return;
      if (field.type === 'checkbox') {
        field.checked = Boolean(value);
      } else {
        field.value = value;
      }
    });
  }

  updateSmsPreview();
  setDirtyState(false);
  showToast('Policy rules restored to standard store defaults.', 'info');
}

function exportJsonBackup() {
  showToast('Packaging encrypted store ledger JSON backup...', 'info');
  setTimeout(() => {
    const storeName = (document.getElementById('id_store_name')?.value || 'Aling Nena Tindahan').trim();
    const dummyData = {
      store: storeName,
      timestamp: new Date().toISOString(),
      version: '2.0-Vertical-Slice',
      records: { customers: 48, transactions: 154, batches: 28 },
    };
    const blob = new Blob([JSON.stringify(dummyData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tindahan_backup_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Ledger JSON backup downloaded successfully.', 'check');
  }, 600);
}

function exportCsvData() {
  showToast('Compiling customer ledger CSV...', 'info');
  setTimeout(() => {
    const csvContent =
      'data:text/csv;charset=utf-8,ID,Name,Nickname,RunningBalance,CreditLimit,DaysOverdue\n1,Maria Santos,Aling Maria,2350.00,5000,12\n2,Pedro Reyes,Mang Pedro,1800.00,3000,8\n3,Rosa dela Cruz,Ate Rosa,950.00,2000,5\n';
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `customer_utang_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('Customer CSV exported.', 'check');
  }, 600);
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('settings-form');
  const jumpLinks = document.querySelectorAll('.settings-jump-link');

  updateSmsPreview();
  setDirtyState(false);

  if (form) {
    form.addEventListener('input', () => {
      setDirtyState(true);
      updateSmsPreview();
    });
    form.addEventListener('change', () => {
      setDirtyState(true);
      updateSmsPreview();
    });
  }

  jumpLinks.forEach((link) => {
    link.addEventListener('click', () => {
      jumpLinks.forEach((item) => item.classList.remove('active'));
      link.classList.add('active');
    });
  });
});
