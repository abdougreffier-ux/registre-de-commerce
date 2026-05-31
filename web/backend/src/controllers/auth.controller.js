const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { validationResult } = require('express-validator');
const { query } = require('../config/database');
const logger = require('../config/logger');

const generateToken = (user) =>
  jwt.sign(
    { id: user.id, login: user.login, role_id: user.role_id, role_code: user.role_code },
    process.env.JWT_SECRET,
    { expiresIn: process.env.JWT_EXPIRES_IN || '8h' }
  );

exports.login = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) return res.status(422).json({ success: false, errors: errors.array() });

    const { login, password } = req.body;

    const result = await query(
      `SELECT u.*, r.code AS role_code, r.libelle AS role_libelle
       FROM utilisateurs u
       LEFT JOIN roles r ON r.id = u.role_id
       WHERE u.login = $1 AND u.actif = TRUE`,
      [login]
    );

    const user = result.rows[0];
    if (!user) {
      return res.status(401).json({ success: false, message: 'Login ou mot de passe incorrect.' });
    }

    const valid = await bcrypt.compare(password, user.password_hash);
    if (!valid) {
      return res.status(401).json({ success: false, message: 'Login ou mot de passe incorrect.' });
    }

    // Mettre à jour la dernière connexion
    await query('UPDATE utilisateurs SET derniere_cnx = NOW() WHERE id = $1', [user.id]);

    const token = generateToken(user);

    logger.info(`Connexion: ${user.login} [${user.role_code}]`);

    res.json({
      success: true,
      token,
      user: {
        id: user.id,
        nom: user.nom,
        prenom: user.prenom,
        login: user.login,
        email: user.email,
        role: { code: user.role_code, libelle: user.role_libelle }
      }
    });
  } catch (err) {
    next(err);
  }
};

exports.refreshToken = async (req, res, next) => {
  try {
    const { token } = req.body;
    if (!token) return res.status(400).json({ success: false, message: 'Token requis.' });

    const decoded = jwt.verify(token, process.env.JWT_SECRET, { ignoreExpiration: true });
    const result = await query(
      'SELECT u.*, r.code AS role_code FROM utilisateurs u LEFT JOIN roles r ON r.id = u.role_id WHERE u.id = $1 AND u.actif = TRUE',
      [decoded.id]
    );

    if (!result.rows[0]) return res.status(401).json({ success: false, message: 'Utilisateur non trouvé.' });

    const newToken = generateToken(result.rows[0]);
    res.json({ success: true, token: newToken });
  } catch (err) {
    next(err);
  }
};

exports.logout = (req, res) => {
  // Côté serveur on n'invalide pas le token JWT (stateless).
  // Le client doit supprimer le token.
  res.json({ success: true, message: 'Déconnexion réussie.' });
};

exports.getMe = async (req, res, next) => {
  try {
    const result = await query(
      `SELECT u.id, u.nom, u.prenom, u.login, u.email, u.telephone, u.matricule,
              r.code AS role_code, r.libelle AS role_libelle,
              p.libelle_fr AS poste, l.libelle_fr AS localite
       FROM utilisateurs u
       LEFT JOIN roles r ON r.id = u.role_id
       LEFT JOIN postes p ON p.id = u.poste_id
       LEFT JOIN localites l ON l.id = u.localite_id
       WHERE u.id = $1`,
      [req.user.id]
    );
    if (!result.rows[0]) return res.status(404).json({ success: false, message: 'Utilisateur non trouvé.' });
    res.json({ success: true, data: result.rows[0] });
  } catch (err) {
    next(err);
  }
};

exports.changePassword = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) return res.status(422).json({ success: false, errors: errors.array() });

    const { ancien_mdp, nouveau_mdp } = req.body;

    const result = await query('SELECT password_hash FROM utilisateurs WHERE id = $1', [req.user.id]);
    const user = result.rows[0];

    const valid = await bcrypt.compare(ancien_mdp, user.password_hash);
    if (!valid) return res.status(400).json({ success: false, message: 'Ancien mot de passe incorrect.' });

    const hash = await bcrypt.hash(nouveau_mdp, 12);
    await query('UPDATE utilisateurs SET password_hash = $1, updated_at = NOW() WHERE id = $2', [hash, req.user.id]);

    res.json({ success: true, message: 'Mot de passe modifié avec succès.' });
  } catch (err) {
    next(err);
  }
};
