#!/usr/bin/env node
/**
 * Local MacBook Pro Configuration Test
 * Tests all functionality locally before Google Cloud Run deployment
 */

const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');
const moment = require('moment');
const os = require('os');

class LocalConfigTester {
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
        
        const icon = status === 'PASS' ? '✅' : status === 'FAIL' ? '❌' : '⚠️';
        console.log(`${icon} ${testName}: ${status}`);
        if (details) {
            console.log(`   ${details}`);
        }
    }

    async testSystemEnvironment() {
        console.log('🖥️ Testing Local MacBook Pro Environment...\n');
        
        // Test system info
        this.logTest('MacOS Detection', 
            process.platform === 'darwin' ? 'PASS' : 'FAIL',
            `Platform: ${process.platform}, Architecture: ${process.arch}`
        );
        
        this.logTest('Node.js Version', 
            parseFloat(process.version.slice(1)) >= 18 ? 'PASS' : 'FAIL',
            `Version: ${process.version}`
        );
        
        this.logTest('OpenSSL Version', 
            process.versions.openssl ? 'PASS' : 'FAIL',
            `Version: ${process.versions.openssl}`
        );
        
        // Test memory
        const totalMemory = Math.round(os.totalmem() / 1024 / 1024 / 1024);
        this.logTest('System Memory', 
            totalMemory >= 8 ? 'PASS' : 'WARN',
            `${totalMemory}GB RAM available`
        );
        
        // Test disk space in current directory
        try {
            const stats = fs.statSync(__dirname);
            this.logTest('Directory Access', 'PASS', `Working directory: ${__dirname}`);
        } catch (error) {
            this.logTest('Directory Access', 'FAIL', error.message);
        }
        
        console.log('');
    }

    async testEnvironmentVariables() {
        console.log('🔧 Testing Environment Variables...\n');
        
        // Test .env file
        const envPath = path.join(__dirname, '.env');
        this.logTest('.env File Exists', 
            fs.existsSync(envPath) ? 'PASS' : 'FAIL',
            `Path: ${envPath}`
        );
        
        // Test Google credentials path
        const credPath = process.env.GOOGLE_APPLICATION_CREDENTIALS || 
                         path.join(__dirname, 'service-account.json');
        this.logTest('Google Credentials Path', 
            fs.existsSync(credPath) ? 'PASS' : 'FAIL',
            `Path: ${credPath}`
        );
        
        // Test folder ID
        this.logTest('Drive Folder ID', 
            process.env.GOOGLE_DRIVE_FOLDER_ID ? 'PASS' : 'WARN',
            process.env.GOOGLE_DRIVE_FOLDER_ID || 'Not set (will use root)'
        );
        
        // Test API keys
        const apiKeys = process.env.API_KEYS;
        this.logTest('API Keys Configuration', 
            apiKeys ? 'PASS' : 'WARN',
            apiKeys ? `${apiKeys.split(',').length} keys configured` : 'Not set'
        );
        
        // Test port
        const port = process.env.PORT || '8081';
        this.logTest('Port Configuration', 'PASS', `Port: ${port}`);
        
        console.log('');
    }

    async testGoogleAuthentication() {
        console.log('🔐 Testing Google Authentication...\n');
        
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
            
            this.logTest('Auth Client Creation', 'PASS', 'Google auth client initialized');
            
            // Test drive connection
            const driveResponse = await this.drive.about.get({ fields: 'user' });
            this.logTest('Google Drive API', 'PASS', 
                `Connected as: ${driveResponse.data.user.emailAddress}`
            );
            
            // Test sheets API
            // Create a test spreadsheet to verify write permissions
            try {
                const testSheet = await this.sheets.spreadsheets.create({
                    resource: {
                        properties: { title: `MacBook_Test_${moment().format('YYYY-MM-DD_HH-mm-ss')}` }
                    }
                });
                
                this.logTest('Google Sheets API', 'PASS', 
                    `Test spreadsheet created: ${testSheet.data.spreadsheetId}`
                );
                
                // Clean up test sheet
                await this.drive.files.delete({ fileId: testSheet.data.spreadsheetId });
                this.logTest('Cleanup Test Files', 'PASS', 'Test spreadsheet deleted');
                
            } catch (error) {
                this.logTest('Google Sheets API', 'FAIL', `Cannot create spreadsheets: ${error.message}`);
            }
            
        } catch (error) {
            this.logTest('Google Authentication', 'FAIL', error.message);
        }
        
        console.log('');
    }

    async testServerCapabilities() {
        console.log('🚀 Testing Server Capabilities...\n');
        
        // Test server file
        const serverPath = path.join(__dirname, 'server.js');
        this.logTest('Server File Exists', 
            fs.existsSync(serverPath) ? 'PASS' : 'FAIL',
            `Path: ${serverPath}`
        );
        
        // Test node modules
        const nodeModulesPath = path.join(__dirname, 'node_modules');
        this.logTest('Dependencies Installed', 
            fs.existsSync(nodeModulesPath) ? 'PASS' : 'FAIL',
            `Path: ${nodeModulesPath}`
        );
        
        // Test required dependencies
        const requiredDeps = [
            'express', 'googleapis', 'cors', 'helmet', 
            'compression', 'dotenv', 'multer', 'winston', 
            'joi', 'uuid', 'moment'
        ];
        
        let depCount = 0;
        for (const dep of requiredDeps) {
            try {
                require.resolve(dep);
                depCount++;
            } catch (error) {
                // Dependency not found
            }
        }
        
        this.logTest('Required Dependencies', 
            depCount === requiredDeps.length ? 'PASS' : 'WARN',
            `${depCount}/${requiredDeps.length} dependencies available`
        );
        
        console.log('');
    }

    async testFileOperations() {
        console.log('📁 Testing File Operations...\n');
        
        try {
            // Test write permissions
            const testFile = path.join(__dirname, 'test_write.tmp');
            fs.writeFileSync(testFile, 'MacBook Pro local test');
            this.logTest('File Write Permissions', 'PASS', 'Can create files locally');
            
            // Test read permissions
            const content = fs.readFileSync(testFile, 'utf8');
            this.logTest('File Read Permissions', 
                content === 'MacBook Pro local test' ? 'PASS' : 'FAIL',
                'Can read files locally'
            );
            
            // Cleanup
            fs.unlinkSync(testFile);
            this.logTest('File Cleanup', 'PASS', 'Can delete files locally');
            
        } catch (error) {
            this.logTest('File Operations', 'FAIL', error.message);
        }
        
        console.log('');
    }

    async testNetworkConnectivity() {
        console.log('🌐 Testing Network Connectivity...\n');
        
        // Test Google APIs reachability
        try {
            const https = require('https');
            const testUrls = [
                'https://www.googleapis.com',
                'https://drive.google.com',
                'https://sheets.googleapis.com'
            ];
            
            for (const url of testUrls) {
                try {
                    await new Promise((resolve, reject) => {
                        const req = https.request(url, { method: 'HEAD' }, (res) => {
                            this.logTest(`Network: ${url}`, 'PASS', `Status: ${res.statusCode}`);
                            resolve();
                        });
                        req.on('error', reject);
                        req.setTimeout(5000, () => reject(new Error('Timeout')));
                        req.end();
                    });
                } catch (error) {
                    this.logTest(`Network: ${url}`, 'FAIL', error.message);
                }
            }
            
        } catch (error) {
            this.logTest('Network Connectivity', 'FAIL', error.message);
        }
        
        console.log('');
    }

    async testExcelExportCapabilities() {
        console.log('📊 Testing Excel Export Capabilities...\n');
        
        if (!this.drive || !this.sheets) {
            this.logTest('Excel Export Test', 'SKIP', 'Authentication failed, skipping Excel tests');
            console.log('');
            return;
        }
        
        try {
            // Test creating and downloading Excel
            const testData = {
                headers: ['Test Column 1', 'Test Column 2', 'Timestamp'],
                rows: [
                    ['MacBook Pro', 'Local Test', moment().format('YYYY-MM-DD HH:mm:ss')],
                    ['Configuration', 'Validation', moment().format('YYYY-MM-DD HH:mm:ss')]
                ]
            };
            
            // Create test spreadsheet
            const spreadsheet = await this.sheets.spreadsheets.create({
                resource: {
                    properties: { title: `MacBook_Excel_Test_${moment().format('HHmmss')}` }
                }
            });
            
            // Add data
            await this.sheets.spreadsheets.values.update({
                spreadsheetId: spreadsheet.data.spreadsheetId,
                range: 'A1:C3',
                valueInputOption: 'RAW',
                resource: {
                    values: [testData.headers, ...testData.rows]
                }
            });
            
            this.logTest('Create Test Spreadsheet', 'PASS', 
                `ID: ${spreadsheet.data.spreadsheetId}`);
            
            // Test Excel export
            const response = await this.drive.files.export({
                fileId: spreadsheet.data.spreadsheetId,
                mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }, {
                responseType: 'arraybuffer'
            });
            
            this.logTest('Excel Export', 'PASS', 
                `Excel file generated (${response.data.byteLength} bytes)`);
            
            // Save test Excel file
            const testExcelPath = path.join(__dirname, 'macbook_test_export.xlsx');
            fs.writeFileSync(testExcelPath, Buffer.from(response.data));
            
            this.logTest('Save Excel Locally', 'PASS', 
                `File saved: ${testExcelPath}`);
            
            // Cleanup
            await this.drive.files.delete({ fileId: spreadsheet.data.spreadsheetId });
            fs.unlinkSync(testExcelPath);
            
            this.logTest('Excel Test Cleanup', 'PASS', 'Test files cleaned up');
            
        } catch (error) {
            this.logTest('Excel Export Capabilities', 'FAIL', error.message);
        }
        
        console.log('');
    }

    generateTestReport() {
        console.log('📋 MacBook Pro Local Configuration Test Report');
        console.log('=' .repeat(60));
        console.log(`🕒 Test completed at: ${moment().format('YYYY-MM-DD HH:mm:ss')}`);
        console.log(`🖥️  Platform: MacOS ${os.release()}`);
        console.log(`📍 Working Directory: ${__dirname}`);
        console.log('');
        
        const summary = {
            total: this.testResults.length,
            passed: this.testResults.filter(r => r.status === 'PASS').length,
            failed: this.testResults.filter(r => r.status === 'FAIL').length,
            warnings: this.testResults.filter(r => r.status === 'WARN').length,
            skipped: this.testResults.filter(r => r.status === 'SKIP').length
        };
        
        console.log('📊 Test Summary:');
        console.log(`   ✅ Passed: ${summary.passed}`);
        console.log(`   ❌ Failed: ${summary.failed}`);
        console.log(`   ⚠️  Warnings: ${summary.warnings}`);
        console.log(`   ⏭️  Skipped: ${summary.skipped}`);
        console.log(`   📝 Total: ${summary.total}`);
        console.log('');
        
        // Deployment readiness
        const isReady = summary.failed === 0;
        console.log('🚀 Google Cloud Run Deployment Readiness:');
        console.log(`   Status: ${isReady ? '✅ READY' : '❌ NOT READY'}`);
        
        if (!isReady) {
            console.log('   ⚠️  Fix the failed tests before deploying to Google Cloud Run');
            const failedTests = this.testResults.filter(r => r.status === 'FAIL');
            failedTests.forEach(test => {
                console.log(`      - ${test.test}: ${test.details}`);
            });
        } else {
            console.log('   🎉 All critical tests passed - ready for cloud deployment!');
        }
        
        console.log('');
        console.log('📝 Next Steps:');
        if (isReady) {
            console.log('   1. ✅ Local configuration is working correctly');
            console.log('   2. 🚀 Ready to deploy to Google Cloud Run');
            console.log('   3. 🔗 Test server locally with: npm start');
            console.log('   4. 📊 Test Excel exports with: npm run ubuntu-excel');
            console.log('   5. ☁️  Deploy with: npm run deploy');
        } else {
            console.log('   1. 🔧 Fix the failed configuration tests');
            console.log('   2. 🔄 Re-run this test: npm run test-config');
            console.log('   3. 📖 Check the documentation for troubleshooting');
        }
        
        return isReady;
    }

    async runAllTests() {
        try {
            console.log('🧪 MacBook Pro Local Configuration Testing');
            console.log('🔬 Preparing for Google Cloud Run Deployment');
            console.log('=' .repeat(60));
            console.log('');
            
            await this.testSystemEnvironment();
            await this.testEnvironmentVariables();
            await this.testGoogleAuthentication();
            await this.testServerCapabilities();
            await this.testFileOperations();
            await this.testNetworkConnectivity();
            await this.testExcelExportCapabilities();
            
            const isReady = this.generateTestReport();
            
            process.exit(isReady ? 0 : 1);
            
        } catch (error) {
            console.error('❌ Test execution failed:', error.message);
            process.exit(1);
        }
    }
}

// Run local configuration tests
if (require.main === module) {
    const tester = new LocalConfigTester();
    tester.runAllTests();
}

module.exports = { LocalConfigTester };
