import { useAuth } from '../contexts/AuthContext';

/**
 * Hook personalizado para manejar permisos de forma más cómoda
 */
export const usePermissions = () => {
  const { hasPermission, hasRole, hasAnyPermission } = useAuth();

  // Permisos específicos del chatbot
  const permissions = {
    // Plantillas
    canCreateTemplates: () => hasPermission('chatbot.templates.create'),
    canEditTemplates: () => hasPermission('chatbot.templates.edit'),
    canDeleteTemplates: () => hasPermission('chatbot.templates.delete'),
    canUseTemplates: () => hasPermission('chatbot.templates.use'),
    canManageTemplates: () => hasAnyPermission([
      'chatbot.templates.create',
      'chatbot.templates.edit',
      'chatbot.templates.delete'
    ]),

    // Contactos
    canViewContacts: () => hasPermission('chatbot.contacts.view'),
    canManageContacts: () => hasPermission('chatbot.contacts.manage'),

    // Mensajes
    canViewMessages: () => hasPermission('chatbot.messages.view'),
    canSendIndividualMessages: () => hasPermission('chatbot.messages.send.individual'),
    canSendMassiveMessages: () => hasPermission('chatbot.messages.send.massive'),
    canSendMessages: () => hasAnyPermission([
      'chatbot.messages.send.individual',
      'chatbot.messages.send.massive'
    ]),

    // Estadísticas
    canViewStatistics: () => hasPermission('chatbot.statistics.view'),
    canManageStatistics: () => hasPermission('chatbot.statistics.manage'),

    // Roles
    isSuperAdmin: () => hasRole('Super Administrador'),
    isAdmin: () => hasRole('Administrador'),
    isChatbotManager: () => hasRole('Chatbot Manager'),

    // Acceso a secciones completas
    canAccessTemplatesSection: () => hasAnyPermission([
      'chatbot.templates.create',
      'chatbot.templates.edit',
      'chatbot.templates.delete',
      'chatbot.templates.use'
    ]),
    canAccessContactsSection: () => hasAnyPermission([
      'chatbot.contacts.view',
      'chatbot.contacts.manage'
    ]),
    canAccessMessagesSection: () => hasAnyPermission([
      'chatbot.messages.view',
      'chatbot.messages.send.individual',
      'chatbot.messages.send.massive'
    ]),
    canAccessStatisticsSection: () => hasAnyPermission([
      'chatbot.statistics.view',
      'chatbot.statistics.manage'
    ])
  };

  return {
    ...permissions,
    // Funciones base
    hasPermission,
    hasRole,
    hasAnyPermission
  };
};
