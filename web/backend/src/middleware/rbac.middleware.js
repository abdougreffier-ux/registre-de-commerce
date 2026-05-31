const { query } = require('../config/database');

/**
 * Vérifie qu'un utilisateur possède l'une des permissions requises.
 * @param  {...string} permissions - codes de permission (ex: 'SAISIE_DEMANDE', 'VALIDER_DEMANDE')
 */
const requirePermission = (...permissions) => async (req, res, next) => {
  try {
    const { role_id } = req.user;

    const result = await query(
      `SELECT p.code FROM permissions p
       JOIN roles_permissions rp ON rp.permission_id = p.id
       WHERE rp.role_id = $1`,
      [role_id]
    );

    const userPermissions = result.rows.map((r) => r.code);
    const hasPermission = permissions.some((p) => userPermissions.includes(p));

    if (!hasPermission) {
      return res.status(403).json({
        success: false,
        message: 'Accès refusé. Permission insuffisante.'
      });
    }
    next();
  } catch (err) {
    next(err);
  }
};

/**
 * Vérifie qu'un utilisateur appartient à l'un des rôles requis.
 * @param  {...string} roles - codes de rôle (ex: 'ADMIN', 'GREFFIER', 'VALIDATEUR')
 */
const requireRole = (...roles) => (req, res, next) => {
  if (!roles.includes(req.user.role_code)) {
    return res.status(403).json({
      success: false,
      message: 'Accès refusé. Rôle insuffisant.'
    });
  }
  next();
};

module.exports = { requirePermission, requireRole };
