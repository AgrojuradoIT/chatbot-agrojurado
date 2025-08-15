/**
 * Utilidades para manejo de autenticación en peticiones HTTP
 */

/**
 * Obtiene las cabeceras HTTP con autenticación
 * @param additionalHeaders Cabeceras adicionales a incluir
 * @param includeContentType Si incluir Content-Type (false para FormData)
 * @returns Headers con Authorization y cabeceras adicionales
 */
export const getAuthHeaders = (additionalHeaders: Record<string, string> = {}, includeContentType: boolean = true): HeadersInit => {
  const token = localStorage.getItem('access_token');
  
  const headers: Record<string, string> = {
    ...additionalHeaders,
  };
  
  if (includeContentType) {
    headers['Content-Type'] = 'application/json';
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};

/**
 * Verifica si el usuario está autenticado
 * @returns true si hay un token válido
 */
export const isAuthenticated = (): boolean => {
  return !!localStorage.getItem('access_token');
};

/**
 * Obtiene el token de acceso actual
 * @returns Token de acceso o null si no existe
 */
export const getAccessToken = (): string | null => {
  return localStorage.getItem('access_token');
};

/**
 * Construye la URL de logout OAuth
 * @param redirectUri URL a la que redirigir después del logout
 * @returns URL completa de logout OAuth
 */
export const buildLogoutUrl = (redirectUri?: string): string => {
  const oauthLogoutUrl = import.meta.env.VITE_OAUTH_LOGOUT_URL;
  const params = new URLSearchParams();
  
  if (redirectUri) {
    params.set('post_logout_redirect_uri', redirectUri);
  }
  
  return `${oauthLogoutUrl}?${params.toString()}`;
};

/**
 * Ejecuta el logout completo (backend + OAuth)
 * @param redirectUri URL a la que redirigir después del logout
 */
export const performLogout = async (redirectUri?: string): Promise<void> => {
  const token = getAccessToken();
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
  
  try {
    // 1. Cerrar sesión en el backend (revocar token)
    if (token) {
      await fetch(`${apiBaseUrl}/auth/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
    }
  } catch (error) {
    console.error('Error cerrando sesión en backend:', error);
  } finally {
    // 2. Limpiar datos locales
    localStorage.removeItem('access_token');
    
    // 3. Redirigir al logout OAuth
    const logoutUrl = buildLogoutUrl(redirectUri || window.location.origin);
    window.location.href = logoutUrl;
  }
};
