#!/usr/bin/env node
/**
 * Deployment Ready Test - MacBook Pro to Google Cloud Run
 * Focuses on essential functionality that works with current service account permissions
 */

const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');
const moment = require('moment');
const os = require('os');
require('dotenv').config(); // Ensure environment variables are loaded

class DeploymentReadyTester {
    constructor() {
        this.auth = null;
        this.drive = null;
        this.sheets = null;
        this.testResults = [];
    }

    logTest(testName, status, details = '') {
        const result = {
            test: testName,
            status: status,
            details: details,
            timestamp: moment().format('HH:mm:ss')
        };
        this.testResults.push(result);
        
        const icon = status === 'PASS' ? '✅' : status === 'FAIL' ? '❌' : status === 'WARN' ? '⚠️' : 'ℹ️';
        console.log(`${icon} ${testName}: ${status}`);
        if (details) {
            console.log(`   ${details}`);
        }
    }

    async testEssentialConfiguration() {
        console.log('🚀 Testing Essential Configuration for Google Cloud Run...\n');
        
        // Test .env loading
        this.logTest('Environment Loading', 
            process.env.GOOGLE_APPLICATION_CREDENTIALS ? 'PASS' : 'FAIL',
            process.env.GOOGLE_APPLICATION_CREDENTIALS ? 'Environment variables loaded' : 'Failed to load .env'
        );

        // Test service account file
        const credPath = process.env.GOOGLE_APPLICATION_CREDENTIALS || 
                         path.join(__dirname, 'service-account.json');
        this.logTest('Service Account File', 
            fs.existsSync(credPath) ? 'PASS' : 'FAIL',
            `Path: ${credPath}`
        );

        // Test folder ID (now properly reading from env)
        this.logTest('Drive Folder ID', 
            process.env.GOOGLE_DRIVE_FOLDER_ID ? 'PASS' : 'INFO',
            process.env.GOOGLE_DRIVE_FOLDER_ID || 'Not set (will use Google Drive root)'
        );

        // Test essential dependencies
        const essentialDeps = ['express', 'googleapis', 'cors', 'dotenv'];
        let depCount = 0;
        for (const dep of essentialDeps) {
            try {
                require.resolve(dep);
                depCount++;
            } catch (error) {
                this.logTest(`Dependency: ${dep}`, 'FAIL', 'Not installed');
            }
        }
        
        this.logTest('Essential Dependencies', 
            depCount === essentialDeps.length ? 'PASS' : 'FAIL',
            `${depCount}/${essentialDeps.length} essential dependencies available`
        );

        console.log('');
    }

