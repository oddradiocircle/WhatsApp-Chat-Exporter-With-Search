# WhatsApp Unified Tool

This tool combines all the functionality of WhatsApp Chat Exporter's search and ML analysis capabilities into a single, easy-to-use interface. It provides both interactive and command-line modes for accessing all features.

## Features

### Basic Features
- **Keyword Search**: Find messages containing specific keywords with relevance scoring
- **Advanced Filtering**: Filter by chat, sender, phone number, and date range
- **Contact Information**: Enhanced display of phone numbers and contact names
- **Message Context**: See surrounding messages for better context understanding
- **Result Saving**: Save search and analysis results to JSON files

### Machine Learning Features
- **Sentiment Analysis**: Classify messages as positive, negative, or neutral
- **Topic Extraction**: Identify the main topics discussed in conversations
- **Semantic Search**: Find messages based on meaning rather than exact keywords
- **Entity Recognition**: Extract people, places, organizations, and other entities from messages
- **Message Clustering**: Group similar messages together to identify patterns
- **Topic Certainty Indicator**: Calculate how certain a conversation is about specific topics

## Prerequisites

- Python 3.6 or higher
- WhatsApp chat data exported using WhatsApp-Chat-Exporter (result.json file)
- Contact information (optional, whatsapp_contacts.json file)
- ML dependencies for advanced features (optional, can be installed on demand)

## Installation

1. Make sure you have Python 3.6 or higher installed
2. Clone or download the WhatsApp-Chat-Exporter repository
3. Install the basic dependencies:

```bash
pip install tqdm
```

4. For ML features, you can either:
   - Install dependencies when prompted by the tool
   - Install them in advance:

```bash
python install_ml_dependencies.py
```

### Project Structure

The project is organized as follows:

- `whatsapp_unified_tool.py`: Main script that provides the unified interface
- `whatsapp_core.py`: Core functionality for loading and processing WhatsApp data
- `chat_search/`: Module containing all search-related functionality
  - `__init__.py`: Package initialization and exports
  - `search_core.py`: Core search functionality
  - `search_utils.py`: Utilities for displaying and saving search results
  - `search_cli.py`: Command-line interface for search
  - `search_ml.py`: Machine learning-based search functionality
  - `README.md`: Documentation for the search module

## Usage

### Interactive Mode

The easiest way to use the tool is through the interactive interface:

```bash
python whatsapp_unified_tool.py --file whatsapp_export/result.json --contacts whatsapp_contacts.json --interactive
```

This will start an interactive session where you can:
1. Search by keywords
2. List available chats
3. Analyze sentiment
4. Extract topics
5. Perform semantic search
6. Extract named entities
7. Cluster messages
8. Run a complete analysis
9. Exit the program

### Command-Line Mode

For more direct usage, you can use the tool with command-line arguments:

```bash
python whatsapp_unified_tool.py --mode search --keywords "meeting,project" --file whatsapp_export/result.json
```

#### Available Modes

- `search`: Search for messages containing specific keywords
- `sentiment`: Analyze the sentiment of messages
- `topics`: Extract main topics from conversations
- `semantic`: Perform semantic search (requires `--query` parameter)
- `entities`: Extract named entities from messages
- `clusters`: Group similar messages together
- `all`: Perform all analyses at once

#### Base Options

- `--file`, `-f`: Path to the WhatsApp chat JSON file (default: whatsapp_export/result.json)
- `--contacts`, `-c`: Path to the contacts JSON file (default: whatsapp_contacts.json)
- `--interactive`, `-i`: Run in interactive mode
- `--output`, `-o`: Save results to a file

#### Search Options

- `--keywords`, `-k`: Comma-separated list of keywords to search for
- `--min-score`, `-m`: Minimum relevance score (0-100, default: 10)
- `--max-results`, `-r`: Maximum number of results to show (default: 20)

#### ML Options

- `--query`, `-q`: Query for semantic search
- `--num-topics`, `-t`: Number of topics to extract (default: 5)
- `--num-clusters`: Number of clusters to create (default: 5)

#### Filter Options

