#!/usr/bin/env python3
"""
Configuration validation script for the Proposaland RFP monitoring system.
Validates critical sections against JSON schema and provides descriptive error messages.
"""

import sys
import os
import json
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator
from typing import Dict, Any, List


# JSON Schema for configuration validation
CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["system", "email", "keywords", "geographic_filters", "target_websites"],
    "properties": {
        "system": {
            "type": "object",
            "required": ["name", "version"],
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
                "execution_time": {"type": "string", "pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$"},
                "timezone": {"type": "string", "minLength": 1}
            },
            "additionalProperties": True
        },
        "email": {
            "type": "object",
            "required": ["recipient"],
            "properties": {
                "recipient": {"type": "string", "format": "email"},
                "sender_email": {"type": "string", "format": "email"},
                "sender_password": {"type": "string", "minLength": 1},
                "smtp_server": {"type": "string", "minLength": 1},
                "smtp_port": {"type": "integer", "minimum": 1, "maximum": 65535},
                "use_tls": {"type": "boolean"},
                "subject_template": {"type": "string", "minLength": 1}
            },
            "additionalProperties": True
        },
        "keywords": {
            "type": "object",
            "required": ["primary"],
            "properties": {
                "primary": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string", "minLength": 1}
                },
                "secondary": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1}
                },
                "exclusions": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1}
                }
            },
            "additionalProperties": True
        },
        "geographic_filters": {
            "type": "object",
            "properties": {
                "excluded_countries": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1}
                },
                "included_countries": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1}
                },
                "excluded_regions": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1}
                }
            },
            "additionalProperties": True
        },
        "target_websites": {
            "type": "object",
            "required": ["high_priority"],
            "properties": {
                "high_priority": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["name", "url", "type", "priority"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "url": {"type": "string", "format": "uri"},
                            "type": {"type": "string", "minLength": 1},
                            "priority": {"type": "number", "minimum": 0, "maximum": 1}
                        },
                        "additionalProperties": True
                    }
                },
                "medium_priority": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "url", "type", "priority"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "url": {"type": "string", "format": "uri"},
                            "type": {"type": "string", "minLength": 1},
                            "priority": {"type": "number", "minimum": 0, "maximum": 1}
                        },
                        "additionalProperties": True
                    }
                },
                "low_priority": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "url", "type", "priority"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "url": {"type": "string", "format": "uri"},
                            "type": {"type": "string", "minLength": 1},
                            "priority": {"type": "number", "minimum": 0, "maximum": 1}
                        },
                        "additionalProperties": True
                    }
                }
            },
            "additionalProperties": True
        },
        "budget_filters": {
            "type": "object",
            "properties": {
                "min_budget": {"type": "number", "minimum": 0},
                "max_budget": {"type": "number", "minimum": 0},
                "currency": {"type": "string", "minLength": 3, "maxLength": 3}
            },
            "additionalProperties": True
        },
        "deadline_filters": {
            "type": "object",
            "properties": {
                "minimum_days": {"type": "integer", "minimum": 0}
            },
            "additionalProperties": True
        },
        "scoring_weights": {
            "type": "object",
            "properties": {
                "keyword_match": {"type": "number", "minimum": 0, "maximum": 1},
                "budget_range": {"type": "number", "minimum": 0, "maximum": 1},
                "deadline_urgency": {"type": "number", "minimum": 0, "maximum": 1},
                "source_priority": {"type": "number", "minimum": 0, "maximum": 1},
                "geographic_fit": {"type": "number", "minimum": 0, "maximum": 1},
                "sector_relevance": {"type": "number", "minimum": 0, "maximum": 1},
                "reference_number_bonus": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "additionalProperties": True
        },
        "priority_thresholds": {
            "type": "object",
            "properties": {
                "critical": {"type": "number", "minimum": 0, "maximum": 1},
                "high": {"type": "number", "minimum": 0, "maximum": 1},
                "medium": {"type": "number", "minimum": 0, "maximum": 1},
                "low": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "additionalProperties": True
        },
        "output_settings": {
            "type": "object",
            "properties": {
                "json_filename": {"type": "string", "minLength": 1},
                "excel_filename": {"type": "string", "minLength": 1},
                "max_opportunities_per_email": {"type": "integer", "minimum": 1},
                "top_opportunities_count": {"type": "integer", "minimum": 1}
            },
            "additionalProperties": True
        }
    },
    "additionalProperties": True
}


