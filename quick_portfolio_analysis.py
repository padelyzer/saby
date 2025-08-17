#!/usr/bin/env python3
"""
Análisis Rápido de Portafolio Optimizado
Enfocado en ETH, BNB, SOL y similares
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from daily_trading_system_v2 import DailyTradingSystemV2

class QuickPortfolioAnalysis:
    """
    Análisis rápido y enfocado de portafolio
    """
    
    def __init__(self):
        self.system = DailyTradingSystemV2(initial_capital=10000)
        
        # Top performers confirmados
        self.top_performers = ['ETH-USD', 'BNB-USD', 'SOL-USD']
        
        # Candidatos similares basados en categorías
        self.similar_candidates = {
            'ETH_ecosystem': ['AAVE-USD', 'UNI-USD', 'MKR-USD', 'LTC-USD'],
            'BNB_similar': ['ADA-USD', 'AVAX-USD', 'DOT-USD', 'NEAR-USD'],
            'SOL_ecosystem': ['ATOM-USD', 'FTM-USD', 'ALGO-USD', 'MANA-USD']
        }
        
        # Portfolios a probar
        self.portfolios = {
            'Top_Only': self.top_performers,
            'Diversified_Small': self.top_performers + ['AAVE-USD', 'ADA-USD', 'ATOM-USD'],
            'Diversified_Medium': self.top_performers + ['AAVE-USD', 'UNI-USD', 'ADA-USD', 'AVAX-USD', 'ATOM-USD', 'FTM-USD'],
            'Conservative': ['ETH-USD', 'BNB-USD', 'ADA-USD', 'AVAX-USD'],
            'Aggressive': ['SOL-USD', 'AAVE-USD', 'UNI-USD', 'ATOM-USD', 'FTM-USD']
        }
    
    def quick_market_analysis(self, symbols, days=30):
        """
        Análisis rápido de mercado
        """
        print(f"📊 Análisis de mercado - {days} días")
        
        market_data = {}
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=start_date, end=end_date, interval='1d')
                
                if len(df) > 10:
                    performance = ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100
                    volatility = df['Close'].pct_change().std() * np.sqrt(252) * 100
                    
                    market_data[symbol] = {
                        'performance': performance,
                        'volatility': volatility,
                        'data_available': True
                    }
                else:
                    market_data[symbol] = {
                        'performance': 0,
                        'volatility': 0,
                        'data_available': False
                    }
                    
            except Exception as e:
                market_data[symbol] = {
                    'performance': 0,
                    'volatility': 0,
                    'data_available': False
                }
        
        return market_data
    
    def backtest_portfolio(self, portfolio_name, symbols):
        """
        Backtest rápido de un portafolio
        """
        print(f"\n🧪 Testing {portfolio_name}:")
        print(f"   Símbolos: {symbols}")
        
        # Filtrar símbolos disponibles
        available_symbols = []
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                test_data = ticker.history(period='5d', interval='1d')
                if len(test_data) > 0:
                    available_symbols.append(symbol)
            except:
                continue
        
        print(f"   Disponibles: {len(available_symbols)}/{len(symbols)}")
        
        if len(available_symbols) < 2:
            print("   ❌ Muy pocos símbolos disponibles")
            return None
        
        # Backtest
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
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
                
                # Diversificación
                symbols_traded = len(set(t['symbol'] for t in trades))
                diversification = symbols_traded / len(available_symbols)
                
                result = {
                    'name': portfolio_name,
                    'symbols': available_symbols,
                    'total_trades': total_trades,
                    'win_rate': win_rate,
                    'roi': roi,
                    'profit_factor': profit_factor,
                    'total_pnl': total_pnl,
                    'diversification': diversification,
                    'symbols_traded': symbols_traded
                }
                
                print(f"   ✅ {total_trades} trades | {win_rate:.1f}% WR | {roi:.1f}% ROI | {profit_factor:.2f} PF")
                return result
            else:
                print("   ❌ No trades generados")
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None
    
    def run_analysis(self):
        """
        Ejecuta análisis completo
        """
        print("🚀 ANÁLISIS RÁPIDO DE PORTAFOLIO OPTIMIZADO")
        print("="*60)
        print("Objetivo: Encontrar el mejor portafolio basado en ETH, BNB, SOL")
        print("="*60)
        
        # Paso 1: Análisis de mercado
        all_symbols = set()
        for symbols in self.portfolios.values():
            all_symbols.update(symbols)
        
        market_data = self.quick_market_analysis(list(all_symbols))
        
        print(f"\n📈 Top performers últimos 30 días:")
        sorted_performance = sorted(
            [(s, d) for s, d in market_data.items() if d['data_available']], 
            key=lambda x: x[1]['performance'], 
            reverse=True
        )[:10]
        
        for symbol, data in sorted_performance:
            print(f"   • {symbol:<12} {data['performance']:+6.1f}% (Vol: {data['volatility']:5.1f}%)")
        
        # Paso 2: Backtest de portafolios
        print(f"\n🧪 BACKTESTING DE PORTAFOLIOS:")
        print("-"*60)
        
        results = []
        for name, symbols in self.portfolios.items():
            result = self.backtest_portfolio(name, symbols)
            if result:
                results.append(result)
        
        # Paso 3: Análisis de resultados
        if results:
            print(f"\n📊 RANKING DE PORTAFOLIOS:")
            print(f"{'Rank':<5} {'Nombre':<18} {'ROI':<8} {'WR':<8} {'PF':<6} {'Trades':<7} {'Div':<5}")
            print("-"*60)
            
            sorted_results = sorted(results, key=lambda x: x['roi'], reverse=True)
            
            for i, result in enumerate(sorted_results, 1):
                print(f"{i:<5} {result['name']:<18} {result['roi']:>6.1f}% "
                      f"{result['win_rate']:>6.1f}% {result['profit_factor']:>5.2f} "
                      f"{result['total_trades']:>5} {result['diversification']:>4.2f}")
            
            # Mejor portafolio
            best = sorted_results[0]
            print(f"\n🏆 MEJOR PORTAFOLIO: {best['name']}")
            print(f"   📋 Símbolos: {', '.join(best['symbols'])}")
            print(f"   📈 ROI: {best['roi']:.1f}%")
            print(f"   🎯 Win Rate: {best['win_rate']:.1f}%")
            print(f"   ⚖️ Profit Factor: {best['profit_factor']:.2f}")
            print(f"   🔄 Diversificación: {best['diversification']:.2f}")
            
            # Recomendaciones
            print(f"\n💡 RECOMENDACIONES:")
            
            if best['roi'] > 50:
                print("   ✅ Excelente rendimiento - Listo para implementar")
            elif best['roi'] > 30:
                print("   🟡 Buen rendimiento - Validar con más días")
            else:
                print("   ⚠️ Rendimiento moderado - Considerar ajustes")
            
            if best['win_rate'] > 60 and best['profit_factor'] > 2:
                print("   ✅ Métricas de calidad excelentes")
            elif best['win_rate'] > 50 and best['profit_factor'] > 1.5:
                print("   🟡 Métricas aceptables")
            else:
                print("   ⚠️ Mejorar selectividad del sistema")
            
            if best['diversification'] > 0.7:
                print("   ✅ Buena diversificación - Múltiples activos activos")
            else:
                print("   ⚠️ Poca diversificación - Revisar filtros")
            
            # Plan de implementación
            print(f"\n🎯 PLAN DE IMPLEMENTACIÓN:")
            print("1. 📊 Paper trading 1-2 semanas")
            print("2. 💰 Capital inicial: $2,000-$5,000")
            print(f"3. 🪙 Asignación: {100/len(best['symbols']):.1f}% por activo")
            print("4. 🔄 Re-evaluación semanal")
            print("5. ⚠️ Stop loss portafolio: -15% semanal")
            
            return sorted_results
        else:
            print("❌ No se pudieron generar resultados")
            return []


def main():
    """
    Función principal
    """
    analyzer = QuickPortfolioAnalysis()
    results = analyzer.run_analysis()
    
    print("\n" + "="*60)
    print("✅ ANÁLISIS COMPLETADO")
    print("="*60)
    
    return results


if __name__ == "__main__":
    results = main()