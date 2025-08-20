#!/usr/bin/env python3
"""
===========================================
FASTAPI SERVER - SIGNAL HAVEN DESK
===========================================

Backend optimizado para tu UI React con WebSockets
para actualización en tiempo real.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from pydantic import BaseModel
from enum import Enum

# Importar sistemas de trading
from philosophers import PhilosophicalTradingSystem
from philosophers_extended import register_extended_philosophers
from binance_integration import BinanceConnector, MultiProjectManager
# import yfinance as yf  # Reemplazado por Binance API

# ===========================================
# MODELOS DE DATOS
# ===========================================

class BotStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"

class TradingSignal(BaseModel):
    timestamp: str
    philosopher: str
    symbol: str
    action: str  # BUY, SELL, HOLD
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    reasoning: List[str]

class Position(BaseModel):
    id: str
    symbol: str
    type: str  # LONG, SHORT
    entry_price: float
    current_price: float
    quantity: float
    pnl: float
    pnl_percentage: float
    stop_loss: float
    take_profit: float
    status: str  # OPEN, CLOSED

class PerformanceMetric(BaseModel):
    total_pnl: float
    daily_pnl: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    sharpe_ratio: float
    max_drawdown: float
    current_balance: float

class Alert(BaseModel):
    timestamp: str
    type: str  # INFO, WARNING, ERROR, SUCCESS
    message: str
    details: Optional[Dict] = None

class BotConfig(BaseModel):
    max_positions: int = 3
    risk_per_trade: float = 0.01
    stop_loss_percentage: float = 0.03
    take_profit_percentage: float = 0.05
    trade_amount_usd: float = 100
    symbols: List[str] = ["DOGEUSDT", "ADAUSDT", "DOTUSDT", "SOLUSDT", "LINKUSDT"]  # Símbolos de menor precio para capital bajo
    philosophers: List[str] = ["SOCRATES", "ARISTOTELES", "PLATON"]

# ===========================================
# TRADING MANAGER (SINGLETON)
# ===========================================

class TradingManager:
    """Gestor principal del sistema de trading"""
    
    def __init__(self):
        self.bot_status = BotStatus.STOPPED
        self.config = BotConfig()
        self.philosophy_system = register_extended_philosophers()
        self.binance = BinanceConnector(testnet=True)
        self.project_manager = MultiProjectManager(self.binance)
        
        # Estado
        self.positions: List[Position] = []
        self.alerts: List[Alert] = []
        self.recent_signals: List[TradingSignal] = []
        self.performance = PerformanceMetric(
            total_pnl=0, daily_pnl=0, win_rate=0,
            total_trades=0, winning_trades=0, losing_trades=0,
            avg_win=0, avg_loss=0, sharpe_ratio=0,
            max_drawdown=0, current_balance=1000
        )
        
        # WebSocket clients
        self.active_connections: List[WebSocket] = []
        
        # Trading task
        self.trading_task = None
        
    async def connect_websocket(self, websocket: WebSocket):
        """Conecta un cliente WebSocket"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Enviar estado inicial
        await self.send_initial_state(websocket)
    
    def disconnect_websocket(self, websocket: WebSocket):
        """Desconecta un cliente WebSocket"""
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Envía mensaje a todos los clientes conectados"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Cliente desconectado
                self.active_connections.remove(connection)
    
    async def send_initial_state(self, websocket: WebSocket):
        """Envía el estado inicial al conectarse"""
        await websocket.send_json({
            "type": "initial_state",
            "data": {
                "bot_status": self.bot_status,
                "positions": [p.dict() for p in self.positions],
                "performance": self.performance.dict(),
                "config": self.config.dict(),
                "alerts": [a.dict() for a in self.alerts[-10:]]  # Últimas 10 alertas
            }
        })
    
    async def start_bot(self):
        """Inicia el bot de trading"""
        if self.bot_status == BotStatus.RUNNING:
            return
        
        self.bot_status = BotStatus.RUNNING
        self.trading_task = asyncio.create_task(self.trading_loop())
        
        await self.add_alert("SUCCESS", "Bot iniciado exitosamente")
        await self.broadcast({
            "type": "bot_status",
            "data": {"status": self.bot_status}
        })
    
    async def stop_bot(self):
        """Detiene el bot de trading"""
        if self.bot_status == BotStatus.STOPPED:
            return
        
        self.bot_status = BotStatus.STOPPED
        
        if self.trading_task:
            self.trading_task.cancel()
            self.trading_task = None
        
        await self.add_alert("INFO", "Bot detenido")
        await self.broadcast({
            "type": "bot_status",
            "data": {"status": self.bot_status}
        })
    
    async def trading_loop(self):
        """Loop principal de trading"""
        while self.bot_status == BotStatus.RUNNING:
            try:
                # 1. Obtener datos de mercado
                market_data = await self.fetch_market_data()
                
                # 2. Análisis filosófico
                signals = await self.analyze_with_philosophers(market_data)
                
                # 3. Ejecutar señales con consenso
                if signals:
                    await self.execute_signals(signals)
                
                # 4. Actualizar posiciones
                await self.update_positions()
                
                # 5. Enviar actualizaciones
                await self.send_updates()
                
                # Esperar próximo ciclo (1 minuto en producción, 10 segundos en demo)
                await asyncio.sleep(10)
                
            except Exception as e:
                await self.add_alert("ERROR", f"Error en trading loop: {str(e)}")
                await asyncio.sleep(60)
    
    async def fetch_market_data(self) -> Dict:
        """Obtiene datos de mercado desde Binance"""
        market_data = {}
        
        for symbol in self.config.symbols:
            try:
                # Usar Binance Connector que ya tenemos
                df = self.binance.get_historical_data(symbol, '1m', 100)
                
                if df is not None and not df.empty:
                    # Los datos de Binance ya vienen normalizados
                    market_data[symbol] = df
                    print(f"✅ Datos obtenidos para {symbol}: {len(df)} velas")
                else:
                    print(f"⚠️ Sin datos para {symbol}")
                    
            except Exception as e:
                print(f"❌ Error obteniendo datos de {symbol}: {e}")
        
        return market_data
    
    async def analyze_with_philosophers(self, market_data: Dict) -> List[TradingSignal]:
        """Analiza el mercado con los filósofos configurados"""
        all_signals = []
        
        for symbol, df in market_data.items():
            if df is not None and not df.empty:
                # Análisis con cada filósofo
                signals = self.philosophy_system.analyze_with_philosophers(
                    df, symbol, self.config.philosophers
                )
                
                # Buscar consenso
                if len(signals) >= 2:  # Al menos 2 filósofos de acuerdo
                    consensus = self.philosophy_system.get_consensus(signals)
                    
                    if consensus:
                        trading_signal = TradingSignal(
                            timestamp=datetime.now().isoformat(),
                            philosopher=", ".join(consensus['philosophers_agreed']),
                            symbol=symbol,
                            action=consensus['action'],
                            entry_price=consensus['entry_price'],
                            stop_loss=consensus['stop_loss'],
                            take_profit=consensus['take_profit'],
                            confidence=consensus['confidence'],
                            reasoning=[f"{s.philosopher}: {s.reasoning[0]}" for s in consensus['signals'][:2]]
                        )
                        
                        all_signals.append(trading_signal)
                        self.recent_signals.append(trading_signal)
                        
                        # Mantener solo las últimas 50 señales
                        if len(self.recent_signals) > 50:
                            self.recent_signals = self.recent_signals[-50:]
                        
                        await self.add_alert(
                            "INFO",
                            f"Señal detectada: {consensus['action']} {symbol}",
                            {"confidence": consensus['confidence']}
                        )
        
        return all_signals
    
    async def execute_signals(self, signals: List[TradingSignal]):
        """Ejecuta las señales de trading"""
        for signal in signals:
            # Verificar límites
            if len(self.positions) >= self.config.max_positions:
                await self.add_alert("WARNING", "Máximo de posiciones alcanzado")
                continue
            
            # Crear posición
            position = Position(
                id=f"POS_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                symbol=signal.symbol,
                type="LONG" if signal.action == "BUY" else "SHORT",
                entry_price=signal.entry_price,
                current_price=signal.entry_price,
                quantity=self.config.trade_amount_usd / signal.entry_price,
                pnl=0,
                pnl_percentage=0,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                status="OPEN"
            )
            
            self.positions.append(position)
            self.performance.total_trades += 1
            
            await self.add_alert(
                "SUCCESS",
                f"Posición abierta: {signal.action} {signal.symbol}",
                {"price": signal.entry_price, "confidence": signal.confidence}
            )
    
    async def update_positions(self):
        """Actualiza el estado de las posiciones"""
        for position in self.positions:
            if position.status == "OPEN":
                # Obtener precio actual desde Binance
                try:
                    # Convertir símbolo al formato de Binance
                    binance_symbol = position.symbol.replace("/", "")
                    if not binance_symbol.endswith("USDT"):
                        binance_symbol = binance_symbol + "USDT"
                    
                    # Obtener precio actual desde Binance
                    current_price = self.binance.get_current_price(binance_symbol)
                    if current_price:
                        position.current_price = current_price
                        
                        # Calcular P&L
                        if position.type == "LONG":
                            position.pnl = (current_price - position.entry_price) * position.quantity
                            position.pnl_percentage = ((current_price / position.entry_price) - 1) * 100
                            
                            # Check stop loss y take profit
                            if current_price <= position.stop_loss:
                                await self.close_position(position, "STOP_LOSS")
                            elif current_price >= position.take_profit:
                                await self.close_position(position, "TAKE_PROFIT")
                    
                except Exception as e:
                    print(f"Error actualizando posición {position.id}: {e}")
    
    async def close_position(self, position: Position, reason: str):
        """Cierra una posición"""
        position.status = "CLOSED"
        
        if position.pnl > 0:
            self.performance.winning_trades += 1
        else:
            self.performance.losing_trades += 1
        
        self.performance.daily_pnl += position.pnl
        self.performance.total_pnl += position.pnl
        
        # Actualizar win rate
        if self.performance.total_trades > 0:
            self.performance.win_rate = self.performance.winning_trades / self.performance.total_trades
        
        await self.add_alert(
            "INFO" if position.pnl > 0 else "WARNING",
            f"Posición cerrada ({reason}): {position.symbol}",
            {"pnl": position.pnl, "pnl_percentage": position.pnl_percentage}
        )
        
        # Remover de posiciones activas
        self.positions = [p for p in self.positions if p.id != position.id]
    
    async def send_updates(self):
        """Envía actualizaciones a los clientes"""
        # Preparar datos para gráfico
        chart_data = await self.prepare_chart_data()
        
        await self.broadcast({
            "type": "update",
            "data": {
                "positions": [p.dict() for p in self.positions if p.status == "OPEN"],
                "performance": self.performance.dict(),
                "chart_data": chart_data,
                "signals": [s.dict() for s in self.recent_signals[-10:]],  # Últimas 10 señales
                "bot_status": self.bot_status
            }
        })
    
    async def prepare_chart_data(self) -> List[Dict]:
        """Prepara datos para el gráfico de trading"""
        chart_data = []
        
        # Obtener datos de BTC para el gráfico principal
        try:
            df = self.binance.get_historical_data("BTCUSDT", "5m", 50)
            
            if df is not None and not df.empty:
                for index, row in df.iterrows():
                    chart_data.append({
                        "time": index.isoformat(),
                        "open": row['open'],
                        "high": row['high'],
                        "low": row['low'],
                        "close": row['close'],
                        "volume": row['volume']
                    })
        except Exception as e:
            print(f"Error preparando datos del gráfico: {e}")
        
        return chart_data
    
    async def add_alert(self, alert_type: str, message: str, details: Optional[Dict] = None):
        """Añade una alerta al sistema"""
        alert = Alert(
            timestamp=datetime.now().isoformat(),
            type=alert_type,
            message=message,
            details=details
        )
        
        self.alerts.append(alert)
        
        # Mantener solo las últimas 100 alertas
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        # Enviar alerta a clientes
        await self.broadcast({
            "type": "alert",
            "data": alert.dict()
        })
    
    async def update_config(self, new_config: BotConfig):
        """Actualiza la configuración del bot"""
        self.config = new_config
        
        await self.add_alert("INFO", "Configuración actualizada")
        
        # Si el bot está corriendo, reiniciar con nueva config
        if self.bot_status == BotStatus.RUNNING:
            await self.stop_bot()
            await asyncio.sleep(1)
            await self.start_bot()

