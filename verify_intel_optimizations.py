#!/usr/bin/env python3
"""
Intel Optimizations Verification Script

This script verifies that Intel optimizations are properly installed and working.
It tests NumPy, scikit-learn, and PyTorch performance with Intel optimizations.
"""

import os
import sys
import platform
import importlib.util
import time

def check_module_exists(module_name):
    """Check if a Python module is installed"""
    return importlib.util.find_spec(module_name) is not None

def print_section(title):
    """Print a section title"""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)

def test_numpy_performance():
    """Test NumPy performance with matrix multiplication"""
    print_section("NumPy Performance Test")
    
    import numpy as np
    
    # Create large matrices
    size = 2000
    print(f"Creating {size}x{size} matrices...")
    A = np.random.rand(size, size)
    B = np.random.rand(size, size)
    
    # Perform matrix multiplication and measure time
    print("Performing matrix multiplication...")
    start_time = time.time()
    C = np.dot(A, B)
    end_time = time.time()
    
    print(f"Matrix multiplication completed in {end_time - start_time:.2f} seconds")
    print(f"Result shape: {C.shape}")
    
    # Check if NumPy is using MKL
    np_config = np.__config__
    if hasattr(np_config, "show") and callable(np_config.show):
        config_info = np_config.show()
        if isinstance(config_info, str) and "mkl" in config_info.lower():
            print("✓ NumPy is using Intel MKL")
        else:
            print("✗ NumPy is NOT using Intel MKL")
            print("NumPy configuration:")
            print(config_info)

def test_sklearn_performance():
    """Test scikit-learn performance with Intel optimizations"""
    print_section("Scikit-learn Performance Test")
    
    if not check_module_exists("sklearn"):
        print("Scikit-learn not installed. Skipping test.")
        return
    
    # Check if Intel Extension for Scikit-learn is available
    intelex_available = check_module_exists("sklearnex")
    if intelex_available:
        print("Intel Extension for Scikit-learn is available")
        
        # Try to patch scikit-learn
        try:
            from sklearnex import patch_sklearn, config_context
            patch_sklearn()
            print("✓ Scikit-learn patched with Intel optimizations")
        except Exception as e:
            print(f"✗ Failed to patch scikit-learn: {e}")
            return
    else:
        print("Intel Extension for Scikit-learn is NOT available")
        return
    
    # Test K-means clustering performance
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

def test_pytorch_performance():
    """Test PyTorch performance with Intel optimizations"""
    print_section("PyTorch Performance Test")
    
    if not check_module_exists("torch"):
        print("PyTorch not installed. Skipping test.")
        return
    
    import torch
    print(f"PyTorch version: {torch.__version__}")
    
    # Check if Intel Extension for PyTorch is available
    ipex_available = check_module_exists("intel_extension_for_pytorch")
    if ipex_available:
        print("Intel Extension for PyTorch is available")
        try:
            import intel_extension_for_pytorch as ipex
            print(f"IPEX version: {ipex.__version__}")
        except Exception as e:
            print(f"✗ Failed to import IPEX: {e}")
    else:
        print("Intel Extension for PyTorch is NOT available")
    
    # Check for Intel GPU
    intel_gpu_available = False
    try:
        if hasattr(torch, "xpu") and callable(getattr(torch.xpu, "is_available", None)):
            intel_gpu_available = torch.xpu.is_available()
            if intel_gpu_available:
                print(f"✓ Intel GPU is available: {torch.xpu.get_device_name(0)}")
                device = torch.device("xpu")
            else:
                print("✗ Intel GPU is NOT available")
                device = torch.device("cpu")
        else:
            print("✗ PyTorch XPU support is NOT available")
            device = torch.device("cpu")
    except Exception as e:
        print(f"✗ Error checking Intel GPU: {e}")
        device = torch.device("cpu")
    
    # Test matrix multiplication performance
    print("\nTesting matrix multiplication performance...")
    size = 2000
    print(f"Creating {size}x{size} matrices...")
    
    # Create tensors
    A = torch.rand(size, size, device=device)
    B = torch.rand(size, size, device=device)
    
    # Warm-up
    for _ in range(3):
        C = torch.matmul(A, B)
    
    # Measure performance
    start_time = time.time()
    C = torch.matmul(A, B)
    if device.type != "cpu":  # Need to synchronize for GPU timing
        torch.xpu.synchronize() if intel_gpu_available else torch.cuda.synchronize()
    end_time = time.time()
    
    print(f"Matrix multiplication completed in {end_time - start_time:.2f} seconds")
    print(f"Result shape: {C.shape}")

def main():
    """Main function to verify Intel optimizations"""
    print_section("Intel Optimizations Verification")
    
    print(f"Python version: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")
    print(f"Processor: {platform.processor()}")
    
    # Check for Intel optimizations
    print("\nChecking for Intel optimizations:")
    optimizations = {
        "scikit-learn-intelex": check_module_exists("sklearnex"),
        "intel-extension-for-pytorch": check_module_exists("intel_extension_for_pytorch"),
        "numpy": check_module_exists("numpy"),
        "scipy": check_module_exists("scipy"),
        "torch": check_module_exists("torch")
    }
    
    for name, available in optimizations.items():
        print(f"- {name}: {'Available' if available else 'Not available'}")
    
    # Run performance tests
    test_numpy_performance()
    test_sklearn_performance()
    test_pytorch_performance()
    
    print_section("Verification Complete")

if __name__ == "__main__":
    main()
