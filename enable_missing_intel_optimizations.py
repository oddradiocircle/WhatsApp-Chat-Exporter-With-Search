#!/usr/bin/env python3
"""
Enable Missing Intel Optimizations

This script focuses on enabling the missing Intel optimizations detected by check_intel_hardware.py:
- Intel Extension for PyTorch (IPEX)
- MKL integration with NumPy

It's designed to work with the existing Intel optimizations already installed.
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

def install_ipex():
    """Install Intel Extension for PyTorch (IPEX)"""
    print("\n" + "=" * 50)
    print("Installing Intel Extension for PyTorch (IPEX)")
    print("=" * 50)
    
    # Check PyTorch version first
    try:
        import torch
        torch_version = torch.__version__
        print(f"Detected PyTorch version: {torch_version}")
        
        # Extract major.minor version
        version_parts = torch_version.split('+')[0].split('.')
        major_minor = f"{version_parts[0]}.{version_parts[1]}"
        print(f"PyTorch major.minor version: {major_minor}")
        
    except ImportError:
        print("PyTorch not installed. Installing PyTorch first...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchvision", "torchaudio"])
            import torch
            torch_version = torch.__version__
            version_parts = torch_version.split('+')[0].split('.')
            major_minor = f"{version_parts[0]}.{version_parts[1]}"
        except Exception as e:
            print(f"Failed to install PyTorch: {e}")
            return False
    
    # Try different installation methods for IPEX
    methods = [
        # Method 1: Direct pip install
        [sys.executable, "-m", "pip", "install", "intel-extension-for-pytorch"],
        
        # Method 2: Version-specific install
        [sys.executable, "-m", "pip", "install", f"intel-extension-for-pytorch=={major_minor}.0"],
        
        # Method 3: CPU-only version
        [sys.executable, "-m", "pip", "install", f"intel-extension-for-pytorch=={major_minor}.0+cpu"],
        
        # Method 4: From Intel channel
        [sys.executable, "-m", "pip", "install", "intel-extension-for-pytorch", "-f", "https://developer.intel.com/ipex-whl-stable-cpu"],
        
        # Method 5: Specific older version that might be more compatible
        [sys.executable, "-m", "pip", "install", "intel-extension-for-pytorch==2.0.100+cpu"],
        
        # Method 6: Very specific version
        [sys.executable, "-m", "pip", "install", "intel-extension-for-pytorch==2.0.110+cpu"]
    ]
    
    success = False
    for i, method in enumerate(methods):
        try:
            print(f"\nTrying IPEX installation method {i+1}...")
            subprocess.check_call(method)
            
            # Verify installation
            try:
                import intel_extension_for_pytorch as ipex
                print(f"✓ Intel Extension for PyTorch installed successfully (version {ipex.__version__})")
                success = True
                break
            except ImportError:
                print("Installation seemed to succeed but module cannot be imported.")
                continue
                
        except subprocess.CalledProcessError as e:
            print(f"Method {i+1} failed: {e}")
    
    if not success:
        print("\n⚠️ Could not install Intel Extension for PyTorch after trying multiple methods.")
        print("The WhatsApp tool will still work, but without Intel PyTorch optimizations.")
        return False
    
    return True

def enable_mkl_for_numpy():
    """Enable MKL for NumPy"""
    print("\n" + "=" * 50)
    print("Enabling MKL for NumPy")
    print("=" * 50)
    
    # Check if oneAPI is installed
    oneapi_path = None
    if platform.system() == "Windows":
        possible_paths = [
            r"C:\Program Files (x86)\Intel\oneAPI",
            r"C:\Program Files\Intel\oneAPI"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                oneapi_path = path
                break
    
    if oneapi_path:
        print(f"Found oneAPI at: {oneapi_path}")
        
        # Create a batch file to set up oneAPI environment
        batch_file = "setup_oneapi_env.bat"
        with open(batch_file, "w") as f:
            f.write(f'call "{oneapi_path}\\setvars.bat"\n')
            f.write(f'echo MKL environment variables set up successfully\n')
            f.write(f'echo You can now run your Python scripts with MKL support\n')
            f.write(f'echo To use this environment, run: {batch_file}\n')
        
        print(f"\n✓ Created oneAPI environment setup script: {batch_file}")
        print(f"Run this script before running your Python code to enable MKL support.")
        
        # Try to install numpy with MKL
        try:
            print("\nInstalling NumPy with MKL support...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--force-reinstall", "numpy"])
            
            # Check if MKL is now available
            import importlib
            import numpy as np
            importlib.reload(np)
            
            np_config = np.__config__
            if hasattr(np_config, "show") and callable(np_config.show):
                config_info = np_config.show()
                if isinstance(config_info, str) and "mkl" in config_info.lower():
                    print("✓ NumPy is now using MKL")
                    return True
                else:
                    print("NumPy reinstalled but MKL not detected.")
            else:
                print("Cannot check NumPy configuration.")
        except Exception as e:
            print(f"Error reinstalling NumPy: {e}")
    else:
        print("oneAPI not found on the system.")
        print("Please install Intel oneAPI Base Toolkit to enable MKL support.")
        print("Download from: https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit-download.html")
    
    return False

def update_search_ml_file():
    """Update the search_ml.py file to better handle Intel optimizations"""
    print("\n" + "=" * 50)
    print("Updating search_ml.py to better handle Intel optimizations")
    print("=" * 50)
    
    # Check if the file exists
    search_ml_path = os.path.join("chat_search", "search_ml.py")
    if not os.path.exists(search_ml_path):
        print(f"File not found: {search_ml_path}")
        return False
    
    # Read the current file
    with open(search_ml_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if we need to update the file
    if "oneapi_path" in content:
        print("File already updated.")
        return True
    
    # Add improved Intel optimization detection
    improved_detection = """
