#!/usr/bin/env python3
"""
Probar las optimizaciones aplicadas
"""

import requests
import time
from tabulate import tabulate

# Pares optimizados y sus cambios
OPTIMIZED_PAIRS = {
    'DOTUSDT': {'old': 'mean_reversion', 'new': 'momentum', 'reason': 'Bajo WR (37.5%)'},
    'DOGEUSDT': {'old': 'trend_following', 'new': 'volume_breakout', 'reason': 'WR 0%'},
    'ADAUSDT': {'old': 'trend_following', 'new': 'mean_reversion', 'reason': 'Sin señales'},
    'LINKUSDT': {'old': 'trend_following', 'new': 'mean_reversion', 'reason': 'Sin señales'},
    'AVAXUSDT': {'old': 'ultra_estricto', 'new': 'menos_restrictivo', 'reason': 'Pocas señales'}
}

def test_pair(symbol, period=30):
    """Prueba un par específico"""
    try:
        response = requests.post(
            f'http://localhost:8000/api/backtest/{symbol}',
            json={'period_days': period, 'risk_percent': 2.0},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            signals = data.get('signals', [])
            winners = sum(1 for s in signals if s.get('success', False))
            
            return {
                'signals': len(signals),
                'winners': winners,
                'win_rate': (winners / len(signals) * 100) if signals else 0,
                'total_pnl': sum(s.get('profit_loss', 0) for s in signals),
                'strategy': data.get('strategy_used', 'N/A')
            }
        else:
            return {'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'error': str(e)}

def main():
    print("\n🔧 PROBANDO OPTIMIZACIONES APLICADAS")
    print("="*80)
    
    print("\n📝 CAMBIOS REALIZADOS:")
    for symbol, changes in OPTIMIZED_PAIRS.items():
        pair_name = symbol.replace('USDT', '')
        print(f"  • {pair_name}: {changes['old']} → {changes['new']} ({changes['reason']})")
    
    print(f"\n📊 RESULTADOS DE OPTIMIZACIÓN (30 días):")
    print("-"*60)
    
    time.sleep(3)  # Esperar que la API esté lista
    
    table_data = []
    
    for symbol in OPTIMIZED_PAIRS.keys():
        result = test_pair(symbol)
        
        if 'error' not in result:
            pair_name = symbol.replace('USDT', '')
            table_data.append([
                pair_name,
                OPTIMIZED_PAIRS[symbol]['new'],
                result['signals'],
                result['winners'],
                f"{result['win_rate']:.1f}%",
                f"{result['total_pnl']:.2f}%",
                "✅" if result['win_rate'] > 50 else "❌" if result['signals'] > 0 else "⚪"
            ])
        else:
            pair_name = symbol.replace('USDT', '')
            table_data.append([pair_name, "ERROR", "-", "-", "-", "-", "❌"])
    
    headers = ["Par", "Nueva Estrategia", "Señales", "Ganadoras", "Win Rate", "P&L", "Status"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Comparar con resultados previos
    print(f"\n📈 COMPARACIÓN CON RESULTADOS PREVIOS:")
    print("-"*50)
    
    improvements = {
        'DOT': {'prev': '37.5%', 'target': '>50%'},
        'DOGE': {'prev': '0%', 'target': '>40%'},
        'ADA': {'prev': 'Sin señales', 'target': '>3 señales'},
        'LINK': {'prev': 'Sin señales', 'target': '>3 señales'},
        'AVAX': {'prev': '2 señales', 'target': '>5 señales'}
    }
    
    for pair, targets in improvements.items():
        print(f"  • {pair}: Era {targets['prev']} → Objetivo: {targets['target']}")
    
    print(f"\n🎯 CRITERIOS DE ÉXITO:")
    print(f"  • Win rate mínimo: 50%")
    print(f"  • Señales mínimas: 3 por período de 30 días")
    print(f"  • P&L positivo preferible")
    
    print(f"\n💡 PRÓXIMO PASO:")
    print(f"  Comparar estos resultados con el backtest anterior para validar mejoras")

if __name__ == "__main__":
    main()
