#!/usr/bin/env python3
"""
WhatsApp Core Module

Este módulo contiene funciones centrales compartidas por todas las herramientas
de análisis y búsqueda de WhatsApp.
"""

import json
import os
import re
from datetime import datetime
import time
from typing import Dict, List, Optional, Tuple, Union, Any

# Importar el nuevo sistema de resolución de contactos
from contact_resolver import get_resolver, ContactResolver

def load_json_data(file_path):
    """
    Carga datos de WhatsApp desde un archivo JSON.

    Parámetros:
    - file_path: Ruta al archivo JSON

    Retorna:
    - data: Datos de WhatsApp cargados
    """
    print(f"Cargando datos desde {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Datos cargados correctamente. Se encontraron {len(data)} chats.")
        return data
    except Exception as e:
        print(f"Error al cargar datos: {e}")
        return None

def load_contacts(file_path):
    """
    Carga información de contactos desde un archivo JSON.

    Parámetros:
    - file_path: Ruta al archivo JSON de contactos

    Retorna:
    - contacts: Diccionario de contactos
    """
    if not file_path or not os.path.exists(file_path):
        print(f"Archivo de contactos no encontrado: {file_path}")
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            contacts = json.load(f)
        print(f"Contactos cargados correctamente. Se encontraron {len(contacts)} contactos.")
        return contacts
    except Exception as e:
        print(f"Error al cargar contactos: {e}")
        return {}

def format_phone_number(phone, contacts=None, data=None, context=None):
    """
    Formatea un número de teléfono para hacerlo más legible.
    Si se proporcionan contactos, intenta encontrar el nombre del contacto.
    
    Versión mejorada que usa el ContactResolver si está disponible.

    Parámetros:
    - phone: Número de teléfono a formatear
    - contacts: Diccionario de contactos (opcional)
    - data: Datos de WhatsApp (opcional, para resolver contexto)
    - context: Información adicional de contexto (opcional)

    Retorna:
    - formatted_phone: Número de teléfono formateado o nombre del contacto
    """
    # Usar el sistema de resolución avanzado si hay contactos o datos disponibles
    if contacts or data:
        try:
            resolver = get_resolver(contacts_data=contacts, chat_data=data)
            result = resolver.resolve_contact(
                phone, 
                context=context or {},
                fallback="Desconocido"
            )
            return result['display_name']
        except Exception as e:
            # En caso de error, usar la implementación original
            print(f"Error en resolución avanzada: {e}")
            pass
    
    # Implementación original para compatibilidad
    if not phone or not isinstance(phone, str):
        return "Desconocido"

    # Si ya es un nombre (contiene letras), devolver tal cual
    if any(c.isalpha() for c in phone):
        return phone

    # Extraer el número de teléfono (eliminar @s.whatsapp.net)
    phone_raw = phone.split('@')[0] if '@' in phone else phone
    
    # Extraer el número de teléfono (eliminar -grupo)
    if '-' in phone_raw:
        # Si es un grupo, extraer solo el número de creador del grupo
        phone_raw = phone_raw.split('-')[0] 

    # Limpiar el número para comparación
    clean_phone = ''.join(c for c in phone_raw if c.isdigit())

    # Obtener nombre del contacto si está disponible
    contact_name = None
    if contacts:
        # Buscar coincidencia exacta
        if phone_raw in contacts:
            contact_info = contacts[phone_raw]
            if contact_info.get('display_name'):
                contact_name = contact_info.get('display_name')
        else:
            # Buscar por número limpio
            for contact_id, contact_data in contacts.items():
                # Limpiar el número de contacto para comparación
                contact_clean = ''.join(c for c in contact_id if c.isdigit())
                contact_phone_raw = contact_data.get('phone_raw', '')
                contact_phone_clean = ''.join(c for c in contact_phone_raw if c.isdigit())

                # Comparar números limpios
                if (clean_phone == contact_clean or
                    clean_phone == contact_phone_clean or
                    clean_phone.endswith(contact_clean) or
                    contact_clean.endswith(clean_phone) or
                    clean_phone.endswith(contact_phone_clean) or
                    contact_phone_clean.endswith(clean_phone)):

                    if contact_data.get('display_name'):
                        contact_name = contact_data.get('display_name')
                        break

    # Si se encontró un contacto, devolver su nombre
    if contact_name:
        return contact_name

    # Formatear el número independientemente de si encontramos un contacto
    # Asegurar que siempre incluya código de país

    # Si está vacío después de limpiar
    if not clean_phone:
        return "Desconocido"

    # Asegurar que tenga código de país
    if len(clean_phone) <= 10:  # Probablemente sin código de país
        # Asumir que es +52 (México) o ajustar según el país predeterminado
        clean_phone = "52" + clean_phone
    elif len(clean_phone) > 13:  # Probablemente tiene dígitos extra
        # Usar los últimos 12-13 dígitos (típicamente código de país + número)
        clean_phone = clean_phone[-13:]
    
    # Formatear uniformemente 
    # Formato: +XX XXX XXX-XXXX
    if len(clean_phone) >= 10:
        # Extraer las partes
        country_code = clean_phone[:-10]
        if not country_code:
            country_code = "52"  # Default para México, ajustar según necesidad
        
        area_code = clean_phone[-10:-7]
        first_part = clean_phone[-7:-4]
        last_part = clean_phone[-4:]
        
        formatted_number = f"+{country_code} {area_code} {first_part}-{last_part}"
    else:
        formatted_number = f"+{clean_phone}"
    
    return formatted_number

