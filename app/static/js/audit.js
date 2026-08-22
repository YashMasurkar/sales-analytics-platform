/**
 * Data Quality & Audit Module.
 * Renders the Post-Upload Quality Review Gate, Standalone Quality Tab, and Detailed Audit Modal.
 */

import { API } from './api.js';
import { State } from './state.js';
import { Formatters } from './formatters.js';
import { UI } from './ui.js';

export const Audit = {
    init() {
        this.bindEvents();
        State.subscribe((event, payload) => {
            if (event === 'ACTIVE_DATASET_CHANGED' && State.activeView === 'quality') {
                this.loadStandaloneAudit();
            }
            if (event === 'VIEW_CHANGED' && payload === 'quality') {
                this.loadStandaloneAudit();
            }
        });
    },

    bindEvents() {
        // Review Gate Buttons
        const continueBtn = document.getElementById('review-gate-continue-btn');
        const viewDetailedBtn = document.getElementById('review-gate-details-btn');
        const closeAuditModalBtn = document.getElementById('close-audit-modal-btn');
        const standaloneDetailedBtn = document.getElementById('standalone-view-details-btn');

        if (continueBtn) {
            continueBtn.addEventListener('click', () => {
                State.setView('dashboard');
            });
        }

        if (viewDetailedBtn) {
            viewDetailedBtn.addEventListener('click', () => {
                this.openDetailedAuditModal(State.activeDatasetId);
            });
        }

        if (standaloneDetailedBtn) {
            standaloneDetailedBtn.addEventListener('click', () => {
                this.openDetailedAuditModal(State.activeDatasetId);
            });
        }

        if (closeAuditModalBtn) {
            closeAuditModalBtn.addEventListener('click', () => {
                UI.closeModal('audit-modal');
            });
        }
    },

    showReviewGate(data) {
        State.setView('quality');
        this.renderAuditSummary(data, 'review-gate');
    },

    async loadStandaloneAudit() {
        const datasetId = State.activeDatasetId;
        if (!datasetId) {
            document.getElementById('quality-content')?.classList.add('hidden');
            document.getElementById('quality-empty')?.classList.remove('hidden');
            return;
        }

        document.getElementById('quality-content')?.classList.remove('hidden');
        document.getElementById('quality-empty')?.classList.add('hidden');

        try {
            const auditData = await API.getQualityAudit(datasetId);
            this.renderAuditSummary(auditData, 'quality');
        } catch (err) {
            console.error('Failed to load quality audit:', err);
            UI.showToast('Unable to load data quality audit.', 'error');
        }
    },

    renderAuditSummary(audit, prefix = 'quality') {
        const score = audit.health_score ?? 100;
        const badge = Formatters.healthBadge(score);

        // Score Badge
        const scoreEl = document.getElementById(`${prefix}-score-value`);
        const badgeEl = document.getElementById(`${prefix}-score-badge`);
        if (scoreEl) scoreEl.textContent = `${score.toFixed(1)}/100`;
        if (badgeEl) {
            badgeEl.className = `inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold ${badge.bg} ${badge.text} border ${badge.border}`;
            badgeEl.textContent = badge.label;
        }

        // Key Metrics
        const setVal = (id, val) => {
            const el = document.getElementById(`${prefix}-${id}`);
            if (el) el.textContent = Formatters.number(val);
        };

        setVal('raw-rows', audit.total_raw_rows);
        setVal('valid-rows', audit.valid_rows);
        setVal('excluded-rows', audit.excluded_rows);
        setVal('duplicate-rows', audit.exact_duplicates_count);
        setVal('invalid-dates', audit.invalid_dates_count);
        setVal('invalid-numerics', audit.invalid_numerics_count);
        setVal('derived-values', audit.derived_value_count);

        // Total Anomalies
        const totalAnomalies = typeof audit.anomalies_detected === 'object' && audit.anomalies_detected !== null
            ? Object.values(audit.anomalies_detected).reduce((a, b) => a + b, 0)
            : 0;
        setVal('anomalies-count', totalAnomalies);
    },

    async openDetailedAuditModal(datasetId) {
        if (!datasetId) return;

        try {
            const audit = await API.getQualityAudit(datasetId);

            // Modal Header
            const titleEl = document.getElementById('audit-modal-filename');
            if (titleEl) titleEl.textContent = State.activeDataset?.filename || 'Dataset Audit';

            // Missing Values Table
            const missingTbody = document.getElementById('audit-modal-missing-body');
            const missingEntries = Object.entries(audit.missing_values_by_field || {});
            if (missingTbody) {
                if (missingEntries.length === 0) {
                    missingTbody.innerHTML = `<tr><td colspan="2" class="px-4 py-3 text-center text-xs text-slate-400">No missing values detected.</td></tr>`;
                } else {
                    missingTbody.innerHTML = missingEntries.map(([col, cnt]) => `
                        <tr class="border-b border-slate-100 last:border-0">
                            <td class="px-4 py-2 font-mono text-xs text-slate-700 font-medium">${col}</td>
                            <td class="px-4 py-2 text-right text-xs font-semibold text-rose-600">${Formatters.number(cnt)}</td>
                        </tr>
                    `).join('');
                }
            }

            // Exclusion Reasons Table
            const exclTbody = document.getElementById('audit-modal-exclusion-body');
            const exclEntries = Object.entries(audit.exclusion_reasons || {});
            if (exclTbody) {
                if (exclEntries.length === 0) {
                    exclTbody.innerHTML = `<tr><td colspan="2" class="px-4 py-3 text-center text-xs text-slate-400">No records were excluded.</td></tr>`;
                } else {
                    exclTbody.innerHTML = exclEntries.map(([reason, cnt]) => `
                        <tr class="border-b border-slate-100 last:border-0">
                            <td class="px-4 py-2 text-xs text-slate-700 font-medium">${reason}</td>
                            <td class="px-4 py-2 text-right text-xs font-semibold text-rose-600">${Formatters.number(cnt)}</td>
                        </tr>
                    `).join('');
                }
            }

            // Anomalies List
            const anomalyContainer = document.getElementById('audit-modal-anomalies');
            const anomalyEntries = Object.entries(audit.anomalies_detected || {});
            if (anomalyContainer) {
                anomalyContainer.innerHTML = anomalyEntries.map(([name, count]) => {
                    const label = name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    const isZero = count === 0;
                    return `
                        <div class="flex items-center justify-between p-3 rounded-lg border ${isZero ? 'bg-slate-50 border-slate-200' : 'bg-amber-50/60 border-amber-200'}">
                            <span class="text-xs font-medium ${isZero ? 'text-slate-600' : 'text-amber-900'}">${label}</span>
                            <span class="text-xs font-bold ${isZero ? 'text-slate-400' : 'text-amber-700'}">${Formatters.number(count)}</span>
                        </div>
                    `;
                }).join('');
            }

            // Changelog / Derivations List
            const changelogList = document.getElementById('audit-modal-changelog');
            const changelogs = audit.changelog_summary || [];
            if (changelogList) {
                if (changelogs.length === 0) {
                    changelogList.innerHTML = `<li class="text-xs text-slate-400">No automatic transformations required.</li>`;
                } else {
                    changelogList.innerHTML = changelogs.map(entry => `
                        <li class="flex items-start gap-2 text-xs text-slate-700">
                            <span class="text-indigo-500 mt-0.5">•</span>
                            <span>${entry}</span>
                        </li>
                    `).join('');
                }
            }

            UI.openModal('audit-modal');

        } catch (err) {
            console.error('Failed to load detailed audit:', err);
            UI.showToast('Unable to open detailed audit report.', 'error');
        }
    }
};
