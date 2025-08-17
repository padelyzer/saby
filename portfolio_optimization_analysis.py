#!/usr/bin/env python3
"""
Análisis de Optimización de Portafolio
Busca pares con movimientos similares a los top performers (ETH, BNB, SOL)
para crear un portafolio diversificado y optimizado
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
import seaborn as sns

from daily_trading_system_v2 import DailyTradingSystemV2

class PortfolioOptimizer:
    """
    Optimizador de portafolio para trading de criptomonedas
    """
    
    def __init__(self):
        self.system = DailyTradingSystemV2(initial_capital=10000)
        
        # Top performers identificados
        self.top_performers = ['ETH-USD', 'BNB-USD', 'SOL-USD']
        
        # Universo expandido de criptomonedas para análisis
        self.crypto_universe = [
            # Top performers actuales
            'ETH-USD', 'BNB-USD', 'SOL-USD',
            
            # Major coins
            'BTC-USD', 'ADA-USD', 'MATIC-USD', 'AVAX-USD', 'DOT-USD',
            
            # DeFi tokens
            'UNI-USD', 'AAVE-USD', 'COMP-USD', 'MKR-USD', 'SUSHI-USD',
            
            # Layer 1 alternatives
            'ATOM-USD', 'ALGO-USD', 'NEAR-USD', 'FTM-USD', 'ONE-USD',
            
            # Gaming/Metaverse
            'MANA-USD', 'SAND-USD', 'AXS-USD', 'ENJ-USD',
            
            # Storage/Infrastructure
            'FIL-USD', 'AR-USD', 'STORJ-USD',
            
            # AI/Data
            'GRT-USD', 'OCEAN-USD', 'FET-USD',
            
            # Exchange tokens
            'CRO-USD', 'KCS-USD', 'HT-USD',
            
            # Stablecoins alternatives
            'USDC-USD', 'DAI-USD',
            
            # Emerging/High volatility
            'DOGE-USD', 'SHIB-USD', 'LTC-USD', 'BCH-USD',
            
            # Layer 2
            'OP-USD', 'ARB-USD'
        ]
        
        self.market_data = {}
        self.correlation_matrix = None
        self.similarity_scores = {}
        
    def fetch_market_data(self, days=90):
        """
        Obtiene datos de mercado para análisis
        """
        print("📊 Obteniendo datos de mercado...")
        print(f"   Período: {days} días")
        print(f"   Símbolos: {len(self.crypto_universe)} activos")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        successful_fetches = 0
        
        for symbol in self.crypto_universe:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=start_date, end=end_date, interval='1d')
                
                if len(df) > 30:  # Mínimo 30 días de datos
                    # Calcular métricas
                    df['returns'] = df['Close'].pct_change()
                    df['cumulative_return'] = (1 + df['returns']).cumprod()
                    
                    # Volatilidad
                    volatility = df['returns'].std() * np.sqrt(252)
                    
                    # Performance total
                    total_return = ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100
                    
                    # Sharpe ratio (simplificado)
                    sharpe = df['returns'].mean() / df['returns'].std() * np.sqrt(252) if df['returns'].std() > 0 else 0
                    
                    # Max drawdown
                    cumulative = df['cumulative_return']
                    rolling_max = cumulative.expanding().max()
                    drawdown = (cumulative - rolling_max) / rolling_max
                    max_drawdown = drawdown.min() * 100
                    
                    # Volume profile
                    avg_volume = df['Volume'].mean()
                    volume_consistency = 1 - (df['Volume'].std() / df['Volume'].mean()) if df['Volume'].mean() > 0 else 0
                    
                    self.market_data[symbol] = {
                        'data': df,
                        'returns': df['returns'].dropna(),
                        'total_return': total_return,
                        'volatility': volatility,
                        'sharpe_ratio': sharpe,
                        'max_drawdown': max_drawdown,
                        'avg_volume': avg_volume,
                        'volume_consistency': volume_consistency,
                        'start_price': df['Close'].iloc[0],
                        'end_price': df['Close'].iloc[-1]
                    }
                    successful_fetches += 1
                    
                    if successful_fetches % 10 == 0:
                        print(f"   ✓ {successful_fetches} símbolos procesados...")
                        
            except Exception as e:
                print(f"   ⚠️ Error con {symbol}: {str(e)[:50]}...")
                continue
        
        print(f"✅ Datos obtenidos: {successful_fetches}/{len(self.crypto_universe)} símbolos")
        return successful_fetches > 0
    
    def calculate_correlations(self):
        """
        Calcula correlaciones entre todos los pares
        """
        print("\n📈 Calculando correlaciones...")
        
        # Crear matriz de retornos
        returns_matrix = {}
        for symbol, data in self.market_data.items():
            returns_matrix[symbol] = data['returns']
        
        returns_df = pd.DataFrame(returns_matrix).dropna()
        
        if len(returns_df) < 30:
            print("❌ Datos insuficientes para correlaciones")
            return False
        
        # Calcular matriz de correlación
        self.correlation_matrix = returns_df.corr()
        
        print(f"✅ Matriz de correlación creada ({len(returns_df)} observaciones)")
        return True
    
    def find_similar_assets(self):
        """
        Encuentra activos similares a los top performers
        """
        print("\n🔍 Buscando activos similares a top performers...")
        
        for top_performer in self.top_performers:
            if top_performer not in self.correlation_matrix.index:
                print(f"   ⚠️ {top_performer} no disponible en datos")
                continue
            
            print(f"\n📊 Análisis para {top_performer}:")
            
            # Obtener correlaciones
            correlations = self.correlation_matrix[top_performer].drop(top_performer)
            
            # Filtrar por correlación significativa (0.3-0.8)
            similar_assets = correlations[(correlations >= 0.3) & (correlations <= 0.8)].sort_values(ascending=False)
            
            self.similarity_scores[top_performer] = {}
            
            print(f"   Activos con correlación 0.3-0.8:")
            for asset, corr in similar_assets.head(10).items():
                if asset in self.market_data:
                    # Calcular score de similitud compuesto
                    similarity_score = self.calculate_similarity_score(top_performer, asset, corr)
                    self.similarity_scores[top_performer][asset] = similarity_score
                    
                    performance = self.market_data[asset]['total_return']
                    volatility = self.market_data[asset]['volatility']
                    
                    print(f"     • {asset:<12} Corr: {corr:.3f} | Score: {similarity_score:.3f} | "
                          f"Ret: {performance:+6.1f}% | Vol: {volatility:5.1f}%")
    
    def calculate_similarity_score(self, reference, candidate, correlation):
        """
        Calcula score de similitud compuesto
        """
        ref_data = self.market_data[reference]
        cand_data = self.market_data[candidate]
        
        # Factor 1: Correlación (peso 40%)
        corr_score = abs(correlation)
        
        # Factor 2: Volatilidad similar (peso 25%)
        vol_diff = abs(ref_data['volatility'] - cand_data['volatility']) / ref_data['volatility']
        vol_score = max(0, 1 - vol_diff)
        
        # Factor 3: Performance similar (peso 20%)
        perf_diff = abs(ref_data['total_return'] - cand_data['total_return']) / abs(ref_data['total_return'])
        perf_score = max(0, 1 - perf_diff)
        
        # Factor 4: Sharpe ratio similar (peso 15%)
        sharpe_diff = abs(ref_data['sharpe_ratio'] - cand_data['sharpe_ratio'])
        sharpe_score = max(0, 1 - sharpe_diff)
        
        # Score compuesto
        composite_score = (
            corr_score * 0.40 +
            vol_score * 0.25 +
            perf_score * 0.20 +
            sharpe_score * 0.15
        )
        
        return composite_score
    
    def test_portfolio_combinations(self):
        """
        Prueba diferentes combinaciones de portafolio
        """
        print("\n🧪 Probando combinaciones de portafolio...")
        
        # Seleccionar mejores candidatos por top performer
        portfolio_candidates = {}
        
        for top_performer in self.top_performers:
            if top_performer in self.similarity_scores:
                # Top 3 similares por cada top performer
                sorted_similar = sorted(
                    self.similarity_scores[top_performer].items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                portfolio_candidates[top_performer] = [item[0] for item in sorted_similar[:3]]
        
        print("\n📋 Candidatos por categoría:")
        for performer, candidates in portfolio_candidates.items():
            print(f"   {performer}: {candidates}")
        
        # Generar combinaciones de portafolio
        portfolio_combinations = []
        
        # Portafolio 1: Solo top performers
        portfolio_combinations.append({
            'name': 'Top_Performers_Only',
            'symbols': self.top_performers.copy(),
            'description': 'Solo mejores performers actuales'
        })
        
        # Portafolio 2: Top performers + 1 similar por cada uno
        if all(len(candidates) >= 1 for candidates in portfolio_candidates.values()):
            portfolio_2 = self.top_performers.copy()
            for performer, candidates in portfolio_candidates.items():
                portfolio_2.append(candidates[0])
            
            portfolio_combinations.append({
                'name': 'Diversified_Plus_1',
                'symbols': portfolio_2,
                'description': 'Top performers + 1 similar cada uno'
            })
        
        # Portafolio 3: Máxima diversificación
        if all(len(candidates) >= 2 for candidates in portfolio_candidates.values()):
            portfolio_3 = self.top_performers.copy()
            for performer, candidates in portfolio_candidates.items():
                portfolio_3.extend(candidates[:2])
            
            portfolio_combinations.append({
                'name': 'Maximum_Diversification',
                'symbols': portfolio_3,
                'description': 'Top performers + 2 similares cada uno'
            })
        
        # Portafolio 4: Baja correlación
        low_corr_assets = self.find_low_correlation_assets()
        if len(low_corr_assets) >= 5:
            portfolio_combinations.append({
                'name': 'Low_Correlation',
                'symbols': low_corr_assets[:7],
                'description': 'Activos con baja correlación entre sí'
            })
        
        return portfolio_combinations
    
    def find_low_correlation_assets(self):
        """
        Encuentra activos con baja correlación entre sí
        """
        available_assets = list(self.market_data.keys())
        selected_assets = []
        
        # Empezar con el mejor performer
        if 'ETH-USD' in available_assets:
            selected_assets.append('ETH-USD')
        
        # Agregar activos con baja correlación
        for asset in available_assets:
            if asset in selected_assets:
                continue
            
            # Verificar correlación con activos ya seleccionados
            low_corr = True
            for selected in selected_assets:
                if asset in self.correlation_matrix.index and selected in self.correlation_matrix.columns:
                    corr = abs(self.correlation_matrix.loc[asset, selected])
                    if corr > 0.6:  # Umbral de correlación alta
                        low_corr = False
                        break
            
            if low_corr:
                selected_assets.append(asset)
                
            if len(selected_assets) >= 8:
                break
        
        return selected_assets
    
    def backtest_portfolios(self, portfolio_combinations):
        """
        Ejecuta backtesting para cada combinación de portafolio
        """
        print("\n🚀 Ejecutando backtesting de portafolios...")
        
        results = []
        
        # Período de backtesting
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        for i, portfolio in enumerate(portfolio_combinations, 1):
            print(f"\n📊 Portfolio {i}: {portfolio['name']}")
            print(f"   Símbolos: {portfolio['symbols']}")
            print(f"   Descripción: {portfolio['description']}")
            
            # Filtrar símbolos disponibles
            available_symbols = [s for s in portfolio['symbols'] if s in self.market_data]
            print(f"   Disponibles: {len(available_symbols)}/{len(portfolio['symbols'])}")
            
            if len(available_symbols) < 3:
                print("   ⚠️ Muy pocos símbolos disponibles, saltando...")
                continue
            
            # Ejecutar backtesting
            try:
                trades = self.system.backtest_daily(available_symbols, start_date, end_date)
                
                if trades:
                    # Calcular métricas
                    total_trades = len(trades)
                    winning_trades = sum(1 for t in trades if t['pnl'] > 0)
                    win_rate = (winning_trades / total_trades) * 100
                    
                    total_pnl = sum(t['pnl'] for t in trades)
                    roi = (total_pnl / 10000) * 100
                    
                    gross_wins = sum(t['pnl'] for t in trades if t['pnl'] > 0)
                    gross_losses = abs(sum(t['pnl'] for t in trades if t['pnl'] <= 0))
                    profit_factor = gross_wins / gross_losses if gross_losses > 0 else float('inf')
                    
                    # Calcular diversificación (número de símbolos con trades)
                    symbols_traded = len(set(t['symbol'] for t in trades))
                    diversification_ratio = symbols_traded / len(available_symbols)
                    
                    # Análisis de correlación del portafolio
                    portfolio_correlation = self.calculate_portfolio_correlation(available_symbols)
                    
                    result = {
                        'name': portfolio['name'],
                        'description': portfolio['description'],
                        'symbols': available_symbols,
                        'total_trades': total_trades,
                        'win_rate': win_rate,
                        'total_pnl': total_pnl,
                        'roi': roi,
                        'profit_factor': profit_factor,
                        'symbols_traded': symbols_traded,
                        'diversification_ratio': diversification_ratio,
                        'avg_correlation': portfolio_correlation,
                        'trades': trades
                    }
                    
                    results.append(result)
                    
                    print(f"   ✅ Trades: {total_trades} | WR: {win_rate:.1f}% | "
                          f"ROI: {roi:.1f}% | PF: {profit_factor:.2f}")
                else:
                    print("   ❌ No se generaron trades")
            
            except Exception as e:
                print(f"   ❌ Error en backtesting: {e}")
        
        return results
    
    def calculate_portfolio_correlation(self, symbols):
        """
        Calcula correlación promedio del portafolio
        """
        if len(symbols) < 2:
            return 0
        
        correlations = []
        for i in range(len(symbols)):
            for j in range(i+1, len(symbols)):
                if symbols[i] in self.correlation_matrix.index and symbols[j] in self.correlation_matrix.columns:
                    corr = abs(self.correlation_matrix.loc[symbols[i], symbols[j]])
                    correlations.append(corr)
        
        return np.mean(correlations) if correlations else 0
    
    def analyze_portfolio_results(self, results):
        """
        Analiza y compara resultados de portafolios
        """
        print("\n" + "="*80)
        print("📊 ANÁLISIS COMPARATIVO DE PORTAFOLIOS")
        print("="*80)
        
        if not results:
            print("❌ No hay resultados para analizar")
            return
        
        # Ordenar por ROI
        sorted_results = sorted(results, key=lambda x: x['roi'], reverse=True)
        
        print(f"\n🏆 RANKING DE PORTAFOLIOS:")
        print(f"{'Rank':<5} {'Nombre':<20} {'ROI':<8} {'WR':<8} {'PF':<8} {'Trades':<8} {'Div':<6} {'Corr':<6}")
        print(f"{'-'*5} {'-'*20} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*6} {'-'*6}")
        
        for i, result in enumerate(sorted_results, 1):
            print(f"{i:<5} {result['name'][:19]:<20} {result['roi']:>6.1f}% "
                  f"{result['win_rate']:>6.1f}% {result['profit_factor']:>6.2f} "
                  f"{result['total_trades']:>6} {result['diversification_ratio']:>5.2f} "
                  f"{result['avg_correlation']:>5.3f}")
        
        # Análisis detallado del mejor portafolio
        best_portfolio = sorted_results[0]
        print(f"\n🥇 MEJOR PORTAFOLIO: {best_portfolio['name']}")
        print(f"   📋 Descripción: {best_portfolio['description']}")
        print(f"   🪙 Símbolos ({len(best_portfolio['symbols'])}): {', '.join(best_portfolio['symbols'])}")
        print(f"   📈 ROI: {best_portfolio['roi']:.1f}%")
        print(f"   🎯 Win Rate: {best_portfolio['win_rate']:.1f}%")
        print(f"   ⚖️ Profit Factor: {best_portfolio['profit_factor']:.2f}")
        print(f"   🔄 Diversificación: {best_portfolio['diversification_ratio']:.2f}")
        print(f"   📊 Correlación promedio: {best_portfolio['avg_correlation']:.3f}")
        
        # Análisis por símbolo del mejor portafolio
        best_trades = best_portfolio['trades']
        symbol_performance = {}
        
        for trade in best_trades:
            symbol = trade['symbol']
            if symbol not in symbol_performance:
                symbol_performance[symbol] = {'trades': 0, 'wins': 0, 'pnl': 0}
            
            symbol_performance[symbol]['trades'] += 1
            symbol_performance[symbol]['pnl'] += trade['pnl']
            if trade['pnl'] > 0:
                symbol_performance[symbol]['wins'] += 1
        
        print(f"\n📊 PERFORMANCE POR SÍMBOLO (Mejor Portafolio):")
        for symbol, perf in sorted(symbol_performance.items(), key=lambda x: x[1]['pnl'], reverse=True):
            wr = (perf['wins'] / perf['trades'] * 100) if perf['trades'] > 0 else 0
            print(f"   • {symbol:<12} {perf['trades']} trades | {wr:5.1f}% WR | ${perf['pnl']:+7.2f} P&L")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        
        # Evaluar diversificación
        if best_portfolio['avg_correlation'] < 0.3:
            print("   ✅ Excelente diversificación - Baja correlación")
        elif best_portfolio['avg_correlation'] < 0.6:
            print("   🟡 Buena diversificación - Correlación moderada")
        else:
            print("   ⚠️ Mejorar diversificación - Alta correlación")
        
        # Evaluar performance
        if best_portfolio['roi'] > 30:
            print("   ✅ Excelente rentabilidad")
        elif best_portfolio['roi'] > 15:
            print("   🟡 Buena rentabilidad")
        else:
            print("   ⚠️ Rentabilidad mejorable")
        
        # Evaluar estabilidad
        if best_portfolio['win_rate'] > 60 and best_portfolio['profit_factor'] > 2:
            print("   ✅ Sistema estable y consistente")
        elif best_portfolio['win_rate'] > 50 and best_portfolio['profit_factor'] > 1.5:
            print("   🟡 Sistema aceptable")
        else:
            print("   ⚠️ Sistema necesita optimización")
        
        return sorted_results
    
    def create_final_recommendations(self, results):
        """
        Crea recomendaciones finales para implementación
        """
        print("\n" + "="*80)
        print("🎯 RECOMENDACIONES FINALES DE IMPLEMENTACIÓN")
        print("="*80)
        
        if not results:
            return
        
        best_portfolio = results[0]
        
        print(f"\n📋 PORTAFOLIO RECOMENDADO:")
        print(f"   Nombre: {best_portfolio['name']}")
        print(f"   Símbolos: {', '.join(best_portfolio['symbols'])}")
        
        print(f"\n💰 ASIGNACIÓN DE CAPITAL SUGERIDA:")
        total_symbols = len(best_portfolio['symbols'])
        
        # Asignación basada en performance individual
        symbol_performance = {}
        for trade in best_portfolio['trades']:
            symbol = trade['symbol']
            if symbol not in symbol_performance:
                symbol_performance[symbol] = 0
            symbol_performance[symbol] += trade['pnl']
        
        # Normalizar asignaciones
        total_performance = sum(max(0, perf) for perf in symbol_performance.values())
        
        if total_performance > 0:
            print("   Asignación basada en performance:")
            for symbol in best_portfolio['symbols']:
                if symbol in symbol_performance and symbol_performance[symbol] > 0:
                    allocation = (symbol_performance[symbol] / total_performance) * 100
                    allocation = max(5, min(25, allocation))  # Entre 5% y 25%
                else:
                    allocation = 100 / total_symbols
                
                print(f"   • {symbol}: {allocation:.1f}%")
        else:
            print("   Asignación equitativa:")
            allocation = 100 / total_symbols
            for symbol in best_portfolio['symbols']:
                print(f"   • {symbol}: {allocation:.1f}%")
        
        print(f"\n🎯 PLAN DE IMPLEMENTACIÓN:")
        print("1. 📊 Comenzar con paper trading 2 semanas")
        print("2. 💰 Capital inicial sugerido: $1,000-$5,000")
        print("3. 📈 Escalar gradualmente según resultados")
        print("4. 🔄 Re-evaluar portafolio cada 30 días")
        print("5. ⚠️ Stop loss de portafolio: -10% en una semana")
        
        print(f"\n⚡ CONFIGURACIÓN DEL SISTEMA:")
        print("• Risk per trade: 1% (ya configurado)")
        print("• Max daily trades: 3 (ya configurado)")
        print("• Confidence threshold: 40% (ya configurado)")
        print("• Timeframes: 15m, 1h, 4h (ya configurado)")
        print("• Trend filters: Activados (ya configurado)")


def main():
    """
    Función principal del análisis de optimización
    """
    print("🚀 ANÁLISIS DE OPTIMIZACIÓN DE PORTAFOLIO")
    print("="*80)
    print("Objetivo: Encontrar pares similares a ETH, BNB, SOL")
    print("para crear un portafolio diversificado y optimizado")
    print("="*80)
    
    optimizer = PortfolioOptimizer()
    
    # Paso 1: Obtener datos de mercado
    if not optimizer.fetch_market_data(days=90):
        print("❌ Error obteniendo datos de mercado")
        return
    
    # Paso 2: Calcular correlaciones
    if not optimizer.calculate_correlations():
        print("❌ Error calculando correlaciones")
        return
    
    # Paso 3: Encontrar activos similares
    optimizer.find_similar_assets()
    
    # Paso 4: Generar combinaciones de portafolio
    portfolio_combinations = optimizer.test_portfolio_combinations()
    
    # Paso 5: Ejecutar backtesting
    results = optimizer.backtest_portfolios(portfolio_combinations)
    
    # Paso 6: Analizar resultados
    sorted_results = optimizer.analyze_portfolio_results(results)
    
    # Paso 7: Crear recomendaciones finales
    optimizer.create_final_recommendations(sorted_results)
    
    print("\n" + "="*80)
    print("✅ ANÁLISIS DE OPTIMIZACIÓN COMPLETADO")
    print("="*80)
    
    return optimizer, results


if __name__ == "__main__":
    optimizer, results = main()