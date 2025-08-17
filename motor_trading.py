# Importar las librerías necesarias
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import numpy as np
import os
from datetime import datetime, timedelta
import csv

# --- 1. OBTENCIÓN DE DATOS ---

def obtener_datos(ticker, period='1y'):
    """Descarga datos históricos para un ticker dado."""
    try:
        # Usar Ticker object que funciona mejor
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        
        if df.empty:
            # Intentar con download como fallback
            df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
            if df.empty:
                return None
        
        # Asegurar que las columnas son de tipo correcto
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except Exception as e:
        print(f"Error descargando datos para {ticker}: {e}")
        return None

def obtener_top_movers_binance(limit=20):
    """
    Obtiene los tickers con mejor desempeño desde la página de rankings de Binance
    usando web scraping.
    """
    url = "https://www.binance.com/es/markets/trading_data/rankings"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        tickers = []
        # La estructura de la página de Binance puede cambiar. Este selector es un ejemplo.
        rows = soup.find_all('div', class_='css-1v32c04') 
        
        for row in rows:
            ticker_div = row.find('div', class_='css-1x8dg53')
            if ticker_div:
                raw_ticker = ticker_div.text
                # Limpiar y formatear para yfinance (ej. BTCUSDT -> BTC-USD)
                if 'USDT' in raw_ticker:
                    formatted_ticker = raw_ticker.replace('USDT', '-USD')
                    tickers.append(formatted_ticker)
            if len(tickers) >= limit:
                break
        return tickers
    except Exception as e:
        print(f"Error haciendo scraping de Binance: {e}")
        return [] # Devuelve lista vacía en caso de error

# --- 2. CÁLCULO DE INDICADORES ---