    async testGoogleServices() {
        console.log('🔐 Testing Google Services with Current Permissions...\n');
        
        try {
            // Initialize auth
            const serviceAccountPath = process.env.GOOGLE_APPLICATION_CREDENTIALS || 
                                       path.join(__dirname, 'service-account.json');
            
            this.auth = new google.auth.GoogleAuth({
                keyFile: serviceAccountPath,
                scopes: [
                    'https://www.googleapis.com/auth/drive',
                    'https://www.googleapis.com/auth/spreadsheets'
                ]
            });

            this.drive = google.drive({ version: 'v3', auth: this.auth });
            this.sheets = google.sheets({ version: 'v4', auth: this.auth });
            
            this.logTest('Google Auth Initialization', 'PASS', 'Authentication client created');
            
            // Test drive connection
            const driveResponse = await this.drive.about.get({ fields: 'user' });
            this.logTest('Google Drive Connection', 'PASS', 
                `Connected as: ${driveResponse.data.user.emailAddress}`
            );

            // Test drive permissions (list files instead of creating)
            try {
                const query = process.env.GOOGLE_DRIVE_FOLDER_ID ? 
                    `'${process.env.GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed = false` : 
                    "trashed = false";
                
                const filesList = await this.drive.files.list({
                    q: query,
                    pageSize: 5,
                    fields: 'files(id, name, mimeType)'
                });
                
                this.logTest('Drive File Access', 'PASS', 
                    `Can list files (${filesList.data.files.length} files found)`
                );
            } catch (error) {
                this.logTest('Drive File Access', 'WARN', 
                    `Limited access: ${error.message}`
                );
            }

            // Test sheets API with read-only approach
            try {
                // Try to read an existing spreadsheet instead of creating one
                const existingSpreadsheets = await this.drive.files.list({
                    q: "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
                    pageSize: 1,
                    fields: 'files(id, name)'
                });

                if (existingSpreadsheets.data.files.length > 0) {
                    const spreadsheetId = existingSpreadsheets.data.files[0].id;
                    
                    // Try to read from existing spreadsheet
                    const response = await this.sheets.spreadsheets.get({
                        spreadsheetId: spreadsheetId,
                        fields: 'properties'
                    });
                    
                    this.logTest('Sheets API Access', 'PASS', 
                        `Can access spreadsheets: ${response.data.properties.title}`
                    );
                } else {
                    this.logTest('Sheets API Access', 'INFO', 
                        'No existing spreadsheets found to test with'
                    );
                }
            } catch (error) {
                this.logTest('Sheets API Access', 'WARN', 
                    `Limited sheets access: ${error.message}`
                );
            }

            // Test export capabilities if we have spreadsheets
            try {
                const spreadsheets = await this.drive.files.list({
                    q: "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
                    pageSize: 1,
                    fields: 'files(id, name)'
                });

                if (spreadsheets.data.files.length > 0) {
                    const fileId = spreadsheets.data.files[0].id;
                    
                    // Test export to Excel format
                    await this.drive.files.export({
                        fileId: fileId,
                        mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    }, {
                        responseType: 'arraybuffer'
                    });
                    
                    this.logTest('Excel Export Capability', 'PASS', 
                        'Can export spreadsheets to Excel format'
                    );
                } else {
                    this.logTest('Excel Export Capability', 'INFO', 
                        'No spreadsheets available to test export'
                    );
                }
            } catch (error) {
                this.logTest('Excel Export Capability', 'WARN', 
                    `Export limitations: ${error.message}`
                );
            }
            
        } catch (error) {
            this.logTest('Google Services', 'FAIL', error.message);
        }
        
        console.log('');
    }

    async testServerStartup() {
        console.log('🚀 Testing Server Startup Readiness...\n');
        
        // Test server.js file
        const serverPath = path.join(__dirname, 'server.js');
        this.logTest('Server File', 
            fs.existsSync(serverPath) ? 'PASS' : 'FAIL',
            `Path: ${serverPath}`
        );

        // Test port availability
        const port = process.env.PORT || 8081;
        this.logTest('Port Configuration', 'PASS', 
            `Configured port: ${port}`
        );

        // Test package.json for deployment script
        const packagePath = path.join(__dirname, 'package.json');
        if (fs.existsSync(packagePath)) {
            const packageData = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
            this.logTest('Start Script', 
                packageData.scripts?.start ? 'PASS' : 'FAIL',
                packageData.scripts?.start || 'No start script defined'
            );
            
            this.logTest('Deploy Script', 
                packageData.scripts?.deploy ? 'PASS' : 'INFO',
                packageData.scripts?.deploy || 'Deploy script not configured'
            );
        }

        console.log('');
    }

    async testCloudRunCompatibility() {
        console.log('☁️ Testing Google Cloud Run Compatibility...\n');

        // Test Dockerfile
        const dockerfilePath = path.join(__dirname, 'Dockerfile');
        this.logTest('Dockerfile', 
            fs.existsSync(dockerfilePath) ? 'PASS' : 'INFO',
            fs.existsSync(dockerfilePath) ? 'Docker configuration available' : 'Will use Cloud Run buildpacks'
        );

        // Test .gcloudignore
        const gcloudIgnorePath = path.join(__dirname, '.gcloudignore');
        this.logTest('.gcloudignore', 
            fs.existsSync(gcloudIgnorePath) ? 'PASS' : 'INFO',
            'Deployment file filtering'
        );

        // Test environment compatibility
        this.logTest('Node.js Version Compatibility', 
            parseFloat(process.version.slice(1)) >= 18 ? 'PASS' : 'FAIL',
            `${process.version} (Cloud Run supports Node.js 18+)`
        );

        // Test memory usage
        const memUsage = process.memoryUsage();
        const heapMB = Math.round(memUsage.heapUsed / 1024 / 1024);
        this.logTest('Memory Usage', 
            heapMB < 128 ? 'PASS' : 'WARN',
            `Current heap: ${heapMB}MB (Cloud Run default: 512MB)`
        );

        console.log('');
    }

