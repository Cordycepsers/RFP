/**
 * Scraper Utilities
 * Helper functions for data extraction and DOM manipulation
 */

class ScraperUtils {
  constructor() {
    this.baseUrl = window.location.origin;
  }

  /**
   * Extract text from element using multiple selectors
   */
  extractText(container, selectors) {
    if (!container || !selectors) return '';
    
    const selectorList = selectors.split(',').map(s => s.trim());
    
    for (const selector of selectorList) {
      const element = container.querySelector(selector);
      if (element) {
        return this.cleanText(element.textContent || element.innerText || '');
      }
    }
    
    return '';
  }

  /**
   * Extract attribute from element
   */
  extractAttribute(container, selectors, attribute = 'href') {
    if (!container || !selectors) return '';
    
    const selectorList = selectors.split(',').map(s => s.trim());
    
    for (const selector of selectorList) {
      const element = container.querySelector(selector);
      if (element && element.hasAttribute(attribute)) {
        return element.getAttribute(attribute);
      }
    }
    
    return '';
  }

  /**
   * Clean and normalize text
   */
  cleanText(text) {
    return text
      .replace(/\s+/g, ' ')
      .replace(/\n+/g, ' ')
      .trim();
  }

  /**
   * Convert relative URL to absolute
   */
  getAbsoluteUrl(url) {
    if (!url) return '';
    
    try {
      return new URL(url, this.baseUrl).href;
    } catch (error) {
      return url;
    }
  }

  /**
   * Wait for element to appear
   */
  async waitForSelector(selector, timeout = 10000) {
    return new Promise((resolve, reject) => {
      const element = document.querySelector(selector);
      if (element) {
        resolve(element);
        return;
      }

      const observer = new MutationObserver((mutations, obs) => {
        const element = document.querySelector(selector);
        if (element) {
          obs.disconnect();
          resolve(element);
        }
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true
      });

      setTimeout(() => {
        observer.disconnect();
        reject(new Error(`Element ${selector} not found within ${timeout}ms`));
      }, timeout);
    });
  }

  /**
   * Wait for page to be fully loaded
   */
  async waitForPageLoad() {
    return new Promise((resolve) => {
      if (document.readyState === 'complete') {
        resolve();
      } else {
        window.addEventListener('load', resolve, { once: true });
      }
    });
  }

  /**
   * Check if element is visible
   */
  isElementVisible(element) {
    if (!element) return false;
    
    const rect = element.getBoundingClientRect();
    const style = window.getComputedStyle(element);
    
    return (
      rect.width > 0 &&
      rect.height > 0 &&
      style.visibility !== 'hidden' &&
      style.display !== 'none' &&
      style.opacity !== '0'
    );
  }

