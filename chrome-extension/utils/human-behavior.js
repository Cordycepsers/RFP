/**
 * Human Behavior Simulator
 * Mimics natural browsing patterns to avoid bot detection
 */

class HumanBehaviorSimulator {
  constructor() {
    this.profile = this.generateBehaviorProfile();
    this.lastActionTime = Date.now();
  }

  generateBehaviorProfile() {
    return {
      typing: {
        speed: 45 + Math.random() * 40, // 45-85 WPM
        variability: 0.3 + Math.random() * 0.4,
        pauseProbability: 0.05 + Math.random() * 0.15
      },
      mouse: {
        speed: 0.5 + Math.random() * 1.0,
        accuracy: 0.8 + Math.random() * 0.2
      },
      timing: {
        actionDelay: {
          min: 500 + Math.random() * 1000,
          max: 2000 + Math.random() * 3000
        }
      }
    };
  }

  async randomDelay(min = 500, max = 2000) {
    const delay = min + Math.random() * (max - min);
    return new Promise(resolve => setTimeout(resolve, delay));
  }

  async typeText(element, text) {
    if (!element) return;

    // Clear existing text
    element.focus();
    element.select();
    
    // Type character by character with human-like timing
    for (let i = 0; i < text.length; i++) {
      const char = text[i];
      
      // Simulate typing
      element.value = element.value + char;
      element.dispatchEvent(new Event('input', { bubbles: true }));
      
      // Random pause between characters
      if (Math.random() < this.profile.typing.pauseProbability) {
        await this.randomDelay(100, 300);
      }
      
      // Character delay based on typing speed
      const charDelay = (60 / this.profile.typing.speed) * 1000 / 5; // Average 5 chars per word
      const variance = charDelay * this.profile.typing.variability;
      const actualDelay = charDelay + (Math.random() - 0.5) * variance;
      
      await this.randomDelay(Math.max(50, actualDelay - 25), actualDelay + 25);
    }
    
    // Trigger change event
    element.dispatchEvent(new Event('change', { bubbles: true }));
  }

  async simulateClick(element = null) {
    if (element) {
      // Move mouse to element first
      await this.simulateMouseMovement(element);
      
      // Add small delay before click
      await this.randomDelay(100, 300);
      
      // Simulate click
      element.click();
    }
    
    // Update last action time
    this.lastActionTime = Date.now();
  }

  async simulateMouseMovement(element) {
    if (!element) return;
    
    const rect = element.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    // Add some randomness to click position
    const offsetX = (Math.random() - 0.5) * rect.width * 0.3;
    const offsetY = (Math.random() - 0.5) * rect.height * 0.3;
    
    // Simulate mouse movement event
    const mouseEvent = new MouseEvent('mousemove', {
      clientX: centerX + offsetX,
      clientY: centerY + offsetY,
      bubbles: true
    });
    
    element.dispatchEvent(mouseEvent);
  }

  async simulateScroll(direction = 'down', amount = null) {
    const scrollAmount = amount || (300 + Math.random() * 400);
    const scrollDirection = direction === 'down' ? scrollAmount : -scrollAmount;
    
    // Smooth scroll simulation
    const steps = 10;
    const stepAmount = scrollDirection / steps;
    
    for (let i = 0; i < steps; i++) {
      window.scrollBy(0, stepAmount);
      await this.randomDelay(20, 50);
    }
    
    // Random pause after scrolling
    await this.randomDelay(500, 1500);
  }

  async simulateReading(element) {
    if (!element) return;
    
    const text = element.textContent || '';
    const wordCount = text.split(' ').length;
    
    // Estimate reading time (200-300 words per minute)
    const readingSpeed = 200 + Math.random() * 100;
    const readingTime = (wordCount / readingSpeed) * 60 * 1000;
    
    // Minimum and maximum reading times
    const minTime = Math.max(1000, readingTime * 0.5);
    const maxTime = Math.min(10000, readingTime * 1.5);
    
    await this.randomDelay(minTime, maxTime);
  }

  getTimeSinceLastAction() {
    return Date.now() - this.lastActionTime;
  }

  async ensureHumanTiming() {
    const timeSinceLastAction = this.getTimeSinceLastAction();
    const minTimeBetweenActions = this.profile.timing.actionDelay.min;
    
    if (timeSinceLastAction < minTimeBetweenActions) {
      const additionalDelay = minTimeBetweenActions - timeSinceLastAction;
      await this.randomDelay(additionalDelay, additionalDelay + 500);
    }
  }

  // Simulate natural browsing patterns
  async simulateNaturalBrowsing() {
    // Random mouse movements
    if (Math.random() < 0.3) {
      const randomElement = document.elementFromPoint(
        Math.random() * window.innerWidth,
        Math.random() * window.innerHeight
      );
      if (randomElement) {
        await this.simulateMouseMovement(randomElement);
      }
    }
    
    // Occasional scrolling
    if (Math.random() < 0.2) {
      await this.simulateScroll();
    }
    
    // Random pauses
    if (Math.random() < 0.1) {
      await this.randomDelay(1000, 3000);
    }
  }
}

