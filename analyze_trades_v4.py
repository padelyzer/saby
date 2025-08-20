#!/usr/bin/env python3
"""
Análisis Detallado de Trades Ganadores y Perdedores - V4.0
"""

import pandas as pd
import numpy as np
import json
import glob
from datetime import datetime

def analyze_v4_trades():
    """Analiza todos los trades del backtest V4.0"""
    
    print("\n" + "="*80)
    print(" ANÁLISIS DETALLADO DE TRADES V4.0 ".center(80, "="))
    print("="*80 + "\n")
    
    # Leer todos los archivos de backtest
    all_trades = []
    symbols_data = {}
    
    symbol_files = [
        'backtest_v4_ada.md',
        'backtest_v4_xrp.md', 
        'backtest_v4_doge.md',
        'backtest_v4_avax.md',
        'backtest_v4_sol.md',
        'backtest_v4_link.md',
        'backtest_v4_dot.md'
    ]
    
    for file in symbol_files:
        try:
            with open(file, 'r') as f:
                content = f.read()
                
            # Extraer símbolo
            symbol = file.replace('backtest_v4_', '').replace('.md', '').upper() + '-USD'
            
            # Parsear trades de la tabla
            trades = parse_trades_from_markdown(content, symbol)
            
            if trades:
                all_trades.extend(trades)
                symbols_data[symbol] = trades
                
        except FileNotFoundError:
            print(f"Archivo no encontrado: {file}")
            continue
    
    if not all_trades:
        print("⚠️ No se encontraron datos de trades")
        return
    
    # Convertir a DataFrame
    df = pd.DataFrame(all_trades)
    
    # Separar ganadores y perdedores
    winners = df[df['pnl'] > 0]
    losers = df[df['pnl'] <= 0]
    
    print(f"📊 RESUMEN GENERAL")
    print(f"  Total trades: {len(df)}")
    print(f"  Ganadores: {len(winners)} ({len(winners)/len(df)*100:.1f}%)")
    print(f"  Perdedores: {len(losers)} ({len(losers)/len(df)*100:.1f}%)")
    print(f"  P&L promedio: {df['pnl'].mean():.2f}%")
    print(f"  P&L total: {df['pnl'].sum():.2f}%\n")
    
    # ANÁLISIS DE TRADES GANADORES
    print("\n" + "="*80)
    print(" ✅ TRADES GANADORES ".center(80, "="))
    print("="*80 + "\n")
    
    if len(winners) > 0:
        print(f"📊 Estadísticas de Ganadores:")
        print(f"  Total: {len(winners)} trades")
        print(f"  Ganancia promedio: {winners['pnl'].mean():.2f}%")
        print(f"  Ganancia máxima: {winners['pnl'].max():.2f}%")
        print(f"  Ganancia mínima: {winners['pnl'].min():.2f}%")
        print(f"  Desv. estándar: {winners['pnl'].std():.2f}%\n")
        
        # Por régimen
        print("🎯 Por Régimen de Mercado:")
        regime_stats = winners.groupby('regime').agg({
            'pnl': ['count', 'mean', 'sum']
        })
        for regime in regime_stats.index:
            count = regime_stats.loc[regime, ('pnl', 'count')]
            avg = regime_stats.loc[regime, ('pnl', 'mean')]
            total = regime_stats.loc[regime, ('pnl', 'sum')]
            print(f"  {regime}: {count} trades, Avg: {avg:.2f}%, Total: {total:.2f}%")
        
        # Por estrategia
        print("\n🎲 Por Estrategia:")
        strategy_stats = winners.groupby('strategy').agg({
            'pnl': ['count', 'mean', 'sum']
        })
        for strategy in strategy_stats.index:
            count = strategy_stats.loc[strategy, ('pnl', 'count')]
            avg = strategy_stats.loc[strategy, ('pnl', 'mean')]
            total = strategy_stats.loc[strategy, ('pnl', 'sum')]
            print(f"  {strategy}: {count} trades, Avg: {avg:.2f}%, Total: {total:.2f}%")
        
        # Por tipo (LONG/SHORT)
        print("\n🔄 Por Tipo de Operación:")
        type_stats = winners.groupby('type').agg({
            'pnl': ['count', 'mean', 'sum']
        })
        for op_type in type_stats.index:
            count = type_stats.loc[op_type, ('pnl', 'count')]
            avg = type_stats.loc[op_type, ('pnl', 'mean')]
            total = type_stats.loc[op_type, ('pnl', 'sum')]
            print(f"  {op_type}: {count} trades, Avg: {avg:.2f}%, Total: {total:.2f}%")
        
        # Por razón de salida
        print("\n🚪 Por Razón de Salida:")
        exit_stats = winners.groupby('exit_reason').agg({
            'pnl': ['count', 'mean', 'sum']
        })
        for reason in exit_stats.index:
            count = exit_stats.loc[reason, ('pnl', 'count')]
            avg = exit_stats.loc[reason, ('pnl', 'mean')]
            print(f"  {reason}: {count} trades, Avg: {avg:.2f}%")
        
        # Top 10 mejores trades
        print("\n🏆 Top 10 Mejores Trades:")
        top_winners = winners.nlargest(10, 'pnl')
        for idx, trade in top_winners.iterrows():
            print(f"  {trade['symbol']}: {trade['type']} {trade['regime']}/{trade['strategy']} → {trade['pnl']:.2f}% ({trade['exit_reason']})")
        
        # Patrones comunes en ganadores
        print("\n🔍 Patrones Comunes en Ganadores:")
        
        # Combinación más exitosa
        winners['combo'] = winners['regime'] + '_' + winners['strategy']
        combo_stats = winners.groupby('combo').agg({
            'pnl': ['count', 'mean', 'sum']
        }).sort_values(('pnl', 'sum'), ascending=False)
        
        print("  Mejores combinaciones Régimen-Estrategia:")
        for combo in combo_stats.head(5).index:
            count = combo_stats.loc[combo, ('pnl', 'count')]
            avg = combo_stats.loc[combo, ('pnl', 'mean')]
            total = combo_stats.loc[combo, ('pnl', 'sum')]
            print(f"    {combo}: {count} trades, Avg: {avg:.2f}%, Total: {total:.2f}%")
    
    # ANÁLISIS DE TRADES PERDEDORES
    print("\n" + "="*80)
    print(" ❌ TRADES PERDEDORES ".center(80, "="))
    print("="*80 + "\n")
    
    if len(losers) > 0:
        print(f"📊 Estadísticas de Perdedores:")
        print(f"  Total: {len(losers)} trades")
        print(f"  Pérdida promedio: {losers['pnl'].mean():.2f}%")
        print(f"  Pérdida máxima: {losers['pnl'].min():.2f}%")
        print(f"  Pérdida mínima: {losers['pnl'].max():.2f}%")
        print(f"  Desv. estándar: {losers['pnl'].std():.2f}%\n")
        
        # Por régimen
        print("🎯 Por Régimen de Mercado:")
        regime_stats = losers.groupby('regime').agg({
            'pnl': ['count', 'mean', 'sum']
        })
        for regime in regime_stats.index:
            count = regime_stats.loc[regime, ('pnl', 'count')]
            avg = regime_stats.loc[regime, ('pnl', 'mean')]
            total = regime_stats.loc[regime, ('pnl', 'sum')]
            print(f"  {regime}: {count} trades, Avg: {avg:.2f}%, Total: {total:.2f}%")
        
        # Por estrategia
        print("\n🎲 Por Estrategia:")
        strategy_stats = losers.groupby('strategy').agg({
            'pnl': ['count', 'mean', 'sum']
        })
        for strategy in strategy_stats.index:
            count = strategy_stats.loc[strategy, ('pnl', 'count')]
            avg = strategy_stats.loc[strategy, ('pnl', 'mean')]
            total = strategy_stats.loc[strategy, ('pnl', 'sum')]
            print(f"  {strategy}: {count} trades, Avg: {avg:.2f}%, Total: {total:.2f}%")
        
        # Por tipo (LONG/SHORT)
        print("\n🔄 Por Tipo de Operación:")
        type_stats = losers.groupby('type').agg({
            'pnl': ['count', 'mean', 'sum']
        })
        for op_type in type_stats.index:
            count = type_stats.loc[op_type, ('pnl', 'count')]
            avg = type_stats.loc[op_type, ('pnl', 'mean')]
            total = type_stats.loc[op_type, ('pnl', 'sum')]
            print(f"  {op_type}: {count} trades, Avg: {avg:.2f}%, Total: {total:.2f}%")
        
        # Por razón de salida
        print("\n🚪 Por Razón de Salida:")
        exit_stats = losers.groupby('exit_reason').agg({
            'pnl': ['count', 'mean', 'sum']
        })
        for reason in exit_stats.index:
            count = exit_stats.loc[reason, ('pnl', 'count')]
            avg = exit_stats.loc[reason, ('pnl', 'mean')]
            print(f"  {reason}: {count} trades, Avg: {avg:.2f}%")
        
        # Top 10 peores trades
        print("\n🔴 Top 10 Peores Trades:")
        worst_losers = losers.nsmallest(10, 'pnl')
        for idx, trade in worst_losers.iterrows():
            print(f"  {trade['symbol']}: {trade['type']} {trade['regime']}/{trade['strategy']} → {trade['pnl']:.2f}% ({trade['exit_reason']})")
        
        # Patrones problemáticos
        print("\n⚠️ Patrones Problemáticos:")
        
        # Combinaciones menos exitosas
        losers['combo'] = losers['regime'] + '_' + losers['strategy']
        combo_stats = losers.groupby('combo').agg({
            'pnl': ['count', 'mean', 'sum']
        }).sort_values(('pnl', 'sum'))
        
        print("  Peores combinaciones Régimen-Estrategia:")
        for combo in combo_stats.head(5).index:
            count = combo_stats.loc[combo, ('pnl', 'count')]
            avg = combo_stats.loc[combo, ('pnl', 'mean')]
            total = combo_stats.loc[combo, ('pnl', 'sum')]
            print(f"    {combo}: {count} trades, Avg: {avg:.2f}%, Total: {total:.2f}%")
    
    # COMPARACIÓN Y CONCLUSIONES
    print("\n" + "="*80)
    print(" 📊 COMPARACIÓN Y CONCLUSIONES ".center(80, "="))
    print("="*80 + "\n")
    
    if len(winners) > 0 and len(losers) > 0:
        print("🎯 Comparación Ganadores vs Perdedores:")
        print(f"  Ratio Ganadores/Perdedores: {len(winners)/len(losers):.2f}")
        print(f"  Ganancia promedio: {winners['pnl'].mean():.2f}%")
        print(f"  Pérdida promedio: {losers['pnl'].mean():.2f}%")
        print(f"  Ratio Ganancia/Pérdida: {abs(winners['pnl'].mean()/losers['pnl'].mean()):.2f}")
        
        profit_factor = (winners['pnl'].sum() / abs(losers['pnl'].sum())) if losers['pnl'].sum() != 0 else 0
        print(f"  Profit Factor: {profit_factor:.2f}")
        
        # Expectancia matemática
        win_rate = len(winners) / len(df)
        avg_win = winners['pnl'].mean()
        avg_loss = abs(losers['pnl'].mean())
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        print(f"  Expectancia: {expectancy:.2f}%")
    
    print("\n💡 CONCLUSIONES CLAVE:")
    
    # Mejores condiciones
    if len(winners) > 0:
        best_regime = winners.groupby('regime')['pnl'].sum().idxmax()
        best_strategy = winners.groupby('strategy')['pnl'].sum().idxmax()
        best_type = winners.groupby('type')['pnl'].sum().idxmax()
        
        print(f"\n✅ Condiciones más favorables:")
        print(f"  - Mejor régimen: {best_regime}")
        print(f"  - Mejor estrategia: {best_strategy}")
        print(f"  - Mejor tipo de operación: {best_type}")
    
    # Peores condiciones
    if len(losers) > 0:
        worst_regime = losers.groupby('regime')['pnl'].sum().idxmin()
        worst_strategy = losers.groupby('strategy')['pnl'].sum().idxmin()
        worst_type = losers.groupby('type')['pnl'].sum().idxmin()
        
        print(f"\n❌ Condiciones a evitar:")
        print(f"  - Peor régimen: {worst_regime}")
        print(f"  - Peor estrategia: {worst_strategy}")
        print(f"  - Peor tipo de operación: {worst_type}")
    
    # Recomendaciones
    print("\n🎯 RECOMENDACIONES DE OPTIMIZACIÓN:")
    
    if len(winners) > 0 and len(losers) > 0:
        # Análisis de stops
        stopped_out = df[df['exit_reason'] == 'STOP_LOSS']
        stop_loss_rate = len(stopped_out) / len(df) * 100
        
        if stop_loss_rate > 60:
            print(f"  1. ⚠️ Alto % de stop loss ({stop_loss_rate:.1f}%): Considerar stops más amplios")
        
        # Análisis de win rate
        win_rate = len(winners) / len(df) * 100
        if win_rate < 40:
            print(f"  2. 📉 Win rate bajo ({win_rate:.1f}%): Ser más selectivo con las entradas")
        
        # Análisis por estrategia
        for strategy in df['strategy'].unique():
            strategy_df = df[df['strategy'] == strategy]
            strategy_win_rate = len(strategy_df[strategy_df['pnl'] > 0]) / len(strategy_df) * 100
            if strategy_win_rate < 30:
                print(f"  3. 🔄 Revisar estrategia {strategy} (WR: {strategy_win_rate:.1f}%)")
        
        # Análisis de rentabilidad
        if profit_factor < 1.2:
            print(f"  4. 📊 Profit Factor bajo ({profit_factor:.2f}): Mejorar ratio riesgo/beneficio")
        
        # Sugerencias específicas
        print("\n🔧 Ajustes sugeridos:")
        
        if best_regime == 'RANGING' and best_strategy == 'RANGE':
            print("  - Enfocarse en mercados laterales con estrategia mean reversion")
            print("  - Aumentar confianza mínima a 60% para RANGING")
        
        if worst_regime == 'TRENDING_DOWN':
            print("  - Reducir operaciones en tendencias bajistas")
            print("  - Usar confirmaciones adicionales en mercados bajistas")
        
        avg_winner_confidence = winners['confidence'].mean() if 'confidence' in winners else 0
        avg_loser_confidence = losers['confidence'].mean() if 'confidence' in losers else 0
        
        if avg_winner_confidence > avg_loser_confidence:
            print(f"  - Aumentar confianza mínima a {avg_winner_confidence:.1%}")
    
    # Guardar informe
    save_analysis_report(df, winners, losers)
    
    print("\n✅ Análisis completado y guardado en 'trades_analysis_v4.md'")

