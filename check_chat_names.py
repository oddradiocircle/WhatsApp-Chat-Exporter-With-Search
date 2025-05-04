import json

# Cargar datos de WhatsApp
with open('whatsapp_export/result.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Nombres de chat a buscar
chat_names = [
    'Alebrijes',
    'Baby Joha',
    'Pauta Vattea'
]

# Buscar chats
for chat_name in chat_names:
    print(f"Buscando chat '{chat_name}':")
    found = False
    
    for chat_id, chat_data in data.items():
        name = chat_data.get('name', '')
        
        if name == chat_name:
            print(f"  Encontrado: {chat_id} -> {name}")
            found = True
    
    if not found:
        print("  No encontrado")
    
    print()
