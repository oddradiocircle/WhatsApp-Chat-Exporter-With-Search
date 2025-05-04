# WhatsApp Chat Search Module

This module contains all the functionality related to searching WhatsApp chat data, including basic keyword search, ML-based search, and utilities for processing search results. It was created to organize all search-related functionality in a dedicated folder, making the codebase more modular and easier to maintain.

## Structure

- `__init__.py`: Package initialization and exports of all public functions
- `search_core.py`: Core search functionality:
  - `calculate_relevance_score`: Calculate relevance score for messages based on keywords
  - `extract_messages`: Extract messages from WhatsApp data with various filters
  - `get_message_context`: Get surrounding messages for context
- `search_utils.py`: Utilities for displaying and saving search results:
  - `print_results`: Display search results in a readable format
  - `save_results_to_file`: Save results to JSON or Markdown files
- `search_cli.py`: Command-line interface for search functionality:
  - `search_command_handler`: Handle search commands from the command line
  - `search_interactive_handler`: Handle search in interactive mode
- `search_ml.py`: Machine learning-based search functionality:
  - `analyze_sentiment`: Classify messages as positive, negative, or neutral
  - `extract_topics`: Identify main topics in conversations
  - `semantic_search`: Find messages based on meaning rather than exact keywords
  - `extract_entities`: Extract named entities (people, places, organizations, etc.)
  - `cluster_messages`: Group similar messages together

## Features

### Basic Search Features
- Keyword search with relevance scoring
- Message context retrieval
- Contact and chat relevance calculation
- Advanced filtering (by chat, sender, phone number, date range)

### ML-Based Search Features
- Sentiment analysis
- Topic extraction
- Semantic search
- Named entity recognition
- Message clustering

## Usage

### Basic Search
```python
from chat_search import calculate_relevance_score, extract_messages, get_message_context

# Extract messages with filters
messages = extract_messages(
    data,                      # WhatsApp chat data (loaded from result.json)
    contacts=contacts,         # Contact information (optional)
    chat_filter="John",        # Filter by chat name (optional)
    start_date="2023-01-01",   # Start date filter (YYYY-MM-DD, optional)
    end_date="2023-12-31",     # End date filter (YYYY-MM-DD, optional)
    sender_filter=None,        # Filter by sender name (optional)
    phone_filter=None          # Filter by phone number (optional)
)

# Calculate relevance score for a message
score, matched_keywords, keyword_counts = calculate_relevance_score(
    message_text,              # Message content to analyze
    ["keyword1", "keyword2"]   # List of keywords to search for
)

# Get message context
context = get_message_context(
    data,                      # WhatsApp chat data
    chat_id,                   # ID of the chat
    message_id,                # ID of the message
    contacts=contacts,         # Contact information (optional)
    context_size=2             # Number of messages before and after (default: 2)
)
```

### Display and Save Results
```python
from chat_search import print_results, save_results_to_file

# Print search results
print_results(
    results,                   # Search results (list or dict with 'results' key)
    show_context=True,         # Whether to show context messages (default: True)
    show_contact_relevance=True, # Whether to show contact relevance (default: True)
    contacts=contacts          # Contact information (optional)
)

# Save results to file
save_results_to_file(
    results,                   # Search results to save
    "search_results.json",     # Filename (use .json or .md extension)
    contacts=contacts          # Contact information (optional)
)
```

### ML-Based Search
```python
from chat_search.search_ml import analyze_sentiment, extract_topics, semantic_search, extract_entities, cluster_messages

# Analyze sentiment
sentiment_results = analyze_sentiment(
    tool,                      # WhatsAppUnifiedTool instance
    messages=None,             # List of messages (optional, will be extracted if None)
    filters=None               # Filters to apply when extracting messages (optional)
)

# Extract topics
topics, certainties = extract_topics(
    tool,                      # WhatsAppUnifiedTool instance
    messages=None,             # List of messages (optional)
    num_topics=5,              # Number of topics to extract (default: 5)
    filters=None               # Filters to apply (optional)
)

# Semantic search
semantic_results = semantic_search(
    tool,                      # WhatsAppUnifiedTool instance
    query="important message", # Search query
    messages=None,             # List of messages (optional)
    num_results=10,            # Maximum number of results (default: 10)
    filters=None,              # Filters to apply (optional)
    use_cache=True             # Whether to use cached embeddings (default: True)
)

# Extract entities
entity_results = extract_entities(
    tool,                      # WhatsAppUnifiedTool instance
    messages=None,             # List of messages (optional)
    filters=None               # Filters to apply (optional)
)

# Cluster messages
clustered_messages = cluster_messages(
    tool,                      # WhatsAppUnifiedTool instance
    messages=None,             # List of messages (optional)
    num_clusters=5,            # Number of clusters to create (default: 5)
    filters=None               # Filters to apply (optional)
)
```

## Command-Line Interface
The module provides handlers for both interactive and command-line modes:

```python
from chat_search import search_interactive_handler, search_command_handler

# Interactive mode
search_interactive_handler(
    tool                       # WhatsAppUnifiedTool instance
)

# Command-line mode
search_command_handler(
    tool,                      # WhatsAppUnifiedTool instance
    args                       # Command-line arguments from argparse
)
```

## Integration with WhatsApp Unified Tool

The module is designed to be used with the WhatsAppUnifiedTool class:

```python
from whatsapp_core import load_json_data, load_contacts
from chat_search import extract_messages, calculate_relevance_score

# Initialize the tool
tool = WhatsAppUnifiedTool(data_file="whatsapp_export/result.json", contacts_file="whatsapp_contacts.json")

# Use the search method
results = tool.search(
    keywords="meeting,project",
    min_score=10,
    max_results=20,
    chat_filter="Work Group",
    start_date="2023-01-01",
    end_date="2023-12-31"
)
```
