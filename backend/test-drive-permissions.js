#!/usr/bin/env node
/**
 * Test Google Drive with Proper Permissions
 * Tests the specific shared drives and spreadsheets provided
 */

const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');
const moment = require('moment');
require('dotenv').config();

class DrivePermissionTester {
    constructor() {
        this.auth = null;
        this.drive = null;
        this.sheets = null;
        
        // Your specific Google Drive resources
        this.sharedDriveId = process.env.GOOGLE_DRIVE_FOLDER_ID; // 0AHbM0SsjOuLRUk9PVA
        this.rfpFolderId = process.env.GOOGLE_RFP_FOLDER_ID; // 1FGCuypq0uc2_5zrqvWaXVVRbjfcYdbWe
        this.scrapedSheetId = process.env.GOOGLE_SCRAPED_SHEET_ID; // 1oCIum685cKVr6ZGKPk8aSe3ZPAWAg9NPWT7C2YL6ezw
    }

    async init() {
        try {
            console.log('🔐 Initializing Google Drive Permission Test...');
            console.log(`📁 Shared Drive: ${this.sharedDriveId}`);
            console.log(`📂 RFP Folder: ${this.rfpFolderId}`);
            console.log(`📊 Scraped Sheet: ${this.scrapedSheetId}`);
            console.log('');

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
            
            console.log('✅ Google APIs initialized');
            return true;
            
        } catch (error) {
            console.error('❌ Initialization failed:', error.message);
            return false;
        }
    }

    async testSharedDriveAccess() {
        try {
            console.log('📁 Testing Shared Drive Access...');
            
            // List files in shared drive root
            const response = await this.drive.files.list({
                q: `'${this.sharedDriveId}' in parents and trashed = false`,
                fields: 'files(id, name, mimeType, createdTime, modifiedTime, size)',
                pageSize: 10
            });
            
            const files = response.data.files || [];
            console.log(`✅ Shared drive accessible - found ${files.length} items`);
            
            files.forEach((file, index) => {
                const type = file.mimeType.includes('spreadsheet') ? '📊' : 
                            file.mimeType.includes('folder') ? '📁' : 
                            file.mimeType.includes('document') ? '📄' : '📎';
                const size = file.size ? ` (${Math.round(file.size / 1024)}KB)` : '';
                console.log(`   ${index + 1}. ${type} ${file.name}${size}`);
            });
            
            console.log('');
            return true;
            
        } catch (error) {
            console.error('❌ Shared drive access failed:', error.message);
            return false;
        }
    }

    async testRFPFolderAccess() {
        try {
            console.log('📂 Testing RFP Folder Access...');
            
            // Get folder metadata
            const folderInfo = await this.drive.files.get({
                fileId: this.rfpFolderId,
                fields: 'id, name, description, createdTime, modifiedTime'
            });
            
            console.log(`✅ RFP Folder accessible: ${folderInfo.data.name}`);
            console.log(`   Created: ${moment(folderInfo.data.createdTime).format('YYYY-MM-DD HH:mm')}`);
            
            // List files in RFP folder
            const response = await this.drive.files.list({
                q: `'${this.rfpFolderId}' in parents and trashed = false`,
                fields: 'files(id, name, mimeType, size, modifiedTime)',
                pageSize: 20
            });
            
            const files = response.data.files || [];
            console.log(`   Contains ${files.length} files:`);
            
            files.forEach((file, index) => {
                const type = file.mimeType.includes('spreadsheet') ? '📊 XLS' : 
                            file.mimeType.includes('pdf') ? '📄 PDF' : 
                            file.mimeType.includes('document') ? '📝 DOC' : '📎';
                const size = file.size ? ` (${Math.round(file.size / 1024)}KB)` : '';
                const modified = moment(file.modifiedTime).format('MM-DD HH:mm');
                console.log(`     ${index + 1}. ${type} ${file.name}${size} [${modified}]`);
            });
            
            console.log('');
            return true;
            
        } catch (error) {
            console.error('❌ RFP folder access failed:', error.message);
            return false;
        }
    }

