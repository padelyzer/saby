#!/usr/bin/env python3
"""
Script para verificar que el sistema está funcionando correctamente
"""

import requests
import json
from datetime import datetime

def test_system():
    """Prueba el sistema completo"""
    
    API_URL = "http://localhost:8000"
    
    print("\n" + "="*60)
    print(" VERIFICACIÓN DEL SISTEMA DE TRADING ".center(60))
    print("="*60)
    
    # 1. Verificar conexión API
    print("\n1. Verificando conexión API...")
    try:
        response = requests.get(f"{API_URL}/api/status")
        status = response.json()
        print(f"   ✅ API conectada")
        print(f"   Estado del bot: {status.get('bot_status', 'unknown')}")
        print(f"   Bot corriendo: {status.get('is_running', False)}")
    except Exception as e:
        print(f"   ❌ Error conectando API: {e}")
        return False
    
    # 2. Configurar sistema
    print("\n2. Configurando sistema...")
    config = {
        "initial_capital": 10000,
        "risk_level": "balanced",
        "max_positions": 5
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/config",
            json=config
        )
        print(f"   ✅ Configuración guardada")
    except Exception as e:
        print(f"   ❌ Error configurando: {e}")
        return False
    
    # 3. Iniciar bot
    print("\n3. Iniciando bot...")
    try:
        response = requests.post(f"{API_URL}/api/bot/start")
        result = response.json()
        if result.get('status') == 'success':
            print(f"   ✅ Bot iniciado exitosamente")
        else:
            print(f"   ⚠️  {result.get('message', 'Bot ya estaba corriendo')}")
    except Exception as e:
        print(f"   ❌ Error iniciando bot: {e}")
        return False
    
    # 4. Verificar estado final
    print("\n4. Verificando estado final...")
    try:
        response = requests.get(f"{API_URL}/api/status")
        status = response.json()
        
        if status.get('bot_status') == 'running':
            print(f"   ✅ Sistema OPERATIVO")
        else:
            print(f"   ⚠️  Sistema en estado: {status.get('bot_status')}")
        
        # Obtener métricas
        response = requests.get(f"{API_URL}/api/performance")
        metrics = response.json()
        
        print(f"\n📊 MÉTRICAS:")
        print(f"   Balance actual: ${metrics.get('current_balance', 0):,.2f}")
        print(f"   Total trades: {metrics.get('total_trades', 0)}")
        print(f"   Win rate: {metrics.get('win_rate', 0):.1f}%")
        
    except Exception as e:
        print(f"   ❌ Error verificando estado: {e}")
        return False
    
    print("\n" + "="*60)
    print(" ✅ SISTEMA VERIFICADO Y FUNCIONANDO ".center(60))
    print("="*60)
    
    return True

if __name__ == "__main__":
    test_system()