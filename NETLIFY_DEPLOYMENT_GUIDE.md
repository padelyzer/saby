# 🚀 Guía de Deployment Híbrido: Netlify + Backend

## 📋 Resumen de Compatibilidad

### ✅ Compatible con Netlify:
- Frontend React (botphIA UI)
- Routing del cliente
- Assets estáticos
- HTTPS automático

### ❌ NO Compatible con Netlify:
- Backend Python/FastAPI
- WebSockets
- Base de datos
- Trading bot activo

## 🎯 Solución Recomendada: Netlify + Supabase

### Paso 1: Deploy Frontend en Netlify

1. **Crear cuenta en Netlify**
   - Ve a [netlify.com](https://netlify.com)
   - Regístrate con GitHub

2. **Conectar repositorio**
   ```bash
   # Opción A: Desde Netlify UI
   New site from Git → GitHub → padelyzer/saby
   
   # Opción B: Desde CLI
   npm install -g netlify-cli
   netlify init
   netlify deploy --prod
   ```

3. **Configuración de build**
   - Base directory: `botphia`
   - Build command: `npm run build`
   - Publish directory: `botphia/dist`

4. **Variables de entorno**
   ```
   VITE_API_URL=https://tu-backend.supabase.co
   VITE_WS_URL=wss://tu-backend.supabase.co
   ```

### Paso 2: Backend en Supabase

1. **Crear proyecto en Supabase**
   - Ve a [supabase.com](https://supabase.com)
   - Create new project (gratis)

2. **Configurar base de datos**
   ```sql
   -- Crear tablas en Supabase SQL Editor
   CREATE TABLE users (
     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
     email TEXT UNIQUE NOT NULL,
     password_hash TEXT NOT NULL,
     full_name TEXT,
     created_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE positions (
     id TEXT PRIMARY KEY,
     user_id UUID REFERENCES users(id),
     symbol TEXT NOT NULL,
     entry_price DECIMAL,
     quantity DECIMAL,
     status TEXT DEFAULT 'OPEN',
     created_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE signals (
     id TEXT PRIMARY KEY,
     user_id UUID REFERENCES users(id),
     symbol TEXT NOT NULL,
     action TEXT NOT NULL,
     confidence DECIMAL,
     timestamp TIMESTAMP DEFAULT NOW()
   );
   ```

3. **Crear Edge Functions**
   ```typescript
   // supabase/functions/trading-api/index.ts
   import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
   import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

   serve(async (req) => {
     const supabase = createClient(
       Deno.env.get('SUPABASE_URL')!,
       Deno.env.get('SUPABASE_ANON_KEY')!
     )

     const { method, url } = req
     const path = new URL(url).pathname

     // Auth endpoints
     if (path === '/api/auth/login' && method === 'POST') {
       const { email, password } = await req.json()
       const { data, error } = await supabase.auth.signInWithPassword({
         email,
         password
       })
       return new Response(JSON.stringify(data), {
         headers: { 'Content-Type': 'application/json' }
       })
     }

     // Trading endpoints
     if (path === '/api/positions' && method === 'GET') {
       const { data } = await supabase
         .from('positions')
         .select('*')
       return new Response(JSON.stringify(data), {
         headers: { 'Content-Type': 'application/json' }
       })
     }

     return new Response('Not Found', { status: 404 })
   })
   ```

4. **Deploy Edge Function**
   ```bash
   supabase functions deploy trading-api
   ```

## 🔄 Alternativas de Backend Gratuitas

### Opción 1: Railway ($5/mes gratis)
```bash
# Deploy backend
cd trading_api
railway login
railway init
railway add
railway up
```

### Opción 2: Deta Space (100% gratis)
```bash
# Install Deta
curl -fsSL https://get.deta.dev/space-cli.sh | sh

# Deploy
cd trading_api
space new
space push
```

### Opción 3: Cyclic.sh (gratis)
```bash
# Deploy desde GitHub
# 1. Ve a cyclic.sh
# 2. Connect GitHub
# 3. Select repo
# 4. Deploy
```

## 📊 Comparación de Opciones

| Servicio | Frontend | Backend | DB | WebSocket | Costo |
|----------|----------|---------|-----|-----------|-------|
| **Netlify + Supabase** | ✅ | ✅ | ✅ | ✅ Realtime | Gratis |
| **Netlify + Railway** | ✅ | ✅ | ✅ | ✅ | $5 gratis/mes |
| **Netlify + Deta** | ✅ | ✅ | ✅ NoSQL | ❌ | Gratis |
| **Render (1 servicio)** | ✅ | ✅ | ✅ SQLite | ✅ | Gratis* |

*Render ahora pide tarjeta

## 🚀 Comandos Rápidos

### Deploy Frontend en Netlify
```bash
# Instalar CLI
npm install -g netlify-cli

# Login
netlify login

# Deploy
cd botphia
netlify deploy --prod --dir=dist
```

### Actualizar después de cambios
```bash
git add .
git commit -m "Update"
git push
# Netlify actualiza automáticamente
```

## 🔧 Configuración Final

1. **Frontend (Netlify)**
   - URL: `https://botphia.netlify.app`
   - Auto-deploy desde GitHub

2. **Backend (Supabase/Railway/Deta)**
   - API: `https://tu-backend.ejemplo.com`
   - WebSocket: `wss://tu-backend.ejemplo.com`

3. **Usuarios**
   ```javascript
   // Crear usuarios desde frontend
   aurbaez@botphia.com / Profitz2025!
   jalcazar@botphia.com / Profitz2025!
   ```

## ⚡ Ventajas de esta arquitectura

- ✅ Frontend ultra rápido con CDN global
- ✅ Backend escalable independiente
- ✅ Sin tarjeta de crédito
- ✅ HTTPS automático
- ✅ Deploy automático con git push
- ✅ Separación de responsabilidades

## 🎯 Recomendación Final

**Para botphIA recomiendo:**

1. **Netlify** para frontend (gratis, rápido, confiable)
2. **Supabase** para backend (PostgreSQL, auth, realtime, gratis)

Esta combinación te da todo lo necesario sin costo y sin tarjeta de crédito.