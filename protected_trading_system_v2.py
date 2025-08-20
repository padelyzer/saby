#!/usr/bin/env python3
"""
Sistema de Trading Protegido V2 con Datos Segregados por Usuario
Cada usuario tiene su propio portafolio y configuración
"""

from auth_system import auth, require_login
from user_data_manager import user_data, read_user_json, write_user_json
from trading_system_v4 import AdaptiveTradingSystem
import sys
import json
from datetime import datetime


class ProtectedTradingSystemV2:
    """Sistema de trading con autenticación y datos segregados por usuario"""
    
    def __init__(self):
        self.trading_system = AdaptiveTradingSystem()
        
    def _log_access(self, action, details=None):
        """Registra accesos al sistema en el log del usuario"""
        # Obtener el log actual del usuario
        log = read_user_json('trading_access_log.json') or []
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": auth.get_current_user(),
            "action": action,
            "details": details
        }
        
        log.append(log_entry)
        
        # Guardar log actualizado
        write_user_json('trading_access_log.json', log)
    
    @require_login
    def scan_signals(self):
        """Escanea señales de trading (requiere autenticación)"""
        user = auth.get_current_user()
        self._log_access("scan_signals")
        
        print(f"\n📊 Escaneando señales para {user}...")
        
        # Obtener configuración del usuario
        config = read_user_json('bot_config.json')
        if not config:
            print("❌ No se pudo cargar la configuración del usuario")
            return []
        
        # Usar los símbolos configurados por el usuario
        symbols = config.get('symbols', ['BTC-USD', 'ETH-USD'])
        print(f"   Símbolos: {', '.join(symbols)}")
        
        # Escanear señales
        all_signals = []
        for symbol in symbols:
            signals = self.trading_system.scan_signals(symbol)
            if signals:
                all_signals.extend(signals)
        
        print(f"   ✅ Se encontraron {len(all_signals)} señales")
        return all_signals
    
    @require_login
    def execute_trade(self, symbol, signal_type, amount=None):
        """Ejecuta una operación (requiere autenticación)"""
        user = auth.get_current_user()
        
        # Obtener portfolio del usuario
        portfolio = read_user_json('portfolio.json')
        if not portfolio:
            print("❌ No se pudo cargar el portfolio")
            return None
        
        # Verificar balance disponible
        balance = portfolio.get('balance', 0)
        config = read_user_json('bot_config.json')
        risk_per_trade = config.get('risk_per_trade', 0.02)
        
        if amount is None:
            amount = balance * risk_per_trade
        
        if amount > balance:
            print(f"❌ Balance insuficiente. Disponible: ${balance:.2f}")
            return None
        
        self._log_access("execute_trade", {
            "symbol": symbol,
            "signal_type": signal_type,
            "amount": amount
        })
        
        print(f"\n💰 Ejecutando operación para {user}:")
        print(f"   Symbol: {symbol}")
        print(f"   Tipo: {signal_type}")
        print(f"   Monto: ${amount:.2f}")
        
        # Crear trade
        trade = {
            "id": f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "symbol": symbol,
            "type": signal_type,
            "amount": amount,
            "entry_price": 100,  # Precio simulado
            "entry_time": datetime.now().isoformat(),
            "status": "active",
            "user": user
        }
        
        # Actualizar trades activos del usuario
        active_trades = read_user_json('active_trades.json') or []
        active_trades.append(trade)
        write_user_json('active_trades.json', active_trades)
        
        # Actualizar balance
        portfolio['balance'] -= amount
        write_user_json('portfolio.json', portfolio)
        
        print(f"   ✅ Trade ejecutado. Balance restante: ${portfolio['balance']:.2f}")
        return trade
    
    @require_login
    def view_portfolio(self):
        """Muestra el portafolio del usuario actual"""
        user = auth.get_current_user()
        self._log_access("view_portfolio")
        
        print(f"\n📈 Portafolio de {user}:")
        print("-" * 40)
        
        # Cargar portfolio del usuario
        portfolio = read_user_json('portfolio.json')
        if portfolio:
            print(f"💵 Balance: ${portfolio.get('balance', 0):.2f} {portfolio.get('currency', 'USDT')}")
            created = portfolio.get('created', 'N/A')
            print(f"📅 Creado: {created}")
        
        # Cargar trades activos del usuario
        active_trades = read_user_json('active_trades.json') or []
        
        if not active_trades:
            print("\n🔹 No hay operaciones activas")
        else:
            print(f"\n🔹 Operaciones activas ({len(active_trades)}):")
            for trade in active_trades:
                print(f"\n  • {trade.get('symbol', 'N/A')}: {trade.get('type', 'N/A')}")
                print(f"    ID: {trade.get('id', 'N/A')}")
                print(f"    Entrada: ${trade.get('entry_price', 0):.2f}")
                print(f"    Monto: ${trade.get('amount', 0):.2f}")
                
                # Calcular P&L simulado
                if 'current_price' in trade:
                    entry = trade['entry_price']
                    current = trade['current_price']
                    pnl_pct = ((current - entry) / entry * 100) if trade['type'] == 'BUY' else ((entry - current) / entry * 100)
                    pnl_usd = trade['amount'] * (pnl_pct / 100)
                    print(f"    P&L: {pnl_pct:+.2f}% (${pnl_usd:+.2f})")
        
        # Mostrar estadísticas del historial
        history = read_user_json('trade_history.json') or []
        if history:
            total_trades = len(history)
            winning_trades = sum(1 for t in history if t.get('pnl', 0) > 0)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            total_pnl = sum(t.get('pnl', 0) for t in history)
            
            print(f"\n📊 Estadísticas históricas:")
            print(f"  Total trades: {total_trades}")
            print(f"  Win rate: {win_rate:.2f}%")
            print(f"  P&L Total: ${total_pnl:+.2f}")
    
    @require_login
    def compare_portfolios(self):
        """Compara los portfolios de ambos usuarios (solo admin)"""
        current_user = auth.get_current_user()
        
        if current_user != "admin":
            print("❌ Solo el administrador puede comparar portfolios")
            return
        
        self._log_access("compare_portfolios")
        
        print("\n📊 Comparación de Portfolios")
        print("=" * 50)
        
        users = user_data.list_users()
        
        for username in users:
            print(f"\n👤 {username}:")
            
            # Obtener datos del usuario
            stats = user_data.get_user_stats(username)
            
            if stats and stats['portfolio']:
                print(f"  Balance: ${stats['portfolio']['balance']:.2f}")
                print(f"  Trades activos: {stats['active_trades']}")
                
                if 'total_trades' in stats:
                    print(f"  Total histórico: {stats['total_trades']} trades")
                    print(f"  Win rate: {stats.get('win_rate', 0):.2f}%")
                    print(f"  P&L Total: ${stats.get('total_pnl', 0):+.2f}")
            else:
                print("  Sin datos disponibles")
    
    @require_login
    def update_settings(self, settings):
        """Actualiza configuración del usuario actual"""
        user = auth.get_current_user()
        self._log_access("update_settings", settings)
        
        # Cargar configuración actual del usuario
        config = read_user_json('bot_config.json') or {}
        
        # Actualizar con nuevos valores
        config.update(settings)
        
        # Guardar configuración actualizada
        if write_user_json('bot_config.json', config):
            print(f"✅ Configuración actualizada para {user}")
            return True
        else:
            print(f"❌ Error actualizando configuración")
            return False
    
    @require_login
    def view_settings(self):
        """Muestra la configuración del usuario actual"""
        user = auth.get_current_user()
        config = read_user_json('bot_config.json')
        
        print(f"\n⚙️  Configuración de {user}:")
        print("-" * 40)
        
        if config:
            print(f"  Intervalo de escaneo: {config.get('scan_interval', 600)} segundos")
            print(f"  Stop Loss: {config.get('stop_loss', 2.0)}%")
            print(f"  Take Profit: {config.get('take_profit', 4.0)}%")
            print(f"  Max trades simultáneos: {config.get('max_trades', 3)}")
            print(f"  Riesgo por trade: {config.get('risk_per_trade', 0.02) * 100}%")
            print(f"  Símbolos: {', '.join(config.get('symbols', []))}")
        else:
            print("  No hay configuración disponible")
    
    def run_interactive(self):
        """Ejecuta el sistema en modo interactivo"""
        print("\n🤖 Sistema de Trading Protegido V2.0")
        print("    Con datos segregados por usuario")
        print("=" * 50)
        
        while True:
            user = auth.get_current_user()
            
            if user:
                print(f"\n👤 Usuario: {user}")
            
            print("\n📋 Menú Principal:")
            print("1. Escanear señales")
            print("2. Ver mi portafolio")
            print("3. Ejecutar trade simulado")
            print("4. Ver mi configuración")
            print("5. Cambiar configuración")
            
            if user == "admin":
                print("6. Comparar todos los portfolios (admin)")
                print("7. Cerrar sesión")
                print("8. Salir")
            else:
                print("6. Cerrar sesión")
                print("7. Salir")
            
            opcion = input("\nSelecciona una opción: ")
            
            if opcion == "1":
                signals = self.scan_signals()
                if signals:
                    print(f"\n📍 Señales encontradas:")
                    for sig in signals[:5]:  # Mostrar máx 5
                        print(f"  • {sig}")
            
            elif opcion == "2":
                self.view_portfolio()
            
            elif opcion == "3":
                symbol = input("Symbol (ej: BTC-USD): ").upper()
                signal_type = input("Tipo (BUY/SELL): ").upper()
                amount = input("Monto (Enter para usar riesgo por defecto): ")
                amount = float(amount) if amount else None
                
                trade = self.execute_trade(symbol, signal_type, amount)
                if trade:
                    print(f"\n✅ Trade creado: {trade['id']}")
            
            elif opcion == "4":
                self.view_settings()
            
            elif opcion == "5":
                print("\n⚙️  Opciones de configuración:")
                print("1. Cambiar símbolos")
                print("2. Ajustar stop loss")
                print("3. Ajustar take profit")
                print("4. Cambiar riesgo por trade")
                
                config_option = input("\nSelecciona (1-4): ")
                
                settings = {}
                if config_option == "1":
                    symbols = input("Símbolos (separados por coma): ").upper()
                    settings['symbols'] = [s.strip() for s in symbols.split(',')]
                elif config_option == "2":
                    stop_loss = input("Nuevo stop loss (%): ")
                    settings['stop_loss'] = float(stop_loss)
                elif config_option == "3":
                    take_profit = input("Nuevo take profit (%): ")
                    settings['take_profit'] = float(take_profit)
                elif config_option == "4":
                    risk = input("Riesgo por trade (% del capital): ")
                    settings['risk_per_trade'] = float(risk) / 100
                
                if settings:
                    self.update_settings(settings)
            
            elif opcion == "6":
                if user == "admin":
                    self.compare_portfolios()
                else:
                    auth.logout()
                    print("👋 Sesión cerrada. Volviendo al login...")
                    if not auth.login():
                        break
            
            elif opcion == "7":
                if user == "admin":
                    auth.logout()
                    print("👋 Sesión cerrada. Volviendo al login...")
                    if not auth.login():
                        break
                else:
                    print("\n👋 Hasta luego!")
                    break
            
            elif opcion == "8" and user == "admin":
                print("\n👋 Hasta luego!")
                break
            
            else:
                print("❌ Opción no válida")


def main():
    """Punto de entrada principal"""
    system = ProtectedTradingSystemV2()
    
    # Verificar autenticación inicial
    print("\n🔐 Sistema de Trading V2 - Autenticación Requerida")
    print("=" * 50)
    
    if not auth.is_authenticated():
        print("\nPor favor, inicia sesión para continuar")
        print("Usuarios disponibles: admin, trader")
        print("\n⚠️  Cada usuario tiene su propio portfolio y configuración")
        
        # Intentar login
        for attempt in range(3):
            if auth.login():
                break
            if attempt < 2:
                print(f"\nIntentos restantes: {2 - attempt}")
        else:
            print("\n❌ Máximo de intentos alcanzado. Sistema bloqueado.")
            sys.exit(1)
    
    # Ejecutar sistema interactivo
    system.run_interactive()


if __name__ == "__main__":
    main()