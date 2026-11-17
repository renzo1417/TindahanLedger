/**
 * TindaHan Ledger - Store & Owner Profile Client Scripts
 * Vertical Slice: static/js/profile/profile.js
 */

function syncProfileLivePreview() {
  const storeInput = document.getElementById('id_profile_store_name');
  const ownerInput = document.getElementById('id_profile_owner_name');
  const addressInput = document.getElementById('id_profile_address');
  const hoursInput = document.getElementById('id_profile_hours');

  const storeName = (storeInput?.value || '').trim() || 'TindaHan Ledger';
  const ownerName = (ownerInput?.value || '').trim() || 'Store Owner';
  const address = (addressInput?.value || '').trim() || 'Store Barangay Address';
  const hours = (hoursInput?.value || '').trim() || '6:00 AM - 9:00 PM';

  const setText = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };

  setText('hero-store-title', storeName);
  setText('hero-owner-name', ownerName);
  setText('hero-address-text', address);
  setText('hero-avatar-initial', storeName.charAt(0).toUpperCase());

  setText('receipt-store-name', storeName);
  setText('receipt-address', address);
  setText('receipt-hours', `Bukas: ${hours}`);
  setText('receipt-owner', ownerName);

  setText('slip-store-name', storeName);
  setText('slip-owner-name', ownerName);
}

function setProfileEditing(editing) {
  const form = document.getElementById('profile-details-form');
  const saveBtn = document.getElementById('save-profile-btn');
  const label = document.getElementById('toggle-edit-label');
  if (!form) return;

  const editableIds = [
    'id_profile_store_name',
    'id_profile_owner_name',
    'id_profile_address',
    'id_profile_city',
    'id_profile_hours',
  ];

  editableIds.forEach((id) => {
    const field = document.getElementById(id);
    if (field) field.disabled = !editing;
  });

  form.classList.toggle('is-locked', !editing);
  if (saveBtn) saveBtn.disabled = !editing;
  if (label) label.textContent = editing ? 'Lock Fields' : 'Edit Details';

  if (editing) {
    const first = document.getElementById('id_profile_store_name');
    if (first) first.focus();
  }
}

function toggleProfileEdit() {
  const form = document.getElementById('profile-details-form');
  if (!form) return;
  const currentlyLocked = form.classList.contains('is-locked');
  setProfileEditing(currentlyLocked);
  showToast(
    currentlyLocked
      ? 'Profile editing enabled. Changes preview live below.'
      : 'Profile fields locked.',
    'info'
  );
}

function saveProfileForm() {
  syncProfileLivePreview();
  setProfileEditing(false);
  showToast('Store profile changes saved successfully!', 'check');
}

function toggleGcashSlip() {
  const panel = document.getElementById('gcash-slip-panel');
  const btn = document.getElementById('toggle-qr-btn');
  if (!panel || !btn) return;
  const open = panel.classList.toggle('is-open');
  btn.textContent = open ? 'Hide Slip' : 'Show QR';
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('profile-details-form');
  if (form) {
    form.addEventListener('input', syncProfileLivePreview);
  }
  syncProfileLivePreview();

  window.copyToClipboard = function(text, successMsg) {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => {
        showToast(successMsg || 'Copied to clipboard!', 'copy');
      });
    } else {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      showToast(successMsg || 'Copied to clipboard!', 'copy');
    }
  };
});
