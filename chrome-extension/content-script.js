/**
 * Content Script for Media Procurement Data Collection
 * Handles data extraction from procurement websites
 */

class MediaProcurementCollector {
  constructor() {
    this.mediaKeywords = [
      'video', 'photo', 'film', 'multimedia', 'podcast', 'animation',
      'audiovisual', 'media', 'communication', 'production', 'graphic',
      'design', 'branding', 'creative', 'advertising', 'marketing',
      'documentary', 'broadcasting', 'digital', 'content', 'visualization',
      'photography', 'filming', 'editing', 'post-production', 'cinematography'
    ];
    
    this.humanBehavior = new HumanBehaviorSimulator();
    this.scraperUtils = new ScraperUtils();
    
    this.init();
  }

  init() {
    // Listen for collection requests from background script
    window.addEventListener('message', (event) => {
      if (event.data.type === 'COLLECT_DATA') {
        this.collectData(event.data.config);
      }
    });
    
    console.log('📊 Media Procurement Collector ready');
  }

  async collectData(config) {
    console.log(`🎯 Starting collection for ${config.name}`);
    
    try {
      // Wait for page to fully load
      await this.waitForPageLoad();
      
      // Handle login if required
      if (config.requiresLogin) {
        await this.handleLogin(config);
      }
      
      // Extract opportunities
      const opportunities = await this.extractOpportunities(config);
      
      // Filter for media relevance
      const mediaOpportunities = this.filterMediaOpportunities(opportunities);
      
      // Download documents for relevant opportunities
      const documentsData = await this.downloadDocuments(mediaOpportunities, config);
      
      // Send results back
      window.postMessage({
        type: 'COLLECTION_COMPLETE',
        results: {
          website: config.name,
          totalOpportunities: opportunities.length,
          mediaOpportunities: mediaOpportunities.length,
          opportunities: mediaOpportunities,
          documents: documentsData,
          timestamp: new Date().toISOString()
        }
      }, '*');
      
    } catch (error) {
      console.error('Collection error:', error);
      window.postMessage({
        type: 'COLLECTION_COMPLETE',
        results: { error: error.message }
      }, '*');
    }
  }

  async extractOpportunities(config) {
    const opportunities = [];
    
    try {
      // Wait for content to load
      await this.scraperUtils.waitForSelector(config.selectors.listContainer, 10000);
      
      // Get all opportunity items
      const items = document.querySelectorAll(config.selectors.listItems.container);
      console.log(`📋 Found ${items.length} opportunities`);
      
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        
        try {
          const opportunity = await this.extractOpportunityData(item, config);
          if (opportunity) {
            opportunities.push(opportunity);
          }
          
          // Human-like delay between extractions
          await this.humanBehavior.randomDelay(500, 1500);
          
        } catch (error) {
          console.error(`Error extracting opportunity ${i}:`, error);
        }
      }
      
    } catch (error) {
      console.error('Error extracting opportunities:', error);
    }
    
