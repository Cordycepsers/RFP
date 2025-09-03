/**
 * Chrome Extension Test Helper
 * 
 * This script provides utility functions to test the Media Procurement Platform
 * Chrome extension functionality. Run these commands in the browser console
 * while testing the extension.
 */

// Test Helper Functions
window.MediaProcurementTester = {
    
    /**
     * Test extension installation and basic functionality
     */
    testBasicFunctionality: async function() {
        console.log("🧪 Testing Basic Functionality...");
        
        try {
            // Check if extension is loaded
            const response = await chrome.runtime.sendMessage({action: "ping"});
            console.log("✅ Extension loaded:", response);
            
            // Check configuration
            const config = await chrome.runtime.sendMessage({action: "getConfig"});
            console.log("✅ Configuration:", config);
            
            // Check website detection
            const website = await chrome.runtime.sendMessage({action: "detectWebsite"});
            console.log("✅ Website detection:", website);
            
            return true;
        } catch (error) {
            console.error("❌ Basic functionality test failed:", error);
            return false;
        }
    },
    
    /**
     * Test data collection on current page
     */
    testDataCollection: async function() {
        console.log("🧪 Testing Data Collection...");
        
        try {
            // Start collection
            const result = await chrome.runtime.sendMessage({
                action: "startCollection",
                websites: ["current"]
            });
            
            console.log("✅ Collection started:", result);
            
            // Monitor progress
            this.monitorProgress();
            
            return true;
        } catch (error) {
            console.error("❌ Data collection test failed:", error);
            return false;
        }
    },
    
    /**
     * Monitor collection progress
     */
    monitorProgress: function() {
        const interval = setInterval(async () => {
            try {
                const status = await chrome.runtime.sendMessage({action: "getStatus"});
                console.log("📊 Progress:", status);
                
                if (status.completed) {
                    clearInterval(interval);
                    console.log("✅ Collection completed!");
                    this.displayResults(status.results);
                }
            } catch (error) {
                console.error("❌ Progress monitoring failed:", error);
                clearInterval(interval);
            }
        }, 2000);
    },
    
    /**
     * Display collection results
     */
    displayResults: function(results) {
        console.log("📋 Collection Results:");
        console.table(results);
        
        // Analyze results
        const totalOpportunities = results.length;
        const mediaRelevant = results.filter(item => 
            this.containsMediaKeywords(item.title + " " + item.description)
        ).length;
        
        console.log(`📊 Summary:
        - Total Opportunities: ${totalOpportunities}
        - Media Relevant: ${mediaRelevant}
        - Relevance Rate: ${((mediaRelevant/totalOpportunities)*100).toFixed(1)}%`);
    },
    
    /**
     * Check if text contains media keywords
     */
    containsMediaKeywords: function(text) {
        const mediaKeywords = [
            'video', 'photo', 'film', 'multimedia', 'podcast', 'animation',
            'audiovisual', 'media', 'communication', 'production', 'graphic',
            'design', 'branding', 'creative', 'advertising', 'marketing',
            'documentary', 'broadcasting', 'digital', 'content', 'visualization'
        ];
        
        const lowerText = text.toLowerCase();
        return mediaKeywords.some(keyword => lowerText.includes(keyword));
    },
    
    /**
     * Test website selectors on current page
     */
    testSelectors: function() {
        console.log("🧪 Testing Website Selectors...");
        
        // Get current website configuration
        const currentUrl = window.location.href;
        console.log("🌐 Current URL:", currentUrl);
        
        // Test common selectors
        const selectors = [
            '.opportunities-list, .tender-list, table tbody, .procurement-list',
            '.opportunity-item, .tender-item, tr, .procurement-item',
            '.opportunity-title, .tender-title, h3, h4, td:first-child a',
            '.organization, .client, .funder, td:nth-child(2)',
            '.deadline, .closing-date, .expires, td:nth-child(3)',
            '.published, .posted, .date, td:nth-child(4)'
        ];
        
        selectors.forEach((selector, index) => {
            const elements = document.querySelectorAll(selector);
            console.log(`Selector ${index + 1}: "${selector}" → ${elements.length} elements found`);
            
            if (elements.length > 0) {
                console.log("Sample element:", elements[0]);
            }
        });
    },
    
    /**
     * Test human behavior simulation
     */
    testHumanBehavior: function() {
        console.log("🧪 Testing Human Behavior Simulation...");
        
        // Simulate random mouse movements
        for (let i = 0; i < 5; i++) {
            setTimeout(() => {
                const x = Math.random() * window.innerWidth;
                const y = Math.random() * window.innerHeight;
                
                const event = new MouseEvent('mousemove', {
                    clientX: x,
                    clientY: y,
                    bubbles: true
                });
                
                document.dispatchEvent(event);
                console.log(`🖱️ Mouse moved to (${x.toFixed(0)}, ${y.toFixed(0)})`);
            }, i * 1000 + Math.random() * 2000);
        }
        
        // Simulate scrolling
        setTimeout(() => {
            window.scrollBy(0, 200);
            console.log("📜 Scrolled down");
        }, 3000);
    },
    
    /**
     * Test backend connectivity
     */
    testBackendConnection: async function() {
        console.log("🧪 Testing Backend Connection...");
        
        try {
            const response = await chrome.runtime.sendMessage({action: "testBackend"});
            console.log("✅ Backend connection:", response);
            return true;
        } catch (error) {
            console.error("❌ Backend connection failed:", error);
            return false;
        }
    },
    
    /**
     * Run comprehensive test suite
     */
    runFullTestSuite: async function() {
        console.log("🚀 Running Full Test Suite...");
        console.log("=" .repeat(50));
        
        const tests = [
            { name: "Basic Functionality", fn: this.testBasicFunctionality },
            { name: "Backend Connection", fn: this.testBackendConnection },
            { name: "Website Selectors", fn: this.testSelectors },
            { name: "Human Behavior", fn: this.testHumanBehavior },
            { name: "Data Collection", fn: this.testDataCollection }
        ];
        
        const results = [];
        
        for (const test of tests) {
            console.log(`\n🧪 Running: ${test.name}`);
            try {
                const result = await test.fn.call(this);
                results.push({ name: test.name, status: result ? "PASS" : "FAIL" });
                console.log(`${result ? "✅" : "❌"} ${test.name}: ${result ? "PASSED" : "FAILED"}`);
            } catch (error) {
                results.push({ name: test.name, status: "ERROR" });
                console.error(`❌ ${test.name}: ERROR -`, error);
            }
            
            // Wait between tests
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        // Display final results
        console.log("\n📊 Test Suite Results:");
        console.log("=" .repeat(50));
        console.table(results);
        
        const passed = results.filter(r => r.status === "PASS").length;
        const total = results.length;
        console.log(`\n🎯 Overall: ${passed}/${total} tests passed (${((passed/total)*100).toFixed(1)}%)`);
    },
    
    /**
     * Quick test for specific website
     */
    quickTest: function(websiteName) {
        console.log(`🧪 Quick Test for: ${websiteName || "Current Website"}`);
        
        // Test selectors
        this.testSelectors();
        
        // Test data extraction
        setTimeout(() => {
            this.testDataCollection();
        }, 2000);
    }
};

// Auto-run basic test when script loads
console.log("🔧 Media Procurement Test Helper Loaded");
console.log("📖 Available commands:");
console.log("  MediaProcurementTester.runFullTestSuite() - Run all tests");
console.log("  MediaProcurementTester.quickTest() - Quick test current page");
console.log("  MediaProcurementTester.testSelectors() - Test CSS selectors");
console.log("  MediaProcurementTester.testDataCollection() - Test data collection");
console.log("  MediaProcurementTester.testBackendConnection() - Test backend");

// Keyboard shortcut to run quick test (Ctrl+Shift+T)
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.shiftKey && e.key === 'T') {
        e.preventDefault();
        MediaProcurementTester.quickTest();
    }
});

console.log("⌨️ Keyboard shortcut: Ctrl+Shift+T for quick test");

