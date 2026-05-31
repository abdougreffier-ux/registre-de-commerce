const router = require('express').Router();
const { body } = require('express-validator');
const ctrl = require('../controllers/demande.controller');
const auth = require('../middleware/auth.middleware');
const { requireRole } = require('../middleware/rbac.middleware');

router.use(auth);

router.get('/', ctrl.list);
router.get('/stats', ctrl.stats);
router.get('/:id', ctrl.getById);
router.get('/:id/lignes', ctrl.getLignes);

router.post('/',
  [
    body('type_demande_id').isInt(),
    body('type_entite').isIn(['PH', 'PM', 'SC'])
  ],
  ctrl.create
);

router.put('/:id', ctrl.update);
router.delete('/:id', ctrl.remove);

// Changement de statut
router.patch('/:id/soumettre',  ctrl.soumettre);
router.patch('/:id/valider',    requireRole('ADMIN','VALIDATEUR','GREFFIER_CHEF'), ctrl.valider);
router.patch('/:id/rejeter',    requireRole('ADMIN','VALIDATEUR','GREFFIER_CHEF'), ctrl.rejeter);
router.patch('/:id/annuler',    ctrl.annuler);

// Lignes (pièces du dossier)
router.put('/:id/lignes', ctrl.updateLignes);

module.exports = router;
