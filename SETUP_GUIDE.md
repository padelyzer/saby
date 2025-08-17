# 🚀 GUÍA DE SETUP - Trading Bot V2.5 en Render + Telegram

## 📋 PREPARACIÓN (5 minutos)

### 1. **CREAR BOT DE TELEGRAM**
```
1. Abrir Telegram y buscar: @BotFather
2. Enviar: /newbot
3. Nombre del bot: "Trading Bot V2.5"
4. Username: "tu_trading_bot_v25"
5. COPIAR EL TOKEN que te da (ej: 123456789:ABC...)
```

### 2. **OBTENER CHAT ID**
```
1. Enviar cualquier mensaje a tu bot
2. Ir a: https://api.telegram.org/bot<TU_TOKEN>/getUpdates
3. Buscar "chat":{"id": 123456789}
4. COPIAR EL CHAT ID
```

## 🌐 DEPLOYMENT EN RENDER (10 minutos)

### 1. **PREPARAR ARCHIVOS**
```bash
# Archivos necesarios (ya los tienes):
main_trading_bot.py     # Sistema principal
requirements.txt        # Dependencias
render.yaml            # Configuración Render
```

### 2. **CREAR REPOSITORIO EN GITHUB**
```bash
# En tu terminal:
git init
git add .
git commit -m "Trading Bot V2.5 - Initial commit"

# Crear repo en GitHub y hacer push:
git remote add origin https://github.com/tu-usuario/trading-bot-v25.git
git push -u origin main
```

### 3. **CONECTAR A RENDER**
```
1. Ir a: https://render.com
2. Crear cuenta / Login
3. Click "New" → "Background Worker"
4. Conectar tu repositorio GitHub
5. Seleccionar: trading-bot-v25
```

### 4. **CONFIGURAR VARIABLES DE ENTORNO**
```
En Render Dashboard:
1. Environment Variables:

   TELEGRAM_BOT_TOKEN = 123456789:ABC... (el que copiaste de BotFather)
   TELEGRAM_CHAT_ID = 123456789 (el que copiaste de getUpdates)

2. Click "Create Background Worker"
```

## ✅ VERIFICACIÓN (2 minutos)

### 1. **REVISAR LOGS EN RENDER**
```
Dashboard → Services → trading-bot-v25 → Logs

Deberías ver:
🚀 Trading Bot V2.5 iniciado en Render
✅ Telegram configurado correctamente
🔄 Iniciando ciclo de trading...
⏱️ Esperando 15 minutos...
```

### 2. **REVISAR TELEGRAM**
```
Tu bot debería enviarte:
🚀 BOT INICIADO

✅ Sistema V2.5 funcionando
💰 Capital inicial: $10,000
🎯 Símbolos: BTC, ETH, SOL, BNB, ADA
📊 Parámetros validados (70% WR)

⏰ 2024-12-17 14:23:45
```

## 📱 FUNCIONAMIENTO DIARIO

### **LO QUE RECIBIRÁS EN TELEGRAM:**

#### 🎯 NUEVA SEÑAL (cuando hay oportunidad)
```
🟢 NUEVA SEÑAL

📊 Símbolo: BTC-USD
📈 Tipo: LONG
💰 Entry: $43,247.89
🎯 Confianza: 67.5%

🛡️ Stop Loss: $41,805.23
🎊 Take Profit: $46,132.67

🔍 Señales: RSI_OVERSOLD, MACD_BULLISH, UPTREND

⏰ 14:23:15
```

#### ✅ TRADE CERRADO (cuando se cierra posición)
```
✅ TRADE CERRADO

📊 Símbolo: BTC-USD
📈 Resultado: TAKE_PROFIT
💰 P&L: $245.67 (+3.68%)
🕐 Duración: 3.2h

📍 Entry → Exit: $43,247.89 → $44,832.45

⏰ 17:35:22
```

#### 📊 RESUMEN DIARIO (cada mañana 9:00 AM)
```
📈 RESUMEN DIARIO

💰 P&L Total: $1,247.89
📈 ROI: +12.48%
🎯 Win Rate: 68.5%
📊 Trades: 15
⚡ Profit Factor: 2.34
💼 Capital: $11,247.89

🤖 Trading Bot V2.5
```

## 🔧 CONFIGURACIÓN AVANZADA (Opcional)

### **CAMBIAR INTERVALO DE REVISIÓN**
```python
# En main_trading_bot.py línea 28:
'check_interval_minutes': 15,  # Cambiar a 5, 10, 30, etc.
```

### **AJUSTAR NÚMERO MÁXIMO DE TRADES**
```python
# En main_trading_bot.py línea 32:
'max_daily_trades': 5,  # Cambiar a 3, 7, 10, etc.
```

### **MODIFICAR SÍMBOLOS**
```python
# En main_trading_bot.py línea 36:
self.symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'ADA-USD']
# Agregar: 'MATIC-USD', 'AVAX-USD', etc.
```

## 🛡️ MONITOREO Y MANTENIMIENTO

### **REVISAR SISTEMA**
```
1. Logs en Render: Dashboard → Services → Logs
2. Telegram: Recibirás notificaciones automáticas
3. Performance: Resumen diario automático
```

### **REINICIAR SI ES NECESARIO**
```
Render Dashboard → Services → Manual Deploy
```

### **PAUSAR TEMPORALMENTE**
```
Render Dashboard → Services → Suspend
```

## 📊 MÉTRICAS ESPERADAS

Basado en backtesting validado:
- **Win Rate:** ~70%
- **Profit Factor:** ~3.5
- **Trades por día:** 1-3
- **Trades contra-tendencia:** 0%

## 🚨 TROUBLESHOOTING

### **No recibo mensajes de Telegram**
```
1. Verificar TELEGRAM_BOT_TOKEN en Render
2. Verificar TELEGRAM_CHAT_ID en Render
3. Enviar mensaje al bot primero
4. Revisar logs de Render para errores
```

### **Bot no funciona**
```
1. Revisar logs en Render
2. Verificar que yfinance funciona
3. Check variables de entorno
4. Redeploy si es necesario
```

### **Demasiadas/Pocas señales**
```
1. Ajustar min_confidence (línea 31)
2. Modificar max_daily_trades (línea 32)
3. Cambiar check_interval_minutes (línea 28)
```

---

## ✅ CHECKLIST FINAL

- [ ] Bot de Telegram creado
- [ ] TOKEN y CHAT_ID obtenidos
- [ ] Repositorio en GitHub
- [ ] Render configurado
- [ ] Variables de entorno añadidas
- [ ] Bot desplegado y funcionando
- [ ] Mensaje de inicio recibido en Telegram
- [ ] Logs verificados en Render

🎉 **¡Listo! Tu Trading Bot V2.5 está funcionando 24/7**