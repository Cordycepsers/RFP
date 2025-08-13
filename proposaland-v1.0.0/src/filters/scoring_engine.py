"""
Comprehensive scoring engine for Proposaland opportunity monitoring.
Combines multiple criteria to score and prioritize opportunities.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from loguru import logger

from .keyword_filter import KeywordFilter
from .geographic_filter import GeographicFilter


class ScoringEngine:
    """Advanced scoring engine with multi-criteria evaluation."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.weights = config.get('scoring_weights', {})
        self.priority_thresholds = config.get('priority_thresholds', {})
        
        # Initialize filters
        self.keyword_filter = KeywordFilter(config)
        self.geographic_filter = GeographicFilter(config)
        
        # Budget range for scoring
        self.min_budget = config.get('budget_filters', {}).get('min_budget', 5000)
        self.max_budget = config.get('budget_filters', {}).get('max_budget', 500000)
        
    def score_opportunity(self, opportunity: Dict) -> Tuple[float, Dict]:
        """Score an opportunity based on multiple criteria."""
        title = opportunity.get('title', '')
        description = opportunity.get('description', '')
        organization = opportunity.get('organization', '')
        budget = opportunity.get('budget')
        deadline = opportunity.get('deadline')
        location = opportunity.get('location', '')
        reference_number = opportunity.get('reference_number', '')
        reference_confidence = opportunity.get('reference_confidence', 0.0)
        
        scores = {}
        total_score = 0.0
        
        # 1. Keyword Match Score (25%)
        keyword_score = self._calculate_keyword_score(title, description)
        scores['keyword_match'] = keyword_score
        total_score += keyword_score * self.weights.get('keyword_match', 0.25)
        
        # 2. Budget Range Score (20%)
        budget_score = self._calculate_budget_score(budget)
        scores['budget_range'] = budget_score
        total_score += budget_score * self.weights.get('budget_range', 0.20)
        
        # 3. Deadline Urgency Score (15%)
        urgency_score = self._calculate_urgency_score(deadline)
        scores['deadline_urgency'] = urgency_score
        total_score += urgency_score * self.weights.get('deadline_urgency', 0.15)
        
        # 4. Source Priority Score (15%)
        source_score = self._calculate_source_score(organization)
        scores['source_priority'] = source_score
        total_score += source_score * self.weights.get('source_priority', 0.15)
        
        # 5. Geographic Fit Score (10%)
        geographic_score = self._calculate_geographic_score(title, description, location)
        scores['geographic_fit'] = geographic_score
        total_score += geographic_score * self.weights.get('geographic_fit', 0.10)
        
        # 6. Sector Relevance Score (10%)
        sector_score = self._calculate_sector_score(title, description, organization)
        scores['sector_relevance'] = sector_score
        total_score += sector_score * self.weights.get('sector_relevance', 0.10)
        
        # 7. Reference Number Bonus (5%)
        reference_bonus = self._calculate_reference_bonus(reference_number, reference_confidence)
        scores['reference_number_bonus'] = reference_bonus
        total_score += reference_bonus * self.weights.get('reference_number_bonus', 0.05)
        
        # Ensure score is within bounds
        final_score = max(0.0, min(1.0, total_score))
        
        scoring_details = {
            'final_score': final_score,
            'component_scores': scores,
            'weights_used': self.weights
        }
        
        return final_score, scoring_details
    
    def _calculate_keyword_score(self, title: str, description: str) -> float:
        """Calculate keyword relevance score."""
        is_relevant, result = self.keyword_filter.is_relevant_opportunity(title, description)
        
        if not is_relevant:
            return 0.0
        
        return result['keyword_score']
    
    def _calculate_budget_score(self, budget: float) -> float:
        """Calculate budget range score."""
        if not budget or budget <= 0:
            return 0.5  # Neutral score for unknown budget
        
        # Check if within acceptable range
        if budget < self.min_budget:
            return 0.2  # Too small
        elif budget > self.max_budget:
            return 0.3  # Too large
        
        # Calculate score based on position within range
        optimal_budget = (self.min_budget + self.max_budget) / 2
        distance_from_optimal = abs(budget - optimal_budget)
        max_distance = self.max_budget - self.min_budget
        
        # Score decreases as distance from optimal increases
        score = 1.0 - (distance_from_optimal / max_distance)
        
        return max(0.5, score)  # Minimum score of 0.5 for budgets in range
    
    def _calculate_urgency_score(self, deadline) -> float:
        """Calculate deadline urgency score."""
        if not deadline:
            return 0.5  # Neutral score for unknown deadline
        
        # Convert string deadline to datetime if needed
        if isinstance(deadline, str):
            try:
                deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            except:
                return 0.5
        
        if not isinstance(deadline, datetime):
            return 0.5
        
        now = datetime.now()
        if deadline.tzinfo:
            now = now.replace(tzinfo=deadline.tzinfo)
        
        days_until_deadline = (deadline - now).days
        
        if days_until_deadline < 0:
            return 0.0  # Already passed
        elif days_until_deadline < 7:
            return 1.0  # Very urgent
        elif days_until_deadline < 30:
            return 0.8  # Urgent
        elif days_until_deadline < 90:
            return 0.6  # Moderate urgency
        else:
            return 0.4  # Low urgency
    
    def _calculate_source_score(self, organization: str) -> float:
        """Calculate source priority score."""
        if not organization:
            return 0.5
        
        org_lower = organization.lower()
        
        # Get priority from configuration
        all_websites = []
        for priority_group in ['high_priority', 'medium_priority', 'low_priority']:
            websites = self.config.get('target_websites', {}).get(priority_group, [])
            all_websites.extend(websites)
        
        for website in all_websites:
            if website['name'].lower() in org_lower or org_lower in website['name'].lower():
                return website.get('priority', 0.5)
        
        # Default score for unknown sources
        return 0.5
    
    def _calculate_geographic_score(self, title: str, description: str, location: str) -> float:
        """Calculate geographic fit score."""
        is_accepted, result = self.geographic_filter.filter_opportunity(title, description, location)
        
        if not is_accepted:
            return 0.0  # Excluded location
        
        return result['geographic_score']
    
    def _calculate_sector_score(self, title: str, description: str, organization: str) -> float:
        """Calculate sector relevance score."""
        all_text = f"{title} {description} {organization}".lower()
        
        # Development sector indicators
        development_indicators = [
            'development', 'humanitarian', 'ngo', 'non-profit', 'charity',
            'aid', 'relief', 'poverty', 'health', 'education', 'environment',
            'sustainability', 'climate', 'gender', 'human rights', 'peace',
            'governance', 'democracy', 'capacity building', 'community'
        ]
        
        # Multimedia/creative sector indicators
        creative_indicators = [
            'creative', 'agency', 'studio', 'production', 'marketing',
            'advertising', 'branding', 'digital', 'technology', 'innovation'
        ]
        
        development_score = sum(1 for indicator in development_indicators if indicator in all_text)
        creative_score = sum(1 for indicator in creative_indicators if indicator in all_text)
        
        # Normalize scores
        max_development = len(development_indicators)
        max_creative = len(creative_indicators)
        
        dev_normalized = min(1.0, development_score / max_development * 3)  # Boost development sector
        creative_normalized = min(1.0, creative_score / max_creative * 2)
        
        # Combine scores (favor development sector)
        combined_score = (dev_normalized * 0.7) + (creative_normalized * 0.3)
        
        return min(1.0, combined_score)
    
    def _calculate_reference_bonus(self, reference_number: str, confidence: float) -> float:
        """Calculate reference number bonus score."""
        if not reference_number:
            return 0.0
        
        # Base bonus for having a reference number
        base_bonus = 0.5
        
        # Additional bonus based on confidence
        confidence_bonus = confidence * 0.5
        
        return min(1.0, base_bonus + confidence_bonus)
    
    def classify_priority(self, score: float) -> str:
        """Classify opportunity priority based on score."""
        if score >= self.priority_thresholds.get('critical', 0.8):
            return 'Critical'
        elif score >= self.priority_thresholds.get('high', 0.6):
            return 'High'
        elif score >= self.priority_thresholds.get('medium', 0.4):
            return 'Medium'
        else:
            return 'Low'
    
    def score_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """Score a list of opportunities and add scoring information."""
        scored_opportunities = []
        
        for opp in opportunities:
            try:
                score, details = self.score_opportunity(opp)
                priority = self.classify_priority(score)
                
                # Add scoring information to opportunity
                opp_copy = opp.copy()
                opp_copy['relevance_score'] = score
                opp_copy['priority'] = priority
                opp_copy['scoring_details'] = details
                
                scored_opportunities.append(opp_copy)
                
            except Exception as e:
                logger.warning(f"Error scoring opportunity '{opp.get('title', 'Unknown')}': {e}")
                # Add with default low score
                opp_copy = opp.copy()
                opp_copy['relevance_score'] = 0.1
                opp_copy['priority'] = 'Low'
                opp_copy['scoring_details'] = {'error': str(e)}
                scored_opportunities.append(opp_copy)
        
        # Sort by score (highest first)
        scored_opportunities.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return scored_opportunities
    
    def generate_scoring_report(self, opportunities: List[Dict]) -> Dict:
        """Generate comprehensive scoring report."""
        if not opportunities:
            return {'error': 'No opportunities to analyze'}
        
        total_count = len(opportunities)
        priority_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
        score_distribution = {'0.0-0.2': 0, '0.2-0.4': 0, '0.4-0.6': 0, '0.6-0.8': 0, '0.8-1.0': 0}
        
        total_score = 0
        component_averages = {}
        
        for opp in opportunities:
            score = opp.get('relevance_score', 0)
            priority = opp.get('priority', 'Low')
            
            # Count priorities
            priority_counts[priority] += 1
            
            # Count score distribution
            if score < 0.2:
                score_distribution['0.0-0.2'] += 1
            elif score < 0.4:
                score_distribution['0.2-0.4'] += 1
            elif score < 0.6:
                score_distribution['0.4-0.6'] += 1
            elif score < 0.8:
                score_distribution['0.6-0.8'] += 1
            else:
                score_distribution['0.8-1.0'] += 1
            
            total_score += score
            
            # Aggregate component scores
            scoring_details = opp.get('scoring_details', {})
            component_scores = scoring_details.get('component_scores', {})
            
            for component, comp_score in component_scores.items():
                if component not in component_averages:
                    component_averages[component] = []
                component_averages[component].append(comp_score)
        
        # Calculate averages
        average_score = total_score / total_count
        for component in component_averages:
            component_averages[component] = sum(component_averages[component]) / len(component_averages[component])
        
        return {
            'total_opportunities': total_count,
            'average_score': average_score,
            'priority_distribution': priority_counts,
            'score_distribution': score_distribution,
            'component_averages': component_averages,
            'top_opportunities': opportunities[:5],  # Top 5 by score
            'scoring_weights': self.weights,
            'priority_thresholds': self.priority_thresholds
        }