- `--chat`: Filter by chat name
- `--sender`: Filter by sender name
- `--phone`: Filter by phone number
- `--start-date`, `-s`: Start date filter (YYYY-MM-DD)
- `--end-date`, `-e`: End date filter (YYYY-MM-DD)

## Examples

### Basic Search

```bash
python whatsapp_unified_tool.py --mode search --keywords "meeting,project" --min-score 20
```

### Sentiment Analysis

```bash
python whatsapp_unified_tool.py --mode sentiment --chat "Work Group" --output sentiment_results.json
```

### Topic Extraction

```bash
python whatsapp_unified_tool.py --mode topics --num-topics 10 --start-date 2023-01-01 --end-date 2023-12-31
```

### Semantic Search

```bash
python whatsapp_unified_tool.py --mode semantic --query "project deadline" --max-results 15
```

### Entity Extraction

```bash
python whatsapp_unified_tool.py --mode entities --chat "Family Group"
```

### Message Clustering

```bash
python whatsapp_unified_tool.py --mode clusters --num-clusters 8 --sender "John"
```

### Complete Analysis

```bash
python whatsapp_unified_tool.py --mode all --chat "Work Group" --output full_analysis.json
```

## Understanding Results

### Search Results

Search results include:
- The message content
- Relevance score (0-100)
- Matched keywords
- Sender information (name and phone number)
- Date and time
- Chat name
- Context messages (previous and next)

### Sentiment Analysis

Sentiment analysis classifies messages as:
- Positive: Messages with positive emotional tone
- Negative: Messages with negative emotional tone
- Neutral: Messages with neutral emotional tone

Results include percentage breakdown and polarity/subjectivity scores for each message.

### Topic Extraction

Topic extraction identifies main discussion topics by:
- Grouping related keywords together
- Calculating topic certainty (how strongly the conversation focuses on each topic)
- Providing a list of keywords for each topic

### Semantic Search

Semantic search finds messages based on meaning, not just keywords:
- Uses advanced embedding models to understand query meaning
- Returns messages ranked by semantic similarity
- Works even when exact keywords aren't present

### Entity Recognition

Entity recognition identifies:
- People (PER): Names of individuals
- Organizations (ORG): Companies, institutions
- Locations (LOC): Places, geographic locations
- Dates (DATE): Temporal references
- And other entity types

### Message Clustering

Message clustering:
- Groups similar messages together
- Identifies representative keywords for each cluster
- Shows distribution of messages across clusters
- Helps identify patterns and common themes

## Tips for Effective Use

1. **Start with Interactive Mode**: Get familiar with the tool's capabilities before using command-line options
2. **Use Filters Wisely**: Narrow down your analysis by chat, sender, or date range for more focused results
3. **Combine Approaches**: Use basic search to find keywords, then semantic search for related concepts
4. **Save Important Results**: Use the `--output` option to save analysis results for future reference
5. **Install ML Dependencies**: For best performance with advanced features, install all ML dependencies

## Troubleshooting

- **Slow Performance**: For large chat exports, consider filtering by chat or date range
- **Memory Errors**: Reduce the number of messages analyzed by using more specific filters
- **Missing ML Features**: Make sure you've installed the required ML dependencies
- **Incorrect Contacts**: Ensure your contacts file is correctly formatted and up to date
- **Installation Errors**: If you encounter errors installing ML dependencies, try installing them manually with pip

## Under the Hood

The WhatsApp Unified Tool brings together multiple components:
- Core functionality from `whatsapp_core.py`
- Search capabilities from the `chat_search` module:
  - `search_core.py`: Core search functionality (relevance scoring, message extraction, context retrieval)
  - `search_utils.py`: Utilities for displaying and saving search results
  - `search_cli.py`: Command-line interface for search functionality
  - `search_ml.py`: Machine learning-based search functionality
- Interactive interface for easier user experience

All search-related functionality has been organized into a dedicated module, making the codebase more modular and easier to maintain. The main file (`whatsapp_unified_tool.py`) now focuses on orchestrating the different components rather than implementing all the functionality itself.
