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
        print(f"Puntuación total: {contact_data.get('final_score', contact_data['score']):.1f}")
        print(f"Mensajes coincidentes: {contact_data['message_count']}")
        print(f"Densidad de palabras clave: {contact_data['keyword_density']:.2%}")

        # Mostrar diversidad de palabras clave si está disponible
        if 'keyword_diversity' in contact_data:
            print(f"Diversidad de palabras clave: {contact_data['keyword_diversity']:.2%}")

        # Mostrar factor de recencia si está disponible
        if 'recency_factor' in contact_data:
            print(f"Factor de recencia: {contact_data['recency_factor']:.2f}")

        # Mostrar palabras clave más frecuentes para este contacto
        if contact_data['keyword_counts']:
            sorted_keywords = sorted(contact_data['keyword_counts'].items(), key=lambda x: x[1], reverse=True)
            print("Palabras clave más frecuentes:")
            for keyword, count in sorted_keywords[:5]:  # Mostrar las 5 más frecuentes
                print(f"  - {keyword}: {count} veces")
        print("=" * 80 + "\n")

    # Mostrar información sobre criterios de ordenación si están disponibles
    if isinstance(results, dict) and 'sort_criteria' in results:
        sort_criteria = results['sort_criteria']
        if sort_criteria:
            criteria_str = ', '.join(sort_criteria)
            print(f"\nResultados ordenados por: {criteria_str}")

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

            # Mostrar factores adicionales si están disponibles
            additional_factors = []

            if 'proximity_factor' in stats:
                additional_factors.append(f"Proximidad: {stats['proximity_factor']:.2f}")

            if 'position_factor' in stats:
                additional_factors.append(f"Posición: {stats['position_factor']:.2f}")

            if 'partial_matches' in stats and stats['partial_matches'] > 0:
                additional_factors.append(f"Coincidencias parciales: {stats['partial_matches']}")

            if additional_factors:
                print(f"Factores adicionales: {' | '.join(additional_factors)}")

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

                # Usar puntuación final si está disponible, de lo contrario usar puntuación normal
                score_display = data.get('final_score', data['score'])
                print(f"   Puntuación: {score_display:.1f} | Mensajes: {data['message_count']} | Densidad: {data.get('keyword_density', 0):.2%}")

                # Mostrar métricas adicionales si están disponibles
                additional_metrics = []
                if 'keyword_diversity' in data:
                    additional_metrics.append(f"Diversidad: {data['keyword_diversity']:.2%}")
                if 'recency_factor' in data:
                    additional_metrics.append(f"Recencia: {data['recency_factor']:.2f}")

                if additional_metrics:
                    print(f"   {' | '.join(additional_metrics)}")

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
                    # Usar puntuación final si está disponible
                    score_display = data.get('final_score', data['score'])
                    print(f"{i}. {data['display_name']}: {data['message_count']} mensajes (Puntuación: {score_display:.1f})")

                    # Mostrar métricas adicionales si están disponibles
                    additional_metrics = []
                    if 'keyword_density' in data:
                        additional_metrics.append(f"Densidad: {data['keyword_density']:.2%}")
                    if 'keyword_diversity' in data:
                        additional_metrics.append(f"Diversidad: {data['keyword_diversity']:.2%}")
                    if 'recency_factor' in data:
                        additional_metrics.append(f"Recencia: {data['recency_factor']:.2f}")

                    if additional_metrics:
                        print(f"   {' | '.join(additional_metrics)}")

            # Mostrar distribución por contacto
            if contact_relevance:
                print("\nDistribución por contacto:")
                for i, (contact_id, data) in enumerate(contact_relevance[:5], 1):
                    # Usar puntuación final si está disponible
                    score_display = data.get('final_score', data['score'])
                    print(f"{i}. {data['display_name']}: {data['message_count']} mensajes (Puntuación: {score_display:.1f})")

                    # Mostrar métricas adicionales si están disponibles
                    additional_metrics = []
                    if 'keyword_density' in data:
                        additional_metrics.append(f"Densidad: {data['keyword_density']:.2%}")
                    if 'keyword_diversity' in data:
                        additional_metrics.append(f"Diversidad: {data['keyword_diversity']:.2%}")
                    if 'recency_factor' in data:
                        additional_metrics.append(f"Recencia: {data['recency_factor']:.2f}")

                    if additional_metrics:
                        print(f"   {' | '.join(additional_metrics)}")

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
                if isinstance(results, dict):
                    # Manejar diferentes tipos de resultados
                    if 'results' in results:
                        message_results = results['results']
                    elif 'contact_relevance' in results:
                        # Escribir encabezado para relevancia de contactos
                        f.write(f"# Análisis de Relevancia de Contactos\n\n")
                        contact_dict = results['contact_relevance']

                        f.write(f"Se encontraron {len(contact_dict)} contactos relevantes:\n\n")

                        # Ordenar contactos por puntuación
                        sorted_contacts = sorted(
                            contact_dict.items(),
                            key=lambda x: x[1].get('final_score', x[1].get('score', 0)),
                            reverse=True
                        )

                        for i, (contact_id, data) in enumerate(sorted_contacts, 1):
                            score = data.get('final_score', data.get('score', 0))
                            f.write(f"## {i}. {data.get('display_name', 'Desconocido')} (Puntuación: {score:.1f})\n")
                            f.write(f"**Teléfono:** {data.get('phone', 'Desconocido')}\n")
                            f.write(f"**Mensajes coincidentes:** {data.get('message_count', 0)}\n")

                            # Escribir métricas adicionales si están disponibles
                            if 'keyword_density' in data:
                                f.write(f"**Densidad de palabras clave:** {data['keyword_density']:.2%}\n")
                            if 'keyword_diversity' in data:
                                f.write(f"**Diversidad de palabras clave:** {data['keyword_diversity']:.2%}\n")
                            if 'recency_factor' in data:
                                f.write(f"**Factor de recencia:** {data['recency_factor']:.2f}\n")

                            # Escribir palabras clave más frecuentes
                            if 'keyword_counts' in data and data['keyword_counts']:
                                f.write("**Palabras clave más frecuentes:**\n")
                                sorted_keywords = sorted(data['keyword_counts'].items(), key=lambda x: x[1], reverse=True)
                                for keyword, count in sorted_keywords[:5]:
                                    f.write(f"- {keyword}: {count} veces\n")

                            f.write("\n")

                        # Terminar aquí para evitar procesar como mensajes
                        print(f"Resultados guardados en {filename}")
                        return True
                    elif 'chat_relevance' in results:
                        # Escribir encabezado para relevancia de chats
                        f.write(f"# Análisis de Relevancia de Chats\n\n")
                        chat_dict = results['chat_relevance']

                        f.write(f"Se encontraron {len(chat_dict)} chats relevantes:\n\n")

                        # Ordenar chats por puntuación
                        sorted_chats = sorted(
                            chat_dict.items(),
                            key=lambda x: x[1].get('final_score', x[1].get('score', 0)),
                            reverse=True
                        )

                        for i, (chat_id, data) in enumerate(sorted_chats, 1):
                            score = data.get('final_score', data.get('score', 0))
                            f.write(f"## {i}. {data.get('display_name', 'Desconocido')} (Puntuación: {score:.1f})\n")
                            f.write(f"**Mensajes coincidentes:** {data.get('message_count', 0)}\n")

                            # Escribir métricas adicionales si están disponibles
                            if 'keyword_density' in data:
                                f.write(f"**Densidad de palabras clave:** {data['keyword_density']:.2%}\n")
                            if 'keyword_diversity' in data:
                                f.write(f"**Diversidad de palabras clave:** {data['keyword_diversity']:.2%}\n")
                            if 'recency_factor' in data:
                                f.write(f"**Factor de recencia:** {data['recency_factor']:.2f}\n")

                            # Escribir palabras clave más frecuentes
                            if 'keyword_counts' in data and data['keyword_counts']:
                                f.write("**Palabras clave más frecuentes:**\n")
                                sorted_keywords = sorted(data['keyword_counts'].items(), key=lambda x: x[1], reverse=True)
                                for keyword, count in sorted_keywords[:5]:
                                    f.write(f"- {keyword}: {count} veces\n")

                            f.write("\n")

                        # Terminar aquí para evitar procesar como mensajes
                        print(f"Resultados guardados en {filename}")
                        return True
                    elif 'prospects' in results:
                        # Escribir encabezado para prospectos de ventas
                        f.write(f"# Análisis de Prospectos de Ventas\n\n")
                        prospects_dict = results['prospects']

                        f.write(f"Se encontraron {len(prospects_dict)} prospectos potenciales:\n\n")

                        # Ordenar prospectos por puntuación de potencial
                        sorted_prospects = sorted(
                            prospects_dict.items(),
                            key=lambda x: x[1].get('potential_score', 0),
                            reverse=True
                        )

                        for i, (contact_id, data) in enumerate(sorted_prospects, 1):
                            f.write(f"## {i}. {data.get('display_name', 'Desconocido')} ({data.get('phone', 'Desconocido')})\n")
                            f.write(f"**Potencial de compra:** {data.get('potential_level', 'Desconocido')} ({data.get('potential_score', 0):.1f}/100)\n")
                            f.write(f"**Mensajes relevantes:** {data.get('message_count', 0)}\n")
                            f.write(f"**Densidad de palabras clave:** {data.get('keyword_density', 0):.2%}\n")

                            # Escribir interés por categorías
                            if 'categories' in data and data['categories']:
                                f.write("**Interés por categorías:**\n")
                                sorted_categories = sorted(
                                    data['categories'].items(),
                                    key=lambda x: x[1].get('score', 0),
                                    reverse=True
                                )
                                for category_name, category_data in sorted_categories:
                                    f.write(f"- {category_name}: {category_data.get('score', 0):.1f} puntos ({category_data.get('message_count', 0)} mensajes)\n")

                            f.write("\n")

                        # Escribir información de categorías
                        if 'categories' in results:
                            f.write("## Categorías analizadas\n\n")
                            for category_name, keywords in results['categories'].items():
                                f.write(f"**{category_name}:** {', '.join(keywords)}\n")

                        # Escribir información de filtros
                        if 'filters' in results:
                            f.write("\n## Filtros aplicados\n\n")
                            filters = results['filters']
                            if 'start_date' in filters and filters['start_date']:
                                f.write(f"**Fecha de inicio:** {filters['start_date']}\n")
                            if 'end_date' in filters and filters['end_date']:
                                f.write(f"**Fecha de fin:** {filters['end_date']}\n")
                            if 'min_score' in filters:
                                f.write(f"**Puntuación mínima:** {filters['min_score']}\n")

                        # Escribir fecha de análisis
                        if 'analysis_date' in results:
                            f.write(f"\n**Fecha de análisis:** {results['analysis_date']}\n")

                        # Terminar aquí para evitar procesar como mensajes
                        print(f"Resultados guardados en {filename}")
                        return True
                    else:
                        # Si no es ninguno de los tipos especiales, tratar como mensajes
                        message_results = results
                else:
                    # Si no es un diccionario, asumir que es una lista de mensajes
                    message_results = results

                # Escribir encabezado para mensajes
                f.write(f"# Resultados de búsqueda\n\n")

                # Verificar si message_results es una lista
                if isinstance(message_results, list):
                    f.write(f"Se encontraron {len(message_results)} mensajes coincidentes:\n\n")

                    for i, result in enumerate(message_results, 1):
                        f.write(f"## Resultado {i}" + (f" (Puntuación: {result.get('score', 0):.1f})" if 'score' in result else "") + "\n")
                        f.write(f"**Chat:** {result.get('chat_name', 'Desconocido')}\n")

                        # Escribir información del remitente
                        if result.get('from_me'):
                            f.write(f"**Remitente:** Yo\n")
                        else:
                            sender_info = result.get('sender', 'Desconocido')
                            phone_info = result.get('phone', 'Desconocido')

                            if sender_info == phone_info or sender_info == result.get('sender_id', ''):
                                f.write(f"**Remitente:** {phone_info}\n")
                            else:
                                f.write(f"**Remitente:** {sender_info}\n")
                                if phone_info != "Desconocido":
                                    f.write(f"**Teléfono:** {phone_info}\n")

                        f.write(f"**Fecha:** {result.get('date', 'Desconocida')}\n")

                        if 'matched_keywords' in result:
                            f.write(f"**Palabras clave coincidentes:** {', '.join(result['matched_keywords'])}\n")

                        # Incluir estadísticas de palabras si están disponibles
                        if 'word_stats' in result:
                            stats = result['word_stats']
                            f.write(f"**Densidad de palabras clave:** {stats.get('keyword_density', 0):.2%} ({stats.get('total_keywords', 0)} de {stats.get('total_words', 0)} palabras)\n")

                            # Incluir factores adicionales si están disponibles
                            additional_factors = []

                            if 'proximity_factor' in stats:
                                additional_factors.append(f"Proximidad: {stats['proximity_factor']:.2f}")

                            if 'position_factor' in stats:
                                additional_factors.append(f"Posición: {stats['position_factor']:.2f}")

                            if 'partial_matches' in stats and stats['partial_matches'] > 0:
                                additional_factors.append(f"Coincidencias parciales: {stats['partial_matches']}")

                            if additional_factors:
                                f.write(f"**Factores adicionales:** {' | '.join(additional_factors)}\n")

                        f.write(f"**Mensaje:** {result.get('message', '')}\n\n")
                else:
                    # Si no es una lista, escribir un mensaje de error
                    f.write("Error: No se pudieron procesar los resultados en formato adecuado.\n")
        else:
            # Guardar como JSON
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"Resultados guardados en {filename}")
        return True
    except Exception as e:
        print(f"Error al guardar resultados: {e}")
        import traceback
        traceback.print_exc()
        return False
