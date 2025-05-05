#!/usr/bin/env python3
"""
Contact Resolver Module

Este módulo proporciona un sistema avanzado para resolver identidades de contactos
entre diferentes formatos y fuentes, solucionando problemas como contactos "Desconocido" 
y chats con nombre "None".
"""

import re
import unicodedata
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union, Any


class ContactResolver:
    """
    Sistema avanzado para resolver identidades de contactos entre diferentes formatos y fuentes.
    """
    
    def __init__(self, contacts_data: dict = None, chat_data: dict = None):
        """
        Inicializa el resolvedor de contactos.

        Args:
            contacts_data: Diccionario de contactos (cargado desde whatsapp_contacts.json)
            chat_data: Datos de chats de WhatsApp (cargado desde result.json)
        """
        self.contacts_data = contacts_data or {}
        self.chat_data = chat_data or {}
        self.resolved_cache = {}  # Caché de resoluciones para evitar recálculos
        self.correction_map = {}  # Mapa de correcciones manuales
        self.phone_patterns = self._compile_phone_patterns()
        self._build_indexes()
        
        # Nuevo: Cache para información de chats (destino)
        self.chat_info_cache = {}
    
    def _compile_phone_patterns(self) -> Dict[str, re.Pattern]:
        """Crea patrones regex para diferentes formatos de teléfono."""
        return {
            'standard': re.compile(r'^\+?(\d{1,3})?[\s-]?(\d{3})[\s-]?(\d{3,4})[\s-]?(\d{4})$'),
            'whatsapp_id': re.compile(r'^(\d+)@s\.whatsapp\.net$'),
            'group_id': re.compile(r'^(\d+)-(\d+)$'),
        }
    
    def _build_indexes(self) -> None:
        """
        Construye índices para búsqueda eficiente:
        - Índice por número normalizado
        - Índice por nombre 
        - Índice de contactos frecuentes por chat
        - Índice de co-ocurrencias (quién aparece con quién)
        """
        self.number_index = {}
        self.name_index = {}
        self.chat_contacts_index = {}
        self.co_occurrence_index = {}
        
        # Construir índices a partir de los datos de contactos
        for contact_id, info in self.contacts_data.items():
            normalized_number = self._normalize_phone_number(contact_id)
            if normalized_number:
                self.number_index[normalized_number] = contact_id
            
            # Indexar por nombre si está disponible
            if 'display_name' in info and info['display_name']:
                name_key = self._normalize_name(info['display_name'])
                if name_key:
                    self.name_index[name_key] = contact_id
        
        # Analizar chats para crear índices contextuales si hay datos de chat
        if self.chat_data:
            self._build_contextual_indexes()
    
    def _build_contextual_indexes(self) -> None:
        """Construye índices basados en el contexto de los chats."""
        for chat_id, chat_info in self.chat_data.items():
            # Indexar participantes por chat
            participants = set()
            messages = chat_info.get('messages', {})
            
            for msg_id, msg in messages.items():
                sender_id = msg.get('sender_id', '')
                if sender_id:
                    participants.add(sender_id)
                    
            self.chat_contacts_index[chat_id] = participants
            
            # Construir índice de co-ocurrencia para chats grupales
            if len(participants) > 2:  # Es un chat grupal
                for p1 in participants:
                    if p1 not in self.co_occurrence_index:
                        self.co_occurrence_index[p1] = {}
                    
                    for p2 in participants:
                        if p1 != p2:
                            self.co_occurrence_index[p1][p2] = self.co_occurrence_index[p1].get(p2, 0) + 1
    
    def _normalize_phone_number(self, number: str) -> Optional[str]:
        """
        Normaliza un número telefónico a formato estándar E.164.
        Elimina todos los caracteres no numéricos excepto el signo +.
        """
        if not number or not isinstance(number, str):
            return None
            
        # Manejar IDs de WhatsApp
        if '@' in number:
            number = number.split('@')[0]
            
        # Manejar IDs de grupo
        if '-' in number:
            # Para grupos, devolver el ID tal cual
            return number
            
        # Normalizar a solo dígitos y +
        normalized = ''.join(c for c in number if c.isdigit() or c == '+')
        
        # Asegurar que tenga código de país
        if normalized and not normalized.startswith('+'):
            if len(normalized) <= 10:
                # Asumir código de país predeterminado (México)
                normalized = '+52' + normalized
            else:
                normalized = '+' + normalized
                
        return normalized
    
    def _normalize_name(self, name: str) -> Optional[str]:
        """Normaliza un nombre para comparación insensible a caso y acentos."""
        if not name:
            return None
            
        # Convertir a minúsculas
        normalized = name.lower()
        
        # Eliminar caracteres no alfanuméricos
        # Usamos un enfoque más simple para evitar dependencias
        result = ''
        for c in normalized:
            if c.isalnum() or c.isspace():
                result += c
                
        return result.strip()
    
    def resolve_contact(self, identifier: str, context: Dict[str, Any] = None, 
                        fallback: str = "Desconocido") -> Dict[str, Any]:
        """
        Encuentra el nombre de contacto para un identificador con múltiples estrategias.
        
        Args:
            identifier: El ID a resolver (número, ID de WA, etc.)
            context: Información de contexto (chat_id, mensajes cercanos, etc.)
            fallback: Valor a devolver si no se puede resolver
            
        Returns:
            dict: Información de contacto con campos como:
                 - display_name: Nombre para mostrar
                 - phone: Número formateado
                 - confidence: Nivel de confianza (0-100)
        """
        # Verificar que no sea None o vacío
        if not identifier:
            return {
                'display_name': fallback,
                'phone': fallback,
                'confidence': 0,
                'source': 'empty_input'
            }
            
        # Verificar caché primero
        if identifier in self.resolved_cache:
            return self.resolved_cache[identifier]
            
        # Verificar correcciones manuales
        if identifier in self.correction_map:
            result = self.correction_map[identifier]
            self.resolved_cache[identifier] = result
            return result
        
        # Preparar resultado predeterminado
        result = {
            'display_name': fallback,
            'phone': self._format_for_display(identifier),
            'confidence': 0,
            'source': 'default'
        }
        
        # Estrategia 1: Búsqueda directa en contacts_data
        if identifier in self.contacts_data:
            contact_info = self.contacts_data[identifier]
            if contact_info.get('display_name'):
                result = {
                    'display_name': contact_info['display_name'],
                    'phone': self._format_for_display(identifier),
                    'confidence': 100,
                    'source': 'direct_match'
                }
                self.resolved_cache[identifier] = result
                return result
        
        # Estrategia 2: Normalizar y buscar en índice de números
        normalized = self._normalize_phone_number(identifier)
        if normalized and normalized in self.number_index:
            contact_id = self.number_index[normalized]
            contact_info = self.contacts_data.get(contact_id, {})
            if contact_info.get('display_name'):
                result = {
                    'display_name': contact_info['display_name'],
                    'phone': self._format_for_display(identifier),
                    'confidence': 95,
                    'source': 'normalized_match'
                }
                self.resolved_cache[identifier] = result
                return result
        
        # Estrategia 3: Coincidencia difusa de números
        if normalized and not '-' in normalized:  # No aplicar a grupos
            best_match = None
            best_score = 0
            
            for idx_num in self.number_index:
                if '-' in idx_num:  # Saltar grupos
                    continue
                    
                # Comparar sufijos (últimos dígitos)
                if len(normalized) >= 5 and len(idx_num) >= 5:
                    if normalized[-5:] == idx_num[-5:]:
                        score = 80
                        
                        # Bonus por más dígitos coincidentes
                        i = 6
                        while i <= min(len(normalized), len(idx_num)):
                            if normalized[-i:] == idx_num[-i:]:
                                score += 2
                            else:
                                break
                            i += 1
                            
                        if score > best_score:
                            best_score = score
                            best_match = self.number_index[idx_num]
            
            if best_match:
                contact_info = self.contacts_data.get(best_match, {})
                if contact_info.get('display_name'):
                    result = {
                        'display_name': contact_info['display_name'],
                        'phone': self._format_for_display(identifier),
                        'confidence': best_score,
                        'source': 'fuzzy_match'
                    }
                    # No cacheamos resultados difusos de baja confianza para dar
                    # oportunidad a mejores resoluciones futuras
                    if best_score > 85:
                        self.resolved_cache[identifier] = result
                    return result
        
        # Estrategia 4: Usar información contextual
        if context and 'chat_id' in context:
            chat_id = context['chat_id']
            result_from_context = self._resolve_from_context(identifier, chat_id)
            
            if result_from_context and result_from_context['confidence'] > result['confidence']:
                result = result_from_context
                # No cacheamos resultados contextuales de baja confianza
                if result['confidence'] > 80:
                    self.resolved_cache[identifier] = result
                return result
        
        # Almacenar en caché resultados definitivos
        if result['confidence'] > 50:
            self.resolved_cache[identifier] = result
            
        return result
    
    def resolve_chat_info(self, chat_id: str) -> Dict[str, Any]:
        """
        Resuelve la información del chat (destino del mensaje).
        
        Args:
            chat_id: ID del chat
            
        Returns:
            dict: Información del chat con campos como:
                 - display_name: Nombre del chat para mostrar
                 - type: Tipo de chat (individual, grupo)
                 - participants: Lista de participantes (si es un grupo)
        """
        # Verificar caché primero
        if chat_id in self.chat_info_cache:
            return self.chat_info_cache[chat_id]
            
        result = {
            'chat_id': chat_id,
            'display_name': "Chat desconocido",
            'type': 'unknown',
            'participants': [],
            'confidence': 0
        }
        
        # Si no hay datos de chat, devolver resultado predeterminado
        if not self.chat_data or chat_id not in self.chat_data:
            return result
            
        chat_info = self.chat_data.get(chat_id, {})
        
        # Determinar tipo de chat (grupo o individual)
        is_group = '-' in chat_id
        result['type'] = 'group' if is_group else 'individual'
        
        # Obtener nombre del chat
        if chat_info.get('name') and chat_info.get('name') != "None":
            result['display_name'] = chat_info['name']
            result['confidence'] = 100
        else:
            # Usar el resolvedor para sugerir un nombre
            suggested_name = self.suggest_chat_name(chat_id)
            result['display_name'] = suggested_name
            result['confidence'] = 80
            
        # Para grupos, recopilar información de participantes
        if is_group and chat_id in self.chat_contacts_index:
            participants = []
            for participant_id in self.chat_contacts_index[chat_id]:
                if participant_id:
                    # Resolver contacto de cada participante
                    contact_info = self.resolve_contact(participant_id, context={'chat_id': chat_id})
                    participants.append({
                        'id': participant_id,
                        'name': contact_info['display_name'],
                        'phone': contact_info['phone']
                    })
                    
            result['participants'] = participants
            
        # Guardar en caché para futuras consultas
        self.chat_info_cache[chat_id] = result
        
        return result
    
    def get_message_destination_info(self, message: Dict[str, Any], chat_id: str) -> Dict[str, Any]:
        """
        Obtiene información completa sobre el destinatario y destino de un mensaje.
        
        Args:
            message: Datos del mensaje
            chat_id: ID del chat donde se envió el mensaje
            
        Returns:
            dict: Información completa sobre el destino del mensaje:
                 - sender: Información sobre el remitente
                 - chat: Información sobre el chat (destino)
                 - recipient: Información sobre el destinatario específico (en chats individuales)
        """
        result = {
            'sender': {},
            'chat': {},
            'recipient': {},
            'is_outgoing': message.get('from_me', False)
        }
        
        # Obtener información del chat (destino)
        chat_info = self.resolve_chat_info(chat_id)
        result['chat'] = chat_info
        
        # Obtener información del remitente
        sender_id = message.get('sender_id', '')
        if not sender_id and message.get('sender'):
            sender_id = message.get('sender')
            
        if sender_id:
            sender_info = self.resolve_contact(
                sender_id, 
                context={'chat_id': chat_id, 'message_id': message.get('key_id', '')}
            )
            result['sender'] = sender_info
        else:
            result['sender'] = {
                'display_name': message.get('from_me', False) and "Yo" or "Desconocido",
                'phone': "Desconocido",
                'confidence': 0
            }
        
        # Para chats individuales, el destinatario es el otro participante
        if chat_info['type'] == 'individual':
            # Si el mensaje es saliente (from_me=True), el destinatario es el contacto asociado con el chat_id
            if message.get('from_me', False):
                recipient_id = chat_id
                recipient_info = self.resolve_contact(
                    recipient_id,
                    context={'chat_id': chat_id}
                )
                result['recipient'] = recipient_info
            # Si el mensaje es entrante, el destinatario soy yo
            else:
                result['recipient'] = {
                    'display_name': "Yo",
                    'phone': "Yo",
                    'confidence': 100,
                    'source': 'self'
                }
        else:
            # En grupos, el destinatario es el grupo en general
            result['recipient'] = {
                'display_name': chat_info['display_name'],
                'type': 'group',
                'confidence': chat_info['confidence']
            }
            
        return result
    
    def _resolve_from_context(self, identifier: str, chat_id: str) -> Optional[Dict[str, Any]]:
        """Intenta resolver un identificador usando el contexto del chat."""
        # Si es un chat individual, probablemente es la otra persona
        if chat_id in self.chat_data and '-' not in chat_id:
            # Es un chat individual, el otro participante podría ser el chat_id
            if chat_id in self.contacts_data:
                contact_info = self.contacts_data[chat_id]
                if contact_info.get('display_name'):
                    return {
                        'display_name': contact_info['display_name'],
                        'phone': self._format_for_display(identifier),
                        'confidence': 75,
                        'source': 'individual_chat_context'
                    }
        
        # Usar co-ocurrencias para sugerir posibles contactos
        if identifier in self.co_occurrence_index:
            co_occurrences = self.co_occurrence_index[identifier]
            
            if co_occurrences:
                # Encontrar el contacto conocido con mayor co-ocurrencia
                best_match = None
                best_count = 0
                
                for co_id, count in co_occurrences.items():
                    if co_id in self.contacts_data and count > best_count:
                        contact_info = self.contacts_data[co_id]
                        if contact_info.get('display_name'):
                            best_count = count
                            best_match = co_id
                
                if best_match:
                    # Usar información del contacto relacionado
                    related_contact = self.contacts_data[best_match]
                    confidence = min(60 + (best_count * 2), 70)
                    
                    return {
                        'display_name': f"Contacto de {related_contact.get('display_name')}",
                        'phone': self._format_for_display(identifier),
                        'confidence': confidence,
                        'source': 'co_occurrence'
                    }
        
        return None
    
    def _format_for_display(self, phone: str) -> str:
        """Formatea un número telefónico para mostrar."""
        if not phone or not isinstance(phone, str):
            return "Desconocido"
            
        # Si ya es un nombre (contiene letras), devolver tal cual
        if any(c.isalpha() for c in phone):
            return phone
            
        # Extraer número de diferentes formatos
        if '@' in phone:
            phone = phone.split('@')[0]
            
        # Para chats grupales
        if '-' in phone:
            return f"Grupo {phone}"
            
        # Limpiar y formatear
        digits = ''.join(c for c in phone if c.isdigit())
        
        if len(digits) >= 10:
            if len(digits) > 10:
                country_code = digits[:-10]
                number = digits[-10:]
            else:
                country_code = "52"  # Default para México
                number = digits
                
            return f"+{country_code} {number[:3]} {number[3:6]}-{number[6:]}"
        else:
            return phone  # Devolver original si no podemos formatear
    
    def add_manual_correction(self, identifier: str, display_name: str) -> bool:
        """
        Agrega una corrección manual que se usará en futuras resoluciones.
        También actualiza la caché y aprende de esta corrección.
        """
        normalized = self._normalize_phone_number(identifier)
        
        # Guardar corrección
        self.correction_map[identifier] = {
            'display_name': display_name,
            'phone': self._format_for_display(identifier),
            'confidence': 100,
            'source': 'manual_correction'
        }
        
        # Actualizar caché
        self.resolved_cache[identifier] = self.correction_map[identifier]
        
        # Agregar a índices para aprendizaje
        if normalized:
            self.number_index[normalized] = identifier
            
        name_key = self._normalize_name(display_name)
        if name_key:
            self.name_index[name_key] = identifier
        
        return True
    
    def batch_resolve(self, identifiers: List[str], context: Dict[str, Any] = None) -> Dict[str, Dict[str, Any]]:
        """Resuelve múltiples identificadores en lote."""
        results = {}
        for identifier in identifiers:
            results[identifier] = self.resolve_contact(identifier, context)
        return results
    
    def suggest_chat_name(self, chat_id: str) -> str:
        """
        Sugiere un nombre para un chat sin nombre (None).
        Especialmente útil para chats grupales sin nombre.
        """
        if not chat_id or chat_id not in self.chat_data:
            return "Chat desconocido"
            
        chat_info = self.chat_data[chat_id]
        
        # Si ya tiene nombre, usarlo
        if chat_info.get('name') and chat_info.get('name') != "None":
            return chat_info['name']
            
        # Si es un chat grupal
        if '-' in chat_id:
            # Encontrar participantes conocidos
            participants = list(self.chat_contacts_index.get(chat_id, set()))
            known_participants = []
            
            for p in participants:
                info = self.resolve_contact(p)
                if info['confidence'] > 50 and info['display_name'] != "Desconocido":
                    known_participants.append(info['display_name'])
            
            if len(known_participants) >= 2:
                return f"Grupo con {known_participants[0]} y {len(known_participants)-1} más"
            elif len(known_participants) == 1:
                return f"Grupo con {known_participants[0]}"
            else:
                return f"Grupo {chat_id}"
        
        # Para chats individuales
        else:
            # Para chat individual, el nombre podría ser el del contacto
            info = self.resolve_contact(chat_id)
            if info['confidence'] > 0 and info['display_name'] != "Desconocido":
                return info['display_name']
                
        # Si todo falla, devolver formato legible del ID
        return self._format_for_display(chat_id)


# Singleton para mantener una única instancia del resolvedor
_GLOBAL_RESOLVER = None

def get_resolver(contacts_data=None, chat_data=None, reset=False):
    """
    Obtiene una instancia global del ContactResolver.
    Si ya existe una instancia, la reutiliza a menos que reset=True.
    """
    global _GLOBAL_RESOLVER
    if _GLOBAL_RESOLVER is None or reset:
        _GLOBAL_RESOLVER = ContactResolver(contacts_data=contacts_data, chat_data=chat_data)
    return _GLOBAL_RESOLVER