# Nuevas funciones para aprovechar más capacidades del resolvedor
def get_contact_info(identifier, contacts=None, data=None, context=None):
    """
    Versión extendida que devuelve información completa del contacto.
    
    Parámetros:
    - identifier: Identificador del contacto (número, ID, etc.)
    - contacts: Diccionario de contactos
    - data: Datos de WhatsApp
    - context: Información de contexto
    
    Retorna:
    - Dict con información detallada del contacto
    """
    try:
        resolver = get_resolver(contacts_data=contacts, chat_data=data)
        return resolver.resolve_contact(identifier, context=context)
    except Exception as e:
        print(f"Error obteniendo información de contacto: {e}")
        return {
            'display_name': format_phone_number(identifier, contacts),
            'phone': identifier,
            'confidence': 0,
            'source': 'fallback'
        }

def suggest_chat_name(chat_id, contacts=None, data=None):
    """
    Sugiere un nombre para un chat sin nombre (None).
    
    Parámetros:
    - chat_id: ID del chat
    - contacts: Diccionario de contactos
    - data: Datos de WhatsApp
    
    Retorna:
    - Nombre sugerido para el chat
    """
    try:
        resolver = get_resolver(contacts_data=contacts, chat_data=data)
        return resolver.suggest_chat_name(chat_id)
    except Exception as e:
        print(f"Error sugiriendo nombre de chat: {e}")
        return format_phone_number(chat_id, contacts)

def resolve_unknown_participants(data, contacts=None, threshold=50):
    """
    Procesa todos los chats y resuelve participantes desconocidos.
    
    Parámetros:
    - data: Datos de WhatsApp
    - contacts: Diccionario de contactos
    - threshold: Umbral de confianza mínimo para aceptar resoluciones
    
    Retorna:
    - Datos procesados con resoluciones
    """
    if not data or not contacts:
        return data
        
    try:
        # Inicializar el resolvedor
        resolver = get_resolver(contacts_data=contacts, chat_data=data)
        
        # Procesar nombres de chats
        for chat_id, chat_info in data.items():
            if not chat_info.get('name') or chat_info.get('name') == "None":
                suggested_name = resolver.suggest_chat_name(chat_id)
                chat_info['suggested_name'] = suggested_name
        
        # Procesar remitentes desconocidos
        for chat_id, chat_info in data.items():
            messages = chat_info.get('messages', {})
            
            for msg_id, msg in messages.items():
                sender_id = msg.get('sender_id', '')
                
                if sender_id and (not msg.get('sender') or msg.get('sender') == "Desconocido"):
                    # Usar contexto del chat actual
                    contact_info = resolver.resolve_contact(
                        sender_id,
                        context={"chat_id": chat_id}
                    )
                    
                    if contact_info['confidence'] > threshold:
                        msg['resolved_sender'] = contact_info['display_name']
                        msg['resolution_confidence'] = contact_info['confidence']
                        msg['resolution_source'] = contact_info['source']
    except Exception as e:
        print(f"Error procesando participantes desconocidos: {e}")
    
    return data

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
    
    Versión mejorada para usar el ContactResolver cuando esté disponible.

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
    
    # Inicializar resolvedor si hay contactos disponibles
    resolver = None
    if contacts:
        try:
            resolver = get_resolver(contacts_data=contacts, chat_data=data)
        except:
            pass

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

            # Usar el resolvedor avanzado si está disponible
            if resolver and sender_id:
                contact_info = resolver.resolve_contact(
                    sender_id, 
                    context={"chat_id": chat_id, "message_id": prev_id}
                )
                if contact_info['confidence'] > 50:
                    sender_name = contact_info['display_name']
                    formatted_phone = contact_info['phone']
            else:
                # Formatear número de teléfono con método tradicional
                formatted_phone = format_phone_number(sender_id, contacts) if sender_id else "Desconocido"
                
                # Mejorar la visualización del remitente con información de contactos (método tradicional)
                if contacts and sender_id:
                    phone_raw = sender_id.split('@')[0] if '@' in sender_id else sender_id
                    if phone_raw in contacts:
                        contact_info = contacts[phone_raw]
                        if contact_info.get('display_name'):
                            sender_name = contact_info.get('display_name')

            # Determinar qué mostrar para el remitente
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

        # Obtener mensajes siguientes (usar la misma lógica que para mensajes anteriores)
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

            # Usar el resolvedor avanzado si está disponible
            if resolver and sender_id:
                contact_info = resolver.resolve_contact(
                    sender_id, 
                    context={"chat_id": chat_id, "message_id": next_id}
                )
                if contact_info['confidence'] > 50:
                    sender_name = contact_info['display_name']
                    formatted_phone = contact_info['phone']
            else:
                # Formatear número de teléfono de manera tradicional
                formatted_phone = format_phone_number(sender_id, contacts) if sender_id else "Desconocido"
                
                # Mejorar la visualización del remitente con información de contactos (método tradicional)
                if contacts and sender_id:
                    phone_raw = sender_id.split('@')[0] if '@' in sender_id else sender_id
                    if phone_raw in contacts:
                        contact_info = contacts[phone_raw]
                        if contact_info.get('display_name'):
                            sender_name = contact_info.get('display_name')

            # Determinar qué mostrar para el remitente
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
        print(f"Error al obtener contexto: {e}")
        pass

    return context

