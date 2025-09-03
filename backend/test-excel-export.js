#!/usr/bin/env node
/**
 * Test Excel Export Script
 * Creates sample data and exports it as Excel files to Google Drive
 */

const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');
const moment = require('moment');
const { v4: uuidv4 } = require('uuid');

class ExcelExportTester {
    constructor() {
        this.auth = null;
        this.drive = null;
        this.sheets = null;
        this.baseFolderId = process.env.GOOGLE_DRIVE_FOLDER_ID;
    }

    async init() {
        try {
            console.log('🔍 Initializing Excel Export Tester...');
            console.log(`Node.js version: ${process.version}`);
            console.log(`OpenSSL version: ${process.versions.openssl}`);
            console.log('');

            // Set up authentication
            const serviceAccountPath = process.env.GOOGLE_APPLICATION_CREDENTIALS || 
                                       path.join(__dirname, 'service-account.json');
            
            if (!fs.existsSync(serviceAccountPath)) {
                throw new Error(`Service account file not found at: ${serviceAccountPath}`);
            }
            
            console.log(`📁 Using service account: ${serviceAccountPath}`);
            
            this.auth = new google.auth.GoogleAuth({
                keyFile: serviceAccountPath,
                scopes: [
                    'https://www.googleapis.com/auth/drive',
                    'https://www.googleapis.com/auth/spreadsheets'
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

    async listExistingFiles() {
        try {
            console.log('📋 Checking existing files in Google Drive...');
            
            // List files in the base folder
            const query = this.baseFolderId ? 
                `'${this.baseFolderId}' in parents and trashed = false` : 
                "mimeType contains 'spreadsheet' and trashed = false";
            
            const response = await this.drive.files.list({
                q: query,
                fields: 'files(id, name, mimeType, createdTime, modifiedTime, webViewLink)',
                orderBy: 'modifiedTime desc'
            });
            
            const files = response.data.files || [];
            
            if (files.length === 0) {
                console.log('📂 No files found in the specified folder');
                return [];
            }
            
            console.log(`📊 Found ${files.length} files:`);
            files.forEach((file, index) => {
                const type = file.mimeType.includes('spreadsheet') ? '📊 Spreadsheet' : 
                            file.mimeType.includes('folder') ? '📁 Folder' : '📄 File';
                console.log(`  ${index + 1}. ${type}: ${file.name}`);
                console.log(`     Created: ${moment(file.createdTime).format('YYYY-MM-DD HH:mm')}`);
                console.log(`     Link: ${file.webViewLink}`);
                console.log('');
            });
            
            return files;
            
        } catch (error) {
            console.error('❌ Failed to list files:', error.message);
            return [];
        }
    }

    generateSampleData() {
        console.log('🎯 Generating sample procurement data...');
        
        const sampleOpportunities = [
            {
                title: 'TV Commercial Production Services',
                organization: 'ABC Broadcasting Corporation',
                deadline: '2024-12-15',
                published: '2024-09-01',
                reference: 'RFP-TV-2024-001',
                sourceUrl: 'https://abc-corp.com/rfp/tv-production',
                extractedAt: new Date().toISOString()
            },
            {
                title: 'Digital Marketing Campaign Management',
                organization: 'XYZ Media Group',
                deadline: '2024-11-30',
                published: '2024-09-02',
                reference: 'RFP-DIG-2024-002',
                sourceUrl: 'https://xyzmedia.com/tenders/digital-marketing',
                extractedAt: new Date().toISOString()
            },
            {
                title: 'Radio Advertisement Placement',
                organization: 'National Radio Network',
                deadline: '2024-10-20',
                published: '2024-09-03',
                reference: 'RFP-RAD-2024-003',
                sourceUrl: 'https://nationalradio.com/procurement/ads',
                extractedAt: new Date().toISOString()
            },
            {
                title: 'Social Media Content Creation',
                organization: 'Creative Communications Ltd',
                deadline: '2024-11-15',
                published: '2024-09-01',
                reference: 'RFP-SOC-2024-004',
                sourceUrl: 'https://creativecomm.co.uk/rfp/social-media',
                extractedAt: new Date().toISOString()
            },
            {
                title: 'Print Media Advertising Campaign',
                organization: 'Metro Publishing House',
                deadline: '2024-12-01',
                published: '2024-09-02',
                reference: 'RFP-PRT-2024-005',
                sourceUrl: 'https://metropublishing.com/advertising-rfp',
                extractedAt: new Date().toISOString()
            }
        ];

        const summaryData = {
            website: 'media-procurement-test.com',
            timestamp: new Date().toISOString(),
            totalOpportunities: sampleOpportunities.length,
            mediaOpportunities: sampleOpportunities.length,
            documents: [
                'rfp-guidelines.pdf',
                'application-form.docx',
                'terms-conditions.pdf'
            ]
        };

        console.log(`✅ Generated ${sampleOpportunities.length} sample opportunities`);
        
        return {
            opportunities: sampleOpportunities,
            summary: summaryData
        };
    }

    async createTestFolder() {
        try {
            const folderName = `Test_Export_${moment().format('YYYY-MM-DD_HH-mm')}_${uuidv4().slice(0, 8)}`;
            
            console.log(`📁 Creating test folder: ${folderName}`);
            
            const folder = await this.drive.files.create({
                resource: {
                    name: folderName,
                    mimeType: 'application/vnd.google-apps.folder',
                    parents: this.baseFolderId ? [this.baseFolderId] : undefined
                },
                fields: 'id, name, webViewLink'
            });

            console.log(`✅ Created folder: ${folder.data.name}`);
            console.log(`🔗 Folder link: ${folder.data.webViewLink}`);
            
            return folder.data.id;
            
        } catch (error) {
            console.error('❌ Failed to create folder:', error.message);
            throw error;
        }
    }

    async createExcelSpreadsheet(folderId, data) {
        try {
            const sheetTitle = `Media_Procurement_Export_${moment().format('YYYY-MM-DD_HH-mm')}`;
            
            console.log(`📊 Creating Excel spreadsheet: ${sheetTitle}`);
            
            // Create spreadsheet
            const spreadsheet = await this.sheets.spreadsheets.create({
                resource: {
                    properties: { title: sheetTitle },
                    sheets: [
                        { properties: { title: 'Opportunities' } },
                        { properties: { title: 'Summary' } },
                        { properties: { title: 'Analysis' } }
                    ]
                }
            });

            const spreadsheetId = spreadsheet.data.spreadsheetId;
            
            // Move to folder
            await this.drive.files.update({
                fileId: spreadsheetId,
                addParents: folderId,
                removeParents: 'root'
            });

            // Populate with data
            await this.populateSpreadsheet(spreadsheetId, data);
            
            console.log(`✅ Created spreadsheet: ${sheetTitle}`);
            console.log(`🔗 Spreadsheet link: https://docs.google.com/spreadsheets/d/${spreadsheetId}`);
            
            return {
                id: spreadsheetId,
                url: `https://docs.google.com/spreadsheets/d/${spreadsheetId}`,
                title: sheetTitle
            };
            
        } catch (error) {
            console.error('❌ Failed to create spreadsheet:', error.message);
            throw error;
        }
    }

    async populateSpreadsheet(spreadsheetId, data) {
        try {
            console.log('📝 Populating spreadsheet with data...');
            
            // Opportunities sheet
            if (data.opportunities && data.opportunities.length > 0) {
                const headers = [
                    'Title', 'Organization', 'Deadline', 'Published', 
                    'Reference', 'Source URL', 'Extracted At'
                ];

                const rows = data.opportunities.map(opp => [
                    opp.title || '',
                    opp.organization || '',
                    opp.deadline || '',
                    opp.published || '',
                    opp.reference || '',
                    opp.sourceUrl || '',
                    opp.extractedAt || ''
                ]);

                await this.sheets.spreadsheets.values.update({
                    spreadsheetId,
                    range: 'Opportunities!A1:G' + (rows.length + 1),
                    valueInputOption: 'RAW',
                    resource: {
                        values: [headers, ...rows]
                    }
                });
                
                console.log(`✅ Added ${rows.length} opportunities to Opportunities sheet`);
            }

            // Summary sheet
            const summaryData = [
                ['Metric', 'Value'],
                ['Website', data.summary.website || ''],
                ['Collection Time', data.summary.timestamp || ''],
                ['Total Opportunities', data.summary.totalOpportunities || 0],
                ['Media Opportunities', data.summary.mediaOpportunities || 0],
                ['Documents Found', data.summary.documents?.length || 0],
                ['', ''],
                ['Document List', ''],
                ...(data.summary.documents || []).map(doc => ['', doc])
            ];

            await this.sheets.spreadsheets.values.update({
                spreadsheetId,
                range: 'Summary!A1:B' + summaryData.length,
                valueInputOption: 'RAW',
                resource: {
                    values: summaryData
                }
            });
            
            console.log('✅ Added summary data to Summary sheet');

            // Analysis sheet
            const analysisData = [
                ['Analysis', 'Result'],
                ['', ''],
                ['Deadline Analysis', ''],
                ['Urgent (< 30 days)', data.opportunities?.filter(o => moment(o.deadline).diff(moment(), 'days') < 30).length || 0],
                ['Medium term (30-90 days)', data.opportunities?.filter(o => {
                    const days = moment(o.deadline).diff(moment(), 'days');
                    return days >= 30 && days <= 90;
                }).length || 0],
                ['Long term (> 90 days)', data.opportunities?.filter(o => moment(o.deadline).diff(moment(), 'days') > 90).length || 0],
                ['', ''],
                ['Organization Analysis', ''],
                ['Total Unique Organizations', [...new Set(data.opportunities?.map(o => o.organization) || [])].length],
                ['', ''],
                ['Export Information', ''],
                ['Export Date', moment().format('YYYY-MM-DD HH:mm:ss')],
                ['Export Version', 'v1.0']
            ];

            await this.sheets.spreadsheets.values.update({
                spreadsheetId,
                range: 'Analysis!A1:B' + analysisData.length,
                valueInputOption: 'RAW',
                resource: {
                    values: analysisData
                }
            });
            
            console.log('✅ Added analysis data to Analysis sheet');
            
        } catch (error) {
            console.error('❌ Failed to populate spreadsheet:', error.message);
        }
    }

    async downloadAsExcel(spreadsheetId, filename) {
        try {
            console.log(`⬇️ Downloading spreadsheet as Excel file: ${filename}`);
            
            // Export as Excel (XLSX)
            const response = await this.drive.files.export({
                fileId: spreadsheetId,
                mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }, {
                responseType: 'stream'
            });

            const outputPath = path.join(__dirname, filename);
            const writer = fs.createWriteStream(outputPath);
            
            response.data.pipe(writer);
            
            return new Promise((resolve, reject) => {
                writer.on('finish', () => {
                    console.log(`✅ Excel file saved: ${outputPath}`);
                    resolve(outputPath);
                });
                writer.on('error', reject);
            });
            
        } catch (error) {
            console.error('❌ Failed to download Excel file:', error.message);
            throw error;
        }
    }

    async runFullTest() {
        try {
            console.log('🚀 Starting Excel Export Test...\n');
            
            // Initialize
            const initialized = await this.init();
            if (!initialized) {
                throw new Error('Failed to initialize');
            }
            
            // List existing files
            await this.listExistingFiles();
            console.log('');
            
            // Generate sample data
            const sampleData = this.generateSampleData();
            console.log('');
            
            // Create test folder
            const folderId = await this.createTestFolder();
            console.log('');
            
            // Create Excel spreadsheet
            const spreadsheet = await this.createExcelSpreadsheet(folderId, sampleData);
            console.log('');
            
            // Download as Excel file
            const excelFilename = `${spreadsheet.title}.xlsx`;
            await this.downloadAsExcel(spreadsheet.id, excelFilename);
            console.log('');
            
            // Final summary
            console.log('🎉 Excel Export Test Completed Successfully!');
            console.log('');
            console.log('📊 Results:');
            console.log(`   - Test folder created in Google Drive`);
            console.log(`   - Spreadsheet created: ${spreadsheet.title}`);
            console.log(`   - Excel file downloaded: ${excelFilename}`);
            console.log(`   - Direct link: ${spreadsheet.url}`);
            console.log('');
            console.log('✅ Excel exports are now working in Google Drive!');
            
        } catch (error) {
            console.error('❌ Excel Export Test failed:', error.message);
            process.exit(1);
        }
    }
}

// Run the test
if (require.main === module) {
    const tester = new ExcelExportTester();
    tester.runFullTest();
}

module.exports = { ExcelExportTester };