# ===========================================
# INSTANCIA GLOBAL
# ===========================================

trading_manager = TradingManager()

# ===========================================
# LIFESPAN EVENTS
# ===========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación"""
    # Startup
    print("🚀 Starting Signal Haven Desk API...")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    if trading_manager.trading_task:
        trading_manager.trading_task.cancel()

# ===========================================
# FASTAPI APP
# ===========================================

app = FastAPI(
    title="Signal Haven Desk API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS para permitir conexiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================================
# REST ENDPOINTS
# ===========================================

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "bot_status": trading_manager.bot_status,
        "positions": len(trading_manager.positions),
        "version": "1.0.0"
    }

@app.get("/api/status")
async def get_status():
    """Obtiene el estado actual del sistema"""
    return {
        "bot_status": trading_manager.bot_status,
        "positions": [p.dict() for p in trading_manager.positions if p.status == "OPEN"],
        "performance": trading_manager.performance.dict(),
        "config": trading_manager.config.dict()
    }

@app.post("/api/bot/start")
async def start_bot():
    """Inicia el bot de trading"""
    await trading_manager.start_bot()
    return {"status": "started"}

@app.post("/api/bot/stop")
async def stop_bot():
    """Detiene el bot de trading"""
    await trading_manager.stop_bot()
    return {"status": "stopped"}

