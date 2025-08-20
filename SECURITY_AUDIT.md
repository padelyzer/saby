# 🔒 AUDITORÍA DE SEGURIDAD - botphIA v1.05
**Fecha:** 20 de Agosto, 2025  
**Estado:** ⚠️ REQUIERE REMEDIACIÓN ANTES DE PRODUCCIÓN

---

## 🚨 PROBLEMAS CRÍTICOS ENCONTRADOS

### 1. **🔴 CREDENCIALES HARDCODEADAS**
**Severidad:** CRÍTICA  
**Ubicación:** 
- `auth_manager.py:11` - Secret key hardcodeado: `"botphia_secret_key_2025"`
- `fastapi_server.py:1623-1624` - Usuarios y contraseñas demo hardcodeados

**Impacto:** Cualquiera con acceso al código puede:
- Falsificar tokens JWT
- Conocer credenciales de usuarios

**REMEDIACIÓN URGENTE:**
```python
# auth_manager.py - CAMBIAR A:
import os
secret_key = os.getenv("JWT_SECRET_KEY", None)
if not secret_key:
    raise ValueError("JWT_SECRET_KEY no configurado")
```

---

### 2. **🔴 BASE DE DATOS SIN AUTENTICACIÓN**
**Severidad:** ALTA  
**Ubicación:** SQLite sin contraseña en `trading_bot.db`

**Impacto:** 
- Base de datos accesible directamente
- Sin encriptación de datos sensibles
- Posiciones y balances en texto plano

**REMEDIACIÓN:**
```python
# Opción 1: Migrar a PostgreSQL con autenticación
# Opción 2: Encriptar SQLite con sqlcipher
# Opción 3: Al menos, mover fuera del directorio web
```

---

### 3. **🟡 MEZCLA DE CONEXIONES A BD**
**Severidad:** MEDIA  
**Problema:** Inconsistencia en manejo de base de datos
- `database.py` usa su propia instancia
- `fastapi_server.py:1832, 1916` abre conexiones directas
- Sin pool de conexiones
- Sin manejo de transacciones

**REMEDIACIÓN:**
```python
# Usar SOLO la instancia de database.py
from database import db
# NUNCA usar sqlite3.connect() directamente
```

---

### 4. **🟡 CORS MUY PERMISIVO**
**Severidad:** MEDIA  
**Ubicación:** `fastapi_server.py`
```python
allow_origins=["http://localhost:5173", "http://localhost:5174"]
```

**REMEDIACIÓN para producción:**
```python
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Solo dominios específicos
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Solo métodos necesarios
    allow_headers=["Authorization", "Content-Type"],
)
```

---

### 5. **🟡 TOKENS SIN REFRESH**
**Severidad:** MEDIA  
**Problema:** Tokens JWT expiran en 7 días sin refresh token

**REMEDIACIÓN:**
```python
# Implementar refresh tokens
# Reducir expiración a 1 hora para access token
# Refresh token de 30 días
```

---

## 📊 ANÁLISIS DE CONEXIONES A BASE DE DATOS

### Archivos que acceden a la BD:
1. **database.py** ✅ - Clase centralizada `TradingDatabase`
2. **fastapi_server.py** ⚠️ - Conexiones directas en líneas 1832, 1916
3. **binance_integration.py** ❓ - Verificar si accede

### Estado de Tablas:
- `positions` - ✅ Incluye user_id
- `signals` - ✅ Incluye user_id  
- `performance` - ✅ Incluye user_id
- `alerts` - ✅ Incluye user_id
- `user_config` - ✅ Nueva tabla para configuración

---

## 🛡️ CHECKLIST DE SEGURIDAD PRE-PRODUCCIÓN

### CRÍTICO (Hacer antes de publicar):
- [ ] ⚠️ Mover secret keys a variables de entorno
- [ ] ⚠️ Eliminar usuarios hardcodeados
- [ ] ⚠️ Configurar CORS restrictivo
- [ ] ⚠️ Validar todos los inputs del usuario
- [ ] ⚠️ Implementar rate limiting
- [ ] ⚠️ Agregar HTTPS obligatorio

