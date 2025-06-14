#!/usr/bin/env python3
"""
Скрипт проверки зависимостей проекта
"""
import sys
import importlib
import subprocess

def check_package(package_name, import_name=None):
    """Проверяет наличие пакета"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name}")
        return False

def main():
    print("🔍 Проверка зависимостей проекта...\n")
    
    required_packages = [
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('ccxt', 'ccxt'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('ta', 'ta'),
        ('PyMySQL', 'pymysql'),
        ('sqlalchemy', 'sqlalchemy'),
        ('redis', 'redis'),
        ('passlib', 'passlib'),
        ('python-jose', 'jose'),
        ('PyJWT', 'jwt'),
        ('python-dotenv', 'dotenv'),
        ('psutil', 'psutil'),
        ('APScheduler', 'apscheduler'),
        ('httpx', 'httpx')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        if not check_package(package_name, import_name):
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n❌ Отсутствующие пакеты: {', '.join(missing_packages)}")
        print("\n📦 Для установки выполните:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    else:
        print("\n✅ Все зависимости установлены!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
