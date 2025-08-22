"""
Keyword filtering system for Proposaland opportunity monitoring.
Handles multimedia/creative keyword matching and exclusion filtering.
"""

import re
import difflib
from functools import lru_cache
from typing import List, Dict, Set, Tuple
from loguru import logger


class KeywordFilter:
    """Advanced keyword filtering with fuzzy matching and context analysis."""
    
    def __init__(self, config: Dict):
        self.primary_keywords = [kw.lower() for kw in config.get('keywords', {}).get('primary', [])]
        self.exclusion_keywords = [kw.lower() for kw in config.get('keywords', {}).get('exclusions', [])]
        self.keyword_weights = self._initialize_keyword_weights()
        # Precompile simple boundary regexes for speed
        self._compiled_words = {kw: re.compile(rf"\b{re.escape(kw)}\b", re.I) for kw in self.primary_keywords if ' ' not in kw}
        self._compiled_phrases = {kw: re.compile(rf"\b{re.escape(kw)}\b", re.I) for kw in self.primary_keywords if ' ' in kw}
        
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
    
    @lru_cache(maxsize=4096)
    def _normalize(self, s: str) -> str:
        s = s.lower()
        s = re.sub(r"[^\w\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _word_boundary_match(self, keyword: str, text: str) -> bool:
        patt = self._compiled_phrases.get(keyword) if ' ' in keyword else self._compiled_words.get(keyword)
        if patt and patt.search(text):
            return True
        return re.search(rf"\b{re.escape(keyword)}\b", text, re.I) is not None

    def _plural_variants(self, token: str) -> List[str]:
        variants = {token}
        if token.endswith('ies'):
            variants.add(token[:-3] + 'y')
        if token.endswith('es'):
            variants.add(token[:-2])
        if token.endswith('s'):
            variants.add(token[:-1])
        return list(variants)

    def _keyword_matches(self, keyword: str, text: str) -> bool:
        """Fuzzy/boundary-aware matching for single tokens and phrases."""
        norm_text = self._normalize(text)
        norm_kw = self._normalize(keyword)
        
        # Exact word/phrase boundary
        if self._word_boundary_match(norm_kw, norm_text):
            return True
        
        # Phrase: sliding window fuzzy
        if ' ' in norm_kw:
            kw_tokens = norm_kw.split()
            tks = norm_text.split()
            n = len(kw_tokens)
            if re.search(rf"\b{re.escape(norm_kw)}\b", norm_text):
                return True
            for i in range(0, max(0, len(tks) - n + 1)):
                window = " ".join(tks[i:i+n])
                if difflib.SequenceMatcher(None, window, norm_kw).ratio() >= 0.88:
                    return True
            return False
        
        # Single token: plural variants and fuzzy per token
        for v in self._plural_variants(norm_kw):
            if re.search(rf"\b{re.escape(v)}\b", norm_text):
                return True
        for tok in norm_text.split():
            if len(tok) < 3 or tok[0] != norm_kw[0]:
                continue
            if difflib.SequenceMatcher(None, tok, norm_kw).ratio() >= 0.88:
                return True
        return False
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract matching keywords from text with fuzzy matching."""
        if not text:
            return []
        text_lower = text.lower()
        found_keywords = []
        seen = set()
        for keyword in self.primary_keywords:
            if keyword in seen:
                continue
            if self._keyword_matches(keyword, text_lower):
                found_keywords.append(keyword)
                seen.add(keyword)
        return found_keywords
    
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
        """Calculate relevance score based on found keywords (normalized)."""
        if not found_keywords:
            return 0.0
        total_weight = sum(self.keyword_weights.get(k, 0.5) for k in found_keywords)
        max_possible = sum(self.keyword_weights.values())
        score = min(1.0, total_weight / max_possible)
        if len(found_keywords) > 1:
            score = min(1.0, score + min(0.2, len(found_keywords) * 0.05))
        return score

    def score_keywords(self, text: str) -> Tuple[float, List[str]]:
        """Convenience: extract and score in one call."""
        kws = self.extract_keywords(text)
        return self.calculate_keyword_score(kws), kws
    
    def is_relevant_opportunity(self, title: str, description: str) -> Tuple[bool, Dict]:
        """Determine if opportunity is relevant based on keywords."""
        all_text = f"{title} {description}"
        
        found_keywords = self.extract_keywords(all_text)
        has_exclusions, exclusion_list = self.has_exclusion_keywords(all_text)
        keyword_score = self.calculate_keyword_score(found_keywords)
        
        is_relevant = (
            len(found_keywords) > 0 and
            not has_exclusions and
            keyword_score >= 0.3
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
        
        start = 0
        while True:
            pos = text_lower.find(keyword_lower, start)
            if pos == -1:
                break
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
                count = text.lower().count(keyword.lower())
            else:
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
            for keyword in result['found_keywords']:
                keyword_stats[keyword] = keyword_stats.get(keyword, 0) + 1
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

