import React, { createContext, useContext, useState, useEffect } from 'react';
import { performLogout } from '../utils/auth';
import type { ReactNode } from 'react';

interface User {
  id: number;
  name: string;
  email: string;
  sector: string;
  roles: string[];
  permissions: string[];
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isLoggingOut: boolean;
  login: () => void;
  logout: () => void;
  handleCallback: (code: string) => Promise<boolean>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  // URLs de configuración OAuth
  const OAUTH_CLIENT_ID = import.meta.env.VITE_OAUTH_CLIENT_ID;
  const OAUTH_REDIRECT_URI = import.meta.env.VITE_OAUTH_REDIRECT_URI;
  const OAUTH_AUTH_URL = import.meta.env.VITE_OAUTH_AUTH_URL;
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

  // Verificar si hay token guardado al cargar la aplicación
  useEffect(() => {
    const checkAuthStatus = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });
          
          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
          } else {
            // Token inválido, limpiar
            localStorage.removeItem('access_token');
          }
        } catch (error) {
          console.error('Error verificando autenticación:', error);
          localStorage.removeItem('access_token');
        }
      }
      setIsLoading(false);
    };

    checkAuthStatus();
  }, []);

  // Función para iniciar el login OAuth
  const login = () => {
    const params = new URLSearchParams({
      client_id: OAUTH_CLIENT_ID,
      redirect_uri: OAUTH_REDIRECT_URI,
      response_type: 'code',
      scope: '',
    });

    const authUrl = `${OAUTH_AUTH_URL}?${params.toString()}`;
    window.location.href = authUrl;
  };

  // Función para manejar el callback OAuth
  const handleCallback = async (code: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      
      const response = await fetch(`${API_BASE_URL}/auth/callback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        setUser(data.user);
        return true;
      } else {
        console.error('Error en callback OAuth');
        return false;
      }
    } catch (error) {
      console.error('Error procesando callback:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // Función para cerrar sesión
  const logout = async () => {
    try {
      setIsLoggingOut(true);
      // Usar la función de utilidad para logout completo
      await performLogout(window.location.origin);
    } catch (error) {
      console.error('Error en logout:', error);
      // Si falla, al menos limpiar datos locales y redirigir
      localStorage.removeItem('access_token');
      setUser(null);
      window.location.href = '/';
    } finally {
      setIsLoggingOut(false);
    }
  };

  // Funciones para verificar permisos y roles
  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    // Super Administrador tiene todos los permisos
    if (user.roles?.includes('Super Administrador')) return true;
    return user.permissions?.includes(permission) || false;
  };

  const hasRole = (role: string): boolean => {
    if (!user) return false;
    return user.roles?.includes(role) || false;
  };

  const hasAnyPermission = (permissions: string[]): boolean => {
    if (!user) return false;
    // Super Administrador tiene todos los permisos
    if (user.roles?.includes('Super Administrador')) return true;
    return permissions.some(permission => user.permissions?.includes(permission));
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    isLoggingOut,
    login,
    logout,
    handleCallback,
    hasPermission,
    hasRole,
    hasAnyPermission,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth debe ser usado dentro de un AuthProvider');
  }
  return context;
};
