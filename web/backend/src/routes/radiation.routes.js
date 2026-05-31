const router = require('express').Router();
const { body } = require('express-validator');
const ctrl = require('../controllers/radiation.controller');
const auth = require('../middleware/auth.middleware');
const { requireRole } = require('../middleware/rbac.middleware');

router.use(auth);

router.get('/', ctrl.list);
router.get('/:id', ctrl.getById);

router.post('/',
  [
    body('ra_id').isInt(),
    body('motif').notEmpty()
  ],
  ctrl.create
);

router.put('/:id', ctrl.update);
router.patch('/:id/valider', requireRole('ADMIN','VALIDATEUR','GREFFIER_CHEF'), ctrl.valider);
router.patch('/:id/rejeter', requireRole('ADMIN','VALIDATEUR','GREFFIER_CHEF'), ctrl.rejeter);

module.exports = router;
