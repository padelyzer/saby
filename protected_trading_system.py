#!/usr/bin/env python3
"""
Sistema de Trading Protegido con Autenticación
Integra el sistema de trading V4 con autenticación de usuarios
"""

from auth_system import auth, require_login
from trading_system_v4 import AdaptiveTradingSystem
import sys
import json
from datetime import datetime


class ProtectedTradingSystem:
    """Sistema de trading con autenticación integrada"""
    
    def __init__(self):
        self.trading_system = AdaptiveTradingSystem()
        self.log_file = 'trading_access_log.json'
        
    def _log_access(self, action, details=None):
        """Registra accesos al sistema"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": auth.get_current_user(),
            "action": action,
            "details": details
        }
        
        # Cargar log existente
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []
        
        # Añadir nueva entrada
        logs.append(log_entry)
        
        # Guardar log actualizado
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    @require_login
    def scan_signals(self):
        """Escanea señales de trading (requiere autenticación)"""
        self._log_access("scan_signals")
        print("\n📊 Escaneando señales de trading...")
        return self.trading_system.scan_all_symbols()
    
    @require_login
    def execute_trade(self, symbol, signal_type, amount=None):
        """Ejecuta una operación (requiere autenticación)"""
        self._log_access("execute_trade", {
            "symbol": symbol,
            "signal_type": signal_type,
            "amount": amount
        })
        
        print(f"\n💰 Ejecutando operación: {signal_type} {symbol}")
        # Aquí iría la lógica de ejecución real
        return {
            "status": "simulated",
            "symbol": symbol,
            "type": signal_type,
            "timestamp": datetime.now().isoformat()
        }
    
    @require_login
    def view_portfolio(self):
        """Muestra el portafolio actual (requiere autenticación)"""
        self._log_access("view_portfolio")
        print("\n📈 Portafolio actual:")
        print("-" * 40)
        
        # Cargar trades activos
        try:
            with open('active_trades.json', 'r') as f:
                trades = json.load(f)
                
            if not trades:
                print("No hay operaciones activas")
            else:
                for trade in trades:
                    print(f"• {trade.get('symbol', 'N/A')}: {trade.get('type', 'N/A')}")
                    print(f"  Entrada: ${trade.get('entry_price', 0):.2f}")
                    if 'current_price' in trade:
                        pnl = (trade['current_price'] - trade['entry_price']) / trade['entry_price'] * 100
                        print(f"  P&L: {pnl:+.2f}%")
        except FileNotFoundError:
            print("No hay operaciones activas")
    
    @require_login
    def backtest(self, symbol=None, days=30):
        """Ejecuta backtest (requiere autenticación)"""
        self._log_access("backtest", {"symbol": symbol, "days": days})
        
        print(f"\n🔄 Ejecutando backtest...")
        if symbol:
            print(f"   Symbol: {symbol}")
        print(f"   Período: últimos {days} días")
        
        # Aquí iría la lógica de backtest
        return {
            "status": "completed",
            "results": "Backtest completado exitosamente"
        }
    
    @require_login
    def update_settings(self, settings):
        """Actualiza configuración del sistema (requiere autenticación)"""
        user = auth.get_current_user()
        
        # Solo el admin puede cambiar configuración
        if user != "admin":
            print("❌ Solo el administrador puede cambiar la configuración")
            return False
        
        self._log_access("update_settings", settings)
        
        # Actualizar configuración
        try:
            with open('bot_config.json', 'r') as f:
                config = json.load(f)
            
            config.update(settings)
            
            with open('bot_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✅ Configuración actualizada")
            return True
        except Exception as e:
            print(f"❌ Error actualizando configuración: {e}")
            return False
    
    def run_interactive(self):
        """Ejecuta el sistema en modo interactivo"""
        print("\n🤖 Sistema de Trading Protegido V1.0")
        print("=" * 50)
        
        while True:
            print("\n📋 Menú Principal:")
            print("1. Escanear señales")
            print("2. Ver portafolio")
            print("3. Ejecutar backtest")
            print("4. Configuración (solo admin)")
            print("5. Cerrar sesión")
            print("6. Salir")
            
            opcion = input("\nSelecciona una opción (1-6): ")
            
            if opcion == "1":
                signals = self.scan_signals()
                if signals:
                    print(f"\n✅ Se encontraron {len(signals)} señales")
            
            elif opcion == "2":
                self.view_portfolio()
            
            elif opcion == "3":
                symbol = input("Symbol (Enter para todos): ").upper() or None
                days = input("Días de backtest (default 30): ")
                days = int(days) if days else 30
                self.backtest(symbol, days)
            
            elif opcion == "4":
                if auth.get_current_user() != "admin":
                    print("❌ Acceso denegado. Solo administradores.")
                else:
                    print("\nConfiguración disponible:")
                    print("1. Cambiar intervalo de escaneo")
                    print("2. Ajustar stop loss")
                    print("3. Ajustar take profit")
                    
                    config_option = input("\nSelecciona (1-3): ")
                    
                    settings = {}
                    if config_option == "1":
                        interval = input("Nuevo intervalo (minutos): ")
                        settings['scan_interval'] = int(interval)
                    elif config_option == "2":
                        stop_loss = input("Nuevo stop loss (%): ")
                        settings['stop_loss'] = float(stop_loss)
                    elif config_option == "3":
                        take_profit = input("Nuevo take profit (%): ")
                        settings['take_profit'] = float(take_profit)
                    
                    if settings:
                        self.update_settings(settings)
            
            elif opcion == "5":
                auth.logout()
                print("👋 Sesión cerrada. Volviendo al login...")
                if not auth.login():
                    break
            
            elif opcion == "6":
                print("\n👋 Hasta luego!")
                break
            
            else:
                print("❌ Opción no válida")


def main():
    """Punto de entrada principal"""
    system = ProtectedTradingSystem()
    
    # Verificar autenticación inicial
    print("\n🔐 Sistema de Trading - Autenticación Requerida")
    print("=" * 50)
    
    if not auth.is_authenticated():
        print("\nPor favor, inicia sesión para continuar")
        print("Usuarios disponibles: admin, trader")
        
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