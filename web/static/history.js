// JavaScript for MixSync Download History Page

class DownloadHistory {
	constructor() {
		this.currentPage = 1;
		this.pageSize = 50;
		this.totalPages = 1;
		this.currentFilters = {
			search: '',
			status: '',
			source: '',
		};
		this.init();
	}

	init() {
		this.setupEventListeners();
		this.loadStatistics();
		this.loadHistory();
	}

	setupEventListeners() {
		// Search functionality
		const searchBtn = document.getElementById('searchBtn');
		const clearSearchBtn = document.getElementById('clearSearchBtn');
		const searchInput = document.getElementById('searchInput');

		searchBtn.addEventListener('click', () => this.performSearch());
		clearSearchBtn.addEventListener('click', () => this.clearSearch());
		searchInput.addEventListener('keypress', (e) => {
			if (e.key === 'Enter') {
				this.performSearch();
			}
		});

		// Filter controls
		const statusFilter = document.getElementById('statusFilter');
		const sourceFilter = document.getElementById('sourceFilter');
		const refreshBtn = document.getElementById('refreshBtn');

		statusFilter.addEventListener('change', () => this.applyFilters());
		sourceFilter.addEventListener('change', () => this.applyFilters());
		refreshBtn.addEventListener('click', () => this.refreshData());

		// Pagination
		const prevPageBtn = document.getElementById('prevPageBtn');
		const nextPageBtn = document.getElementById('nextPageBtn');

		prevPageBtn.addEventListener('click', () => this.previousPage());
		nextPageBtn.addEventListener('click', () => this.nextPage());
	}

	async loadStatistics() {
		try {
			const response = await fetch('/api/download-stats');
			const stats = await response.json();
			this.displayStatistics(stats);
		} catch (error) {
			console.error('Error loading statistics:', error);
			this.showToast('error', 'Error', 'Failed to load statistics');
		}
	}

	displayStatistics(stats) {
		const container = document.getElementById('statsGrid');

		container.innerHTML = `
			<div class="stat-card">
				<div class="stat-icon completed">
					<i class="fas fa-check-circle"></i>
				</div>
				<div class="stat-content">
					<div class="stat-number">${stats.completed_downloads || 0}</div>
					<div class="stat-label">Completed</div>
				</div>
			</div>
			<div class="stat-card">
				<div class="stat-icon total">
					<i class="fas fa-download"></i>
				</div>
				<div class="stat-content">
					<div class="stat-number">${stats.total_downloads || 0}</div>
					<div class="stat-label">Total Downloads</div>
				</div>
			</div>
			<div class="stat-card">
				<div class="stat-icon playlist">
					<i class="fas fa-music"></i>
				</div>
				<div class="stat-content">
					<div class="stat-number">${stats.playlist_downloads || 0}</div>
					<div class="stat-label">From Playlist</div>
				</div>
			</div>
			<div class="stat-card">
				<div class="stat-icon manual">
					<i class="fas fa-globe"></i>
				</div>
				<div class="stat-content">
					<div class="stat-number">${stats.manual_downloads || 0}</div>
					<div class="stat-label">Manual Downloads</div>
				</div>
			</div>
			<div class="stat-card">
				<div class="stat-icon size">
					<i class="fas fa-hdd"></i>
				</div>
				<div class="stat-content">
					<div class="stat-number">${this.formatFileSize(
						stats.total_file_size || 0
					)}</div>
					<div class="stat-label">Total Size</div>
				</div>
			</div>
			<div class="stat-card">
				<div class="stat-icon success-rate">
					<i class="fas fa-percentage"></i>
				</div>
				<div class="stat-content">
					<div class="stat-number">${(stats.success_rate || 0).toFixed(1)}%</div>
					<div class="stat-label">Success Rate</div>
				</div>
			</div>
		`;
	}

	async loadHistory() {
		const loading = document.getElementById('historyLoading');
		const tableContainer = document.getElementById('historyTableContainer');

		loading.style.display = 'flex';
		tableContainer.style.display = 'none';

		try {
			const params = new URLSearchParams({
				page: this.currentPage,
				limit: this.pageSize,
				...this.currentFilters,
			});

			// Remove empty filters
			Object.keys(this.currentFilters).forEach((key) => {
				if (!this.currentFilters[key]) {
					params.delete(key);
				}
			});

			const response = await fetch(`/api/download-history?${params}`);
			const data = await response.json();

			this.displayHistory(data.downloads || []);
			this.updatePagination(data.pagination || {});
			this.updateHistoryCount(data.pagination?.total || 0);
		} catch (error) {
			console.error('Error loading history:', error);
			this.showToast('error', 'Error', 'Failed to load download history');
		}

		loading.style.display = 'none';
		tableContainer.style.display = 'block';
	}

