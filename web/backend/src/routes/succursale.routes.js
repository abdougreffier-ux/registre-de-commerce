const router = require('express').Router();
const { body } = require('express-validator');
const ctrl = require('../controllers/succursale.controller');
const auth = require('../middleware/auth.middleware');

router.use(auth);

router.get('/', ctrl.list);
router.get('/:id', ctrl.getById);
router.get('/:id/gerants', ctrl.getGerants);

router.post('/',
  [body('denomination').notEmpty().withMessage('Dénomination requise')],
  ctrl.create
);

router.put('/:id', ctrl.update);
router.delete('/:id', ctrl.remove);

router.post('/:id/gerants', ctrl.addGerant);
router.delete('/:id/gerants/:gerId', ctrl.removeGerant);

module.exports = router;
