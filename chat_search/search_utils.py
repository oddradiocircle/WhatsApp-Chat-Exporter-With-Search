#!/usr/bin/env python3
"""
WhatsApp Chat Search Utilities Module

This module contains utility functions for displaying and saving search results.
"""

import json
from datetime import datetime

def print_results(results, show_context=True, contacts=None):
    """
    Imprime resultados de búsqueda en un formato legible.

    Parámetros:
    - results: Lista de resultados de búsqueda o diccionario con resultados y relevancia de contactos
    - show_context: Si se deben mostrar mensajes de contexto
    - contacts: Diccionario de contactos (opcional)
    """
    # Verificar si results es un diccionario con resultados y relevancia de contactos
    if isinstance(results, dict) and 'results' in results:
        results = results['results']

    if not results:
        print("No se encontraron mensajes coincidentes.")
        return

    print(f"\nSe encontraron {len(results)} mensajes coincidentes:\n")

    for i, result in enumerate(results, 1):
        print(f"Resultado {i}" + (f" (Puntuación: {result.get('score', 0):.1f})" if 'score' in result else "") + ":")

        # Mostrar información del chat
        chat_name = result.get('chat_name', "")
        chat_id = result.get('chat_id', "")

        # Asegurarse de que chat_name no sea None para evitar errores
        if chat_name is None:
            chat_name = ""

        # Si el chat_name es diferente del ID (número), mostrar ambos
        if chat_name and chat_id and chat_name != chat_id and not chat_id.startswith(chat_name):
            print(f"Chat: {chat_name} ({chat_id})")
        else:
            print(f"Chat: {chat_id}")

        # Mostrar información del remitente
        if result.get('from_me'):
            print(f"Remitente: Yo")
        else:
            sender_info = result.get('sender', 'Desconocido')
            phone_info = result.get('phone', 'Desconocido')
            sender_id = result.get('sender_id', '')

            # Asegurarse de que sender_info y phone_info no sean None
            if sender_info is None:
                sender_info = "Desconocido"
            if phone_info is None:
                phone_info = "Desconocido"

            # Si hay un nombre de contacto y es diferente del número, mostrar ambos
            if sender_info != phone_info and sender_info != "Desconocido" and sender_info != sender_id:
                print(f"Remitente: {sender_info} ({phone_info})")
            else:
                print(f"Remitente: {phone_info}")

        print(f"Fecha: {result['date']}")

        if 'matched_keywords' in result:
            print(f"Palabras clave coincidentes: {', '.join(result['matched_keywords'])}")

        print(f"Mensaje: {result['message']}")

        if show_context and 'context' in result and result['context']:
            print("\nContexto:")
            for ctx in result['context']:
                prefix = "↑ " if ctx['type'] == 'previous' else "↓ "

                # Formatear remitente para mensajes de contexto
                if ctx.get('from_me'):
                    ctx_sender = "Yo"
                else:
                    ctx_sender = ctx.get('sender', 'Desconocido')
                    if ctx_sender is None:
                        ctx_sender = "Desconocido"
                    ctx_phone = ctx.get('phone', 'Desconocido')
                    if ctx_phone is None:
                        ctx_phone = "Desconocido"
                    # Si el nombre es diferente del teléfono, mostrar ambos
                    if ctx_sender != ctx_phone and ctx_sender != "Desconocido":
                        ctx_sender = f"{ctx_sender} ({ctx_phone})"

                print(f"  {prefix}[{ctx['date']}] {ctx_sender}: {ctx['message']}")

        print("\n" + "-" * 80 + "\n")

    # No mostrar relevancia de contactos
    # Esto se ha eliminado para mantener la salida limpia y enfocada solo en los mensajes

    # No mostrar relevancia de chats
    # Esto se ha eliminado para mantener la salida limpia y enfocada solo en los mensajes

def save_results_to_file(results, filename, contacts=None):
    """
    Guarda resultados en un archivo JSON o Markdown.

    Parámetros:
    - results: Resultados a guardar (lista o diccionario con resultados y relevancia de contactos)
    - filename: Nombre del archivo
    - contacts: Diccionario de contactos (opcional)

    Retorna:
    - success: True si se guardó correctamente, False en caso contrario
    """
    try:
        # Verificar si es un archivo Markdown
        if filename.lower().endswith('.md'):
            with open(filename, 'w', encoding='utf-8') as f:
                # Verificar si results es un diccionario con resultados
                if isinstance(results, dict) and 'results' in results:
                    message_results = results['results']
                else:
                    message_results = results

                # Escribir encabezado
                f.write(f"# Resultados de búsqueda\n\n")

                # Escribir resultados de mensajes
                if message_results:
                    f.write(f"Se encontraron {len(message_results)} mensajes coincidentes:\n\n")

                    for i, result in enumerate(message_results, 1):
                        f.write(f"## Resultado {i}" + (f" (Puntuación: {result.get('score', 0):.1f})" if 'score' in result else "") + "\n")
                        f.write(f"**Chat:** {result['chat_name']}\n")

                        # Escribir información del remitente
                        if result.get('from_me'):
                            f.write(f"**Remitente:** Yo\n")
                        else:
                            sender_info = result['sender']
                            phone_info = result.get('phone', 'Desconocido')

                            if sender_info == phone_info or sender_info == result.get('sender_id', ''):
                                f.write(f"**Remitente:** {phone_info}\n")
                            else:
                                f.write(f"**Remitente:** {sender_info}\n")
                                if phone_info != "Desconocido":
                                    f.write(f"**Teléfono:** {phone_info}\n")

                        f.write(f"**Fecha:** {result['date']}\n")

                        if 'matched_keywords' in result:
                            f.write(f"**Palabras clave coincidentes:** {', '.join(result['matched_keywords'])}\n")

                        f.write(f"**Mensaje:** {result['message']}\n\n")

                # No incluir relevancia de contactos en los archivos guardados
                # Esto se ha eliminado para mantener la salida limpia y enfocada solo en los mensajes

                # No incluir relevancia de chats en los archivos guardados
                # Esto se ha eliminado para mantener la salida limpia y enfocada solo en los mensajes
        else:
            # Guardar como JSON
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"Resultados guardados en {filename}")
        return True
    except Exception as e:
        print(f"Error al guardar resultados: {e}")
        return False
