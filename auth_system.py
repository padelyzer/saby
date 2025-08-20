#!/usr/bin/env python3
"""
Sistema de Autenticación Simple
Maneja login y sesiones para 2 usuarios
"""

import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta
from functools import wraps
import getpass
from user_data_manager import user_data

class AuthSystem:
    """Sistema de autenticación simple con 2 usuarios"""
    
    def __init__(self):
        self.session_file = 'session.json'
        self.config_file = 'auth_config.json'
        self.session_duration = timedelta(hours=24)  # Sesión válida por 24 horas
        self.current_session = None
        
        # Inicializar configuración si no existe
        self._initialize_config()
        
    def _initialize_config(self):
        """Inicializa el archivo de configuración con usuarios por defecto"""
        if not os.path.exists(self.config_file):
            # Usuarios por defecto (cambiar estas credenciales)
            default_users = {
                "admin": self._hash_password("admin2024!"),
                "trader": self._hash_password("trader2024!")
            }
            
            config = {
                "users": default_users,
                "created": datetime.now().isoformat(),
                "note": "IMPORTANTE: Cambia estas contraseñas inmediatamente"
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("\n⚠️  IMPORTANTE: Se han creado usuarios por defecto.")
            print("   Usuario 1: admin / admin2024!")
            print("   Usuario 2: trader / trader2024!")
            print("   Por favor, cambia estas contraseñas inmediatamente.\n")
    
    def _hash_password(self, password):
        """Hashea una contraseña usando SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_token(self):
        """Genera un token de sesión seguro"""
        return secrets.token_hex(32)
    
    def _load_config(self):
        """Carga la configuración de usuarios"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self._initialize_config()
            return self._load_config()
    
    def _save_session(self, username, token):
        """Guarda la sesión actual"""
        session_data = {
            "username": username,
            "token": token,
            "created": datetime.now().isoformat(),
            "expires": (datetime.now() + self.session_duration).isoformat()
        }
        
        with open(self.session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        self.current_session = session_data
        
        # Establecer el usuario en el gestor de datos
        user_data.set_user(username)
        
        return session_data
    
    def _load_session(self):
        """Carga y valida la sesión actual"""
        if not os.path.exists(self.session_file):
            return None
        
        try:
            with open(self.session_file, 'r') as f:
                session = json.load(f)
            
            # Verificar si la sesión ha expirado
            expires = datetime.fromisoformat(session['expires'])
            if datetime.now() > expires:
                self.logout()
                return None
            
            self.current_session = session
            
            # Establecer el usuario en el gestor de datos
            if 'username' in session:
                user_data.set_user(session['username'])
            
            return session
        except (json.JSONDecodeError, KeyError):
            return None
    
    def login(self, username=None, password=None):
        """Realiza el login del usuario"""
        # Si no se proporcionan credenciales, solicitarlas
        if not username:
            username = input("Usuario: ")
        if not password:
            password = getpass.getpass("Contraseña: ")
        
        config = self._load_config()
        users = config.get('users', {})
        
        # Verificar credenciales
        if username in users and users[username] == self._hash_password(password):
            token = self._generate_token()
            session = self._save_session(username, token)
            print(f"✅ Login exitoso. Bienvenido, {username}!")
            return True
        else:
            print("❌ Credenciales incorrectas")
            return False
    
    def logout(self):
        """Cierra la sesión actual"""
        if os.path.exists(self.session_file):
            os.remove(self.session_file)
        self.current_session = None
        print("✅ Sesión cerrada")
    
    def is_authenticated(self):
        """Verifica si hay una sesión válida"""
        session = self._load_session()
        return session is not None
    
    def get_current_user(self):
        """Obtiene el usuario actual"""
        session = self._load_session()
        return session['username'] if session else None
    
    def change_password(self, username, old_password, new_password):
        """Cambia la contraseña de un usuario"""
        config = self._load_config()
        users = config.get('users', {})
        
        # Verificar contraseña actual
        if username not in users or users[username] != self._hash_password(old_password):
            print("❌ Contraseña actual incorrecta")
            return False
        
        # Actualizar contraseña
        users[username] = self._hash_password(new_password)
        config['users'] = users
        config['last_password_change'] = datetime.now().isoformat()
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Contraseña actualizada para {username}")
        return True
    
    def require_auth(self, func):
        """Decorador para proteger funciones que requieren autenticación"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.is_authenticated():
                print("\n⚠️  Esta función requiere autenticación")
                if not self.login():
                    print("❌ No se pudo autenticar. Acceso denegado.")
                    return None
            return func(*args, **kwargs)
        return wrapper


# Instancia global del sistema de autenticación
auth = AuthSystem()


def require_login(func):
    """Decorador simple para proteger funciones"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not auth.is_authenticated():
            print("\n🔒 Autenticación requerida")
            print("-" * 40)
            
            # Intentar login hasta 3 veces
            for attempt in range(3):
                if auth.login():
                    break
                if attempt < 2:
                    print(f"Intentos restantes: {2 - attempt}")
            else:
                print("\n❌ Máximo de intentos alcanzado. Acceso denegado.")
                return None
        
        # Mostrar usuario actual
        user = auth.get_current_user()
        print(f"\n👤 Usuario actual: {user}")
        print("-" * 40)
        
        return func(*args, **kwargs)
    return wrapper


# CLI para gestionar usuarios
def main():
    """CLI para gestionar el sistema de autenticación"""
    print("\n🔐 Sistema de Autenticación - Gestión de Usuarios")
    print("=" * 50)
    
    while True:
        print("\nOpciones:")
        print("1. Login")
        print("2. Logout")
        print("3. Cambiar contraseña")
        print("4. Ver estado de sesión")
        print("5. Salir")
        
        opcion = input("\nSelecciona una opción (1-5): ")
        
        if opcion == "1":
            auth.login()
        
        elif opcion == "2":
            auth.logout()
        
        elif opcion == "3":
            if not auth.is_authenticated():
                print("Debes iniciar sesión primero")
                continue
            
            username = auth.get_current_user()
            old_password = getpass.getpass("Contraseña actual: ")
            new_password = getpass.getpass("Nueva contraseña: ")
            confirm_password = getpass.getpass("Confirmar nueva contraseña: ")
            
            if new_password != confirm_password:
                print("❌ Las contraseñas no coinciden")
            else:
                auth.change_password(username, old_password, new_password)
        
        elif opcion == "4":
            if auth.is_authenticated():
                user = auth.get_current_user()
                session = auth.current_session or auth._load_session()
                expires = datetime.fromisoformat(session['expires'])
                remaining = expires - datetime.now()
                hours = int(remaining.total_seconds() / 3600)
                minutes = int((remaining.total_seconds() % 3600) / 60)
                
                print(f"\n✅ Sesión activa")
                print(f"   Usuario: {user}")
                print(f"   Tiempo restante: {hours}h {minutes}m")
            else:
                print("\n❌ No hay sesión activa")
        
        elif opcion == "5":
            print("\n👋 Hasta luego!")
            break
        
        else:
            print("❌ Opción no válida")


if __name__ == "__main__":
    main()