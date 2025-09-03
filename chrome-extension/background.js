/**
 * Background Service Worker for Media Procurement Collector
 * Handles server communication and task orchestration
 */

class MediaProcurementBackground {
  constructor() {
    this.serverUrl = 'https://your-cloud-run-url.run.app';
    this.apiKey = null;
    this.isCollecting = false;
    this.currentTask = null;
    
    this.init();
  }

  async init() {
    console.log('🚀 Media Procurement Collector initialized');
    
    // Load configuration
    await this.loadConfig();
    
    // Setup message listeners
    this.setupMessageListeners();
    
    // Setup alarm for scheduled collection
    this.setupScheduledCollection();
  }

  async loadConfig() {
    try {
      const result = await chrome.storage.sync.get(['serverUrl', 'apiKey', 'clientEmail']);
      this.serverUrl = result.serverUrl || this.serverUrl;
      this.apiKey = result.apiKey;
      this.clientEmail = result.clientEmail;
      
      console.log('📋 Configuration loaded');
    } catch (error) {
      console.error('Failed to load configuration:', error);
    }
  }

  setupMessageListeners() {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      this.handleMessage(message, sender, sendResponse);
      return true; // Keep message channel open for async response
    });
  }

  async handleMessage(message, sender, sendResponse) {
    try {
      switch (message.type) {
        case 'START_COLLECTION':
          await this.startCollection(message.websites);
          sendResponse({ success: true });
          break;
          
        case 'STOP_COLLECTION':
          await this.stopCollection();
          sendResponse({ success: true });
          break;
          
        case 'UPLOAD_DATA':
          await this.uploadToServer(message.data);
          sendResponse({ success: true });
          break;
          
        case 'GET_STATUS':
          sendResponse({ 
            isCollecting: this.isCollecting,
            currentTask: this.currentTask
          });
          break;
          
        default:
          sendResponse({ error: 'Unknown message type' });
      }
    } catch (error) {
      console.error('Message handling error:', error);
      sendResponse({ error: error.message });
    }
  }

  async startCollection(websites = null) {
    if (this.isCollecting) {
      throw new Error('Collection already in progress');
    }

    this.isCollecting = true;
    console.log('🎯 Starting media procurement collection');

    try {
      // Load website configurations
      const websiteConfigs = websites || await this.loadWebsiteConfigs();
      
      // Process each website
      for (const config of websiteConfigs) {
        if (!this.isCollecting) break; // Check if stopped
        
        this.currentTask = config.name;
        await this.collectFromWebsite(config);
        
        // Delay between websites
        await this.delay(5000);
      }
      
      console.log('✅ Collection completed');
    } catch (error) {
      console.error('Collection error:', error);
      throw error;
    } finally {
      this.isCollecting = false;
      this.currentTask = null;
    }
  }

  async collectFromWebsite(config) {
    console.log(`🌐 Collecting from ${config.name}`);
    
    try {
      // Open tab for the website
      const tab = await chrome.tabs.create({ 
        url: config.url, 
        active: false 
      });
      
      // Wait for page load
      await this.waitForTabLoad(tab.id);
      
      // Inject and execute collection script
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: this.executeCollection,
        args: [config]
      });
      
      // Process results
      if (results[0]?.result) {
        await this.uploadToServer({
          website: config.name,
          data: results[0].result,
          timestamp: new Date().toISOString()
        });
      }
      
      // Close tab
      await chrome.tabs.remove(tab.id);
      
    } catch (error) {
      console.error(`Error collecting from ${config.name}:`, error);
    }
  }

  // This function will be injected into the page
  executeCollection(config) {
    return new Promise((resolve) => {
      // This will be handled by content script
      window.postMessage({
        type: 'COLLECT_DATA',
        config: config
      }, '*');
      
      // Listen for response
      const listener = (event) => {
        if (event.data.type === 'COLLECTION_COMPLETE') {
          window.removeEventListener('message', listener);
          resolve(event.data.results);
        }
      };
      
      window.addEventListener('message', listener);
      
      // Timeout after 60 seconds
      setTimeout(() => {
        window.removeEventListener('message', listener);
        resolve({ error: 'Collection timeout' });
      }, 60000);
    });
  }

  async uploadToServer(data) {
    if (!this.serverUrl || !this.apiKey) {
      console.warn('Server configuration missing');
      return;
    }

    try {
      const response = await fetch(`${this.serverUrl}/api/upload-data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
          'X-Client-Email': this.clientEmail
        },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const result = await response.json();
      console.log('📤 Data uploaded successfully:', result);
      
      // Notify popup of success
      this.notifyPopup('UPLOAD_SUCCESS', result);
      
    } catch (error) {
      console.error('Upload error:', error);
      this.notifyPopup('UPLOAD_ERROR', { error: error.message });
    }
  }

  async loadWebsiteConfigs() {
    try {
      const response = await fetch(chrome.runtime.getURL('config/websites.json'));
      const config = await response.json();
      return config.websites.filter(site => site.priority === 'high');
    } catch (error) {
      console.error('Failed to load website configs:', error);
      return [];
    }
  }

  setupScheduledCollection() {
    // Create daily collection alarm
    chrome.alarms.create('dailyCollection', {
      when: Date.now() + (24 * 60 * 60 * 1000), // 24 hours from now
      periodInMinutes: 24 * 60 // Every 24 hours
    });

    chrome.alarms.onAlarm.addListener((alarm) => {
      if (alarm.name === 'dailyCollection') {
        this.startCollection();
      }
    });
  }

  async waitForTabLoad(tabId) {
    return new Promise((resolve) => {
      const listener = (changedTabId, changeInfo) => {
        if (changedTabId === tabId && changeInfo.status === 'complete') {
          chrome.tabs.onUpdated.removeListener(listener);
          setTimeout(resolve, 2000); // Additional wait for dynamic content
        }
      };
      chrome.tabs.onUpdated.addListener(listener);
    });
  }

  notifyPopup(type, data) {
    chrome.runtime.sendMessage({ type, data }).catch(() => {
      // Popup might not be open, ignore error
    });
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async stopCollection() {
    this.isCollecting = false;
    this.currentTask = null;
    console.log('🛑 Collection stopped');
  }
}

// Initialize background service
new MediaProcurementBackground();

