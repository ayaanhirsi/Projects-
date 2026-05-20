const mongoose = require('mongoose');

const titleSchema = new mongoose.Schema({
    name: {
        type: String,
        required: [true, 'Title name is required.'],
        trim: true,
    },
    type: {
        type: String,
        enum: ['movie', 'anime', 'tv'],
        required: [true, 'Title type is required.'],
    },
    genres: {
        type: [String], 
        required: true,
        default: [],
    },
    year: {
        type: Number,
        required: [true, 'Release year is required.'],
        min: [1888, 'Year must be after 1888 (first known film).'],
    },
    synopsis: {
        type: String,
        required: [true, 'Synopsis is required.'],
        maxlength: [2000, 'Synopsis cannot exceed 2000 characters.'],
    },
    poster: {
        type: String,
        default: 'placeholder.jpg',
    },

}, {
    timestamps: true
});

titleSchema.index({ name: 1 });        
titleSchema.index({ genres: 1 });     
titleSchema.index({ type: 1, year: -1 }); 

const Title = mongoose.model('Title', titleSchema);
module.exports = Title;