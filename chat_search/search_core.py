#!/usr/bin/env python3
"""
WhatsApp Chat Search Core Module

This module contains the core search functionality for WhatsApp chat data,
including relevance scoring, message extraction, and context retrieval.
"""

import re
from datetime import datetime

def calculate_relevance_score(message, keywords):
    """
    Calcula una puntuación de relevancia para un mensaje basado en palabras clave.
    Versión mejorada con soporte para coincidencias parciales, proximidad de palabras clave,
    y posición de palabras clave en el mensaje.

    Parámetros:
    - message: Contenido del mensaje
    - keywords: Lista de palabras clave a buscar

    Retorna:
    - score: Puntuación de relevancia (0-100)
    - matched_keywords: Lista de palabras clave encontradas
    - keyword_counts: Diccionario con el conteo de cada palabra clave
    - word_stats: Estadísticas adicionales sobre palabras (total, proporción, etc.)
    """
    if not message or not keywords:
        return 0, [], {}, {}

    message_lower = message.lower()
    matched_keywords = []
    partial_matches = []
    keyword_positions = {}

    # Contar ocurrencias de cada palabra clave (palabras completas y coincidencias parciales)
    keyword_counts = {}
    for keyword in keywords:
        if not keyword.strip():  # Ignorar palabras clave vacías
            continue

        keyword_lower = keyword.lower().strip()
        if not keyword_lower:  # Ignorar después de strip si está vacío
            continue

        # 1. Buscar palabras completas usando expresiones regulares
        pattern = r'\b' + re.escape(keyword_lower) + r'\b'
        matches = re.findall(pattern, message_lower)
        count = len(matches)

        # 2. Encontrar posiciones de las palabras clave para análisis de proximidad
        positions = []
        for match in re.finditer(pattern, message_lower):
            positions.append(match.start())

        if positions:
            keyword_positions[keyword_lower] = positions

        # 3. Buscar coincidencias parciales si no hay coincidencias exactas
        if count == 0 and len(keyword_lower) > 4:  # Solo para palabras clave más largas
            # Buscar coincidencias parciales (al menos 70% de la palabra)
            min_match_length = max(4, int(len(keyword_lower) * 0.7))
            for i in range(len(keyword_lower) - min_match_length + 1):
                partial = keyword_lower[i:i+min_match_length]
                if partial in message_lower:
                    partial_matches.append(keyword)
                    # Dar menos peso a las coincidencias parciales (50%)
                    if keyword not in keyword_counts:
                        keyword_counts[keyword] = 0.5
                    else:
                        keyword_counts[keyword] += 0.5
                    break

        if count > 0:
            keyword_counts[keyword] = count
            matched_keywords.append(keyword)

    # Añadir coincidencias parciales a la lista de palabras clave coincidentes
    for partial in partial_matches:
        if partial not in matched_keywords:
            matched_keywords.append(partial)

    # Si no hay coincidencias, devolver 0
    if not keyword_counts:
        return 0, [], {}, {}

    # Contar palabras totales en el mensaje
    total_words = len(re.findall(r'\b\w+\b', message_lower))

    # Contar palabras clave totales
    total_keywords = sum(keyword_counts.values())

    # Calcular densidad de palabras clave (proporción de palabras clave vs palabras totales)
    keyword_density = total_keywords / total_words if total_words > 0 else 0

    # Calcular puntuación base basada en el número de palabras clave encontradas
    base_score = min(100, (len(keyword_counts) / len(keywords)) * 100)

    # Ajustar por frecuencia de palabras clave
    frequency_score = min(100, sum(keyword_counts.values()) * 10)

    # Ajustar por densidad de palabras clave (mensajes con mayor proporción de palabras clave son más relevantes)
    density_score = min(100, keyword_density * 100)

    # 4. Calcular factor de proximidad (palabras clave cercanas entre sí son más relevantes)
    proximity_factor = 1.0
    if len(keyword_positions) > 1:
        # Calcular la distancia mínima entre palabras clave diferentes
        min_distances = []
        keywords_list = list(keyword_positions.keys())

        for i in range(len(keywords_list)):
            for j in range(i+1, len(keywords_list)):
                key1, key2 = keywords_list[i], keywords_list[j]
                for pos1 in keyword_positions[key1]:
                    for pos2 in keyword_positions[key2]:
                        distance = abs(pos1 - pos2)
                        # Normalizar distancia: más cercano = mejor puntuación
                        # Considerar distancias de hasta 50 caracteres
                        if distance < 50:
                            min_distances.append(1.0 - (distance / 50.0))

        if min_distances:
            # Promedio de las mejores 3 proximidades o todas si hay menos
            top_proximities = sorted(min_distances, reverse=True)[:min(3, len(min_distances))]
            proximity_factor = 1.0 + (sum(top_proximities) / len(top_proximities)) * 0.5  # Hasta 50% de bonificación

    # 5. Calcular factor de posición (palabras clave al principio del mensaje son más relevantes)
    position_factor = 1.0
    if keyword_positions:
        # Encontrar la posición de la primera palabra clave
        first_positions = []
        for positions in keyword_positions.values():
            if positions:
                first_positions.append(min(positions))

        if first_positions:
            first_keyword_pos = min(first_positions)
            # Si la primera palabra clave está en el primer 20% del mensaje, dar bonificación
            if total_words > 0:
                relative_position = first_keyword_pos / len(message_lower)
                if relative_position < 0.2:
                    position_factor = 1.0 + (1.0 - (relative_position / 0.2)) * 0.3  # Hasta 30% de bonificación

    # Ajustar por longitud del mensaje (mensajes más cortos con palabras clave son más relevantes)
    length_factor = 1.0
    if len(message) > 0:
        length_factor = min(1.0, 50 / len(message))

    # Calcular puntuación final con todos los factores
    final_score = (
        base_score * 0.35 +          # 35% - Diversidad de palabras clave
        frequency_score * 0.25 +     # 25% - Frecuencia de palabras clave
        density_score * 0.2          # 20% - Densidad de palabras clave
    ) * (
        0.7 +                        # Base
        length_factor * 0.1 +        # 10% - Factor de longitud
        proximity_factor * 0.1 +     # 10% - Factor de proximidad
        position_factor * 0.1        # 10% - Factor de posición
    )

    # Estadísticas adicionales para análisis de relevancia
    word_stats = {
        'total_words': total_words,
        'total_keywords': total_keywords,
        'keyword_density': keyword_density,
        'unique_keywords': len(keyword_counts),
        'proximity_factor': proximity_factor,
        'position_factor': position_factor,
        'partial_matches': len(partial_matches)
    }

    return min(100, final_score), matched_keywords, keyword_counts, word_stats

