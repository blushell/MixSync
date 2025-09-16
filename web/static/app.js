// Modern JavaScript for MixSync Web UI

class AudioFetcher {
	constructor() {
		this.ws = null;
		this.currentDownloadId = null;
		this.init();
	}

	init() {
		this.setupWebSocket();
		this.setupEventListeners();
		this.loadSupportedPlatforms();
		this.loadDownloads();
	}

	setupWebSocket() {
		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		const wsUrl = `${protocol}//${window.location.host}/ws`;

		this.ws = new WebSocket(wsUrl);

		this.ws.onopen = () => {
			console.log('WebSocket connected');
		};

		this.ws.onmessage = (event) => {
			const data = JSON.parse(event.data);
			this.handleWebSocketMessage(data);
		};

		this.ws.onclose = () => {
			console.log('WebSocket disconnected, attempting to reconnect...');
			setTimeout(() => this.setupWebSocket(), 3000);
		};

		this.ws.onerror = (error) => {
			console.error('WebSocket error:', error);
		};
	}

	setupEventListeners() {
		// Download form
		const downloadForm = document.getElementById('downloadForm');
		downloadForm.addEventListener('submit', (e) =>
			this.handleDownloadSubmit(e)
		);

		// Refresh downloads button
		const refreshBtn = document.getElementById('refreshBtn');
		refreshBtn.addEventListener('click', () => this.loadDownloads());

		// URL input auto-validation
		const urlInput = document.getElementById('url');
		urlInput.addEventListener('input', (e) => this.validateUrl(e.target.value));
	}

	validateUrl(url) {
		const urlInput = document.getElementById('url');

		if (!url) {
			urlInput.style.borderColor = '';
			return;
		}

		try {
			new URL(url);
			urlInput.style.borderColor = 'var(--success-color)';
		} catch {
			urlInput.style.borderColor = 'var(--error-color)';
		}
	}

	async handleDownloadSubmit(event) {
		event.preventDefault();

		const formData = new FormData(event.target);
		const url = formData.get('url').trim();
		const filename = formData.get('filename').trim();

		if (!url) {
			this.showToast('error', 'Error', 'Please enter a valid URL');
			return;
		}

		try {
			this.setDownloadButtonState(true);

			const response = await fetch('/download', {
				method: 'POST',
				body: formData,
			});

			const result = await response.json();

			if (response.ok) {
				this.currentDownloadId = result.download_id;
				this.showProgressSection();
				this.updateProgress({
					filename: filename || 'Extracting title...',
					status: 'starting',
					progress: 0,
				});
				this.showToast(
					'success',
					'Download Started',
					'Your download has been queued'
				);
			} else {
				throw new Error(result.error || 'Download failed');
			}
		} catch (error) {
			console.error('Download error:', error);
			this.showToast('error', 'Download Failed', error.message);
			this.setDownloadButtonState(false);
		}
	}

	handleWebSocketMessage(data) {
		if (data.download_id !== this.currentDownloadId) {
			return; // Not our current download
		}

		switch (data.type) {
			case 'start':
				this.updateProgress({
					filename: data.filename || 'Starting download...',
					status: 'starting',
					progress: 0,
				});
				break;

			case 'progress':
				this.updateProgress(data.data);
				break;

			case 'complete':
				this.handleDownloadComplete(data.data);
				break;

			case 'error':
				this.handleDownloadError(data.error);
				break;
		}
	}

	showProgressSection() {
		const progressSection = document.getElementById('progressSection');
		progressSection.style.display = 'block';
		progressSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
	}

	hideProgressSection() {
		const progressSection = document.getElementById('progressSection');
		progressSection.style.display = 'none';
	}

	updateProgress(data) {
		const elements = {
			filename: document.getElementById('progressFilename'),
			status: document.getElementById('progressStatus'),
			bar: document.getElementById('progressBar'),
			percentage: document.getElementById('progressPercentage'),
			speed: document.getElementById('progressSpeed'),
			eta: document.getElementById('progressEta'),
		};

		// Update filename
		if (data.filename) {
			elements.filename.textContent = data.filename;
		}

		// Update status
		const status = data.status || 'processing';
		elements.status.textContent = this.formatStatus(status);
		elements.status.className = `progress-status ${status}`;

		// Update progress bar
		const progress = Math.max(0, Math.min(100, data.progress || 0));
		elements.bar.style.width = `${progress}%`;
		elements.percentage.textContent = `${Math.round(progress)}%`;

		// Update speed and ETA
		if (data.speed) {
			elements.speed.textContent = this.formatSpeed(data.speed);
		} else {
			elements.speed.textContent = '';
		}

		if (data.eta) {
			elements.eta.textContent = `ETA: ${this.formatTime(data.eta)}`;
		} else {
			elements.eta.textContent = '';
		}
	}

	handleDownloadComplete(data) {
		if (data.status === 'completed') {
			this.updateProgress({
				filename: data.filename || 'Download completed',
				status: 'completed',
				progress: 100,
			});

			this.showToast(
				'success',
				'Download Complete',
				`Successfully downloaded: ${data.filename || 'audio file'}`
			);

			// Refresh downloads list
			setTimeout(() => this.loadDownloads(), 1000);
		} else {
			this.handleDownloadError(data.error || 'Download failed');
		}

		this.setDownloadButtonState(false);
		this.currentDownloadId = null;

		// Hide progress after a delay
		setTimeout(() => this.hideProgressSection(), 5000);
	}

