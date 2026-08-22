/**
 * Chart.js Integration Module.
 * Encapsulates Chart.js lifecycle, destruction, responsive canvas resizing, and custom tooltips.
 */

const chartInstances = {};

export const Charts = {
    destroyChart(canvasId) {
        if (chartInstances[canvasId]) {
            chartInstances[canvasId].destroy();
            delete chartInstances[canvasId];
        }
    },

    renderTrendChart(canvasId, trends, metricKey = 'revenue') {
        this.destroyChart(canvasId);
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        if (!trends || trends.length === 0) {
            canvas.classList.add('hidden');
            document.getElementById(`${canvasId}-empty`)?.classList.remove('hidden');
            return;
        }

        canvas.classList.remove('hidden');
        document.getElementById(`${canvasId}-empty`)?.classList.add('hidden');

        const labels = trends.map(t => t.period);
        const dataValues = trends.map(t => t[metricKey] !== null ? t[metricKey] : 0);

        const metricLabels = {
            revenue: 'Revenue ($)',
            profit: 'Profit ($)',
            order_count: 'Orders',
        };

        const metricColors = {
            revenue: { line: '#4F46E5', fill: 'rgba(79, 70, 229, 0.08)' },
            profit: { line: '#10B981', fill: 'rgba(16, 185, 129, 0.08)' },
            order_count: { line: '#0EA5E9', fill: 'rgba(14, 165, 233, 0.08)' },
        };

        const color = metricColors[metricKey] || metricColors.revenue;

        const ctx = canvas.getContext('2d');
        chartInstances[canvasId] = new window.Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: metricLabels[metricKey] || 'Metric',
                    data: dataValues,
                    borderColor: color.line,
                    backgroundColor: color.fill,
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.25,
                    pointBackgroundColor: color.line,
                    pointRadius: trends.length > 1 ? 4 : 6,
                    pointHoverRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index',
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#0F172A',
                        titleColor: '#F8FAFC',
                        bodyColor: '#F8FAFC',
                        padding: 10,
                        cornerRadius: 6,
                        callbacks: {
                            label(context) {
                                const val = context.parsed.y;
                                if (metricKey === 'order_count') {
                                    return ` Orders: ${new Intl.NumberFormat().format(val)}`;
                                }
                                return ` ${metricLabels[metricKey]}: $${new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: 'Inter', size: 11 }, color: '#64748B' }
                    },
                    y: {
                        grid: { color: '#F1F5F9' },
                        ticks: {
                            font: { family: 'Inter', size: 11 },
                            color: '#64748B',
                            callback(value) {
                                if (metricKey === 'order_count') return value;
                                if (Math.abs(value) >= 1000) return `$${value / 1000}k`;
                                return `$${value}`;
                            }
                        }
                    }
                }
            }
        });
    },

    renderHorizontalBarChart(canvasId, items, labelKey, valueKey, emptyId, valuePrefix = '$') {
        this.destroyChart(canvasId);
        const canvas = document.getElementById(canvasId);
        const emptyContainer = document.getElementById(emptyId);

        if (!canvas) return;

        if (!items || items.length === 0) {
            canvas.classList.add('hidden');
            if (emptyContainer) emptyContainer.classList.remove('hidden');
            return;
        }

        canvas.classList.remove('hidden');
        if (emptyContainer) emptyContainer.classList.add('hidden');

        const labels = items.map(item => item[labelKey]);
        const dataValues = items.map(item => item[valueKey]);

        // Palette of restrained business colors
        const palette = [
            '#4F46E5', '#6366F1', '#818CF8', '#A5B4FC', '#C7D2FE',
            '#0EA5E9', '#38BDF8', '#7DD3FC', '#BAE6FD', '#E0F2FE'
        ];

        const ctx = canvas.getContext('2d');
        chartInstances[canvasId] = new window.Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    data: dataValues,
                    backgroundColor: labels.map((_, i) => palette[i % palette.length]),
                    borderRadius: 4,
                    barThickness: 18,
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#0F172A',
                        titleColor: '#F8FAFC',
                        bodyColor: '#F8FAFC',
                        padding: 10,
                        cornerRadius: 6,
                        callbacks: {
                            label(context) {
                                const val = context.parsed.x;
                                const item = items[context.dataIndex];
                                const share = item.revenue_share_pct !== undefined ? ` (${item.revenue_share_pct.toFixed(1)}%)` : '';
                                return ` Revenue: $${new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val)}${share}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: '#F1F5F9' },
                        ticks: {
                            font: { family: 'Inter', size: 11 },
                            color: '#64748B',
                            callback(value) {
                                if (Math.abs(value) >= 1000) return `$${value / 1000}k`;
                                return `$${value}`;
                            }
                        }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { font: { family: 'Inter', size: 11 }, color: '#334155' }
                    }
                }
            }
        });
    }
};
