const express = require('express');
const router = express.Router();

router.use('/auth',            require('./auth.routes'));
router.use('/utilisateurs',    require('./utilisateur.routes'));
router.use('/parametrage',     require('./parametrage.routes'));
router.use('/personnes-physiques', require('./personnePhysique.routes'));
router.use('/personnes-morales',   require('./personneMorale.routes'));
router.use('/succursales',     require('./succursale.routes'));
router.use('/demandes',        require('./demande.routes'));
router.use('/depots',          require('./depot.routes'));
router.use('/registres',       require('./registre.routes'));
router.use('/modifications',   require('./modification.routes'));
router.use('/radiations',      require('./radiation.routes'));
router.use('/cessions',        require('./cession.routes'));
router.use('/documents',       require('./document.routes'));
router.use('/rapports',        require('./rapport.routes'));
router.use('/recherche',       require('./recherche.routes'));

module.exports = router;
