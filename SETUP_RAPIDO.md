# 🚀 Configuración Rápida - botphIA + Supabase

## ✅ Ya tienes tu cuenta de Supabase, ahora:

### 1️⃣ Ejecuta el SQL en Supabase
1. Abre tu proyecto en [Supabase Dashboard](https://app.supabase.com)
2. Ve a **SQL Editor** (icono de cilindro en el menú izquierdo)
3. Click en **New Query**
4. Copia TODO el contenido del archivo `supabase_setup.sql`
5. Pégalo en el editor
6. Click **RUN** (botón verde)
7. Deberías ver: "Setup completed! Tables created..."

### 2️⃣ Obtén tus credenciales
1. Ve a **Settings** → **API**
2. Copia estos valores:
   - **Project URL**: https://xxxxx.supabase.co
   - **anon public**: eyJhbGc... (clave larga)

### 3️⃣ Actualiza el archivo .env.local
```bash
cd /Users/ja/saby/botphia
nano .env.local
```

Reemplaza con tus valores:
```env
VITE_SUPABASE_URL=https://tu-proyecto.supabase.co
VITE_SUPABASE_ANON_KEY=tu-anon-key-aqui
```

### 4️⃣ Instala Supabase en el frontend
```bash
cd /Users/ja/saby/botphia
npm install @supabase/supabase-js
```

### 5️⃣ Deploy a Vercel
```bash
cd /Users/ja/saby

# Instalar Vercel CLI si no lo tienes
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Responde:
# - Set up and deploy? Y
# - Which scope? (tu cuenta)
# - Link to existing? N  
# - Project name? botphia
# - Directory? ./
# - Override? N
```

### 6️⃣ Configura variables en Vercel
Cuando termine el deploy, ejecuta:
```bash
# Agregar Supabase URL
vercel env add VITE_SUPABASE_URL
# Pega tu URL: https://xxxxx.supabase.co

# Agregar Supabase Key
vercel env add VITE_SUPABASE_ANON_KEY
# Pega tu anon key: eyJhbGc...

# JWT Secret (genera uno)
vercel env add JWT_SECRET_KEY
# Genera con: openssl rand -hex 32
```

### 7️⃣ Deploy de producción
```bash
vercel --prod
```

## ✅ Verificación

Tu app estará en: `https://botphia.vercel.app`

### Usuarios ya creados:
- **Email**: aurbaez@botphia.com
- **Password**: Profitz2025!

- **Email**: jalcazar@botphia.com  
- **Password**: Profitz2025!

## 🎯 URLs finales
- **Frontend**: https://botphia.vercel.app
- **Base de datos**: Dashboard de Supabase
- **API**: https://botphia.vercel.app/api

## ❓ ¿Problemas?

### Error: "Invalid credentials"
- Verifica que ejecutaste el SQL completo
- Los usuarios deben existir en la tabla

### Error: "Connection failed"
- Verifica VITE_SUPABASE_URL esté correcto
- Revisa que la key sea la "anon public"

### Error en Vercel
- Asegúrate de configurar TODAS las variables de entorno
- Haz `vercel env pull` para verificar

## 🚀 ¡Listo!

Tu sistema botphIA está configurado con:
- ✅ Frontend en Vercel
- ✅ Base de datos en Supabase
- ✅ Autenticación funcionando
- ✅ 100% gratis sin tarjeta