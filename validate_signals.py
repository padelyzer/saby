#!/usr/bin/env python3
"""
Validador de Señales Históricas
Analiza todas las señales enviadas y calcula su resultado real
"""

import json
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List

def load_signals():
    """Carga todas las señales del archivo"""
    with open('signals_20250816.json', 'r') as f:
        return json.load(f)

def validate_signal(signal: dict) -> dict:
    """Valida si una señal alcanzó su TP o SL"""
    ticker = signal['ticker']
    timestamp = datetime.fromisoformat(signal['timestamp'])
    entry_price = signal['price']
    stop_loss = signal['stop_loss']
    take_profit = signal['take_profit']
    direction = signal['direccion']
    
    # Obtener datos históricos desde la señal
    end_date = datetime.now()
    
    try:
        # Obtener datos con suficiente historial
        stock = yf.Ticker(ticker)
        df = stock.history(start=timestamp, end=end_date, interval='1h')
        
        if df.empty:
            return {
                'ticker': ticker,
                'timestamp': signal['timestamp'],
                'result': 'NO_DATA',
                'pnl_pct': 0,
                'hours_to_result': 0
            }
        
        # Buscar si hit TP o SL
        for i, (index, row) in enumerate(df.iterrows()):
            high = row['High']
            low = row['Low']
            
            if direction == 'LONG':
                # Check TP
                if high >= take_profit:
                    hours = i + 1
                    pnl = ((take_profit - entry_price) / entry_price) * 100 * signal['leverage']
                    return {
                        'ticker': ticker,
                        'timestamp': signal['timestamp'],
                        'entry': entry_price,
                        'exit': take_profit,
                        'result': 'TAKE_PROFIT',
                        'pnl_pct': round(pnl, 2),
                        'hours_to_result': hours,
                        'score': signal['score']
                    }
                # Check SL
                elif low <= stop_loss:
                    hours = i + 1
                    pnl = ((stop_loss - entry_price) / entry_price) * 100 * signal['leverage']
                    return {
                        'ticker': ticker,
                        'timestamp': signal['timestamp'],
                        'entry': entry_price,
                        'exit': stop_loss,
                        'result': 'STOP_LOSS',
                        'pnl_pct': round(pnl, 2),
                        'hours_to_result': hours,
                        'score': signal['score']
                    }
            else:  # SHORT
                # Check TP (precio baja)
                if low <= take_profit:
                    hours = i + 1
                    pnl = ((entry_price - take_profit) / entry_price) * 100 * signal['leverage']
                    return {
                        'ticker': ticker,
                        'timestamp': signal['timestamp'],
                        'entry': entry_price,
                        'exit': take_profit,
                        'result': 'TAKE_PROFIT',
                        'pnl_pct': round(pnl, 2),
                        'hours_to_result': hours,
                        'score': signal['score']
                    }
                # Check SL
                elif high >= stop_loss:
                    hours = i + 1
                    pnl = ((entry_price - stop_loss) / entry_price) * 100 * signal['leverage']
                    return {
                        'ticker': ticker,
                        'timestamp': signal['timestamp'],
                        'entry': entry_price,
                        'exit': stop_loss,
                        'result': 'STOP_LOSS',
                        'pnl_pct': round(pnl, 2),
                        'hours_to_result': hours,
                        'score': signal['score']
                    }
        
        # Si no hit ni TP ni SL, calcular PnL actual
        last_price = df['Close'].iloc[-1]
        if direction == 'LONG':
            current_pnl = ((last_price - entry_price) / entry_price) * 100 * signal['leverage']
        else:
            current_pnl = ((entry_price - last_price) / entry_price) * 100 * signal['leverage']
        
        return {
            'ticker': ticker,
            'timestamp': signal['timestamp'],
            'entry': entry_price,
            'current': last_price,
            'result': 'ACTIVE',
            'pnl_pct': round(current_pnl, 2),
            'hours_active': len(df),
            'score': signal['score']
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'timestamp': signal['timestamp'],
            'result': 'ERROR',
            'error': str(e),
            'pnl_pct': 0
        }

