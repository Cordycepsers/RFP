#!/usr/bin/env python3
"""
Final comprehensive fix for all scrapers
Ensures proper imports and data structure consistency
"""

import os
import re

def fix_scraper_file(file_path):
    """Comprehensively fix a scraper file"""
    print(f"Fixing {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove all existing typing imports
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        if 'from typing import' not in line:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # Add proper typing import after the docstring
    lines = content.split('\n')
    docstring_end = 0
    
    # Find end of docstring
    in_docstring = False
    for i, line in enumerate(lines):
        if line.strip().startswith('"""') or line.strip().startswith("'''"):
            if not in_docstring:
                in_docstring = True
            else:
                docstring_end = i + 1
                break
    
    # Insert typing import after docstring
    lines.insert(docstring_end, '')
    lines.insert(docstring_end + 1, 'from typing import List, Dict, Optional, Any')
    
    content = '\n'.join(lines)
    
    # Fix return type annotations
    content = re.sub(r'-> List\[Dict\[str, Any\]\]', '-> List[OpportunityData]', content)
    content = re.sub(r'-> List\[dict\]', '-> List[OpportunityData]', content)
    
    # Ensure OpportunityData is imported
    if 'from .base_scraper import' in content and 'OpportunityData' not in content:
        content = content.replace(
            'from .base_scraper import BaseScraper',
            'from .base_scraper import BaseScraper, OpportunityData'
        )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")

def main():
    """Fix all scrapers"""
    scrapers_dir = '/home/ubuntu/proposaland/src/scrapers'
    
    scrapers_to_fix = [
        'src/scrapers/ungm_scraper.py',
        'src/scrapers/globalfund_scraper.py',
        'src/scrapers/worldbank_scraper.py',
        'src/scrapers/developmentaid_scraper.py',
        'src/scrapers/iucn_scraper.py',
        'src/scrapers/adb_scraper.py'
    ]
    
    for filename in scrapers_to_fix:
        file_path = os.path.join(scrapers_dir, filename)
        if os.path.exists(file_path):
            fix_scraper_file(file_path)
        else:
            print(f"File not found: {file_path}")
    
    print("All scrapers fixed!")

if __name__ == "__main__":
    main()

