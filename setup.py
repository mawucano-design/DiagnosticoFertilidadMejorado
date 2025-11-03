#!/usr/bin/env python3
"""
Script de instalación para la Plataforma Agrícola Integral
"""

import subprocess
import sys
import os

def install_requirements():
    """Instala los requerimientos del proyecto"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requerimientos instalados correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando requerimientos: {e}")
        return False

def create_folders():
    """Crea la estructura de carpetas necesaria"""
    folders = [
        'gemelos_digitales',
        'fertilidad', 
        'utils',
        'data',
        '.streamlit'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"✅ Carpeta creada: {folder}")

def main():
    print("🚀 Configurando Plataforma Agrícola Integral...")
    
    # Crear carpetas
    create_folders()
    
    # Instalar dependencias
    if install_requirements():
        print("\n🎉 ¡Configuración completada!")
        print("\nPara ejecutar la aplicación:")
        print("  streamlit run app.py")
    else:
        print("\n⚠️  Hubo problemas durante la instalación")

if __name__ == "__main__":
    main()
