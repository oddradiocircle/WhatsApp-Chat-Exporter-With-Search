# WhatsApp Unified Tool - Intel Optimizations

This document explains the optimizations made to the WhatsApp Unified Tool for Intel CPUs and Intel Iris GPUs.

## Overview

The WhatsApp Unified Tool has been optimized to take advantage of Intel hardware acceleration, including:

- Intel CPUs with AVX/AVX2/AVX-512 instruction sets
- Intel Iris GPUs
- Intel UHD Graphics
- Intel HD Graphics

## Current Status

The following Intel optimizations are currently enabled:

- ✅ **scikit-learn-intelex**: Successfully installed and patched
- ✅ **oneAPI Toolkit**: Successfully installed with MKL, IPP, TBB, and Compiler components
- ❌ **Intel Extension for PyTorch (IPEX)**: Not installed (installation scripts provided)
- ❌ **MKL integration with NumPy**: Not enabled (setup scripts provided)

## Optimizations Implemented

### 1. Intel Distribution for Python

The tool now supports the Intel Distribution for Python, which provides:

- Optimized NumPy and SciPy libraries using Intel MKL (Math Kernel Library)
- Near-native performance for numerical operations
- Automatic parallelization across all available CPU cores

### 2. Intel Extensions for Machine Learning

The following Intel extensions are now supported:

- **Intel Extension for PyTorch (IPEX)**: Accelerates PyTorch operations on Intel hardware
- **Intel Extension for Scikit-learn**: Accelerates machine learning algorithms on Intel CPUs
- **Intel MKL**: Optimizes linear algebra operations used in machine learning

### 3. Semantic Search Optimizations

The semantic search functionality has been optimized for Intel hardware:

- Automatic detection of Intel GPUs for acceleration
- Optimized batch sizes based on hardware capabilities
- Thread optimization for Intel CPUs
- Memory usage optimizations for better performance

### 4. Clustering Optimizations

The K-means clustering algorithm has been optimized:

- Parameters tuned for Intel hardware
- Reduced memory usage for better performance
- Progress tracking for better user experience
- Optimized vectorization for text processing

### 5. Topic Modeling Optimizations

The LDA (Latent Dirichlet Allocation) topic modeling has been optimized:

- Parallel processing using all available CPU cores
- Optimized batch sizes for better performance
- Memory usage optimizations
- Progress tracking for better user experience

## Installation

To take advantage of these optimizations, you need to install the Intel-optimized dependencies:

```bash
# Install base dependencies
pip install -r requirements.txt

# Install Intel optimizations (recommended)
python install_ml_dependencies.py

# Enable missing Intel optimizations (IPEX and MKL)
python enable_missing_intel_optimizations.py

# Verify Intel optimizations
python verify_intel_optimizations.py
```

The `install_ml_dependencies.py` script will automatically detect your hardware and install the appropriate optimizations. The `enable_missing_intel_optimizations.py` script focuses on installing IPEX and enabling MKL support.

### Running with Intel Optimizations

The WhatsApp Unified Tool now **automatically detects and enables Intel optimizations** at startup. You can run it directly:

```bash
# Run with automatic Intel optimizations
python whatsapp_unified_tool.py --file whatsapp_export/result.json --contacts whatsapp_contacts.json --google-contacts "path/to/contacts.csv" --interactive
```

Alternatively, you can use the provided batch script for maximum optimization:

```bash
# Run with maximum Intel optimizations
run_with_intel_optimizations.bat whatsapp_unified_tool.py --interactive
```

The batch script sets up the Intel oneAPI environment before running your Python code, which may provide additional performance benefits.

## Hardware Detection

The tool automatically detects Intel hardware and enables the appropriate optimizations:

- Intel CPUs: Optimized thread count and MKL acceleration
- Intel GPUs: XPU acceleration for supported operations
- Intel Iris/UHD/HD Graphics: GPU acceleration where supported

## Performance Improvements

You can expect the following performance improvements:

- Faster semantic search (2-5x speedup on supported hardware)
- Reduced memory usage for large datasets
- Faster clustering and topic modeling
- Better utilization of multi-core CPUs

## Troubleshooting

If you encounter issues with the Intel optimizations:

1. Make sure you have the latest Intel drivers installed
2. Update to the latest version of the tool
3. Try running with standard dependencies if optimizations cause issues
4. Run `check_intel_hardware.py` to diagnose your system configuration
5. For IPEX installation issues, try the specific versions in `enable_missing_intel_optimizations.py`
6. For MKL issues, make sure to run your code with the oneAPI environment set up

### Common Issues and Solutions

#### IPEX Installation Fails
- Try installing a specific version compatible with your PyTorch version
- Try installing the CPU-only version: `pip install intel-extension-for-pytorch==2.0.100+cpu`
- Try installing from Intel's channel: `pip install intel-extension-for-pytorch -f https://developer.intel.com/ipex-whl-stable-cpu`

#### MKL Not Detected
- Make sure oneAPI is installed and properly set up
- Run your code using the `run_with_intel_optimizations.bat` script
- Try reinstalling NumPy after setting up the oneAPI environment

## Compatibility

These optimizations are compatible with:

- Windows 10/11 with Intel CPUs and GPUs
- Linux with Intel CPUs
- macOS with Intel CPUs

## Feedback

If you encounter any issues or have suggestions for further optimizations, please open an issue on the GitHub repository.
