# 🚀 Guía de Deploy: Vercel + Supabase

## ✨ Por qué Vercel + Supabase es la MEJOR opción

### Ventajas sobre otras opciones:
- ✅ **Vercel API Routes**: Puedes ejecutar Python sin servidor separado
- ✅ **Supabase Realtime**: WebSockets incluidos gratis
- ✅ **PostgreSQL gratis**: 500MB incluidos
- ✅ **Auth integrada**: Login/registro sin código extra
- ✅ **Sin tarjeta**: 100% gratis para empezar
- ✅ **Escalable**: Crece con tu proyecto

## 📋 Arquitectura

```
┌─────────────────────┐       ┌──────────────────┐
│      VERCEL         │  API  │    SUPABASE      │
│                     │◄──────►                  │
│ • Frontend React    │       │ • PostgreSQL DB  │
│ • API Routes Python │       │ • Auth Service   │
│ • Edge Functions    │       │ • Realtime WS    │
│ • Global CDN        │       │ • Storage        │
│                     │       │                  │
│    GRATIS ✅        │       │   GRATIS ✅      │
└─────────────────────┘       └──────────────────┘
```

## 🛠️ PASO 1: Configurar Supabase

### 1.1 Crear proyecto
1. Ve a [supabase.com](https://supabase.com)
2. **Sign Up** con GitHub
3. **New Project**:
   - Project name: `botphia`
   - Database Password: (guárdala!)
   - Region: `East US (North Virginia)`
   - Click **Create new project**

### 1.2 Crear tablas
1. Ve a **SQL Editor** en Supabase
2. Ejecuta este SQL:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  full_name TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Positions table
CREATE TABLE positions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL,
  type TEXT NOT NULL,
  entry_price DECIMAL(18,8),
  current_price DECIMAL(18,8),
  quantity DECIMAL(18,8),
  stop_loss DECIMAL(18,8),
  take_profit DECIMAL(18,8),
  pnl DECIMAL(18,8) DEFAULT 0,
  pnl_percentage DECIMAL(5,2) DEFAULT 0,
  status TEXT DEFAULT 'OPEN',
  open_time TIMESTAMP DEFAULT NOW(),
  close_time TIMESTAMP,
  strategy TEXT,
  created_by TEXT DEFAULT 'system'
);

-- Signals table
CREATE TABLE signals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL,
  action TEXT NOT NULL,
  confidence DECIMAL(5,2),
  entry_price DECIMAL(18,8),
  stop_loss DECIMAL(18,8),
  take_profit DECIMAL(18,8),
  philosopher TEXT,
  reasoning TEXT,
  market_trend TEXT,
  rsi DECIMAL(5,2),
  volume_ratio DECIMAL(10,2),
  timestamp TIMESTAMP DEFAULT NOW(),
  executed BOOLEAN DEFAULT FALSE
);

