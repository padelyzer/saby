"""
Sistema de Gestión de Autenticación y Sesiones por Usuario
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
import uuid

class AuthManager:
    def __init__(self, secret_key: str = "botphia_secret_key_2025"):
        self.secret_key = secret_key
        self.active_sessions = {}  # user_id -> session_data
        
    def create_token(self, user_data: Dict) -> str:
        """Crea un token JWT para el usuario"""
        payload = {
            'user_id': user_data['id'],
            'email': user_data['email'],
            'name': user_data['name'],
            'role': user_data['role'],
            'exp': datetime.utcnow() + timedelta(days=7),  # Expira en 7 días
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        
        # Crear sesión activa
        self.active_sessions[user_data['id']] = {
            'user_id': user_data['id'],
            'email': user_data['email'],
            'name': user_data['name'],
            'role': user_data['role'],
            'login_time': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'session_id': str(uuid.uuid4())
        }
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verifica y decodifica un token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            user_id = payload['user_id']
            
            # Verificar que la sesión siga activa
            if user_id in self.active_sessions:
                # Actualizar última actividad
                self.active_sessions[user_id]['last_activity'] = datetime.now().isoformat()
                return payload
            
            return None
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_user_session(self, user_id: str) -> Optional[Dict]:
        """Obtiene la sesión activa de un usuario"""
        return self.active_sessions.get(user_id)
    
    def logout_user(self, user_id: str) -> bool:
        """Cierra la sesión de un usuario"""
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]
            return True
        return False
    
    def get_active_users(self) -> list:
        """Obtiene lista de usuarios activos"""
        return list(self.active_sessions.keys())
    
    def cleanup_expired_sessions(self):
        """Limpia sesiones expiradas (ejecutar periódicamente)"""
        current_time = datetime.now()
        expired_users = []
        
        for user_id, session in self.active_sessions.items():
            last_activity = datetime.fromisoformat(session['last_activity'])
            # Sesiones inactivas por más de 24 horas se consideran expiradas
            if (current_time - last_activity).total_seconds() > 24 * 3600:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self.active_sessions[user_id]
        
        return expired_users

# Instancia global del gestor de autenticación
auth_manager = AuthManager()