/**
 * UI Utilities Module.
 * Provides accessible toast notifications, modals, skeleton loaders, and view routing transitions.
 */

import { Formatters } from './formatters.js';

export const UI = {
    init() {
        const cancelBtn = document.getElementById('confirm-modal-cancel-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.closeModal('confirm-modal');
            });
        }

        const confirmModal = document.getElementById('confirm-modal');
        if (confirmModal) {
            confirmModal.addEventListener('click', (e) => {
                if (e.target === confirmModal) {
                    this.closeModal('confirm-modal');
                }
            });
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal('confirm-modal');
                this.closeModal('audit-modal');
            }
        });
    },

    showToast(message, type = 'info', duration = 4000) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        const bgColors = {
            success: 'bg-emerald-800 text-white border-emerald-700',
            error: 'bg-rose-800 text-white border-rose-700',
            warning: 'bg-amber-800 text-white border-amber-700',
            info: 'bg-slate-800 text-slate-100 border-slate-700',
        };

        const icons = {
            success: `<svg class="w-5 h-5 text-emerald-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>`,
            error: `<svg class="w-5 h-5 text-rose-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>`,
            warning: `<svg class="w-5 h-5 text-amber-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>`,
            info: `<svg class="w-5 h-5 text-sky-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`,
        };

        const safeMessage = Formatters.escapeHtml(message);

        toast.className = `flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg border text-sm transition-all duration-300 transform translate-y-2 opacity-0 ${bgColors[type] || bgColors.info}`;
        toast.innerHTML = `
            <div>${icons[type] || icons.info}</div>
            <div class="flex-1 font-medium">${safeMessage}</div>
            <button class="text-slate-400 hover:text-white transition ml-2" aria-label="Close">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
        `;

        const closeBtn = toast.querySelector('button');
        closeBtn.addEventListener('click', () => {
            toast.classList.add('opacity-0', 'translate-y-2');
            setTimeout(() => toast.remove(), 300);
        });

        container.appendChild(toast);
        requestAnimationFrame(() => {
            toast.classList.remove('opacity-0', 'translate-y-2');
        });

        if (duration > 0) {
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.classList.add('opacity-0', 'translate-y-2');
                    setTimeout(() => toast.remove(), 300);
                }
            }, duration);
        }
    },

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            document.body.classList.add('overflow-hidden');
        }
    },

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            document.body.classList.remove('overflow-hidden');
        }
    },

    confirm(title, message, confirmText = 'Confirm', onConfirm = () => {}) {
        const modal = document.getElementById('confirm-modal');
        if (!modal) return;

        document.getElementById('confirm-modal-title').textContent = title;
        document.getElementById('confirm-modal-body').textContent = message;
        
        const confirmBtn = document.getElementById('confirm-modal-btn');
        if (confirmBtn) {
            confirmBtn.textContent = confirmText;
            const newConfirmBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
            newConfirmBtn.addEventListener('click', () => {
                this.closeModal('confirm-modal');
                if (typeof onConfirm === 'function') {
                    onConfirm();
                }
            });
        }

        this.openModal('confirm-modal');
    }
};


