import React from 'react';
import { usePermissions } from '../hooks/usePermissions';

interface ProtectedComponentProps {
  children: React.ReactNode;
  permission?: string;
  permissions?: string[];
  role?: string;
  roles?: string[];
  requireAll?: boolean; // Si true, requiere TODOS los permisos/roles, si false requiere AL MENOS UNO
  fallback?: React.ReactNode; // Qué mostrar si no tiene permisos
  hideWhenNoAccess?: boolean; // Si true, no muestra nada, si false muestra fallback
}

/**
 * Componente para proteger elementos basado en permisos y roles
 * 
 * Ejemplos de uso:
 * 
 * // Mostrar solo si tiene un permiso específico
 * <ProtectedComponent permission="chatbot.templates.create">
 *   <button>Crear Plantilla</button>
 * </ProtectedComponent>
 * 
 * // Mostrar solo si tiene al menos uno de varios permisos
 * <ProtectedComponent permissions={["chatbot.messages.send.individual", "chatbot.messages.send.massive"]}>
 *   <button>Enviar Mensaje</button>
 * </ProtectedComponent>
 * 
 * // Mostrar mensaje personalizado si no tiene acceso
 * <ProtectedComponent permission="chatbot.statistics.view" fallback={<p>No tienes acceso a estadísticas</p>}>
 *   <StatisticsPanel />
 * </ProtectedComponent>
 * 
 * // Ocultar completamente si no tiene acceso
 * <ProtectedComponent permission="chatbot.contacts.manage" hideWhenNoAccess={true}>
 *   <button>Eliminar Contacto</button>
 * </ProtectedComponent>
 */
export const ProtectedComponent: React.FC<ProtectedComponentProps> = ({
  children,
  permission,
  permissions = [],
  role,
  roles = [],
  requireAll = false,
  fallback = null,
  hideWhenNoAccess = false
}) => {
  const { hasPermission, hasRole } = usePermissions();

  // Verificar permisos
  let hasRequiredPermissions = true;

  if (permission) {
    hasRequiredPermissions = hasPermission(permission);
  } else if (permissions.length > 0) {
    if (requireAll) {
      // Requiere TODOS los permisos
      hasRequiredPermissions = permissions.every(p => hasPermission(p));
    } else {
      // Requiere AL MENOS UNO de los permisos
      hasRequiredPermissions = permissions.some(p => hasPermission(p));
    }
  }

  // Verificar roles
  let hasRequiredRoles = true;

  if (role) {
    hasRequiredRoles = hasRole(role);
  } else if (roles.length > 0) {
    if (requireAll) {
      // Requiere TODOS los roles
      hasRequiredRoles = roles.every(r => hasRole(r));
    } else {
      // Requiere AL MENOS UNO de los roles
      hasRequiredRoles = roles.some(r => hasRole(r));
    }
  }

  // El usuario debe cumplir tanto los permisos como los roles
  const hasAccess = hasRequiredPermissions && hasRequiredRoles;

  if (hasAccess) {
    return <>{children}</>;
  }

  // No tiene acceso
  if (hideWhenNoAccess) {
    return null;
  }

  return <>{fallback}</>;
};

// Componentes especializados para casos comunes
export const TemplateProtected: React.FC<{ children: React.ReactNode; action: 'create' | 'edit' | 'delete' | 'use'; fallback?: React.ReactNode }> = ({
  children,
  action,
  fallback = null
}) => (
  <ProtectedComponent permission={`chatbot.templates.${action}`} fallback={fallback}>
    {children}
  </ProtectedComponent>
);

export const MessageProtected: React.FC<{ children: React.ReactNode; action: 'view' | 'send.individual' | 'send.massive'; fallback?: React.ReactNode }> = ({
  children,
  action,
  fallback = null
}) => (
  <ProtectedComponent permission={`chatbot.messages.${action}`} fallback={fallback}>
    {children}
  </ProtectedComponent>
);

export const ContactProtected: React.FC<{ children: React.ReactNode; action: 'view' | 'manage'; fallback?: React.ReactNode }> = ({
  children,
  action,
  fallback = null
}) => (
  <ProtectedComponent permission={`chatbot.contacts.${action}`} fallback={fallback}>
    {children}
  </ProtectedComponent>
);

export const StatisticsProtected: React.FC<{ children: React.ReactNode; action: 'view' | 'manage'; fallback?: React.ReactNode }> = ({
  children,
  action,
  fallback = null
}) => (
  <ProtectedComponent permission={`chatbot.statistics.${action}`} fallback={fallback}>
    {children}
  </ProtectedComponent>
);
