import json

# Cargar contactos
with open('whatsapp_contacts.json', 'r', encoding='utf-8') as f:
    contacts = json.load(f)

# Números de teléfono a buscar
phone_numbers = [
    '3147969080',  # (314) 796-9080
    '3017553804',  # (301) 755-3804
    '3209981257'   # (320) 998-1257
]

# Buscar contactos
for phone in phone_numbers:
    print(f"Buscando contacto para {phone}:")
    found = False
    
    for contact_id, contact_data in contacts.items():
        # Limpiar el número de contacto para comparación
        contact_clean = ''.join(c for c in contact_id if c.isdigit())
        contact_phone_raw = contact_data.get('phone_raw', '')
        contact_phone_clean = ''.join(c for c in contact_phone_raw if c.isdigit())
        
        # Comparar números limpios
        if (phone == contact_clean or 
            phone == contact_phone_clean or
            phone.endswith(contact_clean) or 
            contact_clean.endswith(phone) or
            phone.endswith(contact_phone_clean) or
            contact_phone_clean.endswith(phone)):
            
            print(f"  Encontrado: {contact_id} -> {contact_data.get('display_name', 'Sin nombre')}")
            found = True
    
    if not found:
        print("  No encontrado")
    
    print()
