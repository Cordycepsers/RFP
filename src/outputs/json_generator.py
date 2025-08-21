"""
JSON output generator for Proposaland opportunity monitoring.
Creates structured JSON outputs with complete opportunity data and metadata.
"""

import json
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from loguru import logger


class JSONGenerator:
    """Comprehensive JSON output generator with metadata and validation."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_json_output(self, opportunities: List[Dict], filename: str = None) -> str:
        """Generate comprehensive JSON output with metadata."""
        if not filename:
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f"proposaland_opportunities_{date_str}.json"
        
        filepath = self.output_dir / filename
        
        try:
            # Prepare comprehensive output structure
            output_data = {
                'metadata': self._generate_metadata(opportunities),
                'summary': self._generate_summary(opportunities),
                'opportunities': self._process_opportunities(opportunities),
                'analytics': self._generate_analytics(opportunities),
                'configuration': self._get_configuration_summary()
            }
            
            # Write JSON with proper formatting
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=self._json_serializer)
            
            logger.info(f"Generated JSON output: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating JSON output: {e}")
            raise
    
    def _generate_metadata(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """Generate metadata for the JSON output."""
        return {
            'generated_timestamp': datetime.now().isoformat(),
            'generated_date': datetime.now().strftime('%Y-%m-%d'),
            'generated_time': datetime.now().strftime('%H:%M:%S'),
            'system_version': self.config.get('system', {}).get('version', '1.0.0'),
            'total_opportunities': len(opportunities),
            'data_format_version': '1.0',
            'timezone': 'UTC',
            'generator': 'Proposaland Opportunity Monitor'
        }
    
    def _generate_summary(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics."""
        if not opportunities:
            return {
                'total_count': 0,
                'priority_breakdown': {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0},
                'average_score': 0.0,
                'top_organizations': [],
                'top_keywords': []
            }
        
        # Priority breakdown
        priority_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
        total_score = 0
        org_counts = {}
        keyword_counts = {}
        
        for opp in opportunities:
            # Count priorities
            priority = opp.get('priority', 'Low')
            priority_counts[priority] += 1
            
            # Sum scores
            score = opp.get('relevance_score', 0)
            total_score += score
            
            # Count organizations
            org = opp.get('organization', 'Unknown')
            org_counts[org] = org_counts.get(org, 0) + 1
            
            # Count keywords
            for keyword in opp.get('keywords_found', []):
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Calculate averages and top items
        average_score = total_score / len(opportunities)
        top_orgs = sorted(org_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_count': len(opportunities),
            'priority_breakdown': priority_counts,
            'average_score': round(average_score, 3),
            'score_distribution': self._calculate_score_distribution(opportunities),
            'top_organizations': [{'name': org, 'count': count} for org, count in top_orgs],
            'top_keywords': [{'keyword': kw, 'count': count} for kw, count in top_keywords],
            'deadline_analysis': self._analyze_deadlines(opportunities),
            'budget_analysis': self._analyze_budgets(opportunities),
            'reference_number_stats': self._analyze_reference_numbers(opportunities)
        }
    
    def _process_opportunities(self, opportunities: List[Dict]) -> List[Dict[str, Any]]:
        """Process and clean opportunity data for JSON output."""
        processed_opportunities = []
        
        for i, opp in enumerate(opportunities, 1):
            processed_opp = {
                'id': i,
                'title': opp.get('title', ''),
                'description': opp.get('description', ''),
                'organization': opp.get('organization', ''),
                'source_url': opp.get('source_url', ''),
                'location': opp.get('location', ''),
                'budget': {
                    'amount': opp.get('budget'),
                    'currency': opp.get('currency', 'USD'),
                    'formatted': self._format_budget(opp.get('budget'), opp.get('currency', 'USD'))
                },
                'deadline': {
                    'raw': opp.get('deadline'),
                    'formatted': self._format_deadline(opp.get('deadline')),
                    'days_until': self._calculate_days_until_deadline(opp.get('deadline'))
                },
                'reference_number': {
                    'number': opp.get('reference_number', ''),
                    'confidence': opp.get('reference_confidence', 0.0),
                    'has_reference': bool(opp.get('reference_number'))
                },
                'keywords': {
                    'found': opp.get('keywords_found', []),
                    'count': len(opp.get('keywords_found', [])),
                    'primary_match': opp.get('keywords_found', [None])[0] if opp.get('keywords_found') else None
                },
                'scoring': {
                    'relevance_score': opp.get('relevance_score', 0.0),
                    'priority': opp.get('priority', 'Low'),
                    'scoring_details': opp.get('scoring_details', {}),
                    'rank': i
                },
                'extraction': {
                    'extracted_date': opp.get('extracted_date'),
                    'extraction_method': 'automated_scraping',
                    'data_quality': self._assess_data_quality(opp)
                },
                'raw_data': opp.get('raw_data', {})
            }
            
            processed_opportunities.append(processed_opp)
        
        return processed_opportunities
    
    def _generate_analytics(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """Generate advanced analytics and insights."""
        if not opportunities:
            return {}
        
        return {
            'data_quality': self._analyze_data_quality(opportunities),
            'source_performance': self._analyze_source_performance(opportunities),
            'temporal_analysis': self._analyze_temporal_patterns(opportunities),
            'geographic_distribution': self._analyze_geographic_distribution(opportunities),
            'keyword_analysis': self._analyze_keyword_patterns(opportunities),
            'scoring_analysis': self._analyze_scoring_patterns(opportunities)
        }
    
    def _get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of configuration used for this run."""
        return {
            'keywords': {
                'primary': self.config.get('keywords', {}).get('primary', []),
                'exclusions': self.config.get('keywords', {}).get('exclusions', [])
            },
            'geographic_filters': {
                'excluded_countries': self.config.get('geographic_filters', {}).get('excluded_countries', []),
                'included_countries': self.config.get('geographic_filters', {}).get('included_countries', [])
            },
            'budget_filters': self.config.get('budget_filters', {}),
            'scoring_weights': self.config.get('scoring_weights', {}),
            'priority_thresholds': self.config.get('priority_thresholds', {}),
            'target_websites_count': self._count_target_websites()
        }
    
    def _calculate_score_distribution(self, opportunities: List[Dict]) -> Dict[str, int]:
        """Calculate distribution of relevance scores."""
        distribution = {
            '0.0-0.2': 0,
            '0.2-0.4': 0,
            '0.4-0.6': 0,
            '0.6-0.8': 0,
            '0.8-1.0': 0
        }
        
        for opp in opportunities:
            score = opp.get('relevance_score', 0)
            if score < 0.2:
                distribution['0.0-0.2'] += 1
            elif score < 0.4:
                distribution['0.2-0.4'] += 1
            elif score < 0.6:
                distribution['0.4-0.6'] += 1
            elif score < 0.8:
                distribution['0.6-0.8'] += 1
            else:
                distribution['0.8-1.0'] += 1
        
        return distribution
    
    def _analyze_deadlines(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """Analyze deadline patterns."""
        deadlines = []
        urgent_count = 0
        expired_count = 0
        
        for opp in opportunities:
            deadline = opp.get('deadline')
            if deadline:
                days_until = self._calculate_days_until_deadline(deadline)
                if isinstance(days_until, int):
                    deadlines.append(days_until)
                    if days_until < 7:
                        urgent_count += 1
                    elif days_until < 0:
                        expired_count += 1
        
        return {
            'total_with_deadlines': len(deadlines),
            'urgent_opportunities': urgent_count,
            'expired_opportunities': expired_count,
            'average_days_until_deadline': sum(deadlines) / len(deadlines) if deadlines else None,
            'deadline_distribution': {
                'within_week': len([d for d in deadlines if 0 <= d <= 7]),
                'within_month': len([d for d in deadlines if 7 < d <= 30]),
                'within_quarter': len([d for d in deadlines if 30 < d <= 90]),
                'beyond_quarter': len([d for d in deadlines if d > 90])
            }
        }
    
    def _analyze_budgets(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """Analyze budget patterns."""
        budgets = [opp.get('budget') for opp in opportunities if opp.get('budget')]
        
        if not budgets:
            return {
                'total_with_budgets': 0,
                'average_budget': None,
                'median_budget': None,
                'budget_range': None
            }
        
        budgets.sort()
        
        return {
            'total_with_budgets': len(budgets),
            'average_budget': sum(budgets) / len(budgets),
            'median_budget': budgets[len(budgets) // 2],
            'budget_range': {
                'minimum': min(budgets),
                'maximum': max(budgets)
            },
            'budget_distribution': {
                'under_10k': len([b for b in budgets if b < 10000]),
                '10k_50k': len([b for b in budgets if 10000 <= b < 50000]),
                '50k_100k': len([b for b in budgets if 50000 <= b < 100000]),
                '100k_500k': len([b for b in budgets if 100000 <= b < 500000]),
                'over_500k': len([b for b in budgets if b >= 500000])
            }
        }
    
    def _analyze_reference_numbers(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """Analyze reference number patterns."""
        total_with_refs = 0
        high_confidence_refs = 0
        confidence_scores = []
        
        for opp in opportunities:
            if opp.get('reference_number'):
                total_with_refs += 1
                confidence = opp.get('reference_confidence', 0)
                confidence_scores.append(confidence)
                if confidence >= 0.8:
                    high_confidence_refs += 1
        
        return {
            'total_with_reference_numbers': total_with_refs,
            'reference_number_rate': total_with_refs / len(opportunities) if opportunities else 0,
            'high_confidence_references': high_confidence_refs,
            'average_confidence': sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        }
    
    def _analyze_data_quality(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """Analyze overall data quality."""
        quality_scores = []
        complete_records = 0
        
        for opp in opportunities:
            quality = self._assess_data_quality(opp)
            quality_scores.append(quality)
            if quality >= 0.8:
                complete_records += 1
        
        return {
            'average_quality_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'complete_records': complete_records,
            'completeness_rate': complete_records / len(opportunities) if opportunities else 0
        }
    
    def _analyze_source_performance(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """Analyze performance by source."""
        source_stats = {}
        
        for opp in opportunities:
            org = opp.get('organization', 'Unknown')
            if org not in source_stats:
                source_stats[org] = {
                    'count': 0,
                    'total_score': 0,
                    'high_priority': 0,
                    'with_references': 0
                }
            
            stats = source_stats[org]
            stats['count'] += 1
            stats['total_score'] += opp.get('relevance_score', 0)
            
            if opp.get('priority') in ['Critical', 'High']:
                stats['high_priority'] += 1
            
            if opp.get('reference_number'):
                stats['with_references'] += 1
        
        # Calculate averages
        for org, stats in source_stats.items():
            stats['average_score'] = stats['total_score'] / stats['count']
            stats['high_priority_rate'] = stats['high_priority'] / stats['count']
            stats['reference_rate'] = stats['with_references'] / stats['count']
        
        return source_stats
    
    def _analyze_temporal_patterns(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """Analyze temporal patterns in opportunities."""
        # This would analyze patterns over time if we had historical data
        return {
            'extraction_date': datetime.now().isoformat(),
            'opportunities_by_urgency': self._categorize_by_urgency(opportunities)
        }
    
    def _analyze_geographic_distribution(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """Analyze geographic distribution of opportunities."""
        location_counts = {}
        
        for opp in opportunities:
            location = opp.get('location', 'Unknown')
            location_counts[location] = location_counts.get(location, 0) + 1
        
        return {
            'total_locations': len(location_counts),
            'location_distribution': dict(sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:15])
        }
    
    def _analyze_keyword_patterns(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """Analyze keyword usage patterns."""
        keyword_combinations = {}
        single_keywords = {}
        
        for opp in opportunities:
            keywords = opp.get('keywords_found', [])
            
            # Count single keywords
            for keyword in keywords:
                single_keywords[keyword] = single_keywords.get(keyword, 0) + 1
            
            # Count keyword combinations
            if len(keywords) > 1:
                combo = ', '.join(sorted(keywords))
                keyword_combinations[combo] = keyword_combinations.get(combo, 0) + 1
        
        return {
            'single_keyword_frequency': dict(sorted(single_keywords.items(), key=lambda x: x[1], reverse=True)[:10]),
            'keyword_combinations': dict(sorted(keyword_combinations.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def _analyze_scoring_patterns(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """Analyze scoring patterns and component contributions."""
        component_scores = {}
        
        for opp in opportunities:
            scoring_details = opp.get('scoring_details', {})
            components = scoring_details.get('component_scores', {})
            
            for component, score in components.items():
                if component not in component_scores:
                    component_scores[component] = []
                component_scores[component].append(score)
        
        # Calculate averages for each component
        component_averages = {}
        for component, scores in component_scores.items():
            component_averages[component] = sum(scores) / len(scores) if scores else 0
        
        return {
            'component_averages': component_averages,
            'scoring_distribution': self._calculate_score_distribution(opportunities)
        }
    
    def _assess_data_quality(self, opportunity: Dict) -> float:
        """Assess data quality for a single opportunity."""
        quality_score = 0.0
        max_score = 7.0  # Total possible points
        
        # Title (required)
        if opportunity.get('title'):
            quality_score += 1.0
        
        # Description
        if opportunity.get('description'):
            quality_score += 1.0
        
        # Organization
        if opportunity.get('organization'):
            quality_score += 1.0
        
        # Source URL
        if opportunity.get('source_url'):
            quality_score += 1.0
        
        # Deadline
        if opportunity.get('deadline'):
            quality_score += 1.0
        
        # Budget
        if opportunity.get('budget'):
            quality_score += 1.0
        
        # Reference number
        if opportunity.get('reference_number'):
            quality_score += 1.0
        
        return quality_score / max_score
    
    def _categorize_by_urgency(self, opportunities: List[Dict]) -> Dict[str, int]:
        """Categorize opportunities by urgency."""
        urgency_categories = {
            'immediate': 0,  # < 3 days
            'urgent': 0,     # 3-7 days
            'moderate': 0,   # 1-4 weeks
            'low': 0,        # > 4 weeks
            'unknown': 0     # No deadline
        }
        
        for opp in opportunities:
            days_until = self._calculate_days_until_deadline(opp.get('deadline'))
            
            if days_until is None:
                urgency_categories['unknown'] += 1
            elif days_until < 3:
                urgency_categories['immediate'] += 1
            elif days_until <= 7:
                urgency_categories['urgent'] += 1
            elif days_until <= 28:
                urgency_categories['moderate'] += 1
            else:
                urgency_categories['low'] += 1
        
        return urgency_categories
    
    def _count_target_websites(self) -> int:
        """Count total target websites in configuration."""
        total = 0
        for priority_group in ['high_priority', 'medium_priority', 'low_priority']:
            websites = self.config.get('target_websites', {}).get(priority_group, [])
            total += len(websites)
        return total
    
    def _format_budget(self, budget, currency: str) -> str:
        """Format budget for display."""
        if not budget:
            return 'Not specified'
        
        return f"{currency} {budget:,.2f}"
    
    def _format_deadline(self, deadline) -> str:
        """Format deadline for display."""
        if not deadline:
            return 'Not specified'
        
        if isinstance(deadline, str):
            try:
                deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            except:
                return deadline
        
        if isinstance(deadline, datetime):
            return deadline.strftime('%Y-%m-%d %H:%M:%S')
        
        return str(deadline)
    
    def _calculate_days_until_deadline(self, deadline):
        """Calculate days until deadline."""
        if not deadline:
            return None
        
        if isinstance(deadline, str):
            try:
                deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            except:
                return None
        
        if isinstance(deadline, datetime):
            now = datetime.now()
            if deadline.tzinfo:
                now = now.replace(tzinfo=deadline.tzinfo)
            
            return (deadline - now).days
        
        return None
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