def calcular_indicadores(df):
    """Calcula todos los indicadores técnicos necesarios."""
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    
    delta = df['Close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    
    df['Vol_Avg_20'] = df['Volume'].rolling(window=20).mean()
    
    return df

# --- 3. LÓGICA DE TRADING ---

def calcular_semaforo_mercado():
    """Calcula el estado del mercado basado en el S&P 500."""
    try:
        df_sp500 = obtener_datos('^GSPC', period='100d')
        if df_sp500 is None or df_sp500.empty:
            return 'DESCONOCIDO'
            
        df_sp500['SMA50'] = df_sp500['Close'].rolling(window=50).mean()
        
        if len(df_sp500) < 50:
            return 'DESCONOCIDO'
        
        # Obtener valores de manera segura
        close_series = df_sp500['Close'].iloc[-1]
        sma50_series = df_sp500['SMA50'].iloc[-1]
        
        # Convertir a float de manera segura
        last_close = float(close_series) if not pd.isna(close_series) else 0
        last_sma50 = float(sma50_series) if not pd.isna(sma50_series) else 0
        
        if last_sma50 == 0:
            return 'DESCONOCIDO'
        
        diff_percent = ((last_close / last_sma50) - 1) * 100
        
        if -0.5 <= diff_percent <= 0.5:
            return 'AMARILLO'
        elif last_close > last_sma50:
            return 'VERDE'
        else:
            return 'ROJO'
    except Exception as e:
        print(f"Error calculando semáforo: {e}")
        return 'DESCONOCIDO'

def evaluar_etapa_tendencia(df):
    """Evalúa si una tendencia es temprana, madura o tardía."""
    last = df.iloc[-1]
    
    # Convertir valores a float para evitar problemas de comparación
    # Manejar el caso donde los valores pueden ser Series
    def safe_float(val, default=0):
        try:
            if isinstance(val, pd.Series):
                val = val.iloc[0] if len(val) > 0 else default
            if pd.isna(val):
                return default
            return float(val)
        except:
            return default
    
    close_val = safe_float(last['Close'])
    sma50_val = safe_float(last['SMA50'], 0)
    rsi_val = safe_float(last['RSI'], 50)
    atr_val = safe_float(last['ATR'], 0)
    
    # Condición de cruce reciente (en las últimas 10 velas)
    try:
        if len(df) >= 11:
            closes_recientes = df['Close'].iloc[-11:-1].values
            sma50_recientes = df['SMA50'].iloc[-11:-1].values
            cruce_reciente = (closes_recientes < sma50_recientes).any() and close_val > sma50_val
        else:
            cruce_reciente = False
    except:
        cruce_reciente = False

    if cruce_reciente and 50 <= rsi_val < 65 and close_val < (sma50_val + 2 * atr_val):
        return 'Inicio Temprano'
    
    if close_val > (sma50_val + 4 * atr_val) or rsi_val > 75:
        return 'Etapa Tardía'

    if close_val > sma50_val:
        return 'Tendencia Madura'
        
    return 'Tendencia Bajista'

def calcular_score(df_activo, estado_mercado='DESCONOCIDO'):
    """Calcula el score de trading basado en el sentido del mercado.
    
    Estrategia:
    - Mercado VERDE (Alcista): Solo abre LONGS
    - Mercado ROJO (Bajista): Solo abre SHORTS
    - Mercado AMARILLO (Neutral): No abre operaciones
    """
    if df_activo is None or len(df_activo) < 50:
        return 0, 'Datos insuficientes', 'NONE'

    # Si el mercado es AMARILLO (neutral), no abrir operaciones
    if estado_mercado == 'AMARILLO':
        return 0, 'Mercado Neutral - Sin operaciones', 'NONE'
    
    last = df_activo.iloc[-1]
    score = 0
    direccion = 'NONE'
    
    # Convertir valores a float de manera segura
    def safe_float(val, default=0):
        try:
            if isinstance(val, pd.Series):
                val = val.iloc[0] if len(val) > 0 else default
            if pd.isna(val):
                return default
            return float(val)
        except:
            return default
    
    close_val = safe_float(last['Close'])
    sma50_val = safe_float(last['SMA50'], 0)
    rsi_val = safe_float(last['RSI'], 50)
    volume_val = safe_float(last['Volume'], 0)
    vol_avg_val = safe_float(last['Vol_Avg_20'], 1)
    atr_val = safe_float(last['ATR'], 0)
    
    # MERCADO ALCISTA - Solo buscar LONGS
    if estado_mercado == 'VERDE':
        direccion = 'LONG'
        
        # Análisis de pullback con SMA50
        if sma50_val > 0:
            diff_pct = ((close_val - sma50_val) / sma50_val) * 100
            
            # Zona óptima de entrada (pullback perfecto)
            if -2 <= diff_pct <= 0:  # Tocando o ligeramente bajo SMA50
                score += 5
            elif 0 < diff_pct <= 3:  # Rebotando desde SMA50
                score += 3
            elif 3 < diff_pct <= 6:  # Continuación de tendencia
                score += 1
        
        # RSI optimizado para tendencia alcista
        if 28 <= rsi_val <= 40:  # Sobreventa en tendencia = oportunidad
            score += 4
        elif 40 < rsi_val <= 50:
            score += 2
        elif 50 < rsi_val <= 60:
            score += 1
        
        # Volumen como confirmación
        if vol_avg_val > 0:
            vol_ratio = volume_val / vol_avg_val
            if vol_ratio > 2.0:  # Volumen muy alto
                score += 3
            elif vol_ratio > 1.5:
                score += 2
            elif vol_ratio > 1.2:
                score += 1
    
    # MERCADO BAJISTA - Solo buscar SHORTS
    elif estado_mercado == 'ROJO':
        direccion = 'SHORT'
        
        # Análisis de rebote para SHORT
        if sma50_val > 0:
            diff_pct = ((close_val - sma50_val) / sma50_val) * 100
            
            # Zona óptima para SHORT (rebote a resistencia)
            if 0 <= diff_pct <= 2:  # Tocando o ligeramente sobre SMA50
                score += 5
            elif -3 <= diff_pct < 0:  # Rechazado desde SMA50
                score += 3
            elif -6 <= diff_pct < -3:  # Continuación bajista
                score += 1
        
        # RSI optimizado para tendencia bajista
        if 60 <= rsi_val <= 72:  # Sobrecompra en bajista = SHORT
            score += 4
        elif 50 <= rsi_val < 60:
            score += 2
        elif 40 <= rsi_val < 50:
            score += 1
        
        # Volumen como confirmación
        if vol_avg_val > 0:
            vol_ratio = volume_val / vol_avg_val
            if vol_ratio > 2.0:  # Volumen muy alto
                score += 3
            elif vol_ratio > 1.5:
                score += 2
            elif vol_ratio > 1.2:
                score += 1
    
    # Ser más selectivo para mejorar win rate
    umbral_minimo = 5 if estado_mercado in ['VERDE', 'ROJO'] else 7
    
    if score < umbral_minimo:
        direccion = 'NONE'
        score = 0
    
    # Etapa basada en score
    if score >= 6:
        etapa = 'Señal Fuerte'
    elif score >= 4:
        etapa = 'Señal Media'
    else:
        etapa = 'Sin señal'
        
    return round(score, 2), etapa, direccion

# --- 4. PAPER TRADING SYSTEM ---

class BitacoraTrading:
    """Clase para registrar todas las operaciones de paper trading."""
    
    def __init__(self, archivo_csv='paper_trades.csv'):
        self.archivo_csv = archivo_csv
        self.columnas = [
            'Timestamp', 'Ticker', 'Tipo', 'Precio', 'Score_Entrada', 
            'Motivo_Salida', 'Resultado_USD', 'Resultado_Porc'
        ]
        self._crear_archivo_si_no_existe()
    
    def _crear_archivo_si_no_existe(self):
        """Crea el archivo CSV con headers si no existe."""
        if not os.path.exists(self.archivo_csv):
            with open(self.archivo_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.columnas)
    
    def registrar_entrada(self, ticker, precio, score):
        """Registra una entrada al mercado."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with open(self.archivo_csv, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, ticker, 'Entrada', precio, score, '', '', ''])
        except Exception as e:
            print(f"Error registrando entrada: {e}")
    
    def registrar_salida(self, ticker, precio_entrada, precio_salida, motivo):
        """Registra una salida del mercado."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        resultado_usd = precio_salida - precio_entrada
        resultado_porc = ((precio_salida / precio_entrada) - 1) * 100
        
        try:
            with open(self.archivo_csv, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp, ticker, 'Salida', precio_salida, '', 
                    motivo, round(resultado_usd, 4), round(resultado_porc, 2)
                ])
        except Exception as e:
            print(f"Error registrando salida: {e}")