	handleDownloadError(error) {
		this.updateProgress({
			filename: 'Download failed',
			status: 'error',
			progress: 0,
		});

		this.showToast('error', 'Download Failed', error);
		this.setDownloadButtonState(false);
		this.currentDownloadId = null;

		// Hide progress after a delay
		setTimeout(() => this.hideProgressSection(), 3000);
	}

	setDownloadButtonState(downloading) {
		const btn = document.getElementById('downloadBtn');
		const icon = btn.querySelector('i');

		if (downloading) {
			btn.disabled = true;
			btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Downloading...';
		} else {
			btn.disabled = false;
			btn.innerHTML = '<i class="fas fa-download"></i> Download Audio';
		}
	}

	async loadSupportedPlatforms() {
		try {
			const response = await fetch('/api/supported-sites');
			const data = await response.json();

			this.displaySupportedPlatforms(data.popular_sites || []);
		} catch (error) {
			console.error('Error loading supported platforms:', error);
			this.displaySupportedPlatforms([]);
		}
	}

	displaySupportedPlatforms(platforms) {
		const container = document.getElementById('platformsGrid');

		if (platforms.length === 0) {
			container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Unable to load supported platforms</p>
                </div>
            `;
			return;
		}

		const platformIcons = {
			youtube: 'fab fa-youtube',
			soundcloud: 'fab fa-soundcloud',
			bandcamp: 'fas fa-music',
			vimeo: 'fab fa-vimeo',
			dailymotion: 'fas fa-video',
			mixcloud: 'fas fa-cloud',
			audiomack: 'fas fa-headphones',
		};

		container.innerHTML = platforms
			.map(
				(platform) => `
            <div class="platform-item">
                <i class="${platformIcons[platform] || 'fas fa-globe'}"></i>
                ${platform}
            </div>
        `
			)
			.join('');
	}

	async loadDownloads() {
		const container = document.getElementById('downloadsList');
		const loading = document.getElementById('downloadsLoading');

		if (loading) loading.style.display = 'flex';

		try {
			const response = await fetch('/api/downloads');
			const data = await response.json();

			this.displayDownloads(data.files || [], data);
		} catch (error) {
			console.error('Error loading downloads:', error);
			this.displayDownloads([]);
		}

		if (loading) loading.style.display = 'none';
	}

	displayDownloads(files, metadata = null) {
		const container = document.getElementById('downloadsList');

		if (files.length === 0) {
			container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-folder-open"></i>
                    <p>No downloads yet</p>
                    <small>Downloaded files will appear here</small>
                </div>
            `;
			return;
		}

		// Create info header if we have metadata
		let infoHeader = '';
		if (metadata && metadata.total_files !== undefined) {
			const { showing, total_files, limit } = metadata;
			if (total_files > showing) {
				infoHeader = `
                    <div class="downloads-info">
                        <small class="downloads-count">
                            Showing ${showing} of ${total_files} downloads (limit: ${limit})
                        </small>
                    </div>
                `;
			}
		}

		const filesList = files
			.map(
				(file) => `
            <div class="download-item">
                <div class="download-icon">
                    <i class="fas fa-music"></i>
                </div>
                <div class="download-info">
                    <div class="download-name" title="${file.name}">
                        ${file.name}
                    </div>
                    <div class="download-meta">
                        <span>${this.formatFileSize(file.size)}</span>
                        <span>${this.formatDate(file.created)}</span>
                    </div>
                </div>
            </div>
        `
			)
			.join('');

		container.innerHTML = infoHeader + filesList;
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

	// Utility functions
	formatStatus(status) {
		const statusMap = {
			starting: 'Starting',
			downloading: 'Downloading',
			processing: 'Processing',
			completed: 'Completed',
			error: 'Error',
		};
		return statusMap[status] || status;
	}

	formatSpeed(bytesPerSec) {
		if (!bytesPerSec) return '';

		const units = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
		let size = bytesPerSec;
		let unitIndex = 0;

		while (size >= 1024 && unitIndex < units.length - 1) {
			size /= 1024;
			unitIndex++;
		}

		return `${size.toFixed(1)} ${units[unitIndex]}`;
	}

	formatTime(seconds) {
		if (!seconds) return '';

		const hours = Math.floor(seconds / 3600);
		const minutes = Math.floor((seconds % 3600) / 60);
		const secs = Math.floor(seconds % 60);

		if (hours > 0) {
			return `${hours}:${minutes.toString().padStart(2, '0')}:${secs
				.toString()
				.padStart(2, '0')}`;
		} else {
			return `${minutes}:${secs.toString().padStart(2, '0')}`;
		}
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

	formatDate(timestamp) {
		const date = new Date(timestamp * 1000);
		const now = new Date();
		const diffMs = now - date;
		const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

		if (diffDays === 0) {
			return 'Today';
		} else if (diffDays === 1) {
			return 'Yesterday';
		} else if (diffDays < 7) {
			return `${diffDays} days ago`;
		} else {
			return date.toLocaleDateString();
		}
	}
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
	new AudioFetcher();
});
