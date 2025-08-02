import React, { useEffect, useRef, useCallback, useState } from 'react';
import './InfiniteScroll.css';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

interface InfiniteScrollProps {
  messages: Message[];
  onLoadMore: () => void;
  hasMore: boolean;
  isLoading: boolean;
  children: React.ReactNode;
}

const InfiniteScroll: React.FC<InfiniteScrollProps> = ({
  messages,
  onLoadMore,
  hasMore,
  isLoading,
  children
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isLoadingOlder, setIsLoadingOlder] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [lastScrollHeight, setLastScrollHeight] = useState(0);
  const [lastScrollTop, setLastScrollTop] = useState(0);
  const [shouldMaintainPosition, setShouldMaintainPosition] = useState(false);

  // Detectar cuando el usuario está cerca del inicio
  const isNearTop = useCallback(() => {
    if (!containerRef.current) return false;
    return containerRef.current.scrollTop < 200;
  }, []);

  // Detectar cuando el usuario está cerca del final
  const isNearBottom = useCallback(() => {
    if (!containerRef.current) return true;
    const container = containerRef.current;
    return container.scrollTop + container.clientHeight >= container.scrollHeight - 100;
  }, []);

  const handleScroll = useCallback(() => {
    if (!containerRef.current || isLoading || !hasMore) return;

    const container = containerRef.current;
    const scrollTop = container.scrollTop;
    
    // Guardar posición actual
    setLastScrollTop(scrollTop);
    setLastScrollHeight(container.scrollHeight);

    // Cargar más mensajes cuando está muy cerca del inicio
    if (scrollTop < 100 && hasMore && !isLoadingOlder) {
      console.log('🎯 Cargando mensajes antiguos...');
      setIsLoadingOlder(true);
      setShouldMaintainPosition(true);
      onLoadMore();
    }
  }, [onLoadMore, isLoading, hasMore, isLoadingOlder]);

  // Escuchar eventos de scroll
  useEffect(() => {
    const container = containerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll, { passive: true });
      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, [handleScroll]);

  // Mantener posición del scroll cuando se cargan mensajes antiguos
  useEffect(() => {
    if (!containerRef.current || !shouldMaintainPosition || !isLoadingOlder) return;

    const container = containerRef.current;
    const currentScrollHeight = container.scrollHeight;
    const heightDifference = currentScrollHeight - lastScrollHeight;

    if (heightDifference > 0) {
      console.log('🔒 Manteniendo posición:', { 
        lastScrollTop, 
        heightDifference, 
        newPosition: lastScrollTop + heightDifference 
      });
      
      // Usar requestAnimationFrame para asegurar que el DOM se ha actualizado
      requestAnimationFrame(() => {
        container.scrollTop = lastScrollTop + heightDifference;
        setIsLoadingOlder(false);
        setShouldMaintainPosition(false);
      });
    }
  }, [messages.length, shouldMaintainPosition, isLoadingOlder, lastScrollTop, lastScrollHeight]);

  // Scroll al final en carga inicial o cuando se agregan nuevos mensajes
  useEffect(() => {
    if (!containerRef.current || messages.length === 0) return;

    const container = containerRef.current;
    
    // Solo hacer scroll al final si:
    // 1. Es la carga inicial, o
    // 2. El usuario está cerca del final (nuevos mensajes)
    if (isInitialLoad || (!shouldMaintainPosition && isNearBottom())) {
      console.log('📜 Scroll al final:', { isInitialLoad, isNearBottom: isNearBottom() });
      
      requestAnimationFrame(() => {
        container.scrollTop = container.scrollHeight;
        setIsInitialLoad(false);
      });
    }
  }, [messages.length, isInitialLoad, shouldMaintainPosition]);

  // Resetear estado cuando cambian los mensajes
  useEffect(() => {
    if (messages.length === 0) {
      setIsInitialLoad(true);
      setShouldMaintainPosition(false);
      setIsLoadingOlder(false);
    }
  }, [messages.length]);

  return (
    <div className="infinite-scroll-container" ref={containerRef}>
      {hasMore && isNearTop() && (
        <div className="load-more-indicator">
          {isLoadingOlder ? (
            <div className="loading-more">
              <div className="loading-spinner"></div>
              <span>Cargando mensajes anteriores...</span>
            </div>
          ) : (
            <div className="load-more-text">
              ↑ Desliza hacia arriba para cargar más mensajes
            </div>
          )}
        </div>
      )}
      {children}
    </div>
  );
};

export default InfiniteScroll; 