def extract_messages(data, contacts=None, chat_filter=None, start_date=None, end_date=None, sender_filter=None, phone_filter=None):
    """
    Extrae mensajes de WhatsApp con varios filtros.
    
    Versión mejorada para usar el ContactResolver cuando esté disponible.

    Parámetros:
    - data: Datos de WhatsApp
    - contacts: Diccionario de contactos (opcional)
    - chat_filter: Filtro por nombre de chat (opcional)
    - start_date: Fecha de inicio en formato YYYY-MM-DD (opcional)
    - end_date: Fecha de fin en formato YYYY-MM-DD (opcional)
    - sender_filter: Filtro por nombre de remitente (opcional)
    - phone_filter: Filtro por número de teléfono (opcional)

    Retorna:
    - all_messages: Lista de mensajes que coinciden con los filtros
    """
    all_messages = []
    
    # Variables para filtrado por fecha
    start_timestamp = None
    end_timestamp = None
    
    # Inicializar resolvedor si hay contactos disponibles
    resolver = None
    if contacts:
        try:
            resolver = get_resolver(contacts_data=contacts, chat_data=data)
        except Exception as e:
            print(f"Error al inicializar resolvedor: {e}")
    
    # Convertir fechas a timestamps si se proporcionan
    if start_date:
        try:
            # Establecer la hora al inicio del día
            start_timestamp = datetime.strptime(start_date + ' 00:00:00', '%Y-%m-%d %H:%M:%S').timestamp()
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
        
        # Obtener nombre del chat usando el resolvedor avanzado si está disponible
        if resolver:
            chat_name = resolver.suggest_chat_name(chat_id)
        else:
            # Usar la lógica original para mantener compatibilidad
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
            
            # Intentar usar el remitente resuelto previamente
            if message.get('resolved_sender') and message.get('resolution_confidence', 0) > 50:
                sender_name = message['resolved_sender']

            # Si no hay sender_id pero hay sender, usar sender como sender_id
            if not sender_id and sender_name and sender_name != 'Desconocido':
                sender_id = sender_name

            # Si tenemos un resolvedor, intentar resolver el remitente
            if resolver and sender_id and (sender_name == 'Desconocido' or sender_name == sender_id):
                contact_info = resolver.resolve_contact(
                    sender_id, 
                    context={"chat_id": chat_id, "message_id": msg_id}
                )
                if contact_info['confidence'] > 50:
                    sender_name = contact_info['display_name']
                    formatted_phone = contact_info['phone']
            else:
                # Formatear número de teléfono de manera tradicional
                formatted_phone = format_phone_number(sender_id, contacts) if sender_id else "Desconocido"
                
                # Buscar nombre del remitente en los contactos (método tradicional)
                contact_name = None
                if contacts and sender_id:
                    sender_phone_raw = sender_id.split('@')[0] if sender_id and '@' in sender_id else sender_id
                    
                    if sender_phone_raw in contacts:
                        contact_info = contacts[sender_phone_raw]
                        if contact_info.get('display_name'):
                            contact_name = contact_info.get('display_name')
                            sender_name = contact_name

            # Determinar qué mostrar para el remitente
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
                'contact_name': contact_name if 'contact_name' in locals() else None,
                'from_me': from_me,
                'date': date_str,
                'timestamp': msg_timestamp,
                'message': msg_content
            })

    return all_messages

