const router = require('express').Router();
const ctrl = require('../controllers/recherche.controller');
const auth = require('../middleware/auth.middleware');

router.use(auth);

// Recherche globale (nom, dénomination, NNI, N° RC)
router.get('/', ctrl.rechercher);
// Recherche par NNI
router.get('/nni/:nni', ctrl.rechercherParNNI);
// Recherche par numéro RC
router.get('/rc/:numero_rc', ctrl.rechercherParNumRC);
// Vérification certificat négatif (nom commercial disponible)
router.get('/certificat-negatif', ctrl.verifierNomCommercial);

module.exports = router;
