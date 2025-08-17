#!/usr/bin/env python3
"""
Sistema de Trading Optimizado para Máximos Profits
Versión 4.0 - Ultra Performance
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import joblib
import os
warnings.filterwarnings('ignore')

class TradingSystemPro:
    """Sistema optimizado con estrategias mejoradas para mayor rentabilidad"""
    
    def __init__(self, capital=10000):
        self.capital = capital
        self.initial_capital = capital
        
        # OPTIMIZACIÓN 1: Position sizing dinámico basado en confianza
        self.min_position_size = 0.03  # 3% mínimo
        self.max_position_size = 0.15  # 15% máximo
        
        # OPTIMIZACIÓN 2: Risk/Reward dinámico
        self.min_risk_reward = 1.5  # Mínimo 1:1.5
        self.target_risk_reward = 3.0  # Objetivo 1:3
        
        # OPTIMIZACIÓN 3: Filtros de calidad mejorados
        self.min_volume_ratio = 1.3  # Mayor volumen requerido
        self.min_ml_confidence = 0.60  # Mayor confianza ML
        self.max_correlation = 0.70  # Evitar alta correlación
        
        # OPTIMIZACIÓN 4: Trailing stops agresivos
        self.trailing_activation = 0.015  # Activar trailing a +1.5%
        self.trailing_distance = 0.005  # 0.5% de distancia
        
        self.signals = []
        self.trades_history = []
        
    def calculate_dynamic_position_size(self, score, volatility, account_risk=0.02):
        """
        Calcula el tamaño de posición dinámico basado en:
        - Score de la señal (confianza)
        - Volatilidad del activo
        - Riesgo de la cuenta
        """
        # Base position size según score
        if score >= 8:
            base_size = 0.12  # 12% para señales muy fuertes
        elif score >= 6:
            base_size = 0.08  # 8% para señales fuertes
        elif score >= 4:
            base_size = 0.05  # 5% para señales normales
        else:
            base_size = 0.03  # 3% para señales débiles
        
        # Ajustar por volatilidad (menos tamaño si más volátil)
        volatility_adjustment = max(0.5, min(1.5, 1 / (volatility * 10)))
        
        # Ajustar por drawdown actual
        current_drawdown = ((self.capital / self.initial_capital) - 1) * 100
        if current_drawdown < -10:  # Si estamos en drawdown
            drawdown_adjustment = 0.5  # Reducir tamaño a la mitad
        elif current_drawdown < -5:
            drawdown_adjustment = 0.75
        else:
            drawdown_adjustment = 1.0
        
        # Calcular tamaño final
        final_size = base_size * volatility_adjustment * drawdown_adjustment
        
        # Limitar entre min y max
        return max(self.min_position_size, min(self.max_position_size, final_size))
    
    def calculate_smart_stops(self, price, atr, trend_strength, support_resistance):
        """
        Calcula stops inteligentes basados en:
        - ATR (volatilidad)
        - Fuerza de tendencia
        - Niveles de soporte/resistencia
        """
        # Stop loss base
        if trend_strength > 0.7:  # Tendencia fuerte
            sl_multiplier = 1.0  # Stop más ajustado
        elif trend_strength > 0.3:  # Tendencia moderada
            sl_multiplier = 1.5
        else:  # Tendencia débil
            sl_multiplier = 2.0
        
        stop_loss_distance = atr * sl_multiplier
        
        # Take profit dinámico
        if trend_strength > 0.7:
            tp_multiplier = 4.0  # Target más ambicioso en tendencia fuerte
        elif trend_strength > 0.3:
            tp_multiplier = 3.0
        else:
            tp_multiplier = 2.0
        
        take_profit_distance = atr * tp_multiplier
        
        # Ajustar por soporte/resistencia si existen
        if support_resistance:
            if support_resistance['type'] == 'support':
                # Poner stop justo debajo del soporte
                stop_loss_distance = min(stop_loss_distance, 
                                        abs(price - support_resistance['level']) * 1.1)
            elif support_resistance['type'] == 'resistance':
                # Target en la resistencia
                take_profit_distance = min(take_profit_distance,
                                         abs(support_resistance['level'] - price) * 0.95)
        
        return stop_loss_distance, take_profit_distance
    
    def multi_timeframe_confirmation(self, ticker_symbol):
        """
        Confirma señales en múltiples timeframes
        Returns: score de confirmación (0-10)
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            
            # Timeframes: 15min, 1h, 4h, 1d
            timeframes = [
                ('15m', '2d', 3),   # 15 minutos, peso 3
                ('1h', '5d', 5),    # 1 hora, peso 5
                ('1d', '1mo', 2),   # 1 día, peso 2
            ]
            
            total_score = 0
            total_weight = 0
            
            for interval, period, weight in timeframes:
                df = ticker.history(period=period, interval=interval)
                
                if len(df) < 20:
                    continue
                
                # Calcular tendencia en cada timeframe
                sma_20 = df['Close'].rolling(20).mean().iloc[-1]
                current_price = df['Close'].iloc[-1]
                
                # RSI
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs)).iloc[-1]
                
                # Score para este timeframe
                tf_score = 0
                
                # Tendencia
                if current_price > sma_20:
                    tf_score += 3
                else:
                    tf_score -= 3
                
                # RSI
                if 40 < rsi < 60:
                    tf_score += 2  # Zona neutral buena
                elif rsi < 30 or rsi > 70:
                    tf_score += 1  # Extremos (reversión)
                
                # Momentum
                returns = (current_price / df['Close'].iloc[-5] - 1) * 100
                if abs(returns) > 2:
                    tf_score += 2 if returns > 0 else -2
                
                total_score += tf_score * weight
                total_weight += weight
            
            if total_weight > 0:
                return (total_score / total_weight) + 5  # Normalizar a 0-10
            
            return 5  # Neutral si no hay datos
            
        except:
            return 5
    
    def detect_market_regime(self, df):
        """
        Detecta el régimen del mercado:
        - Trending (alcista/bajista)
        - Ranging (lateral)
        - Volatile
        """
        if len(df) < 50:
            return 'unknown', 0
        
        # Calcular ADX para fuerza de tendencia
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(14).mean()
        
        # Detectar tendencia
        sma_20 = df['Close'].rolling(20).mean()
        sma_50 = df['Close'].rolling(50).mean()
        
        price = df['Close'].iloc[-1]
        
        # Calcular pendiente de regresión lineal
        prices = df['Close'].tail(20).values
        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0]
        normalized_slope = (slope / prices[-1]) * 100
        
        # Volatilidad
        volatility = df['Close'].pct_change().std() * np.sqrt(252)
        
        # Determinar régimen (umbrales más sensibles)
        if abs(normalized_slope) > 0.3:  # Tendencia (reducido de 1 a 0.3)
            if normalized_slope > 0:
                regime = 'trending_up'
                strength = min(1.0, abs(normalized_slope) / 2)
            else:
                regime = 'trending_down'
                strength = min(1.0, abs(normalized_slope) / 2)
        elif volatility > 0.3:  # Volatilidad moderada (reducido de 0.5)
            regime = 'volatile'
            strength = min(1.0, volatility * 1.5)
        else:  # Lateral
            regime = 'ranging'
            strength = 0.5  # Aumentado para dar más peso
        
        return regime, strength
    
    def find_support_resistance(self, df, current_price, lookback=100):
        """
        Encuentra niveles clave de soporte y resistencia
        """
        if len(df) < lookback:
            return None
        
        # Buscar pivots
        highs = []
        lows = []
        
        for i in range(2, len(df)-2):
            # High pivot
            if (df['High'].iloc[i] > df['High'].iloc[i-1] and 
                df['High'].iloc[i] > df['High'].iloc[i-2] and
                df['High'].iloc[i] > df['High'].iloc[i+1] and
                df['High'].iloc[i] > df['High'].iloc[i+2]):
                highs.append(df['High'].iloc[i])
            
            # Low pivot
            if (df['Low'].iloc[i] < df['Low'].iloc[i-1] and 
                df['Low'].iloc[i] < df['Low'].iloc[i-2] and
                df['Low'].iloc[i] < df['Low'].iloc[i+1] and
                df['Low'].iloc[i] < df['Low'].iloc[i+2]):
                lows.append(df['Low'].iloc[i])
        
        # Encontrar nivel más cercano
        if current_price > df['Close'].mean():
            # Buscar resistencia arriba
            resistances = [h for h in highs if h > current_price]
            if resistances:
                nearest = min(resistances, key=lambda x: abs(x - current_price))
                return {'type': 'resistance', 'level': nearest}
        else:
            # Buscar soporte abajo
            supports = [l for l in lows if l < current_price]
            if supports:
                nearest = max(supports, key=lambda x: abs(x - current_price))
                return {'type': 'support', 'level': nearest}
        
        return None
    
    def generate_optimized_signals(self, market_data):
        """
        Genera señales optimizadas con todos los filtros mejorados
        """
        signals = []
        
        for ticker, df in market_data.items():
            if len(df) < 100:
                continue
            
            # Variables actuales
            current_price = df['Close'].iloc[-1]
            volume = df['Volume'].iloc[-1]
            volume_avg = df['Volume'].rolling(20).mean().iloc[-1]
            
            # ATR para volatilidad
            high_low = df['High'] - df['Low']
            atr = high_low.rolling(14).mean().iloc[-1]
            volatility = atr / current_price
            
            # Detectar régimen de mercado
            regime, trend_strength = self.detect_market_regime(df)
            
            # Multi-timeframe confirmation
            mtf_score = self.multi_timeframe_confirmation(ticker)
            
            # Debug info
            print(f"\n   {ticker}: regime={regime}, strength={trend_strength:.2f}, mtf={mtf_score:.1f}")
            
            # Soporte/Resistencia
            sr_levels = self.find_support_resistance(df, current_price)
            
            # === SCORING SYSTEM ===
            score = 0
            reasons = []
            
            # 1. Régimen de mercado (peso alto)
            if regime == 'trending_up':
                score += 3 * trend_strength
                reasons.append(f"Tendencia alcista ({trend_strength:.1f})")
                signal_type = 'LONG'
            elif regime == 'trending_down':
                score += 3 * trend_strength
                reasons.append(f"Tendencia bajista ({trend_strength:.1f})")
                signal_type = 'SHORT'
            elif regime == 'ranging':
                # En lateral, buscar reversiones
                if current_price < df['Close'].rolling(20).mean().iloc[-1] * 0.98:
                    signal_type = 'LONG'
                    score += 1
                    reasons.append("Oversold en rango")
                elif current_price > df['Close'].rolling(20).mean().iloc[-1] * 1.02:
                    signal_type = 'SHORT'
                    score += 1
                    reasons.append("Overbought en rango")
                else:
                    continue
            else:
                continue  # Skip si no hay señal clara
            
            # 2. Multi-timeframe (peso medio)
            if mtf_score > 7:
                score += 2
                reasons.append("MTF confirmación fuerte")
            elif mtf_score > 5:
                score += 1
                reasons.append("MTF confirmación moderada")
            elif mtf_score < 3:
                score -= 2
                reasons.append("MTF divergencia")
            
            # 3. Volumen (peso medio)
            vol_ratio = volume / volume_avg if volume_avg > 0 else 1
            if vol_ratio > self.min_volume_ratio:
                score += 2
                reasons.append(f"Volumen alto ({vol_ratio:.1f}x)")
            
            # 4. Soporte/Resistencia (peso alto)
            if sr_levels:
                if signal_type == 'LONG' and sr_levels['type'] == 'support':
                    distance_to_support = abs(current_price - sr_levels['level']) / current_price
                    if distance_to_support < 0.02:  # Cerca del soporte
                        score += 3
                        reasons.append("Rebote en soporte")
                elif signal_type == 'SHORT' and sr_levels['type'] == 'resistance':
                    distance_to_resistance = abs(sr_levels['level'] - current_price) / current_price
                    if distance_to_resistance < 0.02:  # Cerca de resistencia
                        score += 3
                        reasons.append("Rechazo en resistencia")
            
            # 5. RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            if signal_type == 'LONG' and 30 < rsi < 50:
                score += 1
                reasons.append(f"RSI favorable ({rsi:.0f})")
            elif signal_type == 'SHORT' and 50 < rsi < 70:
                score += 1
                reasons.append(f"RSI favorable ({rsi:.0f})")
            
            # 6. MACD
            ema_12 = df['Close'].ewm(span=12).mean().iloc[-1]
            ema_26 = df['Close'].ewm(span=26).mean().iloc[-1]
            macd = ema_12 - ema_26
            signal_line = df['Close'].ewm(span=9).mean().iloc[-1]
            
            if signal_type == 'LONG' and macd > signal_line:
                score += 1
                reasons.append("MACD bullish")
            elif signal_type == 'SHORT' and macd < signal_line:
                score += 1
                reasons.append("MACD bearish")
            
            # === GENERAR SEÑAL SI SCORE SUFICIENTE ===
            if score >= 3:  # Umbral ajustado para más señales
                # Calcular stops inteligentes
                sl_distance, tp_distance = self.calculate_smart_stops(
                    current_price, atr, trend_strength, sr_levels
                )
                
                # Position size dinámico
                position_size = self.calculate_dynamic_position_size(
                    score, volatility
                )
                
                if signal_type == 'LONG':
                    stop_loss = current_price - sl_distance
                    take_profit = current_price + tp_distance
                else:
                    stop_loss = current_price + sl_distance
                    take_profit = current_price - tp_distance
                
                # Risk/Reward check
                risk = abs(current_price - stop_loss)
                reward = abs(take_profit - current_price)
                risk_reward = reward / risk if risk > 0 else 0
                
                if risk_reward >= self.min_risk_reward:
                    signal = {
                        'ticker': ticker,
                        'type': signal_type,
                        'price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'position_size': position_size,
                        'score': score,
                        'risk_reward': risk_reward,
                        'volatility': volatility,
                        'regime': regime,
                        'trend_strength': trend_strength,
                        'reasons': ', '.join(reasons),
                        'timestamp': datetime.now()
                    }
                    
                    signals.append(signal)
        
        # Filtrar por correlación
        return self.filter_correlated_signals(signals, market_data)
    
    def filter_correlated_signals(self, signals, market_data):
        """
        Filtra señales correlacionadas, manteniendo las mejores
        """
        if len(signals) <= 1:
            return signals
        
        # Calcular correlaciones
        tickers = [s['ticker'] for s in signals]
        correlations = {}
        
        for i, t1 in enumerate(tickers):
            for j, t2 in enumerate(tickers):
                if i < j:
                    if t1 in market_data and t2 in market_data:
                        corr = market_data[t1]['Close'].corr(market_data[t2]['Close'])
                        correlations[(t1, t2)] = corr
        
        # Ordenar señales por score
        signals.sort(key=lambda x: x['score'], reverse=True)
        
        # Filtrar correlacionadas
        filtered = []
        added_tickers = set()
        
        for signal in signals:
            can_add = True
            
            for existing in added_tickers:
                pair = tuple(sorted([signal['ticker'], existing]))
                if pair in correlations:
                    if abs(correlations[pair]) > self.max_correlation:
                        can_add = False
                        break
            
            if can_add:
                filtered.append(signal)
                added_tickers.add(signal['ticker'])
                
                # Máximo 5 señales concurrentes
                if len(filtered) >= 5:
                    break
        
        return filtered
    
    def execute_system(self):
        """
        Ejecuta el sistema completo optimizado
        """
        print("""
╔════════════════════════════════════════════════════════════════════════╗
║             SISTEMA DE TRADING OPTIMIZADO v4.0                          ║
║                    Maximum Profit Edition                               ║
╚════════════════════════════════════════════════════════════════════════╝
        """)
        
        print(f"\n💰 Capital: ${self.capital:,.2f}")
        print(f"🎯 Objetivo: Maximizar profits con gestión de riesgo")
        print("="*60)
        
        # Lista de tickers optimizada (más líquidos)
        tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD',
                  'ADA-USD', 'AVAX-USD', 'LINK-USD', 'DOGE-USD', 'DOT-USD']
        
        # Descargar datos
        print("\n📥 Descargando datos de mercado...")
        market_data = {}
        
        for ticker in tickers:
            try:
                print(f"   {ticker}...", end="")
                data = yf.Ticker(ticker)
                df = data.history(period="1mo", interval="1h")
                
                if len(df) > 100:
                    market_data[ticker] = df
                    print(" ✅")
                else:
                    print(" ⚠️ Datos insuficientes")
            except:
                print(" ❌ Error")
        
        # Generar señales optimizadas
        print(f"\n🔍 Analizando {len(market_data)} activos...")
        signals = self.generate_optimized_signals(market_data)
        
        # Mostrar señales
        if signals:
            print(f"\n🚀 SEÑALES GENERADAS: {len(signals)}")
            print("="*60)
            
            for i, signal in enumerate(signals, 1):
                emoji = "🟢" if signal['type'] == 'LONG' else "🔴"
                
                print(f"\n{emoji} Señal #{i}: {signal['ticker']} - {signal['type']}")
                print(f"├─ Precio: ${signal['price']:.4f}")
                print(f"├─ Stop Loss: ${signal['stop_loss']:.4f}")
                print(f"├─ Take Profit: ${signal['take_profit']:.4f}")
                print(f"├─ Risk/Reward: 1:{signal['risk_reward']:.1f}")
                print(f"├─ Position Size: {signal['position_size']*100:.1f}%")
                print(f"├─ Score: {signal['score']:.1f}/10")
                print(f"├─ Régimen: {signal['regime']} ({signal['trend_strength']:.1f})")
                print(f"└─ Razones: {signal['reasons']}")
                
                # Calcular potencial profit
                risk_amount = self.capital * signal['position_size'] * \
                            abs(signal['price'] - signal['stop_loss']) / signal['price']
                reward_amount = risk_amount * signal['risk_reward']
                
                print(f"   💰 Potencial: -${risk_amount:.2f} / +${reward_amount:.2f}")
            
            # Resumen
            avg_rr = np.mean([s['risk_reward'] for s in signals])
            avg_size = np.mean([s['position_size'] for s in signals])
            total_exposure = sum([s['position_size'] for s in signals])
            
            print("\n" + "="*60)
            print("📊 RESUMEN DE SEÑALES")
            print("="*60)
            print(f"• Risk/Reward promedio: 1:{avg_rr:.1f}")
            print(f"• Tamaño promedio: {avg_size*100:.1f}%")
            print(f"• Exposición total: {total_exposure*100:.1f}%")
            
            # Proyección
            if len(signals) > 0:
                # Asumiendo 60% win rate con el R:R promedio
                win_rate = 0.60
                avg_win = avg_rr
                avg_loss = 1
                
                expected_value = (win_rate * avg_win) - ((1-win_rate) * avg_loss)
                monthly_trades = 20  # Estimado
                
                expected_monthly_return = expected_value * avg_size * monthly_trades * 100
                
                print(f"\n💡 PROYECCIÓN (60% WR):")
                print(f"• Valor esperado por trade: {expected_value:.2f}R")
                print(f"• Retorno mensual esperado: {expected_monthly_return:.1f}%")
                print(f"• Capital en 3 meses: ${self.capital * (1 + expected_monthly_return/100)**3:,.2f}")
                
        else:
            print("\n⚠️ No se generaron señales - Mercado sin oportunidades claras")
            print("   Recomendación: Esperar mejores setups")
        
        print("\n" + "="*60)
        print("✅ ANÁLISIS COMPLETADO")
        print("="*60)
        
        # Guardar señales
        if signals:
            df_signals = pd.DataFrame(signals)
            df_signals.to_csv('signals_optimized.csv', index=False)
            print("\n💾 Señales guardadas en signals_optimized.csv")
        
        return signals

if __name__ == "__main__":
    # Crear sistema optimizado
    system = TradingSystemPro(capital=10000)
    
    # Ejecutar
    signals = system.execute_system()
    
    # Recomendaciones finales
    print("\n🎯 RECOMENDACIONES PARA MÁXIMOS PROFITS:")
    print("1. Solo tomar señales con Score >= 7")
    print("2. Usar trailing stops agresivos después de +1.5%")
    print("3. Cerrar 50% en primer target, dejar correr el resto")
    print("4. No operar en horarios de baja liquidez")
    print("5. Reducir tamaño si en drawdown > 5%")
    print("6. Re-evaluar señales cada 4 horas")
    print("7. Salir si el régimen de mercado cambia")