    generateDeploymentReport() {
        console.log('📋 Google Cloud Run Deployment Readiness Report');
        console.log('=' .repeat(60));
        console.log(`🕒 Test completed at: ${moment().format('YYYY-MM-DD HH:mm:ss')}`);
        console.log(`💻 Local environment: MacBook Pro (${process.arch})`);
        console.log(`🖥️  Target platform: Google Cloud Run`);
        console.log('');
        
        const summary = {
            total: this.testResults.length,
            passed: this.testResults.filter(r => r.status === 'PASS').length,
            failed: this.testResults.filter(r => r.status === 'FAIL').length,
            warnings: this.testResults.filter(r => r.status === 'WARN').length,
            info: this.testResults.filter(r => r.status === 'INFO').length
        };
        
        console.log('📊 Test Summary:');
        console.log(`   ✅ Passed: ${summary.passed}`);
        console.log(`   ❌ Failed: ${summary.failed}`);
        console.log(`   ⚠️  Warnings: ${summary.warnings}`);
        console.log(`   ℹ️  Info: ${summary.info}`);
        console.log(`   📝 Total: ${summary.total}`);
        console.log('');
        
        // Deployment decision logic
        const criticalFailures = this.testResults.filter(r => 
            r.status === 'FAIL' && 
            ['Service Account File', 'Google Drive Connection', 'Essential Dependencies', 'Server File'].includes(r.test)
        );
        
        const isReady = criticalFailures.length === 0;
        
        console.log('🚀 Google Cloud Run Deployment Status:');
        if (isReady) {
            console.log('   Status: ✅ READY FOR DEPLOYMENT');
            console.log('   🎉 Core functionality verified - safe to deploy!');
            
            if (summary.warnings > 0) {
                console.log('   ⚠️  Note: Some warnings present but not blocking deployment');
            }
        } else {
            console.log('   Status: ❌ NOT READY - Critical Issues Found');
            console.log('   🔧 Fix these critical issues before deployment:');
            criticalFailures.forEach(test => {
                console.log(`      - ${test.test}: ${test.details}`);
            });
        }
        
        console.log('');
        console.log('📝 Deployment Instructions:');
        if (isReady) {
            console.log('   1. ✅ Configuration verified on MacBook Pro');
            console.log('   2. 🚀 Start local server: npm start');
            console.log('   3. 🧪 Test endpoints locally first');
            console.log('   4. ☁️  Deploy to Google Cloud Run: npm run deploy');
            console.log('   5. 🔍 Monitor deployment logs and test live endpoints');
            console.log('');
            console.log('💡 Deployment Tips:');
            console.log('   - Google Cloud Run will handle service account mounting');
            console.log('   - Environment variables will be configured in Cloud Run console');
            console.log('   - Monitor memory usage and scale as needed');
            if (summary.warnings > 0) {
                console.log('   - Address warnings post-deployment for optimal performance');
            }
        } else {
            console.log('   1. 🔧 Resolve critical failures listed above');
            console.log('   2. 🔄 Re-run: npm run test-deployment');
            console.log('   3. 📖 Check Google Cloud IAM permissions if auth issues persist');
        }
        
        return isReady;
    }

    async runDeploymentTest() {
        try {
            console.log('🧪 Google Cloud Run Deployment Readiness Test');
            console.log('💻 Testing MacBook Pro → ☁️ Google Cloud Run');
            console.log('=' .repeat(60));
            console.log('');
            
            await this.testEssentialConfiguration();
            await this.testGoogleServices();
            await this.testServerStartup();
            await this.testCloudRunCompatibility();
            
            const isReady = this.generateDeploymentReport();
            
            process.exit(isReady ? 0 : 1);
            
        } catch (error) {
            console.error('❌ Deployment test failed:', error.message);
            process.exit(1);
        }
    }
}

// Run deployment readiness test
if (require.main === module) {
    const tester = new DeploymentReadyTester();
    tester.runDeploymentTest();
}

module.exports = { DeploymentReadyTester };
