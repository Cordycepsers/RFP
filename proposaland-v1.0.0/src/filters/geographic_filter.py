"""
Geographic filtering system for Proposaland opportunity monitoring.
Handles location-based exclusions and geographic relevance scoring.
"""

import re
from typing import List, Dict, Set, Tuple, Optional
from loguru import logger


class GeographicFilter:
    """Geographic filtering with location extraction and exclusion logic."""
    
    def __init__(self, config: Dict):
        self.excluded_countries = [country.lower() for country in config.get('geographic_filters', {}).get('excluded_countries', [])]
        self.included_countries = [country.lower() for country in config.get('geographic_filters', {}).get('included_countries', [])]
        self.excluded_regions = [region.lower() for region in config.get('geographic_filters', {}).get('excluded_regions', [])]
        
        # Initialize country aliases and variations
        self.country_aliases = self._initialize_country_aliases()
        
    def _initialize_country_aliases(self) -> Dict[str, List[str]]:
        """Initialize country aliases and variations for better matching."""
        return {
            'india': ['india', 'indian', 'new delhi', 'mumbai', 'bangalore', 'delhi', 'kolkata', 'chennai'],
            'pakistan': ['pakistan', 'pakistani', 'islamabad', 'karachi', 'lahore', 'rawalpindi'],
            'china': ['china', 'chinese', 'beijing', 'shanghai', 'guangzhou', 'shenzhen', 'prc', "people's republic"],
            'bangladesh': ['bangladesh', 'bangladeshi', 'dhaka', 'chittagong'],
            'sri lanka': ['sri lanka', 'sri lankan', 'colombo', 'kandy'],
            'myanmar': ['myanmar', 'burma', 'burmese', 'yangon', 'naypyidaw'],
            'thailand': ['thailand', 'thai', 'bangkok', 'chiang mai'],
            'vietnam': ['vietnam', 'vietnamese', 'hanoi', 'ho chi minh', 'saigon'],
            'cambodia': ['cambodia', 'cambodian', 'phnom penh'],
            'laos': ['laos', 'lao', 'vientiane'],
            'malaysia': ['malaysia', 'malaysian', 'kuala lumpur', 'penang'],
            'indonesia': ['indonesia', 'indonesian', 'jakarta', 'bali', 'surabaya'],
            'philippines': ['philippines', 'filipino', 'manila', 'cebu'],
            'singapore': ['singapore', 'singaporean'],
            'nepal': ['nepal', 'nepalese', 'kathmandu']  # Included country
        }
    
    def extract_locations(self, text: str) -> List[str]:
        """Extract location mentions from text."""
        if not text:
            return []
        
        text_lower = text.lower()
        found_locations = []
        
        # Check for country names and aliases
        for country, aliases in self.country_aliases.items():
            for alias in aliases:
                if alias in text_lower:
                    found_locations.append(country)
                    break  # Avoid duplicates for the same country
        
        # Look for additional location patterns
        location_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*([A-Z]{2,3})\b',  # City, Country code
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:office|country|region)\b',  # Location office/country
            r'\b(?:based\s+in|located\s+in|office\s+in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'  # Based in location
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    location = match[0].lower().strip()
                else:
                    location = match.lower().strip()
                
                if location and location not in found_locations:
                    found_locations.append(location)
        
        return found_locations
    
    def is_excluded_location(self, location: str) -> Tuple[bool, str]:
        """Check if a location is in the exclusion list."""
        location_lower = location.lower()
        
        # Check direct exclusions
        if location_lower in self.excluded_countries:
            return True, f"Excluded country: {location}"
        
        # Check aliases
        for excluded_country in self.excluded_countries:
            if excluded_country in self.country_aliases:
                aliases = self.country_aliases[excluded_country]
                if location_lower in aliases:
                    return True, f"Excluded country (alias): {location} -> {excluded_country}"
        
        # Check regional exclusions
        for excluded_region in self.excluded_regions:
            if excluded_region in location_lower:
                return True, f"Excluded region: {location} -> {excluded_region}"
        
        return False, ""
    
    def is_included_location(self, location: str) -> bool:
        """Check if a location is explicitly included (overrides exclusions)."""
        location_lower = location.lower()
        
        # Check direct inclusions
        if location_lower in self.included_countries:
            return True
        
        # Check aliases for included countries
        for included_country in self.included_countries:
            if included_country in self.country_aliases:
                aliases = self.country_aliases[included_country]
                if location_lower in aliases:
                    return True
        
        return False
    
    def filter_opportunity(self, title: str, description: str, location: str = "") -> Tuple[bool, Dict]:
        """Filter opportunity based on geographic criteria."""
        all_text = f"{title} {description} {location}"
        
        # Extract all location mentions
        found_locations = self.extract_locations(all_text)
        
        # Check for exclusions and inclusions
        excluded_locations = []
        included_locations = []
        exclusion_reasons = []
        
        for loc in found_locations:
            # Check if explicitly included (overrides exclusions)
            if self.is_included_location(loc):
                included_locations.append(loc)
            else:
                # Check if excluded
                is_excluded, reason = self.is_excluded_location(loc)
                if is_excluded:
                    excluded_locations.append(loc)
                    exclusion_reasons.append(reason)
        
        # Determine if opportunity should be accepted
        # Accept if: no excluded locations OR has included locations that override exclusions
        is_accepted = len(excluded_locations) == 0 or len(included_locations) > 0
        
        # Calculate geographic relevance score
        geographic_score = self._calculate_geographic_score(found_locations, excluded_locations, included_locations)
        
        result = {
            'is_accepted': is_accepted,
            'found_locations': found_locations,
            'excluded_locations': excluded_locations,
            'included_locations': included_locations,
            'exclusion_reasons': exclusion_reasons,
            'geographic_score': geographic_score,
            'location_count': len(found_locations)
        }
        
        return is_accepted, result
    
    def _calculate_geographic_score(self, found_locations: List[str], 
                                  excluded_locations: List[str], 
                                  included_locations: List[str]) -> float:
        """Calculate geographic relevance score."""
        if not found_locations:
            return 0.5  # Neutral score if no location information
        
        # Start with base score
        score = 0.5
        
        # Penalty for excluded locations
        if excluded_locations:
            exclusion_penalty = min(0.4, len(excluded_locations) * 0.2)
            score -= exclusion_penalty
        
        # Bonus for included locations
        if included_locations:
            inclusion_bonus = min(0.3, len(included_locations) * 0.15)
            score += inclusion_bonus
        
        # Bonus for global/international opportunities (no specific location)
        global_indicators = ['global', 'international', 'worldwide', 'remote', 'virtual']
        text_to_check = ' '.join(found_locations).lower()
        
        if any(indicator in text_to_check for indicator in global_indicators):
            score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def analyze_location_patterns(self, opportunities: List[Dict]) -> Dict:
        """Analyze location patterns across opportunities."""
        location_stats = {}
        exclusion_stats = {}
        total_opportunities = len(opportunities)
        accepted_count = 0
        
        for opp in opportunities:
            title = opp.get('title', '')
            description = opp.get('description', '')
            location = opp.get('location', '')
            
            is_accepted, result = self.filter_opportunity(title, description, location)
            
            if is_accepted:
                accepted_count += 1
            
            # Count location occurrences
            for loc in result['found_locations']:
                location_stats[loc] = location_stats.get(loc, 0) + 1
            
            # Count exclusion reasons
            for reason in result['exclusion_reasons']:
                exclusion_stats[reason] = exclusion_stats.get(reason, 0) + 1
        
        return {
            'total_opportunities': total_opportunities,
            'accepted_opportunities': accepted_count,
            'acceptance_rate': accepted_count / total_opportunities if total_opportunities > 0 else 0,
            'location_distribution': dict(sorted(location_stats.items(), key=lambda x: x[1], reverse=True)[:15]),
            'exclusion_reasons': dict(sorted(exclusion_stats.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def get_location_recommendations(self, opportunities: List[Dict]) -> Dict:
        """Get recommendations for location filtering improvements."""
        analysis = self.analyze_location_patterns(opportunities)
        
        recommendations = []
        
        # Check for frequently excluded locations
        exclusion_reasons = analysis['exclusion_reasons']
        if exclusion_reasons:
            most_excluded = max(exclusion_reasons.items(), key=lambda x: x[1])
            if most_excluded[1] > len(opportunities) * 0.1:  # More than 10% of opportunities
                recommendations.append(f"Consider reviewing exclusion for: {most_excluded[0]} (affects {most_excluded[1]} opportunities)")
        
        # Check for new locations that might need classification
        location_dist = analysis['location_distribution']
        unclassified_locations = []
        
        for location, count in location_dist.items():
            if location not in [alias for aliases in self.country_aliases.values() for alias in aliases]:
                if count > 2:  # Appears in multiple opportunities
                    unclassified_locations.append((location, count))
        
        if unclassified_locations:
            recommendations.append(f"New locations to classify: {unclassified_locations[:5]}")
        
        return {
            'analysis': analysis,
            'recommendations': recommendations
        }

