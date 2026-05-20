const express = require('express');
const router = express.Router();
const titleController = require('../controllers/title.controller');

router.get('/', titleController.getAllTitles);

router.get('/:id', titleController.getTitleById);

module.exports = router;
