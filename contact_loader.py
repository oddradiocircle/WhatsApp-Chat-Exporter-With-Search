#!/usr/bin/env python3
"""
Contact Loader for WhatsApp Chat Search

This script loads contact information from VCF files and creates a dictionary
that maps phone numbers to contact names.
"""

import os
import re
import json

def parse_vcf_file(file_path):
    """
    Parse a VCF file and extract contact information.

    Parameters:
    - file_path: Path to the VCF file

    Returns:
    - contact_info: Dictionary with contact information
    """
    contact_info = {
        'name': None,
        'display_name': None,
        'phone': None,
        'phone_raw': None
    }

    try:
        # Use filename as primary source for display name
        base_name = os.path.basename(file_path)
        name_without_ext = os.path.splitext(base_name)[0]
        contact_info['display_name'] = name_without_ext

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # Process line by line
        for line in lines:
            line = line.strip()

            # Extract display name
            if line.startswith('FN:'):
                contact_info['display_name'] = line[3:].strip()

            # Extract phone number
            elif line.startswith('TEL;'):
                # Extract raw phone number (waid)
                waid_match = re.search(r'waid=([0-9]*)', line)
                if waid_match:
                    contact_info['phone_raw'] = waid_match.group(1).strip()

                # Extract formatted phone
                phone_match = re.search(r':([^\r\n]*)', line)
                if phone_match:
                    contact_info['phone'] = phone_match.group(1).strip()

            # Extract name components
            elif line.startswith('N:'):
                parts = line[2:].split(';')
                if len(parts) >= 2:
                    last_name = parts[0].strip()
                    first_name = parts[1].strip()
                    if first_name and last_name:
                        contact_info['name'] = f"{first_name} {last_name}"
                    elif first_name:
                        contact_info['name'] = first_name
                    elif last_name:
                        contact_info['name'] = last_name

        # If no name was extracted, use display name
        if not contact_info['name']:
            contact_info['name'] = contact_info['display_name']

    except Exception as e:
        print(f"Error parsing VCF file {file_path}: {e}")

    return contact_info

def load_contacts(vcards_dir):
    """
    Load all contacts from VCF files in the specified directory.

    Parameters:
    - vcards_dir: Directory containing VCF files

    Returns:
    - contacts_by_phone: Dictionary mapping phone numbers to contact information
    """
    contacts_by_phone = {}

    if not os.path.exists(vcards_dir):
        print(f"Directory not found: {vcards_dir}")
        return contacts_by_phone

    # Get all VCF files in the directory
    vcf_files = [os.path.join(vcards_dir, f) for f in os.listdir(vcards_dir) if f.endswith('.vcf')]

    print(f"Found {len(vcf_files)} VCF files in {vcards_dir}")

    # Parse each VCF file
    for vcf_file in vcf_files:
        contact_info = parse_vcf_file(vcf_file)

        # Add to dictionary if we have a phone number
        if contact_info['phone_raw']:
            contacts_by_phone[contact_info['phone_raw']] = contact_info

    return contacts_by_phone

def save_contacts_to_json(contacts, output_file):
    """
    Save contacts dictionary to a JSON file.

    Parameters:
    - contacts: Dictionary of contacts
    - output_file: Path to the output JSON file
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(contacts, f, ensure_ascii=False, indent=2)
        print(f"Contacts saved to {output_file}")
    except Exception as e:
        print(f"Error saving contacts to {output_file}: {e}")

def main():
    # Paths to vCards directories
    vcards_dirs = [
        "whatsapp_export/WhatsApp/vCards",
        "whatsapp_export/result/WhatsApp/vCards"
    ]

    # Dictionary to store all contacts
    all_contacts = {}

    # Load contacts from each directory
    for vcards_dir in vcards_dirs:
        if os.path.exists(vcards_dir):
            contacts = load_contacts(vcards_dir)
            print(f"Loaded {len(contacts)} contacts from {vcards_dir}")
            all_contacts.update(contacts)

    print(f"Total contacts loaded: {len(all_contacts)}")

    # Save contacts to JSON file
    save_contacts_to_json(all_contacts, "whatsapp_contacts.json")

    # Print some sample contacts
    print("\nSample contacts:")
    for i, (phone, contact) in enumerate(list(all_contacts.items())[:5]):
        print(f"Contact {i+1}:")
        print(f"  Phone: {phone}")
        print(f"  Name: {contact['name']}")
        print(f"  Display Name: {contact['display_name']}")
        print(f"  Formatted Phone: {contact['phone']}")
        print()

if __name__ == "__main__":
    main()
