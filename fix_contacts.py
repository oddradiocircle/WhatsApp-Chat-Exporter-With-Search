#!/usr/bin/env python3
"""
Script to fix contact display in WhatsApp search results
"""

import json
import os
import sys

def format_phone_number(phone):
    """Format a phone number to make it more readable."""
    if not phone or not isinstance(phone, str):
        return "Unknown"
    
    # If it's already a name (contains letters), return as is
    if any(c.isalpha() for c in phone):
        return phone
    
    # Clean the phone number
    digits = ''.join(c for c in phone if c.isdigit())
    
    # Format based on length
    if len(digits) <= 4:
        return phone  # Too short, return as is
    elif len(digits) <= 7:
        return f"{digits[:3]}-{digits[3:]}"  # Local number
    elif len(digits) <= 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"  # National number
    else:
        # International number
        country_code = digits[:-10]
        area_code = digits[-10:-7]
        prefix = digits[-7:-4]
        line = digits[-4:]
        return f"+{country_code} ({area_code}) {prefix}-{line}"

def main():
    # Check if the original script exists
    original_script = "whatsapp_search.py"
    if not os.path.exists(original_script):
        print(f"Error: Original script not found: {original_script}")
        return 1
    
    # Create a backup of the original script
    backup_script = "whatsapp_search.py.bak"
    if not os.path.exists(backup_script):
        try:
            with open(original_script, 'r', encoding='utf-8') as f_in:
                with open(backup_script, 'w', encoding='utf-8') as f_out:
                    f_out.write(f_in.read())
            print(f"Created backup of original script: {backup_script}")
        except Exception as e:
            print(f"Error creating backup: {e}")
            return 1
    
    # Modify the original script to fix contact display
    try:
        with open(original_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add format_phone_number function if it doesn't exist
        if "def format_phone_number(" not in content:
            # Find a good place to insert the function (after imports)
            insert_pos = content.find("def load_json_data(")
            if insert_pos == -1:
                print("Error: Could not find a good place to insert the function")
                return 1
            
            # Define the function to insert
            format_phone_function = """
def format_phone_number(phone):
    \"\"\"
    Format a phone number to make it more readable.
    
    Parameters:
    - phone: The phone number string
    
    Returns:
    - formatted: A more readable phone number
    \"\"\"
    if not phone or not isinstance(phone, str):
        return "Unknown"
    
    # If it's already a name (contains letters), return as is
    if any(c.isalpha() for c in phone):
        return phone
    
    # Clean the phone number
    digits = ''.join(c for c in phone if c.isdigit())
    
    # Format based on length
    if len(digits) <= 4:
        return phone  # Too short, return as is
    elif len(digits) <= 7:
        return f"{digits[:3]}-{digits[3:]}"  # Local number
    elif len(digits) <= 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"  # National number
    else:
        # International number
        country_code = digits[:-10]
        area_code = digits[-10:-7]
        prefix = digits[-7:-4]
        line = digits[-4:]
        return f"+{country_code} ({area_code}) {prefix}-{line}"

"""
            # Insert the function
            content = content[:insert_pos] + format_phone_function + content[insert_pos:]
        
        # Modify the print_results function to format phone numbers
        if "def print_results(" in content:
            # Find the print_results function
            start_pos = content.find("def print_results(")
            if start_pos == -1:
                print("Error: Could not find the print_results function")
                return 1
            
            # Find the part where it prints the sender
            sender_print_pos = content.find('print(f"Sender: {result', start_pos)
            if sender_print_pos == -1:
                print("Error: Could not find where the sender is printed")
                return 1
            
            # Find the line end
            line_end_pos = content.find('\n', sender_print_pos)
            if line_end_pos == -1:
                print("Error: Could not find the end of the line")
                return 1
            
            # Replace the line with improved sender formatting
            old_line = content[sender_print_pos:line_end_pos]
            new_line = """        # Format sender name
        sender_display = result['sender']
        if sender_display == "Unknown" and isinstance(result['sender'], str) and result['sender'].isdigit():
            sender_display = format_phone_number(result['sender'])
        print(f"Sender: {sender_display}")"""
            
            content = content[:sender_print_pos] + new_line + content[line_end_pos:]
        
        # Write the modified content back to the file
        with open(original_script, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Successfully modified {original_script} to improve contact display")
        print("You can now run the script with:")
        print(f"  python {original_script} --keywords \"your,keywords\" --file whatsapp_export/result.json")
        
        return 0
    except Exception as e:
        print(f"Error modifying script: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
