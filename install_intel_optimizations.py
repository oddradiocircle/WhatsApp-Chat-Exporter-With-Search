#!/usr/bin/env python3
"""
Intel Optimizations Installation Script

This script installs Intel-optimized libraries and dependencies for the WhatsApp Unified Tool.
It provides better support for Intel CPUs and GPUs, including:
- Intel Extension for Scikit-learn
- Intel Extension for PyTorch (IPEX)
- Intel MKL (Math Kernel Library)
- Intel oneAPI optimizations
"""

import os
import sys
import platform
import subprocess
import importlib.util
from pathlib import Path

def check_module_exists(module_name):
    """Check if a Python module is installed"""
    return importlib.util.find_spec(module_name) is not None

def detect_intel_hardware():
    """Detect Intel CPU and GPU hardware"""
    hardware_info = {
        "intel_cpu": False,
        "intel_gpu": False,
        "gpu_name": None,
        "cpu_name": None
    }
    
    # Check for Intel CPU
    processor = platform.processor().lower()
    if "intel" in processor:
        hardware_info["intel_cpu"] = True
        hardware_info["cpu_name"] = processor
    
    # Check for Intel GPU on Windows
    if platform.system() == "Windows":
        try:
            # Create a temporary file for dxdiag output
            temp_file = "temp_dxdiag.txt"
            subprocess.run(["dxdiag", "/t", temp_file], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)
            
            # Wait for the file to be created
            import time
            time.sleep(2)
            
            if os.path.exists(temp_file):
                with open(temp_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().lower()
                    
                    # Check for Intel GPU
                    if "intel" in content and any(gpu in content for gpu in ["iris", "uhd", "hd graphics"]):
                        hardware_info["intel_gpu"] = True
                        
                        # Try to extract GPU name
                        for line in content.split('\n'):
                            if "name:" in line and "intel" in line:
                                hardware_info["gpu_name"] = line.split("name:", 1)[1].strip()
                                break
                
                # Clean up
                os.remove(temp_file)
        except Exception as e:
            print(f"Error detecting GPU: {e}")
    
    return hardware_info

def install_base_dependencies():
    """Install base ML dependencies"""
    base_dependencies = [
        "tqdm",
        "numpy",
        "scipy",
        "scikit-learn",
        "nltk",
        "textblob",
        "spacy",
        "sentence-transformers",
        "transformers"
    ]
    
    print("Installing base dependencies...")
    for dep in base_dependencies:
        print(f"Installing {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", dep])
            print(f"✓ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {dep}: {e}")
            print("Continuing with installation...")

def install_pytorch(hardware_info):
    """Install PyTorch with Intel optimizations if possible"""
    print("\nInstalling PyTorch with Intel optimizations...")
    
    try:
        # First, try to install the standard PyTorch
        print("Installing PyTorch...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "torch", "torchvision", "torchaudio"])
        print("✓ PyTorch installed successfully")
        
        # Then try to install Intel Extension for PyTorch
        if hardware_info["intel_cpu"] or hardware_info["intel_gpu"]:
            print("\nInstalling Intel Extension for PyTorch (IPEX)...")
            print("This may take a while...")
            
            # Try different installation methods
            methods = [
                # Method 1: Direct pip install
                [sys.executable, "-m", "pip", "install", "intel-extension-for-pytorch"],
                
                # Method 2: Specific version
                [sys.executable, "-m", "pip", "install", "intel-extension-for-pytorch==2.0.100"],
                
                # Method 3: From Intel channel
                [sys.executable, "-m", "pip", "install", "intel-extension-for-pytorch", "-f", "https://developer.intel.com/ipex-whl-stable-cpu"],
                
                # Method 4: CPU-only version
                [sys.executable, "-m", "pip", "install", "intel-extension-for-pytorch==2.0.100+cpu"]
            ]
            
            success = False
            for i, method in enumerate(methods):
                try:
                    print(f"\nTrying installation method {i+1}...")
                    subprocess.check_call(method)
                    print(f"✓ Intel Extension for PyTorch installed successfully using method {i+1}")
                    success = True
                    break
                except subprocess.CalledProcessError as e:
                    print(f"✗ Method {i+1} failed: {e}")
            
            if not success:
                print("\n⚠️ Could not install Intel Extension for PyTorch.")
                print("The WhatsApp tool will still work, but without Intel GPU acceleration.")
                print("You can try installing it manually later.")
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install PyTorch: {e}")
        print("Continuing with installation...")

def install_scikit_learn_intelex():
    """Install Intel Extension for Scikit-learn"""
    print("\nInstalling Intel Extension for Scikit-learn...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "scikit-learn-intelex"])
        print("✓ Intel Extension for Scikit-learn installed successfully")
        
        # Verify installation
        try:
            import sklearnex
            from sklearnex import patch_sklearn
            patch_sklearn()
            print("✓ Intel Extension for Scikit-learn verified and patched successfully")
        except ImportError:
            print("⚠️ Intel Extension for Scikit-learn installed but could not be imported")
        except Exception as e:
            print(f"⚠️ Intel Extension for Scikit-learn installed but could not be patched: {e}")
    
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install Intel Extension for Scikit-learn: {e}")
        print("Continuing with installation...")

def install_language_resources():
    """Install language resources for NLP"""
    print("\nInstalling language resources...")
    
    # Download spaCy model for Spanish
    try:
        print("Downloading spaCy model for Spanish...")
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "es_core_news_md"])
        print("✓ Spanish language model installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to download spaCy model: {e}")
        print("Continuing with installation...")
    
    # Download NLTK resources
    try:
        print("Downloading NLTK resources...")
        import nltk
        for resource in ['punkt', 'stopwords', 'wordnet']:
            print(f"Downloading {resource}...")
            nltk.download(resource)
        print("✓ NLTK resources installed successfully")
    except Exception as e:
        print(f"✗ Failed to download NLTK resources: {e}")
        print("Continuing with installation...")

