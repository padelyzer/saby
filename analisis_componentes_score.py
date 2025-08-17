#!/usr/bin/env python3
"""
Análisis detallado de componentes individuales del score
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class AnalisisComponentesScore:
    """Analiza cada componente del score individualmente"""
    
    def __init__(self):
        pass
    
    def reconstruir_score_detallado(self, df, signal_type='LONG'):
        """Reconstruye el score paso a paso para análisis"""
        
        if len(df) < 2:
            return None
            
        current = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else current
        
        # Inicializar desglose
        score_breakdown = {
            'base': 3,
            'rsi_score': 0,
            'volume_score': 0, 
            'trend_score': 0,
            'macd_score': 0,
            'strategy_score': 0,
            'volatility_score': 0,
            'total': 3
        }
        
        if signal_type == 'LONG':
            # 1. RSI Component (máximo 3 puntos)
            if current['RSI'] < 30:
                score_breakdown['rsi_score'] += 2
            elif current['RSI'] < 40:
                score_breakdown['rsi_score'] += 1
            
            if current['RSI'] < 20:
                score_breakdown['rsi_score'] += 1
                
            # 2. Volume Component (máximo 3 puntos)
            if current['Volume_Ratio'] >= 3.0:
                score_breakdown['volume_score'] += 2
            elif current['Volume_Ratio'] >= 2.0:
                score_breakdown['volume_score'] += 1
            elif current['Volume_Ratio'] >= 1.5:
                score_breakdown['volume_score'] += 0.5
                
            # 3. Trend Component (máximo 2 puntos)
            ema_trend_strong = (current['Close'] > current['EMA_21'] and 
                               current['EMA_21'] > current['EMA_50'])
            if ema_trend_strong:
                score_breakdown['trend_score'] += 1.5
            elif current['Close'] > current['EMA_21']:
                score_breakdown['trend_score'] += 0.5
                
            # 4. MACD Component (máximo 1.5 puntos)
            try:
                if current['MACD'] > current['MACD_Signal']:
                    score_breakdown['macd_score'] += 1
                    if prev['MACD'] <= prev['MACD_Signal']:
                        score_breakdown['macd_score'] += 0.5
            except:
                pass
                
            # 5. Volatility Component (máximo 1 punto)
            try:
                atr_pct = current['ATR'] / current['Close']
                if 0.02 <= atr_pct <= 0.05:
                    score_breakdown['volatility_score'] += 1
                elif atr_pct > 0.05:
                    score_breakdown['volatility_score'] -= 0.5
            except:
                pass
        
        else:  # SHORT
            # RSI para SHORT
            if current['RSI'] > 70:
                score_breakdown['rsi_score'] += 2
            elif current['RSI'] > 60:
                score_breakdown['rsi_score'] += 1
            if current['RSI'] > 80:
                score_breakdown['rsi_score'] += 1
                
            # Volume (igual)
            if current['Volume_Ratio'] >= 3.0:
                score_breakdown['volume_score'] += 2
            elif current['Volume_Ratio'] >= 2.0:
                score_breakdown['volume_score'] += 1
            elif current['Volume_Ratio'] >= 1.5:
                score_breakdown['volume_score'] += 0.5
                
            # Trend bajista
            ema_trend_bearish = (current['Close'] < current['EMA_21'] and 
                               current['EMA_21'] < current['EMA_50'])
            if ema_trend_bearish:
                score_breakdown['trend_score'] += 1.5
            elif current['Close'] < current['EMA_21']:
                score_breakdown['trend_score'] += 0.5
                
            # MACD bajista
            try:
                if current['MACD'] < current['MACD_Signal']:
                    score_breakdown['macd_score'] += 1
                    if prev['MACD'] >= prev['MACD_Signal']:
                        score_breakdown['macd_score'] += 0.5
            except:
                pass
                
            # Volatility (igual)
            try:
                atr_pct = current['ATR'] / current['Close']
                if 0.02 <= atr_pct <= 0.05:
                    score_breakdown['volatility_score'] += 1
                elif atr_pct > 0.05:
                    score_breakdown['volatility_score'] -= 0.5
            except:
                pass
        
        # Calcular total
        score_breakdown['total'] = (score_breakdown['base'] + 
                                   score_breakdown['rsi_score'] +
                                   score_breakdown['volume_score'] +
                                   score_breakdown['trend_score'] +
                                   score_breakdown['macd_score'] +
                                   score_breakdown['strategy_score'] +
                                   score_breakdown['volatility_score'])
        
        # Agregar valores actuales para análisis
        score_breakdown['current_values'] = {
            'rsi': current['RSI'],
            'volume_ratio': current['Volume_Ratio'],
            'close': current['Close'],
            'ema_21': current['EMA_21'],
            'ema_50': current['EMA_50'],
            'macd': current['MACD'],
            'macd_signal': current['MACD_Signal'],
            'atr_pct': current['ATR'] / current['Close']
        }
        
        return score_breakdown
    
    def calculate_indicators(self, df):
        """Calcula indicadores (copiado del sistema)"""
        df['EMA_21'] = df['Close'].ewm(span=21).mean()
        df['EMA_50'] = df['Close'].ewm(span=50).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        exp1 = df['Close'].ewm(span=12).mean()
        exp2 = df['Close'].ewm(span=26).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        
        df['TR'] = np.maximum(
            df['High'] - df['Low'],
            np.maximum(
                np.abs(df['High'] - df['Close'].shift(1)),
                np.abs(df['Low'] - df['Close'].shift(1))
            )
        )
        df['ATR'] = df['TR'].rolling(window=14).mean()
        
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA'].replace(0, 1)
        df['Volume_Ratio'] = df['Volume_Ratio'].fillna(1.0).clip(lower=0.1)
        
        return df
    
    def analizar_componentes_efectividad(self):
        """Analiza efectividad de cada componente"""
        
        print('🔬 ANÁLISIS DE EFECTIVIDAD POR COMPONENTE')
        print('='*70)
        
        # Obtener datos de múltiples tickers
        tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD']
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        
        all_signals = []
        
        for ticker in tickers:
            print(f'📊 Analizando {ticker}...')
            
            try:
                data = yf.Ticker(ticker)
                df = data.history(start=start_date, end=end_date, interval='1h')
                
                if len(df) < 100:
                    continue
                    
                df = self.calculate_indicators(df)
                
                # Generar múltiples puntos de análisis
                for i in range(50, len(df), 24):  # Cada 24 horas
                    historical_df = df.iloc[:i+1].copy()
                    
                    # Simular diferentes tipos de señales
                    for signal_type in ['LONG', 'SHORT']:
                        score_breakdown = self.reconstruir_score_detallado(historical_df, signal_type)
                        
                        if score_breakdown and score_breakdown['total'] >= 4.0:
                            # Simular resultado (simplificado)
                            future_periods = min(48, len(df) - i - 1)
                            if future_periods > 0:
                                current_price = df.iloc[i]['Close']
                                future_price = df.iloc[i + future_periods]['Close']
                                
                                if signal_type == 'LONG':
                                    profit_pct = (future_price - current_price) / current_price
                                else:
                                    profit_pct = (current_price - future_price) / current_price
                                
                                score_breakdown['ticker'] = ticker
                                score_breakdown['signal_type'] = signal_type
                                score_breakdown['success'] = profit_pct > 0.01  # 1% mínimo
                                score_breakdown['profit_pct'] = profit_pct * 100
                                
                                all_signals.append(score_breakdown)
                                
            except Exception as e:
                print(f'❌ Error con {ticker}: {e}')
                continue
        
        if not all_signals:
            print('❌ No se pudieron generar señales para análisis')
            return
        
        print(f'\\n📈 DATOS GENERADOS: {len(all_signals)} señales')
        
        # Analizar correlación de cada componente con éxito
        self.analizar_correlacion_componentes(all_signals)
        
        return all_signals
    
    def analizar_correlacion_componentes(self, signals):
        """Analiza correlación de cada componente con el éxito"""
        
        print(f'\\n📊 CORRELACIÓN COMPONENTES vs ÉXITO')
        print('-'*50)
        
        exitosos = [s for s in signals if s['success']]
        fallidos = [s for s in signals if not s['success']]
        
        print(f'• Señales exitosas: {len(exitosos)} ({len(exitosos)/len(signals)*100:.1f}%)')
        print(f'• Señales fallidas: {len(fallidos)} ({len(fallidos)/len(signals)*100:.1f}%)')
        
        # Analizar cada componente
        componentes = ['rsi_score', 'volume_score', 'trend_score', 'macd_score', 'volatility_score']
        
        print(f'\\n🎯 EFECTIVIDAD POR COMPONENTE:')
        
        for componente in componentes:
            avg_exitoso = np.mean([s[componente] for s in exitosos]) if exitosos else 0
            avg_fallido = np.mean([s[componente] for s in fallidos]) if fallidos else 0
            diferencia = avg_exitoso - avg_fallido
            
            # Calcular correlación más detallada
            valores_altos = [s for s in signals if s[componente] >= 1.0]
            if valores_altos:
                wr_valores_altos = len([s for s in valores_altos if s['success']]) / len(valores_altos) * 100
            else:
                wr_valores_altos = 0
            
            valores_bajos = [s for s in signals if s[componente] < 1.0]
            if valores_bajos:
                wr_valores_bajos = len([s for s in valores_bajos if s['success']]) / len(valores_bajos) * 100
            else:
                wr_valores_bajos = 0
            
            print(f'\\n{componente.upper()}:')
            print(f'  • Promedio exitosos: {avg_exitoso:.2f}')
            print(f'  • Promedio fallidos: {avg_fallido:.2f}')
            print(f'  • Diferencia: {diferencia:+.2f}')
            print(f'  • WR valores altos (≥1.0): {wr_valores_altos:.1f}%')
            print(f'  • WR valores bajos (<1.0): {wr_valores_bajos:.1f}%')
            
            # Diagnóstico
            if abs(diferencia) < 0.1:
                print(f'  🚨 INÚTIL: No discrimina entre éxito/fallo')
            elif diferencia < 0:
                print(f'  ⚠️ CONTRAPRODUCENTE: Valores altos predicen fallo')
            elif diferencia > 0.5:
                print(f'  ✅ ÚTIL: Buena predicción de éxito')
            else:
                print(f'  📊 MODERADO: Predicción débil')
        
        # Análisis de valores específicos
        print(f'\\n🔬 ANÁLISIS DE VALORES ESPECÍFICOS:')
        self.analizar_valores_especificos(signals)
    
    def analizar_valores_especificos(self, signals):
        """Analiza valores específicos problemáticos"""
        
        print(f'\\nRSI ANALYSIS:')
        exitosos = [s for s in signals if s['success']]
        fallidos = [s for s in signals if not s['success']]
        
        # RSI ranges para LONG
        long_signals = [s for s in signals if s['signal_type'] == 'LONG']
        if long_signals:
            rsi_ranges = [
                (0, 20, 'Extremo Oversold'),
                (20, 30, 'Muy Oversold'),
                (30, 40, 'Oversold'),
                (40, 60, 'Neutral'),
                (60, 100, 'Overbought')
            ]
            
            for min_rsi, max_rsi, label in rsi_ranges:
                range_signals = [s for s in long_signals if min_rsi <= s['current_values']['rsi'] < max_rsi]
                if range_signals:
                    wr = len([s for s in range_signals if s['success']]) / len(range_signals) * 100
                    print(f'  • RSI {label} ({min_rsi}-{max_rsi}): {len(range_signals)} señales, WR: {wr:.1f}%')
        
        print(f'\\nVOLUME RATIO ANALYSIS:')
        volume_ranges = [
            (1.0, 1.5, 'Bajo'),
            (1.5, 2.0, 'Moderado'),
            (2.0, 3.0, 'Alto'),
            (3.0, 10.0, 'Muy Alto')
        ]
        
        for min_vol, max_vol, label in volume_ranges:
            range_signals = [s for s in signals if min_vol <= s['current_values']['volume_ratio'] < max_vol]
            if range_signals:
                wr = len([s for s in range_signals if s['success']]) / len(range_signals) * 100
                print(f'  • Volume {label} ({min_vol}-{max_vol}): {len(range_signals)} señales, WR: {wr:.1f}%')

def main():
    """Función principal"""
    analyzer = AnalisisComponentesScore()
    signals = analyzer.analizar_componentes_efectividad()
    
    if signals:
        print(f'\\n💡 CONCLUSIONES SOBRE COMPONENTES')
        print('='*70)
        print('1. Identifica componentes INÚTILES o CONTRAPRODUCENTES')
        print('2. Ajusta pesos de componentes ÚTILES')
        print('3. Considera eliminar componentes problemáticos')
        print('4. Añade nuevos componentes más predictivos')

if __name__ == "__main__":
    main()