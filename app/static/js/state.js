/**
 * Application State Management.
 * Manages active dataset, reactive filters, view navigation, and notification subscriptions.
 */

import { API } from './api.js';

class AppState {
    constructor() {
        this.activeDatasetId = null;
        this.activeDataset = null;
        this.datasets = [];
        this.activeView = 'dashboard'; // 'dashboard' | 'datasets' | 'quality' | 'upload' | 'about'
        this.filters = {
            startDate: '',
            endDate: '',
            category: '',
            region: '',
        };
        this.filterOptions = {
            minDate: null,
            maxDate: null,
            categories: [],
            regions: [],
        };
        this.listeners = new Set();
    }

    subscribe(listener) {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    notify(event, payload = null) {
        for (const listener of this.listeners) {
            try {
                listener(event, payload, this);
            } catch (err) {
                console.error('State listener error:', err);
            }
        }
    }

    async init() {
        await this.refreshDatasets();
        if (this.datasets.length > 0) {
            // Select most recent dataset by default
            await this.setActiveDataset(this.datasets[0].id);
        } else {
            this.setView('upload');
        }
    }

    async refreshDatasets() {
        try {
            this.datasets = await API.getDatasets();
            this.notify('DATASETS_LOADED', this.datasets);
        } catch (err) {
            console.error('Failed to load datasets:', err);
            this.notify('DATASETS_ERROR', err);
        }
    }

    async setActiveDataset(datasetId) {
        if (!datasetId) {
            this.activeDatasetId = null;
            this.activeDataset = null;
            this.notify('ACTIVE_DATASET_CHANGED', null);
            return;
        }

        try {
            this.activeDatasetId = datasetId;
            this.activeDataset = await API.getDataset(datasetId);
            // Load filter options
            this.filterOptions = await API.getFilterOptions(datasetId);
            // Reset filters to bounds
            this.filters = {
                startDate: '',
                endDate: '',
                category: '',
                region: '',
            };
            this.notify('ACTIVE_DATASET_CHANGED', {
                dataset: this.activeDataset,
                filterOptions: this.filterOptions,
            });
        } catch (err) {
            console.error(`Failed to activate dataset ${datasetId}:`, err);
            this.notify('ACTIVE_DATASET_ERROR', err);
        }
    }

    setFilter(key, value) {
        this.filters[key] = value || '';
        this.notify('FILTERS_CHANGED', this.filters);
    }

    resetFilters() {
        this.filters = {
            startDate: '',
            endDate: '',
            category: '',
            region: '',
        };
        this.notify('FILTERS_CHANGED', this.filters);
    }

    setView(viewName) {
        this.activeView = viewName;
        this.notify('VIEW_CHANGED', viewName);
    }
}

export const State = new AppState();
