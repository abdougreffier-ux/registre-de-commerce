const router = require('express').Router();
const { body } = require('express-validator');
const ctrl = require('../controllers/utilisateur.controller');
const auth = require('../middleware/auth.middleware');
const { requireRole } = require('../middleware/rbac.middleware');

router.use(auth);

router.get('/', requireRole('ADMIN'), ctrl.list);
router.get('/roles', ctrl.listRoles);
router.get('/:id', requireRole('ADMIN'), ctrl.getById);

router.post('/', requireRole('ADMIN'),
  [
    body('nom').notEmpty(),
    body('login').notEmpty(),
    body('password').isLength({ min: 8 }),
    body('role_id').isInt()
  ],
  ctrl.create
);

router.put('/:id', requireRole('ADMIN'), ctrl.update);
router.patch('/:id/activer', requireRole('ADMIN'), ctrl.activer);
router.patch('/:id/desactiver', requireRole('ADMIN'), ctrl.desactiver);
router.patch('/:id/reset-password', requireRole('ADMIN'), ctrl.resetPassword);

module.exports = router;
