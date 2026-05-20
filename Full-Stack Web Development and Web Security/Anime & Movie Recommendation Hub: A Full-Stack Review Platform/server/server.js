const express = require('express');
const dotenv = require('dotenv');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const connectDB = require('./config/db');

dotenv.config();

connectDB();

const app = express();

app.use(helmet()); 

const clientUrl = process.env.CLIENT_URL || 'http://localhost:5173';
const corsOptions = {
    origin: clientUrl,
    optionsSuccessStatus: 200 
};
app.use(cors(corsOptions)); 

app.use(express.json()); 
app.use(express.urlencoded({ extended: true })); 

app.use(morgan('dev'));

app.get('/', (req, res) => {
    res.json({ message: 'Movie Hub API is running!' });
});

app.use('/api/auth', require('./routes/auth.routes'));
app.use('/api/titles', require('./routes/title.routes'));
app.use('/api/reviews', require('./routes/review.routes'));


app.use((err, req, res, next) => {
    console.error(err.stack); 
    
    const status = err.statusCode || 500;
    const message = err.message || 'Internal Server Error';

    res.status(status).json({
        success: false,
        message: message,
    });
});

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
    console.log(`✅ Server is running on port ${PORT}. Client URL allowed: ${clientUrl}`);
});