const router = require('express').Router();
const ctrl = require('../controllers/rapport.controller');
const auth = require('../middleware/auth.middleware');

router.use(auth);

// Attestation d'immatriculation
router.get('/attestation-immatriculation/:ra_id', ctrl.attestationImmatriculation);
// Extrait du Registre du Commerce
router.get('/extrait-rc/:ra_id', ctrl.extraitRC);
// Registre chronologique PDF
router.get('/registre-chronologique', ctrl.registreChronologiquePDF);
// Registre analytique PDF
router.get('/registre-analytique', ctrl.registreAnalytiquePDF);
// Statistiques
router.get('/statistiques', ctrl.statistiques);
// Export Excel demandes
router.get('/export-demandes', ctrl.exportDemandes);
// Tableau de bord
router.get('/tableau-de-bord', ctrl.tableauDeBord);

module.exports = router;
