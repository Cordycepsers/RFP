"""
Keyword filtering system for Proposaland opportunity monitoring.
Handles multimedia/creative keyword matching and exclusion filtering.
"""

import re
from typing import List, Dict, Set, Tuple
from loguru import logger


class KeywordFilter:
    """Advanced keyword filtering with fuzzy matching and context analysis."""
    
    def __init__(self, config: Dict):
        self.primary_keywords = [kw.lower() for kw in config.get('keywords', {}).get('primary', [])]
        self.exclusion_keywords = [kw.lower() for kw in config.get('keywords', {}).get('exclusions', [])]
        self.keyword_weights = self._initialize_keyword_weights()
        
    def _initialize_keyword_weights(self) -> Dict[str, float]:
        """Initialize weights for different keywords based on relevance."""
        return {
            # High relevance multimedia keywords
            'video': 1.0,
            'multimedia': 1.0,
            'film': 1.0,
            'animation': 1.0,
            'audiovisual': 1.0,
            
            # Medium relevance creative keywords
            'photo': 0.8,
            'design': 0.8,
            'visual': 0.8,
            'media': 0.8,
            'communication': 0.8,
            
            # Lower relevance but still relevant
            'campaign': 0.6,
            'podcasts': 0.6,
            'virtual event': 0.6,
            'promotion': 0.6,
            
            # Specific formats
            'animated video': 1.0,
        }
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract matching keywords from text with fuzzy matching."""
        if not text:
            return []
        
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.primary_keywords:
            if self._keyword_matches(keyword, text_lower):
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _keyword_matches(self, keyword: str, text: str) -> bool:
        """Check if keyword matches in text with fuzzy matching."""
        # Exact match
        if keyword in text:
            return True
        
        # Handle compound keywords
        if ' ' in keyword:
            words = keyword.split()
            # All words must be present (not necessarily adjacent)
            if all(word in text for word in words):
                return True
        
        # Handle variations and plurals
        variations = self._get_keyword_variations(keyword)
        for variation in variations:
            if variation in text:
                return True
        
        return False
    
    def _get_keyword_variations(self, keyword: str) -> List[str]:
        """Get variations of a keyword (plurals, related terms)."""
        variations = []
        
        # Add plural forms
        if not keyword.endswith('s'):
            variations.append(keyword + 's')
        
        # Add specific variations for common keywords
        keyword_variations = {
            'video': ['videos', 'videography', 'video production'],
            'photo': ['photos', 'photography', 'photographic'],
            'film': ['films', 'filming', 'filmmaking'],
            'design': ['designs', 'designing', 'designer'],
            'media': ['multimedia', 'social media'],
            'animation': ['animations', 'animated', 'animator'],
            'communication': ['communications', 'comms'],
            'campaign': ['campaigns', 'campaigning'],
            'visual': ['visuals', 'visualization'],
            'audiovisual': ['audio-visual', 'av', 'audio visual']
        }
        
        if keyword in keyword_variations:
            variations.extend(keyword_variations[keyword])
        
        return variations
    
    def has_exclusion_keywords(self, text: str) -> Tuple[bool, List[str]]:
        """Check if text contains exclusion keywords."""
        if not text:
            return False, []
        
        text_lower = text.lower()
        found_exclusions = []
        
        for exclusion in self.exclusion_keywords:
            if exclusion in text_lower:
                found_exclusions.append(exclusion)
        
        return len(found_exclusions) > 0, found_exclusions
    
    def calculate_keyword_score(self, found_keywords: List[str]) -> float:
        """Calculate relevance score based on found keywords."""
        if not found_keywords:
            return 0.0
        
        total_weight = 0.0
        max_possible_weight = sum(self.keyword_weights.values())
        
        for keyword in found_keywords:
            weight = self.keyword_weights.get(keyword, 0.5)  # Default weight for unknown keywords
            total_weight += weight
        
        # Normalize score to 0-1 range
        score = min(1.0, total_weight / max_possible_weight)
        
        # Bonus for multiple relevant keywords
        if len(found_keywords) > 1:
            score += min(0.2, len(found_keywords) * 0.05)
        
        return min(1.0, score)
    
    def is_relevant_opportunity(self, title: str, description: str) -> Tuple[bool, Dict]:
        """Determine if opportunity is relevant based on keywords."""
        all_text = f"{title} {description}"
        
        # Extract keywords
        found_keywords = self.extract_keywords(all_text)
        
        # Check exclusions
        has_exclusions, exclusion_list = self.has_exclusion_keywords(all_text)
        
        # Calculate keyword score
        keyword_score = self.calculate_keyword_score(found_keywords)
        
        # Determine relevance
        is_relevant = (
            len(found_keywords) > 0 and  # Has relevant keywords
            not has_exclusions and       # No exclusion keywords
            keyword_score >= 0.3         # Minimum relevance threshold
        )
        
        result = {
            'is_relevant': is_relevant,
            'found_keywords': found_keywords,
            'keyword_score': keyword_score,
            'has_exclusions': has_exclusions,
            'exclusion_keywords': exclusion_list,
            'keyword_count': len(found_keywords)
        }
        
        return is_relevant, result
    
    def get_keyword_context(self, text: str, keyword: str, context_length: int = 50) -> List[str]:
        """Get context around keyword matches for better understanding."""
        if not text or not keyword:
            return []
        
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        contexts = []
        
        # Find all occurrences of the keyword
        start = 0
        while True:
            pos = text_lower.find(keyword_lower, start)
            if pos == -1:
                break
            
            # Extract context around the keyword
            context_start = max(0, pos - context_length)
            context_end = min(len(text), pos + len(keyword) + context_length)
            context = text[context_start:context_end].strip()
            
            contexts.append(context)
            start = pos + 1
        
        return contexts
    
    def analyze_keyword_density(self, text: str) -> Dict[str, float]:
        """Analyze keyword density in text."""
        if not text:
            return {}
        
        words = text.lower().split()
        total_words = len(words)
        
        if total_words == 0:
            return {}
        
        keyword_counts = {}
        for keyword in self.primary_keywords:
            count = 0
            if ' ' in keyword:
                # Multi-word keyword
                keyword_phrase = keyword.lower()
                count = text.lower().count(keyword_phrase)
            else:
                # Single word keyword
                count = words.count(keyword.lower())
            
            if count > 0:
                density = count / total_words
                keyword_counts[keyword] = density
        
        return keyword_counts
    
    def get_filter_summary(self, opportunities: List[Dict]) -> Dict:
        """Generate summary of keyword filtering results."""
        total_opportunities = len(opportunities)
        relevant_count = 0
        excluded_count = 0
        keyword_stats = {}
        exclusion_stats = {}
        
        for opp in opportunities:
            title = opp.get('title', '')
            description = opp.get('description', '')
            
            is_relevant, result = self.is_relevant_opportunity(title, description)
            
            if is_relevant:
                relevant_count += 1
            
            if result['has_exclusions']:
                excluded_count += 1
            
            # Count keyword occurrences
            for keyword in result['found_keywords']:
                keyword_stats[keyword] = keyword_stats.get(keyword, 0) + 1
            
            # Count exclusion occurrences
            for exclusion in result['exclusion_keywords']:
                exclusion_stats[exclusion] = exclusion_stats.get(exclusion, 0) + 1
        
        return {
            'total_opportunities': total_opportunities,
            'relevant_opportunities': relevant_count,
            'excluded_opportunities': excluded_count,
            'relevance_rate': relevant_count / total_opportunities if total_opportunities > 0 else 0,
            'top_keywords': dict(sorted(keyword_stats.items(), key=lambda x: x[1], reverse=True)[:10]),
            'exclusion_reasons': dict(sorted(exclusion_stats.items(), key=lambda x: x[1], reverse=True)[:5])
        }

