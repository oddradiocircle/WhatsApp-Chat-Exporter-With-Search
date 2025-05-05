#!/usr/bin/env python3
"""
Test Intel K-means Performance

This script tests the performance of K-means clustering with Intel optimizations.
"""

import time
import numpy as np
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs

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
