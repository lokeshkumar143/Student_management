/**
 * AcadVerify Enterprise Client Behavior
 * - Counter animations
 * - Interaction-timed ARIA sync for form validation
 * - Password visibility toggles
 * - Live BVA/ECP marks range visualizer
 * - Live AJAX Pytest suite execution & dynamic QA dashboard updates
 */

document.addEventListener('DOMContentLoaded', () => {
  initCounters();
  initValidationAriaSync();
  initPasswordToggles();
  initDemoCredentialFiller();
  initMarksBvaFeedback();
  initTestMatrixFiltering();
  initLiveTestRunner();
});

/* ----------------------------------------------------------
   1. Animated KPI Counters (respects reduced motion)
   ---------------------------------------------------------- */
function initCounters() {
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('[data-count]').forEach((el) => {
    const target = parseFloat(el.getAttribute('data-count'));
    if (Number.isNaN(target)) return;
    const decimals = parseInt(el.getAttribute('data-decimals') || '0', 10);
    const suffix = el.getAttribute('data-suffix') || '';

    if (prefersReduced) {
      el.textContent = target.toFixed(decimals) + suffix;
      return;
    }

    const duration = 550;
    let startTs = null;
    const step = (ts) => {
      if (!startTs) startTs = ts;
      const progress = Math.min((ts - startTs) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = (target * eased).toFixed(decimals) + suffix;
      if (progress < 1) {
        window.requestAnimationFrame(step);
      }
    };
    window.requestAnimationFrame(step);
  });
}

/* ----------------------------------------------------------
   2. Post-interaction Form Validation & ARIA Synchronization
   ---------------------------------------------------------- */
function initValidationAriaSync() {
  const fields = document.querySelectorAll('form input, form select, form textarea');
  fields.forEach((el) => {
    if (!el.hasAttribute('aria-invalid')) {
      el.setAttribute('aria-invalid', el.classList.contains('is-invalid') ? 'true' : 'false');
    }
  });

  document.addEventListener('blur', (e) => {
    const el = e.target;
    if (!el.matches?.('input, select, textarea') || el.type === 'hidden') return;
    if (el.checkValidity) {
      const valid = el.checkValidity();
      el.setAttribute('aria-invalid', valid ? 'false' : 'true');
    }
  }, true);

  document.addEventListener('input', (e) => {
    const el = e.target;
    if (!el.matches?.('input, select, textarea')) return;
    if (el.classList.contains('is-invalid')) {
      el.classList.remove('is-invalid');
    }
    if (el.checkValidity && el.checkValidity()) {
      el.setAttribute('aria-invalid', 'false');
    }
  });

  // Disable submit button once form is submitted cleanly to prevent double-POST
  document.querySelectorAll('form[data-prevent-double-submit]').forEach((form) => {
    form.addEventListener('submit', () => {
      const btn = form.querySelector('button[type="submit"]');
      if (btn && !btn.disabled) {
        btn.dataset.originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...';
      }
    });
  });
}

/* ----------------------------------------------------------
   3. Accessible Password Visibility Toggles
   ---------------------------------------------------------- */
function initPasswordToggles() {
  document.querySelectorAll('[data-toggle-password]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-toggle-password');
      const input = document.getElementById(targetId);
      if (!input) return;
      const isHidden = input.type === 'password';
      input.type = isHidden ? 'text' : 'password';
      btn.setAttribute('aria-pressed', isHidden ? 'true' : 'false');
      const icon = btn.querySelector('i');
      if (icon) {
        icon.className = isHidden ? 'bi bi-eye-slash' : 'bi bi-eye';
      }
    });
  });
}

/* ----------------------------------------------------------
   4. Demo Credential Auto-Fill (Login Page)
   ---------------------------------------------------------- */
function initDemoCredentialFiller() {
  const fillBtn = document.getElementById('fillDemoCredentialsBtn');
  if (!fillBtn) return;
  fillBtn.addEventListener('click', () => {
    const userField = document.getElementById('username');
    const passField = document.getElementById('password');
    if (userField) userField.value = 'admin';
    if (passField) passField.value = 'Admin@123';
    userField?.focus();
  });
}

/* ----------------------------------------------------------
   5. Live Marks Boundary & Grade Indicator (Add/Edit Student)
   ---------------------------------------------------------- */