# Check for Intel oneAPI
def check_oneapi_environment():
    \"\"\"
    Check for Intel oneAPI environment and set it up if available.
    
    Returns:
    - dict with oneAPI information
    \"\"\"
    oneapi_info = {
        "available": False,
        "path": None,
        "components": {}
    }
    
    # Check common oneAPI installation paths
    oneapi_paths = []
    
    if platform.system() == "Windows":
        oneapi_paths = [
            r"C:\\Program Files (x86)\\Intel\\oneAPI",
            r"C:\\Program Files\\Intel\\oneAPI"
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
            oneapi_info["available"] = True
            oneapi_info["path"] = path
            
            # Check for common components
            components = ["mkl", "ipp", "tbb", "compiler", "pytorch"]
            for component in components:
                component_path = os.path.join(path, component)
                if os.path.exists(component_path):
                    oneapi_info["components"][component] = {
                        "available": True,
                        "path": component_path
                    }
            
            break
    
    return oneapi_info

# Check for oneAPI
ONEAPI_INFO = check_oneapi_environment()

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
"""
    
    # Replace the existing import section
    import_section = "# Import ML dependencies if available\nif ML_AVAILABLE:\n    try:"
    if import_section in content:
        # Split the content at the import section
        parts = content.split(import_section)
        
        # Replace with our improved detection
        new_content = parts[0] + improved_detection + parts[1].split("        # Try to use Intel optimized scikit-learn if available", 1)[1]
        
        # Write the updated content
        with open(search_ml_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        print("✓ Updated search_ml.py with improved Intel optimization detection")
        return True
    else:
        print("Could not find the import section in search_ml.py")
        return False

def create_oneapi_setup_script():
    """Create a script to set up the oneAPI environment"""
    print("\n" + "=" * 50)
    print("Creating oneAPI Setup Script")
    print("=" * 50)
    
    # Check if oneAPI is installed
    oneapi_path = None
    if platform.system() == "Windows":
        possible_paths = [
            r"C:\Program Files (x86)\Intel\oneAPI",
            r"C:\Program Files\Intel\oneAPI"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                oneapi_path = path
                break
    
    if not oneapi_path:
        print("oneAPI not found on the system.")
        return False
    
    # Create a batch file to set up oneAPI environment
    batch_file = "run_with_intel_optimizations.bat"
    with open(batch_file, "w") as f:
        f.write(f'@echo off\n')
        f.write(f'echo Setting up Intel oneAPI environment...\n')
        f.write(f'call "{oneapi_path}\\setvars.bat" > nul\n')
        f.write(f'echo Intel oneAPI environment set up successfully.\n')
        f.write(f'echo.\n')
        f.write(f'echo Running WhatsApp Unified Tool with Intel optimizations...\n')
        f.write(f'echo.\n')
        f.write(f'python %*\n')
    
    print(f"✓ Created oneAPI setup script: {batch_file}")
    print(f"To run your Python scripts with Intel optimizations, use:")
    print(f"  {batch_file} whatsapp_unified_tool.py [arguments]")
    
    return True

def main():
    """Main function to enable missing Intel optimizations"""
    print("=" * 50)
    print("Enable Missing Intel Optimizations")
    print("=" * 50)
    print("\nThis script will enable the missing Intel optimizations detected by check_intel_hardware.py.")
    
    # Confirm installation
    print("\nThis script will install/configure the following:")
    print("1. Intel Extension for PyTorch (IPEX)")
    print("2. MKL integration with NumPy")
    print("3. Update search_ml.py for better Intel optimization handling")
    print("4. Create a script to run Python with Intel optimizations")
    
    proceed = input("\nDo you want to proceed? (y/n): ")
    if proceed.lower() != 'y':
        print("Operation cancelled.")
        return
    
    # Install IPEX
    ipex_success = install_ipex()
    
    # Enable MKL for NumPy
    mkl_success = enable_mkl_for_numpy()
    
    # Update search_ml.py
    update_success = update_search_ml_file()
    
    # Create oneAPI setup script
    setup_success = create_oneapi_setup_script()
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    
    print(f"Intel Extension for PyTorch (IPEX): {'Installed' if ipex_success else 'Failed'}")
    print(f"MKL integration with NumPy: {'Enabled' if mkl_success else 'Failed'}")
    print(f"search_ml.py update: {'Updated' if update_success else 'Failed'}")
    print(f"oneAPI setup script: {'Created' if setup_success else 'Failed'}")
    
    # Provide additional instructions
    print("\nTo run the WhatsApp Unified Tool with all Intel optimizations:")
    if setup_success:
        print("1. Use the run_with_intel_optimizations.bat script:")
        print("   run_with_intel_optimizations.bat whatsapp_unified_tool.py --interactive")
    else:
        print("1. Set up the oneAPI environment first:")
        print("   call \"C:\\Program Files (x86)\\Intel\\oneAPI\\setvars.bat\"")
        print("2. Then run your Python script:")
        print("   python whatsapp_unified_tool.py --interactive")
    
    print("\nTo verify the optimizations, run:")
    print("python check_intel_hardware.py")

if __name__ == "__main__":
    main()
