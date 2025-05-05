# Guía para Manejar Contactos Desconocidos en WhatsApp Chat Exporter

Este documento explica cómo resolver el problema de los contactos y chats que aparecen como "None" o "Desconocido" en los resultados de búsqueda.

## Causas del problema

Existen varias razones por las que algunos contactos o chats pueden aparecer como desconocidos:

1. **Falta de información en la base de datos**: La base de datos de WhatsApp no siempre contiene toda la información de contacto.
2. **Contactos no guardados**: Mensajes de números que no están en tu lista de contactos.
3. **Problemas de formato**: Diferentes formatos de números telefónicos entre la base de datos y tus contactos.
4. **Chats grupales**: Participantes en grupos que no están en tus contactos.

## Soluciones implementadas

El sistema incluye varias mejoras para resolver automáticamente estos problemas:

### 1. Sistema de resolución avanzada

Se ha implementado un sistema que utiliza múltiples estrategias para identificar contactos:
- Coincidencia exacta con contactos conocidos
- Coincidencia por sufijos de números telefónicos
- Inferencia basada en el contexto del chat
- Análisis de co-ocurrencia (quién aparece con quién en grupos)

### 2. Preprocesamiento de datos

Antes de realizar búsquedas, el sistema puede preprocesar los datos para:
- Resolver contactos desconocidos
- Inferir remitentes en chats individuales
- Aplicar correcciones manuales

### 3. Sistema de correcciones manuales

Para casos que no pueden resolverse automáticamente, se incluye un sistema de correcciones manuales:
- Creación de un archivo de correcciones (`contact_corrections.json`)
- Aplicación de correcciones a los datos

## Cómo usar el sistema de correcciones manuales

### Desde el modo interactivo

1. Ejecuta la herramienta en modo interactivo: `python whatsapp_unified_tool.py -i`
2. Selecciona la opción 9: "Manage contact corrections"
3. Selecciona la opción 1 para crear/actualizar el archivo de correcciones
4. Edita el archivo `contact_corrections.json` con tus correcciones
5. Selecciona la opción 2 para aplicar las correcciones a los datos

### Desde la línea de comandos

Para crear/actualizar el archivo de correcciones:
```
python whatsapp_unified_tool.py --mode corrections --create-corrections
```

Para aplicar correcciones a los datos:
```
python whatsapp_unified_tool.py --mode corrections --apply-corrections
```

Para hacer ambas cosas:
```
python whatsapp_unified_tool.py --mode corrections --create-corrections --apply-corrections
```

### Formato del archivo de correcciones

El archivo `contact_corrections.json` tiene la siguiente estructura:

```json
{
    "unknown_contacts": {
        "5512345678@s.whatsapp.net": "Nombre Correcto",
        "5587654321@s.whatsapp.net": "Otro Contacto"
    },
    "unknown_chats": {
        "5512345678@s.whatsapp.net": "Nombre del Chat",
        "5512345678-1234567890@g.us": "Nombre del Grupo"
    }
}
```

- `unknown_contacts`: Correcciones para remitentes desconocidos
- `unknown_chats`: Correcciones para nombres de chats desconocidos

## Opciones de búsqueda

Al realizar búsquedas, puedes controlar el preprocesamiento:

### Desde el modo interactivo

Al buscar, se te preguntará si deseas preprocesar los datos:
```
Preprocesar datos para mejorar la búsqueda? (s/n, default s):
```

### Desde la línea de comandos

```
# Con preprocesamiento (predeterminado)
python whatsapp_unified_tool.py --mode search --keywords "palabra clave"

# Sin preprocesamiento
python whatsapp_unified_tool.py --mode search --keywords "palabra clave" --no-preprocess
```

## Consejos para mejorar los resultados

1. **Actualiza tu archivo de contactos**: Asegúrate de tener un archivo de contactos actualizado.
2. **Usa el preprocesamiento**: Activa la opción de preprocesamiento para mejorar la identificación.
3. **Crea correcciones manuales**: Para contactos importantes que no se resuelven automáticamente.
4. **Verifica los formatos de números**: Asegúrate de que los números en tus contactos incluyan el código de país.
5. **Usa filtros específicos**: Al buscar, usa filtros de chat o remitente para reducir los resultados desconocidos.

## Estadísticas de contactos desconocidos

Al listar los chats disponibles (opción 2 en el modo interactivo), se mostrará el número de mensajes con remitentes desconocidos en cada chat, lo que te ayudará a identificar dónde se necesitan correcciones.
