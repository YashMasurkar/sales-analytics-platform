/**
 * Dashboard Controller Module.
 * Orchestrates KPI Cards, Charts, Tables, and Reactive Filter Interactions.
 */

import { API } from './api.js';
import { State } from './state.js';
import { Formatters } from './formatters.js';
import { Charts } from './charts.js';
import { UI } from './ui.js';

let activeTrendMetric = 'revenue';
let activeProductTab = 'top';
let cachedProducts = { top_products: [], bottom_products: [], available: false };

export const Dashboard = {
    init() {
        this.bindEvents();
        State.subscribe((event, payload) => {
            if (event === 'ACTIVE_DATASET_CHANGED' || event === 'FILTERS_CHANGED') {
                this.loadDashboardData();
            }
        });
    },

    bindEvents() {
        // Dataset Selector
        const datasetSelect = document.getElementById('dataset-selector');
        if (datasetSelect) {
            datasetSelect.addEventListener('change', (e) => {
                State.setActiveDataset(e.target.value);
            });
        }

        // Remove Selected Dataset Button
        const removeDatasetBtn = document.getElementById('dashboard-delete-dataset-btn');
        if (removeDatasetBtn) {
            removeDatasetBtn.addEventListener('click', () => {
                const datasetId = State.activeDatasetId;
                if (!datasetId) {
                    UI.showToast('Please select a dataset to remove.', 'warning');
                    return;
                }
                const currentDataset = State.datasets.find(d => d.id === datasetId) || State.activeDataset;
                const rawFilename = currentDataset?.filename || 'the selected dataset';
                const filename = Formatters.escapeHtml(rawFilename);

                UI.confirm(
                    'Delete Dataset',
                    `Are you sure you want to permanently delete "${filename}"? All associated analytical records and quality logs will be removed.`,
                    'Delete Dataset',
                    async () => {
                        try {
                            await API.deleteDataset(datasetId);
                            UI.showToast(`Dataset "${filename}" was deleted.`, 'success');
                            await State.refreshDatasets();
                            if (State.activeDatasetId === datasetId) {
                                if (State.datasets.length > 0) {
                                    await State.setActiveDataset(State.datasets[0].id);
                                } else {
                                    await State.setActiveDataset(null);
                                    State.setView('upload');
                                }
                            }
                        } catch (err) {
                            console.error('Delete failed:', err);
                            const msg = err.message || 'Failed to delete dataset.';
                            UI.showToast(msg, 'error');
                        }
                    }
                );
            });
        }


        // Date & Dimension Filters
        const startDateInput = document.getElementById('filter-start-date');
        const endDateInput = document.getElementById('filter-end-date');
        const categorySelect = document.getElementById('filter-category');
        const regionSelect = document.getElementById('filter-region');
        const resetBtn = document.getElementById('filter-reset-btn');
        const exportBtn = document.getElementById('export-cleaned-btn');

        if (startDateInput) {
            startDateInput.addEventListener('change', (e) => State.setFilter('startDate', e.target.value));
        }
        if (endDateInput) {
            endDateInput.addEventListener('change', (e) => State.setFilter('endDate', e.target.value));
        }
        if (categorySelect) {
            categorySelect.addEventListener('change', (e) => State.setFilter('category', e.target.value));
        }
        if (regionSelect) {
            regionSelect.addEventListener('change', (e) => State.setFilter('region', e.target.value));
        }
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                if (startDateInput) startDateInput.value = '';
                if (endDateInput) endDateInput.value = '';
                if (categorySelect) categorySelect.value = '';
                if (regionSelect) regionSelect.value = '';
                State.resetFilters();
            });
        }
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                if (!State.activeDatasetId) {
                    UI.showToast('Please select a dataset to export.', 'warning');
                    return;
                }
                window.location.href = API.getExportCleanedUrl(State.activeDatasetId);
            });
        }

        // Trend Metric Switcher
        const trendButtons = document.querySelectorAll('.trend-metric-btn');
        trendButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                trendButtons.forEach(b => {
                    b.classList.remove('bg-white', 'text-slate-900', 'shadow-xs');
                    b.classList.add('text-slate-500');
                });
                const target = e.currentTarget;
                target.classList.add('bg-white', 'text-slate-900', 'shadow-xs');
                target.classList.remove('text-slate-500');

                activeTrendMetric = target.dataset.metric;
                this.loadTrends();
            });
        });

        // Product Tabs
        const prodTopBtn = document.getElementById('prod-tab-top');
        const prodBottomBtn = document.getElementById('prod-tab-bottom');
        if (prodTopBtn && prodBottomBtn) {
            prodTopBtn.addEventListener('click', () => {
                prodTopBtn.className = 'px-3 py-1.5 text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-md transition';
                prodBottomBtn.className = 'px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 bg-white border border-slate-200 rounded-md transition';
                activeProductTab = 'top';
                this.renderProductTable();
            });
            prodBottomBtn.addEventListener('click', () => {
                prodBottomBtn.className = 'px-3 py-1.5 text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-md transition';
                prodTopBtn.className = 'px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 bg-white border border-slate-200 rounded-md transition';
                activeProductTab = 'bottom';
                this.renderProductTable();
            });
        }
    },

    updateFilterOptions(filterOptions) {
        const categorySelect = document.getElementById('filter-category');
        const regionSelect = document.getElementById('filter-region');
        const startDateInput = document.getElementById('filter-start-date');
        const endDateInput = document.getElementById('filter-end-date');

        if (categorySelect) {
            categorySelect.innerHTML = '<option value="">All Categories</option>';
            filterOptions.categories.forEach(cat => {
                const opt = document.createElement('option');
                opt.value = cat;
                opt.textContent = cat;
                categorySelect.appendChild(opt);
            });
            categorySelect.disabled = filterOptions.categories.length === 0;
        }

        if (regionSelect) {
            regionSelect.innerHTML = '<option value="">All Regions</option>';
            filterOptions.regions.forEach(reg => {
                const opt = document.createElement('option');
                opt.value = reg;
                opt.textContent = reg;
                regionSelect.appendChild(opt);
            });
            regionSelect.disabled = filterOptions.regions.length === 0;
        }

        if (startDateInput && filterOptions.min_date) {
            startDateInput.min = filterOptions.min_date;
            startDateInput.max = filterOptions.max_date || '';
        }
        if (endDateInput && filterOptions.max_date) {
            endDateInput.min = filterOptions.min_date || '';
            endDateInput.max = filterOptions.max_date;
        }

    },

    async loadDashboardData() {
        const datasetId = State.activeDatasetId;
        if (!datasetId) {
            document.getElementById('dashboard-content')?.classList.add('hidden');
            document.getElementById('dashboard-empty')?.classList.remove('hidden');
            return;
        }

        document.getElementById('dashboard-content')?.classList.remove('hidden');
        document.getElementById('dashboard-empty')?.classList.add('hidden');

        // Update Dataset Selector value
        const selector = document.getElementById('dataset-selector');
        if (selector && selector.value !== datasetId) {
            selector.value = datasetId;
        }

        // Run data fetching in parallel
        await Promise.all([
            this.loadKPIs(),
            this.loadTrends(),
            this.loadCategories(),
            this.loadRegions(),
            this.loadProducts(),
        ]);
    },

    async loadKPIs() {
        const datasetId = State.activeDatasetId;
        try {
            const data = await API.getKPIs(datasetId, State.filters);
            
            // 1. Revenue Card
            document.getElementById('kpi-revenue').textContent = Formatters.currency(data.financials.total_revenue);
            const momEl = document.getElementById('kpi-revenue-mom');
            if (data.mom_revenue_growth_pct !== null && data.mom_revenue_growth_pct !== undefined) {
                const isPositive = data.mom_revenue_growth_pct >= 0;
                momEl.className = `inline-flex items-center gap-1 text-xs font-semibold ${isPositive ? 'text-emerald-700 bg-emerald-50 border border-emerald-200' : 'text-rose-700 bg-rose-50 border border-rose-200'} px-2 py-0.5 rounded-full`;
                momEl.innerHTML = `${isPositive ? '↑' : '↓'} ${Formatters.percent(data.mom_revenue_growth_pct)} MoM`;
                momEl.classList.remove('hidden');
            } else {
                momEl.classList.add('hidden');
            }

            // 2. Profit Card
            const profitEl = document.getElementById('kpi-profit');
            const profitMarginEl = document.getElementById('kpi-profit-margin');
            if (data.available_metrics.profit && data.financials.total_profit !== null) {
                profitEl.textContent = Formatters.currency(data.financials.total_profit);
                profitEl.className = 'text-2xl font-bold tracking-tight text-slate-900';
                const margin = data.financials.profit_margin_pct;
                profitMarginEl.textContent = margin !== null ? `Margin: ${margin.toFixed(1)}%` : '';
                profitMarginEl.className = 'text-xs text-slate-500 font-medium';
            } else {
                profitEl.textContent = 'Unavailable';
                profitEl.className = 'text-2xl font-semibold tracking-tight text-slate-400';
                profitMarginEl.textContent = 'Cost data not provided';
                profitMarginEl.className = 'text-xs text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 inline-block font-medium';
            }

            // 3. Orders Card
            document.getElementById('kpi-orders').textContent = Formatters.number(data.volumes.total_orders);
            document.getElementById('kpi-aov').textContent = `AOV: ${Formatters.currency(data.volumes.average_order_value)}`;

            // 4. Customers Card
            const custEl = document.getElementById('kpi-customers');
            const unitsEl = document.getElementById('kpi-units');
            if (data.available_metrics.unique_customers && data.volumes.total_unique_customers !== null) {
                custEl.textContent = Formatters.number(data.volumes.total_unique_customers);
                custEl.className = 'text-2xl font-bold tracking-tight text-slate-900';
                custEl.title = '';
                unitsEl.textContent = data.volumes.total_units_sold !== null ? `Units Sold: ${Formatters.number(data.volumes.total_units_sold)}` : '';
                unitsEl.className = 'text-xs text-slate-500 font-medium';
            } else {
                custEl.textContent = 'Unavailable';
                custEl.className = 'text-2xl font-semibold tracking-tight text-slate-400';
                unitsEl.textContent = 'Customer ID not provided';
                unitsEl.className = 'text-xs text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 inline-block font-medium';
            }

        } catch (err) {
            console.error('Failed to load KPIs:', err);
            UI.showToast('Unable to load executive KPI metrics.', 'error');
        }
    },

    async loadTrends() {
        const datasetId = State.activeDatasetId;
        try {
            const data = await API.getTrends(datasetId, State.filters);
            Charts.renderTrendChart('trend-chart-canvas', data.trends, activeTrendMetric);
        } catch (err) {
            console.error('Failed to load Trends:', err);
        }
    },

    async loadCategories() {
        const datasetId = State.activeDatasetId;
        try {
            const data = await API.getCategories(datasetId, State.filters);
            if (data.available && data.categories.length > 0) {
                Charts.renderHorizontalBarChart('category-chart-canvas', data.categories, 'category', 'revenue', 'category-chart-empty');
            } else {
                Charts.destroyChart('category-chart-canvas');
                document.getElementById('category-chart-canvas')?.classList.add('hidden');
                document.getElementById('category-chart-empty')?.classList.remove('hidden');
            }
        } catch (err) {
            console.error('Failed to load Categories:', err);
        }
    },

    async loadRegions() {
        const datasetId = State.activeDatasetId;
        try {
            const data = await API.getRegions(datasetId, State.filters);
            if (data.available && data.regions.length > 0) {
                Charts.renderHorizontalBarChart('region-chart-canvas', data.regions, 'region', 'revenue', 'region-chart-empty');
            } else {
                Charts.destroyChart('region-chart-canvas');
                document.getElementById('region-chart-canvas')?.classList.add('hidden');
                document.getElementById('region-chart-empty')?.classList.remove('hidden');
            }
        } catch (err) {
            console.error('Failed to load Regions:', err);
        }
    },

    async loadProducts() {
        const datasetId = State.activeDatasetId;
        try {
            cachedProducts = await API.getProducts(datasetId, State.filters);
            this.renderProductTable();
        } catch (err) {
            console.error('Failed to load Products:', err);
        }
    },

    renderProductTable() {
        const tableBody = document.getElementById('product-table-body');
        const emptyState = document.getElementById('product-table-empty');
        const tableContainer = document.getElementById('product-table-container');

        if (!tableBody) return;

        if (!cachedProducts.available) {
            tableContainer?.classList.add('hidden');
            emptyState?.classList.remove('hidden');
            return;
        }

        tableContainer?.classList.remove('hidden');
        emptyState?.classList.add('hidden');

        const items = activeProductTab === 'top' ? (cachedProducts.top_products || []) : (cachedProducts.bottom_products || []);
        if (items.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="4" class="px-4 py-8 text-center text-sm text-slate-400">No products found matching filters.</td></tr>`;
            return;
        }

        tableBody.innerHTML = items.map((prod, index) => {
            const rank = activeProductTab === 'top' ? index + 1 : (cachedProducts.bottom_products.length - index);
            const rankBadge = activeProductTab === 'top' && rank <= 3 
                ? `<span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-amber-100 text-amber-800 text-xs font-bold">${rank}</span>`
                : `<span class="text-xs font-medium text-slate-400">${rank}</span>`;

            return `
                <tr class="hover:bg-slate-50/80 transition-colors border-b border-slate-100 last:border-0">
                    <td class="px-4 py-3 text-center w-12">${rankBadge}</td>
                    <td class="px-4 py-3 font-medium text-slate-900 text-sm truncate max-w-xs" title="${prod.product_name}">
                        ${prod.product_name}
                    </td>
                    <td class="px-4 py-3 text-right font-semibold text-slate-900 text-sm">
                        ${Formatters.currency(prod.revenue)}
                    </td>
                    <td class="px-4 py-3 text-right text-slate-600 text-sm">
                        ${Formatters.number(prod.order_count)}
                    </td>
                </tr>
            `;
        }).join('');
    }
};
