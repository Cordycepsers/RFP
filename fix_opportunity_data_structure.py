#!/usr/bin/env python3
"""
Fix script for Proposaland data structure mismatch
Converts dictionary returns from scrapers to OpportunityData objects
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.base_scraper import OpportunityData

def convert_dict_to_opportunity_data(opp_dict: Dict[str, Any]) -> OpportunityData:
    """Convert dictionary to OpportunityData object"""
    opp = OpportunityData()
    
    # Map dictionary fields to object attributes
    opp.title = opp_dict.get('title', '')
    opp.description = opp_dict.get('description', '')
    opp.organization = opp_dict.get('organization', '')
    opp.source_url = opp_dict.get('source_url', opp_dict.get('url', ''))
    opp.location = opp_dict.get('location', '')
    opp.reference_number = opp_dict.get('reference_number', '')
    opp.reference_confidence = opp_dict.get('reference_confidence', 0.0)
    opp.keywords_found = opp_dict.get('keywords_found', [])
    opp.currency = opp_dict.get('currency', 'USD')
    
    # Handle deadline conversion
    deadline = opp_dict.get('deadline')
    if deadline:
        if isinstance(deadline, str):
            try:
                opp.deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            except:
                opp.deadline = None
        elif isinstance(deadline, datetime):
            opp.deadline = deadline
    
    # Handle budget conversion
    budget = opp_dict.get('budget')
    if budget:
        if isinstance(budget, (int, float)):
            opp.budget = float(budget)
        elif isinstance(budget, str):
            try:
                # Extract numeric value from budget string
                import re
                numbers = re.findall(r'[\d,]+\.?\d*', budget.replace(',', ''))
                if numbers:
                    opp.budget = float(numbers[0])
            except:
                opp.budget = None
    
    # Handle extracted date
    extracted_date = opp_dict.get('extracted_date')
    if extracted_date:
        if isinstance(extracted_date, str):
            try:
                opp.extracted_date = datetime.fromisoformat(extracted_date.replace('Z', '+00:00'))
            except:
                opp.extracted_date = datetime.now()
        elif isinstance(extracted_date, datetime):
            opp.extracted_date = extracted_date
    else:
        opp.extracted_date = datetime.now()
    
    # Store all additional data in raw_data
    opp.raw_data = opp_dict.copy()
    
    return opp

def fix_scraper_return_type(scraper_file_path: str):
    """Fix scraper to return OpportunityData objects instead of dictionaries"""
    
    print(f"Fixing scraper: {scraper_file_path}")
    
    # Read the file
    with open(scraper_file_path, 'r') as f:
        content = f.read()
    
    # Add import for OpportunityData if not present
    if 'from scrapers.base_scraper import OpportunityData' not in content and 'from .base_scraper import OpportunityData' not in content:
        # Find the imports section and add the import
        lines = content.split('\n')
        import_line_added = False
        
        for i, line in enumerate(lines):
            if line.startswith('from scrapers.base_scraper import') or line.startswith('from .base_scraper import'):
                if 'OpportunityData' not in line:
                    lines[i] = line.replace('import', 'import OpportunityData,')
                    import_line_added = True
                    break
        
        if not import_line_added:
            # Add import after other imports
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    continue
                else:
                    lines.insert(i, 'from scrapers.base_scraper import OpportunityData')
                    break
        
        content = '\n'.join(lines)
    
    # Add conversion function to the scraper
    conversion_function = '''
    def _convert_dict_to_opportunity_data(self, opp_dict: Dict[str, Any]) -> OpportunityData:
        """Convert dictionary to OpportunityData object"""
        opp = OpportunityData()
        
        # Map dictionary fields to object attributes
        opp.title = opp_dict.get('title', '')
        opp.description = opp_dict.get('description', '')
        opp.organization = opp_dict.get('organization', '')
        opp.source_url = opp_dict.get('source_url', opp_dict.get('url', ''))
        opp.location = opp_dict.get('location', '')
        opp.reference_number = opp_dict.get('reference_number', '')
        opp.reference_confidence = opp_dict.get('reference_confidence', 0.0)
        opp.keywords_found = opp_dict.get('keywords_found', [])
        opp.currency = opp_dict.get('currency', 'USD')
        
        # Handle deadline conversion
        deadline = opp_dict.get('deadline')
        if deadline:
            if isinstance(deadline, str):
                try:
                    opp.deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                except:
                    opp.deadline = None
            elif isinstance(deadline, datetime):
                opp.deadline = deadline
        
        # Handle budget conversion
        budget = opp_dict.get('budget')
        if budget:
            if isinstance(budget, (int, float)):
                opp.budget = float(budget)
            elif isinstance(budget, str):
                try:
                    # Extract numeric value from budget string
                    import re
                    numbers = re.findall(r'[\\d,]+\\.?\\d*', budget.replace(',', ''))
                    if numbers:
                        opp.budget = float(numbers[0])
                except:
                    opp.budget = None
        
        # Handle extracted date
        extracted_date = opp_dict.get('extracted_date')
        if extracted_date:
            if isinstance(extracted_date, str):
                try:
                    opp.extracted_date = datetime.fromisoformat(extracted_date.replace('Z', '+00:00'))
                except:
                    opp.extracted_date = datetime.now()
            elif isinstance(extracted_date, datetime):
                opp.extracted_date = extracted_date
        else:
            opp.extracted_date = datetime.now()
        
        # Store all additional data in raw_data
        opp.raw_data = opp_dict.copy()
        
        return opp
'''
    
    # Add the conversion function before the last method
    if '_convert_dict_to_opportunity_data' not in content:
        # Find the last method and add before it
        lines = content.split('\n')
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith('def ') and not lines[i].strip().startswith('def _convert_dict_to_opportunity_data'):
                lines.insert(i, conversion_function)
                break
        content = '\n'.join(lines)
    
    # Modify the scrape_opportunities method to convert dictionaries to OpportunityData objects
    if 'return filtered_opportunities' in content:
        content = content.replace(
            'return filtered_opportunities',
            '''# Convert dictionaries to OpportunityData objects
        opportunity_objects = []
        for opp in filtered_opportunities:
            if isinstance(opp, dict):
                opportunity_objects.append(self._convert_dict_to_opportunity_data(opp))
            else:
                opportunity_objects.append(opp)
        
        return opportunity_objects'''
        )
    
    # Write the fixed content back
    with open(scraper_file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed scraper: {scraper_file_path}")

def main():
    """Fix all scrapers to return OpportunityData objects"""
    
    scrapers_to_fix = [
        '/home/ubuntu/proposaland/src/scrapers/adb_scraper.py',
        '/home/ubuntu/proposaland/src/scrapers/developmentaid_scraper.py',
        '/home/ubuntu/proposaland/src/scrapers/iucn_scraper.py',
        '/home/ubuntu/proposaland/src/scrapers/ungm_scraper.py',
        '/home/ubuntu/proposaland/src/scrapers/globalfund_scraper.py',
        '/home/ubuntu/proposaland/src/scrapers/worldbank_scraper.py'
    ]
    
    print("🔧 Fixing Proposaland data structure mismatch...")
    print("Converting dictionary returns to OpportunityData objects")
    
    for scraper_path in scrapers_to_fix:
        if os.path.exists(scraper_path):
            try:
                fix_scraper_return_type(scraper_path)
                print(f"✅ Fixed: {os.path.basename(scraper_path)}")
            except Exception as e:
                print(f"❌ Error fixing {os.path.basename(scraper_path)}: {e}")
        else:
            print(f"⚠️  File not found: {scraper_path}")
    
    print("\n🎉 Data structure fix completed!")
    print("All scrapers should now return OpportunityData objects instead of dictionaries.")

if __name__ == "__main__":
    main()

