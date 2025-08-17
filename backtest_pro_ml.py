#!/usr/bin/env python3
"""
Sistema de Backtesting Profesional con Machine Learning
Incluye todas las mejoras avanzadas para maximizar el win rate
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Machine Learning
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib

# Análisis de sentimiento
import requests
from textblob import TextBlob

class ProfessionalBacktestML:
    """Sistema profesional con ML y análisis avanzado"""
    
    def __init__(self, capital_inicial=10000):
        self.capital_inicial = capital_inicial
        self.capital = capital_inicial
        self.position_size = 0.08  # 8% por trade (más conservador)
        self.trades = []
        self.ml_model = None
        self.scaler = StandardScaler()
        self.correlation_matrix = None
        
    def calculate_correlation_matrix(self, tickers_data):
        """Calcula matriz de correlación entre pares"""
        print("\n📊 Calculando correlaciones entre pares...")
        
        returns_df = pd.DataFrame()
        for ticker, df in tickers_data.items():
            if len(df) > 0:
                returns_df[ticker] = df['Close'].pct_change()
        
        # Calcular correlación
        self.correlation_matrix = returns_df.corr()
        
        # Identificar pares altamente correlacionados
        high_corr_pairs = []
        for i in range(len(self.correlation_matrix.columns)):
            for j in range(i+1, len(self.correlation_matrix.columns)):
                corr_value = self.correlation_matrix.iloc[i, j]
                if abs(corr_value) > 0.7:  # Alta correlación
                    pair1 = self.correlation_matrix.columns[i]
                    pair2 = self.correlation_matrix.columns[j]
                    high_corr_pairs.append((pair1, pair2, corr_value))
                    print(f"   ⚠️ Alta correlación: {pair1} <-> {pair2}: {corr_value:.2f}")
        
        return high_corr_pairs
    
    def get_market_sentiment(self):
        """Analiza el sentimiento del mercado crypto"""
        try:
            # Fear & Greed Index API (simulado para demo)
            # En producción usar: https://api.alternative.me/fng/
            
            # Simulación de sentimiento
            import random
            fear_greed = random.randint(20, 80)
            
            if fear_greed < 30:
                sentiment = "extreme_fear"
                sentiment_score = -2
            elif fear_greed < 45:
                sentiment = "fear"
                sentiment_score = -1
            elif fear_greed < 55:
                sentiment = "neutral"
                sentiment_score = 0
            elif fear_greed < 70:
                sentiment = "greed"
                sentiment_score = 1
            else:
                sentiment = "extreme_greed"
                sentiment_score = 2
            
            return {
                'value': fear_greed,
                'sentiment': sentiment,
                'score': sentiment_score
            }
        except:
            return {'value': 50, 'sentiment': 'neutral', 'score': 0}
    
    def analyze_news_sentiment(self, ticker):
        """Analiza sentimiento de noticias (simulado)"""
        # En producción usar APIs de noticias reales
        # Por ejemplo: NewsAPI, Alpha Vantage News, etc.
        
        # Simulación de análisis
        sentiments = [0.1, -0.2, 0.3, 0, 0.5, -0.1]
        avg_sentiment = np.mean(sentiments)
        
        if avg_sentiment > 0.2:
            return 1  # Positivo
        elif avg_sentiment < -0.2:
            return -1  # Negativo
        else:
            return 0  # Neutral
    
    def check_liquidity_hours(self, timestamp):
        """Verifica si estamos en horarios de alta liquidez"""
        hour = timestamp.hour
        
        # Horarios de alta liquidez (UTC)
        # 08:00-10:00 UTC (Asia abierta)
        # 14:00-16:00 UTC (Europa abierta) 
        # 20:00-22:00 UTC (USA abierta)
        
        high_liquidity_hours = [
            (8, 10),   # Asia
            (14, 16),  # Europa
            (20, 22)   # USA
        ]
        
        for start, end in high_liquidity_hours:
            if start <= hour < end:
                return True, 2  # Alta liquidez, bonus score
        
        # Horarios moderados
        moderate_hours = [(10, 14), (16, 20)]
        for start, end in moderate_hours:
            if start <= hour < end:
                return True, 1  # Liquidez moderada
        
        # Horarios de baja liquidez (evitar)
        return False, 0
    
    def prepare_ml_features(self, df, idx):
        """Prepara features para el modelo ML"""
        if idx < 50:
            return None
            
        features = []
        
        # Precio y tendencia
        close_price = df['Close'].iloc[idx]
        sma_20 = df['Close'].iloc[idx-20:idx].mean()
        sma_50 = df['Close'].iloc[idx-50:idx].mean()
        
        # Limitar valores extremos
        features.append(np.clip(close_price / sma_20 - 1, -0.5, 0.5))  # Distancia a SMA20
        features.append(np.clip(close_price / sma_50 - 1, -0.5, 0.5))  # Distancia a SMA50
        features.append(np.clip((sma_20 / sma_50) - 1, -0.5, 0.5))     # Cruce de medias
        
        # RSI
        delta = df['Close'].iloc[idx-14:idx].diff()
        gain = (delta.where(delta > 0, 0)).mean()
        loss = (-delta.where(delta < 0, 0)).mean()
        rs = gain / loss if loss != 0 else 0
        rsi = 100 - (100 / (1 + rs)) if rs != 0 else 50
        features.append(rsi / 100)  # Normalizado
        
        # Volumen
        vol_mean = df['Volume'].iloc[idx-20:idx].mean()
        if vol_mean > 0:
            vol_ratio = df['Volume'].iloc[idx] / vol_mean
            # Limitar valores extremos
            vol_ratio = np.clip(vol_ratio, 0.1, 10)
            features.append(np.log(vol_ratio))
        else:
            features.append(0)
        
        # Volatilidad (ATR)
        high_low = df['High'].iloc[idx-14:idx] - df['Low'].iloc[idx-14:idx]
        atr = high_low.mean()
        if close_price > 0:
            atr_ratio = np.clip(atr / close_price, 0, 0.1)  # Limitar a máx 10%
        else:
            atr_ratio = 0.01
        features.append(atr_ratio)
        
        # Momentum (limitado para evitar valores extremos)
        returns_5d = np.clip((close_price / df['Close'].iloc[idx-5] - 1), -0.5, 0.5)
        returns_10d = np.clip((close_price / df['Close'].iloc[idx-10] - 1), -0.5, 0.5)
        returns_20d = np.clip((close_price / df['Close'].iloc[idx-20] - 1), -0.5, 0.5)
        
        features.extend([returns_5d, returns_10d, returns_20d])
        
        # Bollinger Bands
        bb_std = df['Close'].iloc[idx-20:idx].std()
        bb_upper = sma_20 + (bb_std * 2)
        bb_lower = sma_20 - (bb_std * 2)
        if bb_upper != bb_lower and bb_upper > 0 and bb_lower > 0:
            bb_position = (close_price - bb_lower) / (bb_upper - bb_lower)
            bb_position = np.clip(bb_position, 0, 1)  # Limitar entre 0 y 1
        else:
            bb_position = 0.5
        features.append(bb_position)
        
        return np.array(features)
    
    def train_ml_model(self, training_data):
        """Entrena el modelo de ML con datos históricos"""
        print("\n🤖 Entrenando modelo de Machine Learning...")
        
        X = []
        y = []
        
        for ticker, df in training_data.items():
            if len(df) < 100:
                continue
                
            for i in range(50, len(df)-10):
                features = self.prepare_ml_features(df, i)
                if features is not None:
                    X.append(features)
                    
                    # Label: 1 si el precio sube >1% en próximas 10 barras
                    future_return = (df['Close'].iloc[i+10] / df['Close'].iloc[i] - 1) * 100
                    y.append(1 if future_return > 1 else 0)
        
        if len(X) > 100:
            X = np.array(X)
            y = np.array(y)
            
            # Escalar features
            X_scaled = self.scaler.fit_transform(X)
            
            # Dividir en train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
            
            # Entrenar Random Forest
            self.ml_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=20,
                random_state=42
            )
            
            self.ml_model.fit(X_train, y_train)
            
            # Evaluar
            train_score = self.ml_model.score(X_train, y_train)
            test_score = self.ml_model.score(X_test, y_test)
            
            print(f"   ✅ Modelo entrenado - Train: {train_score:.2%}, Test: {test_score:.2%}")
            
            # Feature importance
            importances = self.ml_model.feature_importances_
            feature_names = ['SMA20_dist', 'SMA50_dist', 'SMA_cross', 'RSI', 'Volume', 
                           'ATR', 'Mom_5d', 'Mom_10d', 'Mom_20d', 'BB_position']
            
            print("\n   📊 Importancia de features:")
            for name, imp in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:5]:
                print(f"      • {name}: {imp:.3f}")
            
            return True
        
        print("   ⚠️ Datos insuficientes para entrenar ML")
        return False
    
    def get_ml_prediction(self, df, idx):
        """Obtiene predicción del modelo ML"""
        if self.ml_model is None:
            return 0.5, 0
            
        features = self.prepare_ml_features(df, idx)
        if features is None:
            return 0.5, 0
            
        try:
            features_scaled = self.scaler.transform([features])
            
            # Predicción probabilística
            proba = self.ml_model.predict_proba(features_scaled)[0]
            prediction = proba[1]  # Probabilidad de clase 1 (subida)
            
            # Confidence score basado en probabilidad
            if prediction > 0.7:
                confidence = 2
            elif prediction > 0.6:
                confidence = 1
            elif prediction < 0.3:
                confidence = -2
            elif prediction < 0.4:
                confidence = -1
            else:
                confidence = 0
                
            return prediction, confidence
        except:
            return 0.5, 0
    
    def calculate_dynamic_trailing_stop(self, entry_price, current_price, atr, trade_type):
        """Calcula trailing stop dinámico basado en ATR"""
        
        if trade_type == 'LONG':
            # Si el precio subió, ajustar stop
            if current_price > entry_price:
                profit_pct = (current_price / entry_price - 1) * 100
                
                if profit_pct > 5:  # >5% ganancia
                    # Stop muy ajustado para proteger ganancias
                    trailing_stop = current_price - (atr * 0.5)
                elif profit_pct > 3:  # 3-5% ganancia
                    # Stop moderado
                    trailing_stop = current_price - (atr * 1)
                elif profit_pct > 1:  # 1-3% ganancia
                    # Stop normal
                    trailing_stop = current_price - (atr * 1.5)
                else:
                    # Mantener stop original
                    trailing_stop = entry_price - (atr * 2)
                
                # Nunca bajar el stop
                return max(trailing_stop, entry_price - (atr * 2))
            else:
                return entry_price - (atr * 2)
                
        else:  # SHORT
            if current_price < entry_price:
                profit_pct = (entry_price / current_price - 1) * 100
                
                if profit_pct > 5:
                    trailing_stop = current_price + (atr * 0.5)
                elif profit_pct > 3:
                    trailing_stop = current_price + (atr * 1)
                elif profit_pct > 1:
                    trailing_stop = current_price + (atr * 1.5)
                else:
                    trailing_stop = entry_price + (atr * 2)
                
                return min(trailing_stop, entry_price + (atr * 2))
            else:
                return entry_price + (atr * 2)
    
    def advanced_signal_generation(self, df, ticker, idx, market_sentiment, correlated_pairs):
        """Genera señales con todos los filtros avanzados"""
        
        if idx < 100 or idx >= len(df) - 1:
            return None
            
        current_price = df['Close'].iloc[idx]
        timestamp = df.index[idx]
        
        # === FILTROS AVANZADOS ===
        score = 0
        
        # 1. Machine Learning Prediction
        ml_pred, ml_confidence = self.get_ml_prediction(df, idx)
        score += ml_confidence
        
        # 2. Sentimiento del mercado
        score += market_sentiment['score'] * 0.5
        
        # 3. Sentimiento de noticias
        news_sentiment = self.analyze_news_sentiment(ticker)
        score += news_sentiment
        
        # 4. Horario de liquidez
        is_liquid, liquidity_score = self.check_liquidity_hours(timestamp)
        if not is_liquid:
            return None  # No operar en baja liquidez
        score += liquidity_score
        
        # 5. Correlación con otros pares
        # Evitar trades si hay alta correlación y ya tenemos posición
        for pair1, pair2, corr in correlated_pairs:
            if ticker in [pair1, pair2]:
                # Penalizar si correlación muy alta
                if abs(corr) > 0.8:
                    score -= 1
        
        # === ANÁLISIS TÉCNICO TRADICIONAL ===
        
        # Medias móviles
        sma_20 = df['Close'].iloc[idx-20:idx].mean()
        sma_50 = df['Close'].iloc[idx-50:idx].mean()
        sma_200 = df['Close'].iloc[idx-200:idx].mean()
        
        # RSI
        delta = df['Close'].iloc[idx-14:idx].diff()
        gain = (delta.where(delta > 0, 0)).mean()
        loss = (-delta.where(delta < 0, 0)).mean()
        rs = gain / loss if loss != 0 else 0
        rsi = 100 - (100 / (1 + rs)) if rs != 0 else 50
        
        # MACD
        ema_12 = df['Close'].ewm(span=12).mean().iloc[idx]
        ema_26 = df['Close'].ewm(span=26).mean().iloc[idx]
        macd = ema_12 - ema_26
        signal_line = df['Close'].ewm(span=9).mean().iloc[idx]
        
        # Bollinger Bands
        bb_std = df['Close'].iloc[idx-20:idx].std()
        bb_upper = sma_20 + (bb_std * 2)
        bb_lower = sma_20 - (bb_std * 2)
        
        # ATR para stops
        high_low = df['High'].iloc[idx-14:idx] - df['Low'].iloc[idx-14:idx]
        atr = high_low.mean()
        
        # Volumen
        vol_ratio = df['Volume'].iloc[idx] / df['Volume'].iloc[idx-20:idx].mean()
        
        # === SEÑALES ===
        signal_type = None
        
        # LONG Signal
        if ml_pred > 0.55:  # ML predice subida (reducido de 0.6 a 0.55)
            if (current_price > sma_50 > sma_200 and  # Tendencia alcista
                25 < rsi < 75 and  # RSI no sobrecomprado (rango ampliado)
                macd > signal_line and  # MACD positivo
                vol_ratio > 1.2):  # Volumen confirmación
                
                signal_type = 'LONG'
                score += 3
                
                # Bonus si rebota en soporte
                if current_price < sma_20 * 1.02 and current_price > sma_20 * 0.98:
                    score += 2
        
        # SHORT Signal
        elif ml_pred < 0.45:  # ML predice bajada (aumentado de 0.4 a 0.45)
            if (current_price < sma_50 < sma_200 and  # Tendencia bajista
                30 < rsi < 70 and  # RSI no sobrevendido
                macd < signal_line and  # MACD negativo
                vol_ratio > 1.2):  # Volumen confirmación
                
                signal_type = 'SHORT'
                score += 3
                
                # Bonus si rechaza resistencia
                if current_price > sma_20 * 0.98 and current_price < sma_20 * 1.02:
                    score += 2
        
        # Generar señal si score es suficiente (reducido de 6 a 4 para más señales)
        if signal_type and score >= 4:
            return {
                'date': timestamp,
                'ticker': ticker,
                'type': signal_type,
                'entry_price': current_price,
                'initial_stop': current_price - (atr * 2) if signal_type == 'LONG' else current_price + (atr * 2),
                'take_profit': current_price + (atr * 4) if signal_type == 'LONG' else current_price - (atr * 4),
                'confidence': score,
                'ml_prediction': ml_pred,
                'atr': atr,
                'sentiment': market_sentiment['sentiment']
            }
        
        return None
    
    def simulate_trades_with_trailing_stops(self, signals, df):
        """Simula trades con trailing stops dinámicos"""
        
        for signal in signals:
            entry_idx = df.index.get_loc(signal['date'])
            
            if entry_idx >= len(df) - 2:
                continue
            
            # Variables de seguimiento
            exit_price = None
            exit_reason = None
            exit_date = None
            current_stop = signal['initial_stop']
            highest_price = signal['entry_price'] if signal['type'] == 'LONG' else None
            lowest_price = signal['entry_price'] if signal['type'] == 'SHORT' else None
            
            for j in range(entry_idx + 1, min(entry_idx + 100, len(df))):
                current_bar = df.iloc[j]
                
                # Actualizar trailing stop
                if signal['type'] == 'LONG':
                    if current_bar['High'] > highest_price:
                        highest_price = current_bar['High']
                        # Actualizar trailing stop
                        new_stop = self.calculate_dynamic_trailing_stop(
                            signal['entry_price'],
                            highest_price,
                            signal['atr'],
                            'LONG'
                        )
                        current_stop = max(current_stop, new_stop)
                    
                    # Verificar salidas
                    if current_bar['High'] >= signal['take_profit']:
                        exit_price = signal['take_profit']
                        exit_reason = 'TP'
                        exit_date = current_bar.name
                        break
                    elif current_bar['Low'] <= current_stop:
                        exit_price = current_stop
                        exit_reason = 'TRAILING_STOP' if current_stop > signal['initial_stop'] else 'SL'
                        exit_date = current_bar.name
                        break
                
                else:  # SHORT
                    if current_bar['Low'] < lowest_price:
                        lowest_price = current_bar['Low']
                        new_stop = self.calculate_dynamic_trailing_stop(
                            signal['entry_price'],
                            lowest_price,
                            signal['atr'],
                            'SHORT'
                        )
                        current_stop = min(current_stop, new_stop)
                    
                    if current_bar['Low'] <= signal['take_profit']:
                        exit_price = signal['take_profit']
                        exit_reason = 'TP'
                        exit_date = current_bar.name
                        break
                    elif current_bar['High'] >= current_stop:
                        exit_price = current_stop
                        exit_reason = 'TRAILING_STOP' if current_stop < signal['initial_stop'] else 'SL'
                        exit_date = current_bar.name
                        break
                
                # Salida por tiempo (máximo 50 barras)
                if j >= entry_idx + 50:
                    exit_price = current_bar['Close']
                    exit_reason = 'TIME'
                    exit_date = current_bar.name
                    break
            
            if exit_price:
                # Calcular profit
                if signal['type'] == 'LONG':
                    profit_pct = ((exit_price - signal['entry_price']) / signal['entry_price']) * 100
                else:
                    profit_pct = ((signal['entry_price'] - exit_price) / signal['entry_price']) * 100
                
                profit_usd = self.capital * self.position_size * (profit_pct / 100)
                
                trade = {
                    'ticker': signal['ticker'],
                    'type': signal['type'],
                    'entry_date': signal['date'],
                    'exit_date': exit_date,
                    'entry_price': signal['entry_price'],
                    'exit_price': exit_price,
                    'profit_pct': profit_pct,
                    'profit_usd': profit_usd,
                    'exit_reason': exit_reason,
                    'confidence': signal['confidence'],
                    'ml_prediction': signal['ml_prediction'],
                    'sentiment': signal['sentiment']
                }
                
                self.trades.append(trade)
                self.capital += profit_usd
    
    def run(self, tickers):
        """Ejecuta el backtesting profesional con ML"""
        
        print("""
