// override:true garantit que .env écrase toute variable système (ex. PORT=3000 héritée de l'OS)
require('dotenv').config({ override: true });
const app = require('./app');
const { pool } = require('./config/database');
const logger = require('./config/logger');

const PORT = process.env.PORT || 5000;

// Vérification connexion DB au démarrage
pool.query('SELECT NOW()', (err) => {
  if (err) {
    logger.error('Erreur connexion PostgreSQL:', err.message);
    process.exit(1);
  }
  logger.info('PostgreSQL connecté');

  app.listen(PORT, () => {
    logger.info(`Serveur démarré sur le port ${PORT} [${process.env.NODE_ENV}]`);
  });
});

process.on('unhandledRejection', (err) => {
  logger.error('Unhandled Rejection:', err);
  process.exit(1);
});
