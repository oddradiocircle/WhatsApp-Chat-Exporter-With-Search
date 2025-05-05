#!/usr/bin/env python3
"""
Intel Hardware Detection Script

This script checks for Intel hardware and available optimizations,
providing detailed information about the system configuration.
"""

import os
import sys
import platform
import subprocess
import importlib.util
from pprint import pprint

def check_module_exists(module_name):
    """Check if a Python module is installed"""
    return importlib.util.find_spec(module_name) is not None

def get_cpu_info():
    """Get detailed CPU information"""
    cpu_info = {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "architecture": platform.architecture(),
        "python_version": platform.python_version(),
        "system": platform.system(),
        "machine": platform.machine(),
    }
    
    # Try to get more detailed CPU info on Windows
    if platform.system() == "Windows":
        try:
            # Use Windows Management Instrumentation (WMI) to get CPU info
            import wmi
            w = wmi.WMI()
            for processor in w.Win32_Processor():
                cpu_info["name"] = processor.Name
                cpu_info["manufacturer"] = processor.Manufacturer
                cpu_info["cores"] = processor.NumberOfCores
                cpu_info["threads"] = processor.NumberOfLogicalProcessors
                cpu_info["max_clock_speed"] = f"{processor.MaxClockSpeed} MHz"
                break
        except ImportError:
            # If WMI is not available, try using subprocess
            try:
                result = subprocess.run(
                    ["wmic", "cpu", "get", "name,manufacturer,numberofcores,numberoflogicalprocessors,maxclockspeed"],
                    capture_output=True, text=True, check=True
                )
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    headers = lines[0].split()
                    values = lines[1].split()
                    for i, header in enumerate(headers):
                        if i < len(values):
                            cpu_info[header.lower()] = values[i]
            except Exception as e:
                cpu_info["wmic_error"] = str(e)
    
    return cpu_info

def get_gpu_info():
    """Get detailed GPU information"""
    gpu_info = {"detected": False, "intel_gpu": False, "details": {}}
    
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
                    content = f.read()
                    
                # Extract GPU information
                gpu_info["detected"] = True
                
                # Check for Intel GPU
                if "intel" in content.lower() and any(gpu in content.lower() for gpu in ["iris", "uhd", "hd graphics"]):
                    gpu_info["intel_gpu"] = True
                    
                    # Extract more details
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if "Display Devices" in line or "Display Device" in line:
                            # Extract the next few lines which should contain GPU details
                            for j in range(i+1, min(i+20, len(lines))):
                                if ":" in lines[j]:
                                    key, value = lines[j].split(":", 1)
                                    gpu_info["details"][key.strip()] = value.strip()
                
                # Clean up
                os.remove(temp_file)
        except Exception as e:
            gpu_info["error"] = str(e)
    
    # Try using PyTorch to detect GPUs
    try:
        if check_module_exists("torch"):
            import torch
            gpu_info["torch_available"] = True
            gpu_info["cuda_available"] = torch.cuda.is_available()
            
            if torch.cuda.is_available():
                gpu_info["cuda_device_count"] = torch.cuda.device_count()
                gpu_info["cuda_devices"] = []
                
                for i in range(torch.cuda.device_count()):
                    device_name = torch.cuda.get_device_name(i)
                    gpu_info["cuda_devices"].append({
                        "index": i,
                        "name": device_name,
                        "is_intel": "intel" in device_name.lower()
                    })
    except Exception as e:
        gpu_info["torch_error"] = str(e)
    
    return gpu_info