    async testScrapedSheetAccess() {
        try {
            console.log('📊 Testing Scraped Data Spreadsheet...');
            
            // Get spreadsheet metadata
            const sheetInfo = await this.sheets.spreadsheets.get({
                spreadsheetId: this.scrapedSheetId,
                fields: 'properties, sheets(properties)'
            });
            
            const props = sheetInfo.data.properties;
            console.log(`✅ Spreadsheet accessible: ${props.title}`);
            console.log(`   Created: ${moment(props.createdTime).format('YYYY-MM-DD HH:mm')}`);
            console.log(`   Updated: ${moment(props.updatedTime).format('YYYY-MM-DD HH:mm')}`);
            
            // List sheets
            const sheets = sheetInfo.data.sheets || [];
            console.log(`   Contains ${sheets.length} sheets:`);
            sheets.forEach((sheet, index) => {
                const sheetProps = sheet.properties;
                console.log(`     ${index + 1}. ${sheetProps.title} (${sheetProps.gridProperties.rowCount} rows)`);
            });
            
            // Try to read some data from the first sheet
            const firstSheetName = sheets[0]?.properties?.title || 'Sheet1';
            try {
                const dataResponse = await this.sheets.spreadsheets.values.get({
                    spreadsheetId: this.scrapedSheetId,
                    range: `${firstSheetName}!A1:Z10`, // First 10 rows
                });
                
                const rows = dataResponse.data.values || [];
                if (rows.length > 0) {
                    console.log(`   📈 Sample data (${rows.length} rows found):`);
                    console.log(`     Headers: [${rows[0]?.slice(0, 5).join(', ')}${rows[0]?.length > 5 ? '...' : ''}]`);
                    if (rows.length > 1) {
                        console.log(`     First row: [${rows[1]?.slice(0, 3).join(', ')}...]`);
                    }
                } else {
                    console.log('   📄 Sheet appears to be empty');
                }
                
            } catch (readError) {
                console.log(`   ⚠️  Could not read data: ${readError.message}`);
            }
            
            console.log('');
            return true;
            
        } catch (error) {
            console.error('❌ Scraped sheet access failed:', error.message);
            return false;
        }
    }

    async testExcelExportFromExisting() {
        try {
            console.log('📊 Testing Excel Export from Existing Sheet...');
            
            // Export the scraped sheet to Excel format
            const response = await this.drive.files.export({
                fileId: this.scrapedSheetId,
                mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }, {
                responseType: 'stream'
            });

            const outputPath = path.join(__dirname, 'RFP_scraped_export.xlsx');
            const writer = fs.createWriteStream(outputPath);
            
            response.data.pipe(writer);
            
            await new Promise((resolve, reject) => {
                writer.on('finish', () => {
                    const stats = fs.statSync(outputPath);
                    console.log(`✅ Excel export successful!`);
                    console.log(`   📁 Saved to: ${outputPath}`);
                    console.log(`   📊 File size: ${Math.round(stats.size / 1024)}KB`);
                    resolve();
                });
                writer.on('error', reject);
            });
            
            console.log('');
            return true;
            
        } catch (error) {
            console.error('❌ Excel export failed:', error.message);
            return false;
        }
    }

    async testCreateFileInRFPFolder() {
        try {
            console.log('📝 Testing File Creation in RFP Folder...');
            
            // Try to create a simple text file for testing
            const testFileName = `MacBook_Test_${moment().format('YYYY-MM-DD_HH-mm-ss')}.txt`;
            const testContent = `Test file created from MacBook Pro
Created: ${moment().format('YYYY-MM-DD HH:mm:ss')}
Purpose: Testing write permissions to RFP folder
Environment: Local development
Target: Google Cloud Run deployment`;

            const response = await this.drive.files.create({
                resource: {
                    name: testFileName,
                    parents: [this.rfpFolderId],
                    description: 'Test file from MacBook Pro configuration validation'
                },
                media: {
                    mimeType: 'text/plain',
                    body: testContent
                },
                fields: 'id, name, webViewLink'
            });

            console.log(`✅ File creation successful!`);
            console.log(`   📁 File: ${response.data.name}`);
            console.log(`   🆔 ID: ${response.data.id}`);
            console.log(`   🔗 Link: ${response.data.webViewLink}`);
            
            // Clean up test file
            await this.drive.files.delete({ fileId: response.data.id });
            console.log(`   🧹 Test file cleaned up`);
            
            console.log('');
            return true;
            
        } catch (error) {
            console.error('❌ File creation failed:', error.message);
            return false;
        }
    }

