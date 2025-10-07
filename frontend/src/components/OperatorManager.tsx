import React, { useState, useEffect } from 'react';
import { operatorService } from '../services/operatorService';
import type { Operator, OperatorCreateRequest } from '../services/operatorService';
import OperatorImport from './OperatorImport';
import SearchInput from './SearchInput';
import LoadingButton from './LoadingButton';
import '../styles/ContactImport.css';
import '../styles/ContactManager.css';
import '../styles/SearchInput.css';
import '../styles/OperatorManager.css';
import { useNotifications } from './NotificationContainer';
import { useConfirm } from '../hooks/useConfirm';
import ConfirmDialog from './ConfirmDialog';
import { ProtectedComponent } from './ProtectedComponent';
import { useOperators } from '../contexts/OperatorContext';

interface OperatorManagerProps {
  onOperatorUpdate?: () => void;
}

const OperatorManager: React.FC<OperatorManagerProps> = ({ 
  onOperatorUpdate
}) => {
  const { showNotification } = useNotifications();
  const { confirm, confirmDialog } = useConfirm();
  const { operators, loading, error, refreshOperators } = useOperators();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [editingOperator, setEditingOperator] = useState<Operator | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [newOperator, setNewOperator] = useState<OperatorCreateRequest>({
    cedula: '',
    name: '',
    expedition_date: ''
  });
  
  const [searchTerm, setSearchTerm] = useState('');

  // Nota: el contexto ya mantiene cache y escucha WebSocket. Aquí solo filtramos por búsqueda local.
  useEffect(() => {
    // Si se requiere búsqueda en backend, podríamos llamar refreshOperators con search, pero por ahora es filtro local.
  }, [searchTerm]);

  // Filtrar empleados basado en el término de búsqueda
  const filteredEmployees = operators.filter(operator => {
    if (!searchTerm.trim()) return true;
    
    const searchLower = searchTerm.toLowerCase().trim();
    const nameMatch = operator.name.toLowerCase().includes(searchLower);
    const cedulaMatch = operator.cedula.includes(searchTerm);
    
    return nameMatch || cedulaMatch;
  });

  const handleCreateOperator = async () => {
    if (!newOperator.cedula || !newOperator.name || !newOperator.expedition_date) {
      showNotification({
        type: 'warning',
        title: 'Campos Incompletos',
        message: 'Por favor completa todos los campos requeridos.'
      });
      return;
    }

    // Validar cédula
    const cleanCedula = newOperator.cedula.replace(/\D/g, '');
    if (cleanCedula.length < 6 || cleanCedula.length > 10) {
      showNotification({
        type: 'warning',
        title: 'Cédula Inválida',
        message: 'La cédula debe tener entre 6 y 10 dígitos.'
      });
      return;
    }

    setIsCreating(true);
    try {
      await operatorService.createOperator({
        ...newOperator,
        cedula: cleanCedula
      });
      
      setNewOperator({ cedula: '', name: '', expedition_date: '' });
      setShowCreateModal(false);
      // El WebSocket operator_updated refrescará el contexto automáticamente
      // Como respaldo opcional, podemos forzar refresh
      refreshOperators().catch(() => {});
      onOperatorUpdate?.();
      
      showNotification({
        type: 'success',
        title: 'Empleado Creado',
        message: `El empleado "${newOperator.name}" se ha creado exitosamente.`
      });
    } catch (err: any) {
      showNotification({
        type: 'error',
        title: 'Error al Crear Empleado',
        message: err.message || 'Error al crear el empleado'
      });
    } finally {
      setIsCreating(false);
    }
  };

  const handleUpdateOperator = async () => {
    if (!editingOperator) return;

    setIsUpdating(true);
    try {
      await operatorService.updateOperator(editingOperator.cedula, {
        name: editingOperator.name,
        expedition_date: editingOperator.expedition_date,
        is_active: editingOperator.is_active
      });
      
      setShowEditModal(false);
      setEditingOperator(null);
      refreshOperators().catch(() => {});
      onOperatorUpdate?.();
      
      showNotification({
        type: 'success',
        title: 'Empleado Actualizado',
        message: `El empleado "${editingOperator.name}" se ha actualizado exitosamente.`
      });
    } catch (err: any) {
      showNotification({
        type: 'error',
        title: 'Error al Actualizar Empleado',
        message: err.message || 'Error al actualizar el empleado'
      });
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteOperator = async (cedula: string) => {
    const confirmed = await confirm({
      title: 'Eliminar Empleado',
      message: '¿Estás seguro de que quieres eliminar este empleado? Esta acción no se puede deshacer.',
      confirmText: 'Eliminar',
      cancelText: 'Cancelar',
      type: 'delete'
    });

    if (!confirmed) {
      return;
    }

    try {
      await operatorService.deleteOperator(cedula);
      refreshOperators().catch(() => {});
      onOperatorUpdate?.();
      
      showNotification({
        type: 'success',
        title: 'Empleado Eliminado',
        message: 'El empleado se ha eliminado exitosamente.'
      });
    } catch (err: any) {
      showNotification({
        type: 'error',
        title: 'Error al Eliminar Empleado',
        message: err.message || 'Error al eliminar el empleado'
      });
    }
  };

  const openEditModal = (operator: Operator) => {
    setEditingOperator({ ...operator });
    setShowEditModal(true);
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('es-ES');
    } catch {
      return dateString;
    }
  };

  const formatCedula = (cedula: string) => {
    // Formatear cédula con puntos para mejor legibilidad
    return cedula.replace(/(\d{1,3})(?=(\d{3})+(?!\d))/g, '$1.');
  };

  return (
    <div className="contact-manager-panel">
      <div className="contacts-header">
        <h3>Empleados</h3>
        <div className="contacts-actions">
          <ProtectedComponent permissions={['chatbot.operators.manage']}>
            <button 
              className="import-contact-btn"
              onClick={() => setShowImportModal(true)}
              title="Importar empleados desde Excel"
            >
              <span className="material-icons">upload_file</span>
              Importar
            </button>
          </ProtectedComponent>
          <ProtectedComponent permissions={['chatbot.operators.manage']}>
            <button 
              className="create-contact-btn"
              onClick={() => setShowCreateModal(true)}
            >
              <span className="material-icons">add</span>
              Agregar
            </button>
          </ProtectedComponent>
        </div>
      </div>

      {/* Campo de búsqueda */}
      <SearchInput
        value={searchTerm}
        onChange={setSearchTerm}
        placeholder="Buscar empleados por nombre o cédula..."
        resultsCount={filteredEmployees.length}
        totalCount={operators.length}
        className="contact-search"
      />

      {loading && <div className="loading">Cargando empleados...</div>}
      {error && <div className="template-error">{error}</div>}

      <div className="contacts-list">
        {!loading && !error && filteredEmployees.map((operator) => (
          <div 
            key={operator.cedula} 
            className="contact-item"
          >
            <div className="contact-avatar">
              {operator.name.charAt(0).toUpperCase()}
            </div>
            <div className="contact-info">
              <div className="contact-name">{operator.name}</div>
              <div className="operator-cedula">Cédula: {formatCedula(operator.cedula)}</div>
              <div className="contact-last-message">
                {operator.is_active ? (
                  <>
                    <span className="material-icons">check_circle</span>
                    Activo
                  </>
                ) : (
                  <>
                    <span className="material-icons">cancel</span>
                    Inactivo
                  </>
                )} • Expedición: {formatDate(operator.expedition_date)}
              </div>
            </div>
            <div className="contact-actions" onClick={(e) => e.stopPropagation()}>
              <ProtectedComponent permissions={['chatbot.operators.manage']}>
                <button 
                  className="edit-btn"
                  onClick={() => openEditModal(operator)}
                  title="Editar operario"
                >
                  <span className="material-icons">edit</span>
                </button>
              </ProtectedComponent>
              <ProtectedComponent permissions={['chatbot.operators.manage']}>
                <button 
                  className="delete-btn"
                  onClick={() => handleDeleteOperator(operator.cedula)}
                  title="Eliminar operario"
                >
                  <span className="material-icons">delete</span>
                </button>
              </ProtectedComponent>
            </div>
          </div>
        ))}
        
        {!loading && !error && filteredEmployees.length === 0 && (
          <div className="no-contacts">
            <p>No hay empleados registrados</p>
            <p>Crea tu primer empleado para comenzar</p>
          </div>
        )}
      </div>

      {/* Modal para crear empleado */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h4>Agregar Nuevo Empleado</h4>
            <div className="form-group">
              <label>Cédula:</label>
              <input
                type="text"
                value={newOperator.cedula}
                onChange={(e) => setNewOperator({ ...newOperator, cedula: e.target.value })}
                placeholder="Número de cédula"
                maxLength={10}
              />
            </div>
            <div className="form-group">
              <label>Nombre:</label>
              <input
                type="text"
                value={newOperator.name}
                onChange={(e) => setNewOperator({ ...newOperator, name: e.target.value })}
                placeholder="Nombre completo del empleado"
              />
            </div>
            <div className="form-group">
              <label>Fecha de Expedición:</label>
              <input
                type="date"
                value={newOperator.expedition_date}
                onChange={(e) => setNewOperator({ ...newOperator, expedition_date: e.target.value })}
              />
            </div>
            <div className="modal-actions">
              <LoadingButton onClick={handleCreateOperator} loading={isCreating}>
                Crear
              </LoadingButton>
              <button onClick={() => setShowCreateModal(false)} disabled={isCreating}>
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal para editar empleado */}
      {showEditModal && editingOperator && (
        <div className="modal-overlay">
          <div className="modal">
            <h4>Editar Empleado</h4>
            <div className="form-group">
              <label>Cédula:</label>
              <input
                type="text"
                value={editingOperator.cedula}
                disabled
                className="disabled-input"
              />
            </div>
            <div className="form-group">
              <label>Nombre:</label>
              <input
                type="text"
                value={editingOperator.name}
                onChange={(e) => setEditingOperator({ ...editingOperator, name: e.target.value })}
                placeholder="Nombre completo del empleado"
              />
            </div>
            <div className="form-group">
              <label>Fecha de Expedición:</label>
              <input
                type="date"
                value={editingOperator.expedition_date.split('T')[0]}
                onChange={(e) => setEditingOperator({ 
                  ...editingOperator, 
                  expedition_date: new Date(e.target.value).toISOString()
                })}
              />
            </div>
            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={editingOperator.is_active}
                  onChange={(e) => setEditingOperator({ ...editingOperator, is_active: e.target.checked })}
                />
                Empleado activo
              </label>
            </div>
            <div className="modal-actions">
              <LoadingButton onClick={handleUpdateOperator} loading={isUpdating}>
                Actualizar
              </LoadingButton>
              <button onClick={() => setShowEditModal(false)} disabled={isUpdating}>
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal para importar empleados */}
      {showImportModal && (
        <OperatorImport
          onImportComplete={() => {
            refreshOperators().catch(() => {});
            onOperatorUpdate?.();
          }}
          onClose={() => setShowImportModal(false)}
        />
      )}

      {/* Diálogo de confirmación */}
      {confirmDialog && (
        <ConfirmDialog
          isOpen={confirmDialog.isOpen}
          title={confirmDialog.title}
          message={confirmDialog.message}
          confirmText={confirmDialog.confirmText}
          cancelText={confirmDialog.cancelText}
          type={confirmDialog.type}
          onConfirm={confirmDialog.onConfirm}
          onCancel={confirmDialog.onCancel}
        />
      )}
    </div>
  );
};

export default OperatorManager;
