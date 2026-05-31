const logger = require('../config/logger');

const errorHandler = (err, req, res, next) => {
  logger.error(`${req.method} ${req.path} - ${err.message}`, { stack: err.stack });

  // Erreur de validation Express-validator (traitée dans les routes)
  if (err.type === 'validation') {
    return res.status(422).json({ success: false, errors: err.errors });
  }

  // Violation de contrainte PostgreSQL
  if (err.code === '23505') {
    return res.status(409).json({
      success: false,
      message: 'Enregistrement en double: une entrée avec ces données existe déjà.'
    });
  }
  if (err.code === '23503') {
    return res.status(400).json({
      success: false,
      message: 'Référence invalide: l\'enregistrement lié n\'existe pas.'
    });
  }
  if (err.code === '23502') {
    return res.status(400).json({
      success: false,
      message: 'Champ obligatoire manquant.'
    });
  }

  // Erreur multer (upload)
  if (err.name === 'MulterError') {
    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({
        success: false,
        message: `Fichier trop volumineux. Taille maximum: ${process.env.MAX_FILE_SIZE_MB || 10} Mo.`
      });
    }
    return res.status(400).json({ success: false, message: err.message });
  }

  // Erreur personnalisée
  if (err.statusCode) {
    return res.status(err.statusCode).json({ success: false, message: err.message });
  }

  // Erreur interne
  res.status(500).json({
    success: false,
    message: process.env.NODE_ENV === 'production'
      ? 'Erreur interne du serveur.'
      : err.message
  });
};

module.exports = errorHandler;