def get_message_context(data, chat_id, msg_id, contacts=None, context_size=2):
    """
    Obtiene mensajes de contexto (anteriores y siguientes) para un mensaje dado.

    Parámetros:
    - data: Datos de WhatsApp
    - chat_id: ID del chat
    - msg_id: ID del mensaje
    - contacts: Diccionario de contactos (opcional)
    - context_size: Número de mensajes de contexto a obtener

    Retorna:
    - context: Lista de mensajes de contexto
    """
    context = []

    try:
        chat_data = data.get(chat_id, {})
        messages = chat_data.get('messages', {})

        # Encontrar el índice del mensaje actual
        message_ids = list(messages.keys())
        if msg_id not in message_ids:
            return context

        current_index = message_ids.index(msg_id)

        # Obtener mensajes anteriores
        for i in range(max(0, current_index - context_size), current_index):
            prev_id = message_ids[i]
            prev_msg = messages.get(prev_id, {})

            # Obtener contenido del mensaje
            content = prev_msg.get('content', '')
            if not content:
                continue

            # Obtener información del remitente
            sender_name = prev_msg.get('sender', 'Desconocido')
            sender_id = prev_msg.get('sender_id', '')
            from_me = prev_msg.get('from_me', False)

            # Verificar si hay un remitente resuelto previamente
            if prev_msg.get('resolved_sender') and prev_msg.get('resolution_confidence', 0) > 50:
                sender_name = prev_msg['resolved_sender']

            # Si no hay sender_id pero hay sender, usar sender como sender_id
            if not sender_id and sender_name and sender_name != 'Desconocido':
                sender_id = sender_name

            # Si el sender_id es "None" o "Desconocido" como string, intentar inferirlo del contexto
            if sender_id == "None" or sender_id == "Desconocido":
                # En chats individuales, el remitente probablemente es el chat_id
                if '-' not in chat_id:  # No es un grupo
                    sender_id = chat_id

            # Intentar usar el resolvedor avanzado si está disponible
            try:
                from contact_resolver import get_resolver
                resolver = get_resolver(contacts_data=contacts, chat_data=data)
                if resolver and sender_id:
                    contact_info = resolver.resolve_contact(
                        sender_id,
                        context={"chat_id": chat_id, "message_id": prev_id}
                    )
                    if contact_info['confidence'] > 50:
                        sender_name = contact_info['display_name']
                        formatted_phone = contact_info['phone']
                    else:
                        # Formatear número de teléfono
                        formatted_phone = format_phone_number(sender_id, contacts) if sender_id else "Desconocido"
                else:
                    # Formatear número de teléfono
                    formatted_phone = format_phone_number(sender_id, contacts) if sender_id else "Desconocido"
            except Exception:
                # Si hay error con el resolvedor, usar el método tradicional
                # Formatear número de teléfono
                formatted_phone = format_phone_number(sender_id, contacts) if sender_id else "Desconocido"

                # Mejorar la visualización del remitente con información de contactos (método tradicional)
                if contacts and sender_id:
                    # Extraer el número de teléfono del sender_id (eliminar @s.whatsapp.net)
                    phone_raw = sender_id.split('@')[0] if '@' in sender_id else sender_id
                    if phone_raw in contacts:
                        contact_info = contacts[phone_raw]
                        if contact_info.get('display_name'):
                            sender_name = contact_info.get('display_name')

            # Determinar qué mostrar para el remitente
            if from_me:
                sender_display = "Yo"
            elif not sender_name or sender_name == "Desconocido":
                if sender_id and sender_id != "None" and sender_id != "Desconocido":
                    sender_display = formatted_phone
                else:
                    # Para chats individuales, usar el nombre del chat como último recurso
                    chat_data = data.get(chat_id, {})
                    chat_name = chat_data.get('name')
                    if '-' not in chat_id and chat_name and chat_name != chat_id:
                        sender_display = chat_name
                    else:
                        sender_display = "Desconocido"
            else:
                sender_display = sender_name

            # Formatear marca de tiempo
            timestamp = prev_msg.get('timestamp', 0)
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

            context.append({
                'type': 'previous',
                'sender': sender_display,
                'sender_id': sender_id,
                'phone': formatted_phone,
                'from_me': from_me,
                'date': date_str,
                'message': content
            })

        # Obtener mensajes siguientes
        for i in range(current_index + 1, min(len(message_ids), current_index + 1 + context_size)):
            next_id = message_ids[i]
            next_msg = messages.get(next_id, {})

            # Obtener contenido del mensaje
            content = next_msg.get('content', '')
            if not content:
                continue

            # Obtener información del remitente
            sender_name = next_msg.get('sender', 'Desconocido')
            sender_id = next_msg.get('sender_id', '')
            from_me = next_msg.get('from_me', False)

            # Verificar si hay un remitente resuelto previamente
            if next_msg.get('resolved_sender') and next_msg.get('resolution_confidence', 0) > 50:
                sender_name = next_msg['resolved_sender']

            # Si no hay sender_id pero hay sender, usar sender como sender_id
            if not sender_id and sender_name and sender_name != 'Desconocido':
                sender_id = sender_name

            # Si el sender_id es "None" o "Desconocido" como string, intentar inferirlo del contexto
            if sender_id == "None" or sender_id == "Desconocido":
                # En chats individuales, el remitente probablemente es el chat_id
                if '-' not in chat_id:  # No es un grupo
                    sender_id = chat_id

            # Intentar usar el resolvedor avanzado si está disponible
            try:
                from contact_resolver import get_resolver
                resolver = get_resolver(contacts_data=contacts, chat_data=data)
                if resolver and sender_id:
                    contact_info = resolver.resolve_contact(
                        sender_id,
                        context={"chat_id": chat_id, "message_id": next_id}
                    )
                    if contact_info['confidence'] > 50:
                        sender_name = contact_info['display_name']
                        formatted_phone = contact_info['phone']
                    else:
                        # Formatear número de teléfono
                        formatted_phone = format_phone_number(sender_id, contacts) if sender_id else "Desconocido"
                else:
                    # Formatear número de teléfono
                    formatted_phone = format_phone_number(sender_id, contacts) if sender_id else "Desconocido"
            except Exception:
                # Si hay error con el resolvedor, usar el método tradicional
                # Formatear número de teléfono
                formatted_phone = format_phone_number(sender_id, contacts) if sender_id else "Desconocido"

                # Mejorar la visualización del remitente con información de contactos (método tradicional)
                if contacts and sender_id:
                    # Extraer el número de teléfono del sender_id (eliminar @s.whatsapp.net)
                    phone_raw = sender_id.split('@')[0] if '@' in sender_id else sender_id
                    if phone_raw in contacts:
                        contact_info = contacts[phone_raw]
                        if contact_info.get('display_name'):
                            sender_name = contact_info.get('display_name')

            # Determinar qué mostrar para el remitente
            if from_me:
                sender_display = "Yo"
            elif not sender_name or sender_name == "Desconocido":
                if sender_id and sender_id != "None" and sender_id != "Desconocido":
                    sender_display = formatted_phone
                else:
                    # Para chats individuales, usar el nombre del chat como último recurso
                    chat_data = data.get(chat_id, {})
                    chat_name = chat_data.get('name')
                    if '-' not in chat_id and chat_name and chat_name != chat_id:
                        sender_display = chat_name
                    else:
                        sender_display = "Desconocido"
            else:
                sender_display = sender_name

            # Formatear marca de tiempo
            timestamp = next_msg.get('timestamp', 0)
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

            context.append({
                'type': 'next',
                'sender': sender_display,
                'sender_id': sender_id,
                'phone': formatted_phone,
                'from_me': from_me,
                'date': date_str,
                'message': content
            })
    except Exception as e:
        # Si hay algún error al obtener el contexto, simplemente devolver una lista vacía
        pass

    return context

