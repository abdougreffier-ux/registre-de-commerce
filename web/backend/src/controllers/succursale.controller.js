const { validationResult } = require('express-validator');
const { query } = require('../config/database');

exports.list = async (req, res, next) => {
  try {
    const { page = 1, limit = 20 } = req.query;
    const offset = (page - 1) * limit;
    const result = await query(
      `SELECT sc.*, l.libelle_fr AS localite, pm.denomination AS pm_mere
       FROM succursales sc
       LEFT JOIN localites l ON l.id = sc.localite_id
       LEFT JOIN personnes_morales pm ON pm.id = sc.pm_mere_id
       ORDER BY sc.denomination LIMIT $1 OFFSET $2`,
      [limit, offset]
    );
    const count = await query('SELECT COUNT(*) FROM succursales');
    res.json({ success: true, data: result.rows, pagination: { total: parseInt(count.rows[0].count), page: parseInt(page), limit: parseInt(limit) } });
  } catch (err) { next(err); }
};

exports.getById = async (req, res, next) => {
  try {
    const result = await query(
      `SELECT sc.*, l.libelle_fr AS localite, pm.denomination AS pm_mere
       FROM succursales sc
       LEFT JOIN localites l ON l.id = sc.localite_id
       LEFT JOIN personnes_morales pm ON pm.id = sc.pm_mere_id
       WHERE sc.id = $1`,
      [req.params.id]
    );
    if (!result.rows[0]) return res.status(404).json({ success: false, message: 'Succursale non trouvée.' });
    res.json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.create = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) return res.status(422).json({ success: false, errors: errors.array() });

    const { pm_mere_id, denomination, denomination_ar, pays_origine, capital_affecte, devise, siege_social, ville, localite_id, telephone, email } = req.body;

    const result = await query(
      `INSERT INTO succursales (pm_mere_id, denomination, denomination_ar, pays_origine, capital_affecte, devise, siege_social, ville, localite_id, telephone, email, created_by)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) RETURNING *`,
      [pm_mere_id, denomination, denomination_ar, pays_origine, capital_affecte, devise, siege_social, ville, localite_id, telephone, email, req.user.id]
    );
    res.status(201).json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.update = async (req, res, next) => {
  try {
    const { denomination, denomination_ar, pays_origine, capital_affecte, devise, siege_social, ville, localite_id, telephone, email } = req.body;
    const result = await query(
      `UPDATE succursales SET denomination=$1, denomination_ar=$2, pays_origine=$3, capital_affecte=$4, devise=$5,
       siege_social=$6, ville=$7, localite_id=$8, telephone=$9, email=$10, updated_at=NOW()
       WHERE id=$11 RETURNING *`,
      [denomination, denomination_ar, pays_origine, capital_affecte, devise, siege_social, ville, localite_id, telephone, email, req.params.id]
    );
    if (!result.rows[0]) return res.status(404).json({ success: false, message: 'Non trouvé.' });
    res.json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.remove = async (req, res, next) => {
  try {
    const check = await query('SELECT id FROM registre_analytique WHERE sc_id = $1 LIMIT 1', [req.params.id]);
    if (check.rows.length > 0) return res.status(400).json({ success: false, message: 'Liée à un registre.' });
    await query('DELETE FROM succursales WHERE id = $1', [req.params.id]);
    res.json({ success: true, message: 'Supprimé.' });
  } catch (err) { next(err); }
};

exports.getGerants = async (req, res, next) => {
  try {
    const result = await query(
      `SELECT g.*, CASE g.type_gerant WHEN 'PH' THEN ph.nom||' '||COALESCE(ph.prenom,'') END AS nom_entite, f.libelle_fr AS fonction
       FROM gerants g
       JOIN registre_analytique ra ON ra.id = g.ra_id AND ra.sc_id = $1
       LEFT JOIN personnes_physiques ph ON ph.id = g.ph_id
       LEFT JOIN fonctions f ON f.id = g.fonction_id
       WHERE g.actif = TRUE`,
      [req.params.id]
    );
    res.json({ success: true, data: result.rows });
  } catch (err) { next(err); }
};

exports.addGerant = async (req, res, next) => {
  try {
    const { type_gerant, ph_id, nom_gerant, nationalite_id, fonction_id, date_debut, pouvoirs } = req.body;
    const ra = await query('SELECT id FROM registre_analytique WHERE sc_id = $1 AND statut != $2 LIMIT 1', [req.params.id, 'RADIE']);
    if (!ra.rows[0]) return res.status(404).json({ success: false, message: 'Aucun RA actif.' });
    const result = await query(
      `INSERT INTO gerants (ra_id, type_gerant, ph_id, nom_gerant, nationalite_id, fonction_id, date_debut, pouvoirs)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING *`,
      [ra.rows[0].id, type_gerant, ph_id, nom_gerant, nationalite_id, fonction_id, date_debut, pouvoirs]
    );
    res.status(201).json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.removeGerant = async (req, res, next) => {
  try {
    await query('UPDATE gerants SET actif=FALSE, date_fin=CURRENT_DATE WHERE id=$1', [req.params.gerId]);
    res.json({ success: true, message: 'Gérant retiré.' });
  } catch (err) { next(err); }
};
