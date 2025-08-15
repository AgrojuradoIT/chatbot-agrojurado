from fastapi import WebSocket
from typing import Dict, Set
import asyncio

class ConnectionManager:
    """Gestiona las conexiones WebSocket para comunicación en tiempo real"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.general_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, phone_number: str):
        """Conecta un WebSocket específico para un número de teléfono"""
        await websocket.accept()
        if phone_number not in self.active_connections:
            self.active_connections[phone_number] = set()
        self.active_connections[phone_number].add(websocket)
        print(f"Cliente conectado al WebSocket para {phone_number}. Total conexiones: {len(self.active_connections[phone_number])}")

    async def connect_general(self, websocket: WebSocket):
        """Conecta un WebSocket general para todos los contactos"""
        await websocket.accept()
        self.general_connections.add(websocket)
        print(f"Cliente conectado al WebSocket general. Total conexiones: {len(self.general_connections)}")

    def disconnect(self, websocket: WebSocket, phone_number: str):
        """Desconecta un WebSocket específico"""
        if phone_number in self.active_connections:
            self.active_connections[phone_number].discard(websocket)
            if not self.active_connections[phone_number]:
                del self.active_connections[phone_number]
        print(f"Cliente desconectado del WebSocket para {phone_number}")

    def disconnect_general(self, websocket: WebSocket):
        """Desconecta un WebSocket general"""
        self.general_connections.discard(websocket)
        print(f"Cliente desconectado del WebSocket general")

    async def send_message_to_phone(self, phone_number: str, message: dict):
        """Envía mensaje a todas las conexiones de un número específico"""
        if phone_number in self.active_connections:
            disconnected_websockets = []
            for websocket in self.active_connections[phone_number]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    print(f"Error enviando mensaje a WebSocket: {e}")
                    disconnected_websockets.append(websocket)
            
            # Remover conexiones desconectadas
            for websocket in disconnected_websockets:
                self.disconnect(websocket, phone_number)

    async def send_message_to_all(self, message: dict):
        """Envía mensaje a todas las conexiones generales"""
        disconnected_websockets = []
        for websocket in self.general_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error enviando mensaje a WebSocket general: {e}")
                disconnected_websockets.append(websocket)
        
        # Remover conexiones desconectadas
        for websocket in disconnected_websockets:
            self.disconnect_general(websocket)

# Instancia global del manager
manager = ConnectionManager()