    async testWriteToScrapedSheet() {
        try {
            console.log('✏️ Testing Write Access to Scraped Sheet...');
            
            // Try to append a test row to the scraped sheet
            const testData = [
                moment().format('YYYY-MM-DD HH:mm:ss'),
                'MacBook Pro Test',
                'Configuration Validation',
                'Local Testing',
                'Ready for deployment',
                'test@example.com'
            ];

            // First, find a good place to write (try to append to existing data)
            const sheets = await this.sheets.spreadsheets.get({
                spreadsheetId: this.scrapedSheetId,
                fields: 'sheets(properties)'
            });
            
            const firstSheetName = sheets.data.sheets[0]?.properties?.title || 'Sheet1';
            
            // Get existing data to find next empty row
            const existingData = await this.sheets.spreadsheets.values.get({
                spreadsheetId: this.scrapedSheetId,
                range: `${firstSheetName}!A:A`
            });
            
            const nextRow = (existingData.data.values?.length || 0) + 1;
            const range = `${firstSheetName}!A${nextRow}:F${nextRow}`;
            
            await this.sheets.spreadsheets.values.update({
                spreadsheetId: this.scrapedSheetId,
                range: range,
                valueInputOption: 'RAW',
                resource: {
                    values: [testData]
                }
            });

            console.log(`✅ Write successful!`);
            console.log(`   📊 Added test row at: ${range}`);
            console.log(`   📝 Data: [${testData.slice(0, 3).join(', ')}...]`);
            
            // Clean up: remove the test row
            await this.sheets.spreadsheets.values.clear({
                spreadsheetId: this.scrapedSheetId,
                range: range
            });
            
            console.log(`   🧹 Test data cleaned up`);
            console.log('');
            return true;
            
        } catch (error) {
            console.error('❌ Write to scraped sheet failed:', error.message);
            console.log('   ℹ️  This may be expected if sheet is read-only');
            console.log('');
            return false;
        }
    }

    async runAllTests() {
        try {
            console.log('🧪 Google Drive Permissions Test');
            console.log('🔗 Testing Specific Shared Resources');
            console.log('=' .repeat(50));
            console.log('');
            
            const initialized = await this.init();
            if (!initialized) return;
            
            const results = [];
            results.push(await this.testSharedDriveAccess());
            results.push(await this.testRFPFolderAccess());
            results.push(await this.testScrapedSheetAccess());
            results.push(await this.testExcelExportFromExisting());
            results.push(await this.testCreateFileInRFPFolder());
            results.push(await this.testWriteToScrapedSheet());
            
            // Summary
            const passed = results.filter(r => r).length;
            const total = results.length;
            
            console.log('📋 Test Results Summary');
            console.log('=' .repeat(30));
            console.log(`✅ Passed: ${passed}/${total}`);
            console.log(`❌ Failed: ${total - passed}/${total}`);
            console.log('');
            
            if (passed >= 4) { // Core functionality working
                console.log('🎉 Google Drive integration is working!');
                console.log('✅ Ready for Ubuntu webscraper configuration');
                console.log('🚀 Ready for Google Cloud Run deployment');
                console.log('');
                console.log('📂 Your Resources:');
                console.log(`   • Shared Drive: https://drive.google.com/drive/folders/${this.sharedDriveId}`);
                console.log(`   • RFP Folder: https://drive.google.com/drive/folders/${this.rfpFolderId}`);
                console.log(`   • Scraped Sheet: https://docs.google.com/spreadsheets/d/${this.scrapedSheetId}`);
                console.log('');
                console.log('🔧 Next Steps:');
                console.log('   1. npm start - Test server locally');
                console.log('   2. npm run deploy - Deploy to Google Cloud Run');
                console.log('   3. Configure Ubuntu webscraper to use these resources');
            } else {
                console.log('⚠️  Some permissions issues detected');
                console.log('📖 Check service account permissions');
            }
            
        } catch (error) {
            console.error('❌ Test execution failed:', error.message);
        }
    }
}

// Run permission tests
if (require.main === module) {
    const tester = new DrivePermissionTester();
    tester.runAllTests();
}

module.exports = { DrivePermissionTester };
