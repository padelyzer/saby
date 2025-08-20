#!/usr/bin/env python3
"""
Gestor de Datos por Usuario
Maneja la segregación de datos entre usuarios
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime


class UserDataManager:
    """Gestiona datos segregados por usuario"""
    
    def __init__(self, base_dir="users"):
        self.base_dir = Path(base_dir)
        self.shared_dir = Path("shared_data")
        self.current_user = None
        
        # Archivos que son únicos por usuario
        self.user_files = [
            "active_trades.json",
            "trade_history.json", 
            "bot_config.json",
            "system_state.json",
            "trading_access_log.json",
            "portfolio.json",
            "user_settings.json"
        ]
        
        # Archivos compartidos entre todos los usuarios
        self.shared_files = [
            "signals_*.json",
            "backtest_results_*.json",
            "expert_agents_state*.json",
            "cache/*"
        ]
        
        # Crear directorios base si no existen
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Asegura que existan los directorios necesarios"""
        self.base_dir.mkdir(exist_ok=True)
        self.shared_dir.mkdir(exist_ok=True)
    
    def set_user(self, username):
        """Establece el usuario actual"""
        self.current_user = username
        self.user_dir = self.base_dir / username
        
        # Crear directorio del usuario si no existe
        if not self.user_dir.exists():
            self.initialize_user(username)
        
        return self.user_dir
    
    def initialize_user(self, username):
        """Inicializa el directorio y archivos para un nuevo usuario"""
        user_dir = self.base_dir / username
        user_dir.mkdir(exist_ok=True)
        
        print(f"📁 Inicializando datos para usuario: {username}")
        
        # Crear archivos iniciales vacíos o con configuración por defecto
        initial_files = {
            "active_trades.json": [],
            "trade_history.json": [],
            "portfolio.json": {
                "balance": 10000,  # Balance inicial de $10,000
                "currency": "USDT",
                "created": datetime.now().isoformat()
            },
            "bot_config.json": {
                "scan_interval": 600,  # 10 minutos
                "stop_loss": 2.0,      # 2%
                "take_profit": 4.0,    # 4%
                "max_trades": 3,
                "risk_per_trade": 0.02, # 2% del capital
                "symbols": [
                    "BTC-USD", "ETH-USD", "SOL-USD", 
                    "ADA-USD", "DOGE-USD", "XRP-USD"
                ]
            },
            "system_state.json": {
                "is_running": False,
                "last_scan": None,
                "total_trades": 0,
                "successful_trades": 0,
                "failed_trades": 0
            },
            "user_settings.json": {
                "notifications": True,
                "auto_trade": False,
                "theme": "dark",
                "timezone": "UTC"
            },
            "trading_access_log.json": []
        }
        
        # Crear archivos iniciales
        for filename, content in initial_files.items():
            filepath = user_dir / filename
            if not filepath.exists():
                with open(filepath, 'w') as f:
                    json.dump(content, f, indent=2)
                print(f"  ✅ Creado: {filename}")
        
        return user_dir
    
    def get_user_file(self, filename, user=None):
        """Obtiene la ruta completa de un archivo para el usuario"""
        if user is None:
            user = self.current_user
        
        if user is None:
            raise ValueError("No se ha establecido un usuario")
        
        user_dir = self.base_dir / user
        return user_dir / filename
    
    def get_shared_file(self, filename):
        """Obtiene la ruta de un archivo compartido"""
        return self.shared_dir / filename
    
    def read_user_data(self, filename, user=None):
        """Lee datos del archivo de un usuario"""
        filepath = self.get_user_file(filename, user)
        
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Archivo no encontrado: {filepath}")
            return None
        except json.JSONDecodeError:
            print(f"⚠️  Error leyendo JSON: {filepath}")
            return None
    
    def write_user_data(self, filename, data, user=None):
        """Escribe datos al archivo de un usuario"""
        filepath = self.get_user_file(filename, user)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error escribiendo archivo: {e}")
            return False
    
    def copy_to_user(self, source_file, username, target_filename=None):
        """Copia un archivo al directorio del usuario"""
        if target_filename is None:
            target_filename = Path(source_file).name
        
        target_path = self.base_dir / username / target_filename
        
        try:
            shutil.copy2(source_file, target_path)
            print(f"  ✅ Copiado: {source_file} → {target_path}")
            return True
        except Exception as e:
            print(f"  ❌ Error copiando: {e}")
            return False
    
    def migrate_existing_data(self):
        """Migra datos existentes a la estructura de usuarios"""
        print("\n🔄 Migrando datos existentes...")
        
        # Lista de archivos a migrar
        files_to_migrate = {
            "active_trades.json": "active_trades.json",
            "trade_history.json": "trade_history.json",
            "bot_config.json": "bot_config.json",
            "system_state.json": "system_state.json"
        }
        
        # Migrar para ambos usuarios
        for username in ["admin", "trader"]:
            print(f"\n👤 Migrando datos para: {username}")
            user_dir = self.base_dir / username
            
            if not user_dir.exists():
                self.initialize_user(username)
            
            for source, target in files_to_migrate.items():
                if Path(source).exists():
                    # Si es el primer usuario, mover el archivo
                    if username == "admin":
                        self.copy_to_user(source, username, target)
                    # Para el segundo usuario, copiar configuración limpia
                    else:
                        # Solo copiar configuración, no trades
                        if source == "bot_config.json":
                            self.copy_to_user(source, username, target)
        
        print("\n✅ Migración completada")
    
    def get_user_stats(self, username):
        """Obtiene estadísticas del usuario"""
        self.set_user(username)
        
        stats = {
            "username": username,
            "portfolio": self.read_user_data("portfolio.json"),
            "active_trades": len(self.read_user_data("active_trades.json") or []),
            "system_state": self.read_user_data("system_state.json")
        }
        
        # Calcular P&L del historial
        history = self.read_user_data("trade_history.json") or []
        if history and isinstance(history, list) and len(history) > 0:
            # Verificar que history contiene diccionarios
            if isinstance(history[0], dict):
                total_pnl = sum(trade.get('pnl', 0) for trade in history)
                win_rate = sum(1 for t in history if t.get('pnl', 0) > 0) / len(history) * 100
                stats['total_pnl'] = total_pnl
                stats['win_rate'] = win_rate
                stats['total_trades'] = len(history)
        
        return stats
    
    def list_users(self):
        """Lista todos los usuarios con sus directorios"""
        users = []
        
        if self.base_dir.exists():
            for user_dir in self.base_dir.iterdir():
                if user_dir.is_dir():
                    users.append(user_dir.name)
        
        return users
    
    def backup_user_data(self, username):
        """Crea un backup de los datos del usuario"""
        user_dir = self.base_dir / username
        
        if not user_dir.exists():
            print(f"❌ Usuario no encontrado: {username}")
            return False
        
        # Crear directorio de backups
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        # Nombre del archivo de backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{username}_backup_{timestamp}"
        backup_path = backup_dir / backup_name
        
        try:
            shutil.copytree(user_dir, backup_path)
            print(f"✅ Backup creado: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ Error creando backup: {e}")
            return False


