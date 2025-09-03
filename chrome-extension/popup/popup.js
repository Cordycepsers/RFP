/**
 * Popup Interface for Media Procurement Collector
 * Handles user interactions and communication with background script
 */

class PopupInterface {
  constructor() {
    this.isCollecting = false;
    this.currentResults = null;
    
    this.init();
  }

  async init() {
    console.log('🎛️ Popup interface initialized');
    
    // Load saved configuration
    await this.loadConfiguration();
    
    // Setup event listeners
    this.setupEventListeners();
    
    // Update status
    await this.updateStatus();
    
    // Load recent results
    await this.loadRecentResults();
  }

  setupEventListeners() {
    // Configuration
    document.getElementById('saveConfig').addEventListener('click', () => {
      this.saveConfiguration();
    });

    // Collection controls
    document.getElementById('startCollection').addEventListener('click', () => {
      this.startCollection();
    });

    document.getElementById('stopCollection').addEventListener('click', () => {
      this.stopCollection();
    });

    // Results actions
    document.getElementById('viewResults').addEventListener('click', () => {
      this.viewResults();
    });

    document.getElementById('downloadReport').addEventListener('click', () => {
      this.downloadReport();
    });

    // Settings
    document.getElementById('autoSchedule').addEventListener('change', (e) => {
      this.updateSetting('autoSchedule', e.target.checked);
    });

    document.getElementById('notifications').addEventListener('change', (e) => {
      this.updateSetting('notifications', e.target.checked);
    });

    document.getElementById('scheduleTime').addEventListener('change', (e) => {
      this.updateSetting('scheduleTime', e.target.value);
    });

    // Toast close
    document.getElementById('toastClose').addEventListener('click', () => {
      this.hideToast();
    });

    // Listen for background script messages
    chrome.runtime.onMessage.addListener((message) => {
      this.handleBackgroundMessage(message);
    });
  }

  async loadConfiguration() {
    try {
      const result = await chrome.storage.sync.get([
        'serverUrl', 'apiKey', 'clientEmail', 'autoSchedule', 
        'notifications', 'scheduleTime'
      ]);

      // Populate form fields
      if (result.serverUrl) {
        document.getElementById('serverUrl').value = result.serverUrl;
      }
      if (result.apiKey) {
        document.getElementById('apiKey').value = result.apiKey;
      }
      if (result.clientEmail) {
        document.getElementById('clientEmail').value = result.clientEmail;
      }

      // Settings
      document.getElementById('autoSchedule').checked = result.autoSchedule || false;
      document.getElementById('notifications').checked = result.notifications !== false;
      document.getElementById('scheduleTime').value = result.scheduleTime || '09:00';

    } catch (error) {
      console.error('Error loading configuration:', error);
    }
  }

  async saveConfiguration() {
    try {
      const config = {
        serverUrl: document.getElementById('serverUrl').value.trim(),
        apiKey: document.getElementById('apiKey').value.trim(),
        clientEmail: document.getElementById('clientEmail').value.trim()
      };

      // Validate configuration
      if (!config.serverUrl || !config.apiKey || !config.clientEmail) {
        this.showToast('Please fill in all configuration fields', 'error');
        return;
      }

      // Validate URL
      try {
        new URL(config.serverUrl);
      } catch {
        this.showToast('Please enter a valid server URL', 'error');
        return;
      }

      // Validate email
      if (!this.isValidEmail(config.clientEmail)) {
        this.showToast('Please enter a valid email address', 'error');
        return;
      }

      await chrome.storage.sync.set(config);
      this.showToast('Configuration saved successfully', 'success');

    } catch (error) {
      console.error('Error saving configuration:', error);
      this.showToast('Error saving configuration', 'error');
    }
  }

  async startCollection() {
    try {
      // Check if configuration is complete
      const config = await chrome.storage.sync.get(['serverUrl', 'apiKey', 'clientEmail']);
      if (!config.serverUrl || !config.apiKey || !config.clientEmail) {
        this.showToast('Please configure the extension first', 'error');
        return;
      }

      // Send start message to background script
      const response = await chrome.runtime.sendMessage({
        type: 'START_COLLECTION'
      });

      if (response.success) {
        this.isCollecting = true;
        this.updateCollectionUI();
        this.showToast('Collection started', 'success');
      } else {
        this.showToast('Failed to start collection', 'error');
      }

    } catch (error) {
      console.error('Error starting collection:', error);
      this.showToast('Error starting collection', 'error');
    }
  }

  async stopCollection() {
    try {
      const response = await chrome.runtime.sendMessage({
        type: 'STOP_COLLECTION'
      });

      if (response.success) {
        this.isCollecting = false;
        this.updateCollectionUI();
        this.showToast('Collection stopped', 'success');
      }

    } catch (error) {
      console.error('Error stopping collection:', error);
      this.showToast('Error stopping collection', 'error');
    }
  }

