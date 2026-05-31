const router = require('express').Router();
const { body } = require('express-validator');
const ctrl = require('../controllers/personneMorale.controller');
const auth = require('../middleware/auth.middleware');

router.use(auth);

router.get('/', ctrl.list);
router.get('/search', ctrl.search);
router.get('/:id', ctrl.getById);
router.get('/:id/associes', ctrl.getAssocies);
router.get('/:id/gerants', ctrl.getGerants);

router.post('/',
  [
    body('denomination').notEmpty().withMessage('Dénomination requise'),
    body('forme_juridique_id').isInt().withMessage('Forme juridique requise')
  ],
  ctrl.create
);

router.put('/:id',
  [body('denomination').notEmpty()],
  ctrl.update
);

router.delete('/:id', ctrl.remove);

// Associés
router.post('/:id/associes', ctrl.addAssocie);
router.put('/:id/associes/:assId', ctrl.updateAssocie);
router.delete('/:id/associes/:assId', ctrl.removeAssocie);

// Gérants
router.post('/:id/gerants', ctrl.addGerant);
router.put('/:id/gerants/:gerId', ctrl.updateGerant);
router.delete('/:id/gerants/:gerId', ctrl.removeGerant);

module.exports = router;
