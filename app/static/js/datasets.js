/**
 * Datasets Management Module.
 * Displays uploaded datasets table, quality health scores, direct actions, and deletion workflows.
 */

import { API } from './api.js';
import { State } from './state.js';
import { Formatters } from './formatters.js';
import { UI } from './ui.js';
import { Audit } from './audit.js';

export const Datasets = {
    init() {
        State.subscribe((event, payload) => {
            if (event === 'DATASETS_LOADED' || event === 'ACTIVE_DATASET_CHANGED') {
                this.renderDatasetsTable();
            }
        });
    },

    renderDatasetsTable() {
        const tableBody = document.getElementById('datasets-table-body');
        const emptyState = document.getElementById('datasets-empty-state');
        const tableContainer = document.getElementById('datasets-table-container');

        if (!tableBody) return;

        const datasets = State.datasets || [];

        if (datasets.length === 0) {
            tableContainer?.classList.add('hidden');
            emptyState?.classList.remove('hidden');
            return;
        }

        tableContainer?.classList.remove('hidden');
        emptyState?.classList.add('hidden');

        tableBody.innerHTML = datasets.map(d => {
            const isActive = d.id === State.activeDatasetId;
            const badge = Formatters.healthBadge(d.health_score);
            const safeFilename = Formatters.escapeHtml(d.filename);
            const safeFormat = Formatters.escapeHtml(d.file_format);
            const safeId = Formatters.escapeHtml(d.id);

            return `
                <tr class="hover:bg-slate-50/80 transition-colors border-b border-slate-200/80 last:border-0 ${isActive ? 'bg-indigo-50/30' : ''}">
                    <td class="px-6 py-4">
                        <div class="flex items-center gap-2">
                            <div class="p-1.5 rounded bg-slate-100 text-slate-600 font-mono text-[10px] uppercase font-bold">
                                ${safeFormat}
                            </div>
                            <div>
                                <div class="font-semibold text-slate-900 text-sm">${safeFilename}</div>
                                <div class="text-xs text-slate-400 font-mono">${safeId.substring(0, 8)}...</div>
                            </div>
                        </div>
                    </td>
                    <td class="px-6 py-4 text-xs text-slate-600">
                        ${Formatters.dateTime(d.upload_timestamp)}
                    </td>
                    <td class="px-6 py-4 text-sm font-mono text-slate-700 text-right">
                        ${Formatters.number(d.total_cleaned_rows)} <span class="text-xs text-slate-400">/ ${Formatters.number(d.total_raw_rows)}</span>
                    </td>
                    <td class="px-6 py-4 text-center">
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${badge.bg} ${badge.text} border ${badge.border}">
                            ${d.health_score !== null && d.health_score !== undefined ? `${d.health_score.toFixed(1)}%` : 'N/A'}
                        </span>
                    </td>
                    <td class="px-6 py-4 text-right">
                        <div class="flex items-center justify-end gap-2">
                            <button data-action="analyze" data-id="${safeId}" class="px-2.5 py-1 text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded border border-indigo-200 transition">
                                Dashboard
                            </button>
                            <button data-action="audit" data-id="${safeId}" class="px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100 rounded border border-slate-200 transition">
                                Quality
                            </button>
                            <a href="${API.getExportCleanedUrl(d.id)}" download class="p-1 text-slate-500 hover:text-slate-900 rounded hover:bg-slate-100 transition" title="Download Cleaned CSV">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                            </a>
                            <button data-action="delete" data-id="${safeId}" data-filename="${safeFilename}" class="p-1 text-rose-500 hover:text-rose-700 rounded hover:bg-rose-50 transition" title="Delete Dataset">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        // Bind dynamic action buttons
        tableBody.querySelectorAll('button[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = btn.dataset.action;
                const id = btn.dataset.id;
                const filename = btn.dataset.filename;

                if (action === 'analyze') {
                    State.setActiveDataset(id);
                    State.setView('dashboard');
                } else if (action === 'audit') {
                    Audit.openDetailedAuditModal(id);
                } else if (action === 'delete') {
                    UI.confirm(
                        'Delete Dataset',
                        `Are you sure you want to permanently delete "${filename}"? All associated analytical records and quality logs will be removed.`,
                        'Delete Dataset',
                        async () => {
                            try {
                                await API.deleteDataset(id);
                                UI.showToast(`Dataset "${filename}" was deleted.`, 'success');
                                await State.refreshDatasets();
                                if (State.activeDatasetId === id) {
                                    if (State.datasets.length > 0) {
                                        await State.setActiveDataset(State.datasets[0].id);
                                    } else {
                                        await State.setActiveDataset(null);
                                    }
                                }
                            } catch (err) {
                                console.error('Delete failed:', err);
                                UI.showToast('Failed to delete dataset.', 'error');
                            }
                        }
                    );
                }
            });
        });
    }
};
