#!/usr/bin/env python3
"""
Demo de cómo funcionan las señales avanzadas
Muestra ejemplos de lo que detectaría el sistema
"""

import yfinance as yf
import pandas as pd
from datetime import datetime

def analyze_btc_example():
    """Analiza BTC para mostrar ejemplo"""
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║     🎯 EJEMPLO DE SEÑAL AVANZADA - MOVIMIENTOS LARGOS          ║
╚════════════════════════════════════════════════════════════════╝
""")
    
    # Obtener datos reales de BTC
    btc = yf.Ticker('BTC-USD')
    df = btc.history(period='1mo', interval='1h')
    
    current_price = df['Close'].iloc[-1]
    
    # Encontrar niveles reales
    recent_high = df['High'].tail(100).max()
    recent_low = df['Low'].tail(100).min()
    
    # Identificar soportes y resistencias reales
    print(f"\n📊 ANÁLISIS ACTUAL DE BTC-USD")
    print(f"{'='*60}")
    print(f"Precio actual: ${current_price:,.2f}")
    print(f"Máximo reciente (100h): ${recent_high:,.2f}")
    print(f"Mínimo reciente (100h): ${recent_low:,.2f}")
    
    # Calcular niveles clave
    pivot = (recent_high + recent_low + current_price) / 3
    r1 = (2 * pivot) - recent_low
    r2 = pivot + (recent_high - recent_low)
    s1 = (2 * pivot) - recent_high
    s2 = pivot - (recent_high - recent_low)
    
    print(f"\n📍 NIVELES CLAVE CALCULADOS:")
    print(f"{'='*60}")
    print(f"Resistencia 2: ${r2:,.2f} ({((r2/current_price - 1)*100):+.2f}%)")
    print(f"Resistencia 1: ${r1:,.2f} ({((r1/current_price - 1)*100):+.2f}%)")
    print(f"Pivot Point:   ${pivot:,.2f} ({((pivot/current_price - 1)*100):+.2f}%)")
    print(f"Soporte 1:     ${s1:,.2f} ({((s1/current_price - 1)*100):+.2f}%)")
    print(f"Soporte 2:     ${s2:,.2f} ({((s2/current_price - 1)*100):+.2f}%)")
    
    # Ejemplo de señal que buscaría el sistema
    print(f"\n🎯 EJEMPLO DE SEÑAL QUE BUSCA EL SISTEMA:")
    print(f"{'='*60}")
    
    # Señal LONG si el precio está cerca de un soporte
    distance_to_s1 = abs(current_price - s1) / current_price * 100
    
    if distance_to_s1 < 2:  # Dentro del 2% del soporte
        print(f"""
🟢 **SEÑAL LONG DETECTADA**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 BTC-USD
💰 Entrada: ${current_price:,.2f}
🛑 Stop Loss: ${s2:,.2f} (Debajo de S2)
🎯 Target 1: ${pivot:,.2f} (Pivot Point)
🚀 Target 2: ${r1:,.2f} (Resistencia 1)
🌟 Target 3: ${r2:,.2f} (Resistencia 2)

📈 RATIOS:
• Target 1: {((pivot - current_price)/(current_price - s2)):.2f}:1 R:R
• Target 2: {((r1 - current_price)/(current_price - s2)):.2f}:1 R:R
• Target 3: {((r2 - current_price)/(current_price - s2)):.2f}:1 R:R

✅ RAZONES:
• Rebote en soporte S1
• Tendencia general alcista
• RSI en zona de sobreventa
• Volumen creciente
""")
    
    # Fibonacci levels
    fib_range = recent_high - recent_low
    fib_levels = {
        '0%': recent_high,
        '23.6%': recent_high - (fib_range * 0.236),
        '38.2%': recent_high - (fib_range * 0.382),
        '50%': recent_high - (fib_range * 0.5),
        '61.8%': recent_high - (fib_range * 0.618),
        '78.6%': recent_high - (fib_range * 0.786),
        '100%': recent_low
    }
    
    print(f"\n📐 NIVELES DE FIBONACCI:")
    print(f"{'='*60}")
    for level, price in fib_levels.items():
        distance = ((price / current_price - 1) * 100)
        marker = " ← Cerca" if abs(distance) < 2 else ""
        print(f"{level:>6}: ${price:,.2f} ({distance:+.2f}%){marker}")
    
    # Mostrar zonas de liquidación comunes
    print(f"\n💀 ZONAS DE LIQUIDACIÓN TÍPICAS (con leverage):")
    print(f"{'='*60}")
    leverages = [3, 5, 10]
    for lev in leverages:
        liq_long = current_price * (1 - 1/lev)
        liq_short = current_price * (1 + 1/lev)
        print(f"Leverage {lev}x:")
        print(f"  • Long liquidation: ${liq_long:,.2f} ({((liq_long/current_price - 1)*100):+.2f}%)")
        print(f"  • Short liquidation: ${liq_short:,.2f} ({((liq_short/current_price - 1)*100):+.2f}%)")
    
    print(f"\n💡 ESTRATEGIA DE MOVIMIENTOS LARGOS:")
    print(f"{'='*60}")
    print("""
El sistema busca:
1. **Entradas en zonas de alta confluencia**:
   - Soporte/Resistencia + Fibonacci + Patrón

2. **Targets basados en estructura**:
   - No usa % fijos
   - Busca próxima resistencia/soporte real
   - Considera niveles psicológicos ($60k, $65k, etc)

3. **Stop Loss inteligente**:
   - Debajo de estructura clave
   - No solo un % arbitrario
   - Protege de barridos de liquidación

4. **Gestión de posición**:
   - Cerrar 50% en Target 1
   - Dejar 50% correr hasta Target 2-3
   - Mover SL a breakeven después de Target 1

VENTAJAS:
✅ Capturas movimientos de 5-20% en vez de 2-3%
✅ Mejor ratio riesgo/recompensa (3:1 a 5:1)
✅ Menos trades pero más rentables
✅ Evitas el ruido del mercado
""")

if __name__ == "__main__":
    analyze_btc_example()