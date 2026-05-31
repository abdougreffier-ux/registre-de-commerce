const router = require('express').Router();
const { body } = require('express-validator');
const ctrl = require('../controllers/modification.controller');
const auth = require('../middleware/auth.middleware');
const { requireRole } = require('../middleware/rbac.middleware');

router.use(auth);

router.get('/', ctrl.list);
router.get('/:id', ctrl.getById);
router.get('/:id/lignes', ctrl.getLignes);

router.post('/',
  [body('ra_id').isInt()],
  ctrl.create
);

router.put('/:id', ctrl.update);
router.delete('/:id', ctrl.remove);
router.patch('/:id/valider', requireRole('ADMIN','VALIDATEUR','GREFFIER_CHEF'), ctrl.valider);
router.patch('/:id/rejeter', requireRole('ADMIN','VALIDATEUR','GREFFIER_CHEF'), ctrl.rejeter);

module.exports = router;
