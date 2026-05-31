const router = require('express').Router();
const { body } = require('express-validator');
const ctrl = require('../controllers/auth.controller');
const auth = require('../middleware/auth.middleware');

router.post('/login',
  [
    body('login').notEmpty().withMessage('Login requis'),
    body('password').notEmpty().withMessage('Mot de passe requis')
  ],
  ctrl.login
);

router.post('/refresh-token', ctrl.refreshToken);

router.post('/logout', auth, ctrl.logout);

router.get('/me', auth, ctrl.getMe);

router.post('/change-password', auth,
  [
    body('ancien_mdp').notEmpty(),
    body('nouveau_mdp').isLength({ min: 8 }).withMessage('Minimum 8 caractères')
  ],
  ctrl.changePassword
);

module.exports = router;
