import React from 'react';
import { Link } from 'react-router-dom';

const HomePage = () => {
    return (
        <div style={{ padding: '40px', textAlign: 'center' }}>
            <h1>🎥 Welcome to the Movie Hub!</h1>
            <p>Your centralized place for rating movies and anime.</p>
            <p style={{ marginTop: '20px' }}>
                <Link to="/browse" style={{ 
                    padding: '10px 20px', 
                    backgroundColor: '#007bff', 
                    color: 'white', 
                    textDecoration: 'none', 
                    borderRadius: '5px' 
                }}>
                    Start Browsing Now
                </Link>
            </p>
        </div>
    );
};

export default HomePage;