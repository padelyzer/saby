"""
Sistema de Base de Datos para Trading Bot
Gestiona la persistencia de señales y posiciones
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

class TradingDatabase:
    def __init__(self, db_path: str = "trading_bot.db"):
        """Inicializa la conexión a la base de datos"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Crea las tablas si no existen"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de posiciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                type TEXT NOT NULL,
                entry_price REAL NOT NULL,
                current_price REAL,
                quantity REAL NOT NULL,
                stop_loss REAL,
                take_profit REAL,
                pnl REAL DEFAULT 0,
                pnl_percentage REAL DEFAULT 0,
                status TEXT DEFAULT 'OPEN',
                open_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                close_time TIMESTAMP,
                strategy TEXT,
                created_by TEXT DEFAULT 'system'
            )
        """)
        
        # Tabla de señales
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                confidence REAL NOT NULL,
                entry_price REAL,
                stop_loss REAL,
                take_profit REAL,
                philosopher TEXT,
                reasoning TEXT,
                market_trend TEXT,
                rsi REAL,
                volume_ratio REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                executed BOOLEAN DEFAULT 0
            )
        """)
        
        # Tabla de métricas de performance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                date DATE DEFAULT CURRENT_DATE,
                total_pnl REAL DEFAULT 0,
                daily_pnl REAL DEFAULT 0,
                win_rate REAL DEFAULT 0,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                open_positions INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de alertas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                message TEXT NOT NULL,
                data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    # === POSICIONES ===
    
    def save_position(self, position: Dict) -> bool:
        """Guarda una nueva posición"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO positions 
                (id, user_id, symbol, type, entry_price, current_price, quantity, 
                 stop_loss, take_profit, pnl, pnl_percentage, status, strategy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                position['id'],
                position['user_id'],
                position['symbol'],
                position['type'],
                position['entry_price'],
                position.get('current_price', position['entry_price']),
                position['quantity'],
                position.get('stop_loss'),
                position.get('take_profit'),
                position.get('pnl', 0),
                position.get('pnl_percentage', 0),
                position.get('status', 'OPEN'),
                position.get('strategy', 'Manual')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving position: {e}")
            return False
    
    def get_open_positions(self, user_id: str = None) -> List[Dict]:
        """Obtiene las posiciones abiertas (opcionalmente filtradas por usuario)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute("""
                SELECT * FROM positions 
                WHERE status = 'OPEN' AND user_id = ?
                ORDER BY open_time DESC
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT * FROM positions 
                WHERE status = 'OPEN'
                ORDER BY open_time DESC
            """)
        
        columns = [col[0] for col in cursor.description]
        positions = []
        for row in cursor.fetchall():
            positions.append(dict(zip(columns, row)))
        
        conn.close()
        return positions
    
    def update_position(self, position_id: str, updates: Dict) -> bool:
        """Actualiza una posición existente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Construir la consulta dinámicamente
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [position_id]
            
            cursor.execute(f"""
                UPDATE positions 
                SET {set_clause}
                WHERE id = ?
            """, values)
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating position: {e}")
            return False
    
    def close_position(self, position_id: str, pnl: float, pnl_percentage: float) -> bool:
        """Cierra una posición"""
        return self.update_position(position_id, {
            'status': 'CLOSED',
            'pnl': pnl,
            'pnl_percentage': pnl_percentage,
            'close_time': datetime.now().isoformat()
        })
    
    # === SEÑALES ===
    
    def save_signal(self, signal: Dict) -> bool:
        """Guarda una nueva señal"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO signals 
                (id, user_id, symbol, action, confidence, entry_price, stop_loss, 
                 take_profit, philosopher, reasoning, market_trend, rsi, volume_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal['id'],
                signal['user_id'],
                signal['symbol'],
                signal['action'],
                signal['confidence'],
                signal.get('entry_price'),
                signal.get('stop_loss'),
                signal.get('take_profit'),
                signal.get('philosopher', 'System'),
                signal.get('reasoning', ''),
                signal.get('market_trend'),
                signal.get('rsi'),
                signal.get('volume_ratio')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving signal: {e}")
            return False
    
    def get_recent_signals(self, limit: int = 20, user_id: str = None) -> List[Dict]:
        """Obtiene las señales más recientes (opcionalmente filtradas por usuario)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute("""
                SELECT * FROM signals 
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM signals 
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
        
        columns = [col[0] for col in cursor.description]
        signals = []
        for row in cursor.fetchall():
            signals.append(dict(zip(columns, row)))
        
        conn.close()
        return signals
    
    def mark_signal_executed(self, signal_id: str) -> bool:
        """Marca una señal como ejecutada"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE signals 
                SET executed = 1
                WHERE id = ?
            """, (signal_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error marking signal as executed: {e}")
            return False
    
    # === PERFORMANCE ===
    
    def save_performance_metrics(self, metrics: Dict) -> bool:
        """Guarda métricas de performance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO performance 
                (total_pnl, daily_pnl, win_rate, total_trades, 
                 winning_trades, losing_trades, open_positions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.get('total_pnl', 0),
                metrics.get('daily_pnl', 0),
                metrics.get('win_rate', 0),
                metrics.get('total_trades', 0),
                metrics.get('winning_trades', 0),
                metrics.get('losing_trades', 0),
                metrics.get('open_positions', 0)
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving performance metrics: {e}")
            return False
    
    def get_latest_performance(self) -> Optional[Dict]:
        """Obtiene las métricas de performance más recientes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM performance 
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        if row:
            columns = [col[0] for col in cursor.description]
            performance = dict(zip(columns, row))
        else:
            performance = None
        
        conn.close()
        return performance
    
    # === ALERTAS ===
    
    def save_alert(self, alert_type: str, message: str, data: Dict = None) -> bool:
        """Guarda una alerta"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO alerts (type, message, data)
                VALUES (?, ?, ?)
            """, (
                alert_type,
                message,
                json.dumps(data) if data else None
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving alert: {e}")
            return False
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Obtiene las alertas más recientes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM alerts 
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        columns = [col[0] for col in cursor.description]
        alerts = []
        for row in cursor.fetchall():
            alert = dict(zip(columns, row))
            if alert['data']:
                alert['data'] = json.loads(alert['data'])
            alerts.append(alert)
        
        conn.close()
        return alerts
    
    # === ESTADÍSTICAS ===
    
    def get_statistics(self) -> Dict:
        """Obtiene estadísticas generales del sistema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total de posiciones
        cursor.execute("SELECT COUNT(*) FROM positions")
        stats['total_positions'] = cursor.fetchone()[0]
        
        # Posiciones abiertas
        cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'OPEN'")
        stats['open_positions'] = cursor.fetchone()[0]
        
        # Total de señales
        cursor.execute("SELECT COUNT(*) FROM signals")
        stats['total_signals'] = cursor.fetchone()[0]
        
        # Señales ejecutadas
        cursor.execute("SELECT COUNT(*) FROM signals WHERE executed = 1")
        stats['executed_signals'] = cursor.fetchone()[0]
        
        # PnL total
        cursor.execute("SELECT SUM(pnl) FROM positions WHERE status = 'CLOSED'")
        result = cursor.fetchone()[0]
        stats['total_pnl'] = result if result else 0
        
        conn.close()
        return stats

# Instancia global de la base de datos
db = TradingDatabase()