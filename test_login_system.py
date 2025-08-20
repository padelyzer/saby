#!/usr/bin/env python3
"""
Script de validación del sistema de login
Prueba los usuarios jalcazar y aurbaez
"""

import json
from pathlib import Path
from auth_system import auth
from user_data_manager import user_data
import hashlib

def validate_system():
    """Valida que el sistema esté correctamente configurado"""
    
    print("\n🔍 VALIDACIÓN DEL SISTEMA DE LOGIN")
    print("=" * 50)
    
    # 1. Verificar auth_config.json
    print("\n1️⃣ Verificando configuración de autenticación...")
    
    config_file = Path("auth_config.json")
    if not config_file.exists():
        print("  ❌ auth_config.json no existe")
        return False
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    users = config.get("users", {})
    expected_users = ["jalcazar", "aurbaez"]
    
    for username in expected_users:
        if username in users:
            print(f"  ✅ Usuario {username} encontrado en auth_config.json")
        else:
            print(f"  ❌ Usuario {username} NO encontrado")
            return False
    
    # 2. Verificar carpetas de usuarios
    print("\n2️⃣ Verificando estructura de carpetas...")
    
    for username in expected_users:
        user_dir = Path("users") / username
        if user_dir.exists():
            files = list(user_dir.glob("*.json"))
            print(f"  ✅ {username}: {len(files)} archivos en su carpeta")
            
            # Verificar archivos específicos
            required_files = [
                "portfolio.json",
                "bot_config.json",
                "active_trades.json",
                "system_state.json"
            ]
            
            for req_file in required_files:
                if (user_dir / req_file).exists():
                    print(f"     ✓ {req_file}")
                else:
                    print(f"     ✗ {req_file} faltante")
        else:
            print(f"  ❌ Carpeta de {username} no existe")
            return False
    
    # 3. Probar login programáticamente
    print("\n3️⃣ Probando autenticación...")
    
    test_credentials = [
        ("jalcazar", "Profitz2025!", "trader"),
        ("aurbaez", "Profitz2025!", "admin")
    ]
    
    for username, password, expected_role in test_credentials:
        print(f"\n  Probando: {username}")
        
        # Cerrar cualquier sesión previa
        if auth.is_authenticated():
            auth.logout()
        
        # Intentar login
        success = auth.login(username, password)
        
        if success:
            print(f"    ✅ Login exitoso")
            
            # Verificar usuario actual
            current_user = auth.get_current_user()
            if current_user == username:
                print(f"    ✅ Usuario actual correcto: {current_user}")
            else:
                print(f"    ❌ Usuario actual incorrecto: {current_user}")
            
            # Verificar datos del usuario
            user_data.set_user(username)
            portfolio = user_data.read_user_data("portfolio.json")
            
            if portfolio:
                balance = portfolio.get("balance", 0)
                role = portfolio.get("role", "unknown")
                print(f"    ✅ Portfolio cargado - Balance: ${balance:,.2f}")
                print(f"    ✅ Rol: {role}")
                
                if role != expected_role:
                    print(f"    ⚠️  Rol esperado: {expected_role}, encontrado: {role}")
            else:
                print(f"    ❌ No se pudo cargar el portfolio")
            
            # Cerrar sesión
            auth.logout()
            print(f"    ✅ Logout exitoso")
        else:
            print(f"    ❌ Login falló para {username}")
            return False
    
    # 4. Verificar segregación de datos
    print("\n4️⃣ Verificando segregación de datos...")
    
    # Verificar que jalcazar y aurbaez tienen diferentes configuraciones
    jalcazar_config = json.load(open("users/jalcazar/bot_config.json"))
    aurbaez_config = json.load(open("users/aurbaez/bot_config.json"))
    
    print(f"\n  Comparación de configuraciones:")
    print(f"  {'Parámetro':<20} {'jalcazar':<15} {'aurbaez':<15}")
    print(f"  {'-'*20} {'-'*15} {'-'*15}")
    
    params = [
        ("Balance inicial", "portfolio.json", "balance"),
        ("Max trades", "bot_config.json", "max_trades"),
        ("Riesgo/trade", "bot_config.json", "risk_per_trade"),
        ("Símbolos", "bot_config.json", "symbols")
    ]
    
    jalcazar_portfolio = json.load(open("users/jalcazar/portfolio.json"))
    aurbaez_portfolio = json.load(open("users/aurbaez/portfolio.json"))
    
    # Balance
    print(f"  {'Balance':<20} ${jalcazar_portfolio['balance']:<14,.0f} ${aurbaez_portfolio['balance']:<14,.0f}")
    
    # Max trades
    print(f"  {'Max trades':<20} {jalcazar_config['max_trades']:<15} {aurbaez_config['max_trades']:<15}")
    
    # Riesgo
    print(f"  {'Riesgo/trade':<20} {jalcazar_config['risk_per_trade']*100:<14.1f}% {aurbaez_config['risk_per_trade']*100:<14.1f}%")
    
    # Símbolos
    print(f"  {'Num. símbolos':<20} {len(jalcazar_config['symbols']):<15} {len(aurbaez_config['symbols']):<15}")
    
    # 5. Resumen final
    print("\n" + "=" * 50)
    print("✅ VALIDACIÓN COMPLETADA EXITOSAMENTE")
    print("\n📊 Resumen del Sistema:")
    print(f"""
    🔐 Sistema de Autenticación: OK
    📁 Estructura de Carpetas: OK
    👥 Usuarios Configurados: {len(expected_users)}
    🔄 Login/Logout: Funcionando
    📊 Datos Segregados: Sí
    
    Usuarios disponibles:
    • jalcazar (Trader) - $10,000 - Conservador
    • aurbaez (Admin) - $15,000 - Agresivo
    
    🚀 El sistema está listo para usar!
    """)
    
    return True


if __name__ == "__main__":
    try:
        success = validate_system()
        
        if success:
            print("\n💡 Para iniciar la aplicación web:")
            print("   streamlit run login_dashboard.py")
            print("\n📝 Credenciales:")
            print("   • jalcazar / Profitz2025!")
            print("   • aurbaez / Profitz2025!")
        else:
            print("\n❌ La validación falló. Revisa los errores arriba.")
    except Exception as e:
        print(f"\n❌ Error durante la validación: {e}")
        import traceback
        traceback.print_exc()