    return opportunities;
  }

  async extractOpportunityData(item, config) {
    const selectors = config.selectors.listItems;
    
    const opportunity = {
      title: this.scraperUtils.extractText(item, selectors.title),
      organization: this.scraperUtils.extractText(item, selectors.organization),
      deadline: this.scraperUtils.extractText(item, selectors.deadline),
      published: this.scraperUtils.extractText(item, selectors.published),
      reference: this.scraperUtils.extractText(item, selectors.reference),
      sourceUrl: window.location.href,
      extractedAt: new Date().toISOString()
    };
    
    // Get detail page link if available
    const detailLink = item.querySelector(selectors.clickTarget);
    if (detailLink) {
      opportunity.detailUrl = this.scraperUtils.getAbsoluteUrl(detailLink.href);
      
      // Extract additional details if configured for conditional clicking
      if (config.automation.clickEachItem === 'conditional') {
        const hasMediaKeywords = this.containsMediaKeywords(opportunity.title + ' ' + opportunity.organization);
        
        if (hasMediaKeywords) {
          const detailData = await this.extractDetailPage(opportunity.detailUrl, config);
          Object.assign(opportunity, detailData);
        }
      }
    }
    
    return opportunity;
  }

  async extractDetailPage(url, config) {
    try {
      // Simulate human-like clicking behavior
      await this.humanBehavior.simulateClick();
      
      // Open detail page in new tab (handled by background script)
      // For now, we'll skip detail extraction to keep it simple
      // In production, this would involve more complex tab management
      
      return {
        fullDescription: '',
        requirements: '',
        contactInfo: '',
        budget: ''
      };
      
    } catch (error) {
      console.error('Error extracting detail page:', error);
      return {};
    }
  }

  filterMediaOpportunities(opportunities) {
    return opportunities.filter(opp => {
      const searchText = (opp.title + ' ' + opp.organization + ' ' + opp.fullDescription).toLowerCase();
      return this.containsMediaKeywords(searchText);
    });
  }

  containsMediaKeywords(text) {
    const lowerText = text.toLowerCase();
    return this.mediaKeywords.some(keyword => lowerText.includes(keyword));
  }

  async downloadDocuments(opportunities, config) {
    const documents = [];
    
    for (const opp of opportunities) {
      if (opp.detailUrl) {
        try {
          // In a simplified version, we'll just collect document URLs
          // Actual downloading would be handled by the background script
          const docUrls = await this.findDocumentUrls(opp.detailUrl, config);
          
          for (const url of docUrls) {
            documents.push({
              opportunityId: opp.reference || opp.title,
              url: url,
              filename: this.extractFilename(url),
              type: this.getFileType(url)
            });
          }
          
        } catch (error) {
          console.error('Error finding documents:', error);
        }
      }
    }
    
    return documents;
  }

  async findDocumentUrls(pageUrl, config) {
    // In production, this would navigate to the page and extract document links
    // For now, return empty array
    return [];
  }

  extractFilename(url) {
    return url.split('/').pop().split('?')[0];
  }

  getFileType(url) {
    const extension = url.split('.').pop().toLowerCase();
    return extension;
  }

  async handleLogin(config) {
    // Check if already logged in
    if (this.isLoggedIn()) {
      console.log('✅ Already logged in');
      return;
    }
    
    console.log('🔐 Attempting login...');
    
    try {
      // Get stored credentials
      const credentials = await this.getStoredCredentials(config.name);
      
      if (!credentials) {
        throw new Error('No credentials found for ' + config.name);
      }
      
      // Perform login
      await this.performLogin(credentials);
      
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }

  isLoggedIn() {
    // Check for common login indicators
    const loginIndicators = [
      '.user-menu', '.logout', '.profile', '.dashboard',
      '[href*="logout"]', '[href*="profile"]'
    ];
    
    return loginIndicators.some(selector => document.querySelector(selector));
  }

  async getStoredCredentials(siteName) {
    try {
      const result = await chrome.storage.local.get(['credentials']);
      return result.credentials?.[siteName];
    } catch (error) {
      console.error('Error getting credentials:', error);
      return null;
    }
  }

  async performLogin(credentials) {
    // Find login form
    const usernameField = document.querySelector('input[type="email"], input[name*="email"], input[name*="username"]');
    const passwordField = document.querySelector('input[type="password"]');
    const submitButton = document.querySelector('button[type="submit"], input[type="submit"], .login-button');
    
    if (!usernameField || !passwordField || !submitButton) {
      throw new Error('Login form not found');
    }
    
    // Fill credentials with human-like behavior
    await this.humanBehavior.typeText(usernameField, credentials.username);
    await this.humanBehavior.randomDelay(500, 1000);
    
    await this.humanBehavior.typeText(passwordField, credentials.password);
    await this.humanBehavior.randomDelay(500, 1000);
    
    // Submit form
    await this.humanBehavior.simulateClick(submitButton);
    
    // Wait for login to complete
    await this.waitForPageLoad();
  }

  async waitForPageLoad() {
    return new Promise((resolve) => {
      if (document.readyState === 'complete') {
        resolve();
      } else {
        window.addEventListener('load', resolve, { once: true });
      }
    });
  }
}

// Initialize collector when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new MediaProcurementCollector();
  });
} else {
  new MediaProcurementCollector();
}

