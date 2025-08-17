#!/usr/bin/env python3
"""
Demo del Monitor Definitivo
Demostración rápida del sistema de monitoreo
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def demo_monitor():
    """Demostración del monitor definitivo"""
    
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║                     DEMO MONITOR DEFINITIVO                            ║
║                   Sistema de Seguimiento en Vivo                       ║
╚════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Trade ejemplo (señal DOGE generada por el sistema)
    trade = {
        'id': 1,
        'ticker': 'DOGE-USD',
        'type': 'SHORT',
        'entry_price': 0.2295,
        'stop_loss': 0.2334,
        'partial_target': 0.2238,
        'main_target': 0.2180,
        'position_size': 0.05,
        'entry_time': datetime.now() - timedelta(hours=2),
        'trailing_stop': None,
        'partial_closed': False,
        'status': 'ACTIVE'
    }
    
    print(f"🎯 TRADE ACTIVO EN MONITOREO:")
    print(f"{'='*50}")
    print(f"• Ticker: {trade['ticker']}")
    print(f"• Tipo: {trade['type']}")
    print(f"• Entry: ${trade['entry_price']:.4f}")
    print(f"• Stop Loss: ${trade['stop_loss']:.4f}")
    print(f"• Target Parcial (40%): ${trade['partial_target']:.4f}")
    print(f"• Target Principal: ${trade['main_target']:.4f}")
    print(f"• Position Size: {trade['position_size']*100:.1f}%")
    print(f"• Tiempo activo: {datetime.now() - trade['entry_time']}")
    
    # Obtener precio actual
    try:
        print(f"\n🔍 Obteniendo precio actual de {trade['ticker']}...")
        data = yf.Ticker(trade['ticker'])
        hist = data.history(period="1d", interval="5m")
        
        if len(hist) > 0:
            current_price = hist['Close'].iloc[-1]
            
            # Calcular P&L actual
            if trade['type'] == 'SHORT':
                current_profit_pct = (trade['entry_price'] - current_price) / trade['entry_price']
            else:
                current_profit_pct = (current_price - trade['entry_price']) / trade['entry_price']
            
            # Estado actual
            emoji = "🟢" if current_profit_pct > 0 else "🔴"
            
            print(f"\n{emoji} ESTADO ACTUAL:")
            print(f"{'='*30}")
            print(f"• Precio actual: ${current_price:.4f}")
            print(f"• P&L no realizado: {current_profit_pct*100:+.2f}%")
            
            # Verificar condiciones
            print(f"\n📊 ANÁLISIS DE CONDICIONES:")
            print(f"{'='*35}")
            
            # Distancia a targets
            distance_to_partial = abs(current_price - trade['partial_target']) / trade['entry_price'] * 100
            distance_to_main = abs(current_price - trade['main_target']) / trade['entry_price'] * 100
            distance_to_stop = abs(current_price - trade['stop_loss']) / trade['entry_price'] * 100
            
            print(f"• Distancia a Target Parcial: {distance_to_partial:.2f}%")
            print(f"• Distancia a Target Principal: {distance_to_main:.2f}%")
            print(f"• Distancia a Stop Loss: {distance_to_stop:.2f}%")
            
            # Verificar trailing
            trailing_activation = 0.010  # 1.0%
            if abs(current_profit_pct) >= trailing_activation:
                print(f"✅ Trailing Stop ACTIVADO (+{trailing_activation*100:.1f}%)")
                
                if trade['type'] == 'SHORT':
                    trailing_price = current_price * 1.005  # 0.5% arriba
                else:
                    trailing_price = current_price * 0.995  # 0.5% abajo
                
                print(f"📈 Trailing Stop: ${trailing_price:.4f}")
            else:
                needed_for_trailing = (trailing_activation - abs(current_profit_pct)) * 100
                print(f"⏳ Para activar trailing: {needed_for_trailing:.2f}% más")
            
            # Verificar targets
            print(f"\n🎯 ANÁLISIS DE TARGETS:")
            
            if trade['type'] == 'SHORT':
                if current_price <= trade['partial_target']:
                    print(f"💰 TARGET PARCIAL ALCANZADO - Cerrar 40%")
                elif current_price <= trade['main_target']:
                    print(f"🚀 TARGET PRINCIPAL ALCANZADO - Cerrar resto")
                elif current_price >= trade['stop_loss']:
                    print(f"🛑 STOP LOSS ALCANZADO - Cerrar posición")
                else:
                    print(f"⏳ Esperando targets...")
            else:  # LONG
                if current_price >= trade['partial_target']:
                    print(f"💰 TARGET PARCIAL ALCANZADO - Cerrar 40%")
                elif current_price >= trade['main_target']:
                    print(f"🚀 TARGET PRINCIPAL ALCANZADO - Cerrar resto")
                elif current_price <= trade['stop_loss']:
                    print(f"🛑 STOP LOSS ALCANZADO - Cerrar posición")
                else:
                    print(f"⏳ Esperando targets...")
            
            # Proyección
            print(f"\n💡 PROYECCIÓN DE RESULTADOS:")
            print(f"{'='*30}")
            
            # Si alcanza target parcial
            if trade['type'] == 'SHORT':
                partial_profit = ((trade['entry_price'] - trade['partial_target']) / trade['entry_price']) * 0.4
                main_profit = ((trade['entry_price'] - trade['main_target']) / trade['entry_price']) * 0.6
                stop_loss = ((trade['entry_price'] - trade['stop_loss']) / trade['entry_price'])
            else:
                partial_profit = ((trade['partial_target'] - trade['entry_price']) / trade['entry_price']) * 0.4
                main_profit = ((trade['main_target'] - trade['entry_price']) / trade['entry_price']) * 0.6
                stop_loss = ((trade['stop_loss'] - trade['entry_price']) / trade['entry_price'])
            
            total_if_both_targets = (partial_profit + main_profit) * 100
            partial_only = partial_profit * 100
            stop_loss_result = stop_loss * 100
            
            print(f"• Si alcanza ambos targets: {total_if_both_targets:+.2f}%")
            print(f"• Si solo target parcial: {partial_only:+.2f}%")
            print(f"• Si hit stop loss: {stop_loss_result:+.2f}%")
            
            # Recomendaciones
            print(f"\n🎯 RECOMENDACIONES:")
            print(f"{'='*20}")
            
            if abs(current_profit_pct) >= trailing_activation:
                print("1. ✅ Activar trailing stop inmediatamente")
                print("2. 📱 Monitorear cada 30 minutos")
                print("3. 🔔 Configurar alertas de precio")
            else:
                print("1. ⏰ Monitorear cada hora")
                print("2. 🎯 Esperar desarrollo del setup")
                print("3. 🛡️ Respetar stop loss sin excepciones")
            
            print("4. 💰 Cerrar 40% automáticamente en target parcial")
            print("5. 📊 Documentar resultado para análisis")
            
        else:
            print("❌ No se pudo obtener precio actual")
    
    except Exception as e:
        print(f"❌ Error obteniendo datos: {e}")
    
    print(f"\n{'='*60}")
    print("✅ DEMO MONITOR COMPLETADA")
    print(f"{'='*60}")
    
    print(f"\n💡 CARACTERÍSTICAS DEL MONITOR COMPLETO:")
    print("• Actualización automática cada 30 segundos")
    print("• Tracking de trailing stops en tiempo real")
    print("• Gestión automática de cierres parciales")
    print("• Alertas de targets y stop loss")
    print("• Registro de performance por trade")
    print("• Estadísticas de win rate en vivo")
    
    print(f"\n🚀 Para usar el monitor completo:")
    print("python3 monitor_definitivo.py")

if __name__ == "__main__":
    demo_monitor()