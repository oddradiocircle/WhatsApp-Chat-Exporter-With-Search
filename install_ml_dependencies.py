#!/usr/bin/env python3
"""
Script para instalar las dependencias necesarias para el análisis de WhatsApp con ML
Optimizado para CPUs y GPUs Intel
"""

import subprocess
import sys
import os
import platform

def install_dependencies():
    """Instala las dependencias necesarias para el análisis con ML optimizadas para Intel"""
    # Dependencias básicas
    base_dependencies = [
        "tqdm",
        "numpy",
        "scipy",
        "scikit-learn",
        "nltk",
        "textblob",
        "spacy",
        "sentence-transformers",
        "transformers"
    ]

    # Verificar si estamos en Windows y si hay una GPU Intel
    is_windows = platform.system() == "Windows"
    has_intel_gpu = False

    if is_windows:
        try:
            # Verificar si hay una GPU Intel disponible
            result = subprocess.run(["dxdiag", "/t", "temp_dxdiag.txt"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

            # Esperar a que se genere el archivo
            import time
            time.sleep(2)

            if os.path.exists("temp_dxdiag.txt"):
                with open("temp_dxdiag.txt", "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().lower()
                    if "intel" in content and ("iris" in content or "uhd" in content or "hd graphics" in content):
                        has_intel_gpu = True

                # Eliminar el archivo temporal
                os.remove("temp_dxdiag.txt")
        except Exception as e:
            print(f"No se pudo detectar la GPU: {e}")

    print("Instalando dependencias básicas...")
    for dep in base_dependencies:
        print(f"Instalando {dep}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

    # Instalar PyTorch con soporte para Intel
    print("Instalando PyTorch optimizado...")
    if has_intel_gpu:
        print("Detectada GPU Intel. Instalando PyTorch con soporte para GPU Intel...")
        # PyTorch con soporte para GPU Intel
        subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchvision", "torchaudio"])

        # Intentar instalar extensiones de Intel para PyTorch
        try:
            print("Instalando Intel Extension for PyTorch...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "intel-extension-for-pytorch"])
        except Exception as e:
            print(f"No se pudo instalar Intel Extension for PyTorch: {e}")
            print("Continuando con la instalación...")
    else:
        # PyTorch estándar
        print("Instalando PyTorch estándar...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "torch"])

    # Intentar instalar Intel Extension for Scikit-learn
    try:
        print("Instalando Intel Extension for Scikit-learn...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-learn-intelex"])
    except Exception as e:
        print(f"No se pudo instalar Intel Extension for Scikit-learn: {e}")
        print("Continuando con la instalación...")

    # Descargar modelos de spaCy
    print("Descargando modelo de spaCy para español...")
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "es_core_news_md"])

    # Descargar recursos de NLTK
    print("Descargando recursos de NLTK...")
    import nltk
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

    print("\nTodas las dependencias han sido instaladas correctamente.")
    print("El sistema está optimizado para hardware Intel.")
    print("Ahora puedes ejecutar el script de análisis de WhatsApp con ML.")

if __name__ == "__main__":
    install_dependencies()
