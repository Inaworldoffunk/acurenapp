// Acuren Inspection Progress Tracker - Main Application
class AcurenApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.currentView = 'dashboard';
        this.currentPage = 1;
        this.tasksPerPage = 50;
        this.tasks = [];
        this.filteredTasks = [];
        this.dashboardData = {};
        
        this.init();
    }

    async init() {
        this.showLoadingScreen();
        await this.loadInitialData();
        this.setupEventListeners();
        this.hideLoadingScreen();
        this.showView('dashboard');
    }

    showLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        const mainApp = document.getElementById('main-app');
        
        loadingScreen.classList.remove('hidden');
        mainApp.classList.add('hidden');
        
        // Simulate loading progress
        const progressBar = document.querySelector('.loading-progress');
        const loadingText = document.querySelector('.loading-text');
        
        const loadingSteps = [
            { progress: 20, text: 'Connecting to database...' },
            { progress: 40, text: 'Loading inspection data...' },
            { progress: 60, text: 'Initializing dashboard...' },
            { progress: 80, text: 'Setting up user interface...' },
            { progress: 100, text: 'Ready!' }
        ];
        
        let currentStep = 0;
        const stepInterval = setInterval(() => {
            if (currentStep < loadingSteps.length) {
                const step = loadingSteps[currentStep];
                progressBar.style.width = `${step.progress}%`;
                loadingText.textContent = step.text;
                currentStep++;
            } else {
                clearInterval(stepInterval);
            }
        }, 600);
    }

    hideLoadingScreen() {
        setTimeout(() => {
            const loadingScreen = document.getElementById('loading-screen');
            const mainApp = document.getElementById('main-app');
            
            loadingScreen.classList.add('hidden');
            mainApp.classList.remove('hidden');
        }, 3000);
    }

    async loadInitialData() {
        try {
            // Load dashboard data
            await this.loadDashboardData();
            
            // Load tasks
            await this.loadTasks();
            
            // Load lookup data
            await this.loadLookupData();
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showNotification('Error loading data. Using demo data.', 'error');
            this.loadDemoData();
        }
    }

    async loadDashboardData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/dashboard/summary`);
            if (response.ok) {
                this.dashboardData = await response.json();
                this.updateDashboard();
            } else {
                throw new Error('Failed to load dashboard data');
            }
        } catch (error) {
            console.error('Dashboard data error:', error);
            this.loadDemoDashboard();
        }
    }

    async loadTasks() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/tasks?page=${this.currentPage}&per_page=${this.tasksPerPage}`);
            if (response.ok) {
                const data = await response.json();
                this.tasks = data.tasks;
                this.filteredTasks = [...this.tasks];
                this.updateTasksTable();
            } else {
                throw new Error('Failed to load tasks');
            }
        } catch (error) {
            console.error('Tasks loading error:', error);
            this.loadDemoTasks();
        }
    }

    async loadLookupData() {
        try {
            // Load inspectors, sites, methods, etc.
            const [inspectors, sites, methods, statusTypes] = await Promise.all([
                fetch(`${this.apiBaseUrl}/lookups/inspectors`).then(r => r.json()),
                fetch(`${this.apiBaseUrl}/lookups/sites`).then(r => r.json()),
                fetch(`${this.apiBaseUrl}/lookups/methods`).then(r => r.json()),
                fetch(`${this.apiBaseUrl}/lookups/status-types`).then(r => r.json())
            ]);
            
            this.populateFilterDropdowns({ inspectors, sites, methods, statusTypes });
        } catch (error) {
            console.error('Lookup data error:', error);
            this.loadDemoLookups();
        }
    }

    loadDemoData() {
        this.loadDemoDashboard();
        this.loadDemoTasks();
        this.loadDemoLookups();
    }

    loadDemoDashboard() {
        this.dashboardData = {
            summary: {
                total_tasks: 1804,
                claimed_tasks: 156,
                completed_tasks: 89,
                pending_tasks: 342,
                overdue_tasks: 23
            },
            by_site: [
                { site: '2901', task_count: 456, completed_count: 234 },
                { site: '1201', task_count: 234, completed_count: 156 },
                { site: '7101', task_count: 123, completed_count: 45 }
            ],
            by_inspector: [
                { inspector: 'Kent Manuel', task_count: 45, completed_count: 23 },
                { inspector: 'Brad Sisk', task_count: 38, completed_count: 19 },
                { inspector: 'Hunter Doucet', task_count: 32, completed_count: 18 }
            ]
        };
        this.updateDashboard();
    }

    loadDemoTasks() {
        this.tasks = [
            {
                id: 1,
                hierarchy_item_name: '019A',
                site: '2901',
                description: 'CWS',
                method: 'VI-EXT',
                inspection_priority: 20,
                inspector: 'Unassigned',
                status: 'UnInitiated',
                due_date: '2025-04-01',
                comments: '38 PAGES'
            },
            {
                id: 2,
                hierarchy_item_name: '006AR',
                site: '2901',
                description: 'LU-1200 Recycle Comp Pkg.',
                method: 'VI-EXT',
                inspection_priority: 22,
                inspector: 'Kent Manuel',
                status: 'Claimed',
                due_date: '2025-01-05',
                comments: ''
            },
            {
                id: 3,
                hierarchy_item_name: '013A',
                site: '2901',
                description: 'Catalyst Tote',
                method: 'VI-EXT',
                inspection_priority: 25,
                inspector: 'Brad Sisk',
                status: 'Reported',
                due_date: '2025-02-01',
                comments: ''
            }
        ];
        this.filteredTasks = [...this.tasks];
        this.updateTasksTable();
    }

    loadDemoLookups() {
        const inspectorFilter = document.getElementById('inspector-filter');
        const siteFilter = document.getElementById('site-filter');
        
        // Populate inspector filter
        const inspectors = ['Kent Manuel', 'Brad Sisk', 'Hunter Doucet', 'Landon Curtis'];
        inspectors.forEach(inspector => {
            const option = document.createElement('option');
            option.value = inspector;
            option.textContent = inspector;
            inspectorFilter.appendChild(option);
        });
        
        // Populate site filter
        const sites = ['1201', '1401', '1501', '2901', '7101', '7201'];
        sites.forEach(site => {
            const option = document.createElement('option');
            option.value = site;
            option.textContent = `Site ${site}`;
            siteFilter.appendChild(option);
        });
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const view = e.currentTarget.dataset.view;
                this.showView(view);
            });
        });

        // Task filters
        document.getElementById('task-search').addEventListener('input', (e) => {
            this.filterTasks();
        });

        document.getElementById('site-filter').addEventListener('change', () => {
            this.filterTasks();
        });

        document.getElementById('status-filter').addEventListener('change', () => {
            this.filterTasks();
        });

        document.getElementById('inspector-filter').addEventListener('change', () => {
            this.filterTasks();
        });

        // File upload
        this.setupFileUpload();

        // Modal
        this.setupModal();

        // Pagination
        document.getElementById('prev-page').addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.loadTasks();
            }
        });

        document.getElementById('next-page').addEventListener('click', () => {
            this.currentPage++;
            this.loadTasks();
        });

        // Site cards
        document.querySelectorAll('.site-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const site = e.currentTarget.dataset.site;
                this.showView('tasks');
                document.getElementById('site-filter').value = site;
                this.filterTasks();
            });
        });
    }

    setupFileUpload() {
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('file-input');
        const uploadProgress = document.getElementById('upload-progress');

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });

        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });
    }

    async handleFileUpload(file) {
        if (!file.name.match(/\.(xlsx|xls)$/)) {
            this.showNotification('Please select an Excel file (.xlsx or .xls)', 'error');
            return;
        }

        const uploadProgress = document.getElementById('upload-progress');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');

        uploadProgress.classList.remove('hidden');

        // Simulate upload progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            progressFill.style.width = `${progress}%`;
            progressText.textContent = `Uploading... ${Math.round(progress)}%`;
        }, 200);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${this.apiBaseUrl}/upload-scope`, {
                method: 'POST',
                body: formData
            });

            clearInterval(progressInterval);
            progressFill.style.width = '100%';
            progressText.textContent = 'Upload complete!';

            if (response.ok) {
                const result = await response.json();
                this.showNotification(`File uploaded successfully! Processed ${result.records_processed} records.`, 'success');
                
                // Refresh data
                await this.loadTasks();
                await this.loadDashboardData();
            } else {
                throw new Error('Upload failed');
            }
        } catch (error) {
            clearInterval(progressInterval);
            console.error('Upload error:', error);
            this.showNotification('Upload failed. Please try again.', 'error');
        }

        setTimeout(() => {
            uploadProgress.classList.add('hidden');
            progressFill.style.width = '0%';
        }, 2000);
    }

    setupModal() {
        const modal = document.getElementById('task-modal');
        const modalClose = document.getElementById('modal-close');
        const modalCancel = document.getElementById('modal-cancel');

        modalClose.addEventListener('click', () => {
            this.hideModal();
        });

        modalCancel.addEventListener('click', () => {
            this.hideModal();
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.hideModal();
            }
        });
    }

    showView(viewName) {
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-view="${viewName}"]`).classList.add('active');

        // Update views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });
        document.getElementById(`${viewName}-view`).classList.add('active');

        this.currentView = viewName;

        // Load view-specific data
        if (viewName === 'analytics') {
            this.loadAnalytics();
        }
    }

    updateDashboard() {
        const { summary } = this.dashboardData;
        
        // Update metric cards
        document.getElementById('total-tasks').textContent = summary.total_tasks.toLocaleString();
        document.getElementById('pending-tasks').textContent = summary.pending_tasks.toLocaleString();
        document.getElementById('claimed-tasks').textContent = summary.claimed_tasks.toLocaleString();
        document.getElementById('completed-tasks').textContent = summary.completed_tasks.toLocaleString();

        // Update progress circle
        const completionRate = Math.round((summary.completed_tasks / summary.total_tasks) * 100);
        const progressRing = document.querySelector('.progress-ring-fill');
        const progressPercentage = document.querySelector('.progress-percentage');
        
        const circumference = 2 * Math.PI * 80; // radius = 80
        const offset = circumference - (completionRate / 100) * circumference;
        
        progressRing.style.strokeDashoffset = offset;
        progressPercentage.textContent = `${completionRate}%`;
    }

    updateTasksTable() {
        const tbody = document.getElementById('tasks-table-body');
        tbody.innerHTML = '';

        this.filteredTasks.forEach(task => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><span class="task-id">${task.hierarchy_item_name}</span></td>
                <td>${task.site}</td>
                <td>${task.description}</td>
                <td>${task.method}</td>
                <td><span class="priority-badge priority-${Math.ceil(task.inspection_priority / 10)}">${task.inspection_priority}</span></td>
                <td>${task.inspector}</td>
                <td><span class="status-badge ${task.status.toLowerCase().replace(' ', '-')}">${task.status}</span></td>
                <td>${this.formatDate(task.due_date)}</td>
                <td>
                    <button class="action-btn view" onclick="app.showTaskDetails(${task.id})">View</button>
                    ${task.status === 'UnInitiated' ? `<button class="action-btn claim" onclick="app.claimTask(${task.id})">Claim</button>` : ''}
                </td>
            `;
            tbody.appendChild(row);
        });

        // Update pagination info
        const totalPages = Math.ceil(this.tasks.length / this.tasksPerPage);
        document.getElementById('pagination-info').textContent = `Page ${this.currentPage} of ${totalPages}`;
    }

    filterTasks() {
        const searchTerm = document.getElementById('task-search').value.toLowerCase();
        const siteFilter = document.getElementById('site-filter').value;
        const statusFilter = document.getElementById('status-filter').value;
        const inspectorFilter = document.getElementById('inspector-filter').value;

        this.filteredTasks = this.tasks.filter(task => {
            const matchesSearch = !searchTerm || 
                task.hierarchy_item_name.toLowerCase().includes(searchTerm) ||
                task.description.toLowerCase().includes(searchTerm);
            
            const matchesSite = !siteFilter || task.site === siteFilter;
            const matchesStatus = !statusFilter || task.status === statusFilter;
            const matchesInspector = !inspectorFilter || task.inspector === inspectorFilter;

            return matchesSearch && matchesSite && matchesStatus && matchesInspector;
        });

        this.updateTasksTable();
    }

    async claimTask(taskId) {
        try {
            const inspector = 'Current User'; // In real app, get from auth
            
            const response = await fetch(`${this.apiBaseUrl}/tasks/${taskId}/claim`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ inspector })
            });

            if (response.ok) {
                this.showNotification('Task claimed successfully!', 'success');
                await this.loadTasks();
                await this.loadDashboardData();
            } else {
                throw new Error('Failed to claim task');
            }
        } catch (error) {
            console.error('Claim task error:', error);
            this.showNotification('Failed to claim task. Please try again.', 'error');
        }
    }

    showTaskDetails(taskId) {
        const task = this.tasks.find(t => t.id === taskId);
        if (!task) return;

        const modal = document.getElementById('task-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');

        modalTitle.textContent = `Task ${task.hierarchy_item_name} - ${task.description}`;
        
        modalBody.innerHTML = `
            <div class="task-details">
                <div class="detail-row">
                    <label>Site:</label>
                    <span>${task.site}</span>
                </div>
                <div class="detail-row">
                    <label>Method:</label>
                    <span>${task.method}</span>
                </div>
                <div class="detail-row">
                    <label>Priority:</label>
                    <span>${task.inspection_priority}</span>
                </div>
                <div class="detail-row">
                    <label>Inspector:</label>
                    <span>${task.inspector}</span>
                </div>
                <div class="detail-row">
                    <label>Status:</label>
                    <span class="status-badge ${task.status.toLowerCase().replace(' ', '-')}">${task.status}</span>
                </div>
                <div class="detail-row">
                    <label>Due Date:</label>
                    <span>${this.formatDate(task.due_date)}</span>
                </div>
                <div class="detail-row">
                    <label>Comments:</label>
                    <textarea rows="3" style="width: 100%; background: rgba(42, 52, 65, 0.6); border: 1px solid rgba(0, 212, 255, 0.2); border-radius: 8px; padding: 12px; color: #F8FAFC; font-family: inherit;">${task.comments || ''}</textarea>
                </div>
            </div>
        `;

        modal.classList.remove('hidden');
    }

    hideModal() {
        document.getElementById('task-modal').classList.add('hidden');
    }

    loadAnalytics() {
        // Create sample charts
        this.createCompletionChart();
        this.createStatusChart();
        this.createInspectorChart();
        this.createSiteChart();
    }

    createCompletionChart() {
        const ctx = document.getElementById('completion-chart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Completed Tasks',
                    data: [12, 19, 15, 25, 22, 30],
                    borderColor: '#00D4FF',
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: {
                            color: '#F8FAFC'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#94A3B8' },
                        grid: { color: 'rgba(0, 212, 255, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#94A3B8' },
                        grid: { color: 'rgba(0, 212, 255, 0.1)' }
                    }
                }
            }
        });
    }

    createStatusChart() {
        const ctx = document.getElementById('status-chart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['UnInitiated', 'Claimed', 'Field Complete', 'Reported'],
                datasets: [{
                    data: [342, 156, 89, 45],
                    backgroundColor: ['#94A3B8', '#42A5F5', '#66BB6A', '#00FFB3']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: {
                            color: '#F8FAFC'
                        }
                    }
                }
            }
        });
    }

    createInspectorChart() {
        const ctx = document.getElementById('inspector-chart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Kent Manuel', 'Brad Sisk', 'Hunter Doucet', 'Landon Curtis'],
                datasets: [{
                    label: 'Tasks Completed',
                    data: [23, 19, 18, 15],
                    backgroundColor: '#00FFB3'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: {
                            color: '#F8FAFC'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#94A3B8' },
                        grid: { color: 'rgba(0, 212, 255, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#94A3B8' },
                        grid: { color: 'rgba(0, 212, 255, 0.1)' }
                    }
                }
            }
        });
    }

    createSiteChart() {
        const ctx = document.getElementById('site-chart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Site 2901', 'Site 1201', 'Site 7101', 'Site 1401'],
                datasets: [{
                    label: 'Progress %',
                    data: [89, 67, 45, 78],
                    backgroundColor: '#00D4FF'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: {
                            color: '#F8FAFC'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#94A3B8' },
                        grid: { color: 'rgba(0, 212, 255, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#94A3B8' },
                        grid: { color: 'rgba(0, 212, 255, 0.1)' },
                        max: 100
                    }
                }
            }
        });
    }

    populateFilterDropdowns(data) {
        // Populate inspector filter
        const inspectorFilter = document.getElementById('inspector-filter');
        data.inspectors.forEach(inspector => {
            const option = document.createElement('option');
            option.value = inspector.name;
            option.textContent = inspector.name;
            inspectorFilter.appendChild(option);
        });

        // Populate site filter
        const siteFilter = document.getElementById('site-filter');
        data.sites.forEach(site => {
            const option = document.createElement('option');
            option.value = site.site_code;
            option.textContent = `Site ${site.site_code}`;
            siteFilter.appendChild(option);
        });
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString();
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close">
                <i class="fas fa-times"></i>
            </button>
        `;

        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? 'rgba(102, 187, 106, 0.9)' : type === 'error' ? 'rgba(239, 83, 80, 0.9)' : 'rgba(0, 212, 255, 0.9)'};
            color: white;
            padding: 16px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            display: flex;
            align-items: center;
            gap: 12px;
            max-width: 400px;
            animation: slideInRight 0.3s ease-out;
        `;

        // Add to page
        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);

        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        });
    }
}

// Add notification animations to CSS
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 8px;
        flex: 1;
    }
    
    .notification-close {
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        transition: background-color 0.2s;
    }
    
    .notification-close:hover {
        background: rgba(255, 255, 255, 0.2);
    }
    
    .detail-row {
        display: flex;
        margin-bottom: 16px;
        align-items: flex-start;
    }
    
    .detail-row label {
        font-weight: 600;
        color: #00D4FF;
        min-width: 120px;
        margin-right: 16px;
    }
    
    .detail-row span {
        color: #F8FAFC;
    }
`;
document.head.appendChild(notificationStyles);

// Initialize the application
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new AcurenApp();
});

// Add SVG gradient for progress ring
document.addEventListener('DOMContentLoaded', () => {
    const svg = document.querySelector('.progress-ring');
    if (svg) {
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
        gradient.id = 'progressGradient';
        gradient.innerHTML = `
            <stop offset="0%" style="stop-color:#00D4FF;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#00FFB3;stop-opacity:1" />
        `;
        defs.appendChild(gradient);
        svg.appendChild(defs);
    }
});

