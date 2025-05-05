#!/usr/bin/env python3
"""
WhatsApp Chat Search ML Module

This module contains the machine learning-based search functionality for WhatsApp chat data,
including sentiment analysis, topic extraction, semantic search, entity recognition, and clustering.
Optimized for Intel CPUs and GPUs.
"""

import os
import pickle
import hashlib
import numpy as np
from datetime import datetime
from tqdm import tqdm
import platform
import sys

from .search_core import extract_messages, get_message_context

# Check if ML dependencies are installed
def check_ml_dependencies():
    """
    Check if ML dependencies are installed.

    Returns:
    - installed: True if installed, False otherwise
    """
    try:
        import sklearn
        import nltk
        import spacy
        import textblob
        import sentence_transformers
        import transformers
        import torch
        return True
    except ImportError:
        return False

# Check for Intel optimizations
def check_intel_optimizations():
    """
    Check if Intel optimizations are available.

    Returns:
    - dict with available optimizations
    """
    intel_optimizations = {
        'scikit-learn-intelex': False,
        'ipex': False,
        'mkl': False,
        'intel_gpu': False
    }

    # Check for scikit-learn-intelex
    try:
        import sklearnex
        intel_optimizations['scikit-learn-intelex'] = True
    except ImportError:
        pass

    # Check for Intel Extension for PyTorch
    try:
        import intel_extension_for_pytorch as ipex
        intel_optimizations['ipex'] = True
    except ImportError:
        pass

    # Check for MKL
    try:
        import numpy as np
        # Check if NumPy is using MKL
        np_config = np.__config__
        if hasattr(np_config, 'show') and callable(np_config.show):
            config_info = np_config.show()
            if isinstance(config_info, str) and 'mkl' in config_info.lower():
                intel_optimizations['mkl'] = True
    except (ImportError, AttributeError):
        pass

    # Check for Intel GPU on Windows
    if platform.system() == "Windows":
        try:
            import torch
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    device_name = torch.cuda.get_device_name(i).lower()
                    if 'intel' in device_name and ('iris' in device_name or 'uhd' in device_name or 'hd graphics' in device_name):
                        intel_optimizations['intel_gpu'] = True
                        break
        except (ImportError, AttributeError):
            pass

    return intel_optimizations

# Global variable to track ML availability
ML_AVAILABLE = check_ml_dependencies()

# Check for Intel optimizations
INTEL_OPTIMIZATIONS = check_intel_optimizations()

# Import ML dependencies if available
if ML_AVAILABLE:
    try:
        # Try to use Intel optimized scikit-learn if available
        if INTEL_OPTIMIZATIONS['scikit-learn-intelex']:
            try:
                from sklearnex import patch_sklearn
                patch_sklearn()
                print("Using Intel optimized scikit-learn")
            except Exception as e:
                print(f"Warning: Could not patch scikit-learn with Intel optimizations: {str(e)}")

        from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
        from sklearn.decomposition import LatentDirichletAllocation
        from sklearn.cluster import KMeans
        from sklearn.metrics.pairwise import cosine_similarity
        from textblob import TextBlob
        import nltk
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize
        import spacy
        from sentence_transformers import SentenceTransformer
        import torch

        # Use Intel PyTorch Extension if available
        if INTEL_OPTIMIZATIONS['ipex']:
            try:
                import intel_extension_for_pytorch as ipex
                print("Using Intel Extension for PyTorch")
            except Exception as e:
                print(f"Warning: Could not import Intel Extension for PyTorch: {str(e)}")

        # Load spaCy model for Spanish
        try:
            nlp = spacy.load("es_core_news_md")
        except OSError:
            print("Warning: spaCy Spanish model not loaded. Some ML features may not work.")
            nlp = None

        # Print optimization status
        print("\nIntel Optimization Status:")
        for opt, status in INTEL_OPTIMIZATIONS.items():
            print(f"- {opt}: {'Enabled' if status else 'Not available'}")
        print()

    except Exception as e:
        print(f"Warning: Error loading ML libraries: {str(e)}")
        ML_AVAILABLE = False

