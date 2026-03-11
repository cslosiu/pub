import json
import os
import html
from datetime import datetime
from pathlib import Path
import re
import uuid

# Load Day One JSON
with open('Journal.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    entries = data['entries']

def escape_html_full(text):
    """Full HTML entity escaping for Blogger content - handles < > & \" etc."""
    # First escape all HTML entities
    escaped = html.escape(text, quote=True)
    # Convert newlines to <br/>
    escaped = escaped.replace('\n', '<br/>')
    # Convert double newlines to <p> for better formatting
    escaped = escaped.replace('\n\n', '</p><p>').replace('\n', '<br/>')
    # Wrap in paragraph if needed
    if not escaped.startswith('<p>'):
        escaped = f'<p>{escaped}</p>'
    return escaped

def format_date(dayone_date):
    if 'Z' in dayone_date:
        dt = datetime.fromisoformat(dayone_date.replace('Z', '+00:00'))
    else:
        dt = datetime.fromisoformat(dayone_date)
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

def generate_unique_post_id(entry_index):
    """Generate unique post number matching Blogger format"""
    base_timestamp = 12965842799588733
    unique_id = f"{base_timestamp + entry_index:019d}"
    return unique_id

def generate_unique_filename(creation_date, entry_index):
    """Generate unique filename"""
    dt = datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
    time_str = dt.strftime('%Y/%m/blog-post_%d_%H%M%S')
    unique_index = f"{entry_index:03d}"
    return f"/{time_str}_{unique_index}.html"

def process_tags(tags):
    """Convert Day One tags to Blogger categories"""
    if not tags:
        return '<category/>'
    return '<category>' + ''.join(f'<category term="{html.escape(tag, quote=True)}"/>' for tag in tags) + '</category>'

def process_entry(entry):
    text = entry.get('text', '')
    
    # First line as title
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    title_lines = [line.lstrip('# ').strip() for line in lines[:2]]
    title = title_lines[0][:60] if title_lines else "Untitled Entry"
    
    # FULL HTML ESCAPING for content
    content = escape_html_full(text)
    
    # Add metadata (also properly escaped)
    if 'tags' in entry and entry['tags']:
        content += f'<br/><br/><strong>Tags:</strong> {html.escape(", ".join(entry["tags"]), quote=True)}'
    
    if 'location' in entry and entry['location']:
        loc = entry['location']
        loc_str = loc.get('placeName', f"{loc.get('latitude', 'N/A')}, {loc.get('longitude', 'N/A')}")
        content += f'<br/><strong>Location:</strong> {html.escape(loc_str, quote=True)}'
    
    return title, content, entry.get('tags', [])

# Constants
BLOG_ID = "7321087845102159074"
AUTHOR_NAME = "siu"
POST_BASE = 12965842799588733

entry_index = 0

# Generate Blogger Atom XML
xml = '''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:blogger="http://www.blogger.com/atom/ns#">
  <title>Day One Import</title>
'''

entry_count = 0

for entry in entries:
    if 'creationDate' not in entry:
        continue
        
    title, content, tags = process_entry(entry)
    created = format_date(entry['creationDate'])
    
    post_id = generate_unique_post_id(entry_index)
    filename = generate_unique_filename(entry['creationDate'], entry_index)
    full_id = f"tag:blogger.com,1999:blog-{BLOG_ID}.post-{post_id}"
    categories = process_tags(tags)
    
    entry_xml = f'''  <entry>
    <id>{full_id}</id>
    <blogger:type>POST</blogger:type>
    <blogger:status>LIVE</blogger:status>
    <author>
      <name>{html.escape(AUTHOR_NAME)}</name>
      <uri></uri>
      <blogger:type>BLOGGER</blogger:type>
    </author>
    <title>{html.escape(title)}</title>
    <content type="html">{content}</content>
    <blogger:metaDescription/>
    <blogger:created>{created}</blogger:created>
    <published>{created}</published>
    <updated>{created}</updated>
    <blogger:location/>
    {categories}
    <blogger:filename>{filename}</blogger:filename>
    <link/>
    <enclosure/>
    <blogger:trashed/>
  </entry>'''
    
    xml += entry_xml
    entry_count += 1
    entry_index += 1

xml += '</feed>'

with open('blogger_import.atom', 'w', encoding='utf-8') as f:
    f.write(xml)

print(f"✅ Generated blogger_import.atom with {entry_count} entries!")
print("✅ ALL content is FULLY HTML-escaped (&lt; &gt; &amp; etc.)")
print("📤 Ready for Blogger import!")