def analyze_results(results: List[dict]):
    """Analiza los resultados de todas las señales"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║              📊 VALIDACIÓN DE SEÑALES HISTÓRICAS                ║
╚════════════════════════════════════════════════════════════════╝
""")
    
    # Contar señales únicas (eliminar duplicados por ticker similar en corto tiempo)
    unique_signals = {}
    for r in results:
        key = f"{r['ticker']}_{r['timestamp'][:13]}"  # Agrupar por ticker y hora
        if key not in unique_signals or r['pnl_pct'] != 0:
            unique_signals[key] = r
    
    results_unique = list(unique_signals.values())
    
    # Estadísticas generales
    total = len(results_unique)
    tp_count = sum(1 for r in results_unique if r['result'] == 'TAKE_PROFIT')
    sl_count = sum(1 for r in results_unique if r['result'] == 'STOP_LOSS')
    active_count = sum(1 for r in results_unique if r['result'] == 'ACTIVE')
    error_count = sum(1 for r in results_unique if r['result'] in ['ERROR', 'NO_DATA'])
    
    print(f"\n📈 RESUMEN GENERAL:")
    print(f"{'='*60}")
    print(f"Total señales únicas: {total}")
    print(f"✅ Take Profit: {tp_count} ({tp_count/total*100:.1f}%)")
    print(f"❌ Stop Loss: {sl_count} ({sl_count/total*100:.1f}%)")
    print(f"🔄 Activas: {active_count}")
    print(f"⚠️ Sin datos/Error: {error_count}")
    
    # Calcular Win Rate
    closed_trades = tp_count + sl_count
    if closed_trades > 0:
        win_rate = (tp_count / closed_trades) * 100
        print(f"\n🎯 WIN RATE: {win_rate:.1f}%")
    
    # Calcular PnL total
    total_pnl = sum(r['pnl_pct'] for r in results_unique if r['result'] in ['TAKE_PROFIT', 'STOP_LOSS'])
    avg_pnl = total_pnl / closed_trades if closed_trades > 0 else 0
    
    print(f"💰 PnL Total: {total_pnl:+.2f}%")
    print(f"📊 PnL Promedio: {avg_pnl:+.2f}%")
    
    # Análisis por ticker
    print(f"\n📊 ANÁLISIS POR ACTIVO:")
    print(f"{'='*60}")
    
    ticker_stats = {}
    for r in results_unique:
        ticker = r['ticker']
        if ticker not in ticker_stats:
            ticker_stats[ticker] = {
                'total': 0,
                'tp': 0,
                'sl': 0,
                'active': 0,
                'pnl': 0,
                'scores': []
            }
        
        ticker_stats[ticker]['total'] += 1
        ticker_stats[ticker]['scores'].append(r.get('score', 0))
        
        if r['result'] == 'TAKE_PROFIT':
            ticker_stats[ticker]['tp'] += 1
            ticker_stats[ticker]['pnl'] += r['pnl_pct']
        elif r['result'] == 'STOP_LOSS':
            ticker_stats[ticker]['sl'] += 1
            ticker_stats[ticker]['pnl'] += r['pnl_pct']
        elif r['result'] == 'ACTIVE':
            ticker_stats[ticker]['active'] += 1
    
    for ticker, stats in ticker_stats.items():
        closed = stats['tp'] + stats['sl']
        wr = (stats['tp'] / closed * 100) if closed > 0 else 0
        avg_score = sum(stats['scores']) / len(stats['scores'])
        
        print(f"\n{ticker}:")
        print(f"  Señales: {stats['total']} | TP: {stats['tp']} | SL: {stats['sl']} | Activas: {stats['active']}")
        print(f"  Win Rate: {wr:.1f}% | PnL: {stats['pnl']:+.2f}% | Score Avg: {avg_score:.1f}")
    
    # Mostrar trades específicos
    print(f"\n📋 DETALLE DE TRADES CERRADOS:")
    print(f"{'='*60}")
    
    for r in sorted(results_unique, key=lambda x: x['timestamp'])[:20]:  # Últimos 20
        if r['result'] in ['TAKE_PROFIT', 'STOP_LOSS']:
            emoji = "✅" if r['result'] == 'TAKE_PROFIT' else "❌"
            time_str = r['timestamp'].split('T')[1][:5]
            print(f"{emoji} {r['ticker']} | {time_str} | {r['result'][:2]} | {r['pnl_pct']:+.2f}% | {r.get('hours_to_result', 0)}h")
    
    # Trades activos
    print(f"\n🔄 TRADES ACTIVOS:")
    print(f"{'='*60}")
    
    for r in results_unique:
        if r['result'] == 'ACTIVE':
            emoji = "🟢" if r['pnl_pct'] > 0 else "🔴" if r['pnl_pct'] < 0 else "⚪"
            print(f"{emoji} {r['ticker']} | Entry: ${r['entry']:.2f} | Current PnL: {r['pnl_pct']:+.2f}%")
    
    # Recomendaciones
    print(f"\n💡 ANÁLISIS Y RECOMENDACIONES:")
    print(f"{'='*60}")
    
    if win_rate > 60:
        print("✅ Win Rate EXCELENTE - El sistema está funcionando muy bien")
    elif win_rate > 50:
        print("✅ Win Rate BUENO - El sistema es rentable")
    else:
        print("⚠️ Win Rate BAJO - Revisar criterios de entrada")
    
    if avg_pnl > 0:
        print(f"✅ Expectativa positiva: {avg_pnl:+.2f}% por trade")
    else:
        print(f"❌ Expectativa negativa: {avg_pnl:+.2f}% por trade")
    
    # Análisis de repetición
    fil_count = sum(1 for r in results if r['ticker'] == 'FIL-USD')
    atom_count = sum(1 for r in results if r['ticker'] == 'ATOM-USD')
    
    print(f"\n⚠️ OBSERVACIONES:")
    print(f"- FIL-USD generó {fil_count} señales (posible sobre-trading)")
    print(f"- ATOM-USD generó {atom_count} señales")
    print(f"- Recomendación: Aumentar cooldown entre señales del mismo activo")

def main():
    # Cargar señales
    signals = load_signals()
    print(f"📥 Cargadas {len(signals)} señales totales")
    
    # Validar cada señal
    print("🔍 Validando señales contra datos reales...")
    results = []
    
    for i, signal in enumerate(signals):
        if i % 10 == 0:
            print(f"  Procesando... {i}/{len(signals)}")
        
        result = validate_signal(signal)
        results.append(result)
    
    # Analizar resultados
    analyze_results(results)
    
    # Guardar resultados
    with open('signal_validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Resultados guardados en signal_validation_results.json")

if __name__ == "__main__":
    main()