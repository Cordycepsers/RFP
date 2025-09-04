#!/usr/bin/env node
/**
 * Check Google Drive Files Script
 * Lists existing files and downloads Excel exports
 */

const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');
const moment = require('moment');

class DriveFileChecker {
    constructor() {
        this.auth = null;
        this.drive = null;
        this.sheets = null;
        this.baseFolderId = process.env.GOOGLE_DRIVE_FOLDER_ID;
    }

    async init() {
        try {
            console.log('🔍 Initializing Google Drive File Checker...');
            
            // Set up authentication
            const serviceAccountPath = process.env.GOOGLE_APPLICATION_CREDENTIALS || 
                                       path.join(__dirname, 'service-account.json');
            
            if (!fs.existsSync(serviceAccountPath)) {
                throw new Error(`Service account file not found at: ${serviceAccountPath}`);
            }
            
            this.auth = new google.auth.GoogleAuth({
                keyFile: serviceAccountPath,
                scopes: [
                    'https://www.googleapis.com/auth/drive.readonly',
                    'https://www.googleapis.com/auth/spreadsheets.readonly'
                ]
            });

            this.drive = google.drive({ version: 'v3', auth: this.auth });
            this.sheets = google.sheets({ version: 'v4', auth: this.auth });
            
            console.log('✅ Google APIs initialized successfully');
            return true;
            
        } catch (error) {
            console.error('❌ Initialization failed:', error.message);
            return false;
        }
    }

    async listAllFiles() {
        try {
            console.log('📋 Listing all files in Google Drive...');
            
            // List files in the base folder or all spreadsheets
            let query;
            if (this.baseFolderId) {
                query = `'${this.baseFolderId}' in parents and trashed = false`;
                console.log(`🎯 Searching in folder: ${this.baseFolderId}`);
            } else {
                query = "trashed = false";
                console.log('🎯 Searching all accessible files');
            }
            
            const response = await this.drive.files.list({
                q: query,
                fields: 'files(id, name, mimeType, createdTime, modifiedTime, webViewLink, size, parents)',
                orderBy: 'modifiedTime desc',
                pageSize: 50
            });
            
            const files = response.data.files || [];
            
            if (files.length === 0) {
                console.log('📂 No files found');
                return [];
            }
            
            console.log(`\\n📊 Found ${files.length} files:\\n`);
            
            // Categorize files
            const categories = {
                spreadsheets: [],
                documents: [],
                folders: [],
                other: []
            };
            
            files.forEach(file => {
                if (file.mimeType.includes('spreadsheet')) {
                    categories.spreadsheets.push(file);
                } else if (file.mimeType.includes('document') || file.mimeType.includes('pdf') || file.mimeType.includes('word')) {
                    categories.documents.push(file);
                } else if (file.mimeType.includes('folder')) {
                    categories.folders.push(file);
                } else {
                    categories.other.push(file);
                }
            });
            
            // Display by category
            if (categories.spreadsheets.length > 0) {
                console.log('📊 SPREADSHEETS & EXCEL FILES:');
                categories.spreadsheets.forEach((file, index) => {
                    const size = file.size ? `(${Math.round(file.size / 1024)}KB)` : '';
                    console.log(`  ${index + 1}. ${file.name} ${size}`);
                    console.log(`     Created: ${moment(file.createdTime).format('YYYY-MM-DD HH:mm')}`);
                    console.log(`     Modified: ${moment(file.modifiedTime).format('YYYY-MM-DD HH:mm')}`);
                    console.log(`     Link: ${file.webViewLink}`);
                    console.log('');
                });
            }
            
            if (categories.documents.length > 0) {
                console.log('📄 DOCUMENTS:');
                categories.documents.forEach((file, index) => {
                    const size = file.size ? `(${Math.round(file.size / 1024)}KB)` : '';
                    console.log(`  ${index + 1}. ${file.name} ${size}`);
                    console.log(`     Type: ${file.mimeType}`);
                    console.log(`     Link: ${file.webViewLink}`);
                    console.log('');
                });
            }
            
            if (categories.folders.length > 0) {
                console.log('📁 FOLDERS:');
                categories.folders.forEach((file, index) => {
                    console.log(`  ${index + 1}. ${file.name}`);
                    console.log(`     Link: ${file.webViewLink}`);
                    console.log('');
                });
            }
            
            return files;
            
        } catch (error) {
            console.error('❌ Failed to list files:', error.message);
            return [];
        }
    }

