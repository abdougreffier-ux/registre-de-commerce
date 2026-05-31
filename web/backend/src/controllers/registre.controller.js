const { validationResult } = require('express-validator');
const { query, withTransaction } = require('../config/database');

// ─────────────────────────────────────────────────────────────
// REGISTRE ANALYTIQUE
// ─────────────────────────────────────────────────────────────

exports.listRA = async (req, res, next) => {
  try {
    const { page = 1, limit = 20, statut, type_entite, q } = req.query;
    const offset = (page - 1) * limit;

    let where = 'WHERE 1=1';
    const params = [];
    if (statut) { params.push(statut); where += ` AND ra.statut = $${params.length}`; }
    if (type_entite) { params.push(type_entite); where += ` AND ra.type_entite = $${params.length}`; }
    if (q) {
      params.push(`%${q}%`);
      where += ` AND (ra.numero_ra ILIKE $${params.length} OR ra.numero_rc ILIKE $${params.length}
                 OR ph.nom ILIKE $${params.length} OR pm.denomination ILIKE $${params.length}
                 OR sc.denomination ILIKE $${params.length})`;
    }

    params.push(limit); params.push(offset);

    const result = await query(
      `SELECT ra.*, vra.denomination, vra.forme_juridique, vra.capital, vra.telephone, vra.localite
       FROM registre_analytique ra
       JOIN v_registre_analytique vra ON vra.id = ra.id
       LEFT JOIN personnes_physiques ph ON ra.ph_id = ph.id
       LEFT JOIN personnes_morales pm ON ra.pm_id = pm.id
       LEFT JOIN succursales sc ON ra.sc_id = sc.id
       ${where}
       ORDER BY ra.numero_ra DESC
       LIMIT $${params.length - 1} OFFSET $${params.length}`,
      params
    );

    const countResult = await query(
      `SELECT COUNT(*) FROM registre_analytique ra
       LEFT JOIN personnes_physiques ph ON ra.ph_id = ph.id
       LEFT JOIN personnes_morales pm ON ra.pm_id = pm.id
       LEFT JOIN succursales sc ON ra.sc_id = sc.id
       ${where}`,
      params.slice(0, -2)
    );

    res.json({
      success: true,
      data: result.rows,
      pagination: { total: parseInt(countResult.rows[0].count), page: parseInt(page), limit: parseInt(limit) }
    });
  } catch (err) { next(err); }
};

