import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext.jsx'; 

import LoginPage from './pages/LoginPage.jsx';
import RegisterPage from './pages/RegisterPage.jsx';
import HomePage from './pages/HomePage.jsx'; 
import BrowsePage from './pages/BrowsePage.jsx'; 
import TitleDetailsPage from './pages/TitleDetailsPage.jsx'; 
import ProfilePage from './pages/ProfilePage.jsx'; 
import Navigation from './components/Navigation.jsx'; 


const ProtectedRoute = ({ children, requiredRole }) => {
    const { isAuthenticated, user, isLoading } = useAuth();

    if (isLoading) {
        return <div className="loading-screen" style={{textAlign: 'center', padding: '50px'}}>Loading application...</div>;
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }
    
    if (requiredRole && user.role !== requiredRole) {
        return <Navigate to="/" replace />; 
    }

    return children;
};


function App() {
    return (
        <>
            <Navigation /> {/* Persistent header/nav bar */}
            <div className="container" style={{padding: '20px'}}>
                <Routes>
                    {/* Public Routes */}
                    <Route path="/" element={<HomePage />} />
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/register" element={<RegisterPage />} />
                    <Route path="/browse" element={<BrowsePage />} />
                    <Route path="/titles/:id" element={<TitleDetailsPage />} />

                    {/* Protected Routes (Require a logged-in user) */}
                    <Route 
                        path="/profile" 
                        element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} 
                    />
                    
                    {/* Admin Protected Route Example (Requires 'admin' role) */}
                    <Route
                        path="/titles/new"
                        element={<ProtectedRoute requiredRole="admin"><h1>Admin: Create New Title</h1></ProtectedRoute>}
                    />
                    
                    {/* Catch-all route for paths not found */}
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </div>
        </>
    );
}

export default App;