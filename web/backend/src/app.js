const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const path = require('path');

const routes = require('./routes');
const errorHandler = require('./middleware/errorHandler.middleware');
const logger = require('./config/logger');

const app = express();

// Sécurité
app.use(helmet());

// CORS
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 200,
  message: { success: false, message: 'Trop de requêtes, veuillez réessayer plus tard.' }
});
app.use('/api', limiter);

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Compression
app.use(compression());

// Logs HTTP
app.use(morgan('combined', {
  stream: { write: (msg) => logger.http(msg.trim()) }
}));

// Fichiers statiques (documents uploadés)
app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

// Routes API
app.use('/api', routes);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Servir le build React (production) — doit être après toutes les routes API
const frontendBuildPath = path.join(__dirname, '../../frontend/build');
app.use(express.static(frontendBuildPath));

// SPA fallback : toutes les routes non-API renvoient index.html
// Permet le rechargement direct et la navigation vers /modifications/nouvelle etc.
app.get('*', (req, res) => {
  const indexFile = path.join(frontendBuildPath, 'index.html');
  res.sendFile(indexFile, (err) => {
    if (err) {
      // Si le build n'existe pas encore, retourner 404 JSON
      res.status(404).json({ success: false, message: 'Route non trouvée' });
    }
  });
});

// Gestionnaire d'erreurs global
app.use(errorHandler);

module.exports = app;
