const express = require('express');
const router = express.Router();
const reviewController = require('../controllers/review.controller');
const { isAuthenticated } = require('../middleware/auth.middleware');

router.get('/title/:titleId', reviewController.getReviewsByTitle);

router.post('/', isAuthenticated, reviewController.createReview);

module.exports = router;