# Instancia global del gestor de datos
user_data = UserDataManager()


def get_user_file_path(filename, username=None):
    """Función helper para obtener rutas de archivos de usuario"""
    if username:
        user_data.set_user(username)
    return user_data.get_user_file(filename)


def read_user_json(filename, username=None):
    """Función helper para leer JSON de usuario"""
    if username:
        user_data.set_user(username)
    return user_data.read_user_data(filename)


def write_user_json(filename, data, username=None):
    """Función helper para escribir JSON de usuario"""
    if username:
        user_data.set_user(username)
    return user_data.write_user_data(filename, data)


# CLI para gestión de datos
def main():
    """CLI para gestionar datos de usuarios"""
    print("\n📊 Gestor de Datos por Usuario")
    print("=" * 50)
    
    manager = UserDataManager()
    
    while True:
        print("\nOpciones:")
        print("1. Migrar datos existentes")
        print("2. Ver usuarios")
        print("3. Ver estadísticas de usuario")
        print("4. Crear backup de usuario")
        print("5. Inicializar nuevo usuario")
        print("6. Salir")
        
        opcion = input("\nSelecciona una opción (1-6): ")
        
        if opcion == "1":
            manager.migrate_existing_data()
        
        elif opcion == "2":
            users = manager.list_users()
            if users:
                print("\n👥 Usuarios existentes:")
                for user in users:
                    print(f"  • {user}")
            else:
                print("\n❌ No hay usuarios creados")
        
        elif opcion == "3":
            username = input("Nombre de usuario: ")
            stats = manager.get_user_stats(username)
            
            if stats:
                print(f"\n📈 Estadísticas de {username}:")
                print(f"  Balance: ${stats['portfolio']['balance']:.2f}")
                print(f"  Trades activos: {stats['active_trades']}")
                
                if 'total_trades' in stats:
                    print(f"  Total trades: {stats['total_trades']}")
                    print(f"  Win rate: {stats['win_rate']:.2f}%")
                    print(f"  P&L Total: ${stats['total_pnl']:.2f}")
        
        elif opcion == "4":
            username = input("Usuario a respaldar: ")
            manager.backup_user_data(username)
        
        elif opcion == "5":
            username = input("Nuevo nombre de usuario: ")
            manager.initialize_user(username)
        
        elif opcion == "6":
            print("\n👋 Hasta luego!")
            break
        
        else:
            print("❌ Opción no válida")


if __name__ == "__main__":
    main()