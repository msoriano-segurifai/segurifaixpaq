import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI, userAPI } from '../services/api';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  phone_number?: string;
  paq_wallet_id?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isPAQUser: boolean;
  login: (phone: string, password: string) => Promise<void>;
  loginWithPAQToken: (paqToken: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPAQUser, setIsPAQUser] = useState(false);

  const fetchUser = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setIsLoading(false);
        return;
      }

      const response = await userAPI.getProfile();
      setUser(response.data);

      // Detect if user is a PAQ user based on paq_wallet_id
      const isPAQ = !!response.data.paq_wallet_id || localStorage.getItem('is_paq_user') === 'true';
      setIsPAQUser(isPAQ);
    } catch (error) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('paq_token');
      localStorage.removeItem('is_paq_user');
      setUser(null);
      setIsPAQUser(false);
    } finally {
      setIsLoading(false);
    }
  };

  const checkPAQToken = async () => {
    // Check URL params for PAQ token
    const urlParams = new URLSearchParams(window.location.search);
    const paqToken = urlParams.get('paq_token') || localStorage.getItem('paq_token');

    if (paqToken && !localStorage.getItem('access_token')) {
      try {
        await loginWithPAQToken(paqToken);
      } catch (error) {
        console.error('PAQ token authentication failed:', error);
        setIsLoading(false);
      }
    } else {
      await fetchUser();
    }
  };

  useEffect(() => {
    checkPAQToken();
  }, []);

  const login = async (phone: string, password: string) => {
    const response = await authAPI.login(phone, password);
    const { access, refresh } = response.data;

    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    localStorage.removeItem('paq_token');
    localStorage.setItem('is_paq_user', 'false');

    await fetchUser();
  };

  const loginWithPAQToken = async (paqToken: string) => {
    setIsLoading(true);
    try {
      // Authenticate with PAQ SSO
      const response = await authAPI.paqSSO(paqToken);
      const { access, refresh, user: userData } = response.data;

      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      localStorage.setItem('paq_token', paqToken);
      localStorage.setItem('is_paq_user', 'true');

      setUser(userData);
      setIsPAQUser(true);
    } catch (error) {
      console.error('PAQ SSO failed:', error);
      // Try quick login with wallet ID if available
      const walletId = localStorage.getItem('paq_wallet_id');
      if (walletId) {
        try {
          const response = await authAPI.paqQuickLogin(walletId);
          const { access, refresh, user: userData } = response.data;

          localStorage.setItem('access_token', access);
          localStorage.setItem('refresh_token', refresh);
          localStorage.setItem('is_paq_user', 'true');

          setUser(userData);
          setIsPAQUser(true);
        } catch (quickLoginError) {
          throw error; // Throw original error if quick login also fails
        }
      } else {
        throw error;
      }
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('paq_token');
    localStorage.removeItem('is_paq_user');
    localStorage.removeItem('paq_wallet_id');
    setUser(null);
    setIsPAQUser(false);
    window.location.href = '/login';
  };

  const refreshUser = async () => {
    await fetchUser();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        isPAQUser,
        login,
        loginWithPAQToken,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
