/** Authentication Context Provider */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
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
  const [isLoading, setIsLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [error, setError] = useState(null);

  // Check if user is already authenticated on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setIsAuthenticated(false);
        setUser(null);
        setIsLoading(false);
        return;
      }

      const response = await apiService.get('/api/v1/auth/me');

      if (response.data) {
        setUser(response.data);
        setIsAuthenticated(true);
      } else {
        setIsAuthenticated(false);
        setUser(null);
      }
    } catch (error) {
      console.error('Auth check failed:', error);

      // Token is invalid or expired
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');

      setUser(null);
      setIsAuthenticated(false);
      setError('Authentication failed');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loginWithGoogle = useCallback(async () => {
    try {
      const redirectUri = `${window.location.origin}/auth/callback`;
      const response = await apiService.get('/api/v1/auth/oauth/google', {
        params: { redirect_uri: redirectUri },
      });

      // Store state for verification
      sessionStorage.setItem('oauth_state', response.data.state);
      sessionStorage.setItem('oauth_redirect', window.location.pathname);

      // Redirect to Google OAuth
      window.location.href = response.data.url;
    } catch (error) {
      console.error('Failed to initiate Google login:', error);
      setError('Failed to connect to Google. Please try again.');
    }
  }, []);

  const handleOAuthCallback = useCallback(async (code, state) => {
    try {
      const storedState = sessionStorage.getItem('oauth_state');
      if (state !== storedState) {
        throw new Error('Invalid OAuth state');
      }

      const redirectUri = `${window.location.origin}/auth/callback`;
      const response = await apiService.post('/api/v1/auth/oauth/google/callback', {
        code,
        redirect_uri: redirectUri,
      });

      localStorage.setItem('auth_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);

      // Clear session storage but keep redirect path for component to handle
      const redirectPath = sessionStorage.getItem('oauth_redirect') || '/';
      sessionStorage.removeItem('oauth_state');
      sessionStorage.removeItem('oauth_redirect');

      // Return success - calling component handles navigation
      return { success: true, redirectPath };
    } catch (error) {
      console.error('OAuth callback failed:', error);
      setError('Authentication failed. Please try again.');
      return { success: false, error };
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
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setIsAuthenticated(false);
      // Calling component handles navigation
    }
  }, []);

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
      await logout();
      throw error;
    }
  }, [logout]);

  const value = {
    user,
    isAuthenticated,
    isLoading,
    error,
    loginWithGoogle,
    handleOAuthCallback,
    refreshToken,
    logout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
