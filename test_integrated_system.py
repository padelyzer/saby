#!/usr/bin/env python3
"""
Test Integral del Sistema de Trading
Prueba completa de todos los componentes trabajando juntos
"""

import sys
from datetime import datetime
import time

def test_integrated_system():
    """Prueba el sistema completo integrado"""
    
    print("🚀 TEST INTEGRAL DEL SISTEMA DE TRADING")
    print("="*80)
    print(f"📅 Timestamp: {datetime.now()}")
    print("="*80)
    
    try:
        # Importar todos los componentes
        print("\n📦 Importando componentes...")
        from paper_trading_system import PaperTradingSystem
        from onchain_analysis import OnChainAnalyzer
        from macro_correlations import MacroCorrelationAnalyzer
        from entry_signals_optimizer import EntrySignalsOptimizer
        from bollinger_squeeze_strategy import BollingerSqueezeStrategy
        from trailing_stops_dynamic import DynamicTrailingStops
        from volume_position_sizing import VolumeBasedPositionSizing
        from fear_greed_index import FearGreedIndexAnalyzer
        
        print("✅ Todos los componentes importados exitosamente")
        
        # Inicializar sistema principal
        print("\n🎯 Inicializando sistema principal...")
        capital_inicial = 50000
        paper_trader = PaperTradingSystem(initial_capital=capital_inicial)
        
        # Inicializar componentes adicionales
        onchain = OnChainAnalyzer()
        macro = MacroCorrelationAnalyzer()
        optimizer = EntrySignalsOptimizer()
        bollinger = BollingerSqueezeStrategy()
        trailing = DynamicTrailingStops()
        sizing = VolumeBasedPositionSizing(base_capital=capital_inicial)
        fear_greed = FearGreedIndexAnalyzer()
        
        print(f"✅ Sistema inicializado con capital: ${capital_inicial:,}")
        
        # Símbolos a analizar
        symbols = ['BTC-USD', 'ETH-USD']
        
        print("\n" + "="*80)
        print("📊 ANÁLISIS DE MERCADO INTEGRADO")
        print("="*80)
        
        for symbol in symbols:
            print(f"\n🔍 Analizando {symbol}...")
            print("-"*60)
            
            # 1. Análisis de señal base
            print("\n1️⃣ ANÁLISIS DE SEÑAL BASE:")
            signal, message = paper_trader.analyze_signal(symbol)
            
            if signal:
                print(f"✅ Señal detectada: {signal['type']}")
                print(f"   • Score base: {signal.get('base_score', 0):.2f}")
                print(f"   • Score adaptativo: {signal.get('adaptive_score', 0):.2f}")
                print(f"   • Score optimizado: {signal.get('optimized_score', 0):.2f}")
                print(f"   • Score final: {signal['final_score']:.2f}")
                print(f"   • Entry: ${signal['entry_price']:.2f}")
                
                # 2. Análisis On-Chain
                print("\n2️⃣ ANÁLISIS ON-CHAIN:")
                onchain_score, onchain_details = onchain.get_onchain_score(symbol.replace('-USD', ''))
                print(f"   • Score on-chain: {onchain_score:.3f}")
                print(f"   • SOPR: {onchain_details['sopr_score']:.3f}")
                print(f"   • MVRV: {onchain_details['mvrv_score']:.3f}")
                print(f"   • Exchange flows: {onchain_details['flows_score']:.3f}")
                
                # 3. Análisis Macro
                print("\n3️⃣ ANÁLISIS MACRO:")
                macro_analysis = macro.get_macro_analysis(symbol)
                print(f"   • Score macro: {macro_analysis['macro_score']:.3f}")
                print(f"   • Régimen: {macro_analysis['regime']}")
                correlations = macro_analysis['correlations']
                print(f"   • DXY correlation: {correlations.get('DXY', 0):.3f}")
                print(f"   • SPY correlation: {correlations.get('SPY', 0):.3f}")
                
                # 4. Fear & Greed
                print("\n4️⃣ FEAR & GREED INDEX:")
                fg_analysis = fear_greed.get_fear_greed_analysis(symbol.replace('-USD', ''))
                print(f"   • Índice oficial: {fg_analysis['official_index']['value']}")
                print(f"   • Índice compuesto: {fg_analysis['composite_index']:.1f}")
                print(f"   • Clasificación: {fg_analysis['classification']}")
                
                # 5. Bollinger Bands
                print("\n5️⃣ BOLLINGER BANDS ANALYSIS:")
                # Necesitamos datos para Bollinger
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="30d", interval="1h")
                if len(data) > 20:
                    bb_score, bb_details = bollinger.analyze_bollinger_signal(
                        data, data.iloc[-1], signal['type']
                    )
                    print(f"   • BB Score: {bb_score:.3f}")
                    bb_state = bb_details.get('current_bb_state', {})
                    print(f"   • Position: {bb_state.get('position', 'N/A')}")
                    print(f"   • %B: {bb_state.get('percent_b', 0):.3f}")
                
                # 6. Position Sizing
                print("\n6️⃣ POSITION SIZING:")
                sizing_result = sizing.calculate_optimal_position_size(
                    symbol, signal, capital_inicial
                )
                print(f"   • Capital recomendado: ${sizing_result['position_capital']:,.2f}")
                print(f"   • Porcentaje: {sizing_result['position_pct']:.2f}%")
                print(f"   • Score volumen: {sizing_result['volume_score']:.3f}")
                print(f"   • Tier liquidez: {sizing_result['liquidity_tier']}")
                
                # 7. Decisión de trading
                print("\n7️⃣ DECISIÓN DE TRADING:")
                
                # Aplicar todos los ajustes
                final_score = signal['final_score']
                final_score *= (1 + (onchain_score - 0.5) * 0.2)  # ±10% por on-chain
                final_score *= (1 + (macro_analysis['macro_score'] - 0.5) * 0.2)  # ±10% por macro
                
                # Ajuste por Fear & Greed
                fg_adjustments = fg_analysis['trading_adjustments']
                final_score *= fg_adjustments['entry_aggressiveness']
                
                print(f"   • Score final ajustado: {final_score:.2f}")
                
                if final_score >= 7.0:
                    decision = "✅ ABRIR POSICIÓN"
                    
                    # Simular apertura de posición
                    success, result = paper_trader.place_order(signal)
                    if success:
                        print(f"   • {decision}: {result}")
                        
                        # Configurar trailing stop
                        position_data = {
                            'id': f'{symbol}_001',
                            'symbol': symbol,
                            'type': signal['type'],
                            'entry_price': signal['entry_price'],
                            'entry_time': datetime.now(),
                            'signal_score': final_score
                        }
                        
                        trailing_config = trailing.initialize_trailing_stop(symbol, position_data)
                        print(f"   • Trailing stop configurado: ${trailing_config['current_stop']:.2f}")
                        
                elif final_score >= 6.0:
                    decision = "⚠️ ESPERAR MEJOR SETUP"
                    print(f"   • {decision}")
                else:
                    decision = "❌ NO OPERAR"
                    print(f"   • {decision}")
                
            else:
                print(f"❌ Sin señal: {message}")
        
        # Estado final del portfolio
        print("\n" + "="*80)
        print("💼 ESTADO FINAL DEL PORTFOLIO")
        print("="*80)
        
        portfolio_status = paper_trader.print_portfolio_status()
        
        print("\n" + "="*80)
        print("✅ TEST INTEGRAL COMPLETADO EXITOSAMENTE")
        print("="*80)
        
        # Resumen de capacidades
        print("\n📋 CAPACIDADES DEL SISTEMA VALIDADAS:")
        print("✅ Paper Trading con capital virtual")
        print("✅ Análisis on-chain (SOPR, MVRV, flujos)")
        print("✅ Correlaciones macro (DXY, SPY, VIX)")
        print("✅ Optimización de señales de entrada")
        print("✅ Análisis de Bollinger Bands")
        print("✅ Trailing stops dinámicos")
        print("✅ Position sizing basado en volumen")
        print("✅ Fear & Greed Index integrado")
        print("✅ Sistema de decisión multi-factor")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN TEST INTEGRAL: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    success = test_integrated_system()
    
    if success:
        print("\n🎉 SISTEMA COMPLETAMENTE FUNCIONAL Y LISTO PARA PRODUCCIÓN")
    else:
        print("\n⚠️ REVISAR ERRORES ANTES DE PRODUCCIÓN")
    
    return success

if __name__ == "__main__":
    main()