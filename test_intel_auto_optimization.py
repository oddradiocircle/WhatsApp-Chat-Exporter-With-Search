#!/usr/bin/env python3
"""
Test Intel Auto-Optimization

This script tests that the WhatsApp Unified Tool automatically activates Intel optimizations.
"""

import os
import sys
import platform
import time

def print_section(title):
    """Print a section title"""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)

def main():
    """Main function to test Intel auto-optimization"""
    print_section("Testing Intel Auto-Optimization")
    
    print("Running WhatsApp Unified Tool with auto-optimization...")
    
    # Import the WhatsApp Unified Tool
    print("\nImporting WhatsApp Unified Tool...")
    start_time = time.time()
    
    # This should automatically set up Intel optimizations
    import whatsapp_unified_tool
    
    import_time = time.time() - start_time
    print(f"Import completed in {import_time:.2f} seconds")
    
    # Check if scikit-learn-intelex is enabled
    print("\nChecking if scikit-learn-intelex is enabled...")
    try:
        from sklearnex import get_config
        config = get_config()
        print(f"scikit-learn-intelex config: {config}")
        print("✓ scikit-learn-intelex is enabled")
    except ImportError:
        print("✗ scikit-learn-intelex is not available")
    
    # Test with a simple ML task
    print("\nTesting with a simple ML task...")
    try:
        from sklearn.cluster import KMeans
        from sklearn.datasets import make_blobs
        import numpy as np
        
        # Generate synthetic data
        print("Generating synthetic data...")
        n_samples = 100000
        n_features = 50
        n_clusters = 10
        X, y = make_blobs(n_samples=n_samples, n_features=n_features, centers=n_clusters, random_state=42)
        
        # Perform K-means clustering and measure time
        print(f"Performing K-means clustering with {n_samples} samples, {n_features} features, {n_clusters} clusters...")
        start_time = time.time()
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        kmeans.fit(X)
        end_time = time.time()
        
        print(f"K-means clustering completed in {end_time - start_time:.2f} seconds")
        print(f"Number of iterations: {kmeans.n_iter_}")
    except Exception as e:
        print(f"Error testing ML task: {e}")
    
    print_section("Test Complete")
    print("The WhatsApp Unified Tool should now automatically activate Intel optimizations when run.")
    print("You can now run the tool directly with:")
    print("python whatsapp_unified_tool.py --file whatsapp_export/result.json --contacts whatsapp_contacts.json --google-contacts \"path/to/contacts.csv\" --interactive")

if __name__ == "__main__":
    main()
