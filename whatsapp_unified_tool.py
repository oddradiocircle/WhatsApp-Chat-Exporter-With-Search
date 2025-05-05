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
"""

import argparse
import os
from tqdm import tqdm
import traceback

# Import core functionality
from whatsapp_core import (
    load_json_data,
    load_contacts,
    format_phone_number,
    install_ml_dependencies
)

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

    def __init__(self, data_file=None, contacts_file=None):
        """Initialize the tool with data and contacts files"""
        self.data = None
        self.contacts = {}
        self.data_file = data_file
        self.contacts_file = contacts_file
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

    def load_data(self, file_path):
        """Load WhatsApp chat data from a JSON file"""
        self.data_file = file_path
        self.data = load_json_data(file_path)
        return self.data is not None

    def load_contacts(self, file_path):
        """Load contact information from a JSON file"""
        self.contacts_file = file_path
        self.contacts = load_contacts(file_path)
        return len(self.contacts) > 0



    def get_available_chats(self):
        """Get a list of available chats"""
        if not self.data:
            return []

        chats = []
        for chat_id, chat_data in self.data.items():
            # Extraer número de teléfono del chat_id (eliminar @s.whatsapp.net)
            phone_raw = chat_id.split('@')[0] if '@' in chat_id else chat_id

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
                if not chat_name or chat_name == chat_id:
                    chat_name = formatted_phone

            # Crear nombre de visualización que incluya tanto el nombre del contacto como el número telefónico
            if '-' in phone_raw:  # Es un chat de grupo
                if chat_name and chat_name != chat_id and chat_name != phone_raw:
                    display_name = f"{chat_name} (Grupo {phone_raw})"
                else:
                    display_name = f"Grupo {phone_raw}"
            else:  # Es un chat individual
                if chat_name and chat_name != chat_id and chat_name != phone_raw and not phone_raw.startswith(chat_name):
                    display_name = f"{chat_name} ({formatted_phone})"
                else:
                    display_name = formatted_phone

            # Contar mensajes
            message_count = len(chat_data.get('messages', {}))

            chats.append({
                'id': chat_id,
                'name': display_name,
                'phone': formatted_phone,
                'contact_name': chat_name,
                'message_count': message_count
            })

        # Ordenar por nombre
        chats.sort(key=lambda x: x['name'])
        return chats

    def search(self, keywords=None, min_score=10, max_results=20, start_date=None,
              end_date=None, chat_filter=None, sender_filter=None, phone_filter=None,
              calculate_contact_relevance=False):
        """Search through messages using keywords and filters"""
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

        # Extract messages based on filters
        all_messages = extract_messages(
            self.data,
            contacts=self.contacts,
            chat_filter=chat_filter,
            start_date=start_date,
            end_date=end_date,
            sender_filter=sender_filter,
            phone_filter=phone_filter
        )

        if not all_messages:
            print("No messages found with the specified filters.")
            return []

        print(f"Processing {len(all_messages)} messages...")
        results = []

        # Para calcular la relevancia de contactos
        contact_relevance = {}
        chat_relevance = {}

        # Process each message
        for msg in tqdm(all_messages, desc="Searching"):
            # Calculate relevance score
            score, matched_keywords, keyword_counts = calculate_relevance_score(msg['message'], keywords)

            # Skip if score is below threshold
            if score < min_score or not matched_keywords:
                continue

            # Get message context
            context = get_message_context(self.data, msg['chat_id'], msg['msg_id'],
                                         contacts=self.contacts)

            # Add to results
            results.append({
                **msg,
                'score': score,
                'matched_keywords': matched_keywords,
                'context': context
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
                            'display_name': msg.get('sender', sender_id),
                            'phone': phone_raw
                        }

                    # Actualizar puntuación y conteo
                    contact_relevance[sender_id]['score'] += score
                    contact_relevance[sender_id]['message_count'] += 1

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
                            'display_name': chat_name,
                            'phone': chat_phone if '@' in chat_id else chat_id
                        }

                    # Actualizar puntuación y conteo
                    chat_relevance[chat_id]['score'] += score
                    chat_relevance[chat_id]['message_count'] += 1

                    # Actualizar conteo de palabras clave
                    for keyword, count in keyword_counts.items():
                        if keyword not in chat_relevance[chat_id]['keyword_counts']:
                            chat_relevance[chat_id]['keyword_counts'][keyword] = 0
                        chat_relevance[chat_id]['keyword_counts'][keyword] += count

            # Sort and trim results periodically
            if len(results) % 100 == 0:
                results.sort(key=lambda x: x['score'], reverse=True)
                results = results[:max_results]

        # Final sort and limit
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:max_results]

        # Calcular puntuación final para contactos y chats
        if calculate_contact_relevance:
            # Normalizar puntuaciones de contactos
            for contact_id, data in contact_relevance.items():
                if data['message_count'] > 0:
                    data['avg_score'] = data['score'] / data['message_count']
                else:
                    data['avg_score'] = 0

            # Normalizar puntuaciones de chats
            for chat_id, data in chat_relevance.items():
                if data['message_count'] > 0:
                    data['avg_score'] = data['score'] / data['message_count']
                else:
                    data['avg_score'] = 0

            # Ordenar contactos y chats por puntuación
            sorted_contacts = sorted(
                contact_relevance.items(),
                key=lambda x: x[1]['score'],
                reverse=True
            )

            sorted_chats = sorted(
                chat_relevance.items(),
                key=lambda x: x[1]['score'],
                reverse=True
            )

            return {
                'results': results,
                'contact_relevance': sorted_contacts,
                'chat_relevance': sorted_chats
            }

        return results

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
        print("9. Exit")

        choice = input("\nEnter your choice (1-9): ")

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
            # Exit
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 9.")


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
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive mode')

    # Output option
    parser.add_argument('--output', '-o', help='Save results to file')

    # Mode selection
    parser.add_argument('--mode', choices=['search', 'sentiment', 'topics', 'semantic',
                                         'entities', 'clusters', 'all'],
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
    tool = WhatsAppUnifiedTool(args.file, args.contacts)

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

    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return

    # Save results if output file specified
    if args.output and results:
        save_results_to_file(results, args.output, contacts=tool.contacts)


if __name__ == '__main__':
    main()
