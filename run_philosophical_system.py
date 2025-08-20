#!/usr/bin/env python3
"""
Script para ejecutar el sistema filosófico con consenso
y guardar las señales en formato compatible con la UI
"""

import json
import time
from datetime import datetime
from trading_api.philosophical_trading_system import PhilosophicalConsensusSystem

def run_continuous_scan():
    """Ejecuta el escaneo continuo del sistema filosófico"""
    
    system = PhilosophicalConsensusSystem()
    
    # Símbolos a monitorear
    symbols = [
        'BTC-USD',
        'ETH-USD',
        'SOL-USD',
        'DOGE-USD',
        'ADA-USD',
        'AVAX-USD',
        'LINK-USD',
        'DOT-USD'
    ]
    
    print("\n" + "="*70)
    print(" SISTEMA FILOSÓFICO ACTIVO ".center(70))
    print("="*70)
    print("\n✅ Monitoreando mercados cada 10 minutos")
    print("✅ Solo señales con consenso > 65%")
    print("✅ Sin señales contradictorias\n")
    
    while True:
        try:
            print(f"\n⏰ Escaneo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 50)
            
            # Escanear símbolos
            signals = system.scan_symbols(symbols)
            
            if signals:
                # Convertir a formato compatible con la UI
                ui_signals = []
                for signal in signals:
                    ui_signal = {
                        'timestamp': signal.timestamp.isoformat(),
                        'ticker': signal.symbol,
                        'action': f"{signal.action}_LONG" if signal.action == "BUY" else f"{signal.action}_SHORT",
                        'price': signal.entry_price,
                        'stop_loss': signal.stop_loss,
                        'take_profit': signal.take_profit,
                        'confidence': signal.confidence,
                        'consensus_score': signal.consensus_score,
                        'philosophers_agree': signal.philosophers_agree,
                        'philosophers_disagree': signal.philosophers_disagree,
                        'market_regime': signal.market_regime,
                        'risk_reward_ratio': signal.risk_reward,
                        'reasoning': signal.reasoning,
                        'timeframe': '1H',
                        'exchange': 'Binance',
                        'leverage': 3,
                        'position_size_pct': 3.0 if signal.confidence < 0.8 else 5.0
                    }
                    ui_signals.append(ui_signal)
                
                # Guardar señales
                filename = f"signals_{datetime.now().strftime('%Y%m%d')}.json"
                
                # Cargar señales existentes si hay
                try:
                    with open(filename, 'r') as f:
                        existing_signals = json.load(f)
                except:
                    existing_signals = []
                
                # Agregar nuevas señales
                existing_signals.extend(ui_signals)
                
                # Guardar actualizado
                with open(filename, 'w') as f:
                    json.dump(existing_signals, f, indent=2)
                
                print(f"\n✅ {len(signals)} señales guardadas en {filename}")
                
                for signal in signals:
                    print(f"\n📍 {signal.symbol}: {signal.action} @ ${signal.entry_price:.4f}")
                    print(f"   Confianza: {signal.confidence:.1%}")
                    print(f"   Filósofos: {', '.join(signal.philosophers_agree)}")
            else:
                print("❌ No hay señales con consenso en este ciclo")
            
            # Esperar 10 minutos
            print(f"\n💤 Esperando 10 minutos para próximo escaneo...")
            time.sleep(600)  # 10 minutos
            
        except KeyboardInterrupt:
            print("\n\n⛔ Sistema detenido por el usuario")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Reintentando en 1 minuto...")
            time.sleep(60)

if __name__ == "__main__":
    run_continuous_scan()