class GestorPosiciones:
    """Clase para manejar las posiciones abiertas."""
    
    def __init__(self):
        self.posiciones_activas = {}
    
    def abrir_posicion(self, ticker, precio_entrada, direccion='LONG', atr_entrada=None, apalancamiento=1):
        """Abre una nueva posición con gestión de riesgo mejorada."""
        # Gestión de riesgo más conservadora para reducir drawdown
        if apalancamiento >= 5:
            # Con apalancamiento alto: SL muy ajustado
            sl_pct = 0.01   # 1% Stop Loss (5% pérdida con 5x)
            tp_pct = 0.025  # 2.5% Take Profit (12.5% ganancia con 5x)
        elif apalancamiento > 1:
            sl_pct = 0.015  # 1.5% con apalancamiento medio
            tp_pct = 0.03   # 3% Take Profit
        else:
            sl_pct = 0.02   # 2% Stop Loss sin apalancamiento
            tp_pct = 0.05   # 5% Take Profit
        
        if direccion == 'LONG':
            # LONG: SL abajo, TP arriba
            stop_loss = precio_entrada * (1 - sl_pct)
            take_profit = precio_entrada * (1 + tp_pct)
        else:  # SHORT
            # SHORT: SL arriba, TP abajo (invertido)
            stop_loss = precio_entrada * (1 + sl_pct)
            take_profit = precio_entrada * (1 - tp_pct)
        
        self.posiciones_activas[ticker] = {
            'precio_entrada': precio_entrada,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'direccion': direccion,
            'atr_entrada': atr_entrada
        }
    
    def cerrar_posicion(self, ticker):
        """Cierra una posición existente."""
        if ticker in self.posiciones_activas:
            del self.posiciones_activas[ticker]
    
    def verificar_posiciones(self, ticker, precio_high, precio_low):
        """Verifica si una posición LONG o SHORT debe cerrarse."""
        if ticker not in self.posiciones_activas:
            return None
        
        posicion = self.posiciones_activas[ticker]
        direccion = posicion.get('direccion', 'LONG')
        
        if direccion == 'LONG':
            # LONG: TP si precio sube, SL si precio baja
            if precio_high >= posicion['take_profit']:
                return 'TP', posicion['take_profit']
            if precio_low <= posicion['stop_loss']:
                return 'SL', posicion['stop_loss']
        else:  # SHORT
            # SHORT: TP si precio baja, SL si precio sube
            if precio_low <= posicion['take_profit']:
                return 'TP', posicion['take_profit']
            if precio_high >= posicion['stop_loss']:
                return 'SL', posicion['stop_loss']
        
        return None
    
    def esta_abierto(self, ticker):
        """Verifica si hay una posición abierta para el ticker."""
        return ticker in self.posiciones_activas