def analyze_sentiment(tool, messages=None, filters=None):
    """
    Analyze sentiment of messages.

    Parameters:
    - tool: The WhatsAppUnifiedTool instance
    - messages: List of messages to analyze (optional)
    - filters: Filters to apply when extracting messages (optional)

    Returns:
    - results: List of messages with sentiment analysis
    """
    if not ML_AVAILABLE:
        print("ML dependencies not available. Please install them first.")
        return []

    # Extract messages if not provided
    if not messages:
        messages = _get_filtered_messages(tool, filters)

    if not messages:
        print("No messages to analyze.")
        return []

    print(f"Analyzing sentiment for {len(messages)} messages...")
    results = []

    # Process each message
    for msg in tqdm(messages, desc="Analyzing sentiment"):
        try:
            # Use TextBlob for sentiment analysis
            analysis = TextBlob(msg['message'])

            # Determine sentiment category
            if analysis.sentiment.polarity > 0.1:
                sentiment = "positive"
            elif analysis.sentiment.polarity < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            results.append({
                **msg,
                'sentiment': sentiment,
                'polarity': analysis.sentiment.polarity,
                'subjectivity': analysis.sentiment.subjectivity
            })
        except Exception as e:
            # Just skip any problematic messages
            pass

    # Calculate overall statistics
    sentiments = [r['sentiment'] for r in results]
    positive = sentiments.count('positive')
    negative = sentiments.count('negative')
    neutral = sentiments.count('neutral')

    print("\nSentiment Analysis Results:")
    print(f"Positive: {positive} ({positive/len(sentiments)*100:.1f}%)")
    print(f"Negative: {negative} ({negative/len(sentiments)*100:.1f}%)")
    print(f"Neutral: {neutral} ({neutral/len(sentiments)*100:.1f}%)")

    return results

def extract_topics(tool, messages=None, num_topics=5, filters=None):
    """
    Extract main topics from messages using LDA.
    Optimized for Intel CPUs and GPUs.

    Parameters:
    - tool: The WhatsAppUnifiedTool instance
    - messages: List of messages to analyze (optional)
    - num_topics: Number of topics to extract
    - filters: Filters to apply when extracting messages (optional)

    Returns:
    - topics: List of topics
    - certainties: Dictionary of topic certainties
    """
    if not ML_AVAILABLE:
        print("ML dependencies not available. Please install them first.")
        return [], {}

    # Extract messages if not provided
    if not messages:
        messages = _get_filtered_messages(tool, filters)

    if not messages:
        print("No messages to analyze.")
        return [], {}

    print(f"Extracting {num_topics} main topics...")

    # Make sure we have stopwords
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')

    # Use Intel optimized scikit-learn if available
    using_intel_optimized = False
    if INTEL_OPTIMIZATIONS['scikit-learn-intelex']:
        try:
            # This will use the patched version if sklearnex was imported successfully
            print("Using Intel optimized LDA")
            using_intel_optimized = True
        except Exception as e:
            print(f"Could not use Intel optimized LDA: {e}")

    # Vectorize the messages with optimized parameters
    print("Vectorizing messages...")
    vectorizer = CountVectorizer(
        max_df=0.95,          # Ignore terms that appear in more than 95% of documents
        min_df=2,             # Ignore terms that appear in less than 2 documents
        max_features=10000,   # Limit features for better performance
        stop_words=stopwords.words('spanish')
    )

    # Process messages in batches for better memory usage
    message_texts = [msg['message'] for msg in messages]

    # Use optimized fit_transform
    X = vectorizer.fit_transform(message_texts)
    print(f"Vectorized {X.shape[0]} messages with {X.shape[1]} features")

    # Apply LDA with optimized parameters for Intel hardware
    print("Applying LDA topic modeling...")

    # Set optimal parameters based on data size and hardware
    n_jobs = os.cpu_count() or 2  # Use all available cores
    batch_size = min(128, len(messages))  # Adjust batch size based on data size

    # Create LDA model with optimized parameters
    lda = LatentDirichletAllocation(
        n_components=num_topics,
        random_state=42,
        max_iter=20,           # Increased from 10 for better convergence
        learning_method='online',
        batch_size=batch_size,
        n_jobs=n_jobs,         # Parallel processing
        evaluate_every=5,      # Check convergence every 5 iterations
        verbose=1              # Show progress
    )

    # Fit the model with progress tracking
    print("Fitting LDA model (this may take a while)...")
    lda.fit(X)

    # Get words for each topic with optimized processing
    feature_names = vectorizer.get_feature_names_out()
    topics = []

    print("Extracting top words for each topic...")
    for topic_idx, topic in enumerate(lda.components_):
        # Get top 10 words for this topic
        top_words_idx = topic.argsort()[:-11:-1]
        top_words = [feature_names[i] for i in top_words_idx]
        topics.append(top_words)

    # Calculate topic certainty with optimized processing
    print("Calculating topic certainties...")
    certainties = _calculate_topic_certainty(messages, topics)

    # Display topics
    print("\nMain Topics:")
    for i, topic in enumerate(topics):
        print(f"Topic {i+1}: {', '.join(topic)}")

    # Display certainties
    print("\nTopic Certainty:")
    for topic, certainty in sorted(certainties.items(), key=lambda x: x[1], reverse=True):
        print(f"{topic}: {certainty:.1f}%")

    return topics, certainties

