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

def format_phone_number(phone, contacts=None):
    """
    Formatea un número de teléfono para hacerlo más legible.
    Si se proporcionan contactos, intenta encontrar el nombre del contacto.

    Parámetros:
    - phone: Número de teléfono a formatear
    - contacts: Diccionario de contactos (opcional)

    Retorna:
    - formatted_phone: Número de teléfono formateado o nombre del contacto
    """
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

def check_ml_dependencies():
    """
    Verifica si las dependencias de Machine Learning están instaladas.

    Retorna:
    - installed: True si están instaladas, False en caso contrario
    """
    try:
        import sklearn
        import nltk
        import spacy
        import textblob
        import sentence_transformers
        import transformers
        import torch
        return True
    except ImportError:
        return False

def install_ml_dependencies():
    """
    Instala las dependencias de Machine Learning.

    Retorna:
    - success: True si se instalaron correctamente, False en caso contrario
    """
    try:
        import subprocess
        import sys

        print("Instalando dependencias de Machine Learning...")

        # Lista de paquetes a instalar
        packages = [
            "scikit-learn",
            "nltk",
            "spacy",
            "textblob",
            "sentence-transformers",
            "transformers",
            "torch",
            "tqdm"
        ]

        # Instalar paquetes
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)

        # Descargar modelos de NLTK
        import nltk
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('wordnet')

        # Descargar modelo de spaCy
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "es_core_news_sm"])

        print("Dependencias instaladas correctamente.")
        return True
    except Exception as e:
        print(f"Error al instalar dependencias: {e}")
        return False
