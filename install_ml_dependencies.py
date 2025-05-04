#!/usr/bin/env python3
"""
Script para instalar las dependencias necesarias para el análisis de WhatsApp con ML
"""

import subprocess
import sys

def install_dependencies():
    """Instala las dependencias necesarias para el análisis con ML"""
    dependencies = [
        "scikit-learn",
        "nltk",
        "textblob",
        "spacy",
        "sentence-transformers",
        "transformers",
        "torch",
        "numpy",
        "tqdm"
    ]
    
    print("Instalando dependencias...")
    for dep in dependencies:
        print(f"Instalando {dep}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
    
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
    print("Ahora puedes ejecutar el script de análisis de WhatsApp con ML.")

if __name__ == "__main__":
    install_dependencies()
