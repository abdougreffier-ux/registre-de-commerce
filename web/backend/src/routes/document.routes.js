const router = require('express').Router();
const ctrl = require('../controllers/document.controller');
const auth = require('../middleware/auth.middleware');
const upload = require('../middleware/upload.middleware');

router.use(auth);

router.get('/', ctrl.list);
router.get('/:id', ctrl.getById);
router.get('/:id/download', ctrl.download);

router.post('/', upload.single('fichier'), ctrl.upload);
router.delete('/:id', ctrl.remove);

module.exports = router;
