/**
 * API Client Module for Sales Analytics & BI Platform.
 * Centralizes all REST API calls with robust error handling.
 */

const API_BASE = '/api/v1';

class APIError extends Error {
    constructor(message, status, details = null) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.details = details;
    }
}

async function request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    let response;
    try {
        response = await fetch(url, options);
    } catch (networkError) {
        throw new APIError('Network error: Unable to connect to the analytics server.', 0);
    }

    if (!response.ok) {
        let errorData = {};
        try {
            errorData = await response.json();
        } catch {
            errorData = { detail: response.statusText || 'Unknown server error' };
        }
        const message = errorData.detail || `Request failed with status ${response.status}`;
        throw new APIError(message, response.status, errorData);
    }

    // If 204 or no content
    if (response.status === 204) return null;

    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
        return await response.json();
    }
    return await response.text();
}

export const API = {
    async checkHealth() {
        return await request('/health');
    },

    async uploadDataset(formData) {
        return await request('/upload', {
            method: 'POST',
            body: formData,
        });
    },

    async getDatasets() {
        return await request('/datasets');
    },

    async getDataset(id) {
        return await request(`/datasets/${encodeURIComponent(id)}`);
    },

    async deleteDataset(id) {
        return await request(`/datasets/${encodeURIComponent(id)}`, {
            method: 'DELETE',
        });
    },

    async getQualityAudit(id) {
        return await request(`/datasets/${encodeURIComponent(id)}/quality-audit`);
    },

    async getKPIs(id, filters = {}) {
        const params = new URLSearchParams();
        if (filters.startDate) params.append('start_date', filters.startDate);
        if (filters.endDate) params.append('end_date', filters.endDate);
        if (filters.category) params.append('category', filters.category);
        if (filters.region) params.append('region', filters.region);
        const queryStr = params.toString() ? `?${params.toString()}` : '';
        return await request(`/analytics/${encodeURIComponent(id)}/kpis${queryStr}`);
    },

    async getTrends(id, filters = {}) {
        const params = new URLSearchParams();
        if (filters.startDate) params.append('start_date', filters.startDate);
        if (filters.endDate) params.append('end_date', filters.endDate);
        if (filters.category) params.append('category', filters.category);
        if (filters.region) params.append('region', filters.region);
        const queryStr = params.toString() ? `?${params.toString()}` : '';
        return await request(`/analytics/${encodeURIComponent(id)}/trends${queryStr}`);
    },

    async getCategories(id, filters = {}) {
        const params = new URLSearchParams();
        if (filters.startDate) params.append('start_date', filters.startDate);
        if (filters.endDate) params.append('end_date', filters.endDate);
        if (filters.region) params.append('region', filters.region);
        const queryStr = params.toString() ? `?${params.toString()}` : '';
        return await request(`/analytics/${encodeURIComponent(id)}/categories${queryStr}`);
    },

    async getRegions(id, filters = {}) {
        const params = new URLSearchParams();
        if (filters.startDate) params.append('start_date', filters.startDate);
        if (filters.endDate) params.append('end_date', filters.endDate);
        if (filters.category) params.append('category', filters.category);
        const queryStr = params.toString() ? `?${params.toString()}` : '';
        return await request(`/analytics/${encodeURIComponent(id)}/regions${queryStr}`);
    },

    async getProducts(id, filters = {}) {
        const params = new URLSearchParams();
        if (filters.startDate) params.append('start_date', filters.startDate);
        if (filters.endDate) params.append('end_date', filters.endDate);
        if (filters.category) params.append('category', filters.category);
        if (filters.region) params.append('region', filters.region);
        const queryStr = params.toString() ? `?${params.toString()}` : '';
        return await request(`/analytics/${encodeURIComponent(id)}/products${queryStr}`);
    },

    async getFilterOptions(id) {
        return await request(`/analytics/${encodeURIComponent(id)}/filter-options`);
    },

    getExportCleanedUrl(id) {
        return `${API_BASE}/export/${encodeURIComponent(id)}/cleaned`;
    }
};
