#!/usr/bin/env python3
"""
Backtesting en Tiempo Real
Sistema híbrido con validación continua de performance
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

class BacktestingTiempoReal:
    """
    Sistema de backtesting que simula trading en tiempo real
    con el sistema híbrido optimizado
    """
    
    def __init__(self, capital_inicial=10000):
        self.capital_inicial = capital_inicial
        self.capital_actual = capital_inicial
        self.trades_activos = []
        self.trades_cerrados = []
        self.equity_curve = []
        
        # Configuración optimizada
        self.max_risk_per_trade = 0.02
        self.trailing_activation = 0.015  # 1.5%
        self.trailing_distance = 0.005   # 0.5%
        
        # Métricas de performance
        self.total_trades = 0
        self.trades_ganadores = 0
        self.profit_factor = 0
        
    def calcular_indicadores_rapidos(self, df):
        """Calcula indicadores técnicos optimizados para velocidad"""
        
        # Solo calcular lo esencial
        df['EMA_8'] = df['Close'].ewm(span=8).mean()
        df['EMA_21'] = df['Close'].ewm(span=21).mean()
        
        # RSI simplificado
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # ATR
        high_low = df['High'] - df['Low']
        df['ATR'] = high_low.rolling(14).mean()
        
        # Volumen
        df['Volume_Ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()
        
        return df
    
    def detectar_volume_breakout(self, df, ticker):
        """
        Detecta volume breakouts en tiempo real
        Estrategia principal basada en 67% WR en backtests
        """
        if len(df) < 50:
            return None
            
        current = df.iloc[-1]
        lookback = df.iloc[-25:]  # Últimas 25 velas
        
        # Verificar volumen excepcional
        if pd.isna(current['Volume_Ratio']) or current['Volume_Ratio'] < 2.0:
            return None
        
        # Definir rango
        recent_high = lookback['High'].max()
        recent_low = lookback['Low'].min()
        range_size = recent_high - recent_low
        
        if range_size < current['Close'] * 0.015:  # Rango mínimo 1.5%
            return None
        
        signal = None
        
        # BREAKOUT ALCISTA
        if (current['Close'] > recent_high * 0.9995 and
            current['RSI'] > 55 and current['RSI'] < 80 and
            current['Volume_Ratio'] > 2.5):
            
            signal = {
                'ticker': ticker,
                'type': 'LONG',
                'entry_price': current['Close'],
                'stop_loss': recent_high * 0.985,
                'take_profit': current['Close'] + (range_size * 1.5),
                'timestamp': df.index[-1],
                'strategy': 'Volume Breakout',
                'volume_ratio': current['Volume_Ratio'],
                'rsi': current['RSI']
            }
        
        # BREAKDOWN BAJISTA
        elif (current['Close'] < recent_low * 1.0005 and
              current['RSI'] < 45 and current['RSI'] > 20 and
              current['Volume_Ratio'] > 2.5):
            
            signal = {
                'ticker': ticker,
                'type': 'SHORT',
                'entry_price': current['Close'],
                'stop_loss': recent_low * 1.015,
                'take_profit': current['Close'] - (range_size * 1.5),
                'timestamp': df.index[-1],
                'strategy': 'Volume Breakout',
                'volume_ratio': current['Volume_Ratio'],
                'rsi': current['RSI']
            }
        
        # Verificar R:R mínimo
        if signal:
            risk = abs(signal['entry_price'] - signal['stop_loss'])
            reward = abs(signal['take_profit'] - signal['entry_price'])
            rr_ratio = reward / risk if risk > 0 else 0
            
            if rr_ratio >= 1.8:
                signal['risk_reward'] = rr_ratio
                return signal
        
        return None
    
    def calcular_position_size(self, signal):
        """Calcula tamaño de posición basado en riesgo"""
        
        risk_pct = abs(signal['entry_price'] - signal['stop_loss']) / signal['entry_price']
        max_position = self.max_risk_per_trade / risk_pct
        
        # Limitar entre 3% y 8%
        return max(0.03, min(0.08, max_position))
    
    def ejecutar_trade(self, signal):
        """Ejecuta un trade nuevo"""
        
        position_size = self.calcular_position_size(signal)
        position_value = self.capital_actual * position_size
        
        trade = {
            'id': len(self.trades_activos) + len(self.trades_cerrados),
            'ticker': signal['ticker'],
            'type': signal['type'],
            'entry_price': signal['entry_price'],
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'position_size': position_size,
            'position_value': position_value,
            'entry_time': signal['timestamp'],
            'strategy': signal['strategy'],
            'risk_reward': signal['risk_reward'],
            'trailing_stop': None,
            'status': 'ACTIVE'
        }
        
        self.trades_activos.append(trade)
        print(f"✅ Trade #{trade['id']} ejecutado: {trade['ticker']} {trade['type']} @ ${trade['entry_price']:.2f}")
        return trade
    
    def gestionar_trailing_stops(self, trade, current_price):
        """Gestiona trailing stops dinámicos"""
        
        if trade['type'] == 'LONG':
            # Calcular ganancia actual
            current_profit = (current_price - trade['entry_price']) / trade['entry_price']
            
            if current_profit >= self.trailing_activation:
                # Activar trailing stop
                new_trailing = current_price * (1 - self.trailing_distance)
                
                if trade['trailing_stop'] is None or new_trailing > trade['trailing_stop']:
                    trade['trailing_stop'] = new_trailing
                    return True
        else:  # SHORT
            current_profit = (trade['entry_price'] - current_price) / trade['entry_price']
            
            if current_profit >= self.trailing_activation:
                new_trailing = current_price * (1 + self.trailing_distance)
                
                if trade['trailing_stop'] is None or new_trailing < trade['trailing_stop']:
                    trade['trailing_stop'] = new_trailing
                    return True
        
        return False
    
    def verificar_salidas(self, ticker_data):
        """Verifica condiciones de salida para trades activos"""
        
        trades_cerrados_ahora = []
        
        for trade in self.trades_activos[:]:  # Copia para modificar durante iteración
            ticker = trade['ticker']
            
            if ticker not in ticker_data:
                continue
                
            current_bar = ticker_data[ticker].iloc[-1]
            current_price = current_bar['Close']
            
            exit_price = None
            exit_reason = None
            
            # Gestionar trailing stops
            self.gestionar_trailing_stops(trade, current_price)
            
            if trade['type'] == 'LONG':
                # Verificar take profit
                if current_bar['High'] >= trade['take_profit']:
                    exit_price = trade['take_profit']
                    exit_reason = 'TP'
                # Verificar stop loss
                elif current_bar['Low'] <= trade['stop_loss']:
                    exit_price = trade['stop_loss']
                    exit_reason = 'SL'
                # Verificar trailing stop
                elif trade['trailing_stop'] and current_bar['Low'] <= trade['trailing_stop']:
                    exit_price = trade['trailing_stop']
                    exit_reason = 'TRAIL'
            
            else:  # SHORT
                if current_bar['Low'] <= trade['take_profit']:
                    exit_price = trade['take_profit']
                    exit_reason = 'TP'
                elif current_bar['High'] >= trade['stop_loss']:
                    exit_price = trade['stop_loss']
                    exit_reason = 'SL'
                elif trade['trailing_stop'] and current_bar['High'] >= trade['trailing_stop']:
                    exit_price = trade['trailing_stop']
                    exit_reason = 'TRAIL'
            
            # Cerrar trade si hay señal de salida
            if exit_price:
                self.cerrar_trade(trade, exit_price, exit_reason, ticker_data[ticker].index[-1])
                trades_cerrados_ahora.append(trade)
        
        return trades_cerrados_ahora
    
    def cerrar_trade(self, trade, exit_price, exit_reason, exit_time):
        """Cierra un trade y actualiza métricas"""
        
        # Calcular P&L
        if trade['type'] == 'LONG':
            profit_pct = (exit_price - trade['entry_price']) / trade['entry_price']
        else:
            profit_pct = (trade['entry_price'] - exit_price) / trade['entry_price']
        
        profit_usd = trade['position_value'] * profit_pct
        
        # Actualizar capital
        self.capital_actual += profit_usd
        
        # Actualizar trade
        trade.update({
            'exit_price': exit_price,
            'exit_time': exit_time,
            'exit_reason': exit_reason,
            'profit_pct': profit_pct * 100,
            'profit_usd': profit_usd,
            'status': 'CLOSED'
        })
        
        # Mover a trades cerrados
        self.trades_activos.remove(trade)
        self.trades_cerrados.append(trade)
        
        # Actualizar métricas
        self.total_trades += 1
        if profit_pct > 0:
            self.trades_ganadores += 1
        
        # Mostrar resultado
        emoji = "🟢" if profit_pct > 0 else "🔴"
        print(f"{emoji} Trade #{trade['id']} cerrado: {exit_reason} | {profit_pct*100:+.2f}% | ${profit_usd:+.2f}")
        
        return trade
    
    def simular_periodo(self, start_date, end_date, tickers):
        """
        Simula trading en un período específico
        """
        print(f"\n🔄 SIMULANDO PERÍODO: {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")
        print("="*60)
        
        # Descargar datos para todo el período
        ticker_data = {}
        for ticker in tickers:
            try:
                data = yf.Ticker(ticker)
                df = data.history(start=start_date - timedelta(days=30), 
                                 end=end_date + timedelta(days=1), 
                                 interval='1h')
                
                if len(df) > 50:
                    df = self.calcular_indicadores_rapidos(df)
                    ticker_data[ticker] = df
            except:
                continue
        
        if not ticker_data:
            print("❌ No se pudieron descargar datos")
            return
        
        # Obtener todas las fechas únicas
        all_timestamps = set()
        for df in ticker_data.values():
            all_timestamps.update(df.index)
        
        timestamps_ordenados = sorted([ts for ts in all_timestamps 
                                     if start_date.date() <= ts.date() <= end_date.date()])
        
        print(f"📊 Simulando {len(timestamps_ordenados)} períodos...")
        
        # Simular hora por hora
        for i, timestamp in enumerate(timestamps_ordenados):
            
            # Obtener datos hasta este punto
            current_data = {}
            for ticker, df in ticker_data.items():
                mask = df.index <= timestamp
                if mask.sum() > 50:  # Suficientes datos para indicadores
                    current_data[ticker] = df[mask]
            
            # Buscar nuevas señales
            for ticker, df in current_data.items():
                if len(self.trades_activos) < 3:  # Máximo 3 trades concurrentes
                    signal = self.detectar_volume_breakout(df, ticker)
                    if signal:
                        self.ejecutar_trade(signal)
            
            # Gestionar trades existentes
            trades_cerrados = self.verificar_salidas(current_data)
            
            # Actualizar equity curve cada 24 horas
            if i % 24 == 0:
                equity_actual = self.capital_actual
                
                # Añadir P&L no realizado
                for trade in self.trades_activos:
                    if trade['ticker'] in current_data:
                        current_price = current_data[trade['ticker']]['Close'].iloc[-1]
                        if trade['type'] == 'LONG':
                            unrealized_pct = (current_price - trade['entry_price']) / trade['entry_price']
                        else:
                            unrealized_pct = (trade['entry_price'] - current_price) / trade['entry_price']
                        
                        equity_actual += trade['position_value'] * unrealized_pct
                
                self.equity_curve.append({
                    'timestamp': timestamp,
                    'equity': equity_actual,
                    'drawdown': (equity_actual / self.capital_inicial - 1) * 100,
                    'trades_activos': len(self.trades_activos),
                    'trades_cerrados': len(self.trades_cerrados)
                })
        
        # Cerrar trades restantes al final del período
        for trade in self.trades_activos[:]:
            if trade['ticker'] in ticker_data:
                final_price = ticker_data[trade['ticker']]['Close'].iloc[-1]
                self.cerrar_trade(trade, final_price, 'TIME', timestamps_ordenados[-1])
    
    def analizar_resultados(self):
        """Analiza y muestra resultados del backtesting"""
        
        if not self.trades_cerrados:
            print("❌ No hay trades cerrados para analizar")
            return
        
        # Métricas básicas
        total_trades = len(self.trades_cerrados)
        trades_ganadores = len([t for t in self.trades_cerrados if t['profit_pct'] > 0])
        win_rate = (trades_ganadores / total_trades) * 100
        
        profits = [t['profit_pct'] for t in self.trades_cerrados if t['profit_pct'] > 0]
        losses = [t['profit_pct'] for t in self.trades_cerrados if t['profit_pct'] <= 0]
        
        avg_win = np.mean(profits) if profits else 0
        avg_loss = np.mean(losses) if losses else 0
        
        # Profit Factor
        gross_profit = sum(profits) if profits else 0
        gross_loss = abs(sum(losses)) if losses else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Retorno total
        total_return = (self.capital_actual / self.capital_inicial - 1) * 100
        
        print(f"\n📊 RESULTADOS DEL BACKTESTING")
        print("="*50)
        print(f"• Capital inicial: ${self.capital_inicial:,.2f}")
        print(f"• Capital final: ${self.capital_actual:,.2f}")
        print(f"• Retorno total: {total_return:+.2f}%")
        print(f"• Total trades: {total_trades}")
        print(f"• Win rate: {win_rate:.1f}%")
        print(f"• Profit factor: {profit_factor:.2f}")
        print(f"• Avg win: {avg_win:+.2f}%")
        print(f"• Avg loss: {avg_loss:+.2f}%")
        
        # Análisis por salida
        exit_reasons = {}
        for trade in self.trades_cerrados:
            reason = trade['exit_reason']
            if reason not in exit_reasons:
                exit_reasons[reason] = []
            exit_reasons[reason].append(trade['profit_pct'])
        
        print(f"\n🎯 ANÁLISIS POR SALIDA:")
        for reason, profits in exit_reasons.items():
            reason_wr = (len([p for p in profits if p > 0]) / len(profits)) * 100
            reason_avg = np.mean(profits)
            print(f"• {reason}: {len(profits)} trades, WR: {reason_wr:.0f}%, Avg: {reason_avg:+.2f}%")
        
        # Mejores y peores trades
        best_trade = max(self.trades_cerrados, key=lambda t: t['profit_pct'])
        worst_trade = min(self.trades_cerrados, key=lambda t: t['profit_pct'])
        
        print(f"\n🏆 MEJOR TRADE: {best_trade['ticker']} {best_trade['type']} ({best_trade['profit_pct']:+.2f}%)")
        print(f"💥 PEOR TRADE: {worst_trade['ticker']} {worst_trade['type']} ({worst_trade['profit_pct']:+.2f}%)")
        
        # Evaluación
        if win_rate >= 65:
            grade = "🌟 EXCELENTE"
        elif win_rate >= 60:
            grade = "✅ BUENO"
        elif win_rate >= 50:
            grade = "⚠️ REGULAR"
        else:
            grade = "❌ MALO"
        
        print(f"\n🏆 CALIFICACIÓN: {grade}")
        
        return {
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'total_trades': total_trades,
            'grade': grade
        }

def main():
    """Función principal de backtesting"""
    
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║                    BACKTESTING EN TIEMPO REAL                          ║
║                 Sistema Híbrido de Alto Rendimiento                    ║
╚════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Crear sistema
    backtest = BacktestingTiempoReal(capital_inicial=10000)
    
    # Tickers principales
    tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD']
    
    # Períodos de análisis
    periods = [
        {
            'name': 'Últimos 7 días',
            'start': datetime.now() - timedelta(days=7),
            'end': datetime.now()
        },
        {
            'name': 'Últimos 14 días',
            'start': datetime.now() - timedelta(days=14),
            'end': datetime.now() - timedelta(days=7)
        }
    ]
    
    all_results = []
    
    # Ejecutar backtesting por períodos
    for period in periods:
        print(f"\n🔄 EJECUTANDO: {period['name']}")
        
        # Reset del sistema
        backtest = BacktestingTiempoReal(capital_inicial=10000)
        
        # Simular período
        backtest.simular_periodo(period['start'], period['end'], tickers)
        
        # Analizar resultados
        result = backtest.analizar_resultados()
        if result:
            result['period'] = period['name']
            all_results.append(result)
    
    # Resumen consolidado
    if all_results:
        print(f"\n{'='*60}")
        print("📊 RESUMEN CONSOLIDADO")
        print(f"{'='*60}")
        
        avg_wr = np.mean([r['win_rate'] for r in all_results])
        avg_pf = np.mean([r['profit_factor'] for r in all_results])
        avg_return = np.mean([r['total_return'] for r in all_results])
        
        print(f"• Win Rate promedio: {avg_wr:.1f}%")
        print(f"• Profit Factor promedio: {avg_pf:.2f}")
        print(f"• Retorno promedio: {avg_return:+.1f}%")
        
        # Evaluación final
        if avg_wr >= 65:
            print(f"\n🎯 OBJETIVO ALCANZADO: {avg_wr:.1f}% WR (target: 60-70%)")
            print("✅ Sistema listo para trading en vivo")
        elif avg_wr >= 60:
            print(f"\n✅ BUEN RESULTADO: {avg_wr:.1f}% WR")
            print("🔧 Ajustes menores recomendados")
        else:
            print(f"\n⚠️ RESULTADO INSUFICIENTE: {avg_wr:.1f}% WR")
            print("🔄 Optimización necesaria")

if __name__ == "__main__":
    main()