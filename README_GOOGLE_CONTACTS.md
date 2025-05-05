# Google Contacts Integration for WhatsApp Unified Tool

This document explains how to use Google Contacts CSV exports with the WhatsApp Unified Tool to improve contact resolution and display.

## Overview

The WhatsApp Unified Tool now supports importing contact information from Google Contacts CSV exports. This feature helps to:

1. Resolve phone numbers to contact names more accurately
2. Display proper contact names instead of phone numbers in search results
3. Improve contact relevance analysis with better contact information

## Exporting Google Contacts

To use this feature, you first need to export your contacts from Google Contacts:

1. Go to [Google Contacts](https://contacts.google.com/)
2. Select the contacts you want to export (or select all)
3. Click on "Export" from the left menu
4. Choose "Google CSV" as the export format
5. Click "Export" to download the CSV file
6. Save the file to your computer

## Using Google Contacts with the WhatsApp Unified Tool

### Command Line Mode

To use Google Contacts in command line mode, use the `--google-contacts` or `-g` parameter:

```bash
python whatsapp_unified_tool.py --file whatsapp_export/result.json --google-contacts path/to/google-contacts.csv --interactive
```

Or for a specific search:

```bash
python whatsapp_unified_tool.py --file whatsapp_export/result.json --google-contacts path/to/google-contacts.csv --mode search --keywords "keyword1,keyword2"
```

### Interactive Mode

In interactive mode, you can load Google Contacts using option 14 "Manage Google Contacts":

1. Select option 14 from the main menu
2. Choose option 1 "Load Google Contacts CSV file"
3. Enter the path to your Google Contacts CSV file
4. The contacts will be loaded and merged with existing WhatsApp contacts

You can view the loaded Google Contacts by selecting option 2 "Show loaded Google Contacts".

## How It Works

The Google Contacts integration:

1. Parses the Google Contacts CSV file to extract names and phone numbers
2. Normalizes phone numbers for better matching
3. Merges the Google Contacts data with existing WhatsApp contacts
4. Uses the combined contact information when displaying search results

## Phone Number Matching

The system uses several strategies to match phone numbers:

1. Direct matching of full phone numbers
2. Matching based on the last 8-10 digits (to handle country code differences)
3. Normalization of phone number formats

## Troubleshooting

If you encounter issues with Google Contacts integration:

- Make sure you've exported contacts in "Google CSV" format (not vCard or Outlook CSV)
- Check that the CSV file contains phone numbers in the "Phone X - Value" columns
- Verify that the file path is correct when loading the file
- If contacts aren't matching, check the phone number formats in both WhatsApp and Google Contacts

## Example

When searching for messages, instead of seeing:

```
From: +573001234567
```

You might now see:

```
From: John Doe (+573001234567)
```

This makes it much easier to identify who sent each message.
