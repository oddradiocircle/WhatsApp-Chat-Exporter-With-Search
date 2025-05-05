#!/usr/bin/env python3
"""
WhatsApp Chat Search CLI Module

This module contains the command-line interface for the WhatsApp chat search functionality.
"""

from .search_core import calculate_relevance_score, extract_messages, get_message_context
from .search_utils import print_results, save_results_to_file

def search_command_handler(tool, args):
    """
    Handle the search command from the command line.

    Parameters:
    - tool: The WhatsAppUnifiedTool instance
    - args: Command line arguments

    Returns:
    - results: Search results
    """
    if not args.keywords:
        print("Error: --keywords must be specified for search mode.")
        return None

    # Determinar si se debe preprocesar los datos
    preprocess_data = getattr(args, 'preprocess_data', True)
    if hasattr(args, 'no_preprocess'):
        preprocess_data = not args.no_preprocess

    results = tool.search(
        keywords=args.keywords,
        min_score=args.min_score,
        max_results=args.max_results,
        start_date=args.start_date,
        end_date=args.end_date,
        chat_filter=args.chat,
        sender_filter=args.sender,
        phone_filter=args.phone,
        calculate_contact_relevance=args.contact_relevance,
        preprocess_data=preprocess_data,
        sort_criteria=args.sort_by
    )

    print_results(results, show_context=True, contacts=tool.contacts)

    return results

def search_interactive_handler(tool):
    """
    Handle the search command in interactive mode.

    Parameters:
    - tool: The WhatsAppUnifiedTool instance

    Returns:
    - results: Search results
    """
    # Ask for search parameters
    keywords = input("Enter keywords (comma-separated): ")

    # Ask for filters
    chat_filter = input("Filter by chat name (optional): ")
    sender_filter = input("Filter by sender name (optional): ")
    phone_filter = input("Filter by phone number (optional): ")
    start_date = input("Start date (YYYY-MM-DD, optional): ")
    end_date = input("End date (YYYY-MM-DD, optional): ")
    min_score = float(input("Minimum relevance score (0-100, default 10): ") or 10)
    max_results = int(input("Maximum results to show (default 20): ") or 20)
    preprocess = input("Preprocesar datos para mejorar la búsqueda? (s/n, default s): ").lower() != 'n'
    calculate_contact_relevance = input("Calcular relevancia de contactos? (s/n, default s): ").lower() != 'n'

    # Ask for sort criteria
    from .sort_utils import get_available_sort_criteria

    # Show available sort criteria
    print("\nAvailable sort criteria:")
    criteria_dict = get_available_sort_criteria()
    for i, (key, desc) in enumerate(criteria_dict.items(), 1):
        print(f"{i}. {key}: {desc}")

    # Ask for up to 3 sort criteria
    sort_criteria = []

    print("\nEnter up to 3 sort criteria (leave empty to use default 'relevance'):")
    for i in range(1, 4):
        criterion = input(f"Sort criterion {i} (name or number, empty to skip): ").strip()

        if not criterion:
            # Skip if empty
            continue

        # Check if it's a number
        if criterion.isdigit() and 1 <= int(criterion) <= len(criteria_dict):
            # Convert number to criterion name
            criterion = list(criteria_dict.keys())[int(criterion) - 1]

        # Validate criterion
        if criterion in criteria_dict:
            sort_criteria.append(criterion)
        else:
            print(f"Invalid criterion '{criterion}'. Skipping.")

    # If no criteria selected, use default
    if not sort_criteria:
        sort_criteria = ['relevance']

    # Clean up filters
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

    # Perform search
    results = tool.search(
        keywords=keywords,
        min_score=min_score,
        max_results=max_results,
        start_date=start_date,
        end_date=end_date,
        chat_filter=chat_filter,
        sender_filter=sender_filter,
        phone_filter=phone_filter,
        calculate_contact_relevance=calculate_contact_relevance,
        preprocess_data=preprocess,
        sort_criteria=sort_criteria
    )

    # Show results
    print_results(results, show_context=True, contacts=tool.contacts)

    # Ask if user wants to save results
    save_option = input("Do you want to save these results to a file? (y/n): ")
    if save_option.lower() == 'y':
        filename = input("Enter filename to save results: ")
        save_results_to_file(results, filename, contacts=tool.contacts)

    return results
