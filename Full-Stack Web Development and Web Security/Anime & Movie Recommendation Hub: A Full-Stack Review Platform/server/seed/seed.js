require('dotenv').config();
const mongoose = require('mongoose');
const User = require('../models/User');
const Title = require('../models/Title');
const Review = require('../models/Review');
const bcrypt = require('bcryptjs');

const adminPassword = 'AdminPassword123'; 

const usersData = [
    { username: 'admin', email: 'admin@moviehub.com', passwordHash: adminPassword, role: 'admin' },
    { username: 'coquette_girl', email: 'user1@moviehub.com', passwordHash: 'userpassword1', role: 'user' },
];

const titlesData = [
    { 
        name: 'Barbie', 
        type: 'movie', 
        genres: ['Comedy', 'Fantasy'], 
        year: 2023, 
        synopsis: 'Barbie (2023) is a vibrant, clever film that blends comedy, social commentary, and heartfelt storytelling as Barbie ventures from her perfect pink world into the real one to discover her true identity.', 
        poster: 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fen.wikipedia.org%2Fwiki%2FBarbie_%2528film%2529&psig=AOvVaw3IRAdtZanS99Ry3BvlNLeo&ust=1765412565198000&source=images&cd=vfe&opi=89978449&ved=0CBEQjRxqFwoTCLjm17vgsZEDFQAAAAAdAAAAABAE' 
    },
    { 
        name: 'Mean Girls', 
        type: 'movie', 
        genres: ['Comedy', 'Teen'], 
        year: 2004, 
        synopsis: 'Cady Heron is a hit with The Plastics, the A-list girl clique at her new school, until she makes the mistake of falling for Aaron Samuels, the ex-boyfriend of alpha Plastic Regina George.', 
        poster: 'https://upload.wikimedia.org/wikipedia/en/a/ac/Mean_Girls_film_poster.png' 
    },
    { 
        name: 'Clueless', 
        type: 'movie', 
        genres: ['Comedy', 'Romance'], 
        year: 1995, 
        synopsis: 'Shallow, rich and socially successful Cher is at the top of her Beverly Hills high school pecking order.', 
        poster: 'https://upload.wikimedia.org/wikipedia/en/5/5a/Clueless_film_poster.png' 
    },
    { 
        name: 'Legally Blonde', 
        type: 'movie', 
        genres: ['Comedy', 'Romance'], 
        year: 2001, 
        synopsis: 'Elle Woods, a fashionable sorority queen, is dumped by her boyfriend. She decides to follow him to law school.', 
        poster: 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fencrypted-tbn3.gstatic.com%2Fimages%3Fq%3Dtbn%3AANd9GcT2oaQDVZiWUAZSw7MSZ8_4F4MBHKPXQi-xkLwXwz1ZhnbgChxx&psig=AOvVaw2VjJphow_-Xb3v2JBjQI0T&ust=1765412479003000&source=images&cd=vfe&opi=89978449&ved=0CBEQjRxqFwoTCPjgv5PgsZEDFQAAAAAdAAAAABAb' 
    },
    { 
        name: 'Marie Antoinette', 
        type: 'movie', 
        genres: ['Drama', 'History'], 
        year: 2006, 
        synopsis: 'The retelling of France\'s iconic but ill-fated queen, Marie Antoinette. From her betrothal and marriage to Louis XVI at 15 to her reign as queen at 19 and to the end of her reign as queen, and ultimately the fall of Versailles.', 
        poster: 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fencrypted-tbn3.gstatic.com%2Fimages%3Fq%3Dtbn%3AANd9GcT-UF4GhnfHR6cYm2cOINjHPPzXRGtg6zkAlaP1DGGccImH2y61&psig=AOvVaw1GeZ7atD-WL3_6aSTqrMze&ust=1765412184166000&source=images&cd=vfe&opi=89978449&ved=0CBEQjRxqFwoTCJjKhIbfsZEDFQAAAAAdAAAAABAE' 
    },
     { 
        name: 'Nana', 
        type: 'anime', 
        genres: ['Drama', 'Romance', 'Music'], 
        year: 2006, 
        synopsis: 'Two girls with the same name of Nana meet by chance on a train headed for Tokyo. One is a punk rocker, the other is a naive girl seeking romance.', 
        poster: 'https://cdn.myanimelist.net/images/anime/2/11232.jpg' 
    },
];

async function seedDB() {
    try {
        await mongoose.connect(process.env.MONGODB_URI);
        console.log('--- MongoDB Connected ---');

        console.log('Clearing existing data...');
        await Review.deleteMany({});
        await Title.deleteMany({});
        await User.deleteMany({});

        console.log('Seeding Users...');
        for (let user of usersData) {
            user.passwordHash = await bcrypt.hash(user.passwordHash, 10);
        }
        const createdUsers = await User.insertMany(usersData);
        const user1 = createdUsers.find(u => u.username === 'coquette_girl');

        console.log('Seeding Titles...');
        const createdTitles = await Title.insertMany(titlesData);
        
        console.log('Seeding Reviews...');
        const barbie = createdTitles.find(t => t.name === 'Barbie');
        
        const reviewsData = [
            { userId: user1._id, titleId: barbie._id, rating: 10, text: 'Literally me. This movie is everything.' },
        ];
        await Review.insertMany(reviewsData);

        console.log('✨ Database Seeding Complete! ✨');

    } catch (error) {
        console.error('Database Seeding Failed:', error.message);
    } finally {
        await mongoose.connection.close();
        console.log('--- MongoDB Connection Closed ---');
    }
}

seedDB();