class ConfigValidator:
    """Validates Proposaland configuration files."""
    
    def __init__(self, config_path: str = "config/proposaland_config.json"):
        self.config_path = Path(config_path)
        self.config_data: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def load_config(self) -> bool:
        """Load the configuration file."""
        try:
            if not self.config_path.exists():
                self.errors.append(f"Configuration file not found: {self.config_path}")
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
            
            return True
        
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in config file: {e}")
            return False
        
        except Exception as e:
            self.errors.append(f"Error loading config file: {e}")
            return False
    
    def validate_schema(self) -> bool:
        """Validate configuration against JSON schema."""
        try:
            validate(instance=self.config_data, schema=CONFIG_SCHEMA)
            return True
        
        except ValidationError as e:
            path = " -> ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
            self.errors.append(f"Schema validation failed at '{path}': {e.message}")
            return False
    
    def validate_email_config(self) -> bool:
        """Validate email configuration with detailed checks."""
        email_config = self.config_data.get('email', {})
        valid = True
        
        # Check if email is configured for notifications
        if not email_config:
            self.errors.append("Email configuration is missing but required for notifications")
            return False
        
        # Check for recipient email
        if not email_config.get('recipient'):
            self.errors.append("Email recipient is required")
            valid = False
        
        # Check for SMTP configuration if sender is configured
        if email_config.get('sender_email'):
            if not email_config.get('sender_password'):
                self.warnings.append("Email sender configured but no password provided - email notifications may fail")
            
            if not email_config.get('smtp_server'):
                self.errors.append("SMTP server is required when sender email is configured")
                valid = False
            
            if not email_config.get('smtp_port'):
                self.warnings.append("SMTP port not specified, will use default")
        else:
            self.warnings.append("No sender email configured - system may not be able to send notifications")
        
        return valid
    
    def validate_paths(self) -> bool:
        """Validate that required directories and files exist or can be created."""
        valid = True
        
        # Check output directory can be created
        try:
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
        except Exception as e:
            self.errors.append(f"Cannot create output directory: {e}")
            valid = False
        
        # Check logs directory can be created
        try:
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
        except Exception as e:
            self.errors.append(f"Cannot create logs directory: {e}")
            valid = False
        
        return valid
    
    def validate_scoring_weights(self) -> bool:
        """Validate that scoring weights add up to approximately 1.0."""
        scoring_weights = self.config_data.get('scoring_weights', {})
        if not scoring_weights:
            self.warnings.append("No scoring weights defined - using defaults")
            return True
        
        total_weight = sum(scoring_weights.values())
        if abs(total_weight - 1.0) > 0.01:  # Allow small floating point errors
            self.warnings.append(f"Scoring weights sum to {total_weight:.3f}, should be close to 1.0")
        
        return True
    
    def validate_website_configs(self) -> bool:
        """Validate website configurations."""
        websites = self.config_data.get('target_websites', {})
        if not websites:
            self.errors.append("No target websites configured")
            return False
        
        total_sites = 0
        for priority_level, sites in websites.items():
            if not isinstance(sites, list):
                continue
            
            total_sites += len(sites)
            for site in sites:
                site_name = site.get('name', 'unnamed')
                
                # Check URL accessibility (basic format check)
                url = site.get('url', '')
                if not url.startswith(('http://', 'https://')):
                    self.warnings.append(f"Website '{site_name}' has invalid URL format")
                
                # Check scraper type is specified
                if not site.get('type'):
                    self.warnings.append(f"Website '{site_name}' has no scraper type specified")
        
        if total_sites == 0:
            self.errors.append("No websites configured for monitoring")
            return False
        
        return True
    
    def validate_keywords(self) -> bool:
        """Validate keyword configuration."""
        keywords = self.config_data.get('keywords', {})
        
        primary = keywords.get('primary', [])
        if not primary:
            self.errors.append("No primary keywords configured - system won't filter opportunities effectively")
            return False
        
        if len(primary) < 3:
            self.warnings.append(f"Only {len(primary)} primary keywords configured - consider adding more for better filtering")
        
        return True
    
    def run_validation(self) -> bool:
        """Run all validation checks."""
        print(f"🔍 Validating configuration: {self.config_path}")
        print("=" * 60)
        
        # Load configuration
        if not self.load_config():
            return False
        
        # Run all validation checks
        validations = [
            ("JSON Schema", self.validate_schema),
            ("Email Configuration", self.validate_email_config),
            ("File Paths", self.validate_paths),
            ("Scoring Weights", self.validate_scoring_weights),
            ("Website Configurations", self.validate_website_configs),
            ("Keywords", self.validate_keywords),
        ]
        
        all_valid = True
        for name, validator in validations:
            try:
                valid = validator()
                status = "✅ PASS" if valid else "❌ FAIL"
                print(f"{name:25} {status}")
                if not valid:
                    all_valid = False
            except Exception as e:
                print(f"{name:25} ❌ ERROR: {e}")
                self.errors.append(f"Validation error in {name}: {e}")
                all_valid = False
        
        # Display results
        print("\n" + "=" * 60)
        
        if self.errors:
            print("❌ ERRORS found:")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if all_valid:
            print(f"\n🎉 Configuration validation PASSED!")
            print(f"📝 {len(self.config_data.get('target_websites', {}).get('high_priority', []))} high-priority websites configured")
            print(f"🎯 {len(self.config_data.get('keywords', {}).get('primary', []))} primary keywords configured")
            print(f"📧 Email notifications: {'Configured' if self.config_data.get('email', {}).get('recipient') else 'Not configured'}")
        else:
            print(f"\n❌ Configuration validation FAILED!")
            print("Please fix the errors above before running the system.")
        
        print("=" * 60)
        return all_valid
    
    def suggest_fixes(self) -> List[str]:
        """Suggest fixes for common configuration issues."""
        suggestions = []
        
        if not self.config_data:
            suggestions.append("Create configuration file by copying config/sample_config.json to config/proposaland_config.json")
            return suggestions
        
        email_config = self.config_data.get('email', {})
        
        # Email configuration suggestions
        if not email_config.get('sender_password'):
            suggestions.append("Add 'sender_password' to email configuration (use environment variable in production)")
        
        if not email_config.get('smtp_server'):
            suggestions.append("Add SMTP server configuration (e.g., 'smtp.gmail.com' for Gmail)")
        
        if not email_config.get('smtp_port'):
            suggestions.append("Add SMTP port (587 for TLS, 465 for SSL)")
        
        # Keywords suggestions
        keywords = self.config_data.get('keywords', {})
        if len(keywords.get('primary', [])) < 5:
            suggestions.append("Consider adding more primary keywords for better opportunity filtering")
        
        # Website configuration suggestions
        websites = self.config_data.get('target_websites', {})
        total_sites = sum(len(sites) for sites in websites.values() if isinstance(sites, list))
        if total_sites < 5:
            suggestions.append("Consider adding more target websites to increase opportunity coverage")
        
        return suggestions


def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate Proposaland configuration')
    parser.add_argument(
        '--config', 
        default='config/proposaland_config.json',
        help='Path to configuration file (default: config/proposaland_config.json)'
    )
    parser.add_argument(
        '--suggestions', 
        action='store_true',
        help='Show suggestions for improving configuration'
    )
    
    args = parser.parse_args()
    
    # Run validation
    validator = ConfigValidator(args.config)
    is_valid = validator.run_validation()
    
    # Show suggestions if requested
    if args.suggestions:
        suggestions = validator.suggest_fixes()
        if suggestions:
            print("\n💡 SUGGESTIONS for improvement:")
            for suggestion in suggestions:
                print(f"  • {suggestion}")
    
    # Exit with appropriate code
    return 0 if is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