def print_results(results, show_context=True, show_contact_relevance=False, contacts=None):
    """
    Imprime resultados de búsqueda en un formato legible y optimizado.

    Parámetros:
    - results: Lista de resultados de búsqueda o diccionario con resultados y relevancia de contactos
    - show_context: Si se deben mostrar mensajes de contexto
    - show_contact_relevance: Si se debe mostrar la relevancia de contactos (obsoleto - ya no se usa)
    - contacts: Diccionario de contactos (opcional)
    """
    # Verificar si es un diccionario con resultados y relevancia de contactos
    if isinstance(results, dict) and 'results' in results:
        message_results = results['results']
    else:
        message_results = results

    if not message_results:
        print("\nNo se encontraron mensajes coincidentes con los criterios de búsqueda.")
        return

    print(f"\nSe encontraron {len(message_results)} mensajes coincidentes:\n")

    # Usar línea separadora más sutil
    separator = "─" * 50

    for i, result in enumerate(message_results, 1):
        # Título del resultado con formato más compacto
        print(f"Resultado {i}" + (f" ({result.get('score', 0):.1f})" if 'score' in result else ""))
        
        # Organizar información en un formato más conciso
        # 1. Información del chat (siempre visible)
        chat_name = result.get('chat_name', "")
        if chat_name is None or chat_name == "None":
            chat_name = "Chat sin nombre"
            
        # 2. Información de dirección y tipo (si está disponible)
        if 'destination_info' in result:
            dest_info = result['destination_info']
            direction = dest_info.get('direction', '').capitalize()
            chat_type = dest_info.get('chat_type')
            
            # Mostrar tipo y dirección juntos si ambos están disponibles
            if chat_type == 'group':
                print(f"Chat: {chat_name} (Grupo) • {direction}")
            elif chat_type == 'individual':
                recipient = dest_info.get('recipient_name', '')
                if recipient and recipient != "Yo" and recipient != chat_name:
                    print(f"Chat: {chat_name} • {direction} • Destinatario: {recipient}")
                else:
                    print(f"Chat: {chat_name} • {direction}")
            else:
                print(f"Chat: {chat_name} • {direction}")
        else:
            print(f"Chat: {chat_name}")
            
        # 3. Información del remitente (formato compacto)
        if result.get('from_me'):
            print(f"De: Yo")
        else:
            sender_info = result.get('sender', 'Desconocido')
            phone_info = result.get('phone', 'Desconocido')

            if sender_info == phone_info or sender_info == result.get('sender_id', ''):
                print(f"De: {phone_info}")
            else:
                print(f"De: {sender_info}")
                
        # 4. Fecha del mensaje
        print(f"Fecha: {result.get('date', 'Desconocido')}")

        # 5. Palabras clave coincidentes (si existen)
        if 'matched_keywords' in result and result['matched_keywords']:
            print(f"Coincidencias: {', '.join(result['matched_keywords'])}")

        # 6. Mensaje con formato destacado
        print(f"\n{result.get('message', '')}\n")

        # 7. Contexto (si está disponible y se solicita)
        if show_context and 'context' in result and result['context']:
            print("Contexto:")
            for ctx in result['context']:
                prefix = "↑ " if ctx['type'] == 'previous' else "↓ "

                # Formatear remitente para mensajes de contexto
                if ctx.get('from_me'):
                    ctx_sender = "Yo"
                else:
                    ctx_sender = ctx.get('sender', 'Desconocido')
                    if ctx_sender is None:
                        ctx_sender = "Desconocido"

                print(f"  {prefix}[{ctx['date']}] {ctx_sender}: {ctx['message']}")
            print()

        print(separator + "\n")

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
    # ... (código existente) ...

def check_ml_dependencies():
    """
    Verifica si las dependencias para machine learning están instaladas.

    Retorna:
    - installed: True si están instaladas, False en caso contrario
    """
    # ... (código existente) ...

def install_ml_dependencies():
    """
    Instala las dependencias para machine learning.

    Retorna:
    - success: True si se instalaron correctamente, False en caso contrario
    """
    # ... (código existente) ...