  /**
   * Scroll element into view
   */
  scrollIntoView(element) {
    if (element) {
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
        inline: 'nearest'
      });
    }
  }

  /**
   * Extract all links from container
   */
  extractLinks(container, linkSelector = 'a[href]') {
    if (!container) return [];
    
    const links = container.querySelectorAll(linkSelector);
    return Array.from(links).map(link => ({
      text: this.cleanText(link.textContent),
      url: this.getAbsoluteUrl(link.href),
      title: link.title || ''
    }));
  }

  /**
   * Extract document links (PDF, DOC, etc.)
   */
  extractDocumentLinks(container) {
    const documentSelectors = [
      'a[href*=".pdf"]',
      'a[href*=".doc"]',
      'a[href*=".docx"]',
      'a[href*=".xls"]',
      'a[href*=".xlsx"]',
      'a[href*=".zip"]',
      '.download-link',
      '.attachment',
      '[href*="download"]'
    ];
    
    const documents = [];
    
    for (const selector of documentSelectors) {
      const links = container.querySelectorAll(selector);
      Array.from(links).forEach(link => {
        const url = this.getAbsoluteUrl(link.href);
        if (url && this.isDocumentUrl(url)) {
          documents.push({
            text: this.cleanText(link.textContent),
            url: url,
            filename: this.extractFilename(url),
            type: this.getFileExtension(url)
          });
        }
      });
    }
    
    return documents;
  }

  /**
   * Check if URL points to a document
   */
  isDocumentUrl(url) {
    const documentExtensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip'];
    return documentExtensions.some(ext => url.toLowerCase().includes(ext));
  }

  /**
   * Extract filename from URL
   */
  extractFilename(url) {
    try {
      const pathname = new URL(url).pathname;
      return pathname.split('/').pop() || 'document';
    } catch (error) {
      return 'document';
    }
  }

  /**
   * Get file extension from URL
   */
  getFileExtension(url) {
    try {
      const filename = this.extractFilename(url);
      const parts = filename.split('.');
      return parts.length > 1 ? parts.pop().toLowerCase() : '';
    } catch (error) {
      return '';
    }
  }

  /**
   * Extract date from text
   */
  extractDate(text) {
    if (!text) return null;
    
    // Common date patterns
    const datePatterns = [
      /\d{1,2}\/\d{1,2}\/\d{4}/,  // MM/DD/YYYY
      /\d{1,2}-\d{1,2}-\d{4}/,   // MM-DD-YYYY
      /\d{4}-\d{1,2}-\d{1,2}/,   // YYYY-MM-DD
      /\d{1,2}\s+\w+\s+\d{4}/,   // DD Month YYYY
      /\w+\s+\d{1,2},?\s+\d{4}/  // Month DD, YYYY
    ];
    
    for (const pattern of datePatterns) {
      const match = text.match(pattern);
      if (match) {
        const date = new Date(match[0]);
        if (!isNaN(date.getTime())) {
          return date.toISOString();
        }
      }
    }
    
    return null;
  }

  /**
   * Extract email addresses from text
   */
  extractEmails(text) {
    if (!text) return [];
    
    const emailPattern = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
    return text.match(emailPattern) || [];
  }

  /**
   * Extract phone numbers from text
   */
  extractPhones(text) {
    if (!text) return [];
    
    const phonePatterns = [
      /\+?\d{1,4}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}/g,
      /\(\d{3}\)\s*\d{3}-\d{4}/g,
      /\d{3}-\d{3}-\d{4}/g
    ];
    
    const phones = [];
    for (const pattern of phonePatterns) {
      const matches = text.match(pattern);
      if (matches) {
        phones.push(...matches);
      }
    }
    
    return phones;
  }

  /**
   * Check if page has pagination
   */
  hasPagination() {
    const paginationSelectors = [
      '.pagination',
      '.pager',
      '.page-numbers',
      '[aria-label*="pagination"]',
      'a[href*="page"]',
      'button[aria-label*="next"]'
    ];
    
    return paginationSelectors.some(selector => 
      document.querySelector(selector)
    );
  }

  /**
   * Find next page link
   */
  findNextPageLink() {
    const nextSelectors = [
      'a[aria-label*="next"]',
      'a[title*="next"]',
      '.next',
      '.pagination-next',
      'a:contains("Next")',
      'a:contains(">")'
    ];
    
    for (const selector of nextSelectors) {
      const element = document.querySelector(selector);
      if (element && this.isElementVisible(element)) {
        return element;
      }
    }
    
    return null;
  }

  /**
   * Detect if page uses infinite scroll
   */
  hasInfiniteScroll() {
    const indicators = [
      '.infinite-scroll',
      '.load-more',
      '.lazy-load',
      '[data-infinite-scroll]'
    ];
    
    return indicators.some(selector => 
      document.querySelector(selector)
    );
  }

  /**
   * Get page metadata
   */
  getPageMetadata() {
    return {
      title: document.title,
      url: window.location.href,
      domain: window.location.hostname,
      lastModified: document.lastModified,
      charset: document.characterSet,
      language: document.documentElement.lang
    };
  }
}

