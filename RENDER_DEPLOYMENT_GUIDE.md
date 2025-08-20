# 📚 Guía de Deployment en Render.com - botphIA v1.05

## 🎯 Pre-requisitos

1. **Cuenta en Render.com** (gratis para empezar)
2. **Repositorio GitHub** con el código del proyecto
3. **Cuenta Binance** con API keys (opcional para trading real)

## 📁 Estructura del Proyecto

```
saby/
├── botphia/              # Frontend React
│   ├── src/
│   ├── package.json
│   └── .env.production
├── trading_api/          # Backend FastAPI
│   ├── fastapi_server.py
│   ├── requirements.txt
│   └── start_production.py
└── botphia-render.yaml   # Configuración Render
```

## 🚀 Pasos de Deployment

### Paso 1: Preparar Repositorio GitHub

1. Crear nuevo repositorio en GitHub:
```bash
git init
git add .
git commit -m "Initial commit - botphIA v1.05"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/botphia.git
git push -u origin main
```

### Paso 2: Configurar Render.com

1. **Crear cuenta** en [render.com](https://render.com)
2. **Conectar GitHub** desde Dashboard → New → Connect GitHub
3. **Autorizar acceso** al repositorio `botphia`

### Paso 3: Deploy con Blueprint (Recomendado)

1. En Render Dashboard, click **"New"** → **"Blueprint"**
2. Seleccionar tu repositorio
3. Apuntar al archivo `botphia-render.yaml`
4. Click **"Apply"**

Render creará automáticamente:
- ✅ Base de datos PostgreSQL
- ✅ Backend API
- ✅ Frontend estático

### Paso 4: Configurar Variables de Entorno

#### En el servicio `botphia-api`:

1. Ir a **Environment** → **Environment Variables**
2. Agregar las siguientes variables:

```env
# Binance API (para trading real)
BINANCE_API_KEY=tu_api_key_aqui
BINANCE_SECRET_KEY=tu_secret_key_aqui

# JWT Secret (se genera automáticamente)
JWT_SECRET_KEY=<auto-generado>

# CORS (actualizar después del deploy)
ALLOWED_ORIGINS=https://botphia-web.onrender.com
```

### Paso 5: Actualizar URLs en Frontend

1. Después del primer deploy, obtener las URLs:
   - Backend: `https://botphia-api.onrender.com`
   - Frontend: `https://botphia-web.onrender.com`

2. Actualizar archivo `botphia/.env.production`:
```env
VITE_API_URL=https://botphia-api.onrender.com
VITE_WS_URL=wss://botphia-api.onrender.com/ws
```

3. Commit y push:
```bash
git add botphia/.env.production
git commit -m "Update production URLs"
git push
```

### Paso 6: Crear Usuarios Iniciales

Una vez desplegado, crear los usuarios con curl:

```bash
# Usuario 1
curl -X POST https://botphia-api.onrender.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "aurbaez@botphia.com",
    "password": "Profitz2025!",
    "full_name": "Alejandro Urbaez"
  }'

# Usuario 2
curl -X POST https://botphia-api.onrender.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jalcazar@botphia.com",
    "password": "Profitz2025!",
    "full_name": "Jorge Alcazar"
  }'
```

## 🔍 Verificación Post-Deploy

### 1. Verificar Backend
```bash
curl https://botphia-api.onrender.com/
# Debe retornar: {"status":"online","version":"1.05"}
```

### 2. Verificar Frontend
- Navegar a: `https://botphia-web.onrender.com`
- Debe mostrar el login de botphIA

### 3. Probar Login
- Email: `aurbaez@botphia.com` o `jalcazar@botphia.com`
- Password: `Profitz2025!`

### 4. Verificar WebSocket
```javascript
// En consola del navegador
const ws = new WebSocket('wss://botphia-api.onrender.com/ws');
ws.onopen = () => console.log('WebSocket conectado!');
```

## 🛠️ Mantenimiento

### Ver Logs
1. Dashboard Render → Servicio → **Logs**
2. Filtrar por nivel: Info, Warning, Error

### Reiniciar Servicio
1. Dashboard → Servicio → **Manual Deploy** → **Deploy**

### Escalar Recursos (Producción)
1. Cambiar plan de `free` a `starter` ($7/mes):
   - Base de datos: Mayor capacidad
   - API: Sin sleep después de 15 min
   - Frontend: Mayor ancho de banda

### Backup Base de Datos
```bash
# Desde Render Dashboard → Database → Backups
# O usando pg_dump:
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

## 🚨 Troubleshooting

### Error: "502 Bad Gateway"
- **Causa**: Backend no iniciado
- **Solución**: Verificar logs del backend, reiniciar servicio

### Error: "CORS blocked"
- **Causa**: URLs no actualizadas
- **Solución**: Actualizar `ALLOWED_ORIGINS` en variables de entorno

### Error: "Database connection failed"
- **Causa**: PostgreSQL no configurado
- **Solución**: Verificar `DATABASE_URL` en variables de entorno

### Error: "WebSocket connection failed"
- **Causa**: WSS URL incorrecta
- **Solución**: Actualizar `VITE_WS_URL` en frontend

## 📊 Monitoreo

### Métricas Disponibles
- **CPU & Memory**: Dashboard → Metrics
- **Request count**: Dashboard → Web Service → Metrics
- **Database connections**: Dashboard → Database → Metrics

### Alertas Recomendadas
1. CPU > 80% por más de 5 minutos
2. Memory > 450MB (límite free tier: 512MB)
3. Error rate > 1%
4. Response time > 2 segundos

## 🔒 Seguridad

### Checklist de Seguridad
- ✅ JWT_SECRET_KEY generado aleatoriamente
- ✅ HTTPS habilitado automáticamente
- ✅ Variables sensibles en Environment Variables
- ✅ Rate limiting configurado
- ✅ CORS restrictivo a dominio específico
- ✅ Binance keys solo en producción

### Rotación de Secretos
```bash
# Generar nuevo JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Actualizar en Render Dashboard
```

## 📝 Comandos Útiles

### Desarrollo Local
```bash
# Backend
cd trading_api
python -m uvicorn fastapi_server:app --reload

# Frontend
cd botphia
npm run dev
```

### Producción
```bash
# Ver estado de servicios
curl https://botphia-api.onrender.com/health

# Test completo
npm run test:production
```

## 🎉 ¡Deployment Completado!

Tu sistema botphIA v1.05 está ahora en producción en:
- 🌐 **Frontend**: https://botphia-web.onrender.com
- 🔧 **Backend**: https://botphia-api.onrender.com
- 🗄️ **Database**: PostgreSQL en Render

## 📞 Soporte

- **Render Status**: https://status.render.com
- **Render Docs**: https://render.com/docs
- **botphIA Issues**: GitHub Issues del repositorio