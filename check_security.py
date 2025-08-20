#!/usr/bin/env python3
"""
Script de verificación de seguridad para botphIA
Ejecutar antes de publicar a producción
"""

import os
import sys
import re
import sqlite3
from pathlib import Path
from typing import List, Tuple

class SecurityChecker:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []
        
    def check_env_file(self) -> None:
        """Verifica que existe archivo .env"""
        if not Path('.env').exists():
            self.errors.append("❌ No existe archivo .env")
            self.warnings.append("   Crear desde .env.example")
        else:
            self.passed.append("✅ Archivo .env existe")
            
    def check_secrets_in_code(self) -> None:
        """Busca secretos hardcodeados en el código"""
        patterns = [
            (r'secret_key\s*=\s*["\'][\w\-]+["\']', 'Secret key hardcodeado'),
            (r'password\s*=\s*["\'][\w\!@#$%]+["\']', 'Password hardcodeado'),
            (r'api_key\s*=\s*["\'][\w\-]+["\']', 'API key hardcodeado'),
            (r'botphia_secret_key_2025', 'Secret key por defecto detectado'),
            (r'Profitz2025\!', 'Password demo en código'),
        ]
        
        exclude_dirs = {'.git', 'node_modules', '__pycache__', '.pytest_cache', 'venv', 'env'}
        exclude_files = {'check_security.py', '.env.example', 'SECURITY_AUDIT.md'}
        
        found_issues = []
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file in exclude_files or not file.endswith(('.py', '.ts', '.tsx', '.js')):
                    continue
                    
                filepath = Path(root) / file
                try:
                    content = filepath.read_text()
                    for pattern, description in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            found_issues.append(f"   {filepath}: {description}")
                except:
                    pass
        
        if found_issues:
            self.errors.append("❌ Secretos hardcodeados encontrados:")
            self.errors.extend(found_issues)
        else:
            self.passed.append("✅ No se encontraron secretos hardcodeados")
    
    def check_database_permissions(self) -> None:
        """Verifica permisos de la base de datos"""
        db_files = list(Path('.').glob('*.db'))
        
        for db_file in db_files:
            stat = db_file.stat()
            permissions = oct(stat.st_mode)[-3:]
            
            if permissions != '600':
                self.warnings.append(f"⚠️ {db_file} tiene permisos {permissions} (recomendado: 600)")
                self.warnings.append(f"   Ejecutar: chmod 600 {db_file}")
            else:
                self.passed.append(f"✅ {db_file} tiene permisos correctos")
    
    def check_database_structure(self) -> None:
        """Verifica estructura de la base de datos"""
        if not Path('trading_bot.db').exists():
            self.warnings.append("⚠️ No existe trading_bot.db")
            return
            
        try:
            conn = sqlite3.connect('trading_bot.db')
            cursor = conn.cursor()
            
            # Verificar tablas con user_id
            tables_to_check = ['positions', 'signals', 'performance', 'alerts']
            
            for table in tables_to_check:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'user_id' not in columns:
                    self.errors.append(f"❌ Tabla {table} no tiene columna user_id")
                else:
                    self.passed.append(f"✅ Tabla {table} tiene user_id")
            
            conn.close()
        except Exception as e:
            self.errors.append(f"❌ Error verificando BD: {e}")
    
    def check_cors_config(self) -> None:
        """Verifica configuración CORS"""
        fastapi_file = Path('trading_api/fastapi_server.py')
        if not fastapi_file.exists():
            return
            
        content = fastapi_file.read_text()
        
        # Buscar localhost en CORS
        if 'allow_origins=["*"]' in content:
            self.errors.append("❌ CORS permite todos los orígenes (*)")
        elif 'localhost' in content and 'allow_origins' in content:
            self.warnings.append("⚠️ CORS incluye localhost (cambiar en producción)")
        else:
            self.passed.append("✅ CORS configurado")
    
    def check_dependencies(self) -> None:
        """Verifica dependencias de seguridad"""
        required = ['python-dotenv', 'PyJWT']
        requirements_file = Path('requirements.txt')
        
        if requirements_file.exists():
            content = requirements_file.read_text()
            for dep in required:
                if dep.lower() not in content.lower():
                    self.warnings.append(f"⚠️ Falta dependencia: {dep}")
                    self.warnings.append(f"   Instalar: pip install {dep}")
        
    def generate_report(self) -> None:
        """Genera reporte de seguridad"""
        print("\n" + "="*50)
        print("🔒 REPORTE DE SEGURIDAD - botphIA")
        print("="*50)
        
        if self.passed:
            print("\n✅ VERIFICACIONES PASADAS:")
            for item in self.passed:
                print(f"  {item}")
        
        if self.warnings:
            print("\n⚠️ ADVERTENCIAS:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.errors:
            print("\n❌ ERRORES CRÍTICOS:")
            for error in self.errors:
                print(f"  {error}")
        
        print("\n" + "="*50)
        
        if self.errors:
            print("🚫 ESTADO: NO LISTO PARA PRODUCCIÓN")
            print("   Resolver errores críticos antes de publicar")
        elif self.warnings:
            print("⚠️ ESTADO: REVISAR ADVERTENCIAS")
            print("   Sistema funcional pero con mejoras recomendadas")
        else:
            print("✅ ESTADO: LISTO PARA PRODUCCIÓN")
            print("   Todas las verificaciones pasadas")
        
        print("="*50 + "\n")
        
        return len(self.errors) == 0
    
    def run_all_checks(self) -> bool:
        """Ejecuta todas las verificaciones"""
        print("🔍 Iniciando verificación de seguridad...")
        
        self.check_env_file()
        self.check_secrets_in_code()
        self.check_database_permissions()
        self.check_database_structure()
        self.check_cors_config()
        self.check_dependencies()
        
        return self.generate_report()

def main():
    checker = SecurityChecker()
    is_secure = checker.run_all_checks()
    
    # Salir con código apropiado
    sys.exit(0 if is_secure else 1)

if __name__ == "__main__":
    main()