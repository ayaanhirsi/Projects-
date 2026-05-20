import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext.jsx';
import api from '../services/api';

const ProfilePage = () => {
    const { user, logout } = useAuth();
    const [profileData, setProfileData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchProfileData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.get('/auth/profile'); 
            setProfileData(response.data.user);
            
            
        } catch (err) {
            console.error('Profile fetch error:', err);
            setError('Failed to load profile data. Please try logging in again.');
            if (err.response && err.response.status === 401) {
                 logout();
            }
        } finally {
            setLoading(false);
        }
    }, [logout]);

    useEffect(() => {
        fetchProfileData();
    }, [fetchProfileData]);

    if (loading) return <h2 style={{textAlign: 'center', padding: '50px'}}>Loading Profile...</h2>;
    if (error) return <h2 style={{color: 'red', textAlign: 'center', padding: '50px'}}>{error}</h2>;
    if (!profileData) return <h2 style={{textAlign: 'center', padding: '50px'}}>No profile data found.</h2>;

    return (
        <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
            <h1 style={{borderBottom: '2px solid #007bff', paddingBottom: '10px'}}>Welcome, {profileData.username}!</h1>
            
            <div style={{ marginBottom: '30px' }}>
                <h2>Account Details</h2>
                <p><strong>Email:</strong> {profileData.email}</p>
                <p><strong>Role:</strong> <span style={{ fontWeight: 'bold', color: profileData.role === 'admin' ? 'red' : 'green' }}>{profileData.role.toUpperCase()}</span></p>
                <button onClick={logout} style={{ padding: '10px 15px', marginTop: '15px', backgroundColor: '#dc3545', color: 'white', border: 'none', cursor: 'pointer' }}>
                    Logout
                </button>
            </div>

            <h2 style={{ marginTop: '30px' }}>My Activity (Reviews & Watchlist)</h2>
            
            {/* TODO: Display user's reviews here */}
            <p>Your recent reviews will appear here.</p>

            {/* TODO: Display user's watchlist here */}
            <p>Your movie watchlist will appear here.</p>
        </div>
    );
};

export default ProfilePage;