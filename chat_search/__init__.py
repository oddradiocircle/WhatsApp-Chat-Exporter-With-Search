#!/usr/bin/env python3
"""
WhatsApp Chat Search Package

This package contains all the functionality related to searching WhatsApp chat data,
including basic keyword search, ML-based search, and utilities for processing search results.
"""

from .search_core import (
    calculate_relevance_score,
    extract_messages,
    get_message_context
)

from .search_utils import (
    print_results,
    save_results_to_file
)

from .search_cli import (
    search_command_handler,
    search_interactive_handler
)

from .search_ml import (
    analyze_sentiment,
    extract_topics,
    semantic_search,
    extract_entities,
    cluster_messages
)

__all__ = [
    'calculate_relevance_score',
    'extract_messages',
    'get_message_context',
    'print_results',
    'save_results_to_file',
    'search_command_handler',
    'search_interactive_handler',
    'analyze_sentiment',
    'extract_topics',
    'semantic_search',
    'extract_entities',
    'cluster_messages'
]
