/**
 * Main Application Entry Point.
 * Initializes Navigation, View Routing, Responsive Sidebar, and Component Controllers.
 */

import { API } from './api.js';
import { State } from './state.js';
import { UI } from './ui.js';
import { Dashboard } from './dashboard.js';
import { Upload } from './upload.js';
import { Audit } from './audit.js';
import { Datasets } from './datasets.js';

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Initialize Component Controllers
    UI.init();
    Dashboard.init();
    Upload.init();
    Audit.init();
    Datasets.init();


    // 2. Setup Navigation View Switching
    setupNavigation();

    // 3. Health Check
    try {
        const health = await API.checkHealth();
        const statusPill = document.getElementById('system-health-pill');
        if (statusPill && health.status === 'ok') {
            statusPill.className = 'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200';
            statusPill.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> Online';
        }
    } catch (err) {
        const statusPill = document.getElementById('system-health-pill');
        if (statusPill) {
            statusPill.className = 'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-rose-50 text-rose-700 border border-rose-200';
            statusPill.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span> Offline';
        }
    }

    // 4. State Subscriptions for Global UI
    State.subscribe((event, payload) => {
        if (event === 'VIEW_CHANGED') {
            updateViewUI(payload);
        }
        if (event === 'DATASETS_LOADED') {
            updateDatasetSelectors(payload);
        }
        if (event === 'ACTIVE_DATASET_CHANGED' && payload) {
            Dashboard.updateFilterOptions(payload.filterOptions);
        }
    });

    // 5. Initialize Application State
    await State.init();
});

function setupNavigation() {
    const navItems = document.querySelectorAll('[data-view-target]');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const target = item.dataset.viewTarget;
            State.setView(target);

            // Close mobile menu if open
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('mobile-overlay');
            if (sidebar && overlay) {
                sidebar.classList.add('-translate-x-full');
                overlay.classList.add('hidden');
            }
        });
    });

    // Mobile Hamburger
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('mobile-overlay');

    if (mobileMenuBtn && sidebar && overlay) {
        mobileMenuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('-translate-x-full');
            overlay.classList.toggle('hidden');
        });
        overlay.addEventListener('click', () => {
            sidebar.classList.add('-translate-x-full');
            overlay.classList.add('hidden');
        });
    }
}

function updateViewUI(viewName) {
    const views = ['dashboard', 'datasets', 'quality', 'upload', 'about'];
    views.forEach(v => {
        const el = document.getElementById(`view-${v}`);
        if (el) {
            if (v === viewName) {
                el.classList.remove('hidden');
            } else {
                el.classList.add('hidden');
            }
        }
    });

    // Update active nav styling
    const navItems = document.querySelectorAll('[data-view-target]');
    navItems.forEach(item => {
        const isTarget = item.dataset.viewTarget === viewName;
        if (isTarget) {
            item.className = 'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-semibold bg-indigo-50 text-indigo-700 transition border border-indigo-100/60';
        } else {
            item.className = 'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100/70 transition';
        }
    });
}

function updateDatasetSelectors(datasets) {
    const selector = document.getElementById('dataset-selector');
    const deleteBtn = document.getElementById('dashboard-delete-dataset-btn');
    if (!selector) return;

    selector.innerHTML = '';
    if (datasets.length === 0) {
        selector.innerHTML = '<option value="">No datasets uploaded</option>';
        selector.disabled = true;
        if (deleteBtn) {
            deleteBtn.disabled = true;
            deleteBtn.classList.add('opacity-50', 'cursor-not-allowed');
        }
        return;
    }

    selector.disabled = false;
    if (deleteBtn) {
        deleteBtn.disabled = false;
        deleteBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    }
    datasets.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.id;
        opt.textContent = `${d.filename} (${d.total_cleaned_rows} rows)`;
        if (d.id === State.activeDatasetId) {
            opt.selected = true;
        }
        selector.appendChild(opt);
    });
}

