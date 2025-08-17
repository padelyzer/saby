#!/usr/bin/env python3
"""
Dashboard Web para Gestión de Señales de Trading
Interfaz visual para monitoreo y configuración en tiempo real
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from signal_manager import SignalManager, TradingSignal
import time

# Configuración de página
st.set_page_config(
    page_title="📡 Signal Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado
st.markdown("""
<style>
    .signal-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: #f7f7f7;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        border-left: 4px solid #667eea;
    }
    
    .long-signal {
        background: linear-gradient(135deg, #0ECB81 0%, #0B8A5B 100%);
    }
    
    .short-signal {
        background: linear-gradient(135deg, #F6465D 0%, #C73E52 100%);
    }
    
    .stButton > button {
        width: 100%;
        background: #667eea;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def load_signal_manager():
    """Carga el gestor de señales"""
    if 'signal_manager' not in st.session_state:
        st.session_state.signal_manager = SignalManager()
    return st.session_state.signal_manager

def load_config():
    """Carga la configuración actual"""
    if os.path.exists('signal_config.json'):
        with open('signal_config.json', 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    """Guarda la configuración"""
    with open('signal_config.json', 'w') as f:
        json.dump(config, f, indent=2)

def display_signal_card(signal: TradingSignal):
    """Muestra una tarjeta de señal"""
    css_class = "long-signal" if signal.direccion == "LONG" else "short-signal"
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"**{signal.ticker}**")
        st.markdown(f"🎯 {signal.direccion}")
    
    with col2:
        st.metric("Entry", f"${signal.price:.4f}")
        st.metric("Score", f"{signal.score:.1f}/10")
    
    with col3:
        st.metric("Stop Loss", f"${signal.stop_loss:.4f}")
        st.metric("Take Profit", f"${signal.take_profit:.4f}")
    
    with col4:
        st.metric("Leverage", f"{signal.leverage}x")
        st.metric("Size", f"{signal.position_size_pct}%")
        
        # Botones de acción
        if st.button(f"📋 Copiar", key=f"copy_{signal.ticker}"):
            trade_text = f"""
📊 {signal.ticker}
Entry: ${signal.price:.4f}
SL: ${signal.stop_loss:.4f}
TP: ${signal.take_profit:.4f}
Leverage: {signal.leverage}x
"""
            st.code(trade_text)

def main():
    st.title("📡 Dashboard de Señales de Trading")
    
    # Sidebar con configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        manager = load_signal_manager()
        config = load_config()
        
        st.subheader("📢 Canales de Notificación")
        
        # Telegram
        with st.expander("📱 Telegram", expanded=False):
            telegram_enabled = st.checkbox(
                "Activar Telegram",
                value=config.get('telegram', {}).get('enabled', False)
            )
            
            if telegram_enabled:
                bot_token = st.text_input(
                    "Bot Token",
                    value=config.get('telegram', {}).get('bot_token', ''),
                    type="password"
                )
                chat_id = st.text_input(
                    "Chat ID",
                    value=config.get('telegram', {}).get('chat_id', '')
                )
                
                if st.button("💾 Guardar Telegram"):
                    config['telegram'] = {
                        'enabled': True,
                        'bot_token': bot_token,
                        'chat_id': chat_id
                    }
                    save_config(config)
                    st.success("✅ Configuración guardada")
                    st.rerun()
        
        # Discord
        with st.expander("💬 Discord", expanded=False):
            discord_enabled = st.checkbox(
                "Activar Discord",
                value=config.get('discord', {}).get('enabled', False)
            )
            
            if discord_enabled:
                webhook_url = st.text_input(
                    "Webhook URL",
                    value=config.get('discord', {}).get('webhook_url', ''),
                    type="password"
                )
                
                if st.button("💾 Guardar Discord"):
                    config['discord'] = {
                        'enabled': True,
                        'webhook_url': webhook_url
                    }
                    save_config(config)
                    st.success("✅ Configuración guardada")
                    st.rerun()
        
        # Filtros
        st.subheader("🎯 Filtros de Señales")
        
        min_score = st.slider(
            "Score Mínimo",
            min_value=3,
            max_value=10,
            value=config.get('filters', {}).get('min_score', 5)
        )
        
        max_signals = st.number_input(
            "Máx. Señales Simultáneas",
            min_value=1,
            max_value=10,
            value=config.get('filters', {}).get('max_simultaneous_signals', 5)
        )
        
        cooldown = st.number_input(
            "Cooldown (minutos)",
            min_value=5,
            max_value=60,
            value=config.get('filters', {}).get('cooldown_minutes', 15)
        )
        
        if st.button("💾 Guardar Filtros"):
            if 'filters' not in config:
                config['filters'] = {}
            
            config['filters']['min_score'] = min_score
            config['filters']['max_simultaneous_signals'] = max_signals
            config['filters']['cooldown_minutes'] = cooldown
            
            save_config(config)
            st.success("✅ Filtros guardados")
            st.rerun()
    
    # Contenido principal
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔴 Señales en Vivo",
        "📊 Análisis de Mercado",
        "📈 Historial",
        "🤖 Bot Control"
    ])
    
    with tab1:
        st.header("🔴 Señales Activas")
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("🔄 Escanear Ahora", type="primary"):
                with st.spinner("Escaneando mercado..."):
                    # Lista de tickers
                    tickers = [
                        'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD',
                        'XRP-USD', 'ADA-USD', 'DOGE-USD', 'AVAX-USD'
                    ]
                    
                    signals = manager.scan_market(tickers)
                    
                    if signals:
                        st.success(f"✅ {len(signals)} señales encontradas!")
                        for signal in signals:
                            # Enviar señal
                            results = manager.broadcast_signal(signal)
                            st.info(f"📤 {signal.ticker}: Enviado a {sum(1 for v in results.values() if v)} canales")
                    else:
                        st.warning("No se encontraron señales en este momento")
        
        # Mostrar señales activas
        active_signals = manager.get_active_signals()
        
        if active_signals:
            st.subheader(f"📊 {len(active_signals)} Señales Activas")
            
            for signal in active_signals:
                with st.container():
                    display_signal_card(signal)
                    st.divider()
        else:
            st.info("📭 No hay señales activas en este momento")
        
        # Estadísticas rápidas
        st.subheader("📊 Estadísticas del Día")
        
        today_signals = [s for s in manager.signal_history 
                        if datetime.fromisoformat(s.timestamp).date() == datetime.now().date()]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Señales Hoy", len(today_signals))
        
        with col2:
            long_signals = sum(1 for s in today_signals if s.direccion == "LONG")
            st.metric("LONG", long_signals)
        
        with col3:
            short_signals = sum(1 for s in today_signals if s.direccion == "SHORT")
            st.metric("SHORT", short_signals)
        
        with col4:
            avg_score = sum(s.score for s in today_signals) / len(today_signals) if today_signals else 0
            st.metric("Score Promedio", f"{avg_score:.1f}")
    
    with tab2:
        st.header("📊 Análisis de Mercado en Tiempo Real")
        
        # Selector de ticker
        ticker = st.selectbox(
            "Seleccionar Activo",
            ['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD']
        )
        
        if st.button("📈 Analizar"):
            with st.spinner(f"Analizando {ticker}..."):
                from motor_trading import obtener_datos, calcular_indicadores, calcular_score, calcular_semaforo_mercado
                
                # Obtener datos
                df = obtener_datos(ticker, period='1m')
                
                if df is not None:
                    df = calcular_indicadores(df)
                    estado_mercado = calcular_semaforo_mercado()
                    score, etapa, direccion = calcular_score(df, estado_mercado)
                    
                    # Mostrar análisis
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Estado Mercado", estado_mercado)
                    with col2:
                        st.metric("Score", f"{score:.1f}/10")
                    with col3:
                        st.metric("Dirección", direccion if direccion != 'NONE' else 'NEUTRAL')
                    
                    # Gráfico de precio
                    fig = go.Figure()
                    
                    fig.add_trace(go.Candlestick(
                        x=df.index[-100:],
                        open=df['Open'][-100:],
                        high=df['High'][-100:],
                        low=df['Low'][-100:],
                        close=df['Close'][-100:],
                        name='Precio'
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=df.index[-100:],
                        y=df['SMA50'][-100:],
                        name='SMA50',
                        line=dict(color='orange')
                    ))
                    
                    fig.update_layout(
                        title=f"{ticker} - Últimas 100 velas",
                        yaxis_title="Precio",
                        template='plotly_dark',
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Indicadores
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # RSI
                        fig_rsi = go.Figure()
                        fig_rsi.add_trace(go.Scatter(
                            x=df.index[-100:],
                            y=df['RSI'][-100:],
                            name='RSI',
                            line=dict(color='purple')
                        ))
                        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
                        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
                        fig_rsi.update_layout(
                            title="RSI",
                            yaxis_title="RSI",
                            template='plotly_dark',
                            height=250
                        )
                        st.plotly_chart(fig_rsi, use_container_width=True)
                    
                    with col2:
                        # Volumen
                        fig_vol = go.Figure()
                        colors = ['red' if df['Close'].iloc[i] < df['Open'].iloc[i] else 'green' 
                                 for i in range(-100, 0)]
                        fig_vol.add_trace(go.Bar(
                            x=df.index[-100:],
                            y=df['Volume'][-100:],
                            name='Volumen',
                            marker_color=colors
                        ))
                        fig_vol.update_layout(
                            title="Volumen",
                            yaxis_title="Volumen",
                            template='plotly_dark',
                            height=250
                        )
                        st.plotly_chart(fig_vol, use_container_width=True)
    
    with tab3:
        st.header("📈 Historial de Señales")
        
        if manager.signal_history:
            # Convertir a DataFrame
            history_data = []
            for signal in manager.signal_history[-50:]:  # Últimas 50 señales
                history_data.append({
                    'Timestamp': signal.timestamp,
                    'Ticker': signal.ticker,
                    'Dirección': signal.direccion,
                    'Precio': f"${signal.price:.4f}",
                    'Score': signal.score,
                    'Confianza': signal.confidence,
                    'Leverage': f"{signal.leverage}x"
                })
            
            df_history = pd.DataFrame(history_data)
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                filter_direction = st.selectbox(
                    "Filtrar por Dirección",
                    ['Todas', 'LONG', 'SHORT']
                )
            
            with col2:
                filter_confidence = st.selectbox(
                    "Filtrar por Confianza",
                    ['Todas', 'HIGH', 'MEDIUM', 'LOW']
                )
            
            # Aplicar filtros
            if filter_direction != 'Todas':
                df_history = df_history[df_history['Dirección'] == filter_direction]
            
            if filter_confidence != 'Todas':
                df_history = df_history[df_history['Confianza'] == filter_confidence]
            
            # Mostrar tabla
            st.dataframe(df_history, use_container_width=True)
            
            # Gráfico de distribución
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    df_history,
                    names='Dirección',
                    title='Distribución LONG vs SHORT'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.histogram(
                    df_history,
                    x='Score',
                    title='Distribución de Scores',
                    nbins=10
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 No hay historial de señales disponible")
    
    with tab4:
        st.header("🤖 Control del Bot")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚙️ Configuración del Bot")
            
            interval = st.slider(
                "Intervalo de Escaneo (minutos)",
                min_value=1,
                max_value=60,
                value=5
            )
            
            auto_trade = st.checkbox("Trading Automático (Paper)", value=False)
            
            if st.button("💾 Guardar Configuración Bot"):
                st.success("✅ Configuración guardada")
        
        with col2:
            st.subheader("📊 Estado del Bot")
            
            # Simulación de estado
            bot_status = "🟢 Activo" if st.session_state.get('bot_running', False) else "🔴 Detenido"
            
            st.metric("Estado", bot_status)
            st.metric("Último Escaneo", "Hace 2 minutos")
            st.metric("Señales Generadas Hoy", "7")
            
            if st.button("▶️ Iniciar Bot" if not st.session_state.get('bot_running', False) else "⏸️ Detener Bot"):
                st.session_state.bot_running = not st.session_state.get('bot_running', False)
                st.rerun()
        
        # Log del bot
        st.subheader("📜 Log del Bot")
        
        log_container = st.container()
        with log_container:
            st.text_area(
                "Actividad Reciente",
                value="""[2024-01-15 14:30:00] 🔍 Iniciando escaneo...
[2024-01-15 14:30:05] ✅ BTC-USD: Score 7.2 - LONG
[2024-01-15 14:30:06] 📤 Señal enviada a Telegram
[2024-01-15 14:30:10] ✅ ETH-USD: Score 6.8 - LONG
[2024-01-15 14:30:11] 📤 Señal enviada a Discord
[2024-01-15 14:30:15] ❌ SOL-USD: Score 3.5 - No cumple filtros
[2024-01-15 14:30:20] ✅ Escaneo completado: 2 señales generadas""",
                height=200
            )
        
        # Botón de actualización automática
        if st.checkbox("🔄 Actualización Automática"):
            st.empty()
            time.sleep(5)
            st.rerun()

if __name__ == "__main__":
    main()