const { validationResult } = require('express-validator');
const { query, withTransaction } = require('../config/database');

const BASE_SELECT = `
  SELECT pm.*, fj.libelle_fr AS forme_juridique, fj.code AS fj_code, l.libelle_fr AS localite
  FROM personnes_morales pm
  LEFT JOIN formes_juridiques fj ON fj.id = pm.forme_juridique_id
  LEFT JOIN localites l ON l.id = pm.localite_id
`;

exports.list = async (req, res, next) => {
  try {
    const { page = 1, limit = 20 } = req.query;
    const offset = (page - 1) * limit;
    const result = await query(`${BASE_SELECT} ORDER BY pm.denomination LIMIT $1 OFFSET $2`, [limit, offset]);
    const count = await query('SELECT COUNT(*) FROM personnes_morales');
    res.json({
      success: true,
      data: result.rows,
      pagination: { total: parseInt(count.rows[0].count), page: parseInt(page), limit: parseInt(limit) }
    });
  } catch (err) { next(err); }
};

exports.search = async (req, res, next) => {
  try {
    const { q } = req.query;
    if (!q) return res.json({ success: true, data: [] });
    const result = await query(
      `${BASE_SELECT}
       WHERE pm.denomination ILIKE $1 OR pm.sigle ILIKE $1
       ORDER BY pm.denomination LIMIT 50`,
      [`%${q}%`]
    );
    res.json({ success: true, data: result.rows });
  } catch (err) { next(err); }
};