@app.get("/api/config")
async def get_config():
    """Obtiene la configuración actual"""
    return trading_manager.config.dict()

@app.post("/api/config")
async def update_config(config: BotConfig):
    """Actualiza la configuración del bot"""
    await trading_manager.update_config(config)
    return {"status": "updated", "config": config.dict()}

@app.get("/api/positions")
async def get_positions():
    """Obtiene las posiciones activas"""
    return [p.dict() for p in trading_manager.positions if p.status == "OPEN"]

@app.get("/api/performance")
async def get_performance():
    """Obtiene métricas de performance"""
    return trading_manager.performance.dict()

@app.get("/api/system-status")
async def get_system_status():
    """Obtiene estado detallado del sistema"""
    return {
        "service_status": "online",
        "bot_status": trading_manager.bot_status,
        "active_pairs": trading_manager.config.symbols,
        "active_philosophers": trading_manager.config.philosophers,
        "websocket_clients": len(trading_manager.active_connections),
        "active_positions": len([p for p in trading_manager.positions if p.status == "OPEN"]),
        "total_signals_generated": len(trading_manager.recent_signals),
        "last_signal": trading_manager.recent_signals[-1].dict() if trading_manager.recent_signals else None,
        "alerts_count": len(trading_manager.alerts),
        "performance_summary": {
            "balance": trading_manager.performance.current_balance,
            "total_pnl": trading_manager.performance.total_pnl,
            "win_rate": trading_manager.performance.win_rate,
            "total_trades": trading_manager.performance.total_trades
        }
    }

