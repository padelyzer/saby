# Importar librerías
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import json
import yfinance as yf
from datetime import datetime, timedelta

# Importar módulos del sistema original
from motor_trading import (
    obtener_datos, 
    calcular_indicadores, 
    calcular_score, 
    calcular_semaforo_mercado, 
    obtener_top_movers_binance,
    ejecutar_simulacion,
    analizar_resultados
)

# Importar módulos avanzados
from advanced_signals import AdvancedSignalDetector, scan_for_advanced_signals
from liquidity_pools import LiquidityPoolDetector, format_liquidity_report
from signal_manager import SignalManager
from trade_tracker import TradeTracker

def estilo_binance():
    """Aplica estilos CSS similares a Binance"""
    st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
        background-color: #0B0E11;
    }
    
    .stApp {
        background-color: #0B0E11;
        color: #EAECEF;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1E2329 0%, #2B3139 100%);
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #2B3139;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    
    .price-up {
        color: #0ECB81;
        font-weight: bold;
    }
    
    .price-down {
        color: #F6465D;
        font-weight: bold;
    }
    
    .binance-header {
        background: linear-gradient(135deg, #F0B90B 0%, #F8D12F 100%);
        color: #000;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 20px;
    }
    
    .liquidity-pool {
        background: linear-gradient(135deg, #17c5b4 0%, #0e8b7f 100%);
        padding: 12px;
        border-radius: 6px;
        margin: 8px 0;
        color: #FFF;
    }
    
    .signal-card {
        background: #1E2329;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #2B3139;
        margin: 10px 0;
    }
    
    .trade-status-active {
        background: #0ECB8120;
        border: 1px solid #0ECB81;
    }
    
    .trade-status-win {
        background: #0ECB8140;
        border: 2px solid #0ECB81;
    }
    
    .trade-status-loss {
        background: #F6465D20;
        border: 2px solid #F6465D;
    }
    </style>
    """, unsafe_allow_html=True)

def crear_grafico_velas(df, ticker):
    """Crea gráfico de velas con indicadores"""
    fig = go.Figure()
    
    # Velas
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Precio'
    ))
    
    # SMAs
    if 'SMA_50' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['SMA_50'],
            name='SMA 50', line=dict(color='orange', width=1)
        ))
    
    if 'SMA_200' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['SMA_200'],
            name='SMA 200', line=dict(color='blue', width=1)
        ))
    
    # Configuración del gráfico
    fig.update_layout(
        title=f"{ticker} - Gráfico de Trading",
        template='plotly_dark',
        height=500,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        yaxis_title='Precio',
        xaxis_title='Fecha'
    )
    
    return fig

def mostrar_pools_liquidez(ticker):
    """Muestra análisis de pools de liquidez"""
    detector = LiquidityPoolDetector()
    
    with st.spinner(f"Analizando pools de liquidez para {ticker}..."):
        try:
            # Obtener datos
            stock = yf.Ticker(ticker)
            df = stock.history(period='1mo', interval='1h')
            
            if len(df) < 50:
                st.warning("No hay suficientes datos para análisis de liquidez")
                return
            
            current_price = df['Close'].iloc[-1]
            liquidity_data = detector.detect_liquidity_pools(df, current_price)
            
            # Mostrar precio actual
            st.metric("Precio Actual", f"${current_price:,.2f}")
            
            # Mostrar pools más importantes
            st.subheader("🔥 Pools de Liquidación Importantes")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Pools ARRIBA del precio (Shorts)**")
                above_pools = liquidity_data['pools'].get('above_price', [])[:3]
                for pool in above_pools:
                    color = "🔴" if pool['strength'] > 10 else "🟡"
                    st.markdown(f"""
                    <div class="liquidity-pool">
                    {color} ${pool['price']:.2f} ({pool['distance_pct']:+.2f}%)
                    <br>Fuerza: {'█' * int(pool['strength']/5)}
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("**Pools DEBAJO del precio (Longs)**")
                below_pools = liquidity_data['pools'].get('below_price', [])[:3]
                for pool in below_pools:
                    color = "🟢" if pool['strength'] > 10 else "🟡"
                    st.markdown(f"""
                    <div class="liquidity-pool">
                    {color} ${pool['price']:.2f} ({pool['distance_pct']:+.2f}%)
                    <br>Fuerza: {'█' * int(pool['strength']/5)}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Crear gráfico con pools
            fig = go.Figure()
            
            # Precio actual
            fig.add_trace(go.Scatter(
                x=df.index[-100:], 
                y=df['Close'].tail(100),
                name='Precio',
                line=dict(color='white', width=2)
            ))
            
            # Agregar líneas de pools
            for pool in liquidity_data['heatmap'][:10]:
                color = 'red' if pool['direction'] == 'ABOVE' else 'green'
                opacity = min(pool['importance'] / 20, 0.8)
                
                fig.add_hline(
                    y=pool['price'], 
                    line_dash="dash",
                    line_color=color,
                    opacity=opacity,
                    annotation_text=f"Pool {pool['type'][:10]} ({pool['distance_pct']:+.1f}%)",
                    annotation_position="right"
                )
            
            fig.update_layout(
                title="Mapa de Calor de Liquidez",
                template='plotly_dark',
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Recomendaciones
            st.subheader("💡 Estrategia Recomendada")
            
            suggestions = detector.suggest_entry_exit(liquidity_data, 'LONG')
            
            if suggestions['warnings']:
                for warning in suggestions['warnings']:
                    st.warning(warning)
            
            if suggestions['stop_losses']:
                sl = suggestions['stop_losses'][0]
                st.info(f"**Stop Loss sugerido:** ${sl['price']:.2f} - {sl['reason']}")
            
            if suggestions['take_profits']:
                tp = suggestions['take_profits'][0]
                st.success(f"**Take Profit sugerido:** ${tp['price']:.2f} - {tp['reason']}")
            
        except Exception as e:
            st.error(f"Error analizando liquidez: {e}")

def mostrar_señales_avanzadas():
    """Muestra señales avanzadas con estructura de mercado"""
    detector = AdvancedSignalDetector()
    
    tickers = st.multiselect(
        "Selecciona criptomonedas para analizar",
        ['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 
         'ADA-USD', 'DOT-USD', 'AVAX-USD', 'MATIC-USD', 'LINK-USD'],
        default=['BTC-USD', 'ETH-USD']
    )
    
    if st.button("🔍 Buscar Señales Avanzadas"):
        with st.spinner("Analizando estructura de mercado..."):
            signals = scan_for_advanced_signals(tickers)
            
            if signals:
                st.success(f"✅ {len(signals)} señales encontradas!")
                
                for signal in signals:
                    # Card para cada señal
                    emoji = "🟢" if signal['type'] == 'LONG' else "🔴"
                    
                    with st.expander(f"{emoji} {signal['ticker']} - {signal['type']} (Score: {signal['score']}/10)"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Entrada", f"${signal['entry_price']:.4f}")
                            st.metric("Stop Loss", f"${signal['stop_loss']:.4f}")
                        
                        with col2:
                            st.metric("Target 1", f"${signal['primary_target']['price']:.4f}")
                            st.caption(signal['primary_target']['reason'])
                        
                        with col3:
                            st.metric("R:R Ratio", f"{signal['risk_reward_ratio']}:1")
                            st.metric("Confluencias", signal['confluence_points'])
                        
                        # Razones de entrada
                        st.markdown("**Razones de entrada:**")
                        for reason in signal['entry_reasons']:
                            st.markdown(f"• {reason}")
                        
                        # Patrones detectados
                        if signal['chart_analysis']['patterns']:
                            st.markdown("**Patrones detectados:**")
                            for pattern in signal['chart_analysis']['patterns']:
                                st.markdown(f"• {pattern['name']} ({pattern['reliability']})")
                        
                        # Pools de liquidez cercanos
                        if 'liquidity_pools' in signal['chart_analysis']:
                            st.markdown("**Pools de liquidez cercanos:**")
                            for pool in signal['chart_analysis']['liquidity_pools'][:3]:
                                direction = "↑" if pool['direction'] == 'ABOVE' else "↓"
                                st.markdown(f"• ${pool['price']:.2f} ({pool['distance_pct']:+.2f}%) {direction}")
            else:
                st.warning("No se encontraron señales de alta calidad en este momento")

def mostrar_trade_tracker():
    """Muestra el seguimiento de trades"""
    tracker = TradeTracker()
    
    # Métricas generales
    stats = tracker.get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Trades", stats['total_trades'])
        st.metric("Activos", stats['active_trades'])
    
    with col2:
        st.metric("Ganados", stats['winning_trades'], 
                 delta=f"{stats['win_rate']:.1f}% WR")
    
    with col3:
        st.metric("PnL Total", f"{stats['total_pnl']:+.2f}%")
        st.metric("PnL Promedio", f"{stats['avg_pnl']:+.2f}%")
    
    with col4:
        st.metric("Mejor Trade", f"{stats['best_trade']:+.2f}%")
        st.metric("Peor Trade", f"{stats['worst_trade']:+.2f}%")
    
    # Trades activos
    st.subheader("📊 Trades Activos")
    active_trades = tracker.get_active_trades()
    
    if active_trades:
        for trade_id, trade in active_trades.items():
            current_pnl = trade.get('current_pnl', 0)
            status_class = "trade-status-active"
            if current_pnl > 0:
                status_class = "trade-status-win"
            elif current_pnl < -2:
                status_class = "trade-status-loss"
            
            st.markdown(f"""
            <div class="signal-card {status_class}">
                <b>{trade['ticker']}</b> - {trade['direccion']}
                <br>Entrada: ${trade['entry_price']:.4f} | Actual: ${trade.get('current_price', 0):.4f}
                <br>PnL: {current_pnl:+.2f}% | Tiempo: {trade.get('duration', 'N/A')}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No hay trades activos")
    
    # Historial
    if st.checkbox("Ver historial completo"):
        history_df = tracker.get_history_dataframe()
        if not history_df.empty:
            st.dataframe(history_df.tail(20))
        else:
            st.info("No hay historial de trades")

def main():
    st.set_page_config(
        page_title="Trading System Pro - Completo",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Aplicar estilos
    estilo_binance()
    
    # Header principal
    st.markdown("""
    <div class="binance-header">
        🚀 SISTEMA DE TRADING PROFESIONAL v3.0
        <br><small>Análisis Técnico + Estructura de Mercado + Pools de Liquidez</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar con navegación
    st.sidebar.title("🧭 Navegación")
    
    pagina = st.sidebar.radio(
        "Selecciona módulo:",
        [
            "📊 Dashboard Principal",
            "🎯 Señales Avanzadas",
            "💧 Pools de Liquidez",
            "📈 Paper Trading",
            "🤖 Live Bot Monitor",
            "📋 Trade Tracker",
            "⚙️ Configuración"
        ]
    )
    
    # Estado del mercado en sidebar
    estado_mercado = calcular_semaforo_mercado()
    color_class = {
        'VERDE': 'status-green',
        'AMARILLO': 'status-yellow',
        'ROJO': 'status-red'
    }.get(estado_mercado, 'status-yellow')
    
    st.sidebar.markdown(f"""
    <div class="market-status {color_class}">
        🚦 Mercado: {estado_mercado}
    </div>
    """, unsafe_allow_html=True)
    
    # Routing de páginas
    if pagina == "📊 Dashboard Principal":
        # Vista general del mercado
        st.header("📊 Dashboard Principal")
        
        tab1, tab2, tab3 = st.tabs(["Análisis en Vivo", "Top Movers", "Análisis Técnico"])
        
        with tab1:
            ticker = st.selectbox(
                "Selecciona cripto:",
                ['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD']
            )
            
            df = obtener_datos(ticker)
            if df is not None and len(df) > 0:
                df = calcular_indicadores(df)
                score, etapa, direccion = calcular_score(df, estado_mercado)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Precio", f"${df['Close'].iloc[-1]:,.2f}")
                with col2:
                    st.metric("Score", f"{score}/10")
                with col3:
                    emoji = "🟢" if direccion == "LONG" else "🔴" if direccion == "SHORT" else "⚪"
                    st.metric("Señal", f"{emoji} {direccion}")
                
                # Gráfico
                fig = crear_grafico_velas(df.tail(100), ticker)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No se pudieron obtener datos para este ticker")
        
        with tab2:
            st.subheader("🚀 Top Movers")
            top_movers = obtener_top_movers_binance()
            if top_movers:
                st.dataframe(top_movers)
            else:
                st.info("Cargando top movers...")
        
        with tab3:
            st.subheader("📈 Indicadores Técnicos")
            if df is not None and len(df) > 0:
                col1, col2 = st.columns(2)
                with col1:
                    if 'RSI' in df.columns:
                        st.metric("RSI", f"{df['RSI'].iloc[-1]:.2f}")
                    if 'ATR' in df.columns:
                        st.metric("ATR", f"{df['ATR'].iloc[-1]:.4f}")
                with col2:
                    if 'SMA_50' in df.columns:
                        st.metric("SMA 50", f"${df['SMA_50'].iloc[-1]:,.2f}")
                    if 'SMA_200' in df.columns:
                        st.metric("SMA 200", f"${df['SMA_200'].iloc[-1]:,.2f}")
    
    elif pagina == "🎯 Señales Avanzadas":
        st.header("🎯 Señales Avanzadas con Estructura de Mercado")
        st.markdown("""
        Sistema que detecta movimientos largos basados en:
        - Soportes y Resistencias reales
        - Niveles de Fibonacci
        - Patrones gráficos
        - Order Blocks institucionales
        - Pools de liquidez
        """)
        
        mostrar_señales_avanzadas()
    
    elif pagina == "💧 Pools de Liquidez":
        st.header("💧 Análisis de Pools de Liquidez")
        st.markdown("""
        Detecta zonas donde se acumulan stops y liquidaciones:
        - Niveles de liquidación por leverage (3x, 5x, 10x, etc)
        - Clusters de stop loss
        - Zonas de barrido institucional
        """)
        
        ticker = st.selectbox(
            "Selecciona cripto para análisis de liquidez:",
            ['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD']
        )
        
        mostrar_pools_liquidez(ticker)
    
    elif pagina == "📈 Paper Trading":
        st.header("📈 Paper Trading - Simulación Avanzada")
        
        # Tabs para diferentes tipos de backtesting
        tab1, tab2 = st.tabs(["🚀 Backtesting Avanzado", "📊 Backtesting Simple"])
        
        with tab1:
            st.subheader("Sistema Avanzado con Múltiples Estrategias")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                capital_inicial = st.number_input("Capital Inicial ($)", value=10000, min_value=100, key="adv_capital")
                position_size = st.slider("Tamaño por Trade (%)", 5, 25, 10, key="position_size") / 100
                max_positions = st.number_input("Máx. Posiciones Simultáneas", 1, 10, 5, key="max_pos")
            
            with col2:
                periodo = st.selectbox("Período de Backtesting", 
                                      ['1mo', '3mo', '6mo', '1y'], 
                                      key="adv_period")
                
                # Mapeo de períodos
                period_days = {'1mo': 30, '3mo': 90, '6mo': 180, '1y': 365}
                days = period_days[periodo]
            
            with col3:
                # Selector de estrategias
                all_strategies = [
                    'Momentum',
                    'Mean Reversion', 
                    'Breakout',
                    'Scalping',
                    'Liquidity Hunt',
                    'Grid Trading'
                ]
                
                selected_strategies = st.multiselect(
                    "Estrategias a Probar:",
                    all_strategies,
                    default=['Momentum', 'Mean Reversion', 'Breakout'],
                    key="strategies"
                )
            
            # Selector de pares expandido
            st.subheader("Selección de Pares")
            
            # Predefinidos por categoría
            col1, col2 = st.columns(2)
            
            with col1:
                use_presets = st.checkbox("Usar presets", value=True)
                
                if use_presets:
                    preset = st.selectbox(
                        "Categoría:",
                        ['Top 10', 'DeFi', 'Layer 1', 'Meme Coins', 'Todo (30+)']
                    )
                    
                    preset_tickers = {
                        'Top 10': ['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD',
                                  'ADA-USD', 'DOGE-USD', 'AVAX-USD', 'DOT-USD', 'MATIC-USD'],
                        'DeFi': ['UNI-USD', 'LINK-USD', 'AAVE-USD', 'MKR-USD', 'CRV-USD',
                                'COMP-USD', 'SNX-USD', 'SUSHI-USD'],
                        'Layer 1': ['ETH-USD', 'BNB-USD', 'SOL-USD', 'ADA-USD', 'AVAX-USD',
                                   'DOT-USD', 'ATOM-USD', 'NEAR-USD', 'FTM-USD'],
                        'Meme Coins': ['DOGE-USD', 'SHIB-USD', 'PEPE-USD', 'FLOKI-USD'],
                        'Todo (30+)': ['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD',
                                      'ADA-USD', 'DOGE-USD', 'AVAX-USD', 'DOT-USD', 'MATIC-USD',
                                      'LINK-USD', 'UNI-USD', 'LTC-USD', 'ATOM-USD', 'FIL-USD',
                                      'APT-USD', 'ARB-USD', 'OP-USD', 'NEAR-USD', 'VET-USD',
                                      'ALGO-USD', 'FTM-USD', 'SAND-USD', 'MANA-USD', 'AXS-USD',
                                      'AAVE-USD', 'CRV-USD', 'MKR-USD', 'SNX-USD', 'COMP-USD']
                    }
                    
                    tickers = preset_tickers.get(preset, preset_tickers['Top 10'])
            
            with col2:
                if not use_presets:
                    # Selector manual
                    tickers = st.multiselect(
                        "Selecciona criptos manualmente:",
                        ['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD',
                         'ADA-USD', 'DOGE-USD', 'AVAX-USD', 'DOT-USD', 'MATIC-USD',
                         'LINK-USD', 'UNI-USD', 'LTC-USD', 'ATOM-USD', 'FIL-USD',
                         'APT-USD', 'ARB-USD', 'OP-USD', 'NEAR-USD', 'VET-USD'],
                        default=['BTC-USD', 'ETH-USD', 'SOL-USD'],
                        key="manual_tickers"
                    )
                
                st.info(f"📊 {len(tickers)} pares seleccionados")
            
            # Botón de ejecución
            if st.button("🚀 Ejecutar Backtesting Avanzado", key="run_advanced"):
                with st.spinner(f"Ejecutando backtesting con {len(selected_strategies)} estrategias en {len(tickers)} pares..."):
                    try:
                        from backtesting_avanzado import BacktestEngine
                        from datetime import datetime, timedelta
                        
                        # Calcular fechas
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=days)
                        
                        # Ejecutar backtest
                        engine = BacktestEngine(initial_capital=capital_inicial)
                        results = engine.run_backtest(
                            tickers=tickers,
                            strategies=selected_strategies,
                            start_date=start_date,
                            end_date=end_date,
                            position_size=position_size,
                            max_positions=max_positions
                        )
                        
                        # Mostrar resultados
                        st.success("✅ Backtesting completado!")
                        
                        # Métricas principales
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Total Trades", results['total_trades'])
                            st.metric("Win Rate", f"{results['win_rate']:.1f}%")
                        
                        with col2:
                            st.metric("Profit Factor", f"{results['profit_factor']:.2f}")
                            st.metric("Sharpe Ratio", f"{results['sharpe_ratio']:.2f}")
                        
                        with col3:
                            st.metric("Retorno Total", f"{results['total_return']:+.2f}%")
                            st.metric("Max Drawdown", f"-{results['max_drawdown']:.2f}%")
                        
                        with col4:
                            st.metric("Mejor Trade", f"{results['best_trade']:+.2f}%")
                            st.metric("Peor Trade", f"{results['worst_trade']:+.2f}%")
                        
                        # Gráfico de equity curve
                        if results['equity_curve']:
                            st.subheader("📈 Curva de Capital")
                            
                            equity_df = pd.DataFrame(results['equity_curve'])
                            
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=equity_df['date'],
                                y=equity_df['capital'],
                                mode='lines',
                                name='Capital',
                                line=dict(color='#0ECB81', width=2)
                            ))
                            
                            # Línea de capital inicial
                            fig.add_hline(y=capital_inicial, 
                                        line_dash="dash", 
                                        line_color="gray",
                                        annotation_text="Capital Inicial")
                            
                            fig.update_layout(
                                title="Evolución del Capital",
                                xaxis_title="Fecha",
                                yaxis_title="Capital ($)",
                                template='plotly_dark',
                                height=400
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Performance por estrategia
                        if results['trades_by_strategy']:
                            st.subheader("🎯 Performance por Estrategia")
                            
                            strategy_df = pd.DataFrame.from_dict(results['trades_by_strategy'], orient='index')
                            strategy_df = strategy_df.sort_values('total_pnl', ascending=False)
                            
                            # Gráfico de barras
                            fig = go.Figure(data=[
                                go.Bar(name='PnL Total', 
                                      x=strategy_df.index, 
                                      y=strategy_df['total_pnl'],
                                      marker_color=['#0ECB81' if x > 0 else '#F6465D' 
                                                   for x in strategy_df['total_pnl']])
                            ])
                            
                            fig.update_layout(
                                title="PnL por Estrategia",
                                xaxis_title="Estrategia",
                                yaxis_title="PnL ($)",
                                template='plotly_dark',
                                height=300
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Tabla de estrategias
                            st.dataframe(strategy_df)
                        
                        # Performance por ticker
                        if results['performance_by_ticker']:
                            st.subheader("📊 Top 10 Tickers por Performance")
                            
                            ticker_df = pd.DataFrame.from_dict(results['performance_by_ticker'], orient='index')
                            ticker_df = ticker_df.sort_values('total_pnl', ascending=False).head(10)
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.dataframe(ticker_df)
                            
                            with col2:
                                # Gráfico pie de distribución
                                fig = px.pie(ticker_df.head(5), 
                                           values='total', 
                                           names=ticker_df.head(5).index,
                                           title='Top 5 Tickers por Número de Trades')
                                fig.update_traces(textposition='inside', textinfo='percent+label')
                                fig.update_layout(template='plotly_dark', height=300)
                                st.plotly_chart(fig, use_container_width=True)
                        
                        # Descargar resultados
                        st.download_button(
                            label="📥 Descargar Resultados JSON",
                            data=json.dumps(results, default=str, indent=2),
                            file_name=f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                        
                    except Exception as e:
                        st.error(f"Error en backtesting: {e}")
                        st.exception(e)
        
        with tab2:
            st.subheader("Backtesting Simple (Sistema Original)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                capital_inicial = st.number_input("Capital Inicial ($)", value=10000, min_value=100)
                periodo = st.selectbox("Período de Backtesting", ['1mo', '3mo', '6mo', '1y'])
            
            with col2:
                usar_leverage = st.checkbox("Usar Apalancamiento", value=True)
                leverage = st.slider("Leverage", 1, 10, 3) if usar_leverage else 1
            
            tickers = st.multiselect(
                "Selecciona criptos para backtest:",
                ['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD'],
                default=['BTC-USD', 'ETH-USD']
            )
            
            if st.button("▶️ Ejecutar Simulación"):
                with st.spinner("Ejecutando backtesting..."):
                    # La función ejecutar_simulacion no acepta ticker específico
                    # Ejecuta una simulación general con múltiples activos
                    
                    # Obtener días de simulación basado en período
                    dias_map = {'1mo': 30, '3mo': 90, '6mo': 180, '1y': 365}
                    dias_simulacion = dias_map.get(periodo, 60)
                    
                    # Ejecutar simulación (devuelve solo equity_curve)
                    equity_curve = ejecutar_simulacion(
                        capital_inicial=capital_inicial,
                        dias_simulacion=dias_simulacion,
                        apalancamiento=leverage if usar_leverage else 1
                    )
                    
                    # Analizar resultados del archivo CSV generado
                    metricas = analizar_resultados()
                    
                    if metricas and equity_curve:
                        # Mostrar métricas generales
                        st.subheader("📊 Resultados del Backtesting")
                    
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Total Trades", metricas['total_trades'])
                        with col2:
                            st.metric("Win Rate", f"{metricas['win_rate']:.1f}%")
                        with col3:
                            st.metric("Profit Factor", f"{metricas['profit_factor']:.2f}")
                        with col4:
                            ganancia_pct = ((equity_curve[-1]['Capital'] / capital_inicial) - 1) * 100 if equity_curve else 0
                            st.metric("Retorno Total", f"{ganancia_pct:+.2f}%")
                        
                        # Mostrar gráfico de equity curve
                        if equity_curve:
                            st.subheader("📈 Curva de Capital")
                            equity_df = pd.DataFrame(equity_curve)
                            
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=equity_df['Fecha'],
                                y=equity_df['Capital'],
                                mode='lines',
                                name='Capital',
                                line=dict(color='#0ECB81', width=2)
                            ))
                            
                            fig.update_layout(
                                title="Evolución del Capital",
                                xaxis_title="Fecha",
                                yaxis_title="Capital ($)",
                                template='plotly_dark',
                                height=400
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Mostrar métricas adicionales
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Ganancia Neta USD", f"${metricas['ganancia_neta_usd']:,.2f}")
                        with col2:
                            max_dd = min(equity_df['Drawdown']) if 'Drawdown' in equity_df.columns else 0
                            st.metric("Max Drawdown", f"{max_dd:.2f}%")
                    else:
                        st.warning("No se generaron trades en el período seleccionado")
    
    elif pagina == "🤖 Live Bot Monitor":
        st.header("🤖 Monitor del Bot en Vivo")
        
        # Estado del bot
        bot_status = "🟢 Activo" if os.path.exists('.bot_running') else "🔴 Detenido"
        st.metric("Estado del Bot", bot_status)
        
        # Controles
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ Iniciar Bot"):
                st.success("Bot iniciado! Ejecuta: python3 signal_bot_advanced.py")
                
        with col2:
            if st.button("⏹️ Detener Bot"):
                st.info("Para detener el bot, presiona Ctrl+C en la terminal")
        
        # Últimas señales
        if os.path.exists(f"signals_{datetime.now().strftime('%Y%m%d')}.json"):
            with open(f"signals_{datetime.now().strftime('%Y%m%d')}.json", 'r') as f:
                signals = json.load(f)
                
            st.subheader("📡 Últimas Señales Enviadas")
            for signal in signals[-5:]:  # Últimas 5
                st.markdown(f"""
                <div class="signal-card">
                    {signal['ticker']} - {signal['direccion']} - Score: {signal['score']}
                    <br>Entrada: ${signal['price']:.4f} | SL: ${signal['stop_loss']:.4f} | TP: ${signal['take_profit']:.4f}
                    <br>Hora: {signal['timestamp']}
                </div>
                """, unsafe_allow_html=True)
    
    elif pagina == "📋 Trade Tracker":
        st.header("📋 Seguimiento de Trades")
        st.markdown("Sistema automático de tracking y análisis de performance")
        
        mostrar_trade_tracker()
    
    elif pagina == "⚙️ Configuración":
        st.header("⚙️ Configuración del Sistema")
        
        # Cargar configuración actual
        config_file = 'signal_config.json'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            st.error("No se encontró archivo de configuración")
            return
        
        st.subheader("📡 Canales de Notificación")
        
        # Telegram
        with st.expander("Telegram"):
            telegram_enabled = st.checkbox("Activar Telegram", value=config['telegram']['enabled'])
            if telegram_enabled:
                bot_token = st.text_input("Bot Token", value=config['telegram']['bot_token'])
                chat_id = st.text_input("Chat ID", value=config['telegram']['chat_id'])
        
        st.subheader("🎯 Filtros de Señales")
        
        min_score = st.slider("Score Mínimo", 1, 10, config['filters']['min_score'])
        cooldown = st.number_input("Cooldown (minutos)", value=config['filters']['cooldown_minutes'])
        
        if st.button("💾 Guardar Configuración"):
            # Actualizar config
            config['telegram']['enabled'] = telegram_enabled
            if telegram_enabled:
                config['telegram']['bot_token'] = bot_token
                config['telegram']['chat_id'] = chat_id
            config['filters']['min_score'] = min_score
            config['filters']['cooldown_minutes'] = cooldown
            
            # Guardar
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            st.success("✅ Configuración guardada!")

if __name__ == "__main__":
    main()