const router = require('express').Router();
const ctrl = require('../controllers/registre.controller');
const auth = require('../middleware/auth.middleware');
const { requireRole } = require('../middleware/rbac.middleware');

router.use(auth);

// Registre Analytique
router.get('/analytique', ctrl.listRA);
router.get('/analytique/export', ctrl.exportRA);
router.get('/analytique/:id', ctrl.getRA);
router.post('/analytique', ctrl.createRA);
router.put('/analytique/:id', ctrl.updateRA);
router.patch('/analytique/:id/valider', requireRole('ADMIN','VALIDATEUR','GREFFIER_CHEF'), ctrl.validerRA);
router.get('/analytique/:id/gerants', ctrl.getRAGerants);
router.get('/analytique/:id/associes', ctrl.getRAAssocies);
router.get('/analytique/:id/documents', ctrl.getRADocuments);
router.get('/analytique/:id/historique', ctrl.getRAHistorique);

// Registre Chronologique
router.get('/chronologique', ctrl.listRChrono);
router.get('/chronologique/export', ctrl.exportRChrono);
router.get('/chronologique/:id', ctrl.getRChrono);
router.post('/chronologique', ctrl.createRChrono);
router.put('/chronologique/:id', ctrl.updateRChrono);
router.patch('/chronologique/:id/valider', requireRole('ADMIN','VALIDATEUR','GREFFIER_CHEF'), ctrl.validerRChrono);

module.exports = router;
