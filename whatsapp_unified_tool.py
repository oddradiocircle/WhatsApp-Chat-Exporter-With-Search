#!/usr/bin/env python3
"""
WhatsApp Unified Tool

This script combines search functionality and ML analysis for WhatsApp chat data.
It provides both interactive and command-line modes for accessing all features.

Features:
- Basic search with relevance scoring
- Advanced filtering (by chat, sender, phone, date)
- Contact information handling
- ML analysis (sentiment, topics, semantic search, entities, clustering)
- Interactive and command-line modes
- Result saving functionality
- Intel hardware optimizations
"""

import argparse
import os
import sys
import platform
import subprocess
from tqdm import tqdm
import traceback
from datetime import datetime

# Setup Intel optimizations automatically
def setup_intel_optimizations():
    """Set up Intel optimizations automatically at startup"""
    print("Checking for Intel hardware and setting up optimizations...")

    # Check if we're running on Intel hardware
    is_intel_cpu = "intel" in platform.processor().lower()

    if is_intel_cpu:
        print("Intel CPU detected. Enabling optimizations...")

        # Check for oneAPI installation
        oneapi_path = None
        if platform.system() == "Windows":
            possible_paths = [
                r"C:\Program Files (x86)\Intel\oneAPI",
                r"C:\Program Files\Intel\oneAPI"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    oneapi_path = path
                    break

        if oneapi_path:
            print(f"Intel oneAPI detected at: {oneapi_path}")

            # Set up environment variables for oneAPI
            setvars_path = os.path.join(oneapi_path, "setvars.bat")
            if os.path.exists(setvars_path):
                print("Setting up oneAPI environment...")

                # Create a temporary batch file to capture environment variables
                temp_batch = "temp_oneapi_env.bat"
                with open(temp_batch, "w") as f:
                    f.write(f'@echo off\n')
                    f.write(f'call "{setvars_path}" > nul\n')
                    f.write(f'set > oneapi_env.txt\n')

                # Run the batch file to capture environment variables
                subprocess.run([temp_batch], shell=True)

                # Read the environment variables and set them in the current process
                if os.path.exists("oneapi_env.txt"):
                    with open("oneapi_env.txt", "r") as f:
                        for line in f:
                            if "=" in line:
                                name, value = line.strip().split("=", 1)
                                os.environ[name] = value

                    # Clean up
                    os.remove("oneapi_env.txt")

                # Clean up
                if os.path.exists(temp_batch):
                    os.remove(temp_batch)

                print("Intel oneAPI environment set up successfully.")

        # Enable scikit-learn-intelex if available
        try:
            import sklearnex
            sklearnex.patch_sklearn()
            print("Intel Extension for Scikit-learn enabled.")
        except ImportError:
            print("Intel Extension for Scikit-learn not available.")

        # Try to enable Intel Extension for PyTorch if available
        try:
            import intel_extension_for_pytorch as ipex
            print("Intel Extension for PyTorch enabled.")
        except ImportError:
            print("Intel Extension for PyTorch not available.")

    print("Intel optimization setup complete.")

# Run Intel optimization setup at import time
setup_intel_optimizations()

# Import core functionality
from whatsapp_core import (
    load_json_data,
    load_contacts,
    format_phone_number,
    install_ml_dependencies
)

# Import Google Contacts functionality
try:
    from google_contacts import (
        parse_google_contacts_csv,
        merge_contacts,
        find_matching_contact
    )
    GOOGLE_CONTACTS_AVAILABLE = True
except ImportError:
    GOOGLE_CONTACTS_AVAILABLE = False

# Import search functionality
from chat_search import (
    calculate_relevance_score,
    extract_messages,
    get_message_context,
    print_results,
    save_results_to_file
)

# Import ML functionality
from chat_search.search_ml import check_ml_dependencies

# Check if ML dependencies are installed
ML_AVAILABLE = check_ml_dependencies()


class WhatsAppUnifiedTool:
    """Unified WhatsApp Chat Analysis Tool"""

    def __init__(self, data_file=None, contacts_file=None, google_contacts_file=None):
        """Initialize the tool with data and contacts files"""
        self.data = None
        self.contacts = {}
        self.google_contacts = {}
        self.data_file = data_file
        self.contacts_file = contacts_file
        self.google_contacts_file = google_contacts_file
        self.embeddings_cache = {}
        self.embeddings_model = None
        self.embeddings_cache_file = None

        # Directorio para caché de embeddings
        self.cache_dir = "embeddings_cache"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        # Load data and contacts if provided
        if data_file:
            self.load_data(data_file)

        if contacts_file:
            self.load_contacts(contacts_file)

        if google_contacts_file:
            self.load_google_contacts(google_contacts_file)

    def load_data(self, file_path):
        """Load WhatsApp chat data from a JSON file"""
        self.data_file = file_path
        self.data = load_json_data(file_path)
        return self.data is not None

    def load_contacts(self, file_path):
        """Load contact information from a JSON file"""
        self.contacts_file = file_path
        self.contacts = load_contacts(file_path)

        # If Google contacts are loaded, merge them with WhatsApp contacts
        if self.google_contacts:
            self.contacts = merge_contacts(self.contacts, self.google_contacts)

        return len(self.contacts) > 0

    def load_google_contacts(self, file_path):
        """Load contact information from a Google Contacts CSV file"""
        if not GOOGLE_CONTACTS_AVAILABLE:
            print("Google Contacts support is not available. Make sure google_contacts.py is in the same directory.")
            return False

        self.google_contacts_file = file_path
        self.google_contacts = parse_google_contacts_csv(file_path)

        # Merge with existing contacts if any
        if self.contacts:
            self.contacts = merge_contacts(self.contacts, self.google_contacts)

        return len(self.google_contacts) > 0



    def get_available_chats(self):
        """Get a list of available chats"""
        if not self.data:
            return []

        chats = []
        for chat_id, chat_data in self.data.items():
            # Extraer número de teléfono del chat_id (eliminar @s.whatsapp.net)
            phone_raw = chat_id.split('@')[0] if '@' in chat_id else chat_id

            # Intentar usar el resolvedor avanzado si está disponible
            try:
                from whatsapp_core import get_contact_info, suggest_chat_name

                # Obtener nombre sugerido para el chat
                chat_name = suggest_chat_name(chat_id, self.contacts, self.data)

                # Obtener información de contacto completa
                contact_info = get_contact_info(chat_id, self.contacts, self.data)
                formatted_phone = contact_info['phone']

                # Verificar si el chat tiene un nombre sugerido
                if chat_data.get('suggested_name') and chat_data.get('suggested_name') != "Chat desconocido":
                    chat_name = chat_data.get('suggested_name')
            except Exception:
                # Si hay error con el resolvedor, usar el método tradicional
                # Aplicar formato al número de teléfono para asegurar que incluya código de país
                formatted_phone = format_phone_number(chat_id)

                # Obtener nombre del chat con mejor formato
                chat_name = None
                contact_info = None

                # Primero intentar buscar directamente en los contactos
                if self.contacts and phone_raw in self.contacts:
                    contact_info = self.contacts[phone_raw]
                    if contact_info.get('display_name'):
                        chat_name = contact_info.get('display_name')

                # Si no se encontró nombre en los contactos, usar el nombre guardado en los datos
                if not chat_name:
                    chat_name = chat_data.get('name', '')
                    if not chat_name or chat_name == chat_id or chat_name == "None":
                        chat_name = formatted_phone

            # Crear nombre de visualización que incluya tanto el nombre del contacto como el número telefónico
            if '-' in phone_raw:  # Es un chat de grupo
                if chat_name and chat_name != chat_id and chat_name != phone_raw and chat_name != "None":
                    display_name = f"{chat_name} (Grupo {phone_raw})"
                else:
                    display_name = f"Grupo {phone_raw}"
            else:  # Es un chat individual
                if chat_name and chat_name != chat_id and chat_name != phone_raw and chat_name != "None" and not phone_raw.startswith(chat_name):
                    display_name = f"{chat_name} ({formatted_phone})"
                else:
                    display_name = formatted_phone

            # Contar mensajes
            message_count = len(chat_data.get('messages', {}))

            # Verificar si hay mensajes con remitentes desconocidos
            unknown_senders = 0
            for msg_id, msg in chat_data.get('messages', {}).items():
                sender = msg.get('sender', '')
                if sender == 'Desconocido' or sender == 'None' or not sender:
                    unknown_senders += 1

            chats.append({
                'id': chat_id,
                'name': display_name,
                'phone': formatted_phone,
                'contact_name': chat_name,
                'message_count': message_count,
                'unknown_senders': unknown_senders
            })

        # Ordenar por nombre
        chats.sort(key=lambda x: x['name'])
        return chats

    def search(self, keywords=None, min_score=10, max_results=20, start_date=None,
              end_date=None, chat_filter=None, sender_filter=None, phone_filter=None,
              calculate_contact_relevance=False, preprocess_data=True, use_cache=True,
              sort_criteria=None):
        """
        Search through messages using keywords and filters.
        Optimized for performance with large datasets.

        Parameters:
        - keywords: List of keywords or comma-separated string
        - min_score: Minimum relevance score (0-100)
        - max_results: Maximum number of results to return
        - start_date: Start date filter (YYYY-MM-DD)
        - end_date: End date filter (YYYY-MM-DD)
        - chat_filter: Filter by chat name
        - sender_filter: Filter by sender name
        - phone_filter: Filter by phone number
        - calculate_contact_relevance: Whether to calculate contact and chat relevance
        - preprocess_data: Whether to preprocess data for better search results
        - use_cache: Whether to use cached results for faster repeated searches
        - sort_criteria: List of criteria to sort results by (up to 3)
                        Options: 'relevance' (default), 'date_asc', 'date_desc', 'sender',
                        'chat', 'length_asc', 'length_desc', 'keyword_density', 'keyword_count'

        Returns:
        - List of matching messages or dictionary with results and relevance information
        """
        import hashlib
        import os
        import pickle
        import time

        if not self.data:
            print("No data loaded. Please load data first.")
            return []

        if not keywords:
            print("No keywords provided. Please provide at least one keyword.")
            return []

        if isinstance(keywords, str):
            # Convert comma-separated string to list
            keywords = [k.strip() for k in keywords.split(',')]

        print(f"Searching for keywords: {', '.join(keywords)}")

        # Create a cache key based on search parameters
        cache_key = hashlib.md5(
            f"{str(keywords)}_{min_score}_{max_results}_{start_date}_{end_date}_"
            f"{chat_filter}_{sender_filter}_{phone_filter}_{calculate_contact_relevance}".encode()
        ).hexdigest()

        cache_file = os.path.join("search_cache", f"search_{cache_key}.pkl")

        # Check if we can use cached results
        if use_cache and os.path.exists(cache_file):
            try:
                print("Loading results from cache...")
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    # Verify cache is still valid (data hasn't changed)
                    if cached_data.get('data_hash') == hashlib.md5(str(self.data).encode()).hexdigest():
                        print("Cache hit! Using cached results.")
                        return cached_data.get('results')
                    else:
                        print("Cache invalid (data changed). Performing new search...")
            except Exception as e:
                print(f"Error loading cache: {e}. Performing new search...")

        # Ensure cache directory exists
        os.makedirs("search_cache", exist_ok=True)

        # Preprocesar datos para mejorar la búsqueda si se solicita
        search_data = self.data
        if preprocess_data:
            print("Preprocesando datos para mejorar la búsqueda...")
            from whatsapp_core import preprocess_data_for_search
            search_data = preprocess_data_for_search(self.data, self.contacts)
            print("Preprocesamiento completado.")

        # Extract messages based on filters
        start_time = time.time()
        all_messages = extract_messages(
            search_data,
            contacts=self.contacts,
            chat_filter=chat_filter,
            start_date=start_date,
            end_date=end_date,
            sender_filter=sender_filter,
            phone_filter=phone_filter
        )
        extract_time = time.time() - start_time
        print(f"Message extraction completed in {extract_time:.2f} seconds.")

        if not all_messages:
            print("No messages found with the specified filters.")
            return []

        print(f"Processing {len(all_messages)} messages...")
        results = []

        # Para calcular la relevancia de contactos
        contact_relevance = {}
        chat_relevance = {}

        # Process messages in batches for better performance
        batch_size = 100  # Process 100 messages at a time
        total_batches = (len(all_messages) + batch_size - 1) // batch_size

        start_time = time.time()

        # Process each message in batches
        for batch_idx in tqdm(range(total_batches), desc="Processing batches"):
            batch_start = batch_idx * batch_size
            batch_end = min(batch_start + batch_size, len(all_messages))
            batch = all_messages[batch_start:batch_end]

            batch_results = []

            # Process each message in the current batch
            for msg in batch:
                # Calculate relevance score with the updated function
                score, matched_keywords, keyword_counts, word_stats = calculate_relevance_score(msg['message'], keywords)

                # Skip if score is below threshold
                if score < min_score or not matched_keywords:
                    continue

                # Add to batch results without context (will add context later for top results only)
                batch_results.append({
                    **msg,
                    'score': score,
                    'matched_keywords': matched_keywords,
                    'word_stats': word_stats,
                    'keyword_counts': keyword_counts,  # Store for later use
                    'context': None  # Will be populated later for top results
                })

                # Actualizar relevancia de contactos si se solicita
                if calculate_contact_relevance:
                    # Obtener información del remitente
                    sender_id = msg.get('sender_id', '')
                    chat_id = msg.get('chat_id', '')

                    # Actualizar relevancia del contacto
                    if sender_id:
                        # Extraer número de teléfono del sender_id (eliminar @s.whatsapp.net)
                        phone_raw = sender_id.split('@')[0] if '@' in sender_id else sender_id

                        if sender_id not in contact_relevance:
                            contact_relevance[sender_id] = {
                                'score': 0,
                                'message_count': 0,
                                'keyword_counts': {},
                                'total_words': 0,
                                'total_keywords': 0,
                                'display_name': msg.get('sender', sender_id),
                                'phone': phone_raw
                            }

                        # Actualizar puntuación y conteo
                        contact_relevance[sender_id]['score'] += score
                        contact_relevance[sender_id]['message_count'] += 1

                        # Actualizar estadísticas de palabras
                        contact_relevance[sender_id]['total_words'] += word_stats['total_words']
                        contact_relevance[sender_id]['total_keywords'] += word_stats['total_keywords']

                        # Actualizar conteo de palabras clave
                        for keyword, count in keyword_counts.items():
                            if keyword not in contact_relevance[sender_id]['keyword_counts']:
                                contact_relevance[sender_id]['keyword_counts'][keyword] = 0
                            contact_relevance[sender_id]['keyword_counts'][keyword] += count

                    # Actualizar relevancia del chat
                    if chat_id:
                        if chat_id not in chat_relevance:
                            # Obtener nombre del chat
                            chat_name = chat_id
                            if self.contacts:
                                # Extraer número de teléfono del chat_id
                                chat_phone = chat_id.split('@')[0] if '@' in chat_id else chat_id
                                if chat_phone in self.contacts:
                                    contact = self.contacts[chat_phone]
                                    if contact.get('display_name'):
                                        chat_name = contact.get('display_name')

                            chat_relevance[chat_id] = {
                                'score': 0,
                                'message_count': 0,
                                'keyword_counts': {},
                                'total_words': 0,
                                'total_keywords': 0,
                                'display_name': chat_name,
                                'phone': chat_phone if '@' in chat_id else chat_id
                            }

                        # Actualizar puntuación y conteo
                        chat_relevance[chat_id]['score'] += score
                        chat_relevance[chat_id]['message_count'] += 1

                        # Actualizar estadísticas de palabras
                        chat_relevance[chat_id]['total_words'] += word_stats['total_words']
                        chat_relevance[chat_id]['total_keywords'] += word_stats['total_keywords']

                        # Actualizar conteo de palabras clave
                        for keyword, count in keyword_counts.items():
                            if keyword not in chat_relevance[chat_id]['keyword_counts']:
                                chat_relevance[chat_id]['keyword_counts'][keyword] = 0
                            chat_relevance[chat_id]['keyword_counts'][keyword] += count

            # Add batch results to overall results
            results.extend(batch_results)

            # Sort and trim results after each batch
            if results:
                # Use default sorting by relevance for intermediate results
                results.sort(key=lambda x: x['score'], reverse=True)
                results = results[:max_results * 2]  # Keep twice as many as needed for now

        # Apply custom sorting if specified
        if sort_criteria:
            # Import sort utilities
            from chat_search.sort_utils import sort_results
            results = sort_results(results, sort_criteria)
        else:
            # Default sort by relevance
            results.sort(key=lambda x: x['score'], reverse=True)

        # Limit to max_results
        results = results[:max_results]

        # Now add context only for the top results
        print("Retrieving context for top results...")
        for i, result in enumerate(results):
            # Get message context
            context = get_message_context(self.data, result['chat_id'], result['msg_id'],
                                         contacts=self.contacts)
            results[i]['context'] = context

        processing_time = time.time() - start_time
        print(f"Message processing completed in {processing_time:.2f} seconds.")

        # Calcular puntuación final para contactos y chats
        if calculate_contact_relevance:
            # Obtener la marca de tiempo actual para calcular la recencia
            current_timestamp = datetime.now().timestamp()

            # Normalizar puntuaciones de contactos y calcular métricas adicionales
            for contact_id, data in contact_relevance.items():
                if data['message_count'] > 0:
                    data['avg_score'] = data['score'] / data['message_count']

                    # Calcular densidad de palabras clave para el contacto
                    if data['total_words'] > 0:
                        data['keyword_density'] = data['total_keywords'] / data['total_words']
                    else:
                        data['keyword_density'] = 0

                    # Calcular diversidad de palabras clave (proporción de palabras clave únicas vs total de palabras clave)
                    unique_keywords = len(data['keyword_counts'])
                    total_keywords = len(keywords)
                    data['keyword_diversity'] = unique_keywords / total_keywords if total_keywords > 0 else 0

                    # Calcular factor de recencia basado en las marcas de tiempo de los mensajes
                    # Buscar los mensajes más recientes de este contacto
                    contact_messages = [msg for msg in results if msg.get('sender_id') == contact_id]
                    if contact_messages:
                        # Ordenar por timestamp (más reciente primero)
                        contact_messages.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
                        # Tomar el mensaje más reciente
                        latest_msg = contact_messages[0]
                        latest_timestamp = latest_msg.get('timestamp', 0)

                        # Calcular recencia (1.0 = muy reciente, 0.0 = muy antiguo)
                        # Considerar mensajes de hasta 90 días (7776000 segundos)
                        time_diff = current_timestamp - latest_timestamp
                        recency_factor = max(0.0, 1.0 - (time_diff / 7776000))
                        data['recency_factor'] = recency_factor
                    else:
                        data['recency_factor'] = 0.0

                    # Calcular puntuación de relevancia ajustada por todos los factores
                    data['density_adjusted_score'] = data['score'] * (1 + data['keyword_density'])
                    data['final_score'] = (
                        data['density_adjusted_score'] * 0.6 +  # 60% - Puntuación ajustada por densidad
                        data['keyword_diversity'] * 100 * 0.2 + # 20% - Diversidad de palabras clave
                        data['recency_factor'] * 100 * 0.2      # 20% - Recencia
                    )
                else:
                    data['avg_score'] = 0
                    data['keyword_density'] = 0
                    data['keyword_diversity'] = 0
                    data['recency_factor'] = 0
                    data['density_adjusted_score'] = 0
                    data['final_score'] = 0

            # Normalizar puntuaciones de chats y calcular métricas adicionales
            for chat_id, data in chat_relevance.items():
                if data['message_count'] > 0:
                    data['avg_score'] = data['score'] / data['message_count']

                    # Calcular densidad de palabras clave para el chat
                    if 'total_words' in data and data['total_words'] > 0:
                        data['keyword_density'] = data['total_keywords'] / data['total_words']
                    else:
                        data['keyword_density'] = 0

                    # Calcular diversidad de palabras clave
                    unique_keywords = len(data['keyword_counts'])
                    total_keywords = len(keywords)
                    data['keyword_diversity'] = unique_keywords / total_keywords if total_keywords > 0 else 0

                    # Calcular factor de recencia
                    chat_messages = [msg for msg in results if msg.get('chat_id') == chat_id]
                    if chat_messages:
                        # Ordenar por timestamp (más reciente primero)
                        chat_messages.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
                        # Tomar el mensaje más reciente
                        latest_msg = chat_messages[0]
                        latest_timestamp = latest_msg.get('timestamp', 0)

                        # Calcular recencia
                        time_diff = current_timestamp - latest_timestamp
                        recency_factor = max(0.0, 1.0 - (time_diff / 7776000))
                        data['recency_factor'] = recency_factor
                    else:
                        data['recency_factor'] = 0.0

                    # Calcular puntuación ajustada por todos los factores
                    data['density_adjusted_score'] = data['score'] * (1 + data['keyword_density'])
                    data['final_score'] = (
                        data['density_adjusted_score'] * 0.6 +  # 60% - Puntuación ajustada por densidad
                        data['keyword_diversity'] * 100 * 0.2 + # 20% - Diversidad de palabras clave
                        data['recency_factor'] * 100 * 0.2      # 20% - Recencia
                    )
                else:
                    data['avg_score'] = 0
                    data['keyword_density'] = 0
                    data['keyword_diversity'] = 0
                    data['recency_factor'] = 0
                    data['density_adjusted_score'] = 0
                    data['final_score'] = 0

            # Identificar el contacto con más coincidencias usando la puntuación final
            most_relevant_contact = None
            if contact_relevance:
                most_relevant_contact = max(
                    contact_relevance.items(),
                    key=lambda x: x[1]['final_score']
                )

            # Ordenar contactos por puntuación final
            sorted_contacts = sorted(
                contact_relevance.items(),
                key=lambda x: x[1]['final_score'],
                reverse=True
            )

            # Ordenar chats por puntuación final
            sorted_chats = sorted(
                chat_relevance.items(),
                key=lambda x: x[1]['final_score'],
                reverse=True
            )

            # Prepare results
            final_results = {
                'results': results,
                'contact_relevance': sorted_contacts,
                'chat_relevance': sorted_chats,
                'most_relevant_contact': most_relevant_contact,
                'sort_criteria': sort_criteria
            }

            # Save results to cache if caching is enabled
            if use_cache:
                try:
                    # Create cache data with a hash of the current data for validation
                    cache_data = {
                        'results': final_results,
                        'data_hash': hashlib.md5(str(self.data).encode()).hexdigest(),
                        'timestamp': time.time()
                    }

                    with open(cache_file, 'wb') as f:
                        pickle.dump(cache_data, f)
                    print(f"Search results cached to {cache_file}")
                except Exception as e:
                    print(f"Warning: Could not cache results: {e}")

            return final_results

        # Si se especificaron criterios de ordenación, incluirlos en los resultados
        if sort_criteria:
            simple_results = {
                'results': results,
                'sort_criteria': sort_criteria
            }
        else:
            simple_results = results

        # Save simple results to cache if caching is enabled
        if use_cache:
            try:
                # Create cache data with a hash of the current data for validation
                cache_data = {
                    'results': simple_results,
                    'data_hash': hashlib.md5(str(self.data).encode()).hexdigest(),
                    'timestamp': time.time()
                }

                with open(cache_file, 'wb') as f:
                    pickle.dump(cache_data, f)
                print(f"Search results cached to {cache_file}")
            except Exception as e:
                print(f"Warning: Could not cache results: {e}")

        return simple_results

    # ML Analysis Functions
    def analyze_sentiment(self, messages=None, filters=None):
        """Analyze sentiment of messages"""
        from chat_search.search_ml import analyze_sentiment
        return analyze_sentiment(self, messages, filters)

    def extract_topics(self, messages=None, num_topics=5, filters=None):
        """Extract main topics from messages using LDA"""
        from chat_search.search_ml import extract_topics
        return extract_topics(self, messages, num_topics, filters)

    def semantic_search(self, query, messages=None, num_results=10, filters=None, use_cache=True):
        """Perform semantic search using sentence embeddings with caching support"""
        from chat_search.search_ml import semantic_search
        return semantic_search(self, query, messages, num_results, filters, use_cache)

    def extract_entities(self, messages=None, filters=None):
        """Extract named entities from messages using spaCy"""
        from chat_search.search_ml import extract_entities
        return extract_entities(self, messages, filters)

    def cluster_messages(self, messages=None, num_clusters=5, filters=None):
        """Group similar messages using K-means clustering"""
        from chat_search.search_ml import cluster_messages
        return cluster_messages(self, messages, num_clusters, filters)

    def complete_analysis(self, filters=None, num_topics=5, num_clusters=5):
        """Run a complete analysis including all ML features"""
        if not ML_AVAILABLE:
            print("ML dependencies not available. Please install them first.")
            return {}

        # Get messages
        messages = self._get_filtered_messages(filters)

        if not messages:
            print("No messages to analyze.")
            return {}

        print(f"Running complete analysis on {len(messages)} messages...")

        # Sentiment analysis
        print("\n=== Sentiment Analysis ===")
        sentiment_results = self.analyze_sentiment(messages)

        # Topic extraction
        print("\n=== Topic Extraction ===")
        topics, certainties = self.extract_topics(messages, num_topics=num_topics)

        # Semantic search (example query)
        print("\n=== Semantic Search Example ===")
        query = "important message"
        semantic_results = self.semantic_search(query, messages, num_results=5)

        # Entity extraction
        print("\n=== Entity Extraction ===")
        self.extract_entities(messages)  # We don't use the results directly in this method

        # Message clustering
        print("\n=== Message Clustering ===")
        clustered_messages = self.cluster_messages(messages, num_clusters=num_clusters)

        # Compile results
        sentiments = [r['sentiment'] for r in sentiment_results]

        # Count messages per cluster
        clusters = {}
        for msg in clustered_messages:
            cluster = msg['cluster']
            if cluster not in clusters:
                clusters[cluster] = 0
            clusters[cluster] += 1

        return {
            'sentiment_analysis': {
                'positive': sentiments.count('positive'),
                'negative': sentiments.count('negative'),
                'neutral': sentiments.count('neutral')
            },
            'topics': topics,
            'topic_certainties': certainties,
            'semantic_search': {
                'query': query,
                'top_results': [
                    {
                        'message': r['message'],
                        'similarity': r['similarity_score'],
                        'sender': r['sender'],
                        'date': r['date']
                    } for r in semantic_results[:5]
                ]
            },
            'clusters': {
                'count': num_clusters,
                'distribution': {str(cluster): count for cluster, count in clusters.items()}
            }
        }

    def _get_filtered_messages(self, filters=None):
        """Extract messages using the specified filters"""
        from chat_search import extract_messages

        if not filters:
            filters = {}

        return extract_messages(
            self.data,
            contacts=self.contacts,
            chat_filter=filters.get('chat'),
            start_date=filters.get('start_date'),
            end_date=filters.get('end_date'),
            sender_filter=filters.get('sender'),
            phone_filter=filters.get('phone')
        )


def analyze_relevant_contacts(tool):
    """
    Analiza y muestra los contactos más relevantes basados en palabras clave.

    Esta función permite:
    - Buscar contactos por palabras clave
    - Ver estadísticas detalladas de cada contacto
    - Exportar información de contactos relevantes
    """
    # Solicitar palabras clave
    keywords = input("Ingresa palabras clave para buscar contactos relevantes (separadas por comas): ")
    if not keywords:
        print("No se ingresaron palabras clave. Operación cancelada.")
        return

    # Solicitar filtros opcionales
    chat_filter = input("Filtrar por nombre de chat (opcional): ")
    start_date = input("Fecha de inicio (YYYY-MM-DD, opcional): ")
    end_date = input("Fecha de fin (YYYY-MM-DD, opcional): ")
    min_score = float(input("Puntuación mínima de relevancia (0-100, default 5): ") or 5)
    max_results = int(input("Número máximo de contactos a mostrar (default 20): ") or 20)

    # Solicitar criterios de ordenación
    from chat_search.sort_utils import get_available_sort_criteria

    # Mostrar criterios disponibles
    print("\nCriterios de ordenación disponibles:")
    criteria_dict = get_available_sort_criteria()
    for i, (key, desc) in enumerate(criteria_dict.items(), 1):
        print(f"{i}. {key}: {desc}")

    # Preguntar si se desea ordenar por algún criterio específico
    use_sort = input("\n¿Deseas ordenar los resultados por algún criterio específico? (s/n): ").lower() == 's'

    sort_criteria = None
    if use_sort:
        # Solicitar hasta 3 criterios de ordenación
        sort_criteria = []

        print("\nIngresa hasta 3 criterios de ordenación (deja vacío para usar relevancia por defecto):")
        for i in range(1, 4):
            criterion = input(f"Criterio {i} (nombre o número, vacío para omitir): ").strip()

            if not criterion:
                # Omitir si está vacío
                continue

            # Verificar si es un número
            if criterion.isdigit() and 1 <= int(criterion) <= len(criteria_dict):
                # Convertir número a nombre de criterio
                criterion = list(criteria_dict.keys())[int(criterion) - 1]

            # Validar criterio
            if criterion in criteria_dict:
                sort_criteria.append(criterion)
            else:
                print(f"Criterio inválido '{criterion}'. Omitiendo.")

        # Si no se seleccionó ningún criterio, usar relevancia por defecto
        if not sort_criteria:
            sort_criteria = ['relevance']

    # Limpiar filtros
    if not chat_filter:
        chat_filter = None
    if not start_date:
        start_date = None
    if not end_date:
        end_date = None

    print("\nBuscando contactos relevantes...")

    # Realizar búsqueda con cálculo de relevancia de contactos activado
    results = tool.search(
        keywords=keywords,
        min_score=min_score,
        max_results=100,  # Usar un valor alto para capturar más mensajes
        start_date=start_date,
        end_date=end_date,
        chat_filter=chat_filter,
        calculate_contact_relevance=True,
        preprocess_data=True,
        sort_criteria=sort_criteria
    )

    # Verificar si hay resultados
    if not isinstance(results, dict) or 'contact_relevance' not in results or not results['contact_relevance']:
        print("No se encontraron contactos relevantes.")
        return

    # Extraer y mostrar contactos relevantes
    contact_relevance = results['contact_relevance']

    print("\n" + "=" * 80)
    print("ANÁLISIS DE CONTACTOS RELEVANTES")
    print("=" * 80)

    # Mostrar estadísticas generales
    total_contacts = len(contact_relevance)
    print(f"Se encontraron {total_contacts} contactos relevantes para las palabras clave.")

    # Mostrar los contactos más relevantes
    print("\nContactos más relevantes:")
    for i, (contact_id, data) in enumerate(contact_relevance[:max_results], 1):
        print(f"\n{i}. {data['display_name']} ({data['phone']})")
        print(f"   Puntuación total: {data['score']:.1f}")
        print(f"   Mensajes coincidentes: {data['message_count']}")

        # Mostrar densidad de palabras clave si está disponible
        if 'keyword_density' in data:
            print(f"   Densidad de palabras clave: {data['keyword_density']:.2%}")

        # Mostrar palabras clave más frecuentes
        if 'keyword_counts' in data and data['keyword_counts']:
            sorted_keywords = sorted(data['keyword_counts'].items(), key=lambda x: x[1], reverse=True)
            print("   Palabras clave más frecuentes:")
            for keyword, count in sorted_keywords[:5]:  # Mostrar las 5 más frecuentes
                print(f"     - {keyword}: {count} veces")

    # Preguntar si se desea exportar los resultados
    export_option = input("\n¿Deseas exportar estos resultados a un archivo? (s/n): ")
    if export_option.lower() == 's':
        filename = input("Ingresa el nombre del archivo: ")
        if not filename:
            filename = "contactos_relevantes.json"
        elif not (filename.endswith('.json') or filename.endswith('.md')):
            filename += ".json"

        # Exportar resultados
        from chat_search import save_results_to_file

        # Convertir la lista de tuplas a un diccionario para evitar errores de índice
        contact_dict = {}
        for contact_id, data in contact_relevance:
            contact_dict[contact_id] = data

        save_results_to_file({'contact_relevance': contact_dict}, filename, contacts=tool.contacts)
        print(f"Resultados exportados a {filename}")

def analyze_messages(tool):
    """
    Analiza y muestra mensajes individuales con opciones avanzadas de filtrado.

    Esta función permite:
    - Buscar mensajes con filtros detallados
    - Ver estadísticas de mensajes
    - Exportar mensajes filtrados
    """
    print("\n" + "=" * 80)
    print("ANÁLISIS DE MENSAJES")
    print("=" * 80)

    # Solicitar filtros
    print("\nIngresa los filtros para los mensajes:")

    # Opciones de filtrado
    chat_filter = input("Filtrar por nombre de chat (opcional): ")
    sender_filter = input("Filtrar por nombre de remitente (opcional): ")
    phone_filter = input("Filtrar por número de teléfono (opcional): ")
    start_date = input("Fecha de inicio (YYYY-MM-DD, opcional): ")
    end_date = input("Fecha de fin (YYYY-MM-DD, opcional): ")
    keywords = input("Palabras clave (separadas por comas, opcional): ")

    # Criterios de ordenación
    sort_criteria = None

    # Limpiar filtros
    if not chat_filter:
        chat_filter = None
    if not sender_filter:
        sender_filter = None
    if not phone_filter:
        phone_filter = None
    if not start_date:
        start_date = None
    if not end_date:
        end_date = None

    # Extraer mensajes con los filtros especificados
    print("\nExtrayendo mensajes...")

    # Si se especificaron palabras clave, usar la función de búsqueda
    if keywords:
        min_score = float(input("Puntuación mínima de relevancia (0-100, default 5): ") or 5)
        max_results = int(input("Número máximo de mensajes a mostrar (default 50): ") or 50)

        # Solicitar criterios de ordenación
        from chat_search.sort_utils import get_available_sort_criteria

        # Mostrar criterios disponibles
        print("\nCriterios de ordenación disponibles:")
        criteria_dict = get_available_sort_criteria()
        for i, (key, desc) in enumerate(criteria_dict.items(), 1):
            print(f"{i}. {key}: {desc}")

        # Preguntar si se desea ordenar por algún criterio específico
        use_sort = input("\n¿Deseas ordenar los resultados por algún criterio específico? (s/n): ").lower() == 's'

        if use_sort:
            # Solicitar hasta 3 criterios de ordenación
            sort_criteria = []

            print("\nIngresa hasta 3 criterios de ordenación (deja vacío para usar relevancia por defecto):")
            for i in range(1, 4):
                criterion = input(f"Criterio {i} (nombre o número, vacío para omitir): ").strip()

                if not criterion:
                    # Omitir si está vacío
                    continue

                # Verificar si es un número
                if criterion.isdigit() and 1 <= int(criterion) <= len(criteria_dict):
                    # Convertir número a nombre de criterio
                    criterion = list(criteria_dict.keys())[int(criterion) - 1]

                # Validar criterio
                if criterion in criteria_dict:
                    sort_criteria.append(criterion)
                else:
                    print(f"Criterio inválido '{criterion}'. Omitiendo.")

            # Si no se seleccionó ningún criterio, usar relevancia por defecto
            if not sort_criteria:
                sort_criteria = ['relevance']

        results = tool.search(
            keywords=keywords,
            min_score=min_score,
            max_results=max_results,
            start_date=start_date,
            end_date=end_date,
            chat_filter=chat_filter,
            sender_filter=sender_filter,
            phone_filter=phone_filter,
            calculate_contact_relevance=False,
            preprocess_data=True,
            sort_criteria=sort_criteria
        )

        if not results:
            print("No se encontraron mensajes con los filtros especificados.")
            return

        messages = results if isinstance(results, list) else results.get('results', [])
    else:
        # Si no hay palabras clave, usar extract_messages directamente
        from chat_search import extract_messages

        messages = extract_messages(
            tool.data,
            contacts=tool.contacts,
            chat_filter=chat_filter,
            start_date=start_date,
            end_date=end_date,
            sender_filter=sender_filter,
            phone_filter=phone_filter
        )

        if not messages:
            print("No se encontraron mensajes con los filtros especificados.")
            return

    # Mostrar estadísticas de los mensajes
    print(f"\nSe encontraron {len(messages)} mensajes.")

    # Agrupar por chat
    chats = {}
    for msg in messages:
        chat_name = msg.get('chat_name', 'Desconocido')
        if chat_name not in chats:
            chats[chat_name] = 0
        chats[chat_name] += 1

    # Agrupar por remitente
    senders = {}
    for msg in messages:
        sender = msg.get('sender', 'Desconocido')
        if sender not in senders:
            senders[sender] = 0
        senders[sender] += 1

    # Mostrar distribución por chat
    print("\nDistribución por chat:")
    for chat, count in sorted(chats.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {chat}: {count} mensajes")

    # Mostrar distribución por remitente
    print("\nDistribución por remitente:")
    for sender, count in sorted(senders.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {sender}: {count} mensajes")

    # Preguntar si se desea ver los mensajes
    view_option = input("\n¿Deseas ver los mensajes? (s/n): ")
    if view_option.lower() == 's':
        # Mostrar mensajes con navegación
        from chat_search import print_results
        print_results(messages, show_context=True, contacts=tool.contacts)

    # Preguntar si se desea exportar los resultados
    export_option = input("\n¿Deseas exportar estos mensajes a un archivo? (s/n): ")
    if export_option.lower() == 's':
        filename = input("Ingresa el nombre del archivo: ")
        if not filename:
            filename = "mensajes_filtrados.json"
        elif not (filename.endswith('.json') or filename.endswith('.md')):
            filename += ".json"

        # Exportar resultados
        from chat_search import save_results_to_file
        save_results_to_file(messages, filename, contacts=tool.contacts)
        print(f"Mensajes exportados a {filename}")

def analyze_relevant_chats(tool):
    """
    Analiza y muestra los chats más relevantes basados en palabras clave.

    Esta función permite:
    - Identificar los chats más relevantes para ciertas palabras clave
    - Ver estadísticas detalladas de cada chat
    - Exportar información de chats relevantes
    """
    # Solicitar palabras clave
    keywords = input("Ingresa palabras clave para buscar chats relevantes (separadas por comas): ")
    if not keywords:
        print("No se ingresaron palabras clave. Operación cancelada.")
        return

    # Solicitar filtros opcionales
    start_date = input("Fecha de inicio (YYYY-MM-DD, opcional): ")
    end_date = input("Fecha de fin (YYYY-MM-DD, opcional): ")
    min_score = float(input("Puntuación mínima de relevancia (0-100, default 5): ") or 5)
    max_results = int(input("Número máximo de chats a mostrar (default 20): ") or 20)

    # Solicitar criterios de ordenación
    from chat_search.sort_utils import get_available_sort_criteria

    # Mostrar criterios disponibles
    print("\nCriterios de ordenación disponibles:")
    criteria_dict = get_available_sort_criteria()
    for i, (key, desc) in enumerate(criteria_dict.items(), 1):
        print(f"{i}. {key}: {desc}")

    # Preguntar si se desea ordenar por algún criterio específico
    use_sort = input("\n¿Deseas ordenar los resultados por algún criterio específico? (s/n): ").lower() == 's'

    sort_criteria = None
    if use_sort:
        # Solicitar hasta 3 criterios de ordenación
        sort_criteria = []

        print("\nIngresa hasta 3 criterios de ordenación (deja vacío para usar relevancia por defecto):")
        for i in range(1, 4):
            criterion = input(f"Criterio {i} (nombre o número, vacío para omitir): ").strip()

            if not criterion:
                # Omitir si está vacío
                continue

            # Verificar si es un número
            if criterion.isdigit() and 1 <= int(criterion) <= len(criteria_dict):
                # Convertir número a nombre de criterio
                criterion = list(criteria_dict.keys())[int(criterion) - 1]

            # Validar criterio
            if criterion in criteria_dict:
                sort_criteria.append(criterion)
            else:
                print(f"Criterio inválido '{criterion}'. Omitiendo.")

        # Si no se seleccionó ningún criterio, usar relevancia por defecto
        if not sort_criteria:
            sort_criteria = ['relevance']

    # Limpiar filtros
    if not start_date:
        start_date = None
    if not end_date:
        end_date = None

    print("\nBuscando chats relevantes...")

    # Realizar búsqueda con cálculo de relevancia de chats activado
    results = tool.search(
        keywords=keywords,
        min_score=min_score,
        max_results=100,  # Usar un valor alto para capturar más mensajes
        start_date=start_date,
        end_date=end_date,
        calculate_contact_relevance=True,  # Esto también calcula relevancia de chats
        preprocess_data=True,
        sort_criteria=sort_criteria
    )

    # Verificar si hay resultados
    if not isinstance(results, dict) or 'chat_relevance' not in results or not results['chat_relevance']:
        print("No se encontraron chats relevantes.")
        return

    # Extraer y mostrar chats relevantes
    chat_relevance = results['chat_relevance']

    print("\n" + "=" * 80)
    print("ANÁLISIS DE CHATS RELEVANTES")
    print("=" * 80)

    # Mostrar estadísticas generales
    total_chats = len(chat_relevance)
    print(f"Se encontraron {total_chats} chats relevantes para las palabras clave.")

    # Mostrar los chats más relevantes
    print("\nChats más relevantes:")
    for i, (chat_id, data) in enumerate(chat_relevance[:max_results], 1):
        print(f"\n{i}. {data['display_name']}")
        print(f"   Puntuación total: {data['score']:.1f}")
        print(f"   Mensajes coincidentes: {data['message_count']}")

        # Mostrar densidad de palabras clave si está disponible
        if 'keyword_density' in data:
            print(f"   Densidad de palabras clave: {data['keyword_density']:.2%}")

        # Mostrar palabras clave más frecuentes
        if 'keyword_counts' in data and data['keyword_counts']:
            sorted_keywords = sorted(data['keyword_counts'].items(), key=lambda x: x[1], reverse=True)
            print("   Palabras clave más frecuentes:")
            for keyword, count in sorted_keywords[:5]:  # Mostrar las 5 más frecuentes
                print(f"     - {keyword}: {count} veces")

    # Preguntar si se desea ver mensajes de un chat específico
    view_option = input("\n¿Deseas ver mensajes de un chat específico? (s/n): ")
    if view_option.lower() == 's':
        chat_index = int(input(f"Ingresa el número del chat (1-{min(max_results, total_chats)}): "))

        if 1 <= chat_index <= min(max_results, total_chats):
            # Obtener el chat seleccionado
            selected_chat_id, selected_chat_data = chat_relevance[chat_index - 1]

            # Extraer mensajes de ese chat con las palabras clave
            chat_messages = tool.search(
                keywords=keywords,
                min_score=min_score,
                max_results=50,
                chat_filter=selected_chat_data['display_name'],
                start_date=start_date,
                end_date=end_date,
                calculate_contact_relevance=False,
                preprocess_data=True
            )

            # Mostrar mensajes
            from chat_search import print_results
            print_results(chat_messages, show_context=True, contacts=tool.contacts)
        else:
            print("Número de chat inválido.")

    # Preguntar si se desea exportar los resultados
    export_option = input("\n¿Deseas exportar estos resultados a un archivo? (s/n): ")
    if export_option.lower() == 's':
        filename = input("Ingresa el nombre del archivo: ")
        if not filename:
            filename = "chats_relevantes.json"
        elif not (filename.endswith('.json') or filename.endswith('.md')):
            filename += ".json"

        # Exportar resultados
        from chat_search import save_results_to_file

        # Convertir la lista de tuplas a un diccionario para evitar errores de índice
        chat_dict = {}
        for chat_id, data in chat_relevance:
            chat_dict[chat_id] = data

        save_results_to_file({'chat_relevance': chat_dict}, filename, contacts=tool.contacts)
        print(f"Resultados exportados a {filename}")


def analyze_sales_prospects(tool):
    """
    Analiza y muestra contactos potenciales para ventas de productos y servicios.

    Esta función permite:
    - Identificar contactos con mayor potencial como prospectos de ventas
    - Categorizar contactos por interés en diferentes productos/servicios
    - Calcular puntuación de potencial de compra
    - Exportar información detallada de prospectos
    """
    print("\n" + "=" * 80)
    print("ANÁLISIS DE PROSPECTOS DE VENTAS")
    print("=" * 80)

    # Definir categorías de productos/servicios
    print("\nPrimero, vamos a definir categorías de productos/servicios y sus palabras clave asociadas.")

    categories = {}
    while True:
        category_name = input("\nIngresa el nombre de una categoría de producto/servicio (o deja vacío para terminar): ")
        if not category_name:
            break

        category_keywords = input(f"Ingresa palabras clave para '{category_name}' (separadas por comas): ")
        if category_keywords:
            categories[category_name] = [k.strip().lower() for k in category_keywords.split(',')]
            print(f"Categoría '{category_name}' añadida con {len(categories[category_name])} palabras clave.")
        else:
            print("No se ingresaron palabras clave. Categoría no añadida.")

    if not categories:
        print("No se definieron categorías. Operación cancelada.")
        return

    # Solicitar filtros opcionales
    print("\nAhora, define los filtros para la búsqueda de prospectos:")
    start_date = input("Fecha de inicio (YYYY-MM-DD, opcional): ")
    end_date = input("Fecha de fin (YYYY-MM-DD, opcional): ")
    min_score = float(input("Puntuación mínima de relevancia (0-100, default 5): ") or 5)
    max_results = int(input("Número máximo de prospectos a mostrar (default 20): ") or 20)

    # Solicitar criterios de ordenación
    from chat_search.sort_utils import get_available_sort_criteria

    # Mostrar criterios disponibles
    print("\nCriterios de ordenación disponibles:")
    criteria_dict = get_available_sort_criteria()
    for i, (key, desc) in enumerate(criteria_dict.items(), 1):
        print(f"{i}. {key}: {desc}")

    # Preguntar si se desea ordenar por algún criterio específico
    use_sort = input("\n¿Deseas ordenar los resultados por algún criterio específico? (s/n): ").lower() == 's'

    sort_criteria = None
    if use_sort:
        # Solicitar hasta 3 criterios de ordenación
        sort_criteria = []

        print("\nIngresa hasta 3 criterios de ordenación (deja vacío para usar relevancia por defecto):")
        for i in range(1, 4):
            criterion = input(f"Criterio {i} (nombre o número, vacío para omitir): ").strip()

            if not criterion:
                # Omitir si está vacío
                continue

            # Verificar si es un número
            if criterion.isdigit() and 1 <= int(criterion) <= len(criteria_dict):
                # Convertir número a nombre de criterio
                criterion = list(criteria_dict.keys())[int(criterion) - 1]

            # Validar criterio
            if criterion in criteria_dict:
                sort_criteria.append(criterion)
            else:
                print(f"Criterio inválido '{criterion}'. Omitiendo.")

        # Si no se seleccionó ningún criterio, usar relevancia por defecto
        if not sort_criteria:
            sort_criteria = ['relevance']

    # Limpiar filtros
    if not start_date:
        start_date = None
    if not end_date:
        end_date = None

    # Preparar resultados por categoría
    all_prospects = {}
    category_results = {}

    # Analizar cada categoría
    for category_name, keywords in categories.items():
        print(f"\nAnalizando prospectos para categoría: {category_name}...")

        # Realizar búsqueda con cálculo de relevancia de contactos activado
        results = tool.search(
            keywords=keywords,
            min_score=min_score,
            max_results=100,  # Usar un valor alto para capturar más mensajes
            start_date=start_date,
            end_date=end_date,
            calculate_contact_relevance=True,
            preprocess_data=True,
            sort_criteria=sort_criteria
        )

        # Verificar si hay resultados
        if not isinstance(results, dict) or 'contact_relevance' not in results or not results['contact_relevance']:
            print(f"No se encontraron prospectos para la categoría '{category_name}'.")
            continue

        # Guardar resultados de esta categoría
        category_results[category_name] = results['contact_relevance']

        # Actualizar el diccionario global de prospectos
        for contact_id, data in results['contact_relevance']:
            if contact_id not in all_prospects:
                all_prospects[contact_id] = {
                    'display_name': data['display_name'],
                    'phone': data['phone'],
                    'total_score': 0,
                    'message_count': 0,
                    'categories': {},
                    'keyword_density': 0,
                    'last_interaction': None  # Se llenará después si es posible
                }

            # Actualizar datos del prospecto para esta categoría
            all_prospects[contact_id]['categories'][category_name] = {
                'score': data['score'],
                'message_count': data['message_count'],
                'keyword_density': data.get('keyword_density', 0),
                'keyword_counts': data.get('keyword_counts', {})
            }

            # Actualizar puntuación total y conteo de mensajes
            all_prospects[contact_id]['total_score'] += data['score']
            all_prospects[contact_id]['message_count'] += data['message_count']

            # Actualizar densidad de palabras clave (promedio ponderado)
            if 'keyword_density' in data:
                current_density = all_prospects[contact_id]['keyword_density']
                current_messages = all_prospects[contact_id]['message_count'] - data['message_count']
                new_density = ((current_density * current_messages) +
                              (data['keyword_density'] * data['message_count'])) / all_prospects[contact_id]['message_count']
                all_prospects[contact_id]['keyword_density'] = new_density

    # Verificar si se encontraron prospectos
    if not all_prospects:
        print("\nNo se encontraron prospectos para ninguna categoría.")
        return

    # Calcular puntuación de potencial de compra
    for contact_id, data in all_prospects.items():
        # Factores para la puntuación de potencial:
        # 1. Puntuación total de relevancia (40%)
        # 2. Densidad de palabras clave (30%)
        # 3. Número de categorías de interés (20%)
        # 4. Número total de mensajes relevantes (10%)

        relevance_factor = min(100, data['total_score'] / 10)  # Normalizar a 0-100
        density_factor = min(100, data['keyword_density'] * 100 * 5)  # Multiplicar por 5 para dar más peso
        categories_factor = min(100, len(data['categories']) * 25)  # 25 puntos por categoría
        messages_factor = min(100, data['message_count'] * 2)  # 2 puntos por mensaje

        # Calcular puntuación final ponderada
        potential_score = (
            relevance_factor * 0.4 +
            density_factor * 0.3 +
            categories_factor * 0.2 +
            messages_factor * 0.1
        )

        # Asignar nivel de potencial
        if potential_score >= 75:
            potential_level = "ALTO"
        elif potential_score >= 50:
            potential_level = "MEDIO"
        elif potential_score >= 25:
            potential_level = "BAJO"
        else:
            potential_level = "MUY BAJO"

        # Guardar puntuación y nivel
        data['potential_score'] = potential_score
        data['potential_level'] = potential_level

    # Ordenar prospectos por puntuación de potencial
    sorted_prospects = sorted(
        all_prospects.items(),
        key=lambda x: x[1]['potential_score'],
        reverse=True
    )

    # Mostrar resultados
    print("\n" + "=" * 80)
    print("RESULTADOS: PROSPECTOS DE VENTAS")
    print("=" * 80)

    total_prospects = len(sorted_prospects)
    print(f"\nSe encontraron {total_prospects} prospectos potenciales.")

    # Mostrar los prospectos más relevantes
    print("\nProspectos con mayor potencial de compra:")
    for i, (contact_id, data) in enumerate(sorted_prospects[:max_results], 1):
        print(f"\n{i}. {data['display_name']} ({data['phone']})")
        print(f"   Potencial de compra: {data['potential_level']} ({data['potential_score']:.1f}/100)")
        print(f"   Mensajes relevantes: {data['message_count']}")
        print(f"   Densidad de palabras clave: {data['keyword_density']:.2%}")

        # Mostrar interés por categorías
        print("   Interés por categorías:")
        sorted_categories = sorted(
            data['categories'].items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        for category_name, category_data in sorted_categories:
            print(f"     - {category_name}: {category_data['score']:.1f} puntos ({category_data['message_count']} mensajes)")

    # Preguntar si se desea ver mensajes de un prospecto específico
    view_option = input("\n¿Deseas ver mensajes de un prospecto específico? (s/n): ")
    if view_option.lower() == 's':
        prospect_index = int(input(f"Ingresa el número del prospecto (1-{min(max_results, total_prospects)}): "))

        if 1 <= prospect_index <= min(max_results, total_prospects):
            # Obtener el prospecto seleccionado
            _, selected_data = sorted_prospects[prospect_index - 1]

            # Preguntar por categoría específica
            print("\nCategorías disponibles:")
            for i, category_name in enumerate(selected_data['categories'].keys(), 1):
                print(f"{i}. {category_name}")

            category_index = int(input("Ingresa el número de la categoría (o 0 para todas): "))

            if category_index == 0:
                # Buscar mensajes para todas las categorías
                all_keywords = []
                for keywords in categories.values():
                    all_keywords.extend(keywords)

                # Eliminar duplicados
                all_keywords = list(set(all_keywords))

                # Extraer mensajes del contacto con todas las palabras clave
                contact_messages = tool.search(
                    keywords=all_keywords,
                    min_score=min_score,
                    max_results=50,
                    sender_filter=selected_data['display_name'],
                    start_date=start_date,
                    end_date=end_date,
                    calculate_contact_relevance=False,
                    preprocess_data=True
                )
            else:
                # Obtener categoría seleccionada
                category_names = list(selected_data['categories'].keys())
                if 1 <= category_index <= len(category_names):
                    selected_category = category_names[category_index - 1]

                    # Extraer mensajes del contacto para esta categoría
                    contact_messages = tool.search(
                        keywords=categories[selected_category],
                        min_score=min_score,
                        max_results=50,
                        sender_filter=selected_data['display_name'],
                        start_date=start_date,
                        end_date=end_date,
                        calculate_contact_relevance=False,
                        preprocess_data=True
                    )
                else:
                    print("Número de categoría inválido.")
                    contact_messages = []

            # Mostrar mensajes
            if contact_messages:
                from chat_search import print_results
                print_results(contact_messages, show_context=True, contacts=tool.contacts)
            else:
                print("No se encontraron mensajes para este prospecto con los filtros especificados.")
        else:
            print("Número de prospecto inválido.")

    # Preguntar si se desea exportar los resultados
    export_option = input("\n¿Deseas exportar estos resultados a un archivo? (s/n): ")
    if export_option.lower() == 's':
        filename = input("Ingresa el nombre del archivo: ")
        if not filename:
            filename = "prospectos_ventas.json"
        elif not (filename.endswith('.json') or filename.endswith('.md')):
            filename += ".json"

        # Exportar resultados
        from chat_search import save_results_to_file

        # Convertir la lista de tuplas a un diccionario para evitar errores de índice
        prospects_dict = {}
        for contact_id, data in sorted_prospects:
            prospects_dict[contact_id] = data

        export_data = {
            'prospects': prospects_dict,
            'categories': categories,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'min_score': min_score
            }
        }
        save_results_to_file(export_data, filename, contacts=tool.contacts)
        print(f"Resultados exportados a {filename}")

def interactive_mode(tool):
    """Run the tool in interactive mode"""
    while True:
        print("\n=== WhatsApp Unified Tool ===")
        print("1. Search by keywords")
        print("2. List available chats")
        print("3. Analyze sentiment")
        print("4. Extract topics")
        print("5. Semantic search")
        print("6. Extract entities")
        print("7. Cluster messages")
        print("8. Run complete analysis")
        print("9. Manage contact corrections")
        print("10. Analyze relevant contacts")
        print("11. Analyze messages")
        print("12. Analyze relevant chats")
        print("13. Analizar prospectos de ventas")
        print("14. Manage Google Contacts")
        print("15. Exit")

        choice = input("\nEnter your choice (1-15): ")

        if choice == '1':
            # Search by keywords using the search_interactive_handler from chat_search module
            from chat_search import search_interactive_handler
            search_interactive_handler(tool)

        elif choice == '2':
            # List available chats
            chats = tool.get_available_chats()

            print("\nAvailable Chats:")
            for i, chat in enumerate(chats, 1):
                print(f"{i}. {chat['name']} ({chat['message_count']} messages)")

        elif choice == '3':
            # Analyze sentiment
            if not ML_AVAILABLE:
                print("ML dependencies not available. Please install them first.")
                install_option = input("Do you want to install ML dependencies now? (y/n): ")
                if install_option.lower() == 'y':
                    install_ml_dependencies()
                continue

            # Ask for filters
            chat_filter = input("Filter by chat name (optional): ")
            start_date = input("Start date (YYYY-MM-DD, optional): ")
            end_date = input("End date (YYYY-MM-DD, optional): ")

            # Clean up filters
            filters = {}
            if chat_filter:
                filters['chat'] = chat_filter
            if start_date:
                filters['start_date'] = start_date
            if end_date:
                filters['end_date'] = end_date

            # Perform sentiment analysis
            results = tool.analyze_sentiment(filters=filters)

            # Ask if user wants to save results
            save_option = input("Do you want to save these results to a file? (y/n): ")
            if save_option.lower() == 'y':
                filename = input("Enter filename to save results: ")
                save_results_to_file(results, filename, contacts=tool.contacts)

        elif choice == '4':
            # Extract topics
            if not ML_AVAILABLE:
                print("ML dependencies not available. Please install them first.")
                install_option = input("Do you want to install ML dependencies now? (y/n): ")
                if install_option.lower() == 'y':
                    install_ml_dependencies()
                continue

            # Ask for filters
            chat_filter = input("Filter by chat name (optional): ")
            start_date = input("Start date (YYYY-MM-DD, optional): ")
            end_date = input("End date (YYYY-MM-DD, optional): ")
            num_topics = int(input("Number of topics to extract (default 5): ") or 5)

            # Clean up filters
            filters = {}
            if chat_filter:
                filters['chat'] = chat_filter
            if start_date:
                filters['start_date'] = start_date
            if end_date:
                filters['end_date'] = end_date

            # Extract topics
            topics, certainties = tool.extract_topics(
                num_topics=num_topics,
                filters=filters
            )

            # Ask if user wants to save results
            save_option = input("Do you want to save these results to a file? (y/n): ")
            if save_option.lower() == 'y':
                filename = input("Enter filename to save results: ")
                save_results_to_file({
                    'topics': topics,
                    'certainties': certainties
                }, filename, contacts=tool.contacts)

        elif choice == '5':
            # Semantic search
            if not ML_AVAILABLE:
                print("ML dependencies not available. Please install them first.")
                install_option = input("Do you want to install ML dependencies now? (y/n): ")
                if install_option.lower() == 'y':
                    install_ml_dependencies()
                continue

            # Ask for query and filters
            query = input("Enter search query: ")

            chat_filter = input("Filter by chat name (optional): ")
            start_date = input("Start date (YYYY-MM-DD, optional): ")
            end_date = input("End date (YYYY-MM-DD, optional): ")
            num_results = int(input("Number of results to show (default 10): ") or 10)
            use_cache = input("Use embeddings cache if available? (y/n, default y): ").lower() != 'n'

            # Clean up filters
            filters = {}
            if chat_filter:
                filters['chat'] = chat_filter
            if start_date:
                filters['start_date'] = start_date
            if end_date:
                filters['end_date'] = end_date

            # Perform semantic search
            results = tool.semantic_search(
                query=query,
                num_results=num_results,
                filters=filters,
                use_cache=use_cache
            )

            # Show results
            print_results(results, show_context=True, contacts=tool.contacts)

            # Ask if user wants to save results
            save_option = input("Do you want to save these results to a file? (y/n): ")
            if save_option.lower() == 'y':
                filename = input("Enter filename to save results: ")
                save_results_to_file(results, filename, contacts=tool.contacts)

        elif choice == '6':
            # Extract entities
            if not ML_AVAILABLE:
                print("ML dependencies not available. Please install them first.")
                install_option = input("Do you want to install ML dependencies now? (y/n): ")
                if install_option.lower() == 'y':
                    install_ml_dependencies()
                continue

            # Ask for filters
            chat_filter = input("Filter by chat name (optional): ")
            start_date = input("Start date (YYYY-MM-DD, optional): ")
            end_date = input("End date (YYYY-MM-DD, optional): ")

            # Clean up filters
            filters = {}
            if chat_filter:
                filters['chat'] = chat_filter
            if start_date:
                filters['start_date'] = start_date
            if end_date:
                filters['end_date'] = end_date

            # Extract entities
            results = tool.extract_entities(filters=filters)

            # Ask if user wants to save results
            save_option = input("Do you want to save these results to a file? (y/n): ")
            if save_option.lower() == 'y':
                filename = input("Enter filename to save results: ")
                save_results_to_file(results, filename, contacts=tool.contacts)

        elif choice == '7':
            # Cluster messages
            if not ML_AVAILABLE:
                print("ML dependencies not available. Please install them first.")
                install_option = input("Do you want to install ML dependencies now? (y/n): ")
                if install_option.lower() == 'y':
                    install_ml_dependencies()
                continue

            # Ask for filters
            chat_filter = input("Filter by chat name (optional): ")
            start_date = input("Start date (YYYY-MM-DD, optional): ")
            end_date = input("End date (YYYY-MM-DD, optional): ")
            num_clusters = int(input("Number of clusters to create (default 5): ") or 5)

            # Clean up filters
            filters = {}
            if chat_filter:
                filters['chat'] = chat_filter
            if start_date:
                filters['start_date'] = start_date
            if end_date:
                filters['end_date'] = end_date

            # Cluster messages
            results = tool.cluster_messages(
                num_clusters=num_clusters,
                filters=filters
            )

            # Ask if user wants to save results
            save_option = input("Do you want to save these results to a file? (y/n): ")
            if save_option.lower() == 'y':
                filename = input("Enter filename to save results: ")
                save_results_to_file(results, filename, contacts=tool.contacts)

        elif choice == '8':
            # Run complete analysis
            if not ML_AVAILABLE:
                print("ML dependencies not available. Please install them first.")
                install_option = input("Do you want to install ML dependencies now? (y/n): ")
                if install_option.lower() == 'y':
                    install_ml_dependencies()
                continue

            # Ask for filters
            chat_filter = input("Filter by chat name (optional): ")
            start_date = input("Start date (YYYY-MM-DD, optional): ")
            end_date = input("End date (YYYY-MM-DD, optional): ")
            num_topics = int(input("Number of topics to extract (default 5): ") or 5)
            num_clusters = int(input("Number of clusters to create (default 5): ") or 5)

            # Clean up filters
            filters = {}
            if chat_filter:
                filters['chat'] = chat_filter
            if start_date:
                filters['start_date'] = start_date
            if end_date:
                filters['end_date'] = end_date

            # Run complete analysis
            results = tool.complete_analysis(
                filters=filters,
                num_topics=num_topics,
                num_clusters=num_clusters
            )

            # Ask if user wants to save results
            save_option = input("Do you want to save these results to a file? (y/n): ")
            if save_option.lower() == 'y':
                filename = input("Enter filename to save results: ")
                save_results_to_file(results, filename, contacts=tool.contacts)

        elif choice == '9':
            # Manage contact corrections
            print("\n=== Manage Contact Corrections ===")
            print("1. Create/Update corrections file")
            print("2. Apply corrections to data")
            print("3. Back to main menu")

            subchoice = input("\nEnter your choice (1-3): ")

            if subchoice == '1':
                # Create/Update corrections file
                from whatsapp_core import create_corrections_file
                success = create_corrections_file(tool.data, tool.contacts)
                if success:
                    print("Corrections file created/updated successfully.")
                    print("Edit the file 'contact_corrections.json' to add your corrections.")
                else:
                    print("Failed to create/update corrections file.")

            elif subchoice == '2':
                # Apply corrections to data
                from whatsapp_core import apply_manual_corrections
                tool.data = apply_manual_corrections(tool.data)
                print("Corrections applied to data.")

            elif subchoice == '3':
                # Back to main menu
                continue

            else:
                print("Invalid choice. Please enter a number between 1 and 3.")

        elif choice == '10':
            # Analyze relevant contacts
            analyze_relevant_contacts(tool)

        elif choice == '11':
            # Analyze messages
            analyze_messages(tool)

        elif choice == '12':
            # Analyze relevant chats
            analyze_relevant_chats(tool)

        elif choice == '13':
            # Analizar prospectos de ventas
            analyze_sales_prospects(tool)

        elif choice == '14':
            # Manage Google Contacts
            print("\n=== Manage Google Contacts ===")
            print("1. Load Google Contacts CSV file")
            print("2. Show loaded Google Contacts")
            print("3. Back to main menu")

            subchoice = input("\nEnter your choice (1-3): ")

            if subchoice == '1':
                # Load Google Contacts CSV file
                if not GOOGLE_CONTACTS_AVAILABLE:
                    print("Google Contacts support is not available. Make sure google_contacts.py is in the same directory.")
                    continue

                file_path = input("Enter path to Google Contacts CSV file: ")
                if file_path:
                    success = tool.load_google_contacts(file_path)
                    if success:
                        print(f"Successfully loaded {len(tool.google_contacts)} contacts from Google Contacts CSV.")
                    else:
                        print("Failed to load Google Contacts CSV file.")
                else:
                    print("No file path provided.")

            elif subchoice == '2':
                # Show loaded Google Contacts
                if not tool.google_contacts:
                    print("No Google Contacts loaded. Use option 1 to load a Google Contacts CSV file.")
                    continue

                print(f"\nLoaded {len(tool.google_contacts)} Google Contacts:")

                # Show a sample of contacts
                sample_size = min(10, len(tool.google_contacts))
                sample_contacts = list(tool.google_contacts.items())[:sample_size]

                for i, (phone, contact) in enumerate(sample_contacts, 1):
                    print(f"\n{i}. {contact['display_name']}")
                    print(f"   Phone: {contact.get('phone', 'N/A')}")
                    print(f"   Raw Phone: {contact.get('phone_raw', 'N/A')}")

                if len(tool.google_contacts) > sample_size:
                    print(f"\n... and {len(tool.google_contacts) - sample_size} more contacts.")

            elif subchoice == '3':
                # Back to main menu
                continue

            else:
                print("Invalid choice. Please enter a number between 1 and 3.")

        elif choice == '15':
            # Exit
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 15.")


def main():
    """Main function for command-line usage"""
    # Use the global variable
    global ML_AVAILABLE

    parser = argparse.ArgumentParser(description='WhatsApp Unified Tool')

    # Base options
    parser.add_argument('--file', '-f', default='whatsapp_export/result.json',
                       help='Path to WhatsApp chat JSON file')
    parser.add_argument('--contacts', '-c', default='whatsapp_contacts.json',
                       help='Path to contacts JSON file')
    parser.add_argument('--google-contacts', '-g',
                       help='Path to Google Contacts CSV export file')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive mode')

    # Output option
    parser.add_argument('--output', '-o', help='Save results to file')

    # Mode selection
    parser.add_argument('--mode', choices=['search', 'sentiment', 'topics', 'semantic',
                                         'entities', 'clusters', 'all', 'corrections'],
                       help='Analysis mode (required unless in interactive mode)')

    # Search options
    parser.add_argument('--keywords', '-k', help='Keywords for search (comma-separated)')
    parser.add_argument('--min-score', '-m', type=float, default=10.0,
                       help='Minimum relevance score for search (0-100)')
    parser.add_argument('--max-results', '-r', type=int, default=20,
                       help='Maximum number of results to show')
    parser.add_argument('--contact-relevance', action='store_true', default=False,
                       help='Calculate and show contact relevance scores')
    parser.add_argument('--no-contact-relevance', action='store_false', dest='contact_relevance',
                       help='Do not calculate contact relevance scores')
    parser.add_argument('--preprocess', action='store_true', default=True,
                       help='Preprocesar datos para mejorar la búsqueda (default: True)')
    parser.add_argument('--no-preprocess', action='store_false', dest='preprocess_data',
                       help='No preprocesar datos para la búsqueda')
    parser.add_argument('--sort-by', nargs='+',
                       help='Criteria to sort results by (up to 3). Options: relevance (default), '
                            'date_asc, date_desc, sender, chat, length_asc, length_desc, '
                            'keyword_density, keyword_count')

    # ML options
    parser.add_argument('--query', '-q', help='Query for semantic search')
    parser.add_argument('--num-topics', '-t', type=int, default=5,
                       help='Number of topics to extract')
    parser.add_argument('--num-clusters', type=int, default=5,
                       help='Number of clusters to create')
    parser.add_argument('--use-cache', action='store_true', default=True,
                       help='Use embeddings cache for semantic search if available')
    parser.add_argument('--no-cache', action='store_false', dest='use_cache',
                       help='Do not use embeddings cache for semantic search')

    # Filter options
    parser.add_argument('--chat', help='Filter by chat name')
    parser.add_argument('--sender', help='Filter by sender name')
    parser.add_argument('--phone', help='Filter by phone number')
    parser.add_argument('--start-date', '-s', help='Start date filter (YYYY-MM-DD)')
    parser.add_argument('--end-date', '-e', help='End date filter (YYYY-MM-DD)')

    # Corrections options
    parser.add_argument('--create-corrections', action='store_true',
                       help='Create or update corrections file with unknown contacts')
    parser.add_argument('--apply-corrections', action='store_true',
                       help='Apply corrections from file to data')

    # Parse arguments
    args = parser.parse_args()

    # Check if ML dependencies should be installed
    if args.mode in ['sentiment', 'topics', 'semantic', 'entities', 'clusters', 'all']:
        if not ML_AVAILABLE:
            print("ML dependencies not available.")
            install_option = input("Do you want to install ML dependencies now? (y/n): ")
            if install_option.lower() == 'y':
                success = install_ml_dependencies()
                if not success:
                    print("Failed to install ML dependencies. Exiting.")
                    return
                ML_AVAILABLE = True

    # Initialize tool
    tool = WhatsAppUnifiedTool(args.file, args.contacts, args.google_contacts)

    # Check if we're in interactive mode
    if args.interactive:
        interactive_mode(tool)
        return

    # If not in interactive mode, a mode must be specified
    if not args.mode:
        print("Error: --mode must be specified when not in interactive mode.")
        parser.print_help()
        return

    # Get filters from command line arguments
    filters = {
        'chat': args.chat,
        'sender': args.sender,
        'phone': args.phone,
        'start_date': args.start_date,
        'end_date': args.end_date
    }

    # Run in the selected mode
    results = None

    try:
        if args.mode == 'search':
            from chat_search import search_command_handler
            results = search_command_handler(tool, args)

        elif args.mode == 'sentiment':
            results = tool.analyze_sentiment(filters=filters)

        elif args.mode == 'topics':
            topics, certainties = tool.extract_topics(
                num_topics=args.num_topics,
                filters=filters
            )
            results = {
                'topics': topics,
                'certainties': certainties
            }

        elif args.mode == 'semantic':
            if not args.query:
                print("Error: --query must be specified for semantic search mode.")
                return

            results = tool.semantic_search(
                query=args.query,
                num_results=args.max_results,
                filters=filters,
                use_cache=args.use_cache
            )

            print_results(results, show_context=True, contacts=tool.contacts)

        elif args.mode == 'entities':
            results = tool.extract_entities(filters=filters)

        elif args.mode == 'clusters':
            results = tool.cluster_messages(
                num_clusters=args.num_clusters,
                filters=filters
            )

        elif args.mode == 'all':
            results = tool.complete_analysis(
                filters=filters,
                num_topics=args.num_topics,
                num_clusters=args.num_clusters
            )

        elif args.mode == 'corrections':
            from whatsapp_core import create_corrections_file, apply_manual_corrections

            if args.create_corrections:
                print("Creating/updating corrections file...")
                success = create_corrections_file(tool.data, tool.contacts)
                if success:
                    print("Corrections file created/updated successfully.")
                    print("Edit the file 'contact_corrections.json' to add your corrections.")
                else:
                    print("Failed to create/update corrections file.")

            if args.apply_corrections:
                print("Applying corrections to data...")
                tool.data = apply_manual_corrections(tool.data)
                print("Corrections applied to data.")

            # Si no se especificó ninguna acción, mostrar ayuda
            if not args.create_corrections and not args.apply_corrections:
                print("Error: For corrections mode, specify at least one of --create-corrections or --apply-corrections")
                return

            # No hay resultados para guardar en este modo
            results = None

    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return

    # Save results if output file specified
    if args.output and results:
        save_results_to_file(results, args.output, contacts=tool.contacts)


if __name__ == '__main__':
    main()