### IMPORTANTE:
- [ ] Implementar refresh tokens
- [ ] Agregar logging de auditoría
- [ ] Encriptar datos sensibles en BD
- [ ] Implementar backup automático de BD
- [ ] Agregar monitoreo de errores (Sentry)
- [ ] Configurar límites de memoria/CPU

### RECOMENDADO:
- [ ] Migrar a PostgreSQL
- [ ] Implementar Redis para sesiones
- [ ] Agregar 2FA opcional
- [ ] Implementar API versioning
- [ ] Agregar health checks
- [ ] Documentar API con OpenAPI

---

## 🔧 SCRIPT DE REMEDIACIÓN RÁPIDA

```bash
# 1. Crear archivo .env
cat > /Users/ja/saby/trading_api/.env << EOF
JWT_SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite:///./trading_bot.db
ALLOWED_ORIGINS=http://localhost:5173
BINANCE_API_KEY=your_key_here
BINANCE_SECRET_KEY=your_secret_here
ENVIRONMENT=development
EOF

# 2. Instalar python-dotenv
pip install python-dotenv

# 3. Actualizar permisos de BD
chmod 600 trading_bot.db
```

---

## 📝 CÓDIGO DE REMEDIACIÓN

### 1. Crear archivo `config.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Seguridad
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY no configurado")
    
    # Base de datos
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./trading_bot.db")
    
    # CORS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
    
    # Binance
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")
    
    # Ambiente
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    IS_PRODUCTION = ENVIRONMENT == "production"
    
    # Usuarios (solo para desarrollo)
    if not IS_PRODUCTION:
        DEMO_USERS = {
            "aurbaez@botphia.com": {
                "id": "user_1",
                "password": os.getenv("DEMO_PASSWORD", "change_me"),
                "name": "Aurora Báez",
                "role": "admin"
            }
        }
    else:
        DEMO_USERS = {}

settings = Settings()
```

### 2. Pool de Conexiones para SQLite:
```python
import sqlite3
from contextlib import contextmanager
from threading import Lock

class DatabasePool:
    def __init__(self, db_path, max_connections=5):
        self.db_path = db_path
        self.lock = Lock()
    
    @contextmanager
    def get_connection(self):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()

db_pool = DatabasePool("trading_bot.db")
```

---

## 🚀 PASOS PARA PRODUCCIÓN

### 1. **Inmediato (5 minutos):**
```bash
# Crear .env con secrets seguros
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" > .env
echo "DATABASE_URL=sqlite:///./secure_trading.db" >> .env
```

### 2. **Antes de publicar (30 minutos):**
- Reemplazar todos los hardcoded secrets
- Mover BD fuera del directorio público
- Configurar CORS restrictivo
- Eliminar usuarios demo

### 3. **Primera semana:**
- Implementar refresh tokens
- Agregar rate limiting
- Configurar HTTPS
- Implementar logging

### 4. **Primer mes:**
- Migrar a PostgreSQL
- Agregar Redis
- Implementar 2FA
- Configurar monitoreo

---

## ⚡ COMANDO DE VERIFICACIÓN

```bash
# Verificar que no queden secrets en el código
grep -r "password\|secret\|api_key" --exclude-dir=node_modules --exclude-dir=.git --exclude="*.md" .

# Verificar permisos de BD
ls -la *.db

# Verificar variables de entorno
env | grep -E "JWT|DATABASE|API"
```

---

## 📞 CONTACTO PARA DUDAS
Si necesitas ayuda con la remediación, estos son los puntos críticos:
1. **Secrets en variables de entorno** - CRÍTICO
2. **Usuarios hardcodeados** - CRÍTICO  
3. **CORS restrictivo** - IMPORTANTE
4. **Pool de conexiones** - IMPORTANTE

**Estado Final:** ⚠️ NO LISTO PARA PRODUCCIÓN sin remediación