    async downloadSpreadsheetAsExcel(fileId, fileName) {
        try {
            console.log(`⬇️ Downloading ${fileName} as Excel...`);
            
            // Get file metadata first
            const metadata = await this.drive.files.get({
                fileId: fileId,
                fields: 'id, name, mimeType, size'
            });
            
            console.log(`📋 File: ${metadata.data.name}`);
            console.log(`📊 Type: ${metadata.data.mimeType}`);
            
            // Download as Excel if it's a Google Sheets file
            if (metadata.data.mimeType === 'application/vnd.google-apps.spreadsheet') {
                const response = await this.drive.files.export({
                    fileId: fileId,
                    mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                }, {
                    responseType: 'stream'
                });

                const outputPath = path.join(__dirname, `${fileName}.xlsx`);
                const writer = fs.createWriteStream(outputPath);
                
                response.data.pipe(writer);
                
                return new Promise((resolve, reject) => {
                    writer.on('finish', () => {
                        console.log(`✅ Excel file saved: ${outputPath}`);
                        resolve(outputPath);
                    });
                    writer.on('error', reject);
                });
            } else {
                console.log('ℹ️  File is not a Google Sheets document, skipping Excel export');
                return null;
            }
            
        } catch (error) {
            console.error(`❌ Failed to download ${fileName}:`, error.message);
            return null;
        }
    }

    async readSpreadsheetData(fileId, fileName) {
        try {
            console.log(`📖 Reading data from ${fileName}...`);
            
            // Read the first sheet
            const response = await this.sheets.spreadsheets.values.get({
                spreadsheetId: fileId,
                range: 'A1:Z100', // Read first 100 rows and columns A-Z
            });
            
            const rows = response.data.values || [];
            
            if (rows.length === 0) {
                console.log('📄 Spreadsheet is empty');
                return null;
            }
            
            console.log(`📊 Found ${rows.length} rows of data`);
            console.log(`📋 Headers: ${rows[0]?.join(', ')}`);
            console.log(`📈 Sample data (first 3 rows):`);
            
            rows.slice(0, Math.min(4, rows.length)).forEach((row, index) => {
                if (index === 0) {
                    console.log(`     Headers: [${row.join(', ')}]`);
                } else {
                    console.log(`     Row ${index}: [${row.slice(0, 5).join(', ')}${row.length > 5 ? '...' : ''}]`);
                }
            });
            
            return rows;
            
        } catch (error) {
            console.error(`❌ Failed to read ${fileName}:`, error.message);
            return null;
        }
    }

    async analyzeFiles() {
        try {
            console.log('🔍 Starting Google Drive Analysis...\\n');
            
            // Initialize
            const initialized = await this.init();
            if (!initialized) {
                throw new Error('Failed to initialize');
            }
            
            // List all files
            const files = await this.listAllFiles();
            
            if (files.length === 0) {
                console.log('📂 No files to analyze');
                return;
            }
            
            // Focus on spreadsheets
            const spreadsheets = files.filter(f => f.mimeType.includes('spreadsheet'));
            
            if (spreadsheets.length === 0) {
                console.log('📊 No spreadsheets found');
                return;
            }
            
            console.log(`\\n🔍 Analyzing ${spreadsheets.length} spreadsheets...\\n`);
            
            // Analyze the most recent ones
            const recentSpreadsheets = spreadsheets.slice(0, 3);
            
            for (const file of recentSpreadsheets) {
                console.log(`\\n📊 Analyzing: ${file.name}`);
                console.log('─'.repeat(50));
                
                // Read data
                const data = await this.readSpreadsheetData(file.id, file.name);
                
                // Download as Excel
                if (data && data.length > 0) {
                    await this.downloadSpreadsheetAsExcel(file.id, file.name.replace(/[^a-zA-Z0-9]/g, '_'));
                }
                
                console.log('');
            }
            
            console.log('\\n🎉 Analysis Complete!');
            console.log('\\n📁 Downloaded Files:');
            
            // List downloaded files
            const downloadedFiles = fs.readdirSync(__dirname).filter(f => f.endsWith('.xlsx'));
            downloadedFiles.forEach((file, index) => {
                const stats = fs.statSync(path.join(__dirname, file));
                console.log(`  ${index + 1}. ${file} (${Math.round(stats.size / 1024)}KB)`);
            });
            
        } catch (error) {
            console.error('❌ Analysis failed:', error.message);
        }
    }
}

// Run the analysis
if (require.main === module) {
    const checker = new DriveFileChecker();
    checker.analyzeFiles();
}

module.exports = { DriveFileChecker };
