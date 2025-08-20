#!/usr/bin/env python3
"""
Binance Data Fetcher - Reemplazo de yfinance con datos de Binance
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BinanceDataFetcher:
    """Fetcher de datos optimizado para Binance"""
    
    BASE_URL = "https://api.binance.com/api/v3"
    
    @staticmethod
    def get_klines(symbol: str, interval: str, limit: int = 500):
        """
        Obtiene velas de Binance
        interval: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
        """
        try:
            url = f"{BinanceDataFetcher.BASE_URL}/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": min(limit, 1000)  # Binance max es 1000
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Convertir a DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 
                'volume', 'close_time', 'quote_volume', 
                'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            
            # Convertir tipos
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['Open'] = df['open'].astype(float)
            df['High'] = df['high'].astype(float)
            df['Low'] = df['low'].astype(float)
            df['Close'] = df['close'].astype(float)
            df['Volume'] = df['volume'].astype(float)
            
            # Establecer timestamp como índice
            df.set_index('timestamp', inplace=True)
            
            # Limpiar columnas innecesarias
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de {symbol}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_multiple_timeframes(symbol: str):
        """Obtiene datos en múltiples timeframes"""
        timeframes = {
            '1h': BinanceDataFetcher.get_klines(symbol, '1h', 200),
            '4h': BinanceDataFetcher.get_klines(symbol, '4h', 200),
            '1d': BinanceDataFetcher.get_klines(symbol, '1d', 100)
        }
        
        # Filtrar dataframes vacíos
        return {k: v for k, v in timeframes.items() if not v.empty}
    
    @staticmethod
    def get_ticker_24hr(symbol: str):
        """Obtiene estadísticas de 24h"""
        try:
            url = f"{BinanceDataFetcher.BASE_URL}/ticker/24hr"
            params = {"symbol": symbol}
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'current_price': float(data['lastPrice']),
                'price_change_24h': float(data['priceChange']),
                'price_change_percent_24h': float(data['priceChangePercent']),
                'volume_24h': float(data['volume']),
                'high_24h': float(data['highPrice']),
                'low_24h': float(data['lowPrice']),
                'bid': float(data['bidPrice']),
                'ask': float(data['askPrice'])
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo ticker de {symbol}: {e}")
            return None
    
    @staticmethod
    def calculate_indicators(df):
        """Calcula indicadores técnicos"""
        if df.empty:
            return df
            
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['Signal']
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        # Volume indicators
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        
        # EMAs
        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        return df
    
    @staticmethod
    def get_order_book(symbol: str, limit: int = 20):
        """Obtiene el libro de órdenes"""
        try:
            url = f"{BinanceDataFetcher.BASE_URL}/depth"
            params = {
                "symbol": symbol,
                "limit": limit
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Calcular presión de compra/venta
            total_bid_volume = sum(float(bid[1]) for bid in data['bids'])
            total_ask_volume = sum(float(ask[1]) for ask in data['asks'])
            
            buy_pressure = total_bid_volume / (total_bid_volume + total_ask_volume)
            
            return {
                'bids': data['bids'][:5],  # Top 5 bids
                'asks': data['asks'][:5],  # Top 5 asks
                'buy_pressure': buy_pressure,
                'sell_pressure': 1 - buy_pressure,
                'spread': float(data['asks'][0][0]) - float(data['bids'][0][0])
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo order book de {symbol}: {e}")
            return None

    @staticmethod
    def check_symbol_status(symbol: str):
        """Verifica si un símbolo está activo y disponible"""
        try:
            url = f"{BinanceDataFetcher.BASE_URL}/exchangeInfo"
            params = {"symbol": symbol}
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'symbols' in data and len(data['symbols']) > 0:
                symbol_info = data['symbols'][0]
                return {
                    'status': symbol_info['status'],
                    'is_trading': symbol_info['status'] == 'TRADING',
                    'base_asset': symbol_info['baseAsset'],
                    'quote_asset': symbol_info['quoteAsset'],
                    'min_price': float(next((f['minPrice'] for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'), 0)),
                    'min_qty': float(next((f['minQty'] for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), 0)),
                    'step_size': float(next((f['stepSize'] for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), 0))
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error verificando símbolo {symbol}: {e}")
            return None


if __name__ == "__main__":
    # Test del fetcher
    fetcher = BinanceDataFetcher()
    
    # Test obtener datos
    symbol = "SOLUSDT"
    print(f"\n📊 Obteniendo datos de {symbol}...")
    
    # Ticker 24h
    ticker = fetcher.get_ticker_24hr(symbol)
    if ticker:
        print(f"\n💰 Precio actual: ${ticker['current_price']:.2f}")
        print(f"📈 Cambio 24h: {ticker['price_change_percent_24h']:.2f}%")
        print(f"📊 Volumen 24h: ${ticker['volume_24h']:,.0f}")
    
    # Datos históricos con indicadores
    df = fetcher.get_klines(symbol, '1h', 100)
    if not df.empty:
        df = fetcher.calculate_indicators(df)
        print(f"\n📈 Indicadores actuales:")
        print(f"RSI: {df['RSI'].iloc[-1]:.2f}")
        print(f"MACD: {df['MACD'].iloc[-1]:.4f}")
        print(f"ATR: {df['ATR'].iloc[-1]:.4f}")
    
    # Order book
    order_book = fetcher.get_order_book(symbol)
    if order_book:
        print(f"\n📖 Order Book:")
        print(f"Buy Pressure: {order_book['buy_pressure']:.2%}")
        print(f"Spread: ${order_book['spread']:.4f}")
    
    # Estado del símbolo
    status = fetcher.check_symbol_status(symbol)
    if status:
        print(f"\n✅ Símbolo {symbol}: {status['status']}")
        print(f"Min Qty: {status['min_qty']}")
        print(f"Step Size: {status['step_size']}")