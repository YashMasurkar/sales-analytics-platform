/**
 * Upload Module.
 * Manages file dropzone, format/size pre-checks, upload processing pipeline state, and demo dataset loading.
 */

import { API } from './api.js';
import { State } from './state.js';
import { UI } from './ui.js';
import { Audit } from './audit.js';

export const Upload = {
    init() {
        this.bindEvents();
    },

    bindEvents() {
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        const browseBtn = document.getElementById('browse-file-btn');
        const demoBtn = document.getElementById('try-demo-btn');
        const emptyDemoBtn = document.getElementById('empty-try-demo-btn');

        if (browseBtn && fileInput) {
            browseBtn.addEventListener('click', () => fileInput.click());
        }

        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                if (e.target.files && e.target.files[0]) {
                    this.handleFileUpload(e.target.files[0]);
                }
            });
        }

        if (dropZone) {
            ['dragenter', 'dragover'].forEach(eventName => {
                dropZone.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    dropZone.classList.add('border-indigo-500', 'bg-indigo-50/30');
                });
            });

            ['dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    dropZone.classList.remove('border-indigo-500', 'bg-indigo-50/30');
                });
            });

            dropZone.addEventListener('drop', (e) => {
                const files = e.dataTransfer?.files;
                if (files && files[0]) {
                    this.handleFileUpload(files[0]);
                }
            });
        }

        if (demoBtn) {
            demoBtn.addEventListener('click', () => this.loadDemoDataset());
        }
        if (emptyDemoBtn) {
            emptyDemoBtn.addEventListener('click', () => this.loadDemoDataset());
        }
    },

    setProcessingState(isProcessing, stepText = 'Processing dataset...') {
        const uploadForm = document.getElementById('upload-form-container');
        const processingContainer = document.getElementById('upload-processing-container');
        const stepLabel = document.getElementById('upload-step-label');

        if (isProcessing) {
            uploadForm?.classList.add('hidden');
            processingContainer?.classList.remove('hidden');
            if (stepLabel) stepLabel.textContent = stepText;
        } else {
            uploadForm?.classList.remove('hidden');
            processingContainer?.classList.add('hidden');
        }
    },

    async handleFileUpload(file) {
        // Basic pre-validation
        const allowedExts = ['.csv', '.xlsx', '.xls'];
        const fileName = file.name.toLowerCase();
        const hasValidExt = allowedExts.some(ext => fileName.endsWith(ext));

        if (!hasValidExt) {
            UI.showToast(`Unsupported format. Supported: CSV, XLSX, XLS.`, 'error');
            return;
        }

        if (file.size > 50 * 1024 * 1024) {
            UI.showToast(`File size exceeds the 50MB maximum limit.`, 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        this.setProcessingState(true, 'Uploading & reading dataset...');

        try {
            // Pipeline progress transitions
            setTimeout(() => {
                const label = document.getElementById('upload-step-label');
                if (label) label.textContent = 'Validating schema & mapping fields...';
            }, 300);

            setTimeout(() => {
                const label = document.getElementById('upload-step-label');
                if (label) label.textContent = 'Cleaning data & auditing data quality...';
            }, 600);

            const uploadResult = await API.uploadDataset(formData);

            UI.showToast(`Dataset "${uploadResult.filename}" uploaded successfully!`, 'success');
            await State.refreshDatasets();
            await State.setActiveDataset(uploadResult.dataset_id);

            this.setProcessingState(false);
            
            // Present Data Quality Review Gate immediately after upload
            Audit.showReviewGate(uploadResult);

        } catch (err) {
            this.setProcessingState(false);
            console.error('Upload failed:', err);
            const msg = err.message || 'Something went wrong while processing your dataset.';
            UI.showToast(msg, 'error', 6000);
        } finally {
            const input = document.getElementById('file-input');
            if (input) input.value = '';
        }
    },

    async loadDemoDataset() {
        this.setProcessingState(true, 'Loading sample demo dataset...');
        try {
            const response = await fetch('/static/data/demo_sales.csv');
            if (!response.ok) {
                throw new Error('Failed to retrieve demo dataset file.');
            }
            const blob = await response.blob();
            const demoFile = new File([blob], 'superstore_sales_demo.csv', { type: 'text/csv' });
            await this.handleFileUpload(demoFile);
        } catch (err) {
            this.setProcessingState(false);
            console.error('Demo loading failed:', err);
            UI.showToast('Unable to load demo dataset.', 'error');
        }
    }
};
