const Review = require('../models/Review');
const Title = require('../models/Title');

exports.getReviewsByTitle = async (req, res) => {
    try {
        const reviews = await Review.find({ titleId: req.params.titleId })
            .populate('userId', 'username')
            .sort({ createdAt: -1 });

        res.status(200).json({ success: true, data: reviews });
    } catch (error) {
        console.error(error);
        res.status(500).json({ success: false, message: 'Server Error' });
    }
};

exports.createReview = async (req, res) => {
    try {
        const { titleId, rating, text } = req.body;

        const existingReview = await Review.findOne({ userId: req.user.userId, titleId });
        if (existingReview) {
            return res.status(400).json({ success: false, message: 'You have already reviewed this title.' });
        }

        const review = await Review.create({
            userId: req.user.userId,
            titleId,
            rating,
            text
        });

        res.status(201).json({ success: true, data: review });
    } catch (error) {
        res.status(400).json({ success: false, message: error.message });
    }
};