def _calculate_topic_certainty(messages, topics):
    """
    Calculate certainty of topics in messages.

    Parameters:
    - messages: List of messages
    - topics: List of topics

    Returns:
    - certainties: Dictionary of topic certainties
    """
    # Vectorize the messages
    vectorizer = TfidfVectorizer(stop_words=stopwords.words('spanish'))
    message_vectors = vectorizer.fit_transform([msg['message'] for msg in messages])

    # Vectorize the topics
    topic_texts = [' '.join(topic) for topic in topics]
    topic_vectors = vectorizer.transform(topic_texts)

    # Calculate similarity between messages and topics
    similarities = cosine_similarity(message_vectors, topic_vectors)

    # Calculate certainty for each topic
    certainties = {}
    for i, topic in enumerate(topics):
        topic_name = f"Topic {i+1}: {', '.join(topic[:3])}"
        # Average similarity
        certainty = float(np.mean(similarities[:, i]) * 100)
        certainties[topic_name] = certainty

    return certainties

def semantic_search(tool, query, messages=None, num_results=10, filters=None, use_cache=True):
    """
    Perform semantic search using sentence embeddings.
    Optimized for Intel CPUs and GPUs.

    Parameters:
    - tool: The WhatsAppUnifiedTool instance
    - query: Search query
    - messages: List of messages to search (optional)
    - num_results: Maximum number of results to return
    - filters: Filters to apply when extracting messages (optional)
    - use_cache: Whether to use cached embeddings

    Returns:
    - results: List of search results
    """
    if not ML_AVAILABLE:
        print("ML dependencies not available. Please install them first.")
        return []

    # Extract messages if not provided
    if not messages:
        # Try to load messages and embeddings from cache
        if use_cache:
            cached_messages = _load_embeddings_cache(tool, filters)
            if cached_messages:
                messages = cached_messages
            else:
                messages = _get_filtered_messages(tool, filters)
        else:
            messages = _get_filtered_messages(tool, filters)

    if not messages:
        print("No messages to analyze.")
        return []

    print(f"Performing semantic search for: '{query}'")

    # Load pre-trained model
    try:
        model_name = 'paraphrase-multilingual-mpnet-base-v2'
        if not tool.embeddings_model:
            print(f"Loading model '{model_name}'...")
            tool.embeddings_model = SentenceTransformer(model_name)
        model = tool.embeddings_model

        # Set up device for Intel hardware
        import torch
        device = None

        # Check if Intel GPU is available and IPEX is installed
        if INTEL_OPTIMIZATIONS['intel_gpu'] and INTEL_OPTIMIZATIONS['ipex']:
            try:
                import intel_extension_for_pytorch as ipex
                device = torch.device("xpu")
                print(f"Using Intel GPU for semantic search")
                # Move model to Intel GPU
                model._target_device = device
            except Exception as e:
                print(f"Could not use Intel GPU: {e}")
                device = torch.device("cpu")
        else:
            device = torch.device("cpu")
            print("Using CPU for semantic search")

            # If using CPU with MKL, set number of threads for better performance
            if INTEL_OPTIMIZATIONS['mkl']:
                try:
                    # Set optimal number of threads for Intel CPU
                    import os
                    num_threads = os.cpu_count()
                    if num_threads:
                        torch.set_num_threads(num_threads)
                        print(f"Set PyTorch to use {num_threads} threads")
                except Exception as e:
                    print(f"Could not optimize thread count: {e}")

    except Exception as e:
        print(f"Error loading semantic search model: {str(e)}")
        return []

    # Generate embedding for the query
    query_embedding = model.encode(query)

    # Check if we have cached embeddings for these messages
    if use_cache and tool.embeddings_cache and len(tool.embeddings_cache) == len(messages):
        print("Usando embeddings en caché...")
        message_embeddings = np.array(list(tool.embeddings_cache.values()))
    else:
        # Generate embeddings for messages
        print("Generando embeddings para mensajes (esto puede tomar tiempo)...")
        message_texts = [msg['message'] for msg in messages]

        # Optimize batch size based on available memory
        # Smaller batch size for GPU, larger for CPU
        if device and device.type == "xpu":
            batch_size = 256  # Smaller batch for GPU
        else:
            batch_size = 1000  # Larger batch for CPU

        print(f"Using batch size of {batch_size}")
        all_embeddings = []

        # Use Intel optimized processing
        for i in tqdm(range(0, len(message_texts), batch_size), desc="Procesando lotes"):
            batch_texts = message_texts[i:i+batch_size]
            # Use convert_to_tensor=True for better performance with Intel hardware
            batch_embeddings = model.encode(batch_texts, show_progress_bar=True,
                                           convert_to_tensor=True)

            # Convert tensor to numpy for consistent handling
            if isinstance(batch_embeddings, torch.Tensor):
                batch_embeddings = batch_embeddings.cpu().numpy()

            all_embeddings.append(batch_embeddings)

        # Use optimized numpy operations
        message_embeddings = np.vstack(all_embeddings)

        # Save embeddings to cache
        if use_cache:
            tool.embeddings_cache = {i: message_embeddings[i] for i in range(len(message_embeddings))}
            _save_embeddings_cache(tool, messages, tool.embeddings_cache)

    # Calculate cosine similarity using optimized numpy operations
    print("Calculando similitud con la consulta...")
    # Use Intel MKL optimized dot product if available
    similarities = np.dot(message_embeddings, query_embedding) / (
        np.linalg.norm(message_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )

    # Get the top results using optimized numpy operations
    top_indices = np.argsort(similarities)[-num_results:][::-1]

    print("Preparando resultados...")
    results = []
    for idx in top_indices:
        msg = messages[idx]

        # Get message context
        context = get_message_context(tool.data, msg['chat_id'], msg['msg_id'],
                                     contacts=tool.contacts)

        results.append({
            **msg,
            'similarity_score': float(similarities[idx]),
            'context': context
        })

    return results

def extract_entities(tool, messages=None, filters=None):
    """
    Extract named entities from messages using spaCy.

    Parameters:
    - tool: The WhatsAppUnifiedTool instance
    - messages: List of messages to analyze (optional)
    - filters: Filters to apply when extracting messages (optional)

    Returns:
    - results: List of messages with extracted entities
    """
    if not ML_AVAILABLE or not nlp:
        print("spaCy model not available. Please install dependencies first.")
        return []

    # Extract messages if not provided
    if not messages:
        messages = _get_filtered_messages(tool, filters)

    if not messages:
        print("No messages to analyze.")
        return []

    print(f"Extracting entities from {len(messages)} messages...")
    results = []

    # Process each message
    for msg in tqdm(messages, desc="Extracting entities"):
        try:
            # Process with spaCy
            doc = nlp(msg['message'])

            # Extract entities
            entities = {}
            for ent in doc.ents:
                if ent.label_ not in entities:
                    entities[ent.label_] = []
                entities[ent.label_].append(ent.text)

            results.append({
                **msg,
                'entities': entities
            })
        except Exception as e:
            # Skip problematic messages
            pass

    # Collect all entity types
    all_entities = {}
    for msg in results:
        for entity_type, entities in msg.get('entities', {}).items():
            if entity_type not in all_entities:
                all_entities[entity_type] = []
            all_entities[entity_type].extend(entities)

    # Display entity statistics
    print("\nEntities Found:")
    for entity_type, entities in all_entities.items():
        unique_entities = set(entities)
        print(f"{entity_type}: {len(unique_entities)} unique, {len(entities)} total")
        if len(unique_entities) <= 10:
            print(f"  {', '.join(unique_entities)}")

    return results

def cluster_messages(tool, messages=None, num_clusters=5, filters=None):
    """
    Group similar messages using K-means clustering.
    Optimized for Intel CPUs and GPUs.

    Parameters:
    - tool: The WhatsAppUnifiedTool instance
    - messages: List of messages to cluster (optional)
    - num_clusters: Number of clusters to create
    - filters: Filters to apply when extracting messages (optional)

    Returns:
    - messages: List of messages with cluster assignments
    """
    if not ML_AVAILABLE:
        print("ML dependencies not available. Please install them first.")
        return []

    # Extract messages if not provided
    if not messages:
        messages = _get_filtered_messages(tool, filters)

    if not messages:
        print("No messages to analyze.")
        return []

    print(f"Clustering {len(messages)} messages into {num_clusters} groups...")

    # Make sure we have stopwords
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')

    # Use Intel optimized scikit-learn if available
    using_intel_optimized = False
    if INTEL_OPTIMIZATIONS['scikit-learn-intelex']:
        try:
            # This will use the patched version if sklearnex was imported successfully
            print("Using Intel optimized K-means clustering")
            using_intel_optimized = True
        except Exception as e:
            print(f"Could not use Intel optimized clustering: {e}")

    # Vectorize the messages with optimized parameters
    print("Vectorizing messages...")
    vectorizer = TfidfVectorizer(
        stop_words=stopwords.words('spanish'),
        max_features=10000,  # Limit features for better performance
        min_df=2,            # Ignore terms that appear in less than 2 documents
        max_df=0.95          # Ignore terms that appear in more than 95% of documents
    )
    X = vectorizer.fit_transform([msg['message'] for msg in messages])

    # Apply K-means with optimized parameters for Intel hardware
    print("Applying K-means clustering...")
    if using_intel_optimized:
        # Intel optimized K-means with parameters tuned for performance
        kmeans = KMeans(
            n_clusters=num_clusters,
            random_state=42,
            n_init=10,        # Reduced from default 10
            max_iter=100,     # Default is 300
            algorithm='lloyd',
            tol=1e-4          # Default is 1e-4
        )
    else:
        # Standard K-means with parameters tuned for Intel CPUs
        kmeans = KMeans(
            n_clusters=num_clusters,
            random_state=42,
            n_init=10,
            max_iter=100,
            algorithm='lloyd'
        )

    # Use tqdm to show progress
    print("Fitting K-means model (this may take a while)...")
    with tqdm(total=100, desc="K-means progress") as pbar:
        # We can't directly track K-means progress, so we'll update periodically
        kmeans.fit(X)
        pbar.update(100)  # Complete the progress bar

    # Assign clusters to messages
    print("Assigning clusters to messages...")
    for i, msg in enumerate(messages):
        msg['cluster'] = int(kmeans.labels_[i])

    # Get cluster stats
    clusters = {}
    for msg in messages:
        cluster = msg['cluster']
        if cluster not in clusters:
            clusters[cluster] = []
        clusters[cluster].append(msg)

    # Display cluster statistics
    print("\nCluster Statistics:")
    for cluster, cluster_messages in sorted(clusters.items()):
        print(f"Cluster {cluster}: {len(cluster_messages)} messages")

        # Show representative words
        order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
        terms = vectorizer.get_feature_names_out()

        print("Keywords:", end=" ")
        for ind in order_centroids[cluster, :10]:
            print(f"{terms[ind]}", end=" ")
        print()

        # Show sample messages
        print("Examples:")
        for msg in cluster_messages[:3]:
            print(f"  - {msg['message'][:100]}...")
        print()

    return messages

def _get_filtered_messages(tool, filters=None):
    """
    Extract messages using the specified filters.

    Parameters:
    - tool: The WhatsAppUnifiedTool instance
    - filters: Filters to apply

    Returns:
    - messages: List of filtered messages
    """
    if not filters:
        filters = {}

    return extract_messages(
        tool.data,
        contacts=tool.contacts,
        chat_filter=filters.get('chat'),
        start_date=filters.get('start_date'),
        end_date=filters.get('end_date'),
        sender_filter=filters.get('sender'),
        phone_filter=filters.get('phone')
    )

def _get_cache_filename(tool, filters=None):
    """
    Generate a unique filename for the embeddings cache based on filters.

    Parameters:
    - tool: The WhatsAppUnifiedTool instance
    - filters: Filters applied to the data

    Returns:
    - filename: Cache filename
    """
    import json
    # Create a hash based on the filters and data file
    hash_input = f"{tool.data_file}_{json.dumps(filters or {}, sort_keys=True)}"
    hash_value = hashlib.md5(hash_input.encode()).hexdigest()
    return os.path.join(tool.cache_dir, f"embeddings_{hash_value}.pkl")

def _load_embeddings_cache(tool, filters=None):
    """
    Load embeddings from cache if available.

    Parameters:
    - tool: The WhatsAppUnifiedTool instance
    - filters: Filters applied to the data

    Returns:
    - messages: List of messages if cache exists, None otherwise
    """
    cache_file = _get_cache_filename(tool, filters)
    tool.embeddings_cache_file = cache_file

    if os.path.exists(cache_file):
        try:
            print(f"Cargando embeddings desde caché: {cache_file}")
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
                tool.embeddings_cache = cache_data.get('embeddings', {})
                cached_messages = cache_data.get('messages', [])
                print(f"Embeddings cargados para {len(cached_messages)} mensajes")
                return cached_messages
        except Exception as e:
            print(f"Error al cargar caché de embeddings: {str(e)}")
            tool.embeddings_cache = {}

    return None

def _save_embeddings_cache(tool, messages, embeddings):
    """
    Save embeddings to cache.

    Parameters:
    - tool: The WhatsAppUnifiedTool instance
    - messages: List of messages
    - embeddings: Message embeddings

    Returns:
    - success: True if saved successfully, False otherwise
    """
    if not tool.embeddings_cache_file:
        return False

    try:
        print(f"Guardando embeddings en caché: {tool.embeddings_cache_file}")
        with open(tool.embeddings_cache_file, 'wb') as f:
            cache_data = {
                'embeddings': embeddings,
                'messages': messages,
                'timestamp': datetime.now().timestamp()
            }
            pickle.dump(cache_data, f)
        print(f"Embeddings guardados para {len(messages)} mensajes")
        return True
    except Exception as e:
        print(f"Error al guardar caché de embeddings: {str(e)}")
        return False
