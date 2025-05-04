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

    Parámetros:
    - message: Contenido del mensaje
    - keywords: Lista de palabras clave a buscar

    Retorna:
    - score: Puntuación de relevancia (0-100)
    - matched_keywords: Lista de palabras clave encontradas
    - keyword_counts: Diccionario con el conteo de cada palabra clave
    """
    if not message or not keywords:
        return 0, [], {}

    message_lower = message.lower()
    matched_keywords = []

    # Contar ocurrencias de cada palabra clave (solo palabras completas)
    keyword_counts = {}
    for keyword in keywords:
        if not keyword.strip():  # Ignorar palabras clave vacías
            continue

        keyword_lower = keyword.lower().strip()
        if not keyword_lower:  # Ignorar después de strip si está vacío
            continue

        # Buscar palabras completas usando expresiones regulares
        pattern = r'\b' + re.escape(keyword_lower) + r'\b'
        matches = re.findall(pattern, message_lower)
        count = len(matches)

        if count > 0:
            keyword_counts[keyword] = count
            matched_keywords.append(keyword)

    # Si no hay coincidencias, devolver 0
    if not keyword_counts:
        return 0, [], {}

    # Calcular puntuación base basada en el número de palabras clave encontradas
    base_score = min(100, (len(keyword_counts) / len(keywords)) * 100)

    # Ajustar por frecuencia de palabras clave
    frequency_score = min(100, sum(keyword_counts.values()) * 10)

    # Ajustar por longitud del mensaje (mensajes más cortos con palabras clave son más relevantes)
    length_factor = 1.0
    if len(message) > 0:
        length_factor = min(1.0, 50 / len(message))

    # Calcular puntuación final
    final_score = (base_score * 0.5 + frequency_score * 0.3) * (0.7 + length_factor * 0.3)

    return min(100, final_score), matched_keywords, keyword_counts

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

            # Formatear número de teléfono
            formatted_phone = format_phone_number(sender_id, contacts) if sender_id else "Desconocido"

            # Mejorar la visualización del remitente con información de contactos
            if contacts and sender_id:
                # Extraer el número de teléfono del sender_id (eliminar @s.whatsapp.net)
                phone_raw = sender_id.split('@')[0] if '@' in sender_id else sender_id
                if phone_raw in contacts:
                    contact_info = contacts[phone_raw]
                    if contact_info.get('display_name'):
                        sender_name = contact_info.get('display_name')

            if from_me:
                sender_display = "Yo"
            elif not sender_name or sender_name == "Desconocido":
                if sender_id:
                    sender_display = formatted_phone
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

            # Formatear número de teléfono
            formatted_phone = format_phone_number(sender_id, contacts) if sender_id else "Desconocido"

            # Mejorar la visualización del remitente con información de contactos
            if contacts and sender_id:
                # Extraer el número de teléfono del sender_id (eliminar @s.whatsapp.net)
                phone_raw = sender_id.split('@')[0] if '@' in sender_id else sender_id
                if phone_raw in contacts:
                    contact_info = contacts[phone_raw]
                    if contact_info.get('display_name'):
                        sender_name = contact_info.get('display_name')

            if from_me:
                sender_display = "Yo"
            elif not sender_name or sender_name == "Desconocido":
                if sender_id:
                    sender_display = formatted_phone
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

            # Si no hay sender_id pero hay sender, usar sender como sender_id
            if not sender_id and sender_name and sender_name != 'Desconocido':
                sender_id = sender_name

            # Extraer número de teléfono limpio del sender_id
            sender_phone_raw = sender_id.split('@')[0] if sender_id and '@' in sender_id else sender_id
            
            # Buscar nombre del remitente en los contactos
            contact_name = None
            if contacts and sender_phone_raw and sender_phone_raw in contacts:
                contact_info = contacts[sender_phone_raw]
                if contact_info.get('display_name'):
                    contact_name = contact_info.get('display_name')
                    sender_name = contact_name
            
            # Formatear número de teléfono
            formatted_phone = format_phone_number(sender_id, contacts) if sender_id else "Desconocido"

            if from_me:
                sender_display = "Yo"
            elif contact_name:
                # Si tenemos un nombre de contacto, usarlo
                sender_display = contact_name
            elif not sender_name or sender_name == "Desconocido":
                if sender_id:
                    sender_display = formatted_phone
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