@app.get("/api/alerts")
async def get_alerts(limit: int = 50):
    """Obtiene las últimas alertas"""
    return [a.dict() for a in trading_manager.alerts[-limit:]]

@app.get("/api/recent-signals")
async def get_recent_signals(limit: int = 10):
    """Obtiene las señales recientes"""
    return [s.dict() for s in trading_manager.recent_signals[-limit:]]

@app.get("/api/symbol/{symbol}/data")
async def get_symbol_data(symbol: str):
    """Obtiene datos completos para un símbolo específico"""
    try:
        # Obtener precio actual desde Binance
        current_price = trading_manager.binance.get_current_price(symbol)
        
        # Obtener datos históricos recientes
        df = trading_manager.binance.get_historical_data(symbol, '1m', 100)
        
        if df is not None and not df.empty:
            # Calcular cambios de precio
            latest_close = df['close'].iloc[-1]
            prev_close = df['close'].iloc[-24] if len(df) > 24 else df['close'].iloc[0]
            price_change_24h = latest_close - prev_close
            price_change_percent_24h = ((latest_close / prev_close) - 1) * 100
            volume_24h = df['volume'].tail(24).sum() if len(df) > 24 else df['volume'].sum()
            
            # Analizar con filósofos para obtener señales reales
            signals = trading_manager.philosophy_system.analyze_with_philosophers(
                df, symbol, trading_manager.config.philosophers
            )
            
            # Formatear señales para el frontend
            philosopher_signals = []
            for signal in signals:
                # Calcular % de cuenta sugerido basado en confianza y riesgo
                base_risk = 1.0  # 1% riesgo base
                confidence_factor = signal.confidence
                
                # Ajustar riesgo según confianza: más confianza = más % de cuenta
                if confidence_factor >= 0.8:
                    account_percentage = base_risk * 3  # 3% para alta confianza
                elif confidence_factor >= 0.7:
                    account_percentage = base_risk * 2  # 2% para confianza media-alta
                elif confidence_factor >= 0.6:
                    account_percentage = base_risk * 1.5  # 1.5% para confianza media
                else:
                    account_percentage = base_risk  # 1% para baja confianza
                
                # Calcular riesgo/recompensa
                risk_amount = abs(signal.entry_price - signal.stop_loss)
                reward_amount = abs(signal.take_profit - signal.entry_price)
                risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 1
                
                philosopher_signals.append({
                    "name": signal.philosopher,
                    "action": signal.action,
                    "confidence": signal.confidence * 100,  # Convertir a porcentaje
                    "reasoning": signal.reasoning[0] if signal.reasoning else "",
                    "entry_price": signal.entry_price,
                    "target_price": signal.take_profit,
                    "stop_loss": signal.stop_loss,
                    "account_percentage": account_percentage,
                    "risk_reward_ratio": round(risk_reward_ratio, 2),
                    "timestamp": datetime.now().isoformat()
                })
            
            return {
                "symbol": symbol,
                "current_price": current_price or latest_close,
                "price_change_24h": price_change_24h,
                "price_change_percent_24h": price_change_percent_24h,
                "volume_24h": volume_24h,
                "philosopher_signals": philosopher_signals,
                "positions": [p.dict() for p in trading_manager.positions if p.symbol == symbol],
                "last_update": datetime.now().isoformat()
            }
        else:
            return {
                "symbol": symbol,
                "error": "No data available",
                "current_price": 0,
                "philosopher_signals": []
            }
    except Exception as e:
        print(f"Error obteniendo datos para {symbol}: {e}")
        return {
            "symbol": symbol,
            "error": str(e),
            "current_price": 0,
            "philosopher_signals": []
        }

