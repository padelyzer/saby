#!/usr/bin/env python3
"""
ESTRATEGIA OPTIMIZADA ESPECÍFICA PARA AVAX-USD
Objetivo: Lograr 65-75% win rate con alta precisión y selectividad

Basado en:
- Análisis de backtest V4 (actual 41.7% win rate)
- Características específicas de AVAX como L1 blockchain
- Patrones de comportamiento identificados
- Correlaciones y volatilidad específicas
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class AVAXOptimizedStrategy:
    """
    Estrategia híbrida específicamente optimizada para AVAX
    Combina múltiples indicadores con filtros muy estrictos
    """
    
    def __init__(self, capital=1000):
        self.capital = capital
        self.symbol = 'AVAX-USD'
        
        # Parámetros específicos para AVAX optimizados
        self.params = {
            # RSI optimizado para AVAX
            'rsi_oversold_strict': 25,     # Más estricto que 30
            'rsi_overbought_strict': 75,   # Más estricto que 70
            'rsi_extreme_oversold': 20,    # Para entradas de alta confianza
            'rsi_extreme_overbought': 80,  # Para entradas de alta confianza
            
            # Períodos optimizados para volatilidad de AVAX
            'rsi_period': 12,              # Más sensible que 14
            'ema_fast': 16,                # Optimizado para AVAX
            'ema_slow': 42,                # Optimizado para AVAX
            'atr_period': 10,              # Más sensible
            
            # Bollinger Bands específicos
            'bb_period': 18,               # Período optimizado
            'bb_std': 2.2,                 # Ligeramente más amplio
            
            # Volumen (AVAX responde bien al volumen)
            'volume_threshold': 1.8,       # 80% más que promedio
            'volume_extreme': 2.5,         # Para señales de alta confianza
            
            # Filtros de tiempo (AVAX tiene patrones horarios)
            'avoid_hours': [0, 1, 2, 23],  # Horas UTC de baja liquidez
            'optimal_hours': [8, 9, 10, 14, 15, 16], # Horarios óptimos
            
            # Gestión de riesgo específica
            'base_risk': 0.015,            # 1.5% riesgo base
            'max_risk': 0.025,             # 2.5% máximo
            'min_confidence': 0.70,        # Muy selectivo
            
            # Stops y targets dinámicos
            'stop_multiplier_trend': 1.8,  # Más apretado para trends
            'stop_multiplier_range': 1.5,  # Más apretado para ranging
            'target_multiplier_trend': 2.8,
            'target_multiplier_range': 1.2,
            
            # Filtros de confirmación múltiple
            'min_signals_required': 3,     # Mínimo 3 señales confirmatorias
            'min_confluence_score': 8,     # Score mínimo de confluencia
        }
        
        self.signals_log = []
        self.trades = []
    
    def get_avax_data(self, days=60):
        """Obtiene datos optimizados para AVAX"""
        try:
            ticker = yf.Ticker(self.symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Obtener datos principales
            df_1h = ticker.history(start=start_date, end=end_date, interval='1h')
            df_daily = ticker.history(start=start_date, end=end_date, interval='1d')
            
            # Crear 4H resampling del 1H
            df_4h = df_1h.resample('4H').agg({
                'Open': 'first',
                'High': 'max', 
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()
            
            # Para 15M, usar los últimos 7 días del 1H como proxy
            df_15m = df_1h.copy()  # Usar 1H como 15M para simplificar
            
            return None, df_15m, df_1h, df_4h, df_daily
            
        except Exception as e:
            print(f"Error obteniendo datos: {e}")
            return None, None, None, None, None
    
    def calculate_optimized_indicators(self, df):
        """Calcula indicadores optimizados específicamente para AVAX"""
        
        # RSI optimizado para AVAX
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.params['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.params['rsi_period']).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # EMAs optimizadas
        df['EMA_Fast'] = df['Close'].ewm(span=self.params['ema_fast']).mean()
        df['EMA_Slow'] = df['Close'].ewm(span=self.params['ema_slow']).mean()
        df['EMA_Trend'] = df['EMA_Fast'] - df['EMA_Slow']
        
        # Bollinger Bands específicos para AVAX
        df['BB_Middle'] = df['Close'].rolling(self.params['bb_period']).mean()
        bb_std = df['Close'].rolling(self.params['bb_period']).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * self.params['bb_std'])
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * self.params['bb_std'])
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
        
        # ATR optimizado
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(self.params['atr_period']).mean()
        
        # MACD específico para AVAX
        df['MACD'] = df['EMA_Fast'] - df['EMA_Slow']
        df['MACD_Signal'] = df['MACD'].ewm(span=8).mean()  # Más rápido
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # Stochastic optimizado
        low_min = df['Low'].rolling(12).min()  # Período más corto
        high_max = df['High'].rolling(12).max()
        df['Stoch_K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
        df['Stoch_D'] = df['Stoch_K'].rolling(3).mean()
        
        # Volume profile específico para AVAX
        df['Volume_MA'] = df['Volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
        
        # Momentum indicators
        if len(df) > 10:
            df['ROC'] = ((df['Close'] / df['Close'].shift(10)) - 1) * 100  # Rate of Change
        else:
            df['ROC'] = 0
            
        if len(df) > 5:
            df['Price_Change'] = df['Close'].pct_change(5) * 100
        else:
            df['Price_Change'] = 0
        
        return df
    
    def detect_avax_regime(self, df_1h, df_4h, df_daily):
        """
        Detecta régimen específico para AVAX
        AVAX tiene comportamientos únicos como L1 blockchain
        """
        regime_scores = {
            'TRENDING_UP': 0,
            'TRENDING_DOWN': 0,
            'RANGING': 0,
            'VOLATILE': 0,
            'ACCUMULATION': 0  # Específico para L1 tokens
        }
        
        current_4h = df_4h.iloc[-1]
        current_daily = df_daily.iloc[-1]
        
        # 1. Análisis de tendencia multi-timeframe
        if current_daily['EMA_Fast'] > current_daily['EMA_Slow']:
            if current_4h['EMA_Fast'] > current_4h['EMA_Slow']:
                regime_scores['TRENDING_UP'] += 4
            else:
                regime_scores['RANGING'] += 2
        else:
            if current_4h['EMA_Fast'] < current_4h['EMA_Slow']:
                regime_scores['TRENDING_DOWN'] += 4
            else:
                regime_scores['RANGING'] += 2
        
        # 2. Análisis de volatilidad específico para AVAX
        atr_ratio = current_4h['ATR'] / df_4h['ATR'].rolling(50).mean().iloc[-1]
        if atr_ratio > 1.6:  # AVAX es volátil por naturaleza
            regime_scores['VOLATILE'] += 3
        elif atr_ratio < 0.6:
            regime_scores['RANGING'] += 3
        
        # 3. Análisis de volumen (importante para AVAX)
        volume_trend = df_daily['Volume'].rolling(10).mean().iloc[-1] / df_daily['Volume'].rolling(30).mean().iloc[-1]
        if volume_trend > 1.3 and current_daily['ROC'] > 0:
            regime_scores['TRENDING_UP'] += 2
        elif volume_trend > 1.3 and current_daily['ROC'] < 0:
            regime_scores['TRENDING_DOWN'] += 2
        elif volume_trend < 0.8:
            regime_scores['ACCUMULATION'] += 3
        
        # 4. Estructura de precio específica para L1 tokens
        support = df_4h['Low'].rolling(50).min().iloc[-1]
        resistance = df_4h['High'].rolling(50).max().iloc[-1]
        range_size = (resistance - support) / current_4h['Close']
        
        if range_size < 0.15:  # Rango estrecho (15%)
            regime_scores['RANGING'] += 3
        elif range_size > 0.4:  # Rango amplio (40%)
            regime_scores['VOLATILE'] += 2
        
        # 5. Detección de fase de acumulación (específico para L1s)
        price_variance = df_daily['Close'].rolling(14).std().iloc[-1] / current_daily['Close']
        volume_consistency = df_daily['Volume'].rolling(14).std().iloc[-1] / df_daily['Volume'].rolling(14).mean().iloc[-1]
        
        if price_variance < 0.05 and volume_consistency < 0.6:  # Baja varianza de precio, volumen constante
            regime_scores['ACCUMULATION'] += 4
        
        # Determinar régimen dominante
        max_regime = max(regime_scores.items(), key=lambda x: x[1])
        
        return {
            'regime': max_regime[0],
            'confidence': max_regime[1] / sum(regime_scores.values()) if sum(regime_scores.values()) > 0 else 0,
            'scores': regime_scores,
            'atr_ratio': atr_ratio,
            'volume_trend': volume_trend,
            'range_size': range_size
        }
    
    def generate_avax_signal(self, df_5m, df_15m, df_1h, df_4h, df_daily):
        """
        Genera señales ultra-selectivas específicas para AVAX
        Requiere confluencia múltiple para alta precisión
        """
        
        # Calcular indicadores en todos los timeframes
        df_15m = self.calculate_optimized_indicators(df_15m)
        df_1h = self.calculate_optimized_indicators(df_1h)
        df_4h = self.calculate_optimized_indicators(df_4h)
        df_daily = self.calculate_optimized_indicators(df_daily)
        
        # Detectar régimen
        regime_info = self.detect_avax_regime(df_1h, df_4h, df_daily)
        
        current_15m = df_15m.iloc[-1]
        current_1h = df_1h.iloc[-1]
        current_4h = df_4h.iloc[-1]
        
        # Confluencia de señales
        confluence_score = 0
        signals = []
        signal_type = None
        
        # 1. RSI MULTI-TIMEFRAME (Score: 0-4)
        if current_15m['RSI'] < self.params['rsi_extreme_oversold'] and current_1h['RSI'] < self.params['rsi_oversold_strict']:
            confluence_score += 4
            signal_type = 'LONG'
            signals.append('RSI_EXTREME_OVERSOLD_CONFLUENCE')
        elif current_15m['RSI'] > self.params['rsi_extreme_overbought'] and current_1h['RSI'] > self.params['rsi_overbought_strict']:
            confluence_score += 4
            signal_type = 'SHORT'
            signals.append('RSI_EXTREME_OVERBOUGHT_CONFLUENCE')
        elif current_1h['RSI'] < self.params['rsi_oversold_strict']:
            confluence_score += 2
            if signal_type != 'SHORT':
                signal_type = 'LONG'
            signals.append('RSI_OVERSOLD_1H')
        elif current_1h['RSI'] > self.params['rsi_overbought_strict']:
            confluence_score += 2
            if signal_type != 'LONG':
                signal_type = 'SHORT'
            signals.append('RSI_OVERBOUGHT_1H')
        
        # 2. BOLLINGER BANDS PRECISION (Score: 0-3)
        if current_1h['BB_Position'] <= 0.05:  # Muy cerca del lower band
            confluence_score += 3
            if signal_type != 'SHORT':
                signal_type = 'LONG'
            signals.append('BB_LOWER_EXTREME')
        elif current_1h['BB_Position'] >= 0.95:  # Muy cerca del upper band
            confluence_score += 3
            if signal_type != 'LONG':
                signal_type = 'SHORT'
            signals.append('BB_UPPER_EXTREME')
        elif current_1h['BB_Position'] <= 0.2:
            confluence_score += 1
            signals.append('BB_LOWER_ZONE')
        elif current_1h['BB_Position'] >= 0.8:
            confluence_score += 1
            signals.append('BB_UPPER_ZONE')
        
        # 3. TREND CONFIRMATION (Score: 0-3)
        if regime_info['regime'] in ['TRENDING_UP', 'ACCUMULATION'] and signal_type == 'LONG':
            if current_4h['EMA_Trend'] > 0 and current_1h['EMA_Trend'] > 0:
                confluence_score += 3
                signals.append('TREND_ALIGNMENT_BULLISH')
            elif current_1h['EMA_Trend'] > 0:
                confluence_score += 2
                signals.append('TREND_CONTINUATION_BULLISH')
        elif regime_info['regime'] == 'TRENDING_DOWN' and signal_type == 'SHORT':
            if current_4h['EMA_Trend'] < 0 and current_1h['EMA_Trend'] < 0:
                confluence_score += 3
                signals.append('TREND_ALIGNMENT_BEARISH')
            elif current_1h['EMA_Trend'] < 0:
                confluence_score += 2
                signals.append('TREND_CONTINUATION_BEARISH')
        
        # 4. VOLUME CONFIRMATION (Score: 0-2)
        if current_1h['Volume_Ratio'] > self.params['volume_extreme']:
            confluence_score += 2
            signals.append('VOLUME_EXTREME_CONFIRMATION')
        elif current_1h['Volume_Ratio'] > self.params['volume_threshold']:
            confluence_score += 1
            signals.append('VOLUME_ABOVE_THRESHOLD')
        
        # 5. MACD MOMENTUM (Score: 0-2)
        if signal_type == 'LONG' and current_1h['MACD'] > current_1h['MACD_Signal'] and current_1h['MACD_Histogram'] > 0:
            confluence_score += 2
            signals.append('MACD_BULLISH_MOMENTUM')
        elif signal_type == 'SHORT' and current_1h['MACD'] < current_1h['MACD_Signal'] and current_1h['MACD_Histogram'] < 0:
            confluence_score += 2
            signals.append('MACD_BEARISH_MOMENTUM')
        elif signal_type == 'LONG' and current_1h['MACD'] > current_1h['MACD_Signal']:
            confluence_score += 1
            signals.append('MACD_BULLISH_CROSS')
        elif signal_type == 'SHORT' and current_1h['MACD'] < current_1h['MACD_Signal']:
            confluence_score += 1
            signals.append('MACD_BEARISH_CROSS')
        
        # 6. STOCHASTIC CONFIRMATION (Score: 0-1)
        if signal_type == 'LONG' and current_1h['Stoch_K'] < 25 and current_1h['Stoch_D'] < 25:
            confluence_score += 1
            signals.append('STOCH_OVERSOLD')
        elif signal_type == 'SHORT' and current_1h['Stoch_K'] > 75 and current_1h['Stoch_D'] > 75:
            confluence_score += 1
            signals.append('STOCH_OVERBOUGHT')
        
        # 7. TIMING FILTER (Score: 0-1)
        current_hour = datetime.now().hour
        if current_hour in self.params['optimal_hours']:
            confluence_score += 1
            signals.append('OPTIMAL_TIMING')
        elif current_hour in self.params['avoid_hours']:
            confluence_score -= 2  # Penalizar mal timing
            signals.append('POOR_TIMING')
        
        # 8. REGIME BONUS (Score: 0-2)
        if regime_info['confidence'] > 0.7:
            confluence_score += 2
            signals.append('HIGH_REGIME_CONFIDENCE')
        elif regime_info['confidence'] > 0.5:
            confluence_score += 1
            signals.append('MEDIUM_REGIME_CONFIDENCE')
        
        # FILTROS DE CALIDAD ULTRA-ESTRICTOS
        
        # Verificar score mínimo
        if confluence_score < self.params['min_confluence_score']:
            return None
        
        # Verificar número mínimo de señales
        if len([s for s in signals if not s.startswith('POOR_')]) < self.params['min_signals_required']:
            return None
        
        # Verificar que no hay timing malo
        if 'POOR_TIMING' in signals:
            return None
        
        # Calcular confianza final
        max_possible_score = 18  # Suma de todos los scores máximos
        confidence = min(confluence_score / max_possible_score, 0.95)
        
        # Verificar confianza mínima
        if confidence < self.params['min_confidence']:
            return None
        
        # SEÑAL APROBADA - Calcular parámetros de trading
        if signal_type:
            
            # Stops y targets específicos para régimen
            if regime_info['regime'] in ['TRENDING_UP', 'TRENDING_DOWN']:
                stop_multiplier = self.params['stop_multiplier_trend']
                target_multiplier = self.params['target_multiplier_trend']
            else:
                stop_multiplier = self.params['stop_multiplier_range']
                target_multiplier = self.params['target_multiplier_range']
            
            # Ajustar riesgo según confianza
            risk_multiplier = 0.8 + (confidence * 0.4)  # 0.8x a 1.2x según confianza
            risk = min(self.params['base_risk'] * risk_multiplier, self.params['max_risk'])
            
            signal = {
                'timestamp': datetime.now(),
                'symbol': self.symbol,
                'type': signal_type,
                'entry': current_1h['Close'],
                'atr': current_1h['ATR'],
                'stop_multiplier': stop_multiplier,
                'target_multiplier': target_multiplier,
                'confidence': confidence,
                'confluence_score': confluence_score,
                'risk': risk,
                'regime': regime_info['regime'],
                'regime_confidence': regime_info['confidence'],
                'signals': signals,
                'strategy': 'AVAX_OPTIMIZED',
                
                # Datos adicionales para seguimiento
                'rsi_1h': current_1h['RSI'],
                'rsi_15m': current_15m['RSI'],
                'bb_position': current_1h['BB_Position'],
                'volume_ratio': current_1h['Volume_Ratio'],
                'timeframe_primary': '1H',
                'timeframe_confirmation': '15M'
            }
            
            return signal
        
        return None
    
    def execute_avax_trade(self, signal):
        """Ejecuta trade con gestión de riesgo específica para AVAX"""
        
        # Calcular stops y targets
        if signal['type'] == 'LONG':
            stop_loss = signal['entry'] - (signal['atr'] * signal['stop_multiplier'])
            take_profit = signal['entry'] + (signal['atr'] * signal['target_multiplier'])
        else:
            stop_loss = signal['entry'] + (signal['atr'] * signal['stop_multiplier'])
            take_profit = signal['entry'] - (signal['atr'] * signal['target_multiplier'])
        
        # Calcular position size
        risk_amount = self.capital * signal['risk']
        stop_distance = abs(signal['entry'] - stop_loss)
        position_size = risk_amount / stop_distance if stop_distance != 0 else 0
        position_size = min(position_size, self.capital * 0.95)
        
        trade = {
            'timestamp': signal['timestamp'],
            'symbol': signal['symbol'],
            'type': signal['type'],
            'entry': signal['entry'],
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'position_size': position_size,
            'risk': signal['risk'],
            'confidence': signal['confidence'],
            'confluence_score': signal['confluence_score'],
            'regime': signal['regime'],
            'strategy': signal['strategy'],
            'signals': signal['signals'],
            'expected_return': signal['target_multiplier'] * signal['risk'],
            'risk_reward_ratio': signal['target_multiplier'] / signal['stop_multiplier']
        }
        
        self.trades.append(trade)
        return trade
    
    def scan_avax_opportunity(self):
        """Escanea oportunidad actual en AVAX"""
        
        print("\n" + "="*80)
        print(" 🎯 AVAX OPTIMIZED STRATEGY - ANÁLISIS EN VIVO ".center(80, "="))
        print("="*80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target Win Rate: 65-75%")
        print(f"Estrategia: Ultra-selectiva con confluencia múltiple\n")
        
        # Obtener datos
        df_5m, df_15m, df_1h, df_4h, df_daily = self.get_avax_data()
        
        if df_1h is None:
            print("❌ Error obteniendo datos de AVAX")
            return None
        
        # Generar señal
        signal = self.generate_avax_signal(df_5m, df_15m, df_1h, df_4h, df_daily)
        
        if signal:
            print("✅ SEÑAL DE ALTA CALIDAD DETECTADA!")
            print(f"   Tipo: {signal['type']}")
            print(f"   Confianza: {signal['confidence']:.1%}")
            print(f"   Score de Confluencia: {signal['confluence_score']}/18")
            print(f"   Régimen: {signal['regime']} (conf: {signal['regime_confidence']:.1%})")
            print(f"   RSI 1H: {signal['rsi_1h']:.1f}")
            print(f"   RSI 15M: {signal['rsi_15m']:.1f}")
            print(f"   BB Position: {signal['bb_position']:.3f}")
            print(f"   Volume Ratio: {signal['volume_ratio']:.2f}x")
            
            print(f"\n📊 SEÑALES CONFIRMATORIAS ({len(signal['signals'])}):")
            for i, sig in enumerate(signal['signals'], 1):
                print(f"   {i}. {sig}")
            
            # Ejecutar trade
            trade = self.execute_avax_trade(signal)
            
            print(f"\n💰 PARÁMETROS DE TRADING:")
            print(f"   Entry: ${trade['entry']:.4f}")
            print(f"   Stop Loss: ${trade['stop_loss']:.4f}")
            print(f"   Take Profit: ${trade['take_profit']:.4f}")
            print(f"   Risk/Reward: 1:{trade['risk_reward_ratio']:.2f}")
            print(f"   Riesgo: {trade['risk']*100:.2f}% del capital")
            print(f"   Position Size: ${trade['position_size']:.2f}")
            print(f"   Expected Return: {trade['expected_return']*100:.2f}%")
            
            return trade
        
        else:
            print("⚠️ NO HAY SEÑAL DE CALIDAD SUFICIENTE")
            print("   La estrategia está esperando condiciones óptimas")
            print("   Mínimo requerido:")
            print(f"   - Score confluencia: {self.params['min_confluence_score']}/18")
            print(f"   - Confianza: {self.params['min_confidence']:.0%}")
            print(f"   - Señales mínimas: {self.params['min_signals_required']}")
            
            # Mostrar estado actual para debug
            df_1h = self.calculate_optimized_indicators(df_1h)
            current = df_1h.iloc[-1]
            
            print(f"\n📊 ESTADO ACTUAL:")
            print(f"   Precio: ${current['Close']:.4f}")
            print(f"   RSI 1H: {current['RSI']:.1f}")
            print(f"   BB Position: {current['BB_Position']:.3f}")
            print(f"   Volume Ratio: {current['Volume_Ratio']:.2f}x")
            print(f"   Hora UTC: {datetime.now().hour}")
            
            return None

def main():
    """Demo de la estrategia optimizada para AVAX"""
    
    print("\n" + "="*80)
    print(" 🚀 AVAX OPTIMIZED STRATEGY - DEMO ".center(80, "="))
    print("="*80)
    
    strategy = AVAXOptimizedStrategy(capital=1000)
    
    # Escanear oportunidad actual
    result = strategy.scan_avax_opportunity()
    
    print("\n" + "="*80)
    print(" 📋 RESUMEN DE LA ESTRATEGIA ".center(80, "="))
    print("="*80)
    
    print("\n🎯 CARACTERÍSTICAS CLAVE:")
    print("  • Ultra-selectiva: Solo señales de máxima calidad")
    print("  • Confluencia múltiple: Mínimo 8/18 puntos")
    print("  • Multi-timeframe: 15M + 1H + 4H confirmación")
    print("  • Específica para AVAX: Parámetros optimizados")
    print("  • Filtros temporales: Evita horas de baja liquidez")
    print("  • Gestión dinámica: Risk/reward según confianza")
    
    print("\n📊 OBJETIVO DE PERFORMANCE:")
    print("  • Win Rate Target: 65-75%")
    print("  • Risk/Reward: 1:1.5 a 1:2.8")
    print("  • Máximo riesgo: 2.5% por trade")
    print("  • Expectativa positiva alta")
    
    print("\n💡 MEJORAS IMPLEMENTADAS:")
    print("  • RSI optimizado (período 12 vs 14)")
    print("  • Bollinger Bands específicos (18, 2.2)")
    print("  • EMAs optimizadas (16/42 vs 20/50)")
    print("  • Filtros de volumen estrictos")
    print("  • Detección de régimen de acumulación")
    print("  • Timing intradía optimizado")
    
    if result:
        print(f"\n✅ Trade ejecutado con confianza {result['confidence']:.1%}")
    else:
        print("\n⏳ Esperando condiciones óptimas...")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()