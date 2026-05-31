const router = require('express').Router();
const { body } = require('express-validator');
const ctrl = require('../controllers/parametrage.controller');
const auth = require('../middleware/auth.middleware');
const { requireRole } = require('../middleware/rbac.middleware');

router.use(auth);

// Nationalités
router.get('/nationalites', ctrl.listNationalites);
router.post('/nationalites', requireRole('ADMIN'), [body('code').notEmpty(), body('libelle_fr').notEmpty()], ctrl.createNationalite);
router.put('/nationalites/:id', requireRole('ADMIN'), ctrl.updateNationalite);
router.delete('/nationalites/:id', requireRole('ADMIN'), ctrl.deleteNationalite);

// Formes Juridiques
router.get('/formes-juridiques', ctrl.listFormesJuridiques);
router.post('/formes-juridiques', requireRole('ADMIN'), ctrl.createFormeJuridique);
router.put('/formes-juridiques/:id', requireRole('ADMIN'), ctrl.updateFormeJuridique);
router.delete('/formes-juridiques/:id', requireRole('ADMIN'), ctrl.deleteFormeJuridique);

// Domaines d'activités
router.get('/domaines-activites', ctrl.listDomainesActivites);
router.post('/domaines-activites', requireRole('ADMIN'), ctrl.createDomaineActivite);
router.put('/domaines-activites/:id', requireRole('ADMIN'), ctrl.updateDomaineActivite);
router.delete('/domaines-activites/:id', requireRole('ADMIN'), ctrl.deleteDomaineActivite);

// Fonctions
router.get('/fonctions', ctrl.listFonctions);
router.post('/fonctions', requireRole('ADMIN'), ctrl.createFonction);
router.put('/fonctions/:id', requireRole('ADMIN'), ctrl.updateFonction);
router.delete('/fonctions/:id', requireRole('ADMIN'), ctrl.deleteFonction);

// Types de documents
router.get('/types-documents', ctrl.listTypesDocuments);
router.post('/types-documents', requireRole('ADMIN'), ctrl.createTypeDocument);
router.put('/types-documents/:id', requireRole('ADMIN'), ctrl.updateTypeDocument);

// Types de demandes
router.get('/types-demandes', ctrl.listTypesDemandes);
router.post('/types-demandes', requireRole('ADMIN'), ctrl.createTypeDemande);
router.put('/types-demandes/:id', requireRole('ADMIN'), ctrl.updateTypeDemande);

// Localités
router.get('/localites', ctrl.listLocalites);
router.post('/localites', requireRole('ADMIN'), ctrl.createLocalite);
router.put('/localites/:id', requireRole('ADMIN'), ctrl.updateLocalite);

// Tarifs
router.get('/tarifs', ctrl.listTarifs);
router.post('/tarifs', requireRole('ADMIN'), ctrl.createTarif);
router.put('/tarifs/:id', requireRole('ADMIN'), ctrl.updateTarif);

module.exports = router;
