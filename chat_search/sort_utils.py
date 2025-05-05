#!/usr/bin/env python3
"""
Utilidades de ordenación para resultados de búsqueda de WhatsApp.

Este módulo proporciona funciones para ordenar los resultados de búsqueda
según diferentes criterios.
"""

import re
from datetime import datetime


def get_sort_key_function(sort_by):
    """
    Obtiene la función de clave de ordenación para un criterio dado.

    Parámetros:
    - sort_by: Criterio de ordenación

    Retorna:
    - key_function: Función para usar como clave de ordenación
    - reverse: Booleano que indica si se debe ordenar en orden inverso
    """
    sort_by = sort_by.lower()

    # Diccionario de funciones de ordenación
    sort_functions = {
        'relevance': (lambda x: x.get('score', 0) if isinstance(x.get('score'), (int, float)) else 0, True),
        'date_asc': (lambda x: x.get('timestamp', 0) if isinstance(x.get('timestamp'), (int, float)) else 0, False),
        'date_desc': (lambda x: x.get('timestamp', 0) if isinstance(x.get('timestamp'), (int, float)) else 0, True),
        'sender': (lambda x: x.get('sender', '').lower() if isinstance(x.get('sender'), str) else '', False),
        'chat': (lambda x: x.get('chat_name', '').lower() if isinstance(x.get('chat_name'), str) else '', False),
        'length_asc': (lambda x: len(x.get('message', '')) if isinstance(x.get('message'), str) else 0, False),
        'length_desc': (lambda x: len(x.get('message', '')) if isinstance(x.get('message'), str) else 0, True),
        'keyword_density': (
            lambda x: (
                x.get('word_stats', {}).get('keyword_density', 0) 
                if isinstance(x.get('word_stats', {}).get('keyword_density'), (int, float)) 
                else 0
            ), 
            True
        ),
        'keyword_count': (
            lambda x: (
                len(x.get('matched_keywords', [])) 
                if isinstance(x.get('matched_keywords'), list) 
                else 0
            ), 
            True
        ),
    }

    # Valor predeterminado si el criterio no es válido
    return sort_functions.get(sort_by, sort_functions['relevance'])


def sort_results(results, sort_criteria=None):
    """
    Ordena los resultados según los criterios especificados.

    Parámetros:
    - results: Lista de resultados a ordenar
    - sort_criteria: Lista de criterios de ordenación (hasta 3)
                    Si es None, se usa 'relevance' como predeterminado

    Retorna:
    - sorted_results: Lista de resultados ordenados
    """
    if not results:
        return []

    # Si no se especifican criterios, usar relevancia como predeterminado
    if not sort_criteria:
        sort_criteria = ['relevance']
    
    # Limitar a 3 criterios
    sort_criteria = sort_criteria[:3]
    
    # Validar criterios
    valid_criteria = [
        'relevance', 'date_asc', 'date_desc', 'sender', 'chat', 
        'length_asc', 'length_desc', 'keyword_density', 'keyword_count'
    ]
    
    # Filtrar criterios no válidos
    sort_criteria = [c for c in sort_criteria if c in valid_criteria]
    
    # Si no hay criterios válidos, usar relevancia como predeterminado
    if not sort_criteria:
        sort_criteria = ['relevance']
    
    # Ordenar por múltiples criterios
    sorted_results = results.copy()
    
    # Ordenar en orden inverso (del último criterio al primero)
    for criterion in reversed(sort_criteria):
        key_func, reverse = get_sort_key_function(criterion)
        sorted_results.sort(key=key_func, reverse=reverse)
    
    return sorted_results


def get_available_sort_criteria():
    """
    Obtiene la lista de criterios de ordenación disponibles.

    Retorna:
    - criteria: Diccionario con criterios de ordenación y sus descripciones
    """
    return {
        'relevance': 'Relevancia (puntuación más alta primero)',
        'date_asc': 'Fecha (más antiguos primero)',
        'date_desc': 'Fecha (más recientes primero)',
        'sender': 'Remitente (alfabético)',
        'chat': 'Chat (alfabético)',
        'length_asc': 'Longitud del mensaje (más cortos primero)',
        'length_desc': 'Longitud del mensaje (más largos primero)',
        'keyword_density': 'Densidad de palabras clave (mayor densidad primero)',
        'keyword_count': 'Cantidad de palabras clave coincidentes (mayor cantidad primero)'
    }