function initMarksBvaFeedback() {
  const marksInput = document.getElementById('marks');
  const feedbackBox = document.getElementById('liveBvaFeedback');
  const bvaLabel = document.getElementById('bvaLabel');
  const bvaGrade = document.getElementById('bvaGrade');

  if (!marksInput || !feedbackBox || !bvaLabel || !bvaGrade) return;

  const update = () => {
    const valStr = marksInput.value.trim();
    if (valStr === '') {
      feedbackBox.style.display = 'none';
      return;
    }

    const m = Number(valStr);
    feedbackBox.style.display = 'block';

    if (Number.isNaN(m) || !Number.isFinite(m)) {
      feedbackBox.className = 'mt-2 p-2 px-3 rounded-3 small border bg-danger-subtle text-danger border-danger-subtle';
      bvaLabel.innerHTML = '<i class="bi bi-x-circle-fill me-1"></i> Invalid non-numeric entry';
      bvaGrade.style.display = 'none';
      return;
    }

    bvaGrade.style.display = 'inline-block';

    if (m < 0) {
      feedbackBox.className = 'mt-2 p-2 px-3 rounded-3 small border bg-danger-subtle text-danger border-danger-subtle';
      bvaLabel.innerHTML = '<i class="bi bi-x-circle-fill me-1"></i> Out of range (&lt; 0): rejected on submit';
      bvaGrade.className = 'badge bg-danger';
      bvaGrade.textContent = 'Invalid';
    } else if (m > 100) {
      feedbackBox.className = 'mt-2 p-2 px-3 rounded-3 small border bg-danger-subtle text-danger border-danger-subtle';
      bvaLabel.innerHTML = '<i class="bi bi-x-circle-fill me-1"></i> Out of range (&gt; 100): rejected on submit';
      bvaGrade.className = 'badge bg-danger';
      bvaGrade.textContent = 'Invalid';
    } else {
      const grade = m >= 90 ? 'A+' : m >= 80 ? 'A' : m >= 70 ? 'B' : m >= 60 ? 'C' : m >= 50 ? 'D' : 'F';
      feedbackBox.className = 'mt-2 p-2 px-3 rounded-3 small border bg-success-subtle text-success border-success-subtle';
      let boundaryNote = 'Valid score';
      if (m === 0) boundaryNote = 'Minimum valid boundary (0.0)';
      if (m === 100) boundaryNote = 'Maximum valid boundary (100.0)';
      bvaLabel.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i> ${boundaryNote}`;
      bvaGrade.className = m >= 50 ? 'badge bg-success' : 'badge bg-warning text-dark';
      bvaGrade.textContent = `Grade: ${grade}`;
    }
  };

  marksInput.addEventListener('input', update);
  if (marksInput.value) update();
}

/* ----------------------------------------------------------
   6. Test Case Matrix Filtering (QA Dashboard)
   ---------------------------------------------------------- */
function initTestMatrixFiltering() {
  const filterGroup = document.getElementById('filterBtnGroup');
  const searchInput = document.getElementById('testSearchInput');
  if (!filterGroup && !searchInput) return;

  let activeType = 'all';

  const applyFilters = () => {
    const query = (searchInput?.value || '').trim().toLowerCase();
    document.querySelectorAll('.test-row').forEach((row) => {
      const rowType = row.getAttribute('data-type') || '';
      const rowName = row.getAttribute('data-name') || '';

      let matchesType = false;
      if (activeType === 'all') matchesType = true;
      else if (activeType === 'bva') matchesType = rowType.includes('bva') || rowType.includes('boundary');
      else if (activeType === 'ecp') matchesType = rowType.includes('ecp') || rowType.includes('equivalence');
      else if (activeType === 'unit') matchesType = rowType.includes('unit') || rowType.includes('validator') || rowType.includes('model');
      else if (activeType === 'integration') matchesType = rowType.includes('integration');
      else if (activeType === 'regression') matchesType = rowType.includes('regression');
      else if (activeType === 'auth') matchesType = rowType.includes('authentication');

      const matchesQuery = !query || rowName.includes(query);
      row.style.display = (matchesType && matchesQuery) ? '' : 'none';
    });
  };

  filterGroup?.querySelectorAll('button[data-filter-type]').forEach((btn) => {
    btn.addEventListener('click', () => {
      activeType = btn.getAttribute('data-filter-type') || 'all';
      filterGroup.querySelectorAll('button').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      applyFilters();
    });
  });

  searchInput?.addEventListener('input', applyFilters);
}

/* ----------------------------------------------------------
   7. Live AJAX Test Suite Execution (QA Dashboard)
   ---------------------------------------------------------- */
function initLiveTestRunner() {
  const form = document.getElementById('mainDashboardTestForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('execMainTestsBtn');
    const statusBanner = document.getElementById('liveRunStatusBanner');
    const csrfToken = form.querySelector('input[name="csrf_token"]')?.value || '';
    const suite = form.querySelector('select[name="suite"]')?.value || 'all';

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Running Suite...';
    }
    if (statusBanner) {
      statusBanner.classList.remove('d-none');
      statusBanner.className = 'alert alert-info d-flex align-items-center gap-2 mb-4 animate-enter';
      statusBanner.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span><span>Executing automated Pytest &amp; Coverage.py run...</span>';
    }

    try {
      const resp = await fetch(form.action, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRF-Token': csrfToken
        },
        body: JSON.stringify({ suite })
      });

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }
      // Reload clean view to reflect new DB test_runs, charts, and coverage rows
      window.location.reload();
    } catch (err) {
      // Graceful fallback to standard form submission if fetch fails
      form.submit();
    }
  });
}
