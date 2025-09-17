import React, { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { operatorService } from '../services/operatorService';
import type { Operator } from '../services/operatorService';
import { websocketService, type WebSocketMessage } from '../services/websocketService';

interface OperatorContextType {
  operators: Operator[];
  loading: boolean;
  error: string | null;
  refreshOperators: () => Promise<void>;
}

const OperatorContext = createContext<OperatorContextType | undefined>(undefined);

interface OperatorProviderProps {
  children: ReactNode;
}

export const OperatorProvider: React.FC<OperatorProviderProps> = ({ children }) => {
  const [operators, setOperators] = useState<Operator[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const fetchOperators = async () => {
    try {
      setLoading(true);
      setError(null);
      const resp = await operatorService.getOperators(1, 100, '');
      setOperators(resp.operators);
      setLoaded(true);
    } catch (err) {
      console.error('Error cargando operarios:', err);
      setError('Error al cargar operarios');
    } finally {
      setLoading(false);
    }
  };

  const refreshOperators = async () => {
    await fetchOperators();
  };

  useEffect(() => {
    if (!loaded) {
      fetchOperators();
    }
  }, [loaded]);

  useEffect(() => {
    websocketService.connect();
    const remove = websocketService.onMessage((msg: WebSocketMessage) => {
      if (msg.type === 'operator_updated') {
        fetchOperators();
      }
    });
    return () => remove();
  }, []);

  return (
    <OperatorContext.Provider value={{ operators, loading, error, refreshOperators }}>
      {children}
    </OperatorContext.Provider>
  );
};

export const useOperators = () => {
  const ctx = useContext(OperatorContext);
  if (!ctx) throw new Error('useOperators must be used within an OperatorProvider');
  return ctx;
};


