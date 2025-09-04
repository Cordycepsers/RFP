#!/usr/bin/env node
/**
 * Simple Google Authentication Verification Script
 * Verifies that Google authentication works correctly with Node.js v22 and OpenSSL 3
 */

const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');

async function verifyGoogleAuth() {
  try {
    console.log('🔍 Verifying Google authentication...');
    console.log(`Node.js version: ${process.version}`);
    console.log(`OpenSSL version: ${process.versions.openssl}`);
    console.log('');
    
    // Check service account file
    const serviceAccountPath = process.env.GOOGLE_APPLICATION_CREDENTIALS || 
                               path.join(__dirname, 'service-account.json');
    
    if (!fs.existsSync(serviceAccountPath)) {
      throw new Error(
        `Service account file not found at: ${serviceAccountPath}\n` +
        `Please ensure you have created a Google Cloud service account and downloaded its JSON credentials file.\n` +
        `You can specify the path using the GOOGLE_APPLICATION_CREDENTIALS environment variable.\n` +
        `For instructions, see: https://cloud.google.com/iam/docs/creating-managing-service-account-keys`
      );
    }
    
    console.log(`📁 Using service account: ${serviceAccountPath}`);
    
    // Set up authentication
    const auth = new google.auth.GoogleAuth({
      keyFile: serviceAccountPath,
      scopes: [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
      ]
    });
    
    console.log('✅ Authentication object created successfully');
    
    // Test Google Drive connection
    console.log('🔗 Testing Google Drive API connection...');
    const drive = google.drive({ version: 'v3', auth });
    const response = await drive.about.get({ fields: 'user' });
    
    console.log(`✅ Google Drive API connected successfully`);
    console.log(`📧 Service account email: ${response.data.user.emailAddress}`);
    
    // Test Google Sheets API
    console.log('📊 Testing Google Sheets API...');
    const sheets = google.sheets({ version: 'v4', auth });
    console.log('✅ Google Sheets API client created successfully');
    
    console.log('');
    console.log('🎉 All authentication tests passed!');
    console.log('✅ Google authentication is working correctly with Node.js v22 and OpenSSL 3');
    
  } catch (error) {
    console.error('❌ Authentication verification failed:', error.message);
    if (error.code) {
      console.error(`Error code: ${error.code}`);
    }
    process.exit(1);
  }
}

if (require.main === module) {
  verifyGoogleAuth();
}

module.exports = { verifyGoogleAuth };
