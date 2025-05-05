#!/usr/bin/env python3
"""
Herramienta de corrección de contactos para WhatsApp Chat Exporter

Esta herramienta procesa el archivo result.json y aplica el sistema avanzado de
resolución de contactos para corregir contactos "Desconocido" y chats "None".
"""

import os
import json
import argparse
import sys
from typing import Dict, Any, List, Tuple

from tqdm import tqdm

# Importar el sistema de resolución de contactos
from contact_resolver import get_resolver, ContactResolver
from whatsapp_core import load_json_data, load_contacts, resolve_unknown_participants


def process_file(data_file: str, contacts_file: str, output_file: str = None, 
                threshold: int = 50, backup: bool = True) -> None:
    """
    Procesa el archivo result.json y aplica resolución avanzada de contactos.
    
    Args:
        data_file: Ruta al archivo result.json
        contacts_file: Ruta al archivo de contactos (whatsapp_contacts.json)
        output_file: Archivo de salida (por defecto sobreescribe el original)
        threshold: Umbral de confianza para aceptar resoluciones
        backup: Si se debe crear una copia de seguridad del archivo original
    """
    print(f"Procesando archivo {data_file}...")
    
    # Cargar datos
    data = load_json_data(data_file)
    if not data:
        print("Error: No se pudieron cargar los datos.")
        return
    
    # Cargar contactos
    contacts = load_contacts(contacts_file)
    if not contacts:
        print("Advertencia: No se pudieron cargar contactos. La resolución será limitada.")
    
    # Hacer copia de seguridad si se solicita
    if backup:
        backup_file = f"{data_file}.bak"
        print(f"Creando copia de seguridad en {backup_file}")
        try:
            with open(data_file, 'r', encoding='utf-8') as f_in:
                with open(backup_file, 'w', encoding='utf-8') as f_out:
                    f_out.write(f_in.read())
        except Exception as e:
            print(f"Error creando backup: {e}")
            if input("¿Continuar sin backup? (s/n): ").lower() != 's':
                return
    
    # Inicializar resolvedor
    resolver = get_resolver(contacts_data=contacts, chat_data=data, reset=True)
    
    # Estadísticas
    stats = {
        'total_chats': len(data),
        'renamed_chats': 0,
        'total_messages': 0,
        'renamed_senders': 0,
        'added_destination_info': 0
    }
    
    # Procesar chats sin nombre (None)
    print("Procesando chats sin nombre...")
    for chat_id, chat_info in tqdm(data.items(), desc="Chats"):
        if not chat_info.get('name') or chat_info.get('name') == "None":
            suggested_name = resolver.suggest_chat_name(chat_id)
            
            # Solo aplicar si tenemos un nombre significativo
            if suggested_name and suggested_name != f"Grupo {chat_id}" and suggested_name != chat_id:
                chat_info['name'] = suggested_name
                stats['renamed_chats'] += 1
                print(f"  - Se renombró chat: {chat_id} → {suggested_name}")
    
    # Procesar mensajes con remitentes desconocidos
    print("Procesando remitentes desconocidos y añadiendo información de destino...")
    for chat_id, chat_info in tqdm(data.items(), desc="Mensajes"):
        messages = chat_info.get('messages', {})
        stats['total_messages'] += len(messages)
        
        for msg_id, msg in messages.items():
            sender_id = msg.get('sender_id', '')
            
            # Resolver remitente desconocido
            if sender_id and (not msg.get('sender') or msg.get('sender') == "Desconocido"):
                # Usar contexto del chat actual
                contact_info = resolver.resolve_contact(
                    sender_id,
                    context={"chat_id": chat_id}
                )
                
                if contact_info['confidence'] >= threshold:
                    # Guardar nombre resuelto y metadata
                    msg['sender'] = contact_info['display_name']
                    msg['resolved_sender'] = contact_info['display_name']
                    msg['resolution_confidence'] = contact_info['confidence']
                    msg['resolution_source'] = contact_info['source']
                    stats['renamed_senders'] += 1
            
            # Añadir información completa de destino
            destination_info = resolver.get_message_destination_info(msg, chat_id)
            
            # Añadir la información de destino al mensaje
            if destination_info:
                msg['destination_info'] = {
                    'chat_name': destination_info['chat'].get('display_name', 'Desconocido'),
                    'chat_type': destination_info['chat'].get('type', 'unknown'),
                    'recipient_name': destination_info['recipient'].get('display_name', 'Desconocido'),
                    'direction': 'outgoing' if destination_info['is_outgoing'] else 'incoming'
                }
                stats['added_destination_info'] += 1
                
    # Guardar resultado
    output = output_file or data_file
    print(f"Guardando resultados en {output}...")
    
    try:
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        print("¡Archivo guardado correctamente!")
    except Exception as e:
        print(f"Error guardando archivo: {e}")
    
    # Mostrar estadísticas
    print("\nEstadísticas:")
    print(f"- Total de chats: {stats['total_chats']}")
    print(f"- Chats renombrados: {stats['renamed_chats']}")
    print(f"- Total de mensajes: {stats['total_messages']}")
    print(f"- Remitentes resueltos: {stats['renamed_senders']}")
    print(f"- Mensajes con info de destino añadida: {stats['added_destination_info']}")
    
    # Calcular porcentaje de mejora
    if stats['total_messages'] > 0:
        improvement = (stats['renamed_senders'] / stats['total_messages']) * 100
        print(f"- Porcentaje de mejora: {improvement:.2f}%")


def main():
    parser = argparse.ArgumentParser(description='Herramienta de corrección de contactos para WhatsApp Chat Exporter')
    parser.add_argument('-f', '--file', default='whatsapp_export/result.json',
                        help='Ruta al archivo result.json (default: whatsapp_export/result.json)')
    parser.add_argument('-c', '--contacts', default='whatsapp_contacts.json',
                        help='Ruta al archivo de contactos (default: whatsapp_contacts.json)')
    parser.add_argument('-o', '--output', help='Archivo de salida (por defecto sobreescribe el original)')
    parser.add_argument('-t', '--threshold', type=int, default=50,
                        help='Umbral de confianza para aceptar resoluciones (0-100, default: 50)')
    parser.add_argument('--no-backup', action='store_true',
                        help='No crear copia de seguridad del archivo original')
    
    args = parser.parse_args()
    
    process_file(
        data_file=args.file,
        contacts_file=args.contacts,
        output_file=args.output,
        threshold=args.threshold,
        backup=not args.no_backup
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
