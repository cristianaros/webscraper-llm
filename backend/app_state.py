"""
Estado global de la aplicación.
Almacena la instancia del motor RAG para evitar importaciones circulares.
"""

from typing import Optional

# Será asignado al arrancar la aplicación en main.py
rag_engine = None
