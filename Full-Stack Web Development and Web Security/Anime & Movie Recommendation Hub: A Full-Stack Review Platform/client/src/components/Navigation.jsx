import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';

import logoImg from '../assets/logo.jpg'; 

const Navigation = () => {
    const { isAuthenticated, logout, user } = useAuth();
    
    return (
        <nav className="navbar">
            <div className="nav-content">
                <Link to="/" className="logo-link">
                    {/* Display  image instead of text */}
                    <img src={logoImg} alt="Yanies Movie Recs" className="logo-img" />
                </Link>
                <div className="nav-links">
                    <Link to="/browse">Films</Link>
                    {isAuthenticated ? (
                        <>
                            <Link to="/profile">Profile ({user?.username})</Link>
                            {user?.role === 'admin' && <Link to="/titles/new" style={{color: '#00e054'}}>+ Add Film</Link>}
                            <button onClick={logout} className="secondary" style={{marginLeft: '15px', padding: '5px 10px'}}>Log Out</button>
                        </>
                    ) : (
                        <>
                            <Link to="/login">Sign In</Link>
                            <Link to="/register" className="btn" style={{color: 'white', marginLeft: '10px'}}>Create Account</Link>
                        </>
                    )}
                </div>
            </div>
        </nav>
    );
};

export default Navigation;