def extract_messages(data, contacts=None, chat_filter=None, start_date=None, end_date=None, sender_filter=None, phone_filter=None):
    """
    Extrae mensajes de los datos de WhatsApp con filtros opcionales.

    Parámetros:
    - data: Datos de WhatsApp
    - contacts: Diccionario de contactos (opcional)
    - chat_filter: Filtro de nombre de chat (opcional)
    - start_date: Fecha de inicio (YYYY-MM-DD) (opcional)
    - end_date: Fecha de fin (YYYY-MM-DD) (opcional)
    - sender_filter: Filtro de nombre de remitente (opcional)
    - phone_filter: Filtro de número de teléfono (opcional)

    Retorna:
    - messages: Lista de mensajes extraídos
    """
    all_messages = []

    # Convertir fechas a marcas de tiempo si se proporcionan
    start_timestamp = None
    end_timestamp = None

    if start_date:
        try:
            start_timestamp = datetime.strptime(start_date, '%Y-%m-%d').timestamp()
        except ValueError:
            print(f"Formato de fecha de inicio inválido: {start_date}. Usar formato YYYY-MM-DD.")

    if end_date:
        try:
            # Establecer la hora al final del día
            end_timestamp = datetime.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S').timestamp()
        except ValueError:
            print(f"Formato de fecha de fin inválido: {end_date}. Usar formato YYYY-MM-DD.")

    # Iterar a través de los chats
    for chat_id, chat_data in data.items():
        # Extraer el número de teléfono limpio del chat_id para buscar en contactos
        chat_phone_raw = chat_id.split('@')[0] if '@' in chat_id else chat_id

        # Obtener nombre del chat
        chat_name = None

        # Primero intentar buscar directamente en los contactos
        if contacts and chat_phone_raw in contacts:
            contact_info = contacts[chat_phone_raw]
            if contact_info.get('display_name'):
                chat_name = contact_info.get('display_name')

        # Si no se encontró nombre en los contactos, usar el nombre guardado en los datos
        if not chat_name:
            chat_name = chat_data.get('name', chat_id)

            # Si el nombre sigue siendo el chat_id, intentar formatear el número
            if chat_name == chat_id:
                chat_name = format_phone_number(chat_id, contacts)

        # Aplicar filtro de chat si se proporciona
        if chat_filter and chat_filter.lower() not in chat_name.lower():
            continue

        # Obtener mensajes
        messages = chat_data.get('messages', {})

        # Iterar a través de los mensajes
        for msg_id, message in messages.items():
            # Obtener contenido del mensaje
            msg_content = message.get('content', '')
            # Si no hay contenido, intentar con data o caption
            if not msg_content:
                msg_content = message.get('data', '')
            if not msg_content and message.get('caption'):
                msg_content = message.get('caption', '')
            if not msg_content:
                continue

            # Obtener marca de tiempo
            msg_timestamp = message.get('timestamp', 0)
            # Si no hay timestamp, intentar con time
            if not msg_timestamp and message.get('time'):
                # Convertir time a timestamp si es posible
                try:
                    # Asumimos que time es una cadena con formato HH:MM
                    # y que el mensaje es de hoy
                    time_str = message.get('time', '')
                    if time_str:
                        today = datetime.now().strftime('%Y-%m-%d')
                        datetime_str = f"{today} {time_str}"
                        msg_timestamp = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M').timestamp()
                except Exception:
                    # Si hay algún error, usar 0 como timestamp
                    pass

            # Aplicar filtros de fecha
            if start_timestamp and msg_timestamp < start_timestamp:
                continue
            if end_timestamp and msg_timestamp > end_timestamp:
                continue

            # Obtener información del remitente
            sender_name = message.get('sender', 'Desconocido')
            sender_id = message.get('sender_id', '')
            from_me = message.get('from_me', False)

            # Verificar si hay un remitente resuelto previamente
            if message.get('resolved_sender') and message.get('resolution_confidence', 0) > 50:
                sender_name = message['resolved_sender']

            # Si no hay sender_id pero hay sender, usar sender como sender_id
            if not sender_id and sender_name and sender_name != 'Desconocido':
                sender_id = sender_name

            # Si el sender_id es "None" o "Desconocido" como string, intentar inferirlo del contexto
            if sender_id == "None" or sender_id == "Desconocido":
                # En chats individuales, el remitente probablemente es el chat_id
                if '-' not in chat_id:  # No es un grupo
                    sender_id = chat_id

            # Extraer número de teléfono limpio del sender_id
            sender_phone_raw = sender_id.split('@')[0] if sender_id and '@' in sender_id else sender_id

            # Buscar nombre del remitente en los contactos
            contact_name = None
            if contacts and sender_phone_raw and sender_phone_raw in contacts:
                contact_info = contacts[sender_phone_raw]
                if contact_info.get('display_name'):
                    contact_name = contact_info.get('display_name')
                    sender_name = contact_name

            # Intentar usar el resolvedor avanzado si está disponible
            try:
                from contact_resolver import get_resolver
                resolver = get_resolver(contacts_data=contacts, chat_data=data)
                if resolver and sender_id:
                    contact_info = resolver.resolve_contact(
                        sender_id,
                        context={"chat_id": chat_id, "message_id": msg_id}
                    )
                    if contact_info['confidence'] > 50:
                        sender_name = contact_info['display_name']
                        formatted_phone = contact_info['phone']
                        contact_name = sender_name
                    else:
                        # Formatear número de teléfono
                        formatted_phone = format_phone_number(sender_id, contacts) if sender_id else "Desconocido"
                else:
                    # Formatear número de teléfono
                    formatted_phone = format_phone_number(sender_id, contacts) if sender_id else "Desconocido"
            except Exception:
                # Si hay error con el resolvedor, usar el método tradicional
                formatted_phone = format_phone_number(sender_id, contacts) if sender_id else "Desconocido"

            # Determinar qué mostrar para el remitente
            if from_me:
                sender_display = "Yo"
            elif contact_name:
                # Si tenemos un nombre de contacto, usarlo
                sender_display = contact_name
            elif not sender_name or sender_name == "Desconocido":
                if sender_id and sender_id != "None" and sender_id != "Desconocido":
                    sender_display = formatted_phone
                else:
                    # Para chats individuales, usar el nombre del chat como último recurso
                    if '-' not in chat_id and chat_name and chat_name != chat_id:
                        sender_display = chat_name
                    else:
                        sender_display = "Desconocido"
            else:
                sender_display = sender_name

            # Aplicar filtro de remitente si se proporciona
            if sender_filter:
                if from_me and sender_filter.lower() in "yo":
                    pass  # Permitir coincidencia con "yo" para mensajes propios
                elif not from_me and sender_filter.lower() not in sender_display.lower():
                    continue

            # Aplicar filtro de teléfono si se proporciona
            if phone_filter and (not sender_id or phone_filter not in sender_id):
                continue

            # Formatear marca de tiempo como fecha legible
            date_str = datetime.fromtimestamp(msg_timestamp).strftime('%Y-%m-%d %H:%M:%S')

            # Añadir mensaje a la lista
            all_messages.append({
                'chat_id': chat_id,
                'chat_name': chat_name,
                'msg_id': msg_id,
                'sender': sender_display,
                'sender_id': sender_id,
                'phone': formatted_phone,
                'contact_name': contact_name,
                'from_me': from_me,
                'date': date_str,
                'timestamp': msg_timestamp,
                'message': msg_content
            })

    return all_messages

# Import format_phone_number from whatsapp_core to avoid circular imports
from whatsapp_core import format_phone_number
