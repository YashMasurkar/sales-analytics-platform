/**
 * Formatters and Presentation Helpers.
 * Formats currency, percentages, counts, and dates without altering underlying analytical values.
 */

export const Formatters = {
    currency(value, symbol = '$') {
        if (value === null || value === undefined || isNaN(value)) return 'Unavailable';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(value);
    },

    currencyCompact(value) {
        if (value === null || value === undefined || isNaN(value)) return 'Unavailable';
        if (Math.abs(value) >= 1_000_000) {
            return `$${(value / 1_000_000).toFixed(2)}M`;
        }
        if (Math.abs(value) >= 1_000) {
            return `$${(value / 1_000).toFixed(1)}k`;
        }
        return this.currency(value);
    },

    number(value) {
        if (value === null || value === undefined || isNaN(value)) return 'Unavailable';
        return new Intl.NumberFormat('en-US').format(value);
    },

    percent(value) {
        if (value === null || value === undefined || isNaN(value)) return 'Unavailable';
        const sign = value > 0 ? '+' : '';
        return `${sign}${value.toFixed(2)}%`;
    },

    date(value) {
        if (!value) return 'N/A';
        try {
            const d = new Date(value);
            return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
        } catch {
            return String(value);
        }
    },

    dateTime(value) {
        if (!value) return 'N/A';
        try {
            const d = new Date(value);
            return d.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
            });
        } catch {
            return String(value);
        }
    },

    healthBadge(score) {
        if (score === null || score === undefined) return { label: 'Unrated', bg: 'bg-slate-100', text: 'text-slate-700', border: 'border-slate-300' };
        if (score >= 90) return { label: 'Excellent Quality', bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' };
        if (score >= 75) return { label: 'Good Quality', bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' };
        if (score >= 60) return { label: 'Moderate Issues', bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' };
        return { label: 'Needs Review', bg: 'bg-rose-50', text: 'text-rose-700', border: 'border-rose-200' };
    },

    escapeHtml(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
};

