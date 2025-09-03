/**
 * Simplified Media Procurement Backend Server
 * Google Cloud Run deployment with Google Drive integration
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const { google } = require('googleapis');
const multer = require('multer');
const winston = require('winston');
const Joi = require('joi');
const { v4: uuidv4 } = require('uuid');
const moment = require('moment');

require('dotenv').config();

class MediaProcurementServer {
  constructor() {
    this.app = express();
this.port = process.env.PORT || 3000;
    
    // Google APIs
    this.auth = null;
    this.drive = null;
    this.sheets = null;
    
    // Configuration
    this.baseFolderId = process.env.GOOGLE_DRIVE_FOLDER_ID;
    this.allowedApiKeys = (process.env.API_KEYS || '').split(',').filter(Boolean);
    
    this.init();
  }

  async init() {
    try {
      console.log('🚀 Initializing Media Procurement Server...');
      
      await this.setupGoogleAuth();
      this.setupMiddleware();
      this.setupRoutes();
      this.setupErrorHandling();
      
      console.log('✅ Server initialization complete');
    } catch (error) {
      console.error('❌ Server initialization failed:', error);
      process.exit(1);
    }
  }

  async setupGoogleAuth() {
    try {
      // Service account authentication using JSON file
      const path = require('path');
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

      // Test connection
      const response = await this.drive.about.get({ fields: 'user' });
      console.log(`✅ Google Drive connected as: ${response.data.user.emailAddress}`);
      
    } catch (error) {
      console.error('❌ Google authentication failed:', error);
      throw error;
    }
  }

  setupMiddleware() {
    // Security
    this.app.use(helmet({
      contentSecurityPolicy: false,
      crossOriginEmbedderPolicy: false
    }));

    // CORS
    this.app.use(cors({
      origin: true,
      credentials: true,
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization', 'X-Client-Email']
    }));

    // Compression
    this.app.use(compression());

    // Body parsing
    this.app.use(express.json({ limit: '50mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '50mb' }));

    // Logging
    this.app.use((req, res, next) => {
      console.log(`${req.method} ${req.path} - ${req.ip}`);
      next();
    });

    // API Key authentication
    this.app.use('/api', this.authenticateApiKey.bind(this));
  }

  authenticateApiKey(req, res, next) {
    // Skip authentication for health check
    if (req.path === '/health') {
      return next();
    }

    const authHeader = req.headers.authorization;
    const apiKey = authHeader?.replace('Bearer ', '');

    if (!apiKey || !this.allowedApiKeys.includes(apiKey)) {
      return res.status(401).json({ error: 'Invalid API key' });
    }

    next();
  }

  setupRoutes() {
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        uptime: process.uptime()
      });
    });

    // API routes
    this.app.post('/api/upload-data', this.handleDataUpload.bind(this));
    this.app.post('/api/upload-files', this.handleFileUpload.bind(this));
    this.app.get('/api/status', this.handleStatusCheck.bind(this));

    // Root endpoint
    this.app.get('/', (req, res) => {
      res.json({
        name: 'Media Procurement Backend',
        version: '1.0.0',
        status: 'running',
        endpoints: {
          health: '/health',
          uploadData: '/api/upload-data',
          uploadFiles: '/api/upload-files',
          status: '/api/status'
        }
      });
    });
  }

  async handleDataUpload(req, res) {
    try {
      // Validate request
      const schema = Joi.object({
        website: Joi.string().required(),
        data: Joi.object().required(),
        timestamp: Joi.string().isoDate().required()
      });

      const { error, value } = schema.validate(req.body);
      if (error) {
        return res.status(400).json({ error: error.details[0].message });
      }

      const { website, data, timestamp } = value;
      const clientEmail = req.headers['x-client-email'];

      console.log(`📊 Processing data upload from ${website}`);

      // Create folder structure
      const folderId = await this.createCollectionFolder(timestamp);

      // Upload data as spreadsheet
      const spreadsheetResult = await this.createDataSpreadsheet(
        folderId, 
        website, 
        data, 
        timestamp
      );

      // Share with client if email provided
      if (clientEmail) {
        await this.shareFolder(folderId, clientEmail);
      }

      res.json({
        success: true,
        folderId: folderId,
        spreadsheetId: spreadsheetResult.id,
        spreadsheetUrl: spreadsheetResult.url,
        folderUrl: `https://drive.google.com/drive/folders/${folderId}`,
        timestamp: new Date().toISOString()
      });

    } catch (error) {
      console.error('Data upload error:', error);
      res.status(500).json({ error: 'Failed to upload data' });
    }
  }

  async handleFileUpload(req, res) {
    try {
      // Handle file uploads (documents)
      const upload = multer({ 
        storage: multer.memoryStorage(),
        limits: { fileSize: 50 * 1024 * 1024 } // 50MB
      }).array('files');

      upload(req, res, async (err) => {
        if (err) {
          return res.status(400).json({ error: 'File upload error' });
        }

        const files = req.files || [];
        const folderId = req.body.folderId;

        if (!folderId) {
          return res.status(400).json({ error: 'Folder ID required' });
        }

        const uploadedFiles = [];

        for (const file of files) {
          try {
            const result = await this.uploadFileToDrive(
              file.buffer,
              file.originalname,
              file.mimetype,
              folderId
            );
            uploadedFiles.push(result);
          } catch (error) {
            console.error(`Failed to upload ${file.originalname}:`, error);
          }
        }

        res.json({
          success: true,
          uploadedFiles: uploadedFiles,
          count: uploadedFiles.length
        });
      });

    } catch (error) {
      console.error('File upload error:', error);
      res.status(500).json({ error: 'Failed to upload files' });
    }
  }

  async handleStatusCheck(req, res) {
    try {
      // Check Google Drive connection
      const driveStatus = await this.drive.about.get({ fields: 'user, storageQuota' });
      
      res.json({
        status: 'operational',
        googleDrive: {
          connected: true,
          user: driveStatus.data.user.emailAddress,
          storageUsed: driveStatus.data.storageQuota?.usage || 0
        },
        server: {
          uptime: process.uptime(),
          memory: process.memoryUsage(),
          timestamp: new Date().toISOString()
        }
      });

    } catch (error) {
      res.status(500).json({
        status: 'error',
        error: error.message
      });
    }
  }

  async createCollectionFolder(timestamp) {
    try {
      const date = moment(timestamp).format('YYYY-MM-DD');
      const folderName = `Media_Procurement_${date}_${uuidv4().slice(0, 8)}`;

      const folder = await this.drive.files.create({
        resource: {
          name: folderName,
          mimeType: 'application/vnd.google-apps.folder',
          parents: this.baseFolderId ? [this.baseFolderId] : undefined
        },
        fields: 'id, name, webViewLink'
      });

      console.log(`📁 Created folder: ${folderName}`);
      return folder.data.id;

    } catch (error) {
      console.error('Failed to create folder:', error);
      throw error;
    }
  }

  async createDataSpreadsheet(folderId, website, data, timestamp) {
    try {
      const sheetTitle = `${website}_${moment(timestamp).format('YYYY-MM-DD_HH-mm')}`;

      // Create spreadsheet
      const spreadsheet = await this.sheets.spreadsheets.create({
        resource: {
          properties: { title: sheetTitle },
          sheets: [
            { properties: { title: 'Opportunities' } },
            { properties: { title: 'Summary' } }
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

      console.log(`📊 Created spreadsheet: ${sheetTitle}`);

      return {
        id: spreadsheetId,
        url: `https://docs.google.com/spreadsheets/d/${spreadsheetId}`,
        title: sheetTitle
      };

    } catch (error) {
      console.error('Failed to create spreadsheet:', error);
      throw error;
    }
  }

  async populateSpreadsheet(spreadsheetId, data) {
    try {
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
      }

      // Summary sheet
      const summaryData = [
        ['Metric', 'Value'],
        ['Website', data.website || ''],
        ['Collection Time', data.timestamp || ''],
        ['Total Opportunities', data.totalOpportunities || 0],
        ['Media Opportunities', data.mediaOpportunities || 0],
        ['Documents Found', data.documents?.length || 0]
      ];

      await this.sheets.spreadsheets.values.update({
        spreadsheetId,
        range: 'Summary!A1:B6',
        valueInputOption: 'RAW',
        resource: {
          values: summaryData
        }
      });

    } catch (error) {
      console.error('Failed to populate spreadsheet:', error);
    }
  }

  async uploadFileToDrive(buffer, filename, mimeType, parentId) {
    try {
      const response = await this.drive.files.create({
        resource: {
          name: filename,
          parents: [parentId]
        },
        media: {
          mimeType: mimeType,
          body: buffer
        },
        fields: 'id, name, webViewLink, size'
      });

      return {
        id: response.data.id,
        name: response.data.name,
        url: response.data.webViewLink,
        size: response.data.size
      };

    } catch (error) {
      console.error(`Failed to upload ${filename}:`, error);
      throw error;
    }
  }

  async shareFolder(folderId, email) {
    try {
      await this.drive.permissions.create({
        fileId: folderId,
        resource: {
          role: 'reader',
          type: 'user',
          emailAddress: email
        },
        sendNotificationEmail: true,
        emailMessage: 'Media procurement data collection results are ready.'
      });

      console.log(`🔗 Shared folder with: ${email}`);

    } catch (error) {
      console.error('Failed to share folder:', error);
      // Don't throw - sharing failure shouldn't break the upload
    }
  }

  setupErrorHandling() {
    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({ 
        error: 'Endpoint not found',
        path: req.originalUrl 
      });
    });

    // Global error handler
    this.app.use((error, req, res, next) => {
      console.error('Server error:', error);
      res.status(500).json({ 
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    });

    // Process error handlers
    process.on('uncaughtException', (error) => {
      console.error('Uncaught Exception:', error);
      process.exit(1);
    });

    process.on('unhandledRejection', (reason, promise) => {
      console.error('Unhandled Rejection:', reason);
    });
  }

  start() {
    this.app.listen(this.port, () => {
      console.log(`🌐 Server running on port ${this.port}`);
      console.log(`📊 Health check: http://localhost:${this.port}/health`);
    });
  }
}

// Start server
const server = new MediaProcurementServer();
server.start();

