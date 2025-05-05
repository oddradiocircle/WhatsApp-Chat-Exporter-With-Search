#!/usr/bin/env python3
"""
Google Contacts CSV Parser for WhatsApp Chat Exporter

This module provides functionality to parse Google Contacts CSV exports
and integrate them with the WhatsApp Chat Exporter contact system.
"""

import csv
import os
import re
from typing import Dict, List, Any, Tuple, Optional


def normalize_phone_number(phone: str) -> str:
    """
    Normalize a phone number by removing all non-digit characters
    and ensuring it has the correct format for comparison.

    Args:
        phone: The phone number to normalize

    Returns:
        Normalized phone number (digits only)
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters
    clean_phone = ''.join(c for c in phone if c.isdigit())
    
    return clean_phone


def parse_google_contacts_csv(file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse a Google Contacts CSV export file and extract contact information.

    Args:
        file_path: Path to the Google Contacts CSV file

    Returns:
        Dictionary mapping normalized phone numbers to contact information
    """
    if not os.path.exists(file_path):
        print(f"Google Contacts CSV file not found: {file_path}")
        return {}

    contacts_by_phone = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Extract name components
                first_name = row.get('First Name', '').strip()
                last_name = row.get('Last Name', '').strip()
                middle_name = row.get('Middle Name', '').strip()
                name_prefix = row.get('Name Prefix', '').strip()
                name_suffix = row.get('Name Suffix', '').strip()
                
                # Construct full name
                name_parts = []
                if name_prefix:
                    name_parts.append(name_prefix)
                if first_name:
                    name_parts.append(first_name)
                if middle_name:
                    name_parts.append(middle_name)
                if last_name:
                    name_parts.append(last_name)
                if name_suffix:
                    name_parts.append(name_suffix)
                
                full_name = ' '.join(name_parts).strip()
                
                # If no name components, try using "File As" field
                if not full_name:
                    full_name = row.get('File As', '').strip()
                
                # Skip if we still don't have a name
                if not full_name:
                    continue
                
                # Extract phone numbers (Google Contacts CSV has multiple phone fields)
                phone_fields = [
                    'Phone 1 - Value', 'Phone 2 - Value', 'Phone 3 - Value', 'Phone 4 - Value'
                ]
                
                for phone_field in phone_fields:
                    phone = row.get(phone_field, '').strip()
                    if not phone:
                        continue
                    
                    # Handle multiple phone numbers separated by ' ::: '
                    if ' ::: ' in phone:
                        phone_numbers = phone.split(' ::: ')
                    else:
                        phone_numbers = [phone]
                    
                    for phone_number in phone_numbers:
                        # Normalize phone number
                        normalized_phone = normalize_phone_number(phone_number)
                        if not normalized_phone:
                            continue
                        
                        # Create contact info dictionary
                        contact_info = {
                            'name': full_name,
                            'display_name': full_name,
                            'phone': phone_number,
                            'phone_raw': normalized_phone,
                            'source': 'google_contacts'
                        }
                        
                        # Add to contacts dictionary
                        contacts_by_phone[normalized_phone] = contact_info
                
                # Extract email addresses for additional identification
                email_fields = [
                    'E-mail 1 - Value', 'E-mail 2 - Value', 'E-mail 3 - Value', 'E-mail 4 - Value'
                ]
                
                for email_field in email_fields:
                    email = row.get(email_field, '').strip()
                    if not email:
                        continue
                    
                    # Create a special entry for email-based identification
                    # This can be used for matching in some cases
                    email_key = f"email:{email}"
                    contact_info = {
                        'name': full_name,
                        'display_name': full_name,
                        'email': email,
                        'source': 'google_contacts_email'
                    }
                    
                    # Add to contacts dictionary with special key
                    contacts_by_phone[email_key] = contact_info
        
        print(f"Successfully parsed {len(contacts_by_phone)} contacts from Google Contacts CSV")
        return contacts_by_phone
    
    except Exception as e:
        print(f"Error parsing Google Contacts CSV file: {e}")
        return {}


def merge_contacts(existing_contacts: Dict[str, Dict[str, Any]], 
                  google_contacts: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Merge Google Contacts data with existing contacts data.
    
    Args:
        existing_contacts: Existing contacts dictionary
        google_contacts: Google Contacts dictionary
        
    Returns:
        Merged contacts dictionary
    """
    merged_contacts = existing_contacts.copy()
    
    # Add new contacts from Google Contacts
    for phone, contact_info in google_contacts.items():
        if phone not in merged_contacts:
            merged_contacts[phone] = contact_info
        else:
            # If contact already exists, update with Google Contacts info if it's more complete
            existing_contact = merged_contacts[phone]
            
            # Prefer Google Contacts name if existing name is missing or generic
            if (not existing_contact.get('display_name') or 
                existing_contact.get('display_name') == phone or
                existing_contact.get('display_name') == "Desconocido"):
                existing_contact['display_name'] = contact_info['display_name']
                existing_contact['name'] = contact_info['name']
            
            # Add source information
            existing_contact['source'] = f"{existing_contact.get('source', 'unknown')},google_contacts"
    
    return merged_contacts


def find_matching_contact(phone: str, contacts: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Find a matching contact for a given phone number using various matching strategies.
    
    Args:
        phone: Phone number to match
        contacts: Contacts dictionary
        
    Returns:
        Matching contact info or None if no match found
    """
    if not phone:
        return None
    
    # Direct match
    if phone in contacts:
        return contacts[phone]
    
    # Clean phone number for comparison
    clean_phone = normalize_phone_number(phone)
    if not clean_phone:
        return None
    
    # Try direct match with cleaned number
    if clean_phone in contacts:
        return contacts[clean_phone]
    
    # Try suffix matching (last N digits)
    for length in [8, 9, 10]:
        if len(clean_phone) >= length:
            suffix = clean_phone[-length:]
            
            for contact_phone, contact_info in contacts.items():
                if isinstance(contact_phone, str) and contact_phone.endswith(suffix):
                    return contact_info
    
    # No match found
    return None


if __name__ == "__main__":
    # Simple test function
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python google_contacts.py <path_to_google_contacts.csv>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    contacts = parse_google_contacts_csv(csv_file)
    
    print(f"Parsed {len(contacts)} contacts from {csv_file}")
    
    # Print first 5 contacts as a sample
    print("\nSample contacts:")
    for i, (phone, contact) in enumerate(list(contacts.items())[:5]):
        print(f"Contact {i+1}:")
        print(f"  Phone: {phone}")
        print(f"  Name: {contact['name']}")
        print(f"  Display Name: {contact['display_name']}")
        print(f"  Formatted Phone: {contact.get('phone', 'N/A')}")
        print()
