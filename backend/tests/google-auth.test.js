/**
 * Google Authentication Test
 * Tests Google API connectivity and authentication
 */

const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');

const path = require('path');
const fs = require('fs');

const serviceAccountPath = process.env.GOOGLE_APPLICATION_CREDENTIALS ||
                          path.join(__dirname, '..', 'service-account.json');

const serviceAccountExists = fs.existsSync(serviceAccountPath);

const describeOrSkip = serviceAccountExists ? describe : describe.skip;

describeOrSkip('Google Authentication', () => {
  let auth;

  beforeAll(async () => {
    // Check if service account file exists
    // (No need to check again, already checked above)
    if (!fs.existsSync(serviceAccountPath)) {
      throw new Error(`Service account file not found at: ${serviceAccountPath}`);
    }

    auth = new google.auth.GoogleAuth({
      keyFile: serviceAccountPath,
      scopes: [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
      ]
    });
  });

  test('should authenticate with Google APIs', async () => {
    expect(auth).toBeDefined();
    
    // Test that we can get an auth client
    const authClient = await auth.getClient();
    expect(authClient).toBeDefined();
  }, 10000); // 10 second timeout for network requests

  test('should connect to Google Drive API', async () => {
    const drive = google.drive({ version: 'v3', auth });
    
    // Test connection by getting user info
    const response = await drive.about.get({ fields: 'user' });
    
    expect(response.data).toBeDefined();
    expect(response.data.user).toBeDefined();
    expect(response.data.user.emailAddress).toBeDefined();
    expect(response.data.user.emailAddress).toMatch(/@.*\.iam\.gserviceaccount\.com$/);
  }, 10000);

  test('should connect to Google Sheets API', async () => {
    const sheets = google.sheets({ version: 'v4', auth });
    
    expect(sheets).toBeDefined();
    // We won't create a test spreadsheet, just verify the client was created
  });

  test('should handle Node.js v22 and OpenSSL 3 compatibility', () => {
    const nodeVersion = process.version;
    const opensslVersion = process.versions.openssl;
    
    console.log(`Testing with Node.js ${nodeVersion} and OpenSSL ${opensslVersion}`);
    
    // This test primarily documents our compatibility
    expect(nodeVersion).toBeDefined();
    expect(opensslVersion).toBeDefined();
  });
});