exports.getRA = async (req, res, next) => {
  try {
    const result = await query(
      `SELECT ra.*, vra.denomination, vra.forme_juridique, vra.capital, vra.telephone, vra.email, vra.localite, vra.nni
       FROM registre_analytique ra
       JOIN v_registre_analytique vra ON vra.id = ra.id
       WHERE ra.id = $1`,
      [req.params.id]
    );
    if (!result.rows[0]) return res.status(404).json({ success: false, message: 'RA non trouvé.' });
    res.json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.createRA = async (req, res, next) => {
  try {
    const { type_entite, ph_id, pm_id, sc_id, localite_id, observations } = req.body;

    const numero_ra = await query("SELECT generer_numero('RA', $1) AS num", [localite_id]);

    const result = await query(
      `INSERT INTO registre_analytique (numero_ra, type_entite, ph_id, pm_id, sc_id, localite_id, observations, created_by)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING *`,
      [numero_ra.rows[0].num, type_entite, ph_id, pm_id, sc_id, localite_id, observations, req.user.id]
    );
    res.status(201).json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.updateRA = async (req, res, next) => {
  try {
    const { numero_rc, date_immatriculation, observations } = req.body;
    const result = await query(
      `UPDATE registre_analytique SET numero_rc=$1, date_immatriculation=$2, observations=$3, updated_at=NOW()
       WHERE id=$4 RETURNING *`,
      [numero_rc, date_immatriculation, observations, req.params.id]
    );
    if (!result.rows[0]) return res.status(404).json({ success: false, message: 'RA non trouvé.' });
    res.json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.validerRA = async (req, res, next) => {
  try {
    const result = await query(
      `UPDATE registre_analytique SET statut='IMMATRICULE', validated_at=NOW(), validated_by=$1, updated_at=NOW()
       WHERE id=$2 AND statut='EN_COURS' RETURNING *`,
      [req.user.id, req.params.id]
    );
    if (!result.rows[0]) return res.status(400).json({ success: false, message: 'RA non trouvé ou déjà validé.' });
    res.json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.getRAGerants = async (req, res, next) => {
  try {
    const result = await query(
      `SELECT g.*, CASE g.type_gerant WHEN 'PH' THEN ph.nom||' '||COALESCE(ph.prenom,'') WHEN 'PM' THEN pm.denomination END AS nom_entite,
              f.libelle_fr AS fonction, n.libelle_fr AS nationalite
       FROM gerants g
       LEFT JOIN personnes_physiques ph ON ph.id = g.ph_id
       LEFT JOIN personnes_morales pm ON pm.id = g.pm_id
       LEFT JOIN fonctions f ON f.id = g.fonction_id
       LEFT JOIN nationalites n ON n.id = g.nationalite_id
       WHERE g.ra_id = $1 ORDER BY g.id`,
      [req.params.id]
    );
    res.json({ success: true, data: result.rows });
  } catch (err) { next(err); }
};

exports.getRAAssocies = async (req, res, next) => {
  try {
    const result = await query(
      `SELECT a.*, CASE a.type_associe WHEN 'PH' THEN ph.nom||' '||COALESCE(ph.prenom,'') WHEN 'PM' THEN pm.denomination END AS nom_entite,
              n.libelle_fr AS nationalite
       FROM associes a
       LEFT JOIN personnes_physiques ph ON ph.id = a.ph_id
       LEFT JOIN personnes_morales pm ON pm.id = a.pm_id
       LEFT JOIN nationalites n ON n.id = a.nationalite_id
       WHERE a.ra_id = $1 AND a.actif = TRUE ORDER BY a.id`,
      [req.params.id]
    );
    res.json({ success: true, data: result.rows });
  } catch (err) { next(err); }
};

exports.getRADocuments = async (req, res, next) => {
  try {
    const result = await query(
      `SELECT d.*, td.libelle_fr AS type_doc FROM documents d
       LEFT JOIN types_documents td ON td.id = d.type_doc_id
       WHERE d.ra_id = $1 ORDER BY d.created_at DESC`,
      [req.params.id]
    );
    res.json({ success: true, data: result.rows });
  } catch (err) { next(err); }
};

exports.getRAHistorique = async (req, res, next) => {
  try {
    const result = await query(
      `SELECT rc.*, u.nom||' '||COALESCE(u.prenom,'') AS agent
       FROM registre_chronologique rc
       LEFT JOIN utilisateurs u ON u.id = rc.created_by
       WHERE rc.ra_id = $1 ORDER BY rc.date_acte DESC, rc.id DESC`,
      [req.params.id]
    );
    res.json({ success: true, data: result.rows });
  } catch (err) { next(err); }
};

exports.exportRA = async (req, res, next) => {
  try {
    // Export simple en JSON (le frontend peut le transformer en Excel)
    const result = await query('SELECT * FROM v_registre_analytique ORDER BY numero_ra');
    res.json({ success: true, data: result.rows });
  } catch (err) { next(err); }
};

// ─────────────────────────────────────────────────────────────
// REGISTRE CHRONOLOGIQUE
// ─────────────────────────────────────────────────────────────

exports.listRChrono = async (req, res, next) => {
  try {
    const { page = 1, limit = 20, statut, date_debut, date_fin } = req.query;
    const offset = (page - 1) * limit;

    let where = 'WHERE 1=1';
    const params = [];
    if (statut) { params.push(statut); where += ` AND rc.statut = $${params.length}`; }
    if (date_debut) { params.push(date_debut); where += ` AND rc.date_acte >= $${params.length}`; }
    if (date_fin) { params.push(date_fin); where += ` AND rc.date_acte <= $${params.length}`; }

    params.push(limit); params.push(offset);

    const result = await query(
      `SELECT rc.*, vra.denomination, vra.numero_rc, vra.type_entite,
              u.nom||' '||COALESCE(u.prenom,'') AS agent
       FROM registre_chronologique rc
       LEFT JOIN v_registre_analytique vra ON vra.id = rc.ra_id
       LEFT JOIN utilisateurs u ON u.id = rc.created_by
       ${where}
       ORDER BY rc.date_acte DESC, rc.numero_chrono DESC
       LIMIT $${params.length - 1} OFFSET $${params.length}`,
      params
    );
    const countResult = await query(
      `SELECT COUNT(*) FROM registre_chronologique rc ${where}`,
      params.slice(0, -2)
    );

    res.json({
      success: true,
      data: result.rows,
      pagination: { total: parseInt(countResult.rows[0].count), page: parseInt(page), limit: parseInt(limit) }
    });
  } catch (err) { next(err); }
};

exports.getRChrono = async (req, res, next) => {
  try {
    const result = await query(
      `SELECT rc.*, vra.denomination, vra.numero_rc, vra.type_entite
       FROM registre_chronologique rc
       LEFT JOIN v_registre_analytique vra ON vra.id = rc.ra_id
       WHERE rc.id = $1`,
      [req.params.id]
    );
    if (!result.rows[0]) return res.status(404).json({ success: false, message: 'Non trouvé.' });
    res.json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.createRChrono = async (req, res, next) => {
  try {
    const { ra_id, type_acte, date_acte, description, description_ar } = req.body;

    const numero = await query("SELECT generer_numero('CHRONO') AS num");

    const result = await query(
      `INSERT INTO registre_chronologique (numero_chrono, ra_id, type_acte, date_acte, description, description_ar, created_by)
       VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING *`,
      [numero.rows[0].num, ra_id, type_acte, date_acte, description, description_ar, req.user.id]
    );
    res.status(201).json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.updateRChrono = async (req, res, next) => {
  try {
    const { date_acte, description, description_ar, observations } = req.body;
    const result = await query(
      `UPDATE registre_chronologique SET date_acte=$1, description=$2, description_ar=$3, observations=$4, updated_at=NOW()
       WHERE id=$5 AND statut='EN_INSTANCE' RETURNING *`,
      [date_acte, description, description_ar, observations, req.params.id]
    );
    if (!result.rows[0]) return res.status(400).json({ success: false, message: 'Non trouvé ou déjà validé.' });
    res.json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.validerRChrono = async (req, res, next) => {
  try {
    const result = await query(
      `UPDATE registre_chronologique SET statut='VALIDE', validated_at=NOW(), validated_by=$1, updated_at=NOW()
       WHERE id=$2 AND statut='EN_INSTANCE' RETURNING *`,
      [req.user.id, req.params.id]
    );
    if (!result.rows[0]) return res.status(400).json({ success: false, message: 'Non trouvé ou déjà validé.' });
    res.json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.exportRChrono = async (req, res, next) => {
  try {
    const { date_debut, date_fin } = req.query;
    const result = await query(
      `SELECT rc.*, vra.denomination, vra.numero_rc, vra.type_entite
       FROM registre_chronologique rc
       LEFT JOIN v_registre_analytique vra ON vra.id = rc.ra_id
       WHERE rc.date_acte BETWEEN $1 AND $2
       ORDER BY rc.date_acte, rc.numero_chrono`,
      [date_debut || '2000-01-01', date_fin || 'NOW()']
    );
    res.json({ success: true, data: result.rows });
  } catch (err) { next(err); }
};
