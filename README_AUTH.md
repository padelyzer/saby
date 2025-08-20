# Sistema de Autenticación para Trading Bot

## 🔐 Características

- **Autenticación simple** con 2 usuarios predefinidos
- **Sesiones persistentes** válidas por 24 horas
- **Decoradores de protección** para funciones críticas
- **Registro de accesos** (audit log)
- **Gestión de contraseñas** con hash SHA-256

## 👥 Usuarios Por Defecto

⚠️ **IMPORTANTE:** Cambia estas contraseñas inmediatamente después de la primera instalación.

| Usuario | Contraseña | Permisos |
|---------|------------|----------|
| admin | admin2024! | Acceso completo, puede cambiar configuración |
| trader | trader2024! | Acceso a trading, sin configuración |

## 📁 Archivos Creados

1. **`auth_system.py`** - Sistema de autenticación principal
2. **`protected_trading_system.py`** - Sistema de trading con autenticación integrada
3. **`test_auth.py`** - Script de prueba del sistema
4. **`auth_config.json`** - Configuración de usuarios (creado automáticamente)
5. **`session.json`** - Datos de sesión actual (creado al hacer login)
6. **`trading_access_log.json`** - Registro de accesos (creado al usar el sistema)

## 🚀 Uso Básico

### 1. Gestión de Usuarios (CLI)

```bash
python3 auth_system.py
```

Opciones disponibles:
- Login
- Logout
- Cambiar contraseña
- Ver estado de sesión

### 2. Sistema de Trading Protegido

```bash
python3 protected_trading_system.py
```

El sistema pedirá autenticación antes de permitir acceso a:
- Escaneo de señales
- Visualización de portafolio
- Ejecución de backtest
- Cambio de configuración (solo admin)

### 3. Proteger Funciones Propias

```python
from auth_system import require_login

@require_login
def mi_funcion_protegida():
    # Esta función requiere autenticación
    return "Datos sensibles"
```

## 🔒 Cambiar Contraseñas

### Método 1: Usando el CLI

```bash
python3 auth_system.py
# Seleccionar opción 3 (Cambiar contraseña)
```

### Método 2: Programáticamente

```python
from auth_system import auth

# Primero hacer login
auth.login("admin", "admin2024!")

# Cambiar contraseña
auth.change_password("admin", "admin2024!", "nueva_contraseña_segura")
```

## 📊 Registro de Accesos

Todas las acciones importantes se registran en `trading_access_log.json`:

```json
{
  "timestamp": "2024-08-20T...",
  "user": "admin",
  "action": "scan_signals",
  "details": null
}
```

## 🔄 Integración con Sistema Existente

Para proteger tu sistema actual:

1. **Importa el decorador:**
```python
from auth_system import require_login
```

2. **Protege funciones críticas:**
```python
@require_login
def ejecutar_trade():
    # Tu código aquí
    pass
```

3. **Verifica usuario actual:**
```python
from auth_system import auth

user = auth.get_current_user()
if user == "admin":
    # Permitir acciones administrativas
    pass
```

## ⚙️ Configuración Avanzada

### Cambiar duración de sesión

En `auth_system.py`, modifica:
```python
self.session_duration = timedelta(hours=24)  # Cambiar a lo deseado
```

### Añadir más usuarios

Edita `auth_config.json` manualmente o mediante código:
```python
config = auth._load_config()
config['users']['nuevo_usuario'] = auth._hash_password('contraseña')
# Guardar config...
```

## 🛡️ Seguridad

- Las contraseñas se almacenan con hash SHA-256
- Los tokens de sesión son generados con `secrets.token_hex()`
- Las sesiones expiran automáticamente después de 24 horas
- Límite de 3 intentos de login fallidos

## 📝 Notas Importantes

1. **NO commitees** `auth_config.json` con contraseñas reales
2. **Añade a .gitignore:**
   ```
   auth_config.json
   session.json
   trading_access_log.json
   ```
3. **Cambia las contraseñas por defecto** inmediatamente
4. **Revisa el log de accesos** regularmente

## 🆘 Solución de Problemas

- **"No hay sesión activa"**: Ejecuta login primero
- **"Acceso denegado"**: Verifica credenciales o permisos de usuario
- **Sesión expirada**: Vuelve a hacer login

## 📞 Soporte

Para problemas o preguntas sobre el sistema de autenticación, revisa los logs en `trading_access_log.json` para diagnóstico.