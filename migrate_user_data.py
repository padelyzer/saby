#!/usr/bin/env python3
"""
Script de Migración de Datos a Estructura de Usuarios
Migra los datos existentes a carpetas separadas por usuario
"""

from user_data_manager import UserDataManager
from pathlib import Path
import json
import shutil
from datetime import datetime


def migrate_existing_data():
    """Migra los datos existentes a la nueva estructura"""
    
    print("\n🔄 MIGRACIÓN DE DATOS A ESTRUCTURA DE USUARIOS")
    print("=" * 50)
    
    manager = UserDataManager()
    
    # Crear directorios base
    print("\n📁 Creando estructura de directorios...")
    manager._ensure_directories()
    
    # Inicializar usuarios
    users = ["admin", "trader"]
    
    print("\n👥 Inicializando usuarios:")
    for username in users:
        print(f"\n  👤 Usuario: {username}")
        user_dir = manager.initialize_user(username)
        print(f"     ✅ Directorio creado: {user_dir}")
    
    # Archivos a migrar (si existen)
    files_to_migrate = {
        "active_trades.json": {
            "admin": True,   # Admin obtiene los trades existentes
            "trader": False  # Trader empieza limpio
        },
        "trade_history.json": {
            "admin": True,   # Admin obtiene el historial
            "trader": False  # Trader empieza sin historial
        },
        "bot_config.json": {
            "admin": True,   # Ambos obtienen la config
            "trader": True   # pero pueden personalizarla después
        },
        "system_state.json": {
            "admin": True,
            "trader": False  # Trader empieza con estado nuevo
        }
    }
    
    print("\n📦 Migrando archivos existentes:")
    
    for filename, user_config in files_to_migrate.items():
        source_path = Path(filename)
        
        if source_path.exists():
            print(f"\n  📄 {filename} encontrado")
            
            # Leer el archivo original
            try:
                with open(source_path, 'r') as f:
                    data = json.load(f)
                
                # Migrar según configuración
                for username in users:
                    if user_config.get(username, False):
                        target_path = manager.base_dir / username / filename
                        
                        # Si es trader y es bot_config, personalizar algunos valores
                        if username == "trader" and filename == "bot_config.json":
                            data_copy = data.copy()
                            # Personalizar para trader
                            data_copy['risk_per_trade'] = 0.01  # Trader más conservador
                            data_copy['max_trades'] = 2  # Menos trades simultáneos
                            
                            with open(target_path, 'w') as f:
                                json.dump(data_copy, f, indent=2)
                        else:
                            # Copiar tal cual
                            with open(target_path, 'w') as f:
                                json.dump(data, f, indent=2)
                        
                        print(f"     ✅ Migrado a {username}/{filename}")
                    else:
                        print(f"     ⏭️  {username}: usando valores por defecto")
                        
            except json.JSONDecodeError:
                print(f"     ⚠️  Error leyendo {filename}, saltando...")
        else:
            print(f"\n  ⏭️  {filename} no existe, usando valores por defecto")
    
    # Crear backups de los archivos originales
    print("\n💾 Creando backup de archivos originales...")
    backup_dir = Path("backups/migration_backup")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for filename in files_to_migrate.keys():
        source_path = Path(filename)
        if source_path.exists():
            backup_path = backup_dir / f"{filename}.backup_{timestamp}"
            shutil.copy2(source_path, backup_path)
            print(f"  ✅ Backup: {backup_path}")
    
    # Mostrar resumen
    print("\n📊 RESUMEN DE MIGRACIÓN:")
    print("-" * 40)
    
    for username in users:
        stats = manager.get_user_stats(username)
        print(f"\n👤 {username}:")
        
        if stats and stats['portfolio']:
            print(f"  • Balance inicial: ${stats['portfolio']['balance']:.2f}")
            print(f"  • Trades activos: {stats['active_trades']}")
            
            if username == "admin":
                print(f"  • Datos históricos: ✅ Migrados")
            else:
                print(f"  • Datos históricos: ❌ Inicio limpio")
    
    print("\n" + "=" * 50)
    print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("\n📝 Notas importantes:")
    print("  1. Los archivos originales están respaldados en 'backups/migration_backup'")
    print("  2. Cada usuario ahora tiene su propia carpeta en 'users/'")
    print("  3. Admin heredó los datos existentes")
    print("  4. Trader empieza con configuración limpia")
    print("\n🚀 Puedes ejecutar ahora: python3 protected_trading_system_v2.py")
    
    # Preguntar si eliminar archivos originales
    print("\n⚠️  ¿Deseas eliminar los archivos JSON originales del directorio raíz?")
    print("   (Ya están respaldados en backups/)")
    
    respuesta = input("   Eliminar archivos originales? (s/N): ").lower()
    
    if respuesta == 's':
        print("\n🗑️  Eliminando archivos originales...")
        for filename in files_to_migrate.keys():
            source_path = Path(filename)
            if source_path.exists():
                source_path.unlink()
                print(f"  ✅ Eliminado: {filename}")
        print("\n✅ Limpieza completada")
    else:
        print("\n📌 Archivos originales conservados")


if __name__ == "__main__":
    migrate_existing_data()