exports.getById = async (req, res, next) => {
  try {
    const result = await query(`${BASE_SELECT} WHERE pm.id = $1`, [req.params.id]);
    if (!result.rows[0]) return res.status(404).json({ success: false, message: 'Personne morale non trouvée.' });
    res.json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.create = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) return res.status(422).json({ success: false, errors: errors.array() });

    const {
      denomination, denomination_ar, sigle, forme_juridique_id, capital_social,
      devise_capital, duree_societe, date_constitution, date_ag,
      siege_social, siege_social_ar, ville, localite_id,
      telephone, fax, email, site_web, bp
    } = req.body;

    const result = await query(
      `INSERT INTO personnes_morales
       (denomination, denomination_ar, sigle, forme_juridique_id, capital_social,
        devise_capital, duree_societe, date_constitution, date_ag,
        siege_social, siege_social_ar, ville, localite_id,
        telephone, fax, email, site_web, bp, created_by)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19)
       RETURNING *`,
      [denomination, denomination_ar, sigle, forme_juridique_id, capital_social,
       devise_capital, duree_societe, date_constitution, date_ag,
       siege_social, siege_social_ar, ville, localite_id,
       telephone, fax, email, site_web, bp, req.user.id]
    );
    res.status(201).json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.update = async (req, res, next) => {
  try {
    const {
      denomination, denomination_ar, sigle, forme_juridique_id, capital_social,
      devise_capital, duree_societe, date_constitution, date_ag,
      siege_social, siege_social_ar, ville, localite_id,
      telephone, fax, email, site_web, bp
    } = req.body;

    const result = await query(
      `UPDATE personnes_morales SET
       denomination=$1, denomination_ar=$2, sigle=$3, forme_juridique_id=$4, capital_social=$5,
       devise_capital=$6, duree_societe=$7, date_constitution=$8, date_ag=$9,
       siege_social=$10, siege_social_ar=$11, ville=$12, localite_id=$13,
       telephone=$14, fax=$15, email=$16, site_web=$17, bp=$18, updated_at=NOW()
       WHERE id=$19 RETURNING *`,
      [denomination, denomination_ar, sigle, forme_juridique_id, capital_social,
       devise_capital, duree_societe, date_constitution, date_ag,
       siege_social, siege_social_ar, ville, localite_id,
       telephone, fax, email, site_web, bp, req.params.id]
    );
    if (!result.rows[0]) return res.status(404).json({ success: false, message: 'Non trouvé.' });
    res.json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.remove = async (req, res, next) => {
  try {
    const check = await query('SELECT id FROM registre_analytique WHERE pm_id = $1 LIMIT 1', [req.params.id]);
    if (check.rows.length > 0) {
      return res.status(400).json({ success: false, message: 'Impossible de supprimer: liée à un registre.' });
    }
    await query('DELETE FROM personnes_morales WHERE id = $1', [req.params.id]);
    res.json({ success: true, message: 'Supprimé avec succès.' });
  } catch (err) { next(err); }
};

exports.getAssocies = async (req, res, next) => {
  try {
    const result = await query(
      `SELECT a.*,
              CASE a.type_associe WHEN 'PH' THEN ph.nom||' '||COALESCE(ph.prenom,'') WHEN 'PM' THEN pm.denomination END AS nom_entite,
              n.libelle_fr AS nationalite
       FROM associes a
       JOIN registre_analytique ra ON ra.id = a.ra_id AND ra.pm_id = $1
       LEFT JOIN personnes_physiques ph ON ph.id = a.ph_id
       LEFT JOIN personnes_morales pm ON pm.id = a.pm_id
       LEFT JOIN nationalites n ON n.id = a.nationalite_id
       WHERE a.actif = TRUE
       ORDER BY a.id`,
      [req.params.id]
    );
    res.json({ success: true, data: result.rows });
  } catch (err) { next(err); }
};

exports.getGerants = async (req, res, next) => {
  try {
    const result = await query(
      `SELECT g.*,
              CASE g.type_gerant WHEN 'PH' THEN ph.nom||' '||COALESCE(ph.prenom,'') WHEN 'PM' THEN pm.denomination END AS nom_entite,
              f.libelle_fr AS fonction, n.libelle_fr AS nationalite
       FROM gerants g
       JOIN registre_analytique ra ON ra.id = g.ra_id AND ra.pm_id = $1
       LEFT JOIN personnes_physiques ph ON ph.id = g.ph_id
       LEFT JOIN personnes_morales pm ON pm.id = g.pm_id
       LEFT JOIN fonctions f ON f.id = g.fonction_id
       LEFT JOIN nationalites n ON n.id = g.nationalite_id
       WHERE g.actif = TRUE
       ORDER BY g.id`,
      [req.params.id]
    );
    res.json({ success: true, data: result.rows });
  } catch (err) { next(err); }
};

exports.addAssocie = async (req, res, next) => {
  try {
    const { type_associe, ph_id, pm_id, nom_associe, nationalite_id, nombre_parts, valeur_parts, pourcentage, type_part, date_entree } = req.body;
    // Récupérer le ra_id lié à la PM
    const ra = await query('SELECT id FROM registre_analytique WHERE pm_id = $1 AND statut != $2 LIMIT 1', [req.params.id, 'RADIE']);
    if (!ra.rows[0]) return res.status(404).json({ success: false, message: 'Aucun registre analytique actif trouvé.' });

    const result = await query(
      `INSERT INTO associes (ra_id, type_associe, ph_id, pm_id, nom_associe, nationalite_id, nombre_parts, valeur_parts, pourcentage, type_part, date_entree)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11) RETURNING *`,
      [ra.rows[0].id, type_associe, ph_id, pm_id, nom_associe, nationalite_id, nombre_parts, valeur_parts, pourcentage, type_part, date_entree]
    );
    res.status(201).json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.updateAssocie = async (req, res, next) => {
  try {
    const { nombre_parts, valeur_parts, pourcentage, type_part, date_sortie, actif } = req.body;
    const result = await query(
      `UPDATE associes SET nombre_parts=$1, valeur_parts=$2, pourcentage=$3, type_part=$4, date_sortie=$5, actif=$6, updated_at=NOW()
       WHERE id=$7 RETURNING *`,
      [nombre_parts, valeur_parts, pourcentage, type_part, date_sortie, actif, req.params.assId]
    );
    res.json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.removeAssocie = async (req, res, next) => {
  try {
    await query('UPDATE associes SET actif=FALSE, date_sortie=CURRENT_DATE WHERE id=$1', [req.params.assId]);
    res.json({ success: true, message: 'Associé retiré.' });
  } catch (err) { next(err); }
};

exports.addGerant = async (req, res, next) => {
  try {
    const { type_gerant, ph_id, pm_id, nom_gerant, nationalite_id, fonction_id, date_debut, pouvoirs } = req.body;
    const ra = await query('SELECT id FROM registre_analytique WHERE pm_id = $1 AND statut != $2 LIMIT 1', [req.params.id, 'RADIE']);
    if (!ra.rows[0]) return res.status(404).json({ success: false, message: 'Aucun registre analytique actif.' });

    const result = await query(
      `INSERT INTO gerants (ra_id, type_gerant, ph_id, pm_id, nom_gerant, nationalite_id, fonction_id, date_debut, pouvoirs)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9) RETURNING *`,
      [ra.rows[0].id, type_gerant, ph_id, pm_id, nom_gerant, nationalite_id, fonction_id, date_debut, pouvoirs]
    );
    res.status(201).json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.updateGerant = async (req, res, next) => {
  try {
    const { fonction_id, date_debut, date_fin, pouvoirs, actif } = req.body;
    const result = await query(
      `UPDATE gerants SET fonction_id=$1, date_debut=$2, date_fin=$3, pouvoirs=$4, actif=$5, updated_at=NOW()
       WHERE id=$6 RETURNING *`,
      [fonction_id, date_debut, date_fin, pouvoirs, actif, req.params.gerId]
    );
    res.json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.removeGerant = async (req, res, next) => {
  try {
    await query('UPDATE gerants SET actif=FALSE, date_fin=CURRENT_DATE WHERE id=$1', [req.params.gerId]);
    res.json({ success: true, message: 'Gérant retiré.' });
  } catch (err) { next(err); }
};