def check_intel_optimizations():
    """Check for Intel optimizations"""
    optimizations = {
        "scikit-learn-intelex": {
            "installed": check_module_exists("sklearnex"),
            "version": None,
            "patched": False
        },
        "intel-extension-for-pytorch": {
            "installed": check_module_exists("intel_extension_for_pytorch"),
            "version": None
        },
        "mkl": {
            "installed": False,
            "details": {}
        },
        "numpy": {
            "installed": check_module_exists("numpy"),
            "version": None,
            "using_mkl": False
        },
        "scipy": {
            "installed": check_module_exists("scipy"),
            "version": None
        },
        "pytorch": {
            "installed": check_module_exists("torch"),
            "version": None
        }
    }
    
    # Get versions and additional details
    if optimizations["scikit-learn-intelex"]["installed"]:
        try:
            import sklearnex
            optimizations["scikit-learn-intelex"]["version"] = getattr(sklearnex, "__version__", "Unknown")
            
            # Check if patching works
            try:
                sklearnex.patch_sklearn()
                optimizations["scikit-learn-intelex"]["patched"] = True
            except Exception as e:
                optimizations["scikit-learn-intelex"]["patch_error"] = str(e)
        except Exception as e:
            optimizations["scikit-learn-intelex"]["error"] = str(e)
    
    if optimizations["intel-extension-for-pytorch"]["installed"]:
        try:
            import intel_extension_for_pytorch as ipex
            optimizations["intel-extension-for-pytorch"]["version"] = getattr(ipex, "__version__", "Unknown")
        except Exception as e:
            optimizations["intel-extension-for-pytorch"]["error"] = str(e)
    
    if optimizations["numpy"]["installed"]:
        try:
            import numpy as np
            optimizations["numpy"]["version"] = np.__version__
            
            # Check if NumPy is using MKL
            np_config = np.__config__
            if hasattr(np_config, "show") and callable(np_config.show):
                config_info = np_config.show()
                if isinstance(config_info, str):
                    optimizations["numpy"]["config"] = config_info
                    if "mkl" in config_info.lower():
                        optimizations["numpy"]["using_mkl"] = True
                        optimizations["mkl"]["installed"] = True
                        
                        # Extract MKL details
                        for line in config_info.split('\n'):
                            if "mkl" in line.lower():
                                parts = line.split(":")
                                if len(parts) >= 2:
                                    key = parts[0].strip()
                                    value = parts[1].strip()
                                    optimizations["mkl"]["details"][key] = value
        except Exception as e:
            optimizations["numpy"]["error"] = str(e)
    
    if optimizations["scipy"]["installed"]:
        try:
            import scipy
            optimizations["scipy"]["version"] = scipy.__version__
        except Exception as e:
            optimizations["scipy"]["error"] = str(e)
    
    if optimizations["pytorch"]["installed"]:
        try:
            import torch
            optimizations["pytorch"]["version"] = torch.__version__
            optimizations["pytorch"]["cuda_available"] = torch.cuda.is_available()
            
            # Check for XPU support (Intel GPU)
            try:
                has_xpu = hasattr(torch, "xpu") and callable(getattr(torch.xpu, "is_available", None))
                optimizations["pytorch"]["has_xpu_support"] = has_xpu
                if has_xpu:
                    optimizations["pytorch"]["xpu_available"] = torch.xpu.is_available()
            except Exception as e:
                optimizations["pytorch"]["xpu_error"] = str(e)
        except Exception as e:
            optimizations["pytorch"]["error"] = str(e)
    
    return optimizations

def check_oneapi_toolkit():
    """Check for Intel oneAPI toolkit installation"""
    oneapi_info = {"installed": False, "components": {}}
    
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
            oneapi_info["installed"] = True
            oneapi_info["path"] = path
            
            # Check for common components
            components = ["mkl", "ipp", "tbb", "dpcpp", "compiler", "pytorch"]
            for component in components:
                component_path = os.path.join(path, component)
                if os.path.exists(component_path):
                    oneapi_info["components"][component] = {"installed": True, "path": component_path}
                    
                    # Check for version information
                    version_files = ["version.txt", "version.cfg", "version"]
                    for vfile in version_files:
                        vpath = os.path.join(component_path, vfile)
                        if os.path.exists(vpath):
                            try:
                                with open(vpath, "r") as f:
                                    oneapi_info["components"][component]["version"] = f.read().strip()
                            except:
                                pass
    
    # Check environment variables
    oneapi_env_vars = [var for var in os.environ if "ONEAPI" in var or "INTEL" in var]
    if oneapi_env_vars:
        oneapi_info["environment_variables"] = {var: os.environ[var] for var in oneapi_env_vars}
    
    return oneapi_info

def main():
    """Main function to display system information"""
    print("=" * 50)
    print("Intel Hardware and Optimization Detection")
    print("=" * 50)
    
    # Check CPU
    print("\nCPU Information:")
    cpu_info = get_cpu_info()
    pprint(cpu_info)
    
    # Check GPU
    print("\nGPU Information:")
    gpu_info = get_gpu_info()
    pprint(gpu_info)
    
    # Check Intel optimizations
    print("\nIntel Optimizations:")
    optimizations = check_intel_optimizations()
    pprint(optimizations)
    
    # Check oneAPI toolkit
    print("\nIntel oneAPI Toolkit:")
    oneapi_info = check_oneapi_toolkit()
    pprint(oneapi_info)
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary:")
    print("=" * 50)
    
    print(f"Intel CPU: {'Yes' if 'intel' in cpu_info.get('processor', '').lower() else 'No'}")
    print(f"Intel GPU: {'Yes' if gpu_info.get('intel_gpu', False) else 'No'}")
    print(f"scikit-learn-intelex: {'Installed' if optimizations['scikit-learn-intelex']['installed'] else 'Not installed'}")
    print(f"Intel Extension for PyTorch: {'Installed' if optimizations['intel-extension-for-pytorch']['installed'] else 'Not installed'}")
    print(f"MKL: {'Installed' if optimizations['mkl']['installed'] else 'Not installed'}")
    print(f"oneAPI Toolkit: {'Installed' if oneapi_info['installed'] else 'Not installed'}")
    
    # Recommendations
    print("\nRecommendations:")
    
    if not optimizations['scikit-learn-intelex']['installed']:
        print("- Install Intel Extension for Scikit-learn: pip install scikit-learn-intelex")
    
    if not optimizations['intel-extension-for-pytorch']['installed']:
        print("- Install Intel Extension for PyTorch: pip install intel-extension-for-pytorch")
    
    if not optimizations['mkl']['installed']:
        print("- Install NumPy with MKL support: pip install numpy --upgrade")
    
    if not oneapi_info['installed']:
        print("- Consider installing Intel oneAPI Base Toolkit for comprehensive optimizations")
        print("  Download from: https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit-download.html")

if __name__ == "__main__":
    main()
