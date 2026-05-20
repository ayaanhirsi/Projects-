import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../services/api'; 

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(() => {
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const payload = token.split('.')[1];
                const decoded = JSON.parse(atob(payload));
                return { id: decoded.userId, role: decoded.role };
            } catch (e) {
                localStorage.removeItem('token');
                return null;
            }
        }
        return null;
    });

    const [isLoading, setIsLoading] = useState(false); 
    const login = async (email, password) => {
        setIsLoading(true);
        try {
            const response = await api.post('/auth/login', { email, password });
            
            const { token, user: userData } = response.data;
            localStorage.setItem('token', token);
            setUser(userData);
            return true;
        } catch (error) {
            throw error.response?.data?.message || 'Login failed.';
        } finally {
            setIsLoading(false);
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
    };

    const register = async (username, email, password) => {
        try {
            await api.post('/auth/register', { username, email, password });
            return true;
        } catch (error) {
            throw error.response?.data?.message || 'Registration failed.';
        }
    };

    const value = {
        user,
        isLoading,
        login,
        logout,
        register,
        isAuthenticated: !!user,
        isAdmin: user?.role === 'admin'
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
