const mongoose = require('mongoose');

const reviewSchema = new mongoose.Schema({
    userId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User', 
        required: true,
    },
    titleId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Title', 
        required: true,
    },
    rating: {
        type: Number,
        required: [true, 'Rating is required.'],
        min: [1, 'Rating must be between 1 and 10.'],
        max: [10, 'Rating must be between 1 and 10.'],
    },
    text: {
        type: String,
        trim: true,
        maxlength: [1000, 'Review text cannot exceed 1000 characters.'],
    },
}, {
    timestamps: true
});

reviewSchema.index({ userId: 1, titleId: 1 }, { unique: true });

const Review = mongoose.model('Review', reviewSchema);
module.exports = Review;