def check_oneapi_installation():
    """Check if Intel oneAPI is installed and provide instructions if not"""
    oneapi_installed = False
    
    # Check common oneAPI installation paths
    oneapi_paths = []
    
    if platform.system() == "Windows":
        oneapi_paths = [
            r"C:\Program Files (x86)\Intel\oneAPI",
            r"C:\Program Files\Intel\oneAPI"
        ]
    elif platform.system() == "Linux":
        oneapi_paths = [
            "/opt/intel/oneapi",
            os.path.expanduser("~/intel/oneapi")
        ]
    elif platform.system() == "Darwin":  # macOS
        oneapi_paths = [
            "/opt/intel/oneapi",
            os.path.expanduser("~/intel/oneapi")
        ]
    
    # Check if any of the paths exist
    for path in oneapi_paths:
        if os.path.exists(path):
            oneapi_installed = True
            print(f"\n✓ Intel oneAPI detected at: {path}")
            break
    
    if not oneapi_installed:
        print("\n⚠️ Intel oneAPI not detected.")
        print("For maximum performance, consider installing Intel oneAPI Base Toolkit.")
        print("Download from: https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit-download.html")
        
        # Ask if user wants to download
        download_option = input("\nDo you want to open the download page for Intel oneAPI? (y/n): ")
        if download_option.lower() == 'y':
            import webbrowser
            webbrowser.open("https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit-download.html")

def create_verification_script():
    """Create a script to verify Intel optimizations"""
    script_path = Path("verify_intel_optimizations.py")
    
    script_content = """#!/usr/bin/env python3
\"\"\"
Intel Optimizations Verification Script

This script verifies that Intel optimizations are properly installed and working.
\"\"\"

import os
import sys
import platform
import importlib.util
import numpy as np
import time

def check_module_exists(module_name):
    \"\"\"Check if a Python module is installed\"\"\"
    return importlib.util.find_spec(module_name) is not None

def print_section(title):
    \"\"\"Print a section title\"\"\"
    print("\\n" + "=" * 50)
    print(title)
    print("=" * 50)

def test_numpy_performance():
    \"\"\"Test NumPy performance with matrix multiplication\"\"\"
    print_section("NumPy Performance Test")
    
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

def test_sklearn_performance():
    \"\"\"Test scikit-learn performance with Intel optimizations\"\"\"
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
    \"\"\"Test PyTorch performance with Intel optimizations\"\"\"
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
    print("\\nTesting matrix multiplication performance...")
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
    \"\"\"Main function to verify Intel optimizations\"\"\"
    print_section("Intel Optimizations Verification")
    
    print(f"Python version: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")
    print(f"Processor: {platform.processor()}")
    
    # Check for Intel optimizations
    print("\\nChecking for Intel optimizations:")
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
"""
    
    with open(script_path, "w") as f:
        f.write(script_content)
    
    print(f"\n✓ Created verification script: {script_path}")
    print("You can run this script to verify that Intel optimizations are working correctly.")

def main():
    """Main function to install Intel optimizations"""
    print("=" * 50)
    print("Intel Optimizations Installation")
    print("=" * 50)
    print("\nThis script will install Intel-optimized libraries for the WhatsApp Unified Tool.")
    
    # Detect Intel hardware
    print("\nDetecting Intel hardware...")
    hardware_info = detect_intel_hardware()
    
    if hardware_info["intel_cpu"]:
        print(f"✓ Intel CPU detected: {hardware_info['cpu_name']}")
    else:
        print("✗ Intel CPU not detected. Some optimizations may not be available.")
    
    if hardware_info["intel_gpu"]:
        print(f"✓ Intel GPU detected: {hardware_info['gpu_name']}")
    else:
        print("✗ Intel GPU not detected. GPU acceleration will not be available.")
    
    # Confirm installation
    print("\nThis script will install the following:")
    print("1. Base ML dependencies (numpy, scipy, scikit-learn, etc.)")
    print("2. PyTorch with Intel optimizations")
    print("3. Intel Extension for Scikit-learn")
    print("4. Language resources for NLP (spaCy, NLTK)")
    
    proceed = input("\nDo you want to proceed with the installation? (y/n): ")
    if proceed.lower() != 'y':
        print("Installation cancelled.")
        return
    
    # Install dependencies
    install_base_dependencies()
    install_pytorch(hardware_info)
    install_scikit_learn_intelex()
    install_language_resources()
    
    # Check for oneAPI
    check_oneapi_installation()
    
    # Create verification script
    create_verification_script()
    
    print("\n" + "=" * 50)
    print("Installation Complete")
    print("=" * 50)
    print("\nIntel optimizations have been installed successfully.")
    print("You can now run the WhatsApp Unified Tool with improved performance.")
    print("\nTo verify the optimizations, run:")
    print("python verify_intel_optimizations.py")

if __name__ == "__main__":
    main()
