#!/usr/bin/env python3
"""
Comprehensive Error Fix Script for Proposaland Scrapers
Fixes all identified issues from the error log
"""

import os
import re
import sys
from pathlib import Path

def fix_datetime_import_error():
    """Fix missing datetime import in base_scraper.py"""
    print("🔧 Fixing datetime import error...")
    
    base_scraper_path = Path("src/scrapers/base_scraper.py")
    if base_scraper_path.exists():
        with open(base_scraper_path, 'r') as f:
            content = f.read()
        
        # Check if datetime is imported
        if 'from datetime import datetime' not in content:
            # Add datetime import after other imports
            lines = content.split('\n')
            import_section_end = 0
            
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    import_section_end = i
            
            # Insert datetime import
            lines.insert(import_section_end + 1, 'from datetime import datetime, timedelta')
            content = '\n'.join(lines)
            
            with open(base_scraper_path, 'w') as f:
                f.write(content)
            
            print("    ✓ Fixed datetime import in base_scraper.py")
        else:
            print("    - Datetime import already present")

def fix_backslash_escape_sequences():
    """Fix all backslash escape sequences (\\1\\n) in scrapers"""
    print("🔧 Fixing backslash escape sequences...")
    
    scrapers_dir = Path("src/scrapers")
    fixed_count = 0
    
    for scraper_file in scrapers_dir.glob("*.py"):
        with open(scraper_file, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Remove all backslash escape sequences
        patterns_to_remove = [
            r'\\1\\n',
            r'\\1',
            r'\\2',
            r'\\3',
            r'\\n',
            r'=\\1try:\\n\\1\\s+\\2\\n\\1except \\(AttributeError, TypeError\\):\\n\\1\\s+None',
            r'=\\1try:\\n.*?\\1except.*?None'
        ]
        
        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
        
        # Fix malformed assignments
        content = re.sub(r'(\w+)\s*=\s*try:', r'try:\n        \1 =', content)
        content = re.sub(r'(\w+)\s*=.*?except.*?None', r'\1 = None', content)
        
        if content != original_content:
            with open(scraper_file, 'w') as f:
                f.write(content)
            fixed_count += 1
            print(f"    ✓ Fixed backslash sequences in {scraper_file.name}")
    
    print(f"    Fixed {fixed_count} files")

def fix_indentation_errors():
    """Fix indentation errors in all scrapers"""
    print("🔧 Fixing indentation errors...")
    
    scrapers_dir = Path("src/scrapers")
    fixed_count = 0
    
    for scraper_file in scrapers_dir.glob("*.py"):
        with open(scraper_file, 'r') as f:
            lines = f.readlines()
        
        fixed_lines = []
        in_class = False
        in_method = False
        class_indent = 0
        method_indent = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                fixed_lines.append(line)
                continue
            
            # Detect class definition
            if stripped.startswith('class '):
                in_class = True
                class_indent = len(line) - len(line.lstrip())
                fixed_lines.append(line)
                continue
            
            # Detect method definition
            if stripped.startswith('def ') and in_class:
                in_method = True
                method_indent = class_indent + 4
                # Ensure proper method indentation
                fixed_line = ' ' * method_indent + stripped + '\n'
                fixed_lines.append(fixed_line)
                continue
            
            # Fix indentation for class-level attributes
            if in_class and not in_method and not stripped.startswith(('def ', 'class ', '@')):
                if stripped.startswith('self.'):
                    # This should be in __init__ method, but if it's at class level, fix it
                    fixed_line = ' ' * (class_indent + 8) + stripped + '\n'
                    fixed_lines.append(fixed_line)
                    continue
            
            # Fix method body indentation
            if in_method and not stripped.startswith(('def ', 'class ', '@')):
                expected_indent = method_indent + 4
                fixed_line = ' ' * expected_indent + stripped + '\n'
                fixed_lines.append(fixed_line)
                continue
            
            # Reset flags for new class/method
            if stripped.startswith('class '):
                in_class = True
                in_method = False
                class_indent = len(line) - len(line.lstrip())
            elif stripped.startswith('def ') and in_class:
                in_method = True
                method_indent = class_indent + 4
            
            fixed_lines.append(line)
        
        # Write back if changes were made
        new_content = ''.join(fixed_lines)
        with open(scraper_file, 'r') as f:
            original_content = f.read()
        
        if new_content != original_content:
            with open(scraper_file, 'w') as f:
                f.write(new_content)
            fixed_count += 1
            print(f"    ✓ Fixed indentation in {scraper_file.name}")
    
    print(f"    Fixed indentation in {fixed_count} files")

def fix_syntax_errors():
    """Fix syntax errors in scrapers"""
    print("🔧 Fixing syntax errors...")
    
    scrapers_dir = Path("src/scrapers")
    
    for scraper_file in scrapers_dir.glob("*.py"):
        with open(scraper_file, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix malformed try-except blocks
        content = re.sub(
            r'try:\s*except\s+.*?:',
            'try:\n            pass\n        except Exception:',
            content,
            flags=re.MULTILINE
        )
        
        # Fix incomplete try blocks
        content = re.sub(
            r'try:\s*(\w+)\s*=\s*$',
            r'try:\n            \1 = None',
            content,
            flags=re.MULTILINE
        )
        
        # Fix orphaned except blocks
        content = re.sub(
            r'^\s*except\s+.*?:\s*$',
            '        except Exception:\n            pass',
            content,
            flags=re.MULTILINE
        )
        
        # Fix class-level self references
        content = re.sub(
            r'^(\s*)self\.(\w+)\s*=\s*([^\\n]+)$',
            r'    def __init__(self, *args, **kwargs):\n        super().__init__(*args, **kwargs)\n        self.\2 = \3',
            content,
            flags=re.MULTILINE
        )
        
        if content != original_content:
            with open(scraper_file, 'w') as f:
                f.write(content)
            print(f"    ✓ Fixed syntax errors in {scraper_file.name}")

def fix_class_structure_errors():
    """Fix class structure errors like self outside __init__"""
    print("🔧 Fixing class structure errors...")
    
    scrapers_dir = Path("src/scrapers")
    
    for scraper_file in scrapers_dir.glob("*.py"):
        with open(scraper_file, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Find class definitions and fix self references outside methods
        lines = content.split('\n')
        fixed_lines = []
        in_class = False
        class_name = ""
        init_method_exists = False
        class_attributes = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Detect class definition
            if stripped.startswith('class '):
                in_class = True
                class_name = stripped.split('(')[0].replace('class ', '').strip()
                init_method_exists = False
                class_attributes = []
                fixed_lines.append(line)
                i += 1
                continue
            
            # Check if __init__ method exists
            if in_class and stripped.startswith('def __init__'):
                init_method_exists = True
                fixed_lines.append(line)
                i += 1
                continue
            
            # Collect class-level self attributes
            if in_class and stripped.startswith('self.') and not init_method_exists:
                class_attributes.append(line)
                i += 1
                continue
            
            # If we hit another method and haven't seen __init__, create it
            if in_class and stripped.startswith('def ') and not stripped.startswith('def __init__') and not init_method_exists:
                # Insert __init__ method with collected attributes
                indent = len(line) - len(line.lstrip())
                init_lines = [
                    ' ' * indent + 'def __init__(self, config, website_config=None):',
                    ' ' * (indent + 4) + 'super().__init__(config, website_config)',
                    ' ' * (indent + 4) + '# Setup logging',
                    ' ' * (indent + 4) + 'self.logger = logging.getLogger(f"proposaland.{self.__class__.__name__}")',
                    ''
                ]
                
                # Add collected attributes
                for attr_line in class_attributes:
                    init_lines.append(' ' * (indent + 4) + attr_line.strip())
                
                init_lines.append('')
                
                fixed_lines.extend(init_lines)
                init_method_exists = True
                class_attributes = []
            
            # Reset when we hit a new class
            if stripped.startswith('class ') and in_class:
                in_class = False
            
            fixed_lines.append(line)
            i += 1
        
        new_content = '\n'.join(fixed_lines)
        
        if new_content != original_content:
            with open(scraper_file, 'w') as f:
                f.write(new_content)
            print(f"    ✓ Fixed class structure in {scraper_file.name}")

def fix_import_errors():
    """Fix import errors in all scrapers"""
    print("🔧 Fixing import errors...")
    
    scrapers_dir = Path("src/scrapers")
    
    for scraper_file in scrapers_dir.glob("*.py"):
        with open(scraper_file, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Ensure all necessary imports are present
        required_imports = [
            'import requests',
            'import time',
            'import json',
            'from datetime import datetime, timedelta',
            'from typing import List, Dict, Optional, Any',
            'from bs4 import BeautifulSoup',
            'import logging',
            'import re'
        ]
        
        # Check and add missing imports
        for import_line in required_imports:
            if import_line not in content:
                # Add import at the top after existing imports
                lines = content.split('\n')
                import_section_end = 0
                
                for i, line in enumerate(lines):
                    if line.startswith(('import ', 'from ')) and not line.startswith('from .'):
                        import_section_end = i
                
                lines.insert(import_section_end + 1, import_line)
                content = '\n'.join(lines)
        
        if content != original_content:
            with open(scraper_file, 'w') as f:
                f.write(content)
            print(f"    ✓ Fixed imports in {scraper_file.name}")

def validate_python_syntax():
    """Validate Python syntax for all scrapers"""
    print("🧪 Validating Python syntax...")
    
    scrapers_dir = Path("src/scrapers")
    valid_count = 0
    error_count = 0
    
    for scraper_file in scrapers_dir.glob("*.py"):
        try:
            with open(scraper_file, 'r') as f:
                content = f.read()
            
            compile(content, scraper_file, 'exec')
            valid_count += 1
            print(f"    ✓ {scraper_file.name} - Valid syntax")
            
        except SyntaxError as e:
            error_count += 1
            print(f"    ❌ {scraper_file.name} - Syntax error: {e}")
        except Exception as e:
            error_count += 1
            print(f"    ❌ {scraper_file.name} - Error: {e}")
    
    print(f"    Valid: {valid_count}, Errors: {error_count}")
    return error_count == 0

def create_clean_scrapers():
    """Create clean versions of problematic scrapers"""
    print("🔧 Creating clean scraper templates...")
    
    # Create a clean base scraper template
    base_scraper_template = '''"""
Base scraper class for Proposaland opportunity monitoring system.
Provides common functionality for all website-specific scrapers.
"""

import requests
import time
import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
import logging
import re
import sys
import os

# Add parent directory to path to import reference extractor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from reference_number_extractor import ReferenceNumberExtractor
except ImportError:
    print("Warning: Could not import ReferenceNumberExtractor")
    ReferenceNumberExtractor = None

class OpportunityData:
    """Data class for opportunity information"""
    
    def __init__(self):
        self.title = ""
        self.organization = ""
        self.source_url = ""
        self.description = ""
        self.location = ""
        self.deadline = None
        self.budget = None
        self.reference_number = ""
        self.keywords_found = []
        self.raw_data = {}

class BaseScraper(ABC):
    """Abstract base class for all scrapers"""
    
    def __init__(self, config: Dict, website_config: Dict = None):
        self.config = config
        self.website_config = website_config or {}
        
        # Setup logging
        self.logger = logging.getLogger(f"proposaland.{self.__class__.__name__}")
        
        # Common configuration
        self.request_delay = self.website_config.get('request_delay', 1)
        self.max_retries = self.website_config.get('max_retries', 3)
        self.timeout = self.website_config.get('timeout', 30)
        
        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Initialize reference extractor
        if ReferenceNumberExtractor:
            self.ref_extractor = ReferenceNumberExtractor()
        else:
            self.ref_extractor = None
    
    def get_page(self, url: str, max_retries: int = None) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page"""
        max_retries = max_retries or self.max_retries
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Fetching {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                time.sleep(self.request_delay)
                return soup
                
            except requests.RequestException as e:
                self.logger.warning(f"Request failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    self.logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        
        return None
    
    @abstractmethod
    def scrape_opportunities(self) -> List[OpportunityData]:
        """Scrape opportunities from the website"""
        pass
    
    def extract_reference_number(self, text: str) -> str:
        """Extract reference number from text"""
        if self.ref_extractor:
            result = self.ref_extractor.extract_reference(text)
            return result.get('reference', '') if result else ''
        return ""
    
    def extract_deadline(self, text: str) -> Optional[datetime]:
        """Extract deadline from text"""
        if not text:
            return None
        
        # Common date patterns
        patterns = [
            r'(\\d{1,2}[/-]\\d{1,2}[/-]\\d{4})',
            r'(\\d{4}-\\d{2}-\\d{2})',
            r'(\\d{1,2}\\s+[A-Za-z]{3,9}\\s+\\d{4})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    # Try to parse the date
                    date_str = matches[0]
                    for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d %B %Y', '%d %b %Y']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except:
                    pass
        
        return None
'''
    
    # Write the clean base scraper
    base_scraper_path = Path("src/scrapers/base_scraper.py")
    with open(base_scraper_path, 'w') as f:
        f.write(base_scraper_template)
    
    print("    ✓ Created clean base_scraper.py")

def main():
    """Run all fixes"""
    print("🚀 COMPREHENSIVE ERROR FIX FOR PROPOSALAND SCRAPERS")
    print("=" * 60)
    
    # Change to proposaland directory
    os.chdir('/home/ubuntu/proposaland')
    
    # Run all fixes in order
    fix_datetime_import_error()
    fix_backslash_escape_sequences()
    fix_indentation_errors()
    fix_syntax_errors()
    fix_class_structure_errors()
    fix_import_errors()
    create_clean_scrapers()
    
    # Validate syntax
    print("\n" + "=" * 60)
    if validate_python_syntax():
        print("✅ ALL SYNTAX ERRORS FIXED!")
        print("The scrapers should now import and run without syntax errors.")
    else:
        print("❌ Some syntax errors remain. Manual review may be needed.")
    
    print("\nNext steps:")
    print("1. Test the monitoring system: python3 proposaland_monitor.py")
    print("2. Check individual scrapers if issues persist")
    print("3. Review any remaining runtime errors")

if __name__ == "__main__":
    main()
