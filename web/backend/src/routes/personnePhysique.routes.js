const router = require('express').Router();
const { body, query } = require('express-validator');
const ctrl = require('../controllers/personnePhysique.controller');
const auth = require('../middleware/auth.middleware');

router.use(auth);

router.get('/', ctrl.list);
router.get('/search', ctrl.search);
router.get('/:id', ctrl.getById);

router.post('/',
  [
    body('nom').notEmpty().withMessage('Nom requis'),
    body('nationalite_id').isInt().withMessage('Nationalité requise')
  ],
  ctrl.create
);

router.put('/:id',
  [body('nom').notEmpty().withMessage('Nom requis')],
  ctrl.update
);

router.delete('/:id', ctrl.remove);

module.exports = router;
