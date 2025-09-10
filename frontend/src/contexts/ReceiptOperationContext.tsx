import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

interface UploadProgress {
  isUploading: boolean;
  current: number;
  total: number;
  currentFile: string;
}

interface MoveProgress {
  current: number;
  total: number;
  currentFile: string;
}

interface DeleteProgress {
  current: number;
  total: number;
  currentFile: string;
}

interface ReceiptOperationState {
  uploadProgress: UploadProgress;
  isMoving: boolean;
  moveProgress: MoveProgress;
  isDeleting: boolean;
  deleteProgress: DeleteProgress;
  isAnyOperationInProgress: boolean;
  // Contadores para progreso real basado en WebSocket
  realTimeProgress: {
    totalFiles: number;
    processedFiles: number;
    currentOperation: 'upload' | 'move' | 'delete' | null;
    operationType: string;
  };
}

interface ReceiptOperationContextType {
  operationState: ReceiptOperationState;
  setOperationState: (state: Partial<ReceiptOperationState>) => void;
  resetOperationState: () => void;
  startRealTimeOperation: (operation: 'upload' | 'move' | 'delete', totalFiles: number, operationType: string) => void;
  updateRealTimeProgress: (processedFiles: number | ((prev: number) => number)) => void;
  completeRealTimeOperation: () => void;
}

const initialState: ReceiptOperationState = {
  uploadProgress: {
    isUploading: false,
    current: 0,
    total: 0,
    currentFile: ''
  },
  isMoving: false,
  moveProgress: {
    current: 0,
    total: 0,
    currentFile: ''
  },
  isDeleting: false,
  deleteProgress: {
    current: 0,
    total: 0,
    currentFile: ''
  },
  isAnyOperationInProgress: false,
  realTimeProgress: {
    totalFiles: 0,
    processedFiles: 0,
    currentOperation: null,
    operationType: ''
  }
};

const ReceiptOperationContext = createContext<ReceiptOperationContextType | undefined>(undefined);

export const ReceiptOperationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [operationState, setOperationState] = useState<ReceiptOperationState>(initialState);

  const updateOperationState = (newState: Partial<ReceiptOperationState>) => {
    setOperationState(prev => {
      const updated = { ...prev, ...newState };
      
      // Calcular si hay alguna operación en curso
      updated.isAnyOperationInProgress = 
        updated.uploadProgress.isUploading || 
        updated.isMoving || 
        updated.isDeleting;
      
      return updated;
    });
  };

  const resetOperationState = () => {
    setOperationState(initialState);
  };

  const startRealTimeOperation = (operation: 'upload' | 'move' | 'delete', totalFiles: number, operationType: string) => {
    setOperationState(prev => {
      const updated = {
        ...prev,
        realTimeProgress: {
          totalFiles,
          processedFiles: 0,
          currentOperation: operation,
          operationType
        }
      };
      
      // Recalcular si hay alguna operación en curso
      updated.isAnyOperationInProgress = 
        updated.uploadProgress.isUploading || 
        updated.isMoving || 
        updated.isDeleting ||
        !!updated.realTimeProgress.currentOperation;
      
      return updated;
    });
  };

  const updateRealTimeProgress = (processedFiles: number | ((prev: number) => number)) => {
    setOperationState(prev => {
      const newProcessedFiles = typeof processedFiles === 'function' 
        ? processedFiles(prev.realTimeProgress.processedFiles)
        : processedFiles;
        
      const updated = {
        ...prev,
        realTimeProgress: {
          ...prev.realTimeProgress,
          processedFiles: newProcessedFiles
        }
      };
      
      // Recalcular si hay alguna operación en curso
      updated.isAnyOperationInProgress = 
        updated.uploadProgress.isUploading || 
        updated.isMoving || 
        updated.isDeleting ||
        !!updated.realTimeProgress.currentOperation;
      
      return updated;
    });
  };

  const completeRealTimeOperation = () => {
    setOperationState(prev => {
      const updated = {
        ...prev,
        realTimeProgress: {
          totalFiles: 0,
          processedFiles: 0,
          currentOperation: null,
          operationType: ''
        }
      };
      
      // Recalcular si hay alguna operación en curso
      updated.isAnyOperationInProgress = 
        updated.uploadProgress.isUploading || 
        updated.isMoving || 
        updated.isDeleting ||
        !!updated.realTimeProgress.currentOperation;
      
      return updated;
    });
  };

  return (
    <ReceiptOperationContext.Provider 
      value={{ 
        operationState, 
        setOperationState: updateOperationState,
        resetOperationState,
        startRealTimeOperation,
        updateRealTimeProgress,
        completeRealTimeOperation
      }}
    >
      {children}
    </ReceiptOperationContext.Provider>
  );
};

export const useReceiptOperation = (): ReceiptOperationContextType => {
  const context = useContext(ReceiptOperationContext);
  if (context === undefined) {
    throw new Error('useReceiptOperation must be used within a ReceiptOperationProvider');
  }
  return context;
};
