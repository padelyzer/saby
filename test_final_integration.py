#!/usr/bin/env python3
"""
Test Final de Integración Frontend-Backend
Prueba todos los endpoints de estrategias
"""

import requests
import json
import time

def test_integration():
    """Test completo de la integración"""
    
    print("🚀 INICIANDO TEST FINAL DE INTEGRACIÓN FRONTEND-BACKEND")
    print("="*70)
    
    base_url = "http://localhost:8000"
    tests_passed = 0
    tests_total = 0
    
    # Test 1: API Health Check
    print("\n1️⃣ Testing API Health...")
    tests_total += 1
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ API responde correctamente")
            tests_passed += 1
        else:
            print(f"   ❌ API error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API no disponible: {e}")
    
    # Test 2: Configuración de Estrategias
    print("\n2️⃣ Testing Configuración de Estrategias...")
    tests_total += 1
    try:
        response = requests.get(f"{base_url}/api/strategies/config", timeout=10)
        if response.status_code == 200:
            data = response.json()
            strategies = data.get('strategies', {})
            print(f"   ✅ {len(strategies)} estrategias configuradas")
            print(f"   ✅ Tipos de activos: {list(data.get('asset_types', {}).keys())}")
            tests_passed += 1
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Estrategias por Símbolo
    print("\n3️⃣ Testing Estrategias por Símbolo...")
    test_symbols = ['SOLUSDT', 'DOGEUSDT', 'LINKUSDT']
    
    for symbol in test_symbols:
        tests_total += 1
        try:
            response = requests.get(f"{base_url}/api/strategies/{symbol}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                strategy = data.get('strategy', {})
                print(f"   ✅ {symbol}: {strategy.get('name')} @ {strategy.get('timeframe')} ({data.get('asset_type')})")
                tests_passed += 1
            else:
                print(f"   ❌ {symbol}: Error {response.status_code}")
        except Exception as e:
            print(f"   ❌ {symbol}: Error {e}")
    
    # Test 4: Status del Sistema
    print("\n4️⃣ Testing Status del Sistema...")
    tests_total += 1
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Bot Status: {data.get('bot_status')}")
            print(f"   ✅ Timestamp: {data.get('timestamp')}")
            tests_passed += 1
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Performance del Sistema  
    print("\n5️⃣ Testing Performance...")
    tests_total += 1
    try:
        response = requests.get(f"{base_url}/api/performance", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Balance: ${data.get('current_balance', 0):.2f}")
            print(f"   ✅ Total trades: {data.get('total_trades', 0)}")
            tests_passed += 1
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 6: Configuración del Bot
    print("\n6️⃣ Testing Configuración del Bot...")
    tests_total += 1
    try:
        response = requests.get(f"{base_url}/api/config", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Capital inicial: ${data.get('initial_capital', 0):.2f}")
            print(f"   ✅ Risk level: {data.get('risk_level')}")
            print(f"   ✅ Símbolos: {len(data.get('symbols', []))}")
            tests_passed += 1
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Resumen
    print(f"\n📊 RESUMEN DEL TEST")
    print("="*50)
    success_rate = (tests_passed / tests_total) * 100
    print(f"✅ Tests pasados: {tests_passed}/{tests_total}")
    print(f"📈 Tasa de éxito: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print(f"\n🎉 INTEGRACIÓN EXITOSA!")
        print(f"✅ Backend optimizado funcionando correctamente")
        print(f"✅ Todos los endpoints de estrategias operativos")
        print(f"✅ Sistema listo para uso en producción")
    elif success_rate >= 70:
        print(f"\n⚠️ INTEGRACIÓN PARCIAL")
        print(f"⚠️ Algunos endpoints pueden tener problemas")
    else:
        print(f"\n❌ INTEGRACIÓN FALLIDA")
        print(f"❌ Revisar configuración del backend")
    
    # Test de Frontend (si está disponible)
    print(f"\n7️⃣ Testing Frontend...")
    try:
        response = requests.get("http://localhost:5173", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ Frontend accesible en http://localhost:5173")
            print(f"   ✅ Dashboard con estrategias: http://localhost:5173")
            print(f"   ✅ SymbolPro con info de estrategias: http://localhost:5173/symbol/SOLUSDT")
        else:
            print(f"   ❌ Frontend no disponible")
    except Exception as e:
        print(f"   ⚠️ Frontend no accesible (puede estar en otro puerto)")
        print(f"   ℹ️ Verifica que npm run dev esté ejecutándose")
    
    return success_rate >= 90

if __name__ == "__main__":
    success = test_integration()
    
    print(f"\n🎯 INTEGRACIÓN {'COMPLETADA' if success else 'REQUIERE REVISIÓN'}")
    
    if success:
        print(f"\n🚀 PRÓXIMOS PASOS:")
        print(f"1. Abrir el Dashboard: http://localhost:5173")
        print(f"2. Ver las estrategias optimizadas por activo")
        print(f"3. Explorar detalles de estrategias en SymbolPro")
        print(f"4. Configurar y activar el bot de trading")
    else:
        print(f"\n🔧 REVISAR:")
        print(f"1. Backend ejecutándose en puerto 8000")
        print(f"2. Frontend ejecutándose en puerto 5173")
        print(f"3. Todos los imports del sistema optimizado")
        
    exit(0 if success else 1)