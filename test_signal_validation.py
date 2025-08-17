#!/usr/bin/env python3
"""
Test de validación de coherencia de señales
"""

from advanced_signals import AdvancedSignalDetector
import yfinance as yf

print("🔍 Probando validación de señales...")
print("="*50)

detector = AdvancedSignalDetector()

# Probar con BTC
print("\nAnalizando BTC-USD...")
btc = yf.Ticker('BTC-USD')
df = btc.history(period='3mo', interval='1h')

signal = detector.generate_advanced_signal('BTC-USD', df)

if signal:
    print(f"\n✅ Señal encontrada: {signal['type']}")
    print(f"Precio entrada: ${signal['entry_price']:,.2f}")
    print(f"Stop Loss: ${signal['stop_loss']:,.2f}")
    print(f"Target 1: ${signal['primary_target']['price']:,.2f}")
    print(f"R:R Ratio: {signal['risk_reward_ratio']}:1")
    
    # Validar coherencia
    print(f"\n🔍 Validación de coherencia:")
    
    if signal['type'] == 'LONG':
        tp_valid = signal['primary_target']['price'] > signal['entry_price']
        sl_valid = signal['stop_loss'] < signal['entry_price']
        
        print(f"• Target arriba del precio: {'✅' if tp_valid else '❌'}")
        print(f"• Stop debajo del precio: {'✅' if sl_valid else '❌'}")
        
        if tp_valid and sl_valid:
            print("✅ SEÑAL LONG COHERENTE")
        else:
            print("❌ ERROR: Señal LONG incoherente")
            
    else:  # SHORT
        tp_valid = signal['primary_target']['price'] < signal['entry_price']
        sl_valid = signal['stop_loss'] > signal['entry_price']
        
        print(f"• Target debajo del precio: {'✅' if tp_valid else '❌'}")
        print(f"• Stop arriba del precio: {'✅' if sl_valid else '❌'}")
        
        if tp_valid and sl_valid:
            print("✅ SEÑAL SHORT COHERENTE")
        else:
            print("❌ ERROR: Señal SHORT incoherente")
    
    # Mostrar razones
    print(f"\nRazones ({len(signal['entry_reasons'])}):")
    for reason in signal['entry_reasons']:
        print(f"• {reason}")
        
else:
    print("❌ No se generó señal (filtrada por validación)")

# Probar con más criptos
print("\n" + "="*50)
print("Probando otras criptomonedas...")

tickers = ['ETH-USD', 'SOL-USD', 'BNB-USD']
for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period='3mo', interval='1h')
        signal = detector.generate_advanced_signal(ticker, df)
        
        if signal:
            # Validar
            if signal['type'] == 'LONG':
                valid = signal['primary_target']['price'] > signal['entry_price'] and \
                       signal['stop_loss'] < signal['entry_price']
            else:
                valid = signal['primary_target']['price'] < signal['entry_price'] and \
                       signal['stop_loss'] > signal['entry_price']
            
            status = "✅ Coherente" if valid else "❌ Incoherente"
            print(f"{ticker}: {signal['type']} - {status}")
        else:
            print(f"{ticker}: Sin señal")
    except Exception as e:
        print(f"{ticker}: Error - {e}")

print("\n✅ Test completado")