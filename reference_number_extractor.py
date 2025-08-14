"""
Reference Number Extraction System for Proposaland
Advanced pattern recognition for extracting project reference numbers from opportunity text.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class ReferenceMatch:
    """Container for reference number match with confidence score."""
    reference_number: str
    confidence: float
    pattern_type: str
    organization_type: str
    match_position: int
    context: str


class ReferenceNumberExtractor:
    """Advanced reference number extraction with pattern recognition and confidence scoring."""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.organization_indicators = self._initialize_organization_indicators()
        
    def _initialize_patterns(self) -> Dict[str, List[Dict]]:
        """Initialize reference number patterns for different organization types."""
        return {
            'un_agencies': [
                {
                    'pattern': r'\b(?:RFP|RFQ|ITB|EOI|RFI)[/\-\s]*(\d{4})[/\-](\d{3,4})\b',
                    'confidence': 0.95,
                    'description': 'UN standard format (RFP/2024/001)',
                    'format_func': lambda m: f"{m.group(0).split('/')[0] if '/' in m.group(0) else m.group(0).split('-')[0]}/{m.group(1)}/{m.group(2)}"
                },
                {
                    'pattern': r'\b(UNDP-[A-Z]{2,4}-\d{4,6})\b',
                    'confidence': 0.98,
                    'description': 'UNDP specific format (UNDP-PAK-001234)',
                    'format_func': lambda m: m.group(1)
                },
                {
                    'pattern': r'\b(UN[A-Z]{2,4}[/\-]\d{4}[/\-]\d{3,4})\b',
                    'confidence': 0.90,
                    'description': 'UN agency format (UNHCR/2024/001)',
                    'format_func': lambda m: m.group(1)
                },
                {
                    'pattern': r'\b([A-Z]{3,5}[/\-]\d{4}[/\-][A-Z]{2,4}[/\-]\d{3,4})\b',
                    'confidence': 0.85,
                    'description': 'Extended UN format (UNICEF/2024/PROC/001)',
                    'format_func': lambda m: m.group(1)
                }
            ],
            'world_bank': [
                {
                    'pattern': r'\b(P\d{6})\b',
                    'confidence': 0.95,
                    'description': 'World Bank project ID (P123456)',
                    'format_func': lambda m: m.group(1)
                },
                {
                    'pattern': r'\b(TF\d{6})\b',
                    'confidence': 0.90,
                    'description': 'World Bank trust fund (TF123456)',
                    'format_func': lambda m: m.group(1)
                },
                {
                    'pattern': r'\b(IBRD\d{5})\b',
                    'confidence': 0.88,
                    'description': 'IBRD loan number (IBRD12345)',
                    'format_func': lambda m: m.group(1)
                },
                {
                    'pattern': r'\b(WB[/\-]\d{4}[/\-]\d{3,4})\b',
                    'confidence': 0.85,
                    'description': 'World Bank procurement (WB/2024/001)',
                    'format_func': lambda m: m.group(1)
                }
            ],
            'ngos': [
                {
                    'pattern': r'\b([A-Z]{2,4}[/\-]\d{4}[/\-][A-Z]{3,6}[/\-]\d{3,4})\b',
                    'confidence': 0.90,
                    'description': 'NGO standard format (SC/2024/MEDIA/001)',
                    'format_func': lambda m: m.group(1)
                },
                {
                    'pattern': r'\b([A-Z]{3,5}[\-]\d{4}[\-]\d{3,4})\b',
                    'confidence': 0.85,
                    'description': 'NGO dash format (IRC-2024-001)',
                    'format_func': lambda m: m.group(1)
                },
                {
                    'pattern': r'\b(REF[\-/]\d{4}[\-/]\d{3,4})\b',
                    'confidence': 0.80,
                    'description': 'NGO reference format (REF-2024-001)',
                    'format_func': lambda m: m.group(1)
                },
                {
                    'pattern': r'\b([A-Z]{2,4}\d{6,8})\b',
                    'confidence': 0.75,
                    'description': 'NGO compact format (SC20240001)',
                    'format_func': lambda m: m.group(1)
                }
            ],
            'development_banks': [
                {
                    'pattern': r'\b(ADB[/\-]\d{4}[/\-]\d{3,4})\b',
                    'confidence': 0.90,
                    'description': 'Asian Development Bank (ADB/2024/001)',
                    'format_func': lambda m: m.group(1)
                },
                {
                    'pattern': r'\b(AfDB[/\-]\d{4}[/\-]\d{3,4})\b',
                    'confidence': 0.90,
                    'description': 'African Development Bank (AfDB/2024/001)',
                    'format_func': lambda m: m.group(1)
                },
                {
                    'pattern': r'\b([A-Z]{3,5}DB[/\-]\d{4}[/\-]\d{3,4})\b',
                    'confidence': 0.85,
                    'description': 'Development bank format (IADB/2024/001)',
                    'format_func': lambda m: m.group(1)
                }
            ],
            'generic': [
                {
                    'pattern': r'\b(\d{4}[\-/]\d{3,4})\b',
                    'confidence': 0.60,
                    'description': 'Generic year-number format (2024-001)',
                    'format_func': lambda m: m.group(1)
                },
                {
                    'pattern': r'\b([A-Z]{2,4}\d{4,8})\b',
                    'confidence': 0.55,
                    'description': 'Generic alphanumeric (ABC12345)',
                    'format_func': lambda m: m.group(1)
                },
                {
                    'pattern': r'\b(\d{6,8})\b',
                    'confidence': 0.50,
                    'description': 'Generic numeric (12345678)',
                    'format_func': lambda m: m.group(1)
                },
                {
                    'pattern': r'\b([A-Z]{2,4}[\-/][A-Z]{2,4}[\-/]\d{3,6})\b',
                    'confidence': 0.65,
                    'description': 'Generic code format (ABC-DEF-123)',
                    'format_func': lambda m: m.group(1)
                }
            ]
        }
    
    def _initialize_organization_indicators(self) -> Dict[str, List[str]]:
        """Initialize organization type indicators for context-based classification."""
        return {
            'un_agencies': [
                'undp', 'unicef', 'unhcr', 'wfp', 'who', 'unfpa', 'unops',
                'united nations', 'un global', 'procurement notice'
            ],
            'world_bank': [
                'world bank', 'ibrd', 'ida', 'ifc', 'miga', 'worldbank.org'
            ],
            'ngos': [
                'save the children', 'mercy corps', 'oxfam', 'care', 'irc',
                'plan international', 'world vision', 'actionaid', 'msf'
            ],
            'development_banks': [
                'asian development bank', 'adb', 'african development bank', 'afdb',
                'inter-american development bank', 'iadb', 'european bank'
            ]
        }
    
    def extract_reference_numbers(self, text: str, context: str = "") -> List[ReferenceMatch]:
        """Extract all potential reference numbers from text with confidence scoring."""
        if not text:
            return []
        
        matches = []
        text_lower = text.lower()
        full_context = f"{context} {text}".lower()
        
        # Determine organization type from context
        org_type = self._determine_organization_type(full_context)
        
        # Try patterns in order of specificity
        pattern_groups = ['un_agencies', 'world_bank', 'development_banks', 'ngos', 'generic']
        
        # Prioritize patterns based on detected organization type
        if org_type != 'unknown':
            pattern_groups = [org_type] + [pg for pg in pattern_groups if pg != org_type]
        
        for group_name in pattern_groups:
            group_patterns = self.patterns.get(group_name, [])
            
            for pattern_info in group_patterns:
                pattern = pattern_info['pattern']
                base_confidence = pattern_info['confidence']
                
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    try:
                        # Extract and format reference number
                        ref_number = pattern_info['format_func'](match)
                        
                        # Calculate confidence score
                        confidence = self._calculate_confidence(
                            ref_number, match, text, full_context, 
                            base_confidence, group_name, org_type
                        )
                        
                        # Get surrounding context
                        start = max(0, match.start() - 50)
                        end = min(len(text), match.end() + 50)
                        surrounding_context = text[start:end].strip()
                        
                        ref_match = ReferenceMatch(
                            reference_number=ref_number,
                            confidence=confidence,
                            pattern_type=pattern_info['description'],
                            organization_type=group_name,
                            match_position=match.start(),
                            context=surrounding_context
                        )
                        
                        matches.append(ref_match)
                        
                    except Exception as e:
                        logger.warning(f"Error processing reference match: {e}")
                        continue
        
        # Remove duplicates and sort by confidence
        unique_matches = self._remove_duplicate_matches(matches)
        unique_matches.sort(key=lambda x: x.confidence, reverse=True)
        
        return unique_matches
    
    def _determine_organization_type(self, context: str) -> str:
        """Determine organization type from context."""
        context_lower = context.lower()
        
        for org_type, indicators in self.organization_indicators.items():
            for indicator in indicators:
                if indicator in context_lower:
                    return org_type
        
        return 'unknown'
    
    def _calculate_confidence(self, ref_number: str, match, text: str, context: str, 
                            base_confidence: float, pattern_group: str, detected_org_type: str) -> float:
        """Calculate confidence score for a reference number match."""
        confidence = base_confidence
        
        # Boost confidence if organization type matches context
        if pattern_group == detected_org_type:
            confidence += 0.1
        
        # Boost confidence for common reference indicators
        surrounding_text = text[max(0, match.start()-30):match.end()+30].lower()
        reference_indicators = [
            'reference', 'ref', 'number', 'no', 'id', 'tender', 'rfp', 'rfq', 
            'procurement', 'solicitation', 'opportunity', 'notice'
        ]
        
        indicator_count = sum(1 for indicator in reference_indicators if indicator in surrounding_text)
        confidence += min(0.15, indicator_count * 0.03)
        
        # Reduce confidence for very short or very long numbers
        if len(ref_number) < 4:
            confidence -= 0.2
        elif len(ref_number) > 20:
            confidence -= 0.1
        
        # Boost confidence for current year
        current_year = str(2025)
        if current_year in ref_number:
            confidence += 0.05
        
        # Reduce confidence if it looks like a date, phone number, or other non-reference
        if self._looks_like_non_reference(ref_number):
            confidence -= 0.3
        
        # Ensure confidence is within bounds
        return max(0.0, min(1.0, confidence))
    
    def _looks_like_non_reference(self, text: str) -> bool:
        """Check if text looks like a date, phone number, or other non-reference."""
        # Date patterns
        if re.match(r'^\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}$', text):
            return True
        
        # Phone number patterns
        if re.match(r'^\+?\d{10,15}$', text.replace('-', '').replace(' ', '')):
            return True
        
        # Time patterns
        if re.match(r'^\d{1,2}:\d{2}', text):
            return True
        
        # Very generic numbers
        if re.match(r'^\d{1,3}$', text):
            return True
        
        return False
    
    def _remove_duplicate_matches(self, matches: List[ReferenceMatch]) -> List[ReferenceMatch]:
        """Remove duplicate reference number matches."""
        seen = set()
        unique_matches = []
        
        for match in matches:
            # Create a key based on the reference number (normalized)
            key = re.sub(r'[/\-\s]', '', match.reference_number.upper())
            
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
            else:
                # If we've seen this reference before, keep the one with higher confidence
                for i, existing_match in enumerate(unique_matches):
                    existing_key = re.sub(r'[/\-\s]', '', existing_match.reference_number.upper())
                    if existing_key == key and match.confidence > existing_match.confidence:
                        unique_matches[i] = match
                        break
        
        return unique_matches
    
    def get_best_reference(self, text: str, context: str = "") -> Optional[ReferenceMatch]:
        """Get the best (highest confidence) reference number from text."""
        matches = self.extract_reference_numbers(text, context)
        return matches[0] if matches else None
    
    def extract_with_validation(self, text: str, context: str = "", 
                               min_confidence: float = 0.7) -> List[ReferenceMatch]:
        """Extract reference numbers with minimum confidence threshold."""
        matches = self.extract_reference_numbers(text, context)
        return [match for match in matches if match.confidence >= min_confidence]
    
    def format_reference_summary(self, matches: List[ReferenceMatch]) -> str:
        """Format reference matches into a readable summary."""
        if not matches:
            return "No reference numbers found"
        
        summary_lines = []
        for i, match in enumerate(matches[:3], 1):  # Show top 3 matches
            summary_lines.append(
                f"{i}. {match.reference_number} "
                f"(confidence: {match.confidence:.2f}, "
                f"type: {match.organization_type})"
            )
        
        return "\n".join(summary_lines)


# Convenience functions for easy integration
def extract_reference_number(text: str, context: str = "") -> Tuple[str, float]:
    """Extract the best reference number and its confidence score."""
    extractor = ReferenceNumberExtractor()
    best_match = extractor.get_best_reference(text, context)
    
    if best_match:
        return best_match.reference_number, best_match.confidence
    else:
        return "", 0.0


def extract_all_references(text: str, context: str = "") -> List[Dict]:
    """Extract all reference numbers as a list of dictionaries."""
    extractor = ReferenceNumberExtractor()
    matches = extractor.extract_reference_numbers(text, context)
    
    return [
        {
            'reference_number': match.reference_number,
            'confidence': match.confidence,
            'pattern_type': match.pattern_type,
            'organization_type': match.organization_type,
            'context': match.context
        }
        for match in matches
    ]


if __name__ == "__main__":
    # Test the extractor
    extractor = ReferenceNumberExtractor()
    
    test_texts = [
        "Please submit your proposal for RFP/2024/001 by the deadline.",
        "UNDP-PAK-001234 is the reference for this procurement notice.",
        "World Bank project P123456 requires multimedia services.",
        "Save the Children tender SC/2024/MEDIA/001 for video production.",
        "Reference number: IRC-2024-001 for communication services."
    ]
    
    for text in test_texts:
        print(f"\nText: {text}")
        matches = extractor.extract_reference_numbers(text)
        print(extractor.format_reference_summary(matches))

