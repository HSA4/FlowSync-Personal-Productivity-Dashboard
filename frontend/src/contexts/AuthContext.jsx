/** Authentication Context Provider */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { apiService } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Check if user is already authenticated on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setIsLoading(false);
        return;
      }

      const response = await apiService.get('/api/v1/auth/me');
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (error) {
      // Token is invalid or expired
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithGoogle = useCallback(async () => {
    try {
      // Get Google OAuth URL
      const redirectUri = `${window.location.origin}/auth/callback`;
      const response = await apiService.get('/api/v1/auth/oauth/google', {
        params: { redirect_uri: redirectUri },
      });

      // Store the state for verification
      sessionStorage.setItem('oauth_state', response.data.state);
      sessionStorage.setItem('oauth_redirect', location.pathname);

      // Redirect to Google OAuth
      window.location.href = response.data.url;
    } catch (error) {
      console.error('Failed to initiate Google login:', error);
      throw new Error('Failed to connect to Google. Please try again.');
    }
  }, [location]);

  const handleOAuthCallback = useCallback(async (code, state) => {
    try {
      // Verify state
      const storedState = sessionStorage.getItem('oauth_state');
      if (state !== storedState) {
        throw new Error('Invalid OAuth state');
      }

      // Exchange code for tokens
      const redirectUri = `${window.location.origin}/auth/callback`;
      const response = await apiService.post('/api/v1/auth/oauth/google/callback', {
        code,
        redirect_uri: redirectUri,
      });

      // Store tokens
      localStorage.setItem('auth_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);

      // Get user info
      await checkAuth();

      // Redirect to original destination or home
      const redirectPath = sessionStorage.getItem('oauth_redirect') || '/';
      sessionStorage.removeItem('oauth_state');
      sessionStorage.removeItem('oauth_redirect');
      navigate(redirectPath, { replace: true });
    } catch (error) {
      console.error('OAuth callback failed:', error);
      throw new Error('Authentication failed. Please try again.');
    }
  }, [navigate]);

  const refreshToken = useCallback(async () => {
    try {
      const refreshTk = localStorage.getItem('refresh_token');
      if (!refreshTk) {
        throw new Error('No refresh token available');
      }

      const response = await apiService.post('/api/v1/auth/refresh', { refresh_token: refreshTk });

      localStorage.setItem('auth_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);

      return response.data.access_token;
    } catch (error) {
      // Refresh failed, logout user
      await logout();
      throw error;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (token) {
        await apiService.post('/api/v1/auth/logout');
      }
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      // Clear tokens and user state
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setIsAuthenticated(false);
      navigate('/');
    }
  }, [navigate]);

  const value = {
    user,
    isAuthenticated,
    isLoading,
    loginWithGoogle,
    handleOAuthCallback,
    refreshToken,
    logout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
