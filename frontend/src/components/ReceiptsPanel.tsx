import React, { useState, useEffect } from 'react';
import '../styles/ReceiptsPanel.css';
import { useNotifications } from './NotificationContainer';
import SearchInput from './SearchInput';
import { useReceiptOperation } from '../contexts/ReceiptOperationContext';
import { websocketService } from '../services/websocketService';
import type { WebSocketMessage } from '../services/websocketService';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

interface Receipt {
  id: string;
  nombre: string;
  cedula: string;
  fecha: string;
  carpeta: 'recientes' | 'anteriores';
  tamaño: string;
  ruta: string;
}

interface ReceiptsPanelProps {
  onClose: () => void;
}

const ReceiptsPanel: React.FC<ReceiptsPanelProps> = () => {
  const { showNotification } = useNotifications();
  const { operationState, startRealTimeOperation, updateRealTimeProgress, completeRealTimeOperation } = useReceiptOperation();
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedReceipts, setSelectedReceipts] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<'recientes' | 'anteriores'>('recientes');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showMoveModal, setShowMoveModal] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Load receipts when component mounts
  useEffect(() => {
    loadReceipts();
  }, []);


  // Limpiar búsqueda al cambiar de pestaña
  useEffect(() => {
    setSearchQuery('');
    // Limpiar selección al cambiar de pestaña para evitar problemas
    setSelectedReceipts([]);
  }, [activeTab]);

  // Efecto para escuchar eventos WebSocket en tiempo real
  useEffect(() => {
    const handleWebSocketMessage = (message: WebSocketMessage) => {
      console.log('🔌 WebSocket message received:', message.type, message.data);
      
      if (message.type === 'receipt_deleted' && message.data) {
        // Actualizar UI inmediatamente cuando se elimina un archivo
        setReceipts(prevReceipts => 
          prevReceipts.filter(receipt => receipt.id !== message.data!.receipt_id)
        );
        
        // Actualizar progreso real usando callback para obtener el estado más reciente
        updateRealTimeProgress(prevProcessed => {
          const newProcessedCount = prevProcessed + 1;
          const percentage = Math.round((newProcessedCount / operationState.realTimeProgress.totalFiles) * 100);
          console.log(`📊 Progreso eliminación: ${newProcessedCount}/${operationState.realTimeProgress.totalFiles} (${percentage}%)`);
          
          // Verificar si se completó la operación
          if (newProcessedCount >= operationState.realTimeProgress.totalFiles) {
            console.log('🎯 Operación de eliminación completada por WebSocket');
            // Pequeño delay para que el usuario vea el 100%
            setTimeout(() => {
              completeRealTimeOperation();
              // NO mostrar notificación aquí - ya se mostró por fallback HTTP
            }, 1000);
          }
          
          return newProcessedCount;
        });
        
        console.log('📄 Archivo eliminado en tiempo real:', message.data.filename);
      } else if (message.type === 'receipt_moved' && message.data) {
        // Actualizar UI inmediatamente cuando se mueve un archivo
        setReceipts(prevReceipts => 
          prevReceipts.map(receipt => 
            receipt.id === message.data!.receipt_id 
              ? { ...receipt, carpeta: message.data!.target_folder! as 'recientes' | 'anteriores' }
              : receipt
          )
        );
        
        // Actualizar progreso real usando callback para obtener el estado más reciente
        updateRealTimeProgress(prevProcessed => {
          const newProcessedCount = prevProcessed + 1;
          const percentage = Math.round((newProcessedCount / operationState.realTimeProgress.totalFiles) * 100);
          console.log(`📊 Progreso movimiento: ${newProcessedCount}/${operationState.realTimeProgress.totalFiles} (${percentage}%)`);
          
          // Verificar si se completó la operación
          if (newProcessedCount >= operationState.realTimeProgress.totalFiles) {
            console.log('🎯 Operación de movimiento completada por WebSocket');
            // Pequeño delay para que el usuario vea el 100%
            setTimeout(() => {
              completeRealTimeOperation();
              // NO mostrar notificación aquí - ya se mostró por fallback HTTP
            }, 1000);
          }
          
          return newProcessedCount;
        });
        
        console.log('📄 Archivo movido en tiempo real:', message.data.filename, 'a', message.data.target_folder);
      } else if (message.type === 'receipt_uploaded' && message.data) {
        // Actualizar UI inmediatamente cuando se sube un archivo
        const newReceipt: Receipt = {
          id: `${message.data.folder}_${message.data.filename}`,
          nombre: message.data.filename || 'Unknown',
          cedula: message.data.cedula || 'N/A',
          fecha: message.data.timestamp || new Date().toISOString(),
          carpeta: message.data.folder! as 'recientes' | 'anteriores',
          tamaño: message.data.size_formatted || 'N/A',
          ruta: `${message.data.folder}/${message.data.filename}`
        };
        setReceipts(prevReceipts => {
          // Evitar duplicados verificando si ya existe
          const exists = prevReceipts.some(receipt => receipt.id === newReceipt.id);
          if (exists) {
            console.log('⚠️ Archivo ya existe en el estado, pero actualizando progreso:', newReceipt.id);
            return prevReceipts; // No agregar duplicado, pero continuar con el progreso
          }
          return [newReceipt, ...prevReceipts];
        });
        
        // Actualizar progreso real usando callback para obtener el estado más reciente
        updateRealTimeProgress(prevProcessed => {
          const newProcessedCount = prevProcessed + 1;
          const percentage = Math.round((newProcessedCount / operationState.realTimeProgress.totalFiles) * 100);
          console.log(`📊 Progreso subida: ${newProcessedCount}/${operationState.realTimeProgress.totalFiles} (${percentage}%)`);
          
          // Verificar si se completó la operación
          if (newProcessedCount >= operationState.realTimeProgress.totalFiles) {
            console.log('🎯 Operación de subida completada por WebSocket');
            // Pequeño delay para que el usuario vea el 100%
            setTimeout(() => {
              completeRealTimeOperation();
              // NO mostrar notificación aquí - ya se mostró por fallback HTTP
            }, 1000);
          }
          
          return newProcessedCount;
        });
        
        console.log('📄 Archivo subido en tiempo real:', message.data.filename);
      }
    };

    // Registrar listener de WebSocket
    const removeListener = websocketService.onMessage(handleWebSocketMessage);

    // Limpiar listener al desmontar
    return () => {
      removeListener();
    };
  }, [operationState.realTimeProgress.processedFiles, updateRealTimeProgress]);

  const loadReceipts = async (forceRefresh: boolean = false) => {
    try {
      setLoading(true);
      setError(null);
      
      // Si es actualización forzada, limpiar caché primero
      if (forceRefresh) {
        try {
          await fetch(`${API_BASE_URL}/api/receipts/clear-cache`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
          });
        } catch (err) {
          console.warn('No se pudo limpiar el caché:', err);
        }
      }
      
      const response = await fetch(`${API_BASE_URL}/api/receipts/list`);
      if (!response.ok) {
        throw new Error('Error loading receipts');
      }
      
      const data = await response.json();
        const receiptsData = data.receipts || [];
        setReceipts(receiptsData);
      setLastUpdated(new Date());
        
        // Limpiar selección de archivos que ya no existen
        setSelectedReceipts(prevSelected => {
          const validSelected = prevSelected.filter(id => 
            receiptsData.some((receipt: Receipt) => receipt.id === id)
          );
          if (validSelected.length !== prevSelected.length) {
            console.log(`🧹 Limpiando selección: ${prevSelected.length - validSelected.length} archivos ya no existen`);
          }
          return validSelected;
        });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectReceipt = (id: string) => {
    setSelectedReceipts(prev => 
      prev.includes(id) 
        ? prev.filter(receiptId => receiptId !== id)
        : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    const currentTabReceipts = receipts.filter(receipt => receipt.carpeta === activeTab);
    if (selectedReceipts.length === currentTabReceipts.length) {
      setSelectedReceipts([]);
    } else {
      setSelectedReceipts(currentTabReceipts.map(receipt => receipt.id));
    }
  };

  // 1. FUNCIÓN PRINCIPAL DE ELIMINACIÓN OPTIMIZADA CON PROGRESO REAL
  const handleDeleteReceipts = async () => {
    try {
      // Solo usar el sistema de progreso real-time
      startRealTimeOperation('delete', selectedReceipts.length, 'Eliminando');
      
      setError(null);
      setShowDeleteModal(false); // Cerrar modal inmediatamente
      
      // Procesar en lotes sin progreso simulado
      const response = await fetch(`${API_BASE_URL}/api/receipts/delete-batch`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          ids: selectedReceipts,
          optimize: true 
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status} ${response.statusText}`);
      }
      
      const result = await response.json();
      
      // Actualizar frontend inmediatamente con todos los cambios
      if (result.deleted && result.deleted.length > 0) {
        setReceipts(prevReceipts => 
          prevReceipts.filter(receipt => !result.deleted.includes(receipt.id))
        );
      }
      
      setSelectedReceipts([]);
      
      // Completar progreso basado en el resultado HTTP como fallback
      console.log('📦 Resultado HTTP de eliminación:', result);
      
      // Si no hay errores, completar el progreso inmediatamente
      if (result.total_errors === 0) {
        console.log('✅ Eliminación exitosa, completando progreso por fallback HTTP');
        setTimeout(() => {
          completeRealTimeOperation();
        showNotification({
          type: 'success',
          title: 'Eliminación Exitosa',
          message: `Se eliminaron ${result.total_deleted} archivo(s) exitosamente.`
        });
          // Recargar datos para sincronizar estado
          loadReceipts();
        }, 500);
      } else {
        // Si hay errores, completar progreso pero mostrar advertencia
        console.log('⚠️ Eliminación parcial, completando progreso por fallback HTTP');
        setTimeout(() => {
          completeRealTimeOperation();
        showNotification({
          type: 'warning',
          title: '⚠️ Eliminación Parcial',
          message: `${result.total_deleted} eliminados, ${result.total_errors} fallaron.`
        });
          // Recargar datos para sincronizar estado
          loadReceipts();
        }, 500);
      }
      
    } catch (error) {
      console.error('Error deleting receipts:', error);
      const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
      setError(errorMessage);
      showNotification({
        type: 'error',
        title: 'Error al Eliminar',
        message: errorMessage
      });
    } finally {
        // No limpiar aquí - se maneja por WebSocket
      }
  };

  const handleMoveReceipts = async (targetFolder: 'recientes' | 'anteriores') => {
    try {
      // Validar que los archivos seleccionados existan en la carpeta actual
      const currentTabReceipts = receipts.filter(receipt => receipt.carpeta === activeTab);
      const validReceipts = selectedReceipts.filter(id => 
        currentTabReceipts.some(receipt => receipt.id === id)
      );
      
      if (validReceipts.length === 0) {
        showNotification({
          type: 'error',
          title: 'Error de Validación',
          message: 'No hay archivos válidos seleccionados para mover.'
        });
        return;
      }
      
      if (validReceipts.length !== selectedReceipts.length) {
        console.warn('⚠️ Algunos archivos seleccionados ya no existen en la carpeta actual');
        showNotification({
          type: 'warning',
          title: 'Advertencia',
          message: `Solo ${validReceipts.length} de ${selectedReceipts.length} archivos son válidos para mover.`
        });
      }
      
      console.log('🔄 Iniciando movimiento:', {
        selectedReceipts: validReceipts,
        targetFolder,
        currentTab: activeTab,
        totalSelected: validReceipts.length,
        originalSelected: selectedReceipts.length
      });
      
      // Solo usar el sistema de progreso real-time
      startRealTimeOperation('move', validReceipts.length, 'Moviendo');
      
      setError(null);
      setShowMoveModal(false); // Cerrar modal inmediatamente
      
      // Procesar en lotes sin progreso simulado
          const response = await fetch(`${API_BASE_URL}/api/receipts/move`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
          ids: validReceipts, // Usar solo los archivos válidos
              target_folder: targetFolder 
            }),
          });
          
      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status} ${response.statusText}`);
      }
      
            const result = await response.json();
      
      // Actualizar frontend inmediatamente con todos los cambios
      if (result.moved && result.moved.length > 0) {
        setReceipts(prevReceipts => 
          prevReceipts.map(receipt => 
            result.moved.includes(receipt.id)
              ? { ...receipt, carpeta: targetFolder }
              : receipt
          )
        );
      }
      
      setSelectedReceipts([]);
      
      // Completar progreso basado en el resultado HTTP como fallback
      console.log('📦 Resultado HTTP de movimiento:', result);
      console.log('📊 Detalles del resultado:', {
        moved: result.moved?.length || 0,
        errors: result.errors?.length || 0,
        errorDetails: result.errors,
        movedFiles: result.moved
      });
      
      // Si no hay errores, completar el progreso inmediatamente
      if (!result.errors || result.errors.length === 0) {
        console.log('✅ Movimiento exitoso, completando progreso por fallback HTTP');
        setTimeout(() => {
          completeRealTimeOperation();
        showNotification({
          type: 'success',
          title: 'Archivos Movidos',
            message: `Se movieron ${result.moved?.length || 0} archivo(s) exitosamente a ${targetFolder}.`
        });
          // Recargar datos para sincronizar estado
          loadReceipts();
        }, 500);
      } else {
        // Si hay errores, completar progreso pero mostrar advertencia
        console.log('⚠️ Movimiento parcial, completando progreso por fallback HTTP');
        
        // Verificar si todos los errores son por archivos ya en la carpeta destino
        const allAlreadyInTarget = result.errors?.every((error: string) => 
          error.includes('is already in the target folder')
        );
        
        setTimeout(() => {
          completeRealTimeOperation();
          
          if (allAlreadyInTarget && result.moved?.length === 0) {
            // Todos los archivos ya están en la carpeta destino
            showNotification({
              type: 'info',
              title: 'Archivos Ya Movidos',
              message: `Los archivos seleccionados ya están en la carpeta ${targetFolder}.`
            });
          } else {
            // Movimiento parcial con errores reales
        showNotification({
          type: 'warning',
          title: 'Movimiento Parcial',
              message: `Se movieron ${result.moved?.length || 0} archivo(s), pero ${result.errors?.length || 0} fallaron.`
        });
          }
          
          // Recargar datos para sincronizar estado
          loadReceipts();
        }, 500);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error moving files';
      setError(errorMessage);
      showNotification({
        type: 'error',
        title: 'Error al Mover',
        message: errorMessage
      });
    } finally {
        // No limpiar aquí - se maneja por WebSocket
    }
  };

  const handleUploadFiles = async (files: File[]) => {
    try {
      setError(null);
      setShowUploadModal(false); // Cerrar modal inmediatamente
      
      // Solo usar el sistema de progreso real-time
      startRealTimeOperation('upload', files.length, 'Subiendo');
      
      // Procesar en lotes sin progreso simulado
          const formData = new FormData();
      files.forEach(file => {
            formData.append('files', file);
          });
          formData.append('folder', activeTab);
          
          const response = await fetch(`${API_BASE_URL}/api/receipts/upload-multiple`, {
            method: 'POST',
            body: formData,
          });
          
      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status} ${response.statusText}`);
      }
      
            const result = await response.json();
      console.log('📦 Resultado de subida:', result);
      
      // NO actualizar el estado aquí - el WebSocket ya está manejando esto en tiempo real
      // Solo loggear para debugging
      if (result.uploaded_files && result.uploaded_files.length > 0) {
        console.log('📁 Archivos subidos (manejados por WebSocket):', result.uploaded_files.length);
        console.log('🔌 El WebSocket ya agregó estos archivos al estado en tiempo real');
      }
      
      // Completar progreso basado en el resultado HTTP como fallback
      console.log('📦 Resultado HTTP de subida:', result);
      
      // Si no hay errores, completar el progreso inmediatamente
      if (!result.failed_files || result.failed_files.length === 0) {
        console.log('✅ Subida exitosa, completando progreso por fallback HTTP');
        setTimeout(() => {
          completeRealTimeOperation();
        showNotification({
          type: 'success',
          title: 'Archivos Subidos',
            message: `Se subieron ${result.uploaded_files?.length || 0} archivo(s) exitosamente a ${activeTab}.`
        });
          // Recargar datos para sincronizar estado
          loadReceipts();
        }, 500);
      } else {
        // Si hay errores, completar progreso pero mostrar advertencia
        console.log('⚠️ Subida parcial, completando progreso por fallback HTTP');
        setTimeout(() => {
          completeRealTimeOperation();
        showNotification({
          type: 'warning',
          title: 'Subida Parcial',
            message: `Se subieron ${result.uploaded_files?.length || 0} archivo(s), pero ${result.failed_files?.length || 0} fallaron.`
        });
          // Recargar datos para sincronizar estado
          loadReceipts();
        }, 500);
      }
      
      // No necesitamos recargar la lista completa ya que actualizamos progresivamente
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error uploading files';
      setError(errorMessage);
      showNotification({
        type: 'error',
        title: 'Error al Subir',
        message: errorMessage
      });
    } finally {
        // No limpiar aquí - se maneja por WebSocket
      }
  };

  // Función para filtrar comprobantes por búsqueda
  const filterReceipts = (receiptsList: Receipt[], query: string) => {
    if (!query.trim()) {
      return receiptsList;
    }

    const searchTerm = query.toLowerCase().trim();
    
    return receiptsList.filter(receipt => {
      // Buscar en nombre del archivo
      const nameMatch = receipt.nombre.toLowerCase().includes(searchTerm);
      
      // Buscar en cédula
      const cedulaMatch = receipt.cedula.toLowerCase().includes(searchTerm);
      
      // Buscar en fecha formateada
      const formattedDate = formatDate(receipt.fecha).toLowerCase();
      const dateMatch = formattedDate.includes(searchTerm);
      
      // Buscar en fecha original (formato ISO)
      const originalDate = receipt.fecha.toLowerCase();
      const originalDateMatch = originalDate.includes(searchTerm);
      
      return nameMatch || cedulaMatch || dateMatch || originalDateMatch;
    });
  };

  const getCurrentTabReceipts = () => {
    const tabReceipts = receipts.filter(receipt => receipt.carpeta === activeTab);
    return filterReceipts(tabReceipts, searchQuery);
  };

  // Función para formatear tamaño de archivo (usada en el futuro)
  // const formatFileSize = (bytes: number) => {
  //   if (bytes === 0) return '0 Bytes';
  //   const k = 1024;
  //   const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  //   const i = Math.floor(Math.log(bytes) / Math.log(k));
  //   return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  // };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-CO', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="receipts-panel">

      {/* Header principal con título y navegación */}
      <div className="receipts-header">
        <div className="header-left">
          <h2><span className="material-icons">description</span>Gestión de Comprobantes</h2>
          {lastUpdated && (
            <span className="last-updated">
              <span className="material-icons">schedule</span>Actualizado: {lastUpdated.toLocaleTimeString('es-CO')}
            </span>
          )}
        </div>
        <button 
          className="action-button"
          onClick={() => loadReceipts(true)}
          disabled={loading || operationState.isAnyOperationInProgress}
        >
          {loading ? (
            <>
              <span className="material-icons">hourglass_empty</span>Actualizando...
            </>
          ) : (
            <>
              <span className="material-icons">refresh</span>Actualizar
            </>
          )}
        </button>
      </div>

      {/* Barra unificada con pestañas, acciones y búsqueda */}
      <div className="receipts-toolbar">
        {/* Pestañas */}
        <div className="toolbar-tabs">
        <button 
          className={`tab-button ${activeTab === 'recientes' ? 'active' : ''}`}
          onClick={() => setActiveTab('recientes')}
            disabled={operationState.isAnyOperationInProgress}
        >
          <span className="material-icons">folder</span>Recientes ({receipts.filter(r => r.carpeta === 'recientes').length})
        </button>
        <button 
          className={`tab-button ${activeTab === 'anteriores' ? 'active' : ''}`}
          onClick={() => setActiveTab('anteriores')}
            disabled={operationState.isAnyOperationInProgress}
        >
          <span className="material-icons">folder</span>Anteriores ({receipts.filter(r => r.carpeta === 'anteriores').length})
        </button>
      </div>

        {/* Acciones */}
        <div className="toolbar-actions">
          <button 
            className="action-button primary"
            onClick={() => setShowUploadModal(true)}
            disabled={operationState.isAnyOperationInProgress}
          >
            <span className="material-icons">cloud_upload</span>Subir {activeTab === 'recientes' ? 'Recientes' : 'Anteriores'}
          </button>
        </div>

        {/* Buscador */}
        <div className="toolbar-search">
          <SearchInput
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Buscar por nombre, cédula o fecha..."
            resultsCount={getCurrentTabReceipts().length}
            totalCount={receipts.filter(r => r.carpeta === activeTab).length}
            className="receipts-search-input"
            showResultsInfo={false}
            showClearButton={true}
            disabled={operationState.isAnyOperationInProgress}
          />
        </div>
      </div>

      {/* Acciones de selección múltiple */}
          {selectedReceipts.length > 0 && (
        <div className="selection-actions">
          <div className="selection-info">
            <span className="selection-count">
              {selectedReceipts.length} comprobante{selectedReceipts.length !== 1 ? 's' : ''} seleccionado{selectedReceipts.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="selection-buttons">
              <button 
                className="action-button secondary"
                onClick={() => setShowMoveModal(true)}
                disabled={operationState.isAnyOperationInProgress}
              >
                {operationState.realTimeProgress.currentOperation === 'move' ? (
                  <>
                    <span className="material-icons">hourglass_empty</span>Moviendo...
                  </>
                ) : (
                  <>
                    <span className="material-icons">drive_file_move</span>Mover a {activeTab === 'recientes' ? 'Anteriores' : 'Recientes'}
                  </>
                )}
              </button>
              <button 
                className="action-button danger"
                onClick={() => setShowDeleteModal(true)}
                disabled={operationState.isAnyOperationInProgress}
              >
                {operationState.realTimeProgress.currentOperation === 'delete' ? (
                  <>
                    <span className="material-icons">hourglass_empty</span>Eliminando...
                  </>
                ) : (
                  <>
                    <span className="material-icons">delete</span>Eliminar
                  </>
                )}
              </button>
        </div>
        </div>
      )}

      {error && (
        <div className="error-message">
          <span className="material-icons">error</span>{error}
        </div>
      )}

      <div className="receipts-content">
        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p><span className="material-icons">description</span>Cargando comprobantes...</p>
          </div>
        ) : (
          <div className="receipts-table">
            <div className="table-header">
              <div className="table-cell checkbox">
                <input 
                  type="checkbox" 
                  checked={selectedReceipts.length === getCurrentTabReceipts().length && getCurrentTabReceipts().length > 0}
                  onChange={handleSelectAll}
                            disabled={operationState.isAnyOperationInProgress}
                />
              </div>
              <div className="table-cell">Archivo</div>
              <div className="table-cell">Cedula</div>
              <div className="table-cell">Fecha</div>
              <div className="table-cell">Tamaño</div>
              <div className="table-cell">Acciones</div>
            </div>
            
            {getCurrentTabReceipts().length === 0 ? (
              <div className="empty-state">
                <p><span className="material-icons">folder_open</span>No hay comprobantes en la carpeta {activeTab}</p>
              </div>
            ) : (
              getCurrentTabReceipts().map((receipt) => (
                <div key={receipt.id} className="table-row">
                  <div className="table-cell checkbox">
                    <input 
                      type="checkbox" 
                      checked={selectedReceipts.includes(receipt.id)}
                      onChange={() => handleSelectReceipt(receipt.id)}
                                disabled={operationState.isAnyOperationInProgress}
                    />
                  </div>
                  <div className="table-cell">
                    <div className="file-info">
                      <span className="material-icons file-icon">description</span>
                      <span className="file-name">{receipt.nombre}</span>
                    </div>
                  </div>
                  <div className="table-cell">{receipt.cedula}</div>
                  <div className="table-cell">{formatDate(receipt.fecha)}</div>
                  <div className="table-cell">{receipt.tamaño}</div>
                  <div className="table-cell">
                    <button 
                      className="action-button small"
                      onClick={() => window.open(`${API_BASE_URL}/api/receipts/download/${receipt.id}`, '_blank')}
                                disabled={operationState.isAnyOperationInProgress}
                    >
                      <span className="material-icons">download</span>
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Modal de Subida */}
      {showUploadModal && (
        <UploadModal 
          onClose={() => setShowUploadModal(false)}
          onUpload={handleUploadFiles}
          targetFolder={activeTab}
        />
      )}

      {/* Modal de Eliminación */}
      {showDeleteModal && (
        <DeleteModal 
          onClose={() => setShowDeleteModal(false)}
          onConfirm={handleDeleteReceipts}
          count={selectedReceipts.length}
        />
      )}

      {/* Modal de Movimiento */}
      {showMoveModal && (
        <MoveModal 
          onClose={() => setShowMoveModal(false)}
          onMove={handleMoveReceipts}
          count={selectedReceipts.length}
          currentFolder={activeTab}
        />
      )}
    </div>
  );
};

// Componente Modal de Subida
const UploadModal: React.FC<{
  onClose: () => void;
  onUpload: (files: File[]) => void;
  targetFolder: 'recientes' | 'anteriores';
}> = ({ onClose, onUpload, targetFolder }) => {
  const [files, setFiles] = useState<File[]>([]);
  const [dragActive, setDragActive] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (files.length > 0) {
      onUpload(files);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    setFiles(selectedFiles);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFiles = Array.from(e.dataTransfer.files).filter(file => 
        file.type === 'application/pdf'
      );
      setFiles(droppedFiles);
    }
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  return (
    <div className="modal-overlay">
      <div className="modal upload-modal">
        <div className="modal-header">
          <h3><span className="material-icons">cloud_upload</span>Subir a {targetFolder === 'recientes' ? 'Recientes' : 'Anteriores'}</h3>
          <button className="close-button" onClick={onClose}><span className="material-icons">close</span></button>
        </div>
        <form onSubmit={handleSubmit} className="modal-content">
          <div className="form-group">
            <label>Archivos PDF (múltiples):</label>
            <div 
              className={`file-drop-zone ${dragActive ? 'drag-active' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <div className="drop-zone-content">
                <div className="drop-icon"><span className="material-icons">folder</span></div>
                <p>Arrastra archivos PDF aquí o haz clic para seleccionar</p>
                <p className="drop-hint">Se pueden seleccionar múltiples archivos a la vez</p>
                <input 
                  type="file" 
                  accept=".pdf"
                  multiple
                  onChange={handleFileChange}
                  className="file-input"
                />
              </div>
            </div>
          </div>
          
          {files.length > 0 && (
            <div className="form-group">
              <label>Archivos seleccionados ({files.length}):</label>
              <div className="file-list">
                {files.map((file, index) => (
                  <div key={index} className="file-item">
                    <span className="material-icons file-icon">description</span>
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                    <button 
                      type="button" 
                      className="remove-file"
                      onClick={() => removeFile(index)}
                    >
                      <span className="material-icons">close</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="upload-info">
            <p><span className="material-icons">info</span>La cédula se extraerá automáticamente del nombre de cada archivo.</p>
            <p><span className="material-icons">warning</span>Asegúrate de que los nombres de archivo contengan el número de cédula.</p>
            <p><span className="material-icons">folder</span>Los archivos se subirán a la carpeta: <strong>{targetFolder === 'recientes' ? 'Recientes' : 'Anteriores'}</strong></p>
          </div>


          <div className="modal-actions">
            <button 
              type="button" 
              onClick={onClose}
            >
              Cancelar
            </button>
            <button 
              type="submit" 
              className="primary"
              disabled={files.length === 0}
            >
              Subir {files.length > 0 ? `${files.length} archivo(s)` : 'archivos'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Componente Modal de Eliminación
const DeleteModal: React.FC<{
  onClose: () => void;
  onConfirm: () => void;
  count: number;
}> = ({ onClose, onConfirm, count }) => {
  return (
    <div className="modal-overlay">
      <div className="modal delete-modal">
        <div className="modal-header">
          <h3><span className="material-icons">warning</span>Eliminar Comprobantes</h3>
          <button className="close-button" onClick={onClose}><span className="material-icons">close</span></button>
        </div>
        <div className="modal-content">
          <div className="delete-warning">
            <div className="warning-icon">
              <span className="material-icons">delete_forever</span>
            </div>
            <div className="warning-content">
              <h4>¿Eliminar {count} comprobante{count !== 1 ? 's' : ''}?</h4>
              <p>Los archivos se eliminarán permanentemente del servidor y esta acción no se puede deshacer.</p>
            </div>
          </div>

          <div className="modal-actions">
            <button 
              className="cancel-btn"
              onClick={onClose}
            >
              Cancelar
            </button>
            <button 
              onClick={onConfirm} 
              className="confirm-btn confirm-delete"
            >
              <span className="material-icons">delete_forever</span>
              Eliminar {count} archivo{count !== 1 ? 's' : ''}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Componente Modal de Movimiento
const MoveModal: React.FC<{
  onClose: () => void;
  onMove: (folder: 'recientes' | 'anteriores') => void;
  count: number;
  currentFolder: 'recientes' | 'anteriores';
}> = ({ onClose, onMove, count, currentFolder }) => {
  const targetFolder = currentFolder === 'recientes' ? 'anteriores' : 'recientes';
  
  return (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal-header">
          <h3><span className="material-icons">drive_file_move</span>Mover Comprobantes</h3>
          <button className="close-button" onClick={onClose}><span className="material-icons">close</span></button>
        </div>
        <div className="modal-content">
          <div className="move-info">
            <p><span className="material-icons">drive_file_move</span><strong>Mover {count} comprobante(s)</strong></p>
            <div className="move-path">
              <span className="from-folder"><span className="material-icons">folder</span>{currentFolder === 'recientes' ? 'Recientes' : 'Anteriores'}</span>
              <span className="arrow"><span className="material-icons">arrow_forward</span></span>
              <span className="to-folder"><span className="material-icons">folder</span>{targetFolder === 'recientes' ? 'Recientes' : 'Anteriores'}</span>
            </div>
            <p className="move-description">
              Los archivos se moverán de la carpeta <strong>{currentFolder}</strong> a la carpeta <strong>{targetFolder}</strong>.
            </p>
          </div>

          <div className="modal-actions">
            <button 
              onClick={onClose}
            >
              Cancelar
            </button>
            <button 
              onClick={() => onMove(targetFolder)} 
              className="primary"
            >
              <span className="material-icons">drive_file_move</span>Mover a {targetFolder === 'recientes' ? 'Recientes' : 'Anteriores'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReceiptsPanel;




