#!/usr/bin/env python3
"""
Test del nuevo sistema de clasificación de activos y estrategias
"""

import json
from datetime import datetime
from backtest_system_v2 import BacktestSystemV2
from trading_config import (
    TRADING_SYMBOLS, get_asset_type, get_strategy_config, 
    get_recommended_strategies, ASSET_TYPES, STRATEGY_CONFIG
)

def test_asset_classification():
    """Test de clasificación de activos"""
    
    print("🔍 PRUEBA DE CLASIFICACIÓN DE ACTIVOS")
    print("="*50)
    
    for symbol in TRADING_SYMBOLS:
        asset_type = get_asset_type(symbol)
        recommended = get_recommended_strategies(symbol)
        
        print(f"\n📊 {symbol}:")
        print(f"   Tipo: {asset_type}")
        print(f"   Estrategias recomendadas: {recommended}")
        
        # Test configuraciones específicas
        for strategy in recommended:
            config = get_strategy_config(strategy, symbol)
            print(f"   {strategy}: {config}")

def test_volume_breakout_strategy():
    """Test específico de la estrategia Volume Breakout"""
    
    print("\n🚀 PRUEBA DE ESTRATEGIA VOLUME BREAKOUT")
    print("="*50)
    
    backtest = BacktestSystemV2()
    
    # Test con diferentes tipos de activos
    test_symbols = ['DOGEUSDT', 'SOLUSDT', 'LINKUSDT']  # MEME, LARGE_CAP, UTILITY
    
    for symbol in test_symbols:
        asset_type = get_asset_type(symbol)
        config = get_strategy_config('volume_breakout', symbol)
        
        print(f"\n📈 Testing {symbol} ({asset_type}):")
        print(f"   Config: {config}")
        
        try:
            result = backtest.run_backtest(
                symbol=symbol,
                strategy="volume_breakout",
                interval="1h",
                days_back=7
            )
            
            if result['success']:
                metrics = result['metrics']
                print(f"   ✅ Return: {metrics['total_return']:.2f}%")
                print(f"   ✅ Win Rate: {metrics['win_rate']:.1f}%")
                print(f"   ✅ Trades: {metrics['total_trades']}")
            else:
                print(f"   ❌ Error: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

def test_optimal_strategy_selection():
    """Test de selección automática de estrategia óptima"""
    
    print("\n🎯 PRUEBA DE SELECCIÓN ÓPTIMA DE ESTRATEGIA")
    print("="*50)
    
    backtest = BacktestSystemV2()
    
    # Test con cada tipo de activo
    test_symbols = ['DOGEUSDT', 'SOLUSDT', 'LINKUSDT']
    
    for symbol in test_symbols:
        asset_type = get_asset_type(symbol)
        
        print(f"\n🔎 Optimizando estrategia para {symbol} ({asset_type}):")
        
        try:
            result = backtest.run_optimal_strategy_backtest(
                symbol=symbol,
                interval="1h",
                days_back=7
            )
            
            print(f"   Estrategias probadas: {result['strategies_tested']}")
            print(f"   Mejor estrategia: {result['best_strategy']}")
            print(f"   Score: {result['best_score']:.3f}")
            
            if result['best_result']:
                metrics = result['best_result']['metrics']
                print(f"   Return: {metrics['total_return']:.2f}%")
                print(f"   Win Rate: {metrics['win_rate']:.1f}%")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def generate_comparison_report():
    """Genera reporte comparativo de estrategias por activo"""
    
    print("\n📊 REPORTE COMPARATIVO DE ESTRATEGIAS")
    print("="*60)
    
    backtest = BacktestSystemV2()
    report = {
        'timestamp': datetime.now().isoformat(),
        'comparison': {}
    }
    
    for symbol in TRADING_SYMBOLS[:3]:  # Solo 3 para el test
        asset_type = get_asset_type(symbol)
        
        print(f"\n📈 Analizando {symbol} ({asset_type})...")
        
        try:
            result = backtest.run_optimal_strategy_backtest(
                symbol=symbol,
                interval="1h", 
                days_back=7
            )
            
            report['comparison'][symbol] = {
                'asset_type': asset_type,
                'best_strategy': result['best_strategy'],
                'best_score': result['best_score'],
                'strategies_performance': {}
            }
            
            # Extraer performance de cada estrategia
            for strategy, strategy_result in result['all_results'].items():
                if strategy_result['success']:
                    metrics = strategy_result['metrics']
                    report['comparison'][symbol]['strategies_performance'][strategy] = {
                        'return': metrics['total_return'],
                        'win_rate': metrics['win_rate'],
                        'sharpe': metrics['sharpe_ratio'],
                        'score': strategy_result.get('optimization_score', 0)
                    }
            
            print(f"   ✅ Mejor: {result['best_strategy']} (Score: {result['best_score']:.3f})")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            report['comparison'][symbol] = {'error': str(e)}
    
    # Guardar reporte
    with open('asset_strategy_comparison.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Reporte guardado en: asset_strategy_comparison.json")
    
    return report

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS DEL SISTEMA DE CLASIFICACIÓN DE ACTIVOS")
    print("="*70)
    
    # 1. Test clasificación básica
    test_asset_classification()
    
    # 2. Test estrategia Volume Breakout
    test_volume_breakout_strategy()
    
    # 3. Test selección óptima
    test_optimal_strategy_selection()
    
    # 4. Generar reporte comparativo
    report = generate_comparison_report()
    
    print("\n✅ TODAS LAS PRUEBAS COMPLETADAS")
    print(f"Revisa el archivo asset_strategy_comparison.json para resultados detallados")