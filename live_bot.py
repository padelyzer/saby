#!/usr/bin/env python3
"""
Bot de Live Paper Trading Autónomo
Ejecuta señales de alta probabilidad en tiempo real con estado persistente.
"""

import json
import pandas as pd
import time
import csv
import os
from datetime import datetime
from motor_trading import (
    obtener_datos,
    calcular_indicadores,
    calcular_score,
    calcular_semaforo_mercado,
    obtener_top_movers_binance,
    evaluar_etapa_tendencia
)

class LiveTrader:
    """Bot autónomo de paper trading en tiempo real."""
    
    def __init__(self, balance_inicial=100.0):
        self.archivo_estado = 'bot_estado.json'
        self.archivo_trades = 'live_paper_trades.csv'
        self.balance_inicial = balance_inicial
        
        # Cargar o inicializar estado
        self.cargar_estado()
        
        # Crear archivo de trades si no existe
        self._crear_archivo_trades()
        
        print(f"🤖 LiveTrader inicializado")
        print(f"💰 Balance actual: ${self.balance:.2f}")
        print(f"📊 Posiciones abiertas: {len(self.posiciones_abiertas)}")
    
    def cargar_estado(self):
        """Carga el estado desde archivo JSON o crea uno nuevo."""
        if os.path.exists(self.archivo_estado):
            try:
                with open(self.archivo_estado, 'r') as f:
                    estado = json.load(f)
                    self.balance = estado.get('balance', self.balance_inicial)
                    self.posiciones_abiertas = estado.get('posiciones_abiertas', [])
                    print(f"✅ Estado cargado desde {self.archivo_estado}")
            except Exception as e:
                print(f"⚠️ Error cargando estado: {e}. Creando estado nuevo.")
                self._crear_estado_inicial()
        else:
            self._crear_estado_inicial()
    
    def _crear_estado_inicial(self):
        """Crea el estado inicial del bot."""
        self.balance = self.balance_inicial
        self.posiciones_abiertas = []
        self.guardar_estado()
        print(f"🆕 Nuevo estado creado con balance inicial: ${self.balance:.2f}")
    
    def guardar_estado(self):
        """Guarda el estado actual en archivo JSON."""
        estado = {
            'balance': self.balance,
            'posiciones_abiertas': self.posiciones_abiertas,
            'ultima_actualizacion': datetime.now().isoformat()
        }
        
        try:
            with open(self.archivo_estado, 'w') as f:
                json.dump(estado, f, indent=2)
        except Exception as e:
            print(f"❌ Error guardando estado: {e}")
    
    def _crear_archivo_trades(self):
        """Crea el archivo CSV de trades si no existe."""
        if not os.path.exists(self.archivo_trades):
            with open(self.archivo_trades, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Timestamp', 'Ticker', 'Tipo', 'Precio', 'Score_Entrada', 
                    'Motivo_Salida', 'Resultado_USD', 'Resultado_Porc', 'Balance_Post'
                ])
    
    def registrar_trade(self, ticker, tipo, precio, score=None, motivo=None, resultado_usd=None, resultado_porc=None):
        """Registra una operación en el archivo CSV."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(self.archivo_trades, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, ticker, tipo, precio, score or '', 
                motivo or '', resultado_usd or '', resultado_porc or '', round(self.balance, 2)
            ])
    
    def verificar_salidas(self):
        """Verifica si alguna posición debe cerrarse por SL o TP."""
        posiciones_a_cerrar = []
        
        for i, posicion in enumerate(self.posiciones_abiertas):
            ticker = posicion['ticker']
            precio_entrada = posicion['precio_entrada']
            stop_loss = posicion['stop_loss']
            take_profit = posicion['take_profit']
            tamano_posicion = posicion['tamano_usd']
            direccion = posicion.get('direccion', 'LONG')
            
            # Obtener precio actual
            try:
                df = obtener_datos(ticker, period='5d')
                if df is None or len(df) == 0:
                    continue
                
                precio_actual = df['Close'].iloc[-1]
                precio_high = df['High'].iloc[-1]
                precio_low = df['Low'].iloc[-1]
                
                motivo_cierre = None
                precio_salida = None
                
                if direccion == 'LONG':
                    # LONG: TP si precio sube, SL si precio baja
                    if precio_high >= take_profit:
                        motivo_cierre = 'TP'
                        precio_salida = take_profit
                    elif precio_low <= stop_loss:
                        motivo_cierre = 'SL'
                        precio_salida = stop_loss
                else:  # SHORT
                    # SHORT: TP si precio baja, SL si precio sube
                    if precio_low <= take_profit:
                        motivo_cierre = 'TP'
                        precio_salida = take_profit
                    elif precio_high >= stop_loss:
                        motivo_cierre = 'SL'
                        precio_salida = stop_loss
                
                if motivo_cierre:
                    # Calcular resultado según dirección
                    acciones = tamano_posicion / precio_entrada
                    if direccion == 'LONG':
                        resultado_usd = acciones * (precio_salida - precio_entrada)
                    else:  # SHORT
                        resultado_usd = acciones * (precio_entrada - precio_salida)
                    resultado_porc = (resultado_usd / tamano_posicion) * 100
                    
                    # Actualizar balance
                    self.balance += resultado_usd
                    
                    # Registrar trade
                    self.registrar_trade(
                        ticker, 'Salida', precio_salida, 
                        motivo=motivo_cierre, 
                        resultado_usd=round(resultado_usd, 4),
                        resultado_porc=round(resultado_porc, 2)
                    )
                    
                    # Marcar para cerrar
                    posiciones_a_cerrar.append(i)
                    
                    resultado_emoji = "🟢" if resultado_usd > 0 else "🔴"
                    print(f"{resultado_emoji} SALIDA {ticker} | {motivo_cierre} | ${resultado_usd:+.2f} | Balance: ${self.balance:.2f}")
            
            except Exception as e:
                print(f"⚠️ Error verificando {ticker}: {e}")
        
        # Cerrar posiciones marcadas (en orden inverso para no afectar índices)
        for i in reversed(posiciones_a_cerrar):
            del self.posiciones_abiertas[i]
    
    def buscar_entradas(self):
        """Busca nuevas oportunidades de entrada según el sentido del mercado."""
        # Verificar estado del mercado
        estado_mercado = calcular_semaforo_mercado()
        
        # No operar en mercado neutral
        if estado_mercado == 'AMARILLO':
            print("⚠️ Mercado neutral - Sin nuevas operaciones")
            return
        
        # Solo operar en mercados con tendencia clara
        if estado_mercado not in ['VERDE', 'ROJO']:
            return
        
        # Limitar número de posiciones simultáneas
        max_posiciones = 3  # Máximo 3 posiciones abiertas
        
        # Si ya tenemos el máximo de posiciones, no buscar más
        if len(self.posiciones_abiertas) >= max_posiciones:
            return
            
        # Obtener lista de activos
        tickers = obtener_top_movers_binance(limit=20)
        if not tickers:
            # Fallback
            tickers = ['BTC-USD', 'ETH-USD', 'BNB-USD', 'ADA-USD', 'XRP-USD', 
                      'SOL-USD', 'DOT-USD', 'DOGE-USD', 'AVAX-USD', 'MATIC-USD']
        
        for ticker in tickers:
            # Verificar si ya tenemos posición abierta
            if any(pos['ticker'] == ticker for pos in self.posiciones_abiertas):
                continue
            
            try:
                # Obtener y analizar datos
                df = obtener_datos(ticker, period='1y')
                if df is None or len(df) < 200:
                    continue
                
                df = calcular_indicadores(df)
                score, etapa, direccion = calcular_score(df, estado_mercado)
                
                # Solo operar con señales válidas según el mercado
                if score >= 4 and direccion != 'NONE':
                    
                    # Preparar entrada
                    precio_entrada = df['Close'].iloc[-1]
                    atr = df['ATR'].iloc[-1]
                    
                    # Configurar SL y TP según dirección
                    if direccion == 'LONG':
                        # LONG: SL abajo, TP arriba
                        stop_loss = precio_entrada * 0.97   # -3%
                        take_profit = precio_entrada * 1.07  # +7%
                    else:  # SHORT
                        # SHORT: SL arriba, TP abajo
                        stop_loss = precio_entrada * 1.03   # +3%
                        take_profit = precio_entrada * 0.93  # -7%
                    
                    tamano_usd = 10.0  # Tamaño fijo de posición
                    
                    # Verificar que tenemos suficiente balance
                    if self.balance >= tamano_usd:
                        # Abrir posición
                        nueva_posicion = {
                            'ticker': ticker,
                            'precio_entrada': precio_entrada,
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'tamano_usd': tamano_usd,
                            'direccion': direccion,
                            'atr': atr,
                            'fecha_entrada': datetime.now().isoformat(),
                            'score_entrada': score
                        }
                        
                        self.posiciones_abiertas.append(nueva_posicion)
                        
                        # Registrar trade
                        self.registrar_trade(ticker, f'Entrada {direccion}', precio_entrada, score=score)
                        
                        emoji = "🟢" if direccion == "LONG" else "🔴"
                        print(f"{emoji} {direccion} {ticker} | Score: {score:.1f} | ${precio_entrada:.4f}")
                        print(f"   SL: ${stop_loss:.4f} | TP: ${take_profit:.4f}")
            
            except Exception as e:
                print(f"⚠️ Error analizando {ticker}: {e}")
    
    def ejecutar_ciclo(self):
        """Ejecuta un ciclo completo de trading."""
        print(f"\n🔄 Iniciando ciclo - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. Verificar salidas primero
            self.verificar_salidas()
            
            # 2. Buscar nuevas entradas
            self.buscar_entradas()
            
            # 3. Guardar estado
            self.guardar_estado()
            
            # 4. Mostrar resumen
            ganancia_perdida = self.balance - self.balance_inicial
            rendimiento = (ganancia_perdida / self.balance_inicial) * 100
            
            print(f"📊 Balance: ${self.balance:.2f} | P&L: ${ganancia_perdida:+.2f} ({rendimiento:+.2f}%)")
            print(f"📈 Posiciones abiertas: {len(self.posiciones_abiertas)}")
            
            if self.posiciones_abiertas:
                print("   Activos en cartera:", [pos['ticker'] for pos in self.posiciones_abiertas])
        
        except Exception as e:
            print(f"❌ Error en ciclo: {e}")
    
    def mostrar_resumen(self):
        """Muestra un resumen del estado actual."""
        print("\n" + "="*50)
        print("🤖 RESUMEN DEL BOT DE PAPER TRADING")
        print("="*50)
        print(f"💰 Balance actual: ${self.balance:.2f}")
        print(f"📈 P&L Total: ${self.balance - self.balance_inicial:+.2f}")
        print(f"📊 Rendimiento: {((self.balance / self.balance_inicial) - 1) * 100:+.2f}%")
        print(f"🎯 Posiciones abiertas: {len(self.posiciones_abiertas)}")
        
        if self.posiciones_abiertas:
            print("\n📋 POSICIONES ACTIVAS:")
            for pos in self.posiciones_abiertas:
                print(f"   {pos['ticker']} | Entrada: ${pos['precio_entrada']:.4f} | Score: {pos['score_entrada']:.1f}")
        
        print("="*50)

def main():
    """Función principal del bot."""
    print("🚀 Iniciando Bot de Live Paper Trading")
    print("⚠️  IMPORTANTE: Este es un sistema de trading simulado con fines educativos")
    print("💡 Para detener el bot, presiona Ctrl+C\n")
    
    # Crear instancia del trader
    bot = LiveTrader(balance_inicial=100.0)
    bot.mostrar_resumen()
    
    try:
        while True:
            # Ejecutar ciclo de trading
            bot.ejecutar_ciclo()
            
            # Esperar 5 minutos antes del siguiente ciclo
            print(f"⏳ Esperando 5 minutos hasta el próximo ciclo...")
            time.sleep(300)  # 5 minutos
    
    except KeyboardInterrupt:
        print("\n\n🛑 Bot detenido por el usuario")
        bot.mostrar_resumen()
        print("💾 Estado guardado. Puedes reiniciar el bot ejecutando: python live_bot.py")
    
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        bot.guardar_estado()
        print("💾 Estado guardado antes de salir")

if __name__ == "__main__":
    main()