def parse_trades_from_markdown(content, symbol):
    """Parsea trades desde el contenido markdown"""
    trades = []
    
    # Buscar la tabla de trades
    lines = content.split('\n')
    in_table = False
    
    for line in lines:
        if '| # | Fecha |' in line:
            in_table = True
            continue
        
        if in_table and line.startswith('|') and not line.startswith('|---|'):
            parts = line.split('|')
            if len(parts) >= 11:
                try:
                    trade = {
                        'symbol': symbol,
                        'regime': parts[3].strip(),
                        'strategy': parts[4].strip(),
                        'type': parts[5].strip(),
                        'pnl': float(parts[8].strip().replace('%', '').replace('+', '')),
                        'exit_reason': parts[9].strip(),
                        'confidence': float(parts[10].strip().replace('%', ''))/100 if parts[10].strip() else 0.5
                    }
                    trades.append(trade)
                except (ValueError, IndexError):
                    continue
    
    return trades

def save_analysis_report(df, winners, losers):
    """Guarda el informe de análisis"""
    
    with open('trades_analysis_v4.md', 'w') as f:
        f.write(f"# 📊 ANÁLISIS DETALLADO DE TRADES V4.0\n\n")
        f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Sistema:** Trading Adaptativo V4.0\n\n")
        
        f.write(f"## 📊 Resumen General\n\n")
        f.write(f"- **Total trades:** {len(df)}\n")
        f.write(f"- **Ganadores:** {len(winners)} ({len(winners)/len(df)*100:.1f}%)\n")
        f.write(f"- **Perdedores:** {len(losers)} ({len(losers)/len(df)*100:.1f}%)\n")
        f.write(f"- **P&L promedio:** {df['pnl'].mean():.2f}%\n")
        f.write(f"- **P&L total:** {df['pnl'].sum():.2f}%\n\n")
        
        if len(winners) > 0:
            f.write(f"## ✅ Trades Ganadores\n\n")
            f.write(f"### Estadísticas\n")
            f.write(f"- **Ganancia promedio:** {winners['pnl'].mean():.2f}%\n")
            f.write(f"- **Ganancia máxima:** {winners['pnl'].max():.2f}%\n")
            f.write(f"- **Ganancia mínima:** {winners['pnl'].min():.2f}%\n\n")
            
            f.write(f"### Top 5 Mejores Trades\n")
            top_5 = winners.nlargest(5, 'pnl')
            for idx, trade in top_5.iterrows():
                f.write(f"- {trade['symbol']}: {trade['type']} {trade['pnl']:.2f}%\n")
            f.write("\n")
        
        if len(losers) > 0:
            f.write(f"## ❌ Trades Perdedores\n\n")
            f.write(f"### Estadísticas\n")
            f.write(f"- **Pérdida promedio:** {losers['pnl'].mean():.2f}%\n")
            f.write(f"- **Pérdida máxima:** {losers['pnl'].min():.2f}%\n")
            f.write(f"- **Pérdida mínima:** {losers['pnl'].max():.2f}%\n\n")
            
            f.write(f"### Top 5 Peores Trades\n")
            worst_5 = losers.nsmallest(5, 'pnl')
            for idx, trade in worst_5.iterrows():
                f.write(f"- {trade['symbol']}: {trade['type']} {trade['pnl']:.2f}%\n")

if __name__ == "__main__":
    analyze_v4_trades()