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
    # Extraer componentes si results es un diccionario
    contact_relevance = None
    chat_relevance = None
    most_relevant_contact = None

    if isinstance(results, dict) and 'results' in results:
        message_results = results['results']
        if 'contact_relevance' in results:
            contact_relevance = results['contact_relevance']
        if 'chat_relevance' in results:
            chat_relevance = results['chat_relevance']
        if 'most_relevant_contact' in results:
            most_relevant_contact = results['most_relevant_contact']
    else:
        message_results = results

    if not message_results:
        print("No se encontraron mensajes coincidentes.")
        return

    # Mostrar el contacto más relevante si está disponible
    if most_relevant_contact:
        contact_id, contact_data = most_relevant_contact
        print("\n" + "=" * 80)
        print(f"CONTACTO MÁS RELEVANTE: {contact_data['display_name']} ({contact_data['phone']})")
        print(f"Puntuación total: {contact_data['score']:.1f}")
        print(f"Mensajes coincidentes: {contact_data['message_count']}")
        print(f"Densidad de palabras clave: {contact_data['keyword_density']:.2%}")

        # Mostrar palabras clave más frecuentes para este contacto
        if contact_data['keyword_counts']:
            sorted_keywords = sorted(contact_data['keyword_counts'].items(), key=lambda x: x[1], reverse=True)
            print("Palabras clave más frecuentes:")
            for keyword, count in sorted_keywords[:5]:  # Mostrar las 5 más frecuentes
                print(f"  - {keyword}: {count} veces")
        print("=" * 80 + "\n")

    print(f"\nSe encontraron {len(message_results)} mensajes coincidentes.")

    # Iniciar navegación interactiva
    current_index = 0
    page_size = 1  # Mostrar un resultado a la vez para mejor navegación

    while True:
        # Limpiar pantalla para mejor visualización
        print("\n" + "=" * 80)
        print(f"Resultado {current_index + 1} de {len(message_results)}")
        print("=" * 80)

        # Obtener el resultado actual
        result = message_results[current_index]

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
        print(f"Puntuación: {result.get('score', 0):.1f}")

        if 'matched_keywords' in result:
            print(f"Palabras clave coincidentes: {', '.join(result['matched_keywords'])}")

        # Mostrar estadísticas de palabras si están disponibles
        if 'word_stats' in result:
            stats = result['word_stats']
            print(f"Densidad de palabras clave: {stats['keyword_density']:.2%} ({stats['total_keywords']} de {stats['total_words']} palabras)")

        print(f"\nMensaje: {result['message']}")

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

        # Mostrar opciones de navegación
        print("\n" + "-" * 80)
        print("Navegación: [p]revio | [s]iguiente | [c]ontactos | [r]esumen | [q]salir")

        choice = input("Opción: ").lower()

        if choice == 'p':
            # Ir al resultado anterior
            current_index = max(0, current_index - 1)
        elif choice == 's':
            # Ir al siguiente resultado
            current_index = min(len(message_results) - 1, current_index + 1)
        elif choice == 'c' and contact_relevance:
            # Mostrar relevancia de contactos
            print("\n" + "=" * 80)
            print("RELEVANCIA DE CONTACTOS")
            print("=" * 80)

            for i, (contact_id, data) in enumerate(contact_relevance[:10], 1):  # Mostrar los 10 más relevantes
                print(f"{i}. {data['display_name']} ({data['phone']})")
                print(f"   Puntuación: {data['score']:.1f} | Mensajes: {data['message_count']} | Densidad: {data.get('keyword_density', 0):.2%}")

                # Mostrar palabras clave más frecuentes
                if data['keyword_counts']:
                    sorted_keywords = sorted(data['keyword_counts'].items(), key=lambda x: x[1], reverse=True)
                    keywords_str = ", ".join([f"{k} ({v})" for k, v in sorted_keywords[:3]])
                    print(f"   Palabras clave: {keywords_str}")

                print()

            input("Presiona Enter para continuar...")
        elif choice == 'r':
            # Mostrar resumen de resultados
            print("\n" + "=" * 80)
            print("RESUMEN DE RESULTADOS")
            print("=" * 80)

            # Mostrar distribución de resultados por chat
            if chat_relevance:
                print("\nDistribución por chat:")
                for i, (chat_id, data) in enumerate(chat_relevance[:5], 1):
                    print(f"{i}. {data['display_name']}: {data['message_count']} mensajes")

            # Mostrar distribución por contacto
            if contact_relevance:
                print("\nDistribución por contacto:")
                for i, (contact_id, data) in enumerate(contact_relevance[:5], 1):
                    print(f"{i}. {data['display_name']}: {data['message_count']} mensajes")

            input("\nPresiona Enter para continuar...")
        elif choice == 'q':
            # Salir de la navegación
            break
        else:
            # Opción no válida
            print("Opción no válida. Intenta de nuevo.")

    print("\nBúsqueda finalizada.")

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