@app.get("/api/market/{symbol}/chart")
async def get_chart_data(symbol: str, interval: str = "1m", limit: int = 100):
    """Obtiene datos históricos de gráfica para un símbolo"""
    try:
        df = trading_manager.binance.get_historical_data(symbol, interval, limit)
        
        if df is None or df.empty:
            return []
        
        chart_data = []
        for index, row in df.iterrows():
            chart_data.append({
                "time": index.isoformat(),
                "open": row['open'],
                "high": row['high'],
                "low": row['low'],
                "close": row['close'],
                "volume": row['volume']
            })
        
        return chart_data
    except Exception as e:
        print(f"Error obteniendo datos de gráfica para {symbol}: {e}")
        return []

@app.get("/api/market/{symbol}/indicators")
async def get_market_indicators(symbol: str, interval: str = "15m"):
    """Calcula indicadores de mercado reales para un símbolo"""
    try:
        # Obtener datos históricos (necesitamos más datos para calcular indicadores)
        df = trading_manager.binance.get_historical_data(symbol, interval, 200)
        
        if df is None or df.empty:
            return {"error": "No data available"}
        
        # Calcular RSI
        def calculate_rsi(df, period=14):
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]
        
        # Calcular MACD
        def calculate_macd(df):
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            histogram = macd - signal
            return {
                "value": float(macd.iloc[-1]),
                "signal": float(signal.iloc[-1]),
                "histogram": float(histogram.iloc[-1])
            }
        
        # Calcular volatilidad (desviación estándar del retorno)
        returns = df['close'].pct_change()
        volatility = returns.std() * 100  # Convertir a porcentaje
        
        # Calcular momentum
        momentum = ((df['close'].iloc[-1] / df['close'].iloc[-20]) - 1) * 100
        
        # Calcular volumen promedio
        volume_avg = df['volume'].rolling(window=20).mean().iloc[-1]
        volume_current = df['volume'].iloc[-1]
        volume_ratio = volume_current / volume_avg if volume_avg > 0 else 1
        
        # Identificar soportes y resistencias simples
        recent_high = df['high'].tail(20).max()
        recent_low = df['low'].tail(20).min()
        current_price = df['close'].iloc[-1]
        
        # Determinar fase del mercado
        rsi_value = calculate_rsi(df)
        macd_data = calculate_macd(df)
        
        if rsi_value > 70:
            market_phase = "OVERBOUGHT"
        elif rsi_value < 30:
            market_phase = "OVERSOLD"
        elif abs(momentum) < 2:
            market_phase = "CONSOLIDATION"
        elif momentum > 5:
            market_phase = "BULLISH_TREND"
        elif momentum < -5:
            market_phase = "BEARISH_TREND"
        else:
            market_phase = "NEUTRAL"
        
        # Determinar condición del mercado
        if rsi_value > 70 and volume_ratio > 1.5:
            market_condition = "EXPLOSIVE"
        elif rsi_value > 60 and momentum > 5:
            market_condition = "BULLISH"
        elif rsi_value < 40 and momentum < -5:
            market_condition = "BEARISH"
        elif volume_ratio < 0.5:
            market_condition = "ACCUMULATION"
        elif volume_ratio > 2:
            market_condition = "DISTRIBUTION"
        else:
            market_condition = "NEUTRAL"
        
        return {
            "rsi": float(rsi_value),
            "macd": macd_data,
            "volume": {
                "current": float(volume_current),
                "average": float(volume_avg),
                "ratio": float(volume_ratio)
            },
            "volatility": float(volatility),
            "momentum": float(momentum),
            "trend_strength": abs(float(momentum)),
            "support_resistance": {
                "support": float(recent_low),
                "resistance": float(recent_high),
                "current_price": float(current_price)
            },
            "market_phase": market_phase,
            "market_condition": market_condition,
            "volume_profile": "HIGH" if volume_ratio > 1.5 else "NORMAL" if volume_ratio > 0.5 else "LOW"
        }
    except Exception as e:
        print(f"Error calculando indicadores para {symbol}: {e}")
        return {"error": str(e)}

