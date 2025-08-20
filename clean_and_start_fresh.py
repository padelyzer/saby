#!/usr/bin/env python3
"""
Script para limpiar datos antiguos y empezar sistema limpio
"""

import os
import json
from datetime import datetime
from pathlib import Path

def clean_old_data():
    """Limpia todos los archivos de señales y trades antiguos"""
    
    print("\n" + "="*70)
    print(" LIMPIEZA DE SISTEMA ".center(70))
    print("="*70)
    
    # Archivos a limpiar
    files_to_clean = [
        'active_trades.json',
        'trade_history.json',
        'trade_results.csv',
        'signals_20250816.json',
        'signals_20250817.json', 
        'signals_20250818.json',
        'backtest_results_macro.json',
        'backtest_simulated_results.json',
        'bot_estado.json',
        'paper_trading.db',
        'philosophical_signals*.json'
    ]
    
    # Limpiar archivos
    cleaned = 0
    for pattern in files_to_clean:
        if '*' in pattern:
            # Patrón con wildcard
            for file in Path('/Users/ja/saby').glob(pattern):
                try:
                    os.remove(file)
                    print(f"✅ Eliminado: {file.name}")
                    cleaned += 1
                except Exception as e:
                    print(f"⚠️ No se pudo eliminar {file.name}: {e}")
        else:
            # Archivo específico
            file_path = Path('/Users/ja/saby') / pattern
            if file_path.exists():
                try:
                    os.remove(file_path)
                    print(f"✅ Eliminado: {pattern}")
                    cleaned += 1
                except Exception as e:
                    print(f"⚠️ No se pudo eliminar {pattern}: {e}")
    
    print(f"\n📊 Total archivos limpiados: {cleaned}")
    
    # Crear archivos iniciales limpios
    print("\n🔄 Creando archivos iniciales limpios...")
    
    # Active trades vacío
    active_trades = {
        "trades": [],
        "last_update": datetime.now().isoformat(),
        "total_positions": 0
    }
    
    with open('/Users/ja/saby/active_trades.json', 'w') as f:
        json.dump(active_trades, f, indent=2)
    print("✅ Creado: active_trades.json (vacío)")
    
    # Trade history vacío
    trade_history = {
        "history": [],
        "statistics": {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0
        },
        "last_update": datetime.now().isoformat()
    }
    
    with open('/Users/ja/saby/trade_history.json', 'w') as f:
        json.dump(trade_history, f, indent=2)
    print("✅ Creado: trade_history.json (vacío)")
    
    # Señales del día vacío
    today_signals = []
    signals_file = f"signals_{datetime.now().strftime('%Y%m%d')}.json"
    
    with open(f'/Users/ja/saby/{signals_file}', 'w') as f:
        json.dump(today_signals, f, indent=2)
    print(f"✅ Creado: {signals_file} (vacío)")
    
    # Estado inicial del sistema
    system_state = {
        "status": "ready",
        "initialized_at": datetime.now().isoformat(),
        "configuration": {
            "system": "philosophical_consensus",
            "min_consensus": 0.65,
            "min_philosophers": 3,
            "timelock_minutes": 15,
            "max_positions": 5,
            "position_size": 0.02,
            "symbols": [
                "BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD",
                "ADA-USD", "AVAX-USD", "LINK-USD", "DOT-USD"
            ],
            "philosophers": [
                "Socrates", "Aristoteles", "Platon", "Nietzsche",
                "Kant", "Descartes", "Confucio", "SunTzu"
            ]
        },
        "performance": {
            "total_pnl": 0.0,
            "daily_pnl": 0.0,
            "win_rate": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0
        }
    }
    
    with open('/Users/ja/saby/system_state.json', 'w') as f:
        json.dump(system_state, f, indent=2)
    print("✅ Creado: system_state.json")
    
    print("\n" + "="*70)
    print(" SISTEMA LIMPIO Y LISTO ".center(70))
    print("="*70)
    print("\n✅ Todos los datos antiguos han sido eliminados")
    print("✅ Archivos iniciales creados")
    print("✅ Sistema listo para empezar desde cero")
    
    return True

def verify_clean_state():
    """Verifica que el sistema esté limpio"""
    
    print("\n🔍 Verificando estado limpio...")
    
    checks = []
    
    # Verificar active trades
    with open('/Users/ja/saby/active_trades.json', 'r') as f:
        data = json.load(f)
        checks.append(('Active Trades', len(data.get('trades', [])) == 0))
    
    # Verificar trade history
    with open('/Users/ja/saby/trade_history.json', 'r') as f:
        data = json.load(f)
        checks.append(('Trade History', len(data.get('history', [])) == 0))
    
    # Verificar señales del día
    signals_file = f"signals_{datetime.now().strftime('%Y%m%d')}.json"
    if Path(f'/Users/ja/saby/{signals_file}').exists():
        with open(f'/Users/ja/saby/{signals_file}', 'r') as f:
            data = json.load(f)
            checks.append(('Señales Hoy', len(data) == 0))
    
    # Mostrar resultados
    all_clean = True
    for name, is_clean in checks:
        status = "✅" if is_clean else "❌"
        print(f"  {status} {name}: {'Limpio' if is_clean else 'Contiene datos'}")
        all_clean = all_clean and is_clean
    
    if all_clean:
        print("\n✅ Sistema completamente limpio")
    else:
        print("\n⚠️ Algunos archivos aún contienen datos")
    
    return all_clean

if __name__ == "__main__":
    # Limpiar sistema
    clean_old_data()
    
    # Verificar
    verify_clean_state()
    
    print("\n🚀 PRÓXIMOS PASOS:")
    print("1. Iniciar API Bridge: python3 paper_trading_api_bridge.py")
    print("2. Iniciar UI: npm run dev (en signal-haven-desk)")
    print("3. Usar el botón START en la UI para comenzar paper trading")
    print("\n💡 El sistema empezará completamente limpio sin señales corruptas")