  async updateStatus() {
    try {
      const response = await chrome.runtime.sendMessage({
        type: 'GET_STATUS'
      });

      this.isCollecting = response.isCollecting;
      this.updateCollectionUI();

      if (response.currentTask) {
        this.updateProgress(response.currentTask, 50); // Approximate progress
      }

    } catch (error) {
      console.error('Error updating status:', error);
    }
  }

  updateCollectionUI() {
    const startBtn = document.getElementById('startCollection');
    const stopBtn = document.getElementById('stopCollection');
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    const progressSection = document.getElementById('progressSection');

    if (this.isCollecting) {
      startBtn.disabled = true;
      stopBtn.disabled = false;
      statusIndicator.className = 'status-indicator collecting';
      statusText.textContent = 'Collecting';
      progressSection.style.display = 'block';
    } else {
      startBtn.disabled = false;
      stopBtn.disabled = true;
      statusIndicator.className = 'status-indicator';
      statusText.textContent = 'Ready';
      progressSection.style.display = 'none';
    }
  }

  updateProgress(websiteName, percentage) {
    document.getElementById('currentWebsite').textContent = websiteName;
    document.getElementById('progressPercent').textContent = `${percentage}%`;
    document.getElementById('progressFill').style.width = `${percentage}%`;
  }

  async loadRecentResults() {
    try {
      const result = await chrome.storage.local.get(['lastResults']);
      if (result.lastResults) {
        this.currentResults = result.lastResults;
        this.updateResultsDisplay();
      }
    } catch (error) {
      console.error('Error loading recent results:', error);
    }
  }

  updateResultsDisplay() {
    if (!this.currentResults) return;

    document.getElementById('totalOpportunities').textContent = 
      this.currentResults.totalOpportunities || 0;
    document.getElementById('mediaOpportunities').textContent = 
      this.currentResults.mediaOpportunities || 0;
    document.getElementById('documentsCount').textContent = 
      this.currentResults.documentsCount || 0;

    // Update last run time
    if (this.currentResults.timestamp) {
      const lastRun = new Date(this.currentResults.timestamp);
      document.getElementById('lastRun').textContent = 
        lastRun.toLocaleDateString() + ' ' + lastRun.toLocaleTimeString();
    }
  }

  async viewResults() {
    if (this.currentResults && this.currentResults.driveUrl) {
      chrome.tabs.create({ url: this.currentResults.driveUrl });
    } else {
      this.showToast('No results available to view', 'error');
    }
  }

  async downloadReport() {
    if (this.currentResults && this.currentResults.reportUrl) {
      chrome.downloads.download({
        url: this.currentResults.reportUrl,
        filename: `media-procurement-report-${new Date().toISOString().split('T')[0]}.xlsx`
      });
    } else {
      this.showToast('No report available to download', 'error');
    }
  }

  async updateSetting(key, value) {
    try {
      await chrome.storage.sync.set({ [key]: value });
      
      // Handle auto-schedule setting
      if (key === 'autoSchedule' && value) {
        const scheduleTime = document.getElementById('scheduleTime').value;
        // Send message to background script to setup scheduling
        chrome.runtime.sendMessage({
          type: 'SETUP_SCHEDULE',
          time: scheduleTime
        });
      }

    } catch (error) {
      console.error('Error updating setting:', error);
    }
  }

  handleBackgroundMessage(message) {
    switch (message.type) {
      case 'COLLECTION_PROGRESS':
        this.updateProgress(message.data.website, message.data.percentage);
        break;

      case 'COLLECTION_COMPLETE':
        this.isCollecting = false;
        this.updateCollectionUI();
        this.currentResults = message.data;
        this.updateResultsDisplay();
        this.showToast('Collection completed successfully', 'success');
        
        // Save results
        chrome.storage.local.set({ lastResults: message.data });
        break;

      case 'UPLOAD_SUCCESS':
        this.showToast('Data uploaded to Google Drive', 'success');
        if (message.data.driveUrl) {
          this.currentResults = { ...this.currentResults, driveUrl: message.data.driveUrl };
        }
        break;

      case 'UPLOAD_ERROR':
        this.showToast('Failed to upload data: ' + message.data.error, 'error');
        break;

      case 'COLLECTION_ERROR':
        this.isCollecting = false;
        this.updateCollectionUI();
        this.showToast('Collection error: ' + message.data.error, 'error');
        break;
    }
  }

  showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');

    toastMessage.textContent = message;
    toast.className = `toast show ${type}`;

    // Auto-hide after 5 seconds
    setTimeout(() => {
      this.hideToast();
    }, 5000);
  }

  hideToast() {
    const toast = document.getElementById('toast');
    toast.className = 'toast';
  }

  isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }
}

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new PopupInterface();
});

