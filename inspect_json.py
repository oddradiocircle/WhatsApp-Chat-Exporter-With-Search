#!/usr/bin/env python3
"""
Script to inspect the structure of the WhatsApp result.json file
"""

import json
import sys
import os

def main():
    # Check if file exists
    file_path = "whatsapp_export/result.json"
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return 1
    
    # Get file size
    file_size = os.path.getsize(file_path)
    print(f"File size: {file_size / (1024*1024):.2f} MB")
    
    # Try to load the first few bytes to check if it's valid JSON
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read first 1000 characters
            start = f.read(1000)
            print(f"First 1000 characters: {start}")
            
            # Reset file pointer
            f.seek(0)
            
            # Try to parse as JSON
            print("Attempting to parse JSON...")
            data = json.load(f)
            
            # Print basic info
            print(f"Successfully parsed JSON with {len(data)} top-level keys")
            
            # Print first few keys
            print("First 5 keys:")
            for i, key in enumerate(list(data.keys())[:5]):
                print(f"  {i+1}. {key}")
            
            # Print structure of first chat
            if data:
                first_key = list(data.keys())[0]
                first_chat = data[first_key]
                print(f"\nStructure of first chat ({first_key}):")
                
                # Print top-level keys
                print("  Top-level keys:")
                for key in first_chat.keys():
                    print(f"    - {key}")
                
                # Print contact info if available
                if 'contact' in first_chat:
                    print("\n  Contact info:")
                    for key, value in first_chat['contact'].items():
                        print(f"    - {key}: {value}")
                
                # Print first message if available
                if 'messages' in first_chat and first_chat['messages']:
                    first_msg_key = list(first_chat['messages'].keys())[0]
                    first_msg = first_chat['messages'][first_msg_key]
                    print("\n  First message structure:")
                    for key, value in first_msg.items():
                        print(f"    - {key}: {value}")
            
            return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
