#!/usr/bin/env python3
import sys
import os
import re
from pathlib import Path
from datetime import datetime
from html import unescape
import xml.etree.ElementTree as ET

def parse_blogger_date(date_str):
    """Parse Blogger date formats to YYYY-MM-DD"""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d')
    except:
        return date_str[:10] if date_str else "unknown"

def clean_html_content(html_text):
    """Convert HTML entities + tags to plain text with proper line breaks"""
    if not html_text:
        return ""
    
    # Step 1: Unescape HTML entities FIRST
    text = unescape(str(html_text))
    
    # Step 2: Convert HTML tags to line breaks
    # <br/>, <br>, <p> → newlines
    text = re.sub(r'<br\s*/?>|<br>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p[^>]*>', '\n\n', text, flags=re.IGNORECASE)
    
    # Step 3: Remove ALL other HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Step 4: NEW - Remove space before Chinese full-stop "。"
    text = re.sub(r'\s+([。？！])', r'\1', text)
    
    # Step 5: Clean up excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines → double
    text = re.sub(r' {2,}', ' ', text)  # Multiple spaces → single
    
    # Step 6: Remove Blogger metadata
    text = re.sub(r'Tags:\s*[^。？！\n\r]*[。？！\n\r]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Location:\s*[^。？！\n\r]*[。？！\n\r]*', '', text, flags=re.IGNORECASE)
    
    return text.strip()

def safe_text(element):
    """Safely get text from XML element"""
    return element.text.strip() if element is not None and element.text else ""

def safe_attr(element, attr_name):
    """Safely get attribute from XML element"""
    if element is not None and attr_name in element.attrib:
        return element.attrib[attr_name]
    return None

def main():
    if len(sys.argv) != 3:
        print("Usage: python blogger_to_txt.py <blogger_atom_file> <output_dir_name>")
        sys.exit(1)

    atom_file = Path(sys.argv[1])
    out_dir_name = sys.argv[2]
    
    if not atom_file.exists():
        print(f"❌ Atom file not found: {atom_file}")
        sys.exit(1)

    out_dir = Path.cwd() / out_dir_name
    out_dir.mkdir(parents=True, exist_ok=True)

    # Parse XML
    try:
        tree = ET.parse(atom_file)
        root = tree.getroot()
    except Exception as e:
        print(f"❌ Error parsing XML: {e}")
        sys.exit(1)

    # Namespace handling
    namespaces = {
        'atom': 'http://www.w3.org/2005/Atom',
        'blogger': 'http://www.blogger.com/atom/ns#'
    }

    # Group entries by date
    entries_by_date = {}

    for entry in root.findall('.//atom:entry', namespaces):
        # Get date
        published = entry.find('atom:published', namespaces)
        created = entry.find('blogger:created', namespaces)
        
        date_elem = published if published is not None else created
        if date_elem is None or not date_elem.text:
            continue
            
        date_str = safe_text(date_elem)
        date_key = parse_blogger_date(date_str)
        
        # Get title
        title_elem = entry.find('atom:title', namespaces)
        title = safe_text(title_elem) if title_elem is not None else "No title"
        
        # Get content
        content_elem = entry.find('atom:content', namespaces)
        content_text = ""
        
        if content_elem is not None:
            content_type = safe_attr(content_elem, 'type')
            if content_type == 'html' or content_type == 'text':
                content_text = content_elem.text or ""
        
        # Clean and process content
        content = clean_html_content(content_text)
        
        # Combine title + content
        full_text = f"{title}\n{content}".strip()
        if full_text.strip():
            entries_by_date.setdefault(date_key, []).append(full_text)

    # Write files
    files_written = 0
    total_entries = 0
    
    for date_key, day_entries in sorted(entries_by_date.items()):
        file_name = f"{date_key}-blogger.txt"
        out_path = out_dir / file_name

        with out_path.open("w", encoding="utf-8") as out_f:
            out_f.write(date_key + "\n")
            
            for i, entry_text in enumerate(day_entries, 1):
                if entry_text.strip():
                    out_f.write(entry_text)
                    total_entries += 1
                    if i < len(day_entries):
                        out_f.write("\n\n")
        
        files_written += 1

    print(f"✅ Done. Wrote {files_written} files to {out_dir}")
    print(f"📅 Processed {len(entries_by_date)} unique dates")
    print(f"📄 Total entries: {total_entries}")

if __name__ == "__main__":
    main()
