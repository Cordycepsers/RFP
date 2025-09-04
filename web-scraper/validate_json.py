#!/usr/bin/env python3

import json
import sys
import requests
from urllib.parse import urlparse

def validate_websites_json(fix_issues=False):
    """Validate and optionally fix the websites.json file"""
    
    print("🔍 COMPREHENSIVE WEBSITES.JSON VALIDATOR")
    print("=" * 60)
    
    try:
        with open('websites.json', 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON SYNTAX ERROR: {e}")
        return False
    except FileNotFoundError:
        print("❌ File websites.json not found")
        return False
    
    print(f"✅ JSON file loaded successfully")
    print(f"📊 Header claims {config.get('totalWebsites', 'unknown')} websites")
    print(f"📊 Actually contains {len(config.get('websites', []))} websites")
    
    websites = config.get('websites', [])
    
    if len(websites) != config.get('totalWebsites', 0):
        print(f"⚠️ Website count mismatch!")
    
    issues_found = []
    fixes_applied = []
    
    print(f"\n🔍 Validating {len(websites)} websites:")
    print("-" * 60)
    
    for i, site in enumerate(websites):
        site_name = site.get('name', f'Site #{i+1}')
        print(f"\n{i+1:2d}. {site_name}")
        
        # Check required fields
        required_fields = ['name', 'url', 'selectors']
        site_issues = []
        
        for field in required_fields:
            if not site.get(field):
                site_issues.append(f"Missing required field: {field}")
        
        # Check URL
        url = site.get('url', '')
        if url:
            if not url.startswith('http'):
                site_issues.append("URL doesn't start with http/https")
            
            # Parse URL to check validity
            try:
                parsed = urlparse(url)
                if not parsed.netloc:
                    site_issues.append("Invalid URL format")
            except Exception:
                site_issues.append("URL parsing failed")
        
        # Check selectors structure
        selectors = site.get('selectors', {})
        if selectors:
            # Check listContainer
            if not selectors.get('listContainer'):
                site_issues.append("Missing listContainer selector")
            
            # Check listItems
            list_items = selectors.get('listItems', {})
            if not list_items:
                site_issues.append("Missing listItems object")
            else:
                # Check essential listItems fields
                if not list_items.get('container'):
                    site_issues.append("Missing container selector in listItems")
                    
                    # Auto-fix: If listContainer exists, use it as container
                    if fix_issues and selectors.get('listContainer'):
                        list_items['container'] = selectors['listContainer']
                        fixes_applied.append(f"Site {i+1}: Added container selector from listContainer")
                
                if not list_items.get('title'):
                    site_issues.append("Missing title selector")
        
        # Display issues
        if site_issues:
            for issue in site_issues:
                print(f"    ❌ {issue}")
            issues_found.extend(site_issues)
        else:
            print(f"    ✅ No issues found")
    
    # Summary
    print(f"\n" + "=" * 60)
    print(f"🎯 VALIDATION SUMMARY:")
    print(f"   Total websites: {len(websites)}")
    print(f"   Issues found: {len(issues_found)}")
    print(f"   Fixes applied: {len(fixes_applied)}")
    
    if fixes_applied:
        print(f"\n🔧 FIXES APPLIED:")
        for fix in fixes_applied:
            print(f"   ✅ {fix}")
        
        if fix_issues:
            # Save the fixed configuration
            with open('websites.json', 'w') as f:
                json.dump(config, f, indent=2)
            print(f"\n💾 Updated websites.json saved")
    
    if issues_found:
        print(f"\n⚠️ REMAINING ISSUES:")
        unique_issues = list(set(issues_found))
        for issue in unique_issues:
            count = issues_found.count(issue)
            print(f"   • {issue} ({count} sites)")
        
        print(f"\nRun with --fix to attempt automatic fixes")
        return False
    else:
        print(f"\n🎉 ALL WEBSITES VALIDATED SUCCESSFULLY!")
        return True

def test_site_accessibility():
    """Quick test of website accessibility"""
    print(f"\n🌐 TESTING WEBSITE ACCESSIBILITY:")
    print("-" * 40)
    
    try:
        with open('websites.json', 'r') as f:
            config = json.load(f)
    except:
        print("❌ Cannot load websites.json")
        return
    
    working_sites = []
    problematic_sites = []
    
    # Test a sample of sites
    test_sites = config['websites'][:5]  # Test first 5 sites
    
    for i, site in enumerate(test_sites):
        name = site.get('name', 'Unknown')[:40] + "..."
        url = site.get('url', '')
        
        print(f"{i+1}. {name}")
        
        if not url:
            print(f"   ❌ No URL")
            problematic_sites.append(name)
            continue
        
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            if response.status_code < 400:
                print(f"   ✅ Accessible (HTTP {response.status_code})")
                working_sites.append(name)
            else:
                print(f"   ⚠️ HTTP {response.status_code}")
                problematic_sites.append(name)
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout")
            problematic_sites.append(name)
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error: {str(e)[:30]}...")
            problematic_sites.append(name)
    
    print(f"\n📊 Accessibility Summary:")
    print(f"   Working: {len(working_sites)}")
    print(f"   Problematic: {len(problematic_sites)}")

if __name__ == "__main__":
    fix_mode = '--fix' in sys.argv
    test_access = '--test-access' in sys.argv
    
    if len(sys.argv) == 1:
        print("Usage:")
        print("  python validate_json.py              # Validate only")
        print("  python validate_json.py --fix        # Validate and fix")
        print("  python validate_json.py --test-access # Test website accessibility")
        sys.exit(0)
    
    success = validate_websites_json(fix_issues=fix_mode)
    
    if test_access:
        test_site_accessibility()
    
    sys.exit(0 if success else 1)
