#!/usr/bin/env python3
"""
Script para configurar los nuevos usuarios jalcazar y aurbaez
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from user_data_manager import UserDataManager

def setup_new_users():
    """Configura los nuevos usuarios en el sistema"""
    
    print("\n🔧 CONFIGURACIÓN DE NUEVOS USUARIOS")
    print("=" * 50)
    
    # Hash de la contraseña
    password = "Profitz2025!"
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Usuarios a crear
    new_users = {
        "jalcazar": {
            "password_hash": password_hash,
            "role": "trader",
            "full_name": "J. Alcazar",
            "created": datetime.now().isoformat()
        },
        "aurbaez": {
            "password_hash": password_hash,
            "role": "admin",
            "full_name": "A. Urbaez",
            "created": datetime.now().isoformat()
        }
    }
    
    # 1. Actualizar auth_config.json
    print("\n📝 Actualizando configuración de autenticación...")
    
    config_file = Path("auth_config.json")
    
    # Cargar configuración existente o crear nueva
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        config = {
            "users": {},
            "created": datetime.now().isoformat()
        }
    
    # Agregar nuevos usuarios
    for username, user_data in new_users.items():
        config["users"][username] = user_data["password_hash"]
        print(f"  ✅ Usuario agregado: {username} (Rol: {user_data['role']})")
    
    # Guardar configuración actualizada
    config["last_updated"] = datetime.now().isoformat()
    config["note"] = "Usuarios actualizados con jalcazar y aurbaez"
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n📁 Creando estructura de datos para cada usuario...")
    
    # 2. Inicializar datos para cada usuario
    manager = UserDataManager()
    
    for username, user_data in new_users.items():
        print(f"\n👤 Configurando: {username}")
        
        # Crear directorio del usuario
        user_dir = manager.base_dir / username
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración personalizada según rol
        if user_data["role"] == "admin":
            # Configuración para aurbaez (admin)
            initial_data = {
                "portfolio.json": {
                    "balance": 15000,  # Admin empieza con más capital
                    "currency": "USDT",
                    "created": datetime.now().isoformat(),
                    "user": username,
                    "role": "admin"
                },
                "bot_config.json": {
                    "scan_interval": 300,  # 5 minutos - más agresivo
                    "stop_loss": 2.5,
                    "take_profit": 5.0,
                    "max_trades": 5,  # Más trades simultáneos
                    "risk_per_trade": 0.03,  # 3% del capital
                    "symbols": [
                        "BTC-USD", "ETH-USD", "SOL-USD",
                        "ADA-USD", "DOGE-USD", "XRP-USD",
                        "AVAX-USD", "DOT-USD"  # Más símbolos
                    ],
                    "auto_trade": True,
                    "advanced_mode": True
                }
            }
        else:
            # Configuración para jalcazar (trader)
            initial_data = {
                "portfolio.json": {
                    "balance": 10000,  # Capital estándar
                    "currency": "USDT",
                    "created": datetime.now().isoformat(),
                    "user": username,
                    "role": "trader"
                },
                "bot_config.json": {
                    "scan_interval": 600,  # 10 minutos - conservador
                    "stop_loss": 2.0,
                    "take_profit": 3.5,
                    "max_trades": 3,
                    "risk_per_trade": 0.02,  # 2% del capital
                    "symbols": [
                        "BTC-USD", "ETH-USD", "SOL-USD",
                        "ADA-USD"  # Menos símbolos, más enfocado
                    ],
                    "auto_trade": False,
                    "advanced_mode": False
                }
            }
        
        # Datos comunes para ambos usuarios
        common_data = {
            "active_trades.json": [],
            "trade_history.json": [],
            "system_state.json": {
                "is_running": False,
                "last_scan": None,
                "total_trades": 0,
                "successful_trades": 0,
                "failed_trades": 0,
                "created_by": "setup_script",
                "created_at": datetime.now().isoformat()
            },
            "user_settings.json": {
                "notifications": True,
                "theme": "dark",
                "timezone": "America/New_York",
                "email_alerts": False,
                "telegram_alerts": False,
                "display_currency": "USD",
                "language": "es"
            },
            "trading_access_log.json": [{
                "timestamp": datetime.now().isoformat(),
                "action": "account_created",
                "details": f"Cuenta creada para {username}"
            }]
        }
        
        # Combinar datos específicos del rol con datos comunes
        all_data = {**initial_data, **common_data}
        
        # Crear archivos
        for filename, content in all_data.items():
            filepath = user_dir / filename
            with open(filepath, 'w') as f:
                json.dump(content, f, indent=2)
            print(f"  ✅ Creado: {filename}")
    
    # 3. Resumen de configuración
    print("\n" + "=" * 50)
    print("✅ CONFIGURACIÓN COMPLETADA")
    print("\n📊 Resumen de usuarios creados:")
    print("-" * 40)
    
    print(f"""
    👤 jalcazar (Trader)
       • Contraseña: Profitz2025!
       • Balance: $10,000 USDT
       • Máx trades: 3
       • Riesgo/trade: 2%
       • Símbolos: 4 (BTC, ETH, SOL, ADA)
       • Modo: Conservador
    
    👤 aurbaez (Admin)
       • Contraseña: Profitz2025!
       • Balance: $15,000 USDT
       • Máx trades: 5
       • Riesgo/trade: 3%
       • Símbolos: 8 (incluye AVAX, DOT)
       • Modo: Agresivo
       • Permisos: Acceso total
    """)
    
    print("\n🚀 Los usuarios están listos para usar el sistema")
    print("   Ejecuta: streamlit run login_dashboard.py")
    
    # 4. Verificación rápida
    print("\n🔍 Verificando archivos creados...")
    
    for username in ["jalcazar", "aurbaez"]:
        user_dir = Path("users") / username
        if user_dir.exists():
            files = list(user_dir.glob("*.json"))
            print(f"  ✅ {username}: {len(files)} archivos creados")
        else:
            print(f"  ❌ Error: No se encontró el directorio de {username}")
    
    # Verificar auth_config.json
    if config_file.exists():
        with open(config_file, 'r') as f:
            final_config = json.load(f)
            users_in_config = list(final_config.get("users", {}).keys())
            print(f"\n  ✅ Usuarios en auth_config.json: {', '.join(users_in_config)}")
    
    return True


if __name__ == "__main__":
    success = setup_new_users()
    
    if success:
        print("\n" + "=" * 50)
        print("✨ Todo listo para iniciar el sistema!")
        print("\nPuedes probar el login con:")
        print("  • jalcazar / Profitz2025!")
        print("  • aurbaez / Profitz2025!")
    else:
        print("\n❌ Hubo errores durante la configuración")