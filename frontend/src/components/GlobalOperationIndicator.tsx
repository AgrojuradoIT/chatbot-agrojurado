import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useReceiptOperation } from '../contexts/ReceiptOperationContext';
import { Loader } from './Loader';
import '../styles/ReceiptsPanel.css';

const GlobalOperationIndicator: React.FC = () => {
  const { operationState } = useReceiptOperation();
  const [position, setPosition] = useState({ x: window.innerWidth - 420, y: 20 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const indicatorRef = useRef<HTMLDivElement>(null);

  // Funciones para manejar el drag
  const handleMouseDown = (e: React.MouseEvent) => {
    if (indicatorRef.current) {
      const rect = indicatorRef.current.getBoundingClientRect();
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      });
      setIsDragging(true);
    }
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (isDragging) {
      const newX = e.clientX - dragOffset.x;
      const newY = e.clientY - dragOffset.y;
      
      // Limitar el movimiento dentro de la ventana
      const maxX = window.innerWidth - (indicatorRef.current?.offsetWidth || 300);
      const maxY = window.innerHeight - (indicatorRef.current?.offsetHeight || 100);
      
      setPosition({
        x: Math.max(0, Math.min(newX, maxX)),
        y: Math.max(0, Math.min(newY, maxY))
      });
    }
  }, [isDragging, dragOffset]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Agregar event listeners para el drag
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = 'none'; // Prevenir selección de texto
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = '';
    };
  }, [isDragging, dragOffset]);

  // Calcular porcentaje real basado en WebSocket
  const getRealTimeProgress = () => {
    const { realTimeProgress } = operationState;
    if (realTimeProgress.currentOperation && realTimeProgress.totalFiles > 0) {
      const percentage = Math.round((realTimeProgress.processedFiles / realTimeProgress.totalFiles) * 100);
      return {
        percentage,
        text: `${realTimeProgress.operationType} ${realTimeProgress.totalFiles} archivo(s)... ${percentage}%`,
        processed: realTimeProgress.processedFiles,
        total: realTimeProgress.totalFiles
      };
    }
    return null;
  };

  const realTimeProgress = getRealTimeProgress();

  // Verificar si debe mostrar el componente DESPUÉS de todos los hooks
  if (!operationState.isAnyOperationInProgress && !operationState.realTimeProgress.currentOperation) {
    return null;
  }

  return (
    <div 
      ref={indicatorRef}
      className={`global-operation-indicator ${isDragging ? 'dragging' : ''}`}
      style={{
        position: 'fixed',
        left: position.x,
        top: position.y,
        cursor: isDragging ? 'grabbing' : 'grab',
        zIndex: 9999
      }}
      onMouseDown={handleMouseDown}
    >
      <div className="operation-content">
        <div className="drag-handle">
          <span className="material-icons">drag_indicator</span>
        </div>
        <Loader size={20} color="white" />
        <span className="operation-text">
          {realTimeProgress ? realTimeProgress.text : (
            <>
              {operationState.uploadProgress.isUploading && 
                `Subiendo ${operationState.uploadProgress.total} archivo(s)...`}
              {operationState.isMoving && 
                `Moviendo ${operationState.moveProgress.total} archivo(s)...`}
              {operationState.isDeleting && 
                `Eliminando ${operationState.deleteProgress.total} archivo(s)...`}
            </>
          )}
        </span>
        <span className="operation-wait">
          Por favor espere...
        </span>
        {realTimeProgress && (
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${realTimeProgress.percentage}%` }}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default GlobalOperationIndicator;
