#!/usr/bin/env python3
"""
Validación End-to-End Final del Sistema de Trading
"""

import json
import time
import requests
from datetime import datetime

def test_full_trading_workflow():
    """Test completo del flujo de trading"""
    
    print("🚀 VALIDACIÓN END-TO-END FINAL")
    print("="*50)
    
    results = {}
    api_base = "http://localhost:8000"
    
    # 1. Verificar API status
    print("\n1️⃣ Verificando API status...")
    try:
        response = requests.get(f"{api_base}/api/status", timeout=5)
        if response.status_code == 200:
            print("✅ API operativa")
            results['api_status'] = True
        else:
            print("❌ API no responde")
            results['api_status'] = False
    except:
        print("❌ API no disponible")
        results['api_status'] = False
        return results
    
    # 2. Verificar símbolos y datos de mercado
    print("\n2️⃣ Verificando datos de mercado...")
    symbol = "SOLUSDT"
    try:
        response = requests.get(f"{api_base}/api/symbol/{symbol}/data", timeout=10)
        if response.status_code == 200:
            data = response.json()
            price = data.get('current_price', 0)
            print(f"✅ Datos de {symbol}: ${price:.2f}")
            results['market_data'] = True
        else:
            print("❌ Error obteniendo datos de mercado")
            results['market_data'] = False
    except Exception as e:
        print(f"❌ Error: {e}")
        results['market_data'] = False
    
    # 3. Verificar señales
    print("\n3️⃣ Verificando señales...")
    try:
        response = requests.get(f"{api_base}/api/signals/{symbol}", timeout=10)
        if response.status_code == 200:
            signals = response.json()
            if signals.get('signal'):
                action = signals['signal']['action']
                confidence = signals['signal']['confidence']
                print(f"✅ Señal disponible: {action} (confianza: {confidence:.2f})")
                results['signals'] = True
            else:
                print("ℹ️ No hay señales activas (normal)")
                results['signals'] = True
        else:
            print("❌ Error obteniendo señales")
            results['signals'] = False
    except Exception as e:
        print(f"❌ Error: {e}")
        results['signals'] = False
    
    # 4. Verificar backtest
    print("\n4️⃣ Ejecutando backtest rápido...")
    try:
        response = requests.post(
            f"{api_base}/api/backtest/{symbol}",
            json={"period_days": 3},
            timeout=15
        )
        if response.status_code == 200:
            backtest_data = response.json()
            signals_count = len(backtest_data.get('signals', []))
            print(f"✅ Backtest ejecutado: {signals_count} señales históricas")
            results['backtest'] = True
        else:
            print("❌ Error en backtest")
            results['backtest'] = False
    except Exception as e:
        print(f"❌ Error: {e}")
        results['backtest'] = False
    
    # 5. Verificar estadísticas de mercado
    print("\n5️⃣ Verificando estadísticas de mercado...")
    try:
        response = requests.get(f"{api_base}/api/market/{symbol}/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            rsi = stats.get('rsi', 0)
            trend = stats.get('trend', 'unknown')
            print(f"✅ Stats: RSI {rsi:.1f}, Tendencia: {trend}")
            results['market_stats'] = True
        else:
            print("❌ Error obteniendo estadísticas")
            results['market_stats'] = False
    except Exception as e:
        print(f"❌ Error: {e}")
        results['market_stats'] = False
    
    # 6. Verificar configuración
    print("\n6️⃣ Verificando configuración...")
    try:
        response = requests.get(f"{api_base}/api/config", timeout=5)
        if response.status_code == 200:
            config = response.json()
            symbols = config.get('symbols', [])
            print(f"✅ Configuración: {len(symbols)} símbolos activos")
            results['config'] = True
        else:
            print("❌ Error obteniendo configuración")
            results['config'] = False
    except Exception as e:
        print(f"❌ Error: {e}")
        results['config'] = False
    
    # 7. Verificar performance del sistema
    print("\n7️⃣ Verificando performance...")
    try:
        response = requests.get(f"{api_base}/api/performance", timeout=5)
        if response.status_code == 200:
            perf = response.json()
            print(f"✅ Performance disponible")
            results['performance'] = True
        else:
            print("❌ Error obteniendo performance")
            results['performance'] = False
    except Exception as e:
        print(f"❌ Error: {e}")
        results['performance'] = False
    
    # 8. Test de latencia
    print("\n8️⃣ Midiendo latencia...")
    latencies = []
    for i in range(3):
        start = time.time()
        try:
            response = requests.get(f"{api_base}/api/status", timeout=5)
            if response.status_code == 200:
                latency = (time.time() - start) * 1000
                latencies.append(latency)
        except:
            pass
    
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        print(f"✅ Latencia promedio: {avg_latency:.1f}ms")
        results['latency'] = avg_latency
        results['latency_ok'] = avg_latency < 500  # Menos de 500ms
    else:
        print("❌ No se pudo medir latencia")
        results['latency_ok'] = False
    
    return results

def generate_final_report(results):
    """Genera reporte final del sistema"""
    
    print("\n" + "="*60)
    print("📊 REPORTE FINAL DEL SISTEMA")
    print("="*60)
    
    # Contar tests pasados
    test_keys = [
        'api_status', 'market_data', 'signals', 'backtest', 
        'market_stats', 'config', 'performance', 'latency_ok'
    ]
    
    passed = sum(1 for key in test_keys if results.get(key, False))
    total = len(test_keys)
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    print(f"\n✅ Tests Pasados: {passed}/{total}")
    print(f"📈 Tasa de Éxito: {success_rate:.1f}%")
    
    if 'latency' in results:
        print(f"⚡ Latencia Promedio: {results['latency']:.1f}ms")
    
    # Estado del sistema
    if success_rate >= 90:
        status = "🟢 SISTEMA COMPLETAMENTE OPERATIVO"
        recommendation = "Sistema listo para uso en producción"
    elif success_rate >= 75:
        status = "🟡 SISTEMA MAYORMENTE FUNCIONAL"
        recommendation = "Algunos componentes necesitan atención"
    else:
        status = "🔴 SISTEMA REQUIERE CORRECCIONES"
        recommendation = "Revisar componentes fallidos antes de usar"
    
    print(f"\n{status}")
    print(f"💡 Recomendación: {recommendation}")
    
    # Detalles por componente
    print(f"\n📋 Estado por Componente:")
    components = {
        'api_status': 'API Principal',
        'market_data': 'Datos de Mercado',
        'signals': 'Sistema de Señales',
        'backtest': 'Sistema de Backtest',
        'market_stats': 'Estadísticas de Mercado',
        'config': 'Configuración',
        'performance': 'Métricas de Performance',
        'latency_ok': 'Latencia Aceptable'
    }
    
    for key, name in components.items():
        status_emoji = "✅" if results.get(key, False) else "❌"
        print(f"  {status_emoji} {name}")
    
    # Timestamp
    print(f"\n🕐 Validación completada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Guardar reporte
    report = {
        'timestamp': datetime.now().isoformat(),
        'success_rate': success_rate,
        'tests_passed': passed,
        'tests_total': total,
        'results': results,
        'status': status,
        'recommendation': recommendation
    }
    
    with open('final_validation_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Reporte guardado en: final_validation_report.json")
    
    return report

if __name__ == "__main__":
    # Ejecutar validación completa
    results = test_full_trading_workflow()
    
    # Generar reporte final
    report = generate_final_report(results)
    
    print(f"\n🎯 VALIDACIÓN END-TO-END COMPLETADA")
    print(f"Resultado: {report['success_rate']:.1f}% de éxito")
    
    # Exit code
    exit_code = 0 if report['success_rate'] >= 80 else 1
    exit(exit_code)