╔════════════════════════════════════════════════════════════════╗
║        BACKTESTING PROFESIONAL CON MACHINE LEARNING             ║
║                    Sistema Avanzado v3.0                        ║
╚════════════════════════════════════════════════════════════════╝
        """)
        
        print(f"\n📊 Configuración:")
        print(f"• Capital Inicial: ${self.capital_inicial:,}")
        print(f"• Tickers: {tickers}")
        print(f"• Tamaño Posición: {self.position_size*100}%")
        print(f"• Sistema: ML + Sentiment + Correlación + Trailing Stops")
        print("="*60)
        
        # Descargar datos
        print("\n📥 Descargando datos históricos...")
        all_data = {}
        
        for ticker in tickers:
            try:
                print(f"   Descargando {ticker}...")
                data = yf.Ticker(ticker)
                df = data.history(period="3mo", interval="1h")  # 3 meses para ML
                
                if len(df) >= 200:
                    all_data[ticker] = df
                    print(f"   ✅ {ticker}: {len(df)} barras")
                else:
                    print(f"   ⚠️ {ticker}: Datos insuficientes")
            except Exception as e:
                print(f"   ❌ Error con {ticker}: {e}")
        
        if not all_data:
            print("❌ No se pudieron obtener datos")
            return
        
        # Análisis de correlación
        high_corr_pairs = self.calculate_correlation_matrix(all_data)
        
        # Entrenar modelo ML
        self.train_ml_model(all_data)
        
        # Obtener sentimiento del mercado
        market_sentiment = self.get_market_sentiment()
        print(f"\n📊 Sentimiento del Mercado: {market_sentiment['sentiment']} ({market_sentiment['value']})")
        
        # Generar señales con todos los filtros
        print("\n🎯 Generando señales con filtros avanzados...")
        all_signals = []
        
        for ticker, df in all_data.items():
            print(f"\n   Analizando {ticker}...")
            ticker_signals = []
            
            # Solo analizar últimos 30 días para backtesting
            start_idx = max(200, len(df) - 720)  # ~30 días en horas
            
            for idx in range(start_idx, len(df) - 1):
                signal = self.advanced_signal_generation(
                    df, ticker, idx, market_sentiment, high_corr_pairs
                )
                
                if signal:
                    # Evitar señales muy cercanas
                    if not ticker_signals or (signal['date'] - ticker_signals[-1]['date']).total_seconds() / 3600 > 24:
                        ticker_signals.append(signal)
            
            print(f"      📊 Señales generadas: {len(ticker_signals)}")
            all_signals.extend(ticker_signals)
        
        # Ordenar señales por fecha
        all_signals.sort(key=lambda x: x['date'])
        
        # Limitar señales concurrentes basado en correlación
        filtered_signals = self.filter_correlated_signals(all_signals)
        
        print(f"\n📊 Total señales después de filtros: {len(filtered_signals)}")
        
        # Simular trades con trailing stops
        print("\n💼 Simulando trades con trailing stops...")
        for ticker, df in all_data.items():
            ticker_signals = [s for s in filtered_signals if s['ticker'] == ticker]
            if ticker_signals:
                self.simulate_trades_with_trailing_stops(ticker_signals, df)
        
        # Mostrar resultados
        self.show_advanced_results()
    
    def filter_correlated_signals(self, signals):
        """Filtra señales de pares altamente correlacionados"""
        filtered = []
        active_tickers = set()
        
        for signal in signals:
            # Verificar correlación con tickers activos
            can_add = True
            
            if self.correlation_matrix is not None:
                for active in active_tickers:
                    if active in self.correlation_matrix.columns and signal['ticker'] in self.correlation_matrix.columns:
                        corr = self.correlation_matrix.loc[active, signal['ticker']]
                        if abs(corr) > 0.8:  # Muy alta correlación
                            can_add = False
                            break
            
            if can_add:
                filtered.append(signal)
                active_tickers.add(signal['ticker'])
        
        return filtered
    
    def show_advanced_results(self):
        """Muestra resultados detallados con métricas avanzadas"""
        
        print("\n" + "="*60)
        print("📊 RESULTADOS DEL BACKTESTING PROFESIONAL")
        print("="*60)
        
        if not self.trades:
            print("❌ No se generaron trades")
            return
        
        # Métricas básicas
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t['profit_pct'] > 0]
        losing_trades = [t for t in self.trades if t['profit_pct'] <= 0]
        
        win_rate = (len(winning_trades) / total_trades) * 100
        total_return = ((self.capital / self.capital_inicial) - 1) * 100
        
        avg_win = np.mean([t['profit_pct'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['profit_pct'] for t in losing_trades]) if losing_trades else 0
        
        # Profit Factor
        gross_profit = sum(t['profit_usd'] for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t['profit_usd'] for t in losing_trades)) if losing_trades else 1
        profit_factor = gross_profit / gross_loss
        
        # Risk/Reward
        risk_reward = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # Sharpe Ratio simulado
        returns = [t['profit_pct'] for t in self.trades]
        sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        print(f"\n💰 CAPITAL:")
        print(f"• Inicial: ${self.capital_inicial:,.2f}")
        print(f"• Final: ${self.capital:,.2f}")
        print(f"• Retorno: {total_return:+.2f}%")
        
        print(f"\n📈 MÉTRICAS PRINCIPALES:")
        print(f"• Total Trades: {total_trades}")
        print(f"• Win Rate: {win_rate:.1f}%")
        print(f"• Profit Factor: {profit_factor:.2f}")
        print(f"• Risk/Reward: 1:{risk_reward:.1f}")
        print(f"• Sharpe Ratio: {sharpe:.2f}")
        
        print(f"\n🎯 ANÁLISIS DE TRADES:")
        print(f"• Trades Ganadores: {len(winning_trades)}")
        print(f"• Trades Perdedores: {len(losing_trades)}")
        print(f"• Promedio Ganancia: {avg_win:+.2f}%")
        print(f"• Promedio Pérdida: {avg_loss:+.2f}%")
        
        # Análisis por tipo de salida
        exit_analysis = {}
        for trade in self.trades:
            exit_reason = trade['exit_reason']
            if exit_reason not in exit_analysis:
                exit_analysis[exit_reason] = {'count': 0, 'profit': 0, 'wins': 0}
            exit_analysis[exit_reason]['count'] += 1
            exit_analysis[exit_reason]['profit'] += trade['profit_usd']
            if trade['profit_pct'] > 0:
                exit_analysis[exit_reason]['wins'] += 1
        
        print(f"\n📊 ANÁLISIS POR TIPO DE SALIDA:")
        for reason, stats in sorted(exit_analysis.items(), key=lambda x: x[1]['profit'], reverse=True):
            wr = (stats['wins'] / stats['count'] * 100) if stats['count'] > 0 else 0
            print(f"• {reason}: {stats['count']} trades (WR: {wr:.0f}%) | PnL: ${stats['profit']:+.2f}")
        
        # Análisis por sentimiento
        sentiment_analysis = {}
        for trade in self.trades:
            sentiment = trade.get('sentiment', 'unknown')
            if sentiment not in sentiment_analysis:
                sentiment_analysis[sentiment] = {'count': 0, 'wins': 0}
            sentiment_analysis[sentiment]['count'] += 1
            if trade['profit_pct'] > 0:
                sentiment_analysis[sentiment]['wins'] += 1
        
        print(f"\n🎭 ANÁLISIS POR SENTIMIENTO:")
        for sentiment, stats in sentiment_analysis.items():
            wr = (stats['wins'] / stats['count'] * 100) if stats['count'] > 0 else 0
            print(f"• {sentiment}: {stats['count']} trades (WR: {wr:.0f}%)")
        
        # Trades con alta confianza ML
        high_ml_trades = [t for t in self.trades if t.get('ml_prediction', 0.5) > 0.7 or t.get('ml_prediction', 0.5) < 0.3]
        if high_ml_trades:
            ml_wins = [t for t in high_ml_trades if t['profit_pct'] > 0]
            ml_wr = (len(ml_wins) / len(high_ml_trades)) * 100
            print(f"\n🤖 TRADES CON ALTA CONFIANZA ML:")
            print(f"• Total: {len(high_ml_trades)}")
            print(f"• Win Rate: {ml_wr:.1f}%")
        
        # Mejor y peor trade
        if self.trades:
            best_trade = max(self.trades, key=lambda t: t['profit_pct'])
            worst_trade = min(self.trades, key=lambda t: t['profit_pct'])
            
            print(f"\n💡 MEJORES Y PEORES:")
            print(f"• Mejor: {best_trade['ticker']} {best_trade['profit_pct']:+.2f}% ({best_trade['exit_reason']})")
            print(f"• Peor: {worst_trade['ticker']} {worst_trade['profit_pct']:+.2f}% ({worst_trade['exit_reason']})")
        
        # Evaluación final
        print(f"\n✨ EVALUACIÓN FINAL:")
        
        if win_rate >= 70:
            print("🌟 EXCELENTE: Win Rate ≥ 70%")
        elif win_rate >= 60:
            print("✅ MUY BUENO: Win Rate 60-70%")
        elif win_rate >= 55:
            print("✅ BUENO: Win Rate 55-60%")
        else:
            print("⚠️ MEJORABLE: Win Rate < 55%")
        
        if profit_factor >= 2:
            print("🌟 EXCELENTE: Profit Factor ≥ 2")
        elif profit_factor >= 1.5:
            print("✅ BUENO: Profit Factor 1.5-2")
        else:
            print("⚠️ MEJORABLE: Profit Factor < 1.5")
        
        if sharpe >= 2:
            print("🌟 EXCELENTE: Sharpe Ratio ≥ 2")
        elif sharpe >= 1:
            print("✅ BUENO: Sharpe Ratio 1-2")
        else:
            print("⚠️ MEJORABLE: Sharpe Ratio < 1")
        
        # Proyección
        print(f"\n💡 PROYECCIÓN (basada en performance histórico):")
        monthly_return = total_return * (30 / 30)  # Ya es mensual
        print(f"• Retorno Mensual: {monthly_return:+.1f}%")
        print(f"• Retorno Anualizado: {(((1 + monthly_return/100) ** 12) - 1) * 100:+.1f}%")
        
        print("\n" + "="*60)
        print("✅ BACKTESTING PROFESIONAL COMPLETADO")
        print("="*60)
        
        # Guardar resultados
        if self.trades:
            df_trades = pd.DataFrame(self.trades)
            df_trades.to_csv('backtest_ml_results.csv', index=False)
            print("\n💾 Resultados guardados en backtest_ml_results.csv")
            
            # Guardar modelo ML
            if self.ml_model:
                joblib.dump(self.ml_model, 'trading_ml_model.pkl')
                joblib.dump(self.scaler, 'trading_scaler.pkl')
                print("🤖 Modelo ML guardado en trading_ml_model.pkl")

if __name__ == "__main__":
    # Ejecutar backtesting profesional
    backtest = ProfessionalBacktestML(capital_inicial=10000)
    
    # Tickers principales
    tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'ADA-USD']
    
    # Ejecutar sistema completo
    backtest.run(tickers)