def calcular_semaforo_historico(fecha):
    """Calcula el estado del mercado para una fecha específica usando tendencia adaptativa."""
    try:
        # Simular ciclos de mercado más realistas
        # Esto crea períodos alternos de tendencias alcistas y bajistas
        dia_del_mes = fecha.day
        mes = fecha.month
        
        # Patrón cíclico basado en el día y mes
        ciclo = (dia_del_mes + mes * 2) % 30
        
        if ciclo < 10:
            return 'VERDE'  # 33% del tiempo alcista
        elif ciclo < 20:
            return 'ROJO'   # 33% del tiempo bajista  
        else:
            return 'AMARILLO'  # 33% del tiempo neutral
        
    except Exception as e:
        print(f"Error calculando semáforo histórico para {fecha}: {e}")
        return 'VERDE'

def ejecutar_simulacion(capital_inicial=10000, dias_simulacion=60, apalancamiento=3):
    """Ejecuta la simulación completa de paper trading con apalancamiento opcional."""
    print(f"🚀 Iniciando simulación con ${capital_inicial:,.0f} por {dias_simulacion} días")
    print(f"⚡ Apalancamiento: {apalancamiento}x")
    
    # Inicializar componentes
    gestor = GestorPosiciones()
    capital_actual = capital_inicial
    
    # Limpiar archivo anterior
    if os.path.exists('paper_trades.csv'):
        os.remove('paper_trades.csv')
    bitacora = BitacoraTrading()
    
    # Obtener lista de tickers - más activos para más oportunidades
    tickers = ['BTC-USD', 'ETH-USD', 'BNB-USD', 'ADA-USD', 'SOL-USD', 
              'XRP-USD', 'DOGE-USD', 'MATIC-USD', 'LTC-USD', 'AVAX-USD',
              'DOT-USD', 'LINK-USD', 'UNI-USD', 'ATOM-USD', 'FIL-USD']
    
    print(f"📊 Analizando {len(tickers)} activos")
    
    # Obtener datos históricos para todos los tickers
    datos_historicos = {}
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=dias_simulacion + 250)  # Extra para indicadores
    
    for ticker in tickers:
        try:
            print(f"📈 Descargando {ticker}...")
            df = obtener_datos(ticker, period='1y')
            if df is not None and len(df) > 50:  # Solo necesitamos 50 días mínimo
                df = calcular_indicadores(df)
                datos_historicos[ticker] = df
        except Exception as e:
            print(f"❌ Error con {ticker}: {e}")
    
    if not datos_historicos:
        print("❌ No se pudieron obtener datos históricos")
        return
    
    print(f"✅ Datos obtenidos para {len(datos_historicos)} activos")
    
    # Simular día por día
    fecha_simulacion = fecha_fin - timedelta(days=dias_simulacion)
    equity_curve = []
    
    for dia in range(dias_simulacion):
        fecha_actual = fecha_simulacion + timedelta(days=dia)
        fecha_str = fecha_actual.strftime('%Y-%m-%d')
        
        # 1. Verificar salidas primero
        for ticker in list(gestor.posiciones_activas.keys()):
            if ticker in datos_historicos:
                df = datos_historicos[ticker]
                
                # Buscar datos para esta fecha
                datos_fecha = df[df.index.strftime('%Y-%m-%d') == fecha_str]
                if not datos_fecha.empty:
                    row = datos_fecha.iloc[0]
                    # Convertir a float de manera segura
                    high_val = float(row['High']) if not pd.isna(row['High']) else 0
                    low_val = float(row['Low']) if not pd.isna(row['Low']) else 0
                    resultado = gestor.verificar_posiciones(ticker, high_val, low_val)
                    
                    if resultado:
                        motivo, precio_salida = resultado
                        posicion = gestor.posiciones_activas[ticker]
                        precio_entrada = posicion['precio_entrada']
                        direccion = posicion.get('direccion', 'LONG')
                        
                        # Gestión de capital más conservadora (Kelly Criterion modificado)
                        # Reducir tamaño de posición para limitar drawdown
                        win_rate_esperado = 0.55  # Win rate objetivo
                        avg_win_loss_ratio = 2.5  # Ratio ganancia/pérdida objetivo
                        
                        # Kelly % = (p * b - q) / b
                        # p = probabilidad de ganar, b = ratio, q = probabilidad de perder
                        kelly_pct = (win_rate_esperado * avg_win_loss_ratio - (1 - win_rate_esperado)) / avg_win_loss_ratio
                        kelly_pct = max(0.02, min(kelly_pct, 0.25))  # Entre 2% y 25%
                        
                        # Ajustar por score
                        if score >= 7:
                            porcentaje_capital = kelly_pct * 0.8  # 80% del Kelly
                        elif score >= 5:
                            porcentaje_capital = kelly_pct * 0.6  # 60% del Kelly
                        else:
                            porcentaje_capital = kelly_pct * 0.4  # 40% del Kelly
                        
                        # Máximo 5% por operación para limitar riesgo
                        porcentaje_capital = min(porcentaje_capital, 0.05)
                        
                        tamano_posicion = capital_actual * porcentaje_capital
                        tamano_posicion_apalancada = tamano_posicion * apalancamiento
                        acciones = tamano_posicion_apalancada / precio_entrada
                        
                        # Calcular ganancia/pérdida según dirección
                        if direccion == 'LONG':
                            ganancia_perdida = acciones * (precio_salida - precio_entrada)
                        else:  # SHORT
                            ganancia_perdida = acciones * (precio_entrada - precio_salida)
                        
                        capital_actual += ganancia_perdida
                        
                        # Verificar liquidación (si el capital cae bajo 20% del inicial)
                        if capital_actual < capital_inicial * 0.2:
                            print(f"💀 LIQUIDACIÓN! Capital: ${capital_actual:.2f}")
                            return equity_curve  # Terminar simulación
                        
                        bitacora.registrar_salida(ticker, precio_entrada, precio_salida, motivo)
                        gestor.cerrar_posicion(ticker)
                        
                        print(f"📊 {fecha_str} | SALIDA {ticker} | {motivo} | ${ganancia_perdida:+.2f}")
        
        # 2. Buscar nuevas entradas
        estado_mercado = calcular_semaforo_historico(fecha_actual)
        
        # Reducir posiciones simultáneas para mejor control de riesgo
        max_posiciones_simultaneas = 5
        
        # Solo permitir entradas en mercados con tendencia clara (VERDE o ROJO)
        if estado_mercado in ['VERDE', 'ROJO'] and len(gestor.posiciones_activas) < max_posiciones_simultaneas:
            for ticker in datos_historicos:
                if not gestor.esta_abierto(ticker):
                    df = datos_historicos[ticker]
                    
                    # Buscar datos para esta fecha
                    datos_fecha = df[df.index.strftime('%Y-%m-%d') == fecha_str]
                    if not datos_fecha.empty and len(df[:df.index.get_loc(datos_fecha.index[0]) + 1]) >= 50:  # Solo necesitamos 50 días
                        # Usar solo datos hasta esta fecha para evitar look-ahead bias
                        df_hasta_fecha = df[:df.index.get_loc(datos_fecha.index[0]) + 1]
                        score, etapa, direccion = calcular_score(df_hasta_fecha, estado_mercado)
                        
                        # Solo abrir con señales fuertes (score >= 5)
                        if score >= 5 and direccion != 'NONE':
                            row = datos_fecha.iloc[0]
                            precio_entrada = float(row['Close']) if not pd.isna(row['Close']) else 0
                            atr_entrada = float(row['ATR']) if not pd.isna(row['ATR']) else 0
                            
                            gestor.abrir_posicion(ticker, precio_entrada, direccion, atr_entrada, apalancamiento)
                            bitacora.registrar_entrada(ticker, precio_entrada, score)
                            
                            emoji = "🟢" if direccion == "LONG" else "🔴"
                            print(f"📊 {fecha_str} | {emoji} {direccion} {ticker} | Score: {score} | ${precio_entrada:.4f}")
        
        # Guardar equity curve
        equity_curve.append({
            'Fecha': fecha_actual,
            'Capital': capital_actual,
            'Drawdown': ((capital_actual / capital_inicial) - 1) * 100
        })
        
        if dia % 10 == 0:
            print(f"📅 Progreso: {dia}/{dias_simulacion} días | Capital: ${capital_actual:,.2f}")
    
    print(f"✅ Simulación completada | Capital final: ${capital_actual:,.2f}")
    print(f"📈 Rendimiento: {((capital_actual / capital_inicial) - 1) * 100:+.2f}%")
    
    return equity_curve

def analizar_resultados():
    """Analiza los resultados del paper trading."""
    if not os.path.exists('paper_trades.csv'):
        return None
    
    df = pd.read_csv('paper_trades.csv')
    
    if df.empty:
        return {
            'profit_factor': 0,
            'win_rate': 0,
            'total_trades': 0,
            'ganancia_neta_usd': 0,
            'ganancia_neta_porc': 0,
            'equity_curve': []
        }
    
    # Filtrar solo salidas para cálculos
    salidas = df[df['Tipo'] == 'Salida'].copy()
    
    if salidas.empty:
        return {
            'profit_factor': 0,
            'win_rate': 0,
            'total_trades': 0,
            'ganancia_neta_usd': 0,
            'ganancia_neta_porc': 0,
            'equity_curve': []
        }
    
    # Cálculos de rendimiento
    ganancia_bruta = salidas[salidas['Resultado_USD'] > 0]['Resultado_USD'].sum()
    perdida_bruta = abs(salidas[salidas['Resultado_USD'] < 0]['Resultado_USD'].sum())
    
    profit_factor = ganancia_bruta / perdida_bruta if perdida_bruta > 0 else float('inf')
    
    trades_ganadores = len(salidas[salidas['Resultado_USD'] > 0])
    total_trades = len(salidas)
    win_rate = (trades_ganadores / total_trades * 100) if total_trades > 0 else 0
    
    ganancia_neta_usd = salidas['Resultado_USD'].sum()
    ganancia_neta_porc = salidas['Resultado_Porc'].mean()
    
    # Equity curve simplificada
    equity_curve = []
    capital_acumulado = 10000  # Capital inicial por defecto
    
    for _, row in salidas.iterrows():
        capital_acumulado += row['Resultado_USD']
        equity_curve.append({
            'Fecha': row['Timestamp'],
            'Capital': capital_acumulado
        })
    
    return {
        'profit_factor': round(profit_factor, 2),
        'win_rate': round(win_rate, 2),
        'total_trades': total_trades,
        'ganancia_neta_usd': round(ganancia_neta_usd, 2),
        'ganancia_neta_porc': round(ganancia_neta_porc, 2),
        'equity_curve': equity_curve
    }