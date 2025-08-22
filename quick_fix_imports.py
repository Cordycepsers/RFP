#!/usr/bin/env python3
"""
Quick fix for import issues in scrapers
"""

import os
import re

def fix_scraper_imports(file_path):
    """Fix imports in a scraper file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if typing imports are missing
    if 'from typing import' not in content and 'Dict[str, Any]' in content:
        # Add typing imports after the first import line
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                lines.insert(i + 1, 'from typing import List, Dict, Optional, Any')
                break
        content = '\n'.join(lines)
    
    # Remove duplicate typing imports
    lines = content.split('\n')
    typing_import_count = 0
    new_lines = []
    
    for line in lines:
        if 'from typing import' in line:
            typing_import_count += 1
            if typing_import_count == 1:
                new_lines.append('from typing import List, Dict, Optional, Any')
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    with open(file_path, 'w') as f:
        f.write(content)

def main():
    scrapers_dir = '/home/ubuntu/proposaland/src/scrapers'
    
    for filename in os.listdir(scrapers_dir):
        if filename.endswith('_scraper.py'):
            file_path = os.path.join(scrapers_dir, filename)
            print(f"Fixing imports in {filename}")
            fix_scraper_imports(file_path)
    
    print("Import fixes completed!")

if __name__ == "__main__":
    main()