	displayHistory(downloads) {
		const tbody = document.getElementById('historyTableBody');

		if (downloads.length === 0) {
			tbody.innerHTML = `
				<tr>
					<td colspan="7" class="empty-state-row">
						<div class="empty-state">
							<i class="fas fa-search"></i>
							<p>No downloads found</p>
							<small>Try adjusting your search or filters</small>
						</div>
					</td>
				</tr>
			`;
			return;
		}

		tbody.innerHTML = downloads
			.map(
				(download) => `
			<tr class="history-row ${download.download_status}">
				<td class="filename-cell">
					<div class="filename-content">
						<i class="fas fa-file-audio file-icon"></i>
						<span class="filename" title="${download.filename}">${download.filename}</span>
					</div>
				</td>
				<td class="artist-cell">${download.artist || '-'}</td>
				<td class="track-cell">${download.track_name || '-'}</td>
				<td class="source-cell">
					<span class="source-badge ${download.source_type}">
						<i class="fas ${
							download.source_type === 'playlist' ? 'fa-music' : 'fa-globe'
						}"></i>
						${download.source_type === 'playlist' ? 'Playlist' : 'Manual'}
					</span>
				</td>
				<td class="status-cell">
					<span class="status-badge ${download.download_status}">
						<i class="fas ${this.getStatusIcon(download.download_status)}"></i>
						${this.formatStatus(download.download_status)}
					</span>
				</td>
				<td class="size-cell">${
					download.file_size ? this.formatFileSize(download.file_size) : '-'
				}</td>
				<td class="date-cell" title="${download.created_at}">
					${download.created_at_formatted || '-'}
				</td>
			</tr>
		`
			)
			.join('');
	}

	updatePagination(pagination) {
		const paginationContainer = document.getElementById('paginationContainer');
		const prevBtn = document.getElementById('prevPageBtn');
		const nextBtn = document.getElementById('nextPageBtn');
		const pageInfo = document.getElementById('pageInfo');

		this.totalPages = pagination.total_pages || 1;
		this.currentPage = pagination.current_page || 1;

		prevBtn.disabled = this.currentPage <= 1;
		nextBtn.disabled = this.currentPage >= this.totalPages;

		pageInfo.textContent = `Page ${this.currentPage} of ${this.totalPages}`;

		paginationContainer.style.display = this.totalPages > 1 ? 'flex' : 'none';
	}

	updateHistoryCount(total) {
		const countElement = document.getElementById('historyCount');
		countElement.textContent = `(${total} total)`;
	}

	performSearch() {
		const searchInput = document.getElementById('searchInput');
		this.currentFilters.search = searchInput.value.trim();
		this.currentPage = 1;
		this.loadHistory();
	}

	clearSearch() {
		const searchInput = document.getElementById('searchInput');
		searchInput.value = '';
		this.currentFilters.search = '';
		this.currentPage = 1;
		this.loadHistory();
	}

	applyFilters() {
		const statusFilter = document.getElementById('statusFilter');
		const sourceFilter = document.getElementById('sourceFilter');

		this.currentFilters.status = statusFilter.value;
		this.currentFilters.source = sourceFilter.value;
		this.currentPage = 1;
		this.loadHistory();
	}

	refreshData() {
		this.loadStatistics();
		this.loadHistory();
		this.showToast('success', 'Refreshed', 'Data has been refreshed');
	}

	previousPage() {
		if (this.currentPage > 1) {
			this.currentPage--;
			this.loadHistory();
		}
	}

	nextPage() {
		if (this.currentPage < this.totalPages) {
			this.currentPage++;
			this.loadHistory();
		}
	}

	getStatusIcon(status) {
		const icons = {
			completed: 'fa-check-circle',
			failed: 'fa-times-circle',
			processing: 'fa-clock',
		};
		return icons[status] || 'fa-question-circle';
	}

	formatStatus(status) {
		const statusMap = {
			completed: 'Completed',
			failed: 'Failed',
			processing: 'Processing',
		};
		return statusMap[status] || status;
	}

	formatFileSize(bytes) {
		if (!bytes) return '0 B';

		const units = ['B', 'KB', 'MB', 'GB'];
		let size = bytes;
		let unitIndex = 0;

		while (size >= 1024 && unitIndex < units.length - 1) {
			size /= 1024;
			unitIndex++;
		}

		return `${size.toFixed(1)} ${units[unitIndex]}`;
	}

	showToast(type, title, message) {
		const container = document.getElementById('toastContainer');
		const toastId = `toast-${Date.now()}`;

		const icons = {
			success: 'fas fa-check-circle',
			error: 'fas fa-exclamation-circle',
			warning: 'fas fa-exclamation-triangle',
			info: 'fas fa-info-circle',
		};

		const toast = document.createElement('div');
		toast.className = `toast ${type}`;
		toast.id = toastId;
		toast.innerHTML = `
			<div class="toast-icon">
				<i class="${icons[type] || icons.info}"></i>
			</div>
			<div class="toast-content">
				<div class="toast-title">${title}</div>
				<div class="toast-message">${message}</div>
			</div>
			<button class="toast-close" onclick="this.closest('.toast').remove()">
				<i class="fas fa-times"></i>
			</button>
		`;

		container.appendChild(toast);

		// Auto-remove after 5 seconds
		setTimeout(() => {
			const toastElement = document.getElementById(toastId);
			if (toastElement) {
				toastElement.remove();
			}
		}, 5000);
	}
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
	new DownloadHistory();
});
