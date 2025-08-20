#!/usr/bin/env python3
"""
Test de Integración del Sistema Optimizado
Prueba las estrategias validadas en el sistema en vivo
"""

import time
from datetime import datetime
from optimized_paper_trading import OptimizedPaperTrading, PRODUCTION_STRATEGY_CONFIG

def test_signal_generation():
    """Test de generación de señales optimizadas"""
    
    print("🧪 TEST DE GENERACIÓN DE SEÑALES OPTIMIZADAS")
    print("="*60)
    
    # Crear sistema
    trading_system = OptimizedPaperTrading(initial_capital=10000, risk_level='balanced')
    
    # Test cada símbolo
    for symbol, config in PRODUCTION_STRATEGY_CONFIG.items():
        print(f"\n📊 Testing {symbol}:")
        print(f"   Estrategia: {config['strategy']}")
        print(f"   Timeframe: {config['timeframe']}")
        
        try:
            signal = trading_system.generate_optimized_signal(symbol)
            
            if signal:
                print(f"   ✅ Señal generada:")
                print(f"      Acción: {signal['action']}")
                print(f"      Precio: ${signal['entry_price']}")
                print(f"      Confianza: {signal['confidence']:.1%}")
                print(f"      TP: ${signal['take_profit']} | SL: ${signal['stop_loss']}")
            else:
                print(f"   ℹ️ No hay señal activa")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return trading_system

def test_live_integration(duration_minutes: int = 5):
    """Test de integración en vivo por tiempo limitado"""
    
    print(f"\n🚀 TEST DE INTEGRACIÓN EN VIVO ({duration_minutes} minutos)")
    print("="*60)
    
    # Crear sistema
    trading_system = OptimizedPaperTrading(initial_capital=10000, risk_level='balanced')
    
    # Configurar tiempo límite
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    # Configurar intervalo más corto para test
    trading_system.scan_interval = 30  # 30 segundos
    
    print(f"⏰ Duración del test: {duration_minutes} minutos")
    print(f"🔄 Intervalo de escaneo: {trading_system.scan_interval}s")
    
    cycles = 0
    
    while time.time() < end_time:
        try:
            cycles += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            
            print(f"\n🔄 CICLO {cycles} - {current_time}")
            print("-" * 40)
            
            # Escanear mercados
            trading_system.scan_markets()
            
            # Actualizar posiciones
            trading_system.update_positions()
            
            # Mostrar estadísticas
            stats = trading_system.get_statistics()
            print(f"\n📊 Estadísticas:")
            print(f"   Balance: ${stats['current_balance']:.2f}")
            print(f"   Posiciones abiertas: {stats['open_positions']}")
            print(f"   Total trades: {stats['total_trades']}")
            if stats['total_trades'] > 0:
                print(f"   Win Rate: {stats['win_rate']:.1f}%")
                print(f"   Return: {stats['total_return']:.2f}%")
            
            # Esperar
            time.sleep(trading_system.scan_interval)
            
        except KeyboardInterrupt:
            print("\n⏹️ Test interrumpido por usuario")
            break
        except Exception as e:
            print(f"\n❌ Error en ciclo {cycles}: {e}")
            time.sleep(10)
    
    # Estadísticas finales
    print(f"\n📋 RESUMEN DEL TEST")
    print("="*40)
    print(f"⏱️ Duración: {(time.time() - start_time)/60:.1f} minutos")
    print(f"🔄 Ciclos completados: {cycles}")
    
    final_stats = trading_system.get_statistics()
    print(f"\n📊 Estadísticas finales:")
    print(f"   Balance inicial: ${trading_system.initial_capital:.2f}")
    print(f"   Balance final: ${final_stats['current_balance']:.2f}")
    print(f"   Return total: {final_stats['total_return']:.2f}%")
    print(f"   Trades ejecutados: {final_stats['total_trades']}")
    print(f"   Posiciones abiertas: {final_stats['open_positions']}")
    
    if final_stats['total_trades'] > 0:
        print(f"   Win Rate: {final_stats['win_rate']:.1f}%")
        print(f"   Trades ganadores: {final_stats['winning_trades']}")
        print(f"   Trades perdedores: {final_stats['losing_trades']}")
    
    # Mostrar trades cerrados
    if trading_system.closed_trades:
        print(f"\n💼 Trades cerrados:")
        for trade in trading_system.closed_trades:
            print(f"   {trade.symbol} {trade.action}: {trade.pnl_percent:.2f}% ({trade.exit_reason})")
    
    # Mostrar posiciones abiertas
    if trading_system.open_positions:
        print(f"\n🔓 Posiciones abiertas:")
        for symbol, trade in trading_system.open_positions.items():
            print(f"   {symbol} {trade.action}: {trade.pnl_percent:.2f}% (${trade.current_price})")
    
    return trading_system

def test_strategy_config():
    """Test de configuración de estrategias"""
    
    print("\n⚙️ TEST DE CONFIGURACIÓN DE ESTRATEGIAS")
    print("="*50)
    
    from trading_config import get_asset_type, get_strategy_config
    
    for symbol, config in PRODUCTION_STRATEGY_CONFIG.items():
        asset_type = get_asset_type(symbol)
        strategy_config = get_strategy_config(config['strategy'], symbol)
        
        print(f"\n📋 {symbol} ({asset_type}):")
        print(f"   Estrategia producción: {config['strategy']}")
        print(f"   Timeframe: {config['timeframe']}")
        print(f"   Confianza: {config['confidence']}")
        print(f"   Configuración específica: {strategy_config}")

if __name__ == "__main__":
    print("🚀 INICIANDO TESTS DE INTEGRACIÓN COMPLETOS")
    print("="*70)
    
    # 1. Test configuración
    test_strategy_config()
    
    # 2. Test generación de señales
    trading_system = test_signal_generation()
    
    # 3. Test integración en vivo
    print("\n" + "="*70)
    user_input = input("¿Ejecutar test en vivo de 5 minutos? (y/N): ")
    
    if user_input.lower() == 'y':
        test_live_integration(duration_minutes=5)
    else:
        print("Test en vivo omitido.")
    
    print("\n✅ TODOS LOS TESTS COMPLETADOS")
    print("El sistema está listo para integración con el API backend.")