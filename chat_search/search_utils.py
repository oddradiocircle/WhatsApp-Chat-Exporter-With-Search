#!/usr/bin/env python3
"""
WhatsApp Chat Search Utilities Module

This module contains utility functions for displaying and saving search results.
"""

import json
from datetime import datetime

def print_results(results, show_context=True, show_contact_relevance=True, contacts=None):
    """
    Imprime resultados de búsqueda en un formato legible.

    Parámetros:
    - results: Lista de resultados de búsqueda o diccionario con resultados y relevancia de contactos
    - show_context: Si se deben mostrar mensajes de contexto
    - show_contact_relevance: Si se debe mostrar la relevancia de contactos
    - contacts: Diccionario de contactos (opcional)
    """
    # Verificar si results es un diccionario con resultados y relevancia de contactos
    if isinstance(results, dict) and 'results' in results:
        contact_relevance = results.get('contact_relevance', [])
        chat_relevance = results.get('chat_relevance', [])
        results = results['results']
    else:
        contact_relevance = []
        chat_relevance = []
        show_contact_relevance = False

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

    # Mostrar relevancia de contactos si está disponible
    if show_contact_relevance and contact_relevance:
        print("\n=== RELEVANCIA DE CONTACTOS ===\n")
        print("Los siguientes contactos son los más relevantes para las palabras clave buscadas:\n")

        for i, (contact_id, data) in enumerate(contact_relevance[:10], 1):
            # Formatear el nombre del contacto para mostrar
            display_name = data.get('display_name', 'Desconocido')
            if display_name is None:
                display_name = 'Desconocido'
            phone = data.get('phone', '')

            # Intentar usar el nombre del contacto desde el archivo de contactos
            clean_id = contact_id.split('@')[0] if '@' in contact_id else contact_id
            contact_found = False
            contact_name = None

            if contacts:
                # Intentar encontrar el contacto por el número de teléfono exacto
                if clean_id in contacts:
                    contact_info = contacts[clean_id]
                    if contact_info.get('display_name'):
                        contact_name = contact_info.get('display_name')
                        contact_found = True
                # Si no se encuentra, intentar buscar por el número sin formato
                else:
                    # Eliminar todos los caracteres no numéricos excepto el signo +
                    clean_phone = ''.join(c for c in clean_id if c.isdigit() or c == '+')
                    for contact_id_key, contact_data in contacts.items():
                        contact_phone_raw = contact_data.get('phone_raw', '')
                        if clean_phone == contact_phone_raw or clean_phone.endswith(contact_phone_raw) or contact_phone_raw.endswith(clean_phone):
                            if contact_data.get('display_name'):
                                contact_name = contact_data.get('display_name')
                                contact_found = True
                                break

            # Obtener número telefónico formateado
            from whatsapp_core import format_phone_number
            formatted_phone = format_phone_number(clean_id, contacts)
            
            # Decidir qué mostrar basado en la información disponible
            if contact_found and contact_name:
                if contact_name != display_name and contact_name != formatted_phone:
                    display_text = f"{contact_name} ({formatted_phone})"
                else:
                    display_text = f"{formatted_phone}"
            else:
                if display_name != clean_id and display_name != "Desconocido" and not display_name.isdigit():
                    display_text = f"{display_name} ({formatted_phone})"
                else:
                    display_text = formatted_phone

            print(f"{i}. {display_text} (Puntuación: {data['score']:.1f}, Promedio: {data.get('avg_score', 0):.1f})")

            # Mostrar conteo de palabras clave
            if data['keyword_counts']:
                print("   Palabras clave encontradas:")
                for keyword, count in sorted(data['keyword_counts'].items(), key=lambda x: x[1], reverse=True):
                    print(f"   - {keyword}: {count} veces")

            print()

    # Mostrar relevancia de chats si está disponible
    if show_contact_relevance and chat_relevance:
        print("\n=== RELEVANCIA DE CHATS ===\n")
        print("Los siguientes chats son los más relevantes para las palabras clave buscadas:\n")

        for i, (chat_id, data) in enumerate(chat_relevance[:10], 1):
            # Formatear el nombre del chat para mostrar
            display_name = data.get('display_name', 'Desconocido')
            if display_name is None:
                display_name = 'Desconocido'
            phone = data.get('phone', '')

            # Intentar usar el nombre del contacto desde el archivo de contactos
            clean_id = chat_id.split('@')[0] if '@' in chat_id else chat_id
            contact_found = False
            chat_name = None

            if contacts:
                # Intentar encontrar el contacto por el número de teléfono exacto
                if clean_id in contacts:
                    contact_info = contacts[clean_id]
                    if contact_info.get('display_name'):
                        chat_name = contact_info.get('display_name')
                        contact_found = True
                # Si no se encuentra, intentar buscar por el número sin formato
                elif '-' not in clean_id:  # Solo para chats individuales, no grupos
                    # Eliminar todos los caracteres no numéricos excepto el signo +
                    clean_phone = ''.join(c for c in clean_id if c.isdigit() or c == '+')
                    for contact_id_key, contact_data in contacts.items():
                        contact_phone_raw = contact_data.get('phone_raw', '')
                        if clean_phone == contact_phone_raw or clean_phone.endswith(contact_phone_raw) or contact_phone_raw.endswith(clean_phone):
                            if contact_data.get('display_name'):
                                chat_name = contact_data.get('display_name')
                                contact_found = True
                                break

            # Obtener número telefónico formateado o identificador de chat formateado
            from whatsapp_core import format_phone_number
            if '-' in clean_id:  # Es un chat de grupo
                group_id = clean_id
                if display_name != group_id and display_name != "Desconocido":
                    display_text = f"{display_name} (Grupo {group_id})"
                else:
                    display_text = f"Grupo {group_id}"
            else:  # Es un chat individual
                formatted_phone = format_phone_number(clean_id, contacts)
                
                # Decidir qué mostrar basado en la información disponible
                if contact_found and chat_name:
                    if chat_name != display_name and chat_name != formatted_phone:
                        display_text = f"{chat_name} ({formatted_phone})"
                    else:
                        display_text = f"{formatted_phone}"
                else:
                    if display_name != clean_id and display_name != "Desconocido" and not display_name.isdigit():
                        display_text = f"{display_name} ({formatted_phone})"
                    else:
                        display_text = formatted_phone

            print(f"{i}. {display_text} (Puntuación: {data['score']:.1f}, Promedio: {data.get('avg_score', 0):.1f})")

            # Mostrar conteo de palabras clave
            if data['keyword_counts']:
                print("   Palabras clave encontradas:")
                for keyword, count in sorted(data['keyword_counts'].items(), key=lambda x: x[1], reverse=True):
                    print(f"   - {keyword}: {count} veces")

            print()

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
                # Verificar si results es un diccionario con resultados y relevancia de contactos
                if isinstance(results, dict) and 'results' in results:
                    message_results = results['results']
                    contact_relevance = results.get('contact_relevance', [])
                    chat_relevance = results.get('chat_relevance', [])
                else:
                    message_results = results
                    contact_relevance = []
                    chat_relevance = []

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

                # Escribir relevancia de contactos
                if contact_relevance:
                    f.write(f"\n## Relevancia de Contactos\n\n")
                    f.write("Los siguientes contactos son los más relevantes para las palabras clave buscadas:\n\n")

                    for i, (contact_id, data) in enumerate(contact_relevance[:10], 1):
                        # Formatear el nombre del contacto para mostrar
                        display_name = data['display_name']
                        phone = data.get('phone', '')

                        # Intentar usar el nombre del contacto desde el archivo de contactos
                        clean_id = contact_id.split('@')[0] if '@' in contact_id else contact_id
                        contact_found = False

                        if contacts:
                            # Intentar encontrar el contacto por el número de teléfono exacto
                            if clean_id in contacts:
                                contact_info = contacts[clean_id]
                                if contact_info.get('display_name'):
                                    display_name = contact_info.get('display_name')
                                    contact_found = True
                            # Si no se encuentra, intentar buscar por el número sin formato
                            else:
                                # Eliminar todos los caracteres no numéricos excepto el signo +
                                clean_phone = ''.join(c for c in clean_id if c.isdigit() or c == '+')
                                for contact_id_key, contact_data in contacts.items():
                                    contact_phone_raw = contact_data.get('phone_raw', '')
                                    if clean_phone == contact_phone_raw or clean_phone.endswith(contact_phone_raw) or contact_phone_raw.endswith(clean_phone):
                                        if contact_data.get('display_name'):
                                            display_name = contact_data.get('display_name')
                                            contact_found = True
                                            break

                        # Si no se encontró el contacto y el display_name es igual al ID o al teléfono, mostrar solo el teléfono formateado
                        if not contact_found and (display_name == contact_id or display_name == phone):
                            from whatsapp_core import format_phone_number
                            if phone:
                                display_name = format_phone_number(phone, contacts)
                            else:
                                display_name = format_phone_number(clean_id, contacts)

                        f.write(f"{i}. **{display_name}** (Puntuación: {data['score']:.1f}, Promedio: {data.get('avg_score', 0):.1f})\n")

                        # Escribir conteo de palabras clave
                        if data['keyword_counts']:
                            f.write("   - Palabras clave encontradas:\n")
                            for keyword, count in sorted(data['keyword_counts'].items(), key=lambda x: x[1], reverse=True):
                                f.write(f"     - {keyword}: {count} veces\n")

                        f.write("\n")

                # Escribir relevancia de chats
                if chat_relevance:
                    f.write(f"\n## Relevancia de Chats\n\n")
                    f.write("Los siguientes chats son los más relevantes para las palabras clave buscadas:\n\n")

                    for i, (chat_id, data) in enumerate(chat_relevance[:10], 1):
                        # Formatear el nombre del chat para mostrar
                        display_name = data['display_name']
                        phone = data.get('phone', '')

                        # Intentar usar el nombre del contacto desde el archivo de contactos
                        clean_id = chat_id.split('@')[0] if '@' in chat_id else chat_id
                        contact_found = False

                        if contacts:
                            # Intentar encontrar el contacto por el número de teléfono exacto
                            if clean_id in contacts:
                                contact_info = contacts[clean_id]
                                if contact_info.get('display_name'):
                                    display_name = contact_info.get('display_name')
                                    contact_found = True
                            # Si no se encuentra, intentar buscar por el número sin formato
                            else:
                                # Eliminar todos los caracteres no numéricos excepto el signo +
                                clean_phone = ''.join(c for c in clean_id if c.isdigit() or c == '+')
                                for contact_id_key, contact_data in contacts.items():
                                    contact_phone_raw = contact_data.get('phone_raw', '')
                                    if clean_phone == contact_phone_raw or clean_phone.endswith(contact_phone_raw) or contact_phone_raw.endswith(clean_phone):
                                        if contact_data.get('display_name'):
                                            display_name = contact_data.get('display_name')
                                            contact_found = True
                                            break

                        # Si no se encontró el contacto y el display_name es igual al ID o al teléfono, mostrar solo el teléfono formateado
                        if not contact_found and (display_name == chat_id or display_name == phone):
                            from whatsapp_core import format_phone_number
                            if phone:
                                display_name = format_phone_number(phone, contacts)
                            else:
                                # Extraer número de teléfono del chat_id (eliminar @s.whatsapp.net)
                                display_name = format_phone_number(clean_id, contacts)

                        f.write(f"{i}. **{display_name}** (Puntuación: {data['score']:.1f}, Promedio: {data.get('avg_score', 0):.1f})\n")

                        # Escribir conteo de palabras clave
                        if data['keyword_counts']:
                            f.write("   - Palabras clave encontradas:\n")
                            for keyword, count in sorted(data['keyword_counts'].items(), key=lambda x: x[1], reverse=True):
                                f.write(f"     - {keyword}: {count} veces\n")

                        f.write("\n")
        else:
            # Guardar como JSON
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"Resultados guardados en {filename}")
        return True
    except Exception as e:
        print(f"Error al guardar resultados: {e}")
        return False