-- User config table
CREATE TABLE user_config (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  initial_capital DECIMAL(18,2),
  current_balance DECIMAL(18,2),
  risk_level TEXT,
  risk_per_trade DECIMAL(5,2),
  max_positions INTEGER,
  symbols TEXT,
  philosophers TEXT,
  setup_completed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_positions_user_id ON positions(user_id);
CREATE INDEX idx_signals_user_id ON signals(user_id);
CREATE INDEX idx_positions_status ON positions(status);
CREATE INDEX idx_signals_timestamp ON signals(timestamp);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_config ENABLE ROW LEVEL SECURITY;

-- RLS Policies (users can only see their own data)
CREATE POLICY "Users can view own data" ON users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can view own positions" ON positions
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own signals" ON signals
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own config" ON user_config
  FOR ALL USING (auth.uid() = user_id);
```

### 1.3 Obtener credenciales
1. Ve a **Settings** → **API**
2. Copia:
   - `Project URL`: https://xxxxx.supabase.co
   - `anon public`: eyJhbGc...

## 🚀 PASO 2: Deploy en Vercel

### 2.1 Preparar el código
```bash
cd /Users/ja/saby

# Actualizar configuración del frontend
cd botphia
echo 'VITE_API_URL=/api
VITE_WS_URL=wss://xxxxx.supabase.co/realtime/v1
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGc...' > .env.production

cd ..
```

### 2.2 Instalar Vercel CLI
```bash
npm install -g vercel
```

### 2.3 Deploy
```bash
# Login a Vercel
vercel login

# Deploy (responde las preguntas)
vercel

# Preguntas típicas:
# Set up and deploy? Y
# Which scope? (tu cuenta)
# Link to existing project? N
# Project name? botphia
# Directory? ./
# Override settings? N
```

### 2.4 Configurar variables de entorno
```bash
# Agregar variables de Supabase
vercel env add SUPABASE_URL
# Pega: https://xxxxx.supabase.co

vercel env add SUPABASE_ANON_KEY
# Pega: eyJhbGc...

vercel env add JWT_SECRET_KEY
# Genera uno: openssl rand -hex 32
```

### 2.5 Deploy de producción
```bash
vercel --prod
```

## 📱 PASO 3: Crear usuarios iniciales

### Opción A: Desde la app
1. Abre: `https://botphia.vercel.app`
2. Click en "Register"
3. Crea los usuarios:
   - aurbaez@botphia.com / Profitz2025!
   - jalcazar@botphia.com / Profitz2025!

### Opción B: Con curl
```bash
# Usuario 1
curl -X POST https://botphia.vercel.app/api/auth \
  -H "Content-Type: application/json" \
  -d '{
    "action": "register",
    "email": "aurbaez@botphia.com",
    "password": "Profitz2025!",
    "full_name": "Alejandro Urbaez"
  }'

# Usuario 2
curl -X POST https://botphia.vercel.app/api/auth \
  -H "Content-Type: application/json" \
  -d '{
    "action": "register",
    "email": "jalcazar@botphia.com",
    "password": "Profitz2025!",
    "full_name": "Jorge Alcazar"
  }'
```

## 🔧 PASO 4: Configurar Trading Bot (Supabase Edge Function)

```typescript
// En Supabase Dashboard → Edge Functions → New Function
// Nombre: trading-bot

import { serve } from "https://deno.land/std/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  // Trading logic aquí
  // Fetch Binance data
  // Generate signals
  // Update positions

  return new Response(
    JSON.stringify({ status: 'running' }),
    { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
  )
})
```

## ✅ PASO 5: Verificación

### URLs finales:
- **Frontend + API**: https://botphia.vercel.app
- **Base de datos**: Supabase Dashboard
- **Realtime**: Conectado automáticamente

### Test de funcionamiento:
```bash
# Health check
curl https://botphia.vercel.app/api/health

# Login test
curl -X POST https://botphia.vercel.app/api/auth \
  -H "Content-Type: application/json" \
  -d '{"action":"login","email":"aurbaez@botphia.com","password":"Profitz2025!"}'
```

## 🎯 Ventajas de esta arquitectura

1. **Performance**: 
   - Vercel Edge Network (global)
   - Supabase en US-East
   - < 100ms latencia

2. **Escalabilidad**:
   - Auto-scaling incluido
   - Sin límites de usuarios

3. **Costo**:
   - Gratis hasta 100GB bandwidth
   - Gratis hasta 500MB DB

4. **Seguridad**:
   - HTTPS automático
   - Row Level Security
   - JWT tokens

## 🛠️ Comandos útiles

```bash
# Ver logs de Vercel
vercel logs

# Redeploy después de cambios
git push && vercel --prod

# Ver estado de Supabase
# Dashboard → Database → Health

# Monitorear en tiempo real
# Supabase Dashboard → Realtime → Inspector
```

## 📊 Monitoreo

### Vercel Analytics (gratis):
- Performance metrics
- Error tracking
- Usage statistics

### Supabase Dashboard:
- Query performance
- Database size
- Realtime connections

## 🚨 Troubleshooting

**Error: CORS**
- Verifica SUPABASE_URL en variables de entorno

**Error: Auth failed**
- Revisa JWT_SECRET_KEY coincida

**Error: Database connection**
- Verifica credenciales de Supabase

## 🎉 ¡Listo!

Tu sistema botphIA está corriendo en:
- 🌐 **App**: https://botphia.vercel.app
- 🗄️ **DB**: Supabase Dashboard
- 📊 **Analytics**: Vercel Dashboard

Sistema 100% gratuito, escalable y profesional.