@app.delete("/api/position/{position_id}")
async def close_position_manually(position_id: str):
    """Cierra una posición manualmente"""
    position = next((p for p in trading_manager.positions if p.id == position_id), None)
    
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    await trading_manager.close_position(position, "MANUAL")
    return {"status": "closed", "pnl": position.pnl}

# ===========================================
# WEBSOCKET ENDPOINT
# ===========================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para actualizaciones en tiempo real"""
    await trading_manager.connect_websocket(websocket)
    
    try:
        while True:
            # Mantener conexión viva y recibir comandos
            data = await websocket.receive_json()
            
            # Procesar comandos desde el cliente
            if data.get("command") == "start_bot":
                await trading_manager.start_bot()
            elif data.get("command") == "stop_bot":
                await trading_manager.stop_bot()
            elif data.get("command") == "update_config":
                config = BotConfig(**data.get("config", {}))
                await trading_manager.update_config(config)
                
    except WebSocketDisconnect:
        trading_manager.disconnect_websocket(websocket)
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        trading_manager.disconnect_websocket(websocket)

# ===========================================
# MAIN
# ===========================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔═══════════════════════════════════════╗
    ║   SIGNAL HAVEN DESK - BACKEND API    ║
    ╠═══════════════════════════════════════╣
    ║   Philosophers: 10 Active             ║
    ║   WebSocket: Enabled                  ║
    ║   CORS: Configured for Vite          ║
    ║                                       ║
    ║   http://localhost:8000               ║
    ║   ws://localhost:8000/ws              ║
    ╚═══════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )