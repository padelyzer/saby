#!/usr/bin/env python3
"""
Script de prueba para el sistema de autenticación
"""

from auth_system import auth, require_login
import time


# Función de ejemplo protegida
@require_login
def funcion_protegida():
    """Esta función requiere autenticación"""
    print("✅ Has accedido a una función protegida!")
    print(f"   Usuario actual: {auth.get_current_user()}")
    return "Operación exitosa"


# Función de ejemplo sin protección
def funcion_publica():
    """Esta función es pública"""
    print("Esta es una función pública, no requiere autenticación")
    return "Información pública"


def test_auth_system():
    """Prueba el sistema de autenticación"""
    print("\n🔧 TEST DEL SISTEMA DE AUTENTICACIÓN")
    print("=" * 50)
    
    # Test 1: Función pública
    print("\n1. Probando función pública:")
    resultado = funcion_publica()
    print(f"   Resultado: {resultado}")
    
    # Test 2: Función protegida (debería pedir login)
    print("\n2. Probando función protegida:")
    resultado = funcion_protegida()
    if resultado:
        print(f"   Resultado: {resultado}")
    
    # Test 3: Verificar estado de sesión
    print("\n3. Verificando estado de sesión:")
    if auth.is_authenticated():
        print(f"   ✅ Sesión activa para: {auth.get_current_user()}")
    else:
        print("   ❌ No hay sesión activa")
    
    # Test 4: Segunda llamada a función protegida (no debería pedir login)
    print("\n4. Segunda llamada a función protegida:")
    resultado = funcion_protegida()
    
    # Test 5: Logout
    print("\n5. Cerrando sesión:")
    auth.logout()
    
    # Test 6: Intentar acceder después del logout
    print("\n6. Intentando acceder después del logout:")
    resultado = funcion_protegida()
    
    print("\n" + "=" * 50)
    print("✅ Pruebas completadas")


if __name__ == "__main__":
    test_auth_system()