const { Pool } = require('pg');
const logger = require('./logger');

const pool = new Pool({
  host:     process.env.DB_HOST || 'localhost',
  port:     parseInt(process.env.DB_PORT) || 5432,
  database: process.env.DB_NAME || 'registre_commerce',
  user:     process.env.DB_USER || 'rc_user',
  password: process.env.DB_PASSWORD || 'rc_password_secret',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000
});

pool.on('error', (err) => {
  logger.error('Erreur inattendue du pool PostgreSQL:', err);
});

/**
 * Exécute une requête SQL avec paramètres
 */
const query = (text, params) => pool.query(text, params);

/**
 * Acquiert un client pour une transaction
 */
const getClient = () => pool.connect();

/**
 * Exécute une transaction sécurisée
 * @param {Function} callback - async fn(client) => result
 */
const withTransaction = async (callback) => {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const result = await callback(client);
    await client.query('COMMIT');
    return result;
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }
};

module.exports = { pool, query, getClient, withTransaction };
