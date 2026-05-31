const { validationResult } = require('express-validator');
const { query } = require('../config/database');

const BASE_SELECT = `
  SELECT ph.*, n.libelle_fr AS nationalite, l.libelle_fr AS localite
  FROM personnes_physiques ph
  LEFT JOIN nationalites n ON n.id = ph.nationalite_id
  LEFT JOIN localites l ON l.id = ph.localite_id
`;

exports.list = async (req, res, next) => {
  try {
    const { page = 1, limit = 20, statut } = req.query;
    const offset = (page - 1) * limit;

    const result = await query(`${BASE_SELECT} ORDER BY ph.nom, ph.prenom LIMIT $1 OFFSET $2`, [limit, offset]);
    const count = await query('SELECT COUNT(*) FROM personnes_physiques');

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
       WHERE to_tsvector('simple', unaccent(ph.nom || ' ' || COALESCE(ph.prenom,''))) @@ plainto_tsquery('simple', unaccent($1))
          OR ph.nni ILIKE $2
       ORDER BY ph.nom LIMIT 50`,
      [q, `%${q}%`]
    );
    res.json({ success: true, data: result.rows });
  } catch (err) { next(err); }
};

exports.getById = async (req, res, next) => {
  try {
    const result = await query(`${BASE_SELECT} WHERE ph.id = $1`, [req.params.id]);
    if (!result.rows[0]) return res.status(404).json({ success: false, message: 'Personne physique non trouvée.' });
    res.json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.create = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) return res.status(422).json({ success: false, errors: errors.array() });

    const {
      nni, nom, prenom, nom_ar, prenom_ar, date_naissance, lieu_naissance,
      sexe, nationalite_id, adresse, adresse_ar, ville, localite_id,
      telephone, email, profession, situation_matrimoniale,
      nom_pere, nom_mere, num_passeport, num_carte_identite
    } = req.body;

    const result = await query(
      `INSERT INTO personnes_physiques
       (nni, nom, prenom, nom_ar, prenom_ar, date_naissance, lieu_naissance,
        sexe, nationalite_id, adresse, adresse_ar, ville, localite_id,
        telephone, email, profession, situation_matrimoniale,
        nom_pere, nom_mere, num_passeport, num_carte_identite, created_by)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22)
       RETURNING *`,
      [nni, nom, prenom, nom_ar, prenom_ar, date_naissance, lieu_naissance,
       sexe, nationalite_id, adresse, adresse_ar, ville, localite_id,
       telephone, email, profession, situation_matrimoniale,
       nom_pere, nom_mere, num_passeport, num_carte_identite, req.user.id]
    );

    res.status(201).json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.update = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) return res.status(422).json({ success: false, errors: errors.array() });

    const {
      nni, nom, prenom, nom_ar, prenom_ar, date_naissance, lieu_naissance,
      sexe, nationalite_id, adresse, adresse_ar, ville, localite_id,
      telephone, email, profession, situation_matrimoniale,
      nom_pere, nom_mere, num_passeport, num_carte_identite
    } = req.body;

    const result = await query(
      `UPDATE personnes_physiques SET
       nni=$1, nom=$2, prenom=$3, nom_ar=$4, prenom_ar=$5, date_naissance=$6,
       lieu_naissance=$7, sexe=$8, nationalite_id=$9, adresse=$10, adresse_ar=$11,
       ville=$12, localite_id=$13, telephone=$14, email=$15, profession=$16,
       situation_matrimoniale=$17, nom_pere=$18, nom_mere=$19, num_passeport=$20,
       num_carte_identite=$21, updated_at=NOW()
       WHERE id=$22 RETURNING *`,
      [nni, nom, prenom, nom_ar, prenom_ar, date_naissance, lieu_naissance,
       sexe, nationalite_id, adresse, adresse_ar, ville, localite_id,
       telephone, email, profession, situation_matrimoniale,
       nom_pere, nom_mere, num_passeport, num_carte_identite, req.params.id]
    );

    if (!result.rows[0]) return res.status(404).json({ success: false, message: 'Personne physique non trouvée.' });
    res.json({ success: true, data: result.rows[0] });
  } catch (err) { next(err); }
};

exports.remove = async (req, res, next) => {
  try {
    // Vérifier qu'aucun RA ne référence cette personne
    const check = await query('SELECT id FROM registre_analytique WHERE ph_id = $1 LIMIT 1', [req.params.id]);
    if (check.rows.length > 0) {
      return res.status(400).json({ success: false, message: 'Impossible de supprimer: cette personne est liée à un registre.' });
    }
    await query('DELETE FROM personnes_physiques WHERE id = $1', [req.params.id]);
    res.json({ success: true, message: 'Supprimé avec succès.' });
  } catch (err) { next(err); }
};
