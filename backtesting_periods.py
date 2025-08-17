#!/usr/bin/env python3
"""
Backtesting Exhaustivo por Períodos
Objetivo: 80%+ Win Rate con análisis temporal detallado
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class HighWinRateSystem:
    """Sistema diseñado para 80%+ win rate"""
    
    def __init__(self):
        self.min_score = 8  # Score muy alto para máxima precisión
        self.position_size = 0.05  # 5% conservador
        self.max_risk = 0.015  # Máximo 1.5% riesgo por trade
        self.min_volume_ratio = 2.0  # Solo alto volumen
        self.min_rsi_divergence = 5  # Divergencia mínima RSI
        
    def calculate_advanced_rsi(self, df, period=14):
        """RSI con suavizado para menos ruido"""
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Suavizar RSI para reducir falsas señales
        rsi_smooth = rsi.rolling(3).mean()
        return rsi_smooth
    
    def detect_rsi_divergence(self, df, lookback=10):
        """Detecta divergencias RSI para alta precisión"""
        if len(df) < lookback + 14:
            return False, 0
        
        prices = df['Close'].tail(lookback)
        rsi = self.calculate_advanced_rsi(df).tail(lookback)
        
        # Encontrar extremos
        price_high_idx = prices.idxmax()
        price_low_idx = prices.idxmin()
        rsi_high_idx = rsi.idxmax()
        rsi_low_idx = rsi.idxmin()
        
        # Divergencia alcista: precio baja, RSI sube
        if (price_low_idx < price_high_idx and 
            rsi_low_idx < rsi_high_idx and
            rsi.iloc[-1] > rsi.iloc[0] + self.min_rsi_divergence):
            return True, 3  # Bullish divergence
        
        # Divergencia bajista: precio sube, RSI baja
        elif (price_high_idx < price_low_idx and 
              rsi_high_idx < rsi_low_idx and
              rsi.iloc[-1] < rsi.iloc[0] - self.min_rsi_divergence):
            return True, -3  # Bearish divergence
        
        return False, 0
    
    def calculate_trend_strength(self, df, period=50):
        """Calcula fuerza de tendencia con ADX simplificado"""
        if len(df) < period:
            return 0
        
        # Calcular pendiente de regresión
        prices = df['Close'].tail(period)
        x = np.arange(len(prices))
        slope, _ = np.polyfit(x, prices, 1)
        
        # Normalizar pendiente
        trend_strength = (slope / prices.iloc[-1]) * 100 * period
        
        # R-squared para confirmar tendencia
        y_pred = slope * x + np.mean(prices)
        ss_res = np.sum((prices - y_pred) ** 2)
        ss_tot = np.sum((prices - np.mean(prices)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        
        # Solo tendencias claras
        if r_squared > 0.7:  # Alta correlación
            return trend_strength
        
        return 0
    
    def find_support_resistance_zones(self, df, lookback=100):
        """Encuentra zonas de S/R muy precisas"""
        if len(df) < lookback:
            return []
        
        # Encontrar pivotes usando método de ventana deslizante
        pivots = []
        
        for i in range(5, len(df)-5):
            high = df['High'].iloc[i]
            low = df['Low'].iloc[i]
            
            # Pivot high
            if all(high >= df['High'].iloc[i-j] for j in range(1, 6)) and \
               all(high >= df['High'].iloc[i+j] for j in range(1, 6)):
                pivots.append({'price': high, 'type': 'resistance', 'strength': 1})
            
            # Pivot low
            elif all(low <= df['Low'].iloc[i-j] for j in range(1, 6)) and \
                 all(low <= df['Low'].iloc[i+j] for j in range(1, 6)):
                pivots.append({'price': low, 'type': 'support', 'strength': 1})
        
        # Agrupar pivotes cercanos
        zones = []
        tolerance = 0.005  # 0.5%
        
        for pivot in pivots:
            # Buscar zona existente
            found_zone = False
            for zone in zones:
                if abs(pivot['price'] - zone['price']) / zone['price'] < tolerance:
                    zone['strength'] += 1
                    zone['price'] = (zone['price'] + pivot['price']) / 2  # Promedio
                    found_zone = True
                    break
            
            if not found_zone:
                zones.append(pivot)
        
        # Filtrar zonas fuertes (mínimo 3 toques)
        strong_zones = [z for z in zones if z['strength'] >= 3]
        
        return strong_zones
    
    def generate_high_precision_signals(self, df, ticker):
        """Genera señales con 80%+ win rate"""
        if len(df) < 200:
            return []
        
        signals = []
        current_price = df['Close'].iloc[-1]
        
        # Indicadores
        rsi = self.calculate_advanced_rsi(df).iloc[-1]
        volume_ratio = df['Volume'].iloc[-1] / df['Volume'].rolling(50).mean().iloc[-1]
        
        # ATR para stops
        high_low = df['High'] - df['Low']
        atr = high_low.rolling(20).mean().iloc[-1]
        
        # Medias móviles múltiples
        ema_8 = df['Close'].ewm(span=8).mean().iloc[-1]
        ema_21 = df['Close'].ewm(span=21).mean().iloc[-1]
        ema_55 = df['Close'].ewm(span=55).mean().iloc[-1]
        ema_200 = df['Close'].ewm(span=200).mean().iloc[-1]
        
        # Bollinger Bands
        bb_period = 20
        bb_middle = df['Close'].rolling(bb_period).mean().iloc[-1]
        bb_std = df['Close'].rolling(bb_period).std().iloc[-1]
        bb_upper = bb_middle + (bb_std * 2.5)  # Bandas más amplias
        bb_lower = bb_middle - (bb_std * 2.5)
        
        # Detectar patrones de alta probabilidad
        trend_strength = self.calculate_trend_strength(df)
        has_divergence, div_direction = self.detect_rsi_divergence(df)
        sr_zones = self.find_support_resistance_zones(df)
        
        # === CONDICIONES ULTRA SELECTIVAS ===
        
        score = 0
        signal_type = None
        reasons = []
        
        # SEÑAL LONG - Condiciones muy estrictas
        long_conditions = [
            # 1. Tendencia alcista confirmada
            (current_price > ema_8 > ema_21 > ema_55 > ema_200, 3, "Alineación EMAs perfecta"),
            
            # 2. RSI en zona óptima
            (25 < rsi < 45, 2, "RSI oversold controlado"),
            
            # 3. Divergencia alcista
            (has_divergence and div_direction > 0, 4, "Divergencia RSI alcista"),
            
            # 4. Cerca de BB inferior pero no extremo
            (bb_lower < current_price < bb_lower * 1.02, 2, "Cerca BB inferior"),
            
            # 5. Volumen excepcional
            (volume_ratio > self.min_volume_ratio, 2, f"Volumen {volume_ratio:.1f}x"),
            
            # 6. Rebote en soporte fuerte
            (any(abs(current_price - zone['price'])/current_price < 0.01 
                 and zone['type'] == 'support' and zone['strength'] >= 3 
                 for zone in sr_zones), 3, "Rebote en soporte fuerte"),
            
            # 7. Momentum reciente positivo
            (df['Close'].iloc[-1] > df['Close'].iloc[-3], 1, "Momentum 3-períodos"),
            
            # 8. No sobrecomprado
            (rsi < 60, 1, "No sobrecomprado")
        ]
        
        # SEÑAL SHORT - Condiciones muy estrictas
        short_conditions = [
            # 1. Tendencia bajista confirmada
            (current_price < ema_8 < ema_21 < ema_55 < ema_200, 3, "Alineación EMAs bajista"),
            
            # 2. RSI en zona óptima
            (55 < rsi < 75, 2, "RSI overbought controlado"),
            
            # 3. Divergencia bajista
            (has_divergence and div_direction < 0, 4, "Divergencia RSI bajista"),
            
            # 4. Cerca de BB superior
            (bb_upper * 0.98 < current_price < bb_upper, 2, "Cerca BB superior"),
            
            # 5. Volumen excepcional
            (volume_ratio > self.min_volume_ratio, 2, f"Volumen {volume_ratio:.1f}x"),
            
            # 6. Rechazo en resistencia fuerte
            (any(abs(current_price - zone['price'])/current_price < 0.01 
                 and zone['type'] == 'resistance' and zone['strength'] >= 3 
                 for zone in sr_zones), 3, "Rechazo en resistencia"),
            
            # 7. Momentum reciente negativo
            (df['Close'].iloc[-1] < df['Close'].iloc[-3], 1, "Momentum bajista"),
            
            # 8. No sobrevendido
            (rsi > 40, 1, "No sobrevendido")
        ]
        
        # Evaluar condiciones LONG
        for condition, points, reason in long_conditions:
            if condition:
                score += points
                reasons.append(reason)
        
        if score >= self.min_score:  # Score mínimo muy alto
            signal_type = 'LONG'
            
            # Stops muy precisos
            stop_loss = current_price - (atr * 1.0)  # Stop ajustado
            
            # Target conservador pero realista
            if sr_zones:
                resistance_levels = [z['price'] for z in sr_zones 
                                   if z['type'] == 'resistance' and z['price'] > current_price]
                if resistance_levels:
                    take_profit = min(resistance_levels) * 0.99  # Antes de resistencia
                else:
                    take_profit = current_price + (atr * 2.5)
            else:
                take_profit = current_price + (atr * 2.5)
            
        else:
            # Reset para evaluar SHORT
            score = 0
            reasons = []
            
            for condition, points, reason in short_conditions:
                if condition:
                    score += points
                    reasons.append(reason)
            
            if score >= self.min_score:
                signal_type = 'SHORT'
                
                stop_loss = current_price + (atr * 1.0)
                
                if sr_zones:
                    support_levels = [z['price'] for z in sr_zones 
                                    if z['type'] == 'support' and z['price'] < current_price]
                    if support_levels:
                        take_profit = max(support_levels) * 1.01
                    else:
                        take_profit = current_price - (atr * 2.5)
                else:
                    take_profit = current_price - (atr * 2.5)
        
        # Generar señal solo si pasa todos los filtros
        if signal_type and score >= self.min_score:
            # Verificar risk/reward
            risk = abs(current_price - stop_loss)
            reward = abs(take_profit - current_price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            # Verificar riesgo máximo
            risk_pct = (risk / current_price) * 100
            
            if rr_ratio >= 1.5 and risk_pct <= self.max_risk * 100:
                signal = {
                    'ticker': ticker,
                    'type': signal_type,
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'score': score,
                    'risk_reward': rr_ratio,
                    'risk_pct': risk_pct,
                    'reasons': reasons,
                    'rsi': rsi,
                    'volume_ratio': volume_ratio,
                    'trend_strength': trend_strength,
                    'has_divergence': has_divergence
                }
                
                signals.append(signal)
        
        return signals
    
    def run_period_backtest(self, start_date, end_date, period_name):
        """Ejecuta backtesting para un período específico"""
        
        print(f"\n{'='*60}")
        print(f"📊 BACKTESTING PERÍODO: {period_name}")
        print(f"📅 {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")
        print(f"{'='*60}")
        
        # Tickers principales
        tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD']
        
        all_signals = []
        all_trades = []
        
        for ticker in tickers:
            try:
                print(f"\n📈 Analizando {ticker}...")
                
                # Descargar datos con margen adicional para indicadores
                extended_start = start_date - timedelta(days=60)
                data = yf.Ticker(ticker)
                df = data.history(start=extended_start, end=end_date + timedelta(days=1), interval='1h')
                
                if len(df) < 200:
                    print(f"   ⚠️ Datos insuficientes")
                    continue
                
                # Filtrar por período de análisis
                period_df = df[df.index.date >= start_date.date()]
                period_df = period_df[period_df.index.date <= end_date.date()]
                
                signals_count = 0
                
                # Simular día por día
                for i in range(200, len(df)):  # Empezar después de 200 períodos para indicadores
                    current_date = df.index[i].date()
                    
                    # Solo analizar en el período objetivo
                    if current_date < start_date.date() or current_date > end_date.date():
                        continue
                    
                    # Datos hasta el punto actual
                    historical_df = df.iloc[:i+1]
                    
                    # Generar señal
                    signals = self.generate_high_precision_signals(historical_df, ticker)
                    
                    for signal in signals:
                        signals_count += 1
                        signal['entry_date'] = df.index[i]
                        all_signals.append(signal)
                        
                        # Simular ejecución del trade
                        trade = self.simulate_trade(signal, df, i)
                        if trade:
                            all_trades.append(trade)
                        
                        # Solo una señal por día por ticker
                        break
                
                print(f"   ✅ {signals_count} señales generadas")
                
            except Exception as e:
                print(f"   ❌ Error con {ticker}: {e}")
        
        # Analizar resultados
        return self.analyze_period_results(all_trades, period_name, start_date, end_date)
    
    def simulate_trade(self, signal, df, entry_idx):
        """Simula la ejecución de un trade"""
        
        # Buscar salida en siguientes períodos
        for i in range(entry_idx + 1, min(entry_idx + 100, len(df))):
            current_bar = df.iloc[i]
            
            exit_price = None
            exit_reason = None
            
            if signal['type'] == 'LONG':
                if current_bar['High'] >= signal['take_profit']:
                    exit_price = signal['take_profit']
                    exit_reason = 'TP'
                elif current_bar['Low'] <= signal['stop_loss']:
                    exit_price = signal['stop_loss']
                    exit_reason = 'SL'
            else:  # SHORT
                if current_bar['Low'] <= signal['take_profit']:
                    exit_price = signal['take_profit']
                    exit_reason = 'TP'
                elif current_bar['High'] >= signal['stop_loss']:
                    exit_price = signal['stop_loss']
                    exit_reason = 'SL'
            
            # Salida por tiempo (72 horas máximo)
            if not exit_price and i >= entry_idx + 72:
                exit_price = current_bar['Close']
                exit_reason = 'TIME'
            
            if exit_price:
                # Calcular resultado
                if signal['type'] == 'LONG':
                    profit_pct = ((exit_price - signal['entry_price']) / signal['entry_price']) * 100
                else:
                    profit_pct = ((signal['entry_price'] - exit_price) / signal['entry_price']) * 100
                
                trade = {
                    'ticker': signal['ticker'],
                    'type': signal['type'],
                    'entry_date': signal['entry_date'],
                    'exit_date': df.index[i],
                    'entry_price': signal['entry_price'],
                    'exit_price': exit_price,
                    'profit_pct': profit_pct,
                    'exit_reason': exit_reason,
                    'score': signal['score'],
                    'risk_reward': signal['risk_reward'],
                    'duration_hours': i - entry_idx
                }
                
                return trade
        
        return None
    
    def analyze_period_results(self, trades, period_name, start_date, end_date):
        """Analiza resultados del período"""
        
        if not trades:
            print(f"\n❌ No se ejecutaron trades en {period_name}")
            return {'period': period_name, 'trades': 0, 'win_rate': 0}
        
        # Métricas básicas
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['profit_pct'] > 0]
        losing_trades = [t for t in trades if t['profit_pct'] <= 0]
        
        win_rate = (len(winning_trades) / total_trades) * 100
        
        avg_win = np.mean([t['profit_pct'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['profit_pct'] for t in losing_trades]) if losing_trades else 0
        
        # Profit Factor
        gross_profit = sum(t['profit_pct'] for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t['profit_pct'] for t in losing_trades)) if losing_trades else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Best/Worst
        best_trade = max(trades, key=lambda t: t['profit_pct']) if trades else None
        worst_trade = min(trades, key=lambda t: t['profit_pct']) if trades else None
        
        # Duración promedio
        avg_duration = np.mean([t['duration_hours'] for t in trades])
        
        print(f"\n📊 RESULTADOS {period_name}:")
        print(f"├─ Total Trades: {total_trades}")
        print(f"├─ Win Rate: {win_rate:.1f}%")
        print(f"├─ Profit Factor: {profit_factor:.2f}")
        print(f"├─ Avg Win: {avg_win:+.2f}%")
        print(f"├─ Avg Loss: {avg_loss:+.2f}%")
        print(f"├─ Best: {best_trade['profit_pct']:+.2f}%" if best_trade else "├─ Best: N/A")
        print(f"├─ Worst: {worst_trade['profit_pct']:+.2f}%" if worst_trade else "├─ Worst: N/A")
        print(f"└─ Avg Duration: {avg_duration:.1f}h")
        
        # Análisis por salida
        exit_analysis = {}
        for trade in trades:
            reason = trade['exit_reason']
            if reason not in exit_analysis:
                exit_analysis[reason] = []
            exit_analysis[reason].append(trade['profit_pct'])
        
        print(f"\n🎯 ANÁLISIS POR SALIDA:")
        for reason, profits in exit_analysis.items():
            win_rate_reason = (len([p for p in profits if p > 0]) / len(profits)) * 100
            avg_profit = np.mean(profits)
            print(f"├─ {reason}: {len(profits)} trades, WR: {win_rate_reason:.0f}%, Avg: {avg_profit:+.2f}%")
        
        # Calificación del período
        if win_rate >= 80:
            grade = "🌟 EXCELENTE"
        elif win_rate >= 70:
            grade = "✅ BUENO"
        elif win_rate >= 60:
            grade = "⚠️ ACEPTABLE"
        else:
            grade = "❌ MALO"
        
        print(f"\n🏆 CALIFICACIÓN: {grade}")
        
        return {
            'period': period_name,
            'start_date': start_date,
            'end_date': end_date,
            'trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'best_trade': best_trade['profit_pct'] if best_trade else 0,
            'worst_trade': worst_trade['profit_pct'] if worst_trade else 0,
            'avg_duration': avg_duration,
            'grade': grade
        }

def main():
    """Función principal de backtesting por períodos"""
    
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║                BACKTESTING EXHAUSTIVO POR PERÍODOS                      ║
║                  Objetivo: 80%+ Win Rate System                         ║
╚════════════════════════════════════════════════════════════════════════╝
    """)
    
    system = HighWinRateSystem()
    
    # Definir períodos de análisis
    periods = [
        {
            'name': 'Últimos 60 días',
            'start': datetime.now() - timedelta(days=60),
            'end': datetime.now()
        },
        {
            'name': 'Enero-Marzo 2024',
            'start': datetime(2024, 1, 1),
            'end': datetime(2024, 3, 31)
        },
        {
            'name': 'Marzo-Junio 2024',
            'start': datetime(2024, 3, 1),
            'end': datetime(2024, 6, 30)
        },
        {
            'name': 'Julio-Septiembre 2024',
            'start': datetime(2024, 7, 1),
            'end': datetime(2024, 9, 30)
        },
        {
            'name': 'Octubre-Diciembre 2024',
            'start': datetime(2024, 10, 1),
            'end': datetime(2024, 12, 31)
        }
    ]
    
    results = []
    
    # Ejecutar backtesting para cada período
    for period in periods:
        try:
            result = system.run_period_backtest(
                period['start'], 
                period['end'], 
                period['name']
            )
            results.append(result)
        except Exception as e:
            print(f"❌ Error en período {period['name']}: {e}")
    
    # Resumen consolidado
    print(f"\n{'='*80}")
    print("📊 RESUMEN CONSOLIDADO DE TODOS LOS PERÍODOS")
    print(f"{'='*80}")
    
    if results:
        # Crear tabla resumen
        print(f"\n{'Período':<20} {'Trades':<8} {'Win Rate':<10} {'PF':<6} {'Calificación'}")
        print("-" * 65)
        
        total_trades = 0
        total_wins = 0
        
        for result in results:
            total_trades += result['trades']
            total_wins += (result['trades'] * result['win_rate'] / 100)
            
            print(f"{result['period']:<20} {result['trades']:<8} {result['win_rate']:<9.1f}% "
                  f"{result['profit_factor']:<5.2f} {result['grade']}")
        
        # Promedio general
        overall_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        
        print("-" * 65)
        print(f"{'PROMEDIO GENERAL':<20} {total_trades:<8} {overall_win_rate:<9.1f}%")
        
        # Análisis temporal
        print(f"\n🔍 ANÁLISIS TEMPORAL:")
        
        best_period = max(results, key=lambda x: x['win_rate'])
        worst_period = min(results, key=lambda x: x['win_rate'])
        
        print(f"• Mejor período: {best_period['period']} ({best_period['win_rate']:.1f}% WR)")
        print(f"• Peor período: {worst_period['period']} ({worst_period['win_rate']:.1f}% WR)")
        
        # Estabilidad
        win_rates = [r['win_rate'] for r in results]
        win_rate_std = np.std(win_rates)
        
        if win_rate_std < 10:
            stability = "🟢 ALTA"
        elif win_rate_std < 20:
            stability = "🟡 MEDIA"
        else:
            stability = "🔴 BAJA"
        
        print(f"• Estabilidad: {stability} (σ = {win_rate_std:.1f}%)")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        
        if overall_win_rate >= 80:
            print("🌟 SISTEMA ÓPTIMO - Listo para producción")
        elif overall_win_rate >= 70:
            print("✅ SISTEMA BUENO - Ajustes menores requeridos")
        elif overall_win_rate >= 60:
            print("⚠️ SISTEMA ACEPTABLE - Optimización necesaria")
        else:
            print("❌ SISTEMA DEFICIENTE - Revisión completa requerida")
        
        if win_rate_std > 15:
            print("• Alta variabilidad - Ajustar filtros por condiciones de mercado")
        
        if any(r['trades'] < 10 for r in results):
            print("• Pocos trades en algunos períodos - Considerar relajar filtros")
        
        # Guardar resultados
        df_results = pd.DataFrame(results)
        df_results.to_csv('backtest_periods_analysis.csv', index=False)
        print(f"\n💾 Resultados guardados en backtest_periods_analysis.csv")
        
    else:
        print("❌ No se obtuvieron resultados válidos")

if __name__ == "__main__":
    main()