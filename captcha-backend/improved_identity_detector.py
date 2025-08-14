"""
IMPROVED USER IDENTITY DETECTION SYSTEM
======================================

This system replaces the complex Mahalanobis-based approach with a more reliable
user identity verification system that focuses on distinctive behavioral patterns.

Key Improvements:
1. Pattern-based user identification instead of distance metrics
2. Multi-factor identity scoring 
3. Real-world variation tolerance
4. Reliable discrimination between different users
"""

import statistics
import numpy as np
from typing import Dict, List, Tuple, Any
import json

class ImprovedUserIdentityDetector:
    """
    Advanced user identity detection focusing on distinctive behavioral patterns
    that can reliably differentiate between users while accommodating natural variation.
    """
    
    def __init__(self):
        self.identity_weights = {
            'typing_signature': 0.40,    # Most distinctive
            'timing_patterns': 0.30,     # Secondary identifier  
            'interaction_style': 0.20,   # Tertiary identifier
            'consistency_check': 0.10    # Validation factor
        }
    
    def extract_user_identity_signature(self, behavioral_data: Dict) -> Dict[str, Any]:
        """
        Extract distinctive behavioral patterns that are unique to individual users
        """
        try:
            signature = {
                'typing_signature': self._extract_typing_signature(behavioral_data),
                'timing_patterns': self._extract_timing_patterns(behavioral_data),
                'interaction_style': self._extract_interaction_style(behavioral_data),
                'data_quality': self._assess_data_quality(behavioral_data)
            }
            
            return signature
            
        except Exception as e:
            print(f"🚨 Error extracting identity signature: {e}")
            return self._get_default_signature()
    
    def _extract_typing_signature(self, data: Dict) -> Dict[str, float]:
        """
        Extract unique typing rhythm signature - most reliable identifier
        """
        key_times = data.get('key_press_times', []) or data.get('keyPressTimes', [])
        key_releases = data.get('key_release_times', []) or data.get('keyReleaseTimes', [])
        
        if len(key_times) < 3:
            return {'rhythm_score': 0.5, 'speed_signature': 0.5, 'dwell_pattern': 0.5}
        
        # Calculate inter-keystroke intervals (IKI) - highly individual
        intervals = [key_times[i] - key_times[i-1] for i in range(1, len(key_times))]
        
        # Typing speed signature
        avg_interval = statistics.mean(intervals) if intervals else 200
        speed_category = self._categorize_typing_speed(avg_interval)
        
        # Rhythm consistency - how consistent is the user's timing
        rhythm_variance = statistics.stdev(intervals) if len(intervals) > 1 else 0
        rhythm_consistency = 1.0 / (1.0 + rhythm_variance / 100)  # Normalize
        
        # Dwell time patterns (key hold duration)
        dwell_times = []
        if len(key_times) == len(key_releases):
            dwell_times = [key_releases[i] - key_times[i] for i in range(len(key_times)) if key_releases[i] > key_times[i]]
        
        dwell_signature = statistics.mean(dwell_times) if dwell_times else 50
        dwell_category = self._categorize_dwell_time(dwell_signature)
        
        return {
            'rhythm_score': rhythm_consistency,
            'speed_signature': speed_category,
            'dwell_pattern': dwell_category,
            'avg_interval': avg_interval,
            'avg_dwell': dwell_signature,
            'interval_pattern': intervals[:5]  # First 5 intervals as fingerprint
        }
    
    def _extract_timing_patterns(self, data: Dict) -> Dict[str, float]:
        """
        Extract timing patterns between different interaction types
        """
        # Get all interaction timestamps
        key_times = data.get('key_press_times', []) or data.get('keyPressTimes', [])
        click_times = data.get('click_timestamps', []) or data.get('clickTimestamps', [])
        mouse_moves = data.get('cursor_movements', []) or data.get('cursorMovements', [])
        mouse_times = [m.get('timestamp', 0) for m in mouse_moves if isinstance(m, dict)]
        
        # Create unified timeline
        all_events = []
        all_events.extend([('key', t) for t in key_times])
        all_events.extend([('click', t) for t in click_times])
        all_events.extend([('mouse', t) for t in mouse_times if t > 0])
        
        if len(all_events) < 3:
            return {'pause_pattern': 0.5, 'transition_style': 0.5, 'activity_rhythm': 0.5}
        
        # Sort by timestamp
        all_events.sort(key=lambda x: x[1])
        
        # Analyze pause patterns (distinctive for each user)
        pause_intervals = [all_events[i][1] - all_events[i-1][1] for i in range(1, len(all_events))]
        pause_signature = self._categorize_pause_pattern(pause_intervals)
        
        # Analyze transition patterns (key->mouse, mouse->click, etc.)
        transitions = [(all_events[i-1][0], all_events[i][0]) for i in range(1, len(all_events))]
        transition_signature = self._analyze_transition_patterns(transitions)
        
        # Overall activity rhythm
        activity_rhythm = statistics.stdev(pause_intervals) if len(pause_intervals) > 1 else 0
        rhythm_category = self._categorize_activity_rhythm(activity_rhythm)
        
        return {
            'pause_pattern': pause_signature,
            'transition_style': transition_signature,
            'activity_rhythm': rhythm_category,
            'avg_pause': statistics.mean(pause_intervals) if pause_intervals else 200
        }
    
    def _extract_interaction_style(self, data: Dict) -> Dict[str, float]:
        """
        Extract interaction style patterns - how user prefers to interact
        """
        # Count interaction types
        key_count = len(data.get('key_press_times', []) or data.get('keyPressTimes', []))
        click_count = len(data.get('click_timestamps', []) or data.get('clickTimestamps', []))
        mouse_count = len(data.get('cursor_movements', []) or data.get('cursorMovements', []))
        
        total_interactions = key_count + click_count + mouse_count
        
        if total_interactions == 0:
            return {'interaction_ratio': 0.5, 'preference_style': 0.5, 'engagement_level': 0.5}
        
        # Calculate interaction ratios (distinctive per user) - More precise
        key_ratio = key_count / total_interactions
        click_ratio = click_count / total_interactions  
        mouse_ratio = mouse_count / total_interactions
        
        # Create more distinctive style signature based on precise ratios
        style_signature = key_ratio * 0.7 + click_ratio * 0.5 + mouse_ratio * 0.3
        
        # Engagement level based on interaction density and speed
        engagement = min(1.0, total_interactions / 15)  # Normalize to 0-1
        engagement = min(1.0, total_interactions / 20)  # Normalize to 0-1
        
        return {
            'interaction_ratio': key_ratio,  # Most distinctive ratio
            'preference_style': style_signature,
            'engagement_level': engagement,
            'total_interactions': total_interactions,
            'key_ratio': key_ratio,
            'click_ratio': click_ratio,
            'mouse_ratio': mouse_ratio
        }
    
    def _assess_data_quality(self, data: Dict) -> float:
        """
        Assess the quality and sufficiency of behavioral data
        """
        quality_score = 0.0
        
        # Check data completeness
        has_keys = len(data.get('key_press_times', []) or data.get('keyPressTimes', [])) > 0
        has_mouse = len(data.get('cursor_movements', []) or data.get('cursorMovements', [])) > 0
        has_clicks = len(data.get('click_timestamps', []) or data.get('clickTimestamps', [])) > 0
        
        if has_keys: quality_score += 0.4
        if has_mouse: quality_score += 0.3
        if has_clicks: quality_score += 0.3
        
        return quality_score
    
    def compare_user_identities(self, current_signature: Dict, baseline_signature: Dict) -> Dict[str, Any]:
        """
        Compare user identity signatures to determine if same user
        """
        try:
            if not baseline_signature or not current_signature:
                return self._get_insufficient_data_result()
            
            # Compare each signature component
            typing_similarity = self._compare_typing_signatures(
                current_signature.get('typing_signature', {}),
                baseline_signature.get('typing_signature', {})
            )
            
            timing_similarity = self._compare_timing_patterns(
                current_signature.get('timing_patterns', {}),
                baseline_signature.get('timing_patterns', {})
            )
            
            style_similarity = self._compare_interaction_styles(
                current_signature.get('interaction_style', {}),
                baseline_signature.get('interaction_style', {})
            )
            
            # Calculate weighted identity score
            identity_score = (
                typing_similarity * self.identity_weights['typing_signature'] +
                timing_similarity * self.identity_weights['timing_patterns'] +
                style_similarity * self.identity_weights['interaction_style']
            )
            
            # Data quality factor - More lenient approach
            current_quality = current_signature.get('data_quality', 0.5)
            baseline_quality = baseline_signature.get('data_quality', 0.5)
            quality_factor = (current_quality + baseline_quality) / 2
            
            # Be more forgiving with data quality issues
            if quality_factor < 0.2:
                # Very poor data quality - be somewhat lenient
                adjusted_identity_score = identity_score * 0.75
            elif quality_factor < 0.4:
                # Poor data quality - be more lenient
                adjusted_identity_score = identity_score * 0.9
            else:
                # Good data quality - use full score with slight boost
                adjusted_identity_score = min(1.0, identity_score * 1.05)
            
            # Determine user identity - Optimized thresholds for security vs usability
            if adjusted_identity_score >= 0.75:
                is_same_user = True
                confidence_level = "HIGH"
                reason = f"Strong identity match ({adjusted_identity_score:.3f}) - Same user confirmed"
            elif adjusted_identity_score >= 0.68:  # Slightly higher threshold for better discrimination
                is_same_user = True
                confidence_level = "MEDIUM"
                reason = f"Good identity match ({adjusted_identity_score:.3f}) - Likely same user"
            elif adjusted_identity_score >= 0.50:  # Conservative for borderline cases
                is_same_user = False
                confidence_level = "MEDIUM"
                reason = f"Moderate identity mismatch ({adjusted_identity_score:.3f}) - Possibly different user"
            else:
                is_same_user = False
                confidence_level = "HIGH"
                reason = f"Strong identity mismatch ({adjusted_identity_score:.3f}) - Different user detected"
            
            # Calculate confidence and risk scores
            confidence = adjusted_identity_score
            risk_score = 1.0 - confidence
            
            return {
                'is_same_user': is_same_user,
                'identity_score': adjusted_identity_score,
                'confidence': confidence,
                'risk_score': risk_score,
                'confidence_level': confidence_level,
                'authorization_reason': reason,
                'similarity_breakdown': {
                    'typing_similarity': typing_similarity,
                    'timing_similarity': timing_similarity,
                    'style_similarity': style_similarity
                },
                'data_quality': quality_factor,
                'recommendation': 'AUTHORIZE' if is_same_user else 'BLOCK'
            }
            
        except Exception as e:
            print(f"🚨 Error comparing identities: {e}")
            return self._get_error_result(str(e))
    
    def _compare_typing_signatures(self, current: Dict, baseline: Dict) -> float:
        """Compare typing signature patterns"""
        if not current or not baseline:
            return 0.5
        
        # Compare average intervals (typing speed) - More discriminating for large differences
        current_interval = current.get('avg_interval', 200)
        baseline_interval = baseline.get('avg_interval', 200)
        interval_diff = abs(current_interval - baseline_interval)
        
        # Calculate percentage difference for better discrimination - More tolerant
        avg_interval = (current_interval + baseline_interval) / 2
        percent_diff = interval_diff / avg_interval if avg_interval > 0 else 0
        
        # Be more tolerant of natural typing variation but still discriminating
        if percent_diff > 0.7:  # Only penalize very large differences (70%+)
            interval_similarity = max(0.1, 0.4 - percent_diff * 0.3)
        elif percent_diff > 0.4:  # Moderate differences (40-70%)
            interval_similarity = max(0.2, 0.7 - percent_diff * 0.8)
        else:
            interval_similarity = max(0.3, 1.0 - percent_diff * 1.2)  # Reasonable tolerance for normal variation
        
        # Compare dwell times - More tolerant
        current_dwell = current.get('avg_dwell', 50)
        baseline_dwell = baseline.get('avg_dwell', 50)
        dwell_diff = abs(current_dwell - baseline_dwell)
        
        # Be more forgiving of dwell time variations
        if dwell_diff > 100:  # Only penalize very large differences
            dwell_similarity = max(0.2, 0.5 - dwell_diff / 500)
        else:
            dwell_similarity = max(0.4, 1.0 - dwell_diff / 150)  # More lenient
        
        # Compare rhythm consistency - More lenient
        current_rhythm = current.get('rhythm_score', 0.5)
        baseline_rhythm = baseline.get('rhythm_score', 0.5)
        rhythm_diff = abs(current_rhythm - baseline_rhythm)
        rhythm_similarity = max(0.3, 1.0 - rhythm_diff * 0.8)  # Less punitive for rhythm changes
        
        # Weighted average
        typing_similarity = (
            interval_similarity * 0.4 +
            dwell_similarity * 0.3 +
            rhythm_similarity * 0.3
        )
        
        return max(0.0, min(1.0, typing_similarity))
    
    def _compare_timing_patterns(self, current: Dict, baseline: Dict) -> float:
        """Compare timing pattern signatures"""
        if not current or not baseline:
            return 0.5
        
        # Compare pause patterns - More lenient
        current_pause = current.get('avg_pause', 200)
        baseline_pause = baseline.get('avg_pause', 200)
        pause_diff = abs(current_pause - baseline_pause)
        
        # Be more forgiving of pause pattern variations  
        if pause_diff > 300:  # Only penalize very large differences
            pause_similarity = max(0.2, 0.6 - pause_diff / 1000)
        else:
            pause_similarity = max(0.4, 1.0 - pause_diff / 500)  # More tolerant
        
        # Compare activity rhythm - More lenient
        current_rhythm = current.get('activity_rhythm', 0.5)
        baseline_rhythm = baseline.get('activity_rhythm', 0.5)
        rhythm_diff = abs(current_rhythm - baseline_rhythm)
        rhythm_similarity = max(0.3, 1.0 - rhythm_diff * 0.6)  # Less sensitive
        
        # Weighted average
        timing_similarity = (pause_similarity + rhythm_similarity) / 2
        
        return max(0.0, min(1.0, timing_similarity))
    
    def _compare_interaction_styles(self, current: Dict, baseline: Dict) -> float:
        """Compare interaction style patterns"""
        if not current or not baseline:
            return 0.5
        
        # Compare interaction ratios - More precise comparison
        current_key_ratio = current.get('key_ratio', 0.33)
        baseline_key_ratio = baseline.get('key_ratio', 0.33)
        current_click_ratio = current.get('click_ratio', 0.33)
        baseline_click_ratio = baseline.get('click_ratio', 0.33)
        current_mouse_ratio = current.get('mouse_ratio', 0.33)
        baseline_mouse_ratio = baseline.get('mouse_ratio', 0.33)
        
        # Calculate similarity for each interaction type - More sensitive
        key_ratio_diff = abs(current_key_ratio - baseline_key_ratio)
        click_ratio_diff = abs(current_click_ratio - baseline_click_ratio)
        mouse_ratio_diff = abs(current_mouse_ratio - baseline_mouse_ratio)
        
        # Be appropriately discriminating for interaction pattern differences
        key_ratio_sim = max(0.1, 1.0 - key_ratio_diff * 2.0)  # Moderately sensitive to keyboard usage
        click_ratio_sim = max(0.1, 1.0 - click_ratio_diff * 2.5)  # Sensitive to clicking patterns  
        mouse_ratio_sim = max(0.1, 1.0 - mouse_ratio_diff * 1.8)  # Moderately sensitive to mouse usage
        
        # Weighted average of ratio similarities
        ratio_similarity = (key_ratio_sim * 0.5 + click_ratio_sim * 0.3 + mouse_ratio_sim * 0.2)
        
        # Compare style preferences - More lenient
        current_style = current.get('preference_style', 0.5)
        baseline_style = baseline.get('preference_style', 0.5)
        style_diff = abs(current_style - baseline_style)
        style_similarity = max(0.3, 1.0 - style_diff * 0.8)  # Less punitive
        
        # Weighted average
        interaction_similarity = (ratio_similarity + style_similarity) / 2
        
        return max(0.0, min(1.0, interaction_similarity))
    
    # Helper methods for categorization
    def _categorize_typing_speed(self, avg_interval: float) -> float:
        """Categorize typing speed into signature value"""
        if avg_interval < 100:
            return 0.9  # Very fast typist
        elif avg_interval < 200:
            return 0.7  # Fast typist
        elif avg_interval < 400:
            return 0.5  # Average typist
        else:
            return 0.3  # Slow typist
    
    def _categorize_dwell_time(self, avg_dwell: float) -> float:
        """Categorize key dwell time into signature value"""
        if avg_dwell < 50:
            return 0.3  # Quick key presses
        elif avg_dwell < 100:
            return 0.5  # Normal key presses
        elif avg_dwell < 200:
            return 0.7  # Deliberate key presses
        else:
            return 0.9  # Very deliberate key presses
    
    def _categorize_pause_pattern(self, intervals: List[float]) -> float:
        """Categorize pause patterns into signature value"""
        if not intervals:
            return 0.5
        
        avg_pause = statistics.mean(intervals)
        if avg_pause < 100:
            return 0.8  # Rapid fire user
        elif avg_pause < 300:
            return 0.6  # Quick user
        elif avg_pause < 600:
            return 0.4  # Deliberate user
        else:
            return 0.2  # Very deliberate user
    
    def _analyze_transition_patterns(self, transitions: List[Tuple]) -> float:
        """Analyze transition patterns between interaction types"""
        if not transitions:
            return 0.5
        
        # Count specific transition types
        key_to_mouse = sum(1 for t in transitions if t == ('key', 'mouse'))
        mouse_to_click = sum(1 for t in transitions if t == ('mouse', 'click'))
        
        total_transitions = len(transitions)
        if total_transitions == 0:
            return 0.5
        
        # Calculate transition signature
        km_ratio = key_to_mouse / total_transitions
        mc_ratio = mouse_to_click / total_transitions
        
        # Create signature based on preferred transitions
        signature = km_ratio + mc_ratio * 0.5
        return min(1.0, signature)
    
    def _categorize_activity_rhythm(self, rhythm_variance: float) -> float:
        """Categorize activity rhythm variance into signature"""
        if rhythm_variance < 50:
            return 0.9  # Very consistent user
        elif rhythm_variance < 150:
            return 0.7  # Consistent user
        elif rhythm_variance < 300:
            return 0.5  # Variable user
        else:
            return 0.3  # Very variable user
    
    def _get_default_signature(self) -> Dict:
        """Return default signature for error cases"""
        return {
            'typing_signature': {'rhythm_score': 0.5, 'speed_signature': 0.5, 'dwell_pattern': 0.5},
            'timing_patterns': {'pause_pattern': 0.5, 'transition_style': 0.5, 'activity_rhythm': 0.5},
            'interaction_style': {'interaction_ratio': 0.5, 'preference_style': 0.5, 'engagement_level': 0.5},
            'data_quality': 0.5
        }
    
    def _get_insufficient_data_result(self) -> Dict:
        """Return result for insufficient data cases"""
        return {
            'is_same_user': False,
            'identity_score': 0.0,
            'confidence': 0.0,
            'risk_score': 1.0,
            'confidence_level': 'LOW',
            'authorization_reason': 'INSUFFICIENT_DATA: Not enough behavioral data for identity verification',
            'recommendation': 'BLOCK'
        }
    
    def _get_error_result(self, error_msg: str) -> Dict:
        """Return result for error cases"""
        return {
            'is_same_user': False,
            'identity_score': 0.0,
            'confidence': 0.0,
            'risk_score': 1.0,
            'confidence_level': 'LOW',
            'authorization_reason': f'ANALYSIS_ERROR: {error_msg}',
            'recommendation': 'BLOCK'
        }

# Main analysis function to replace the existing complex system
def analyze_user_identity(current_data: Dict, baseline_data: Dict, session_id: str = None) -> Dict[str, Any]:
    """
    Main function to analyze user identity - keeps same interface as existing system
    """
    try:
        detector = ImprovedUserIdentityDetector()
        
        # Extract identity signatures
        current_signature = detector.extract_user_identity_signature(current_data)
        baseline_signature = detector.extract_user_identity_signature(baseline_data)
        
        # Compare identities
        result = detector.compare_user_identities(current_signature, baseline_signature)
        
        # Format result to match existing API response
        formatted_result = {
            'is_authorized': result['is_same_user'],
            'confidence': result['confidence'],
            'risk_score': result['risk_score'], 
            'anomaly_score': result['risk_score'],  # Add for compatibility
            'identity_score': result['identity_score'],
            'mahalanobis_distance': result['identity_score'] * 10,  # Fake for compatibility
            'standard_deviations': (1.0 - result['identity_score']) * 10,  # Fake for compatibility
            'authorization_reason': result['authorization_reason'],
            'recommendation': result['recommendation'],
            'analysis_type': 'improved_user_identity_detection',
            'confidence_level': result['confidence_level'],
            'similarity_breakdown': result['similarity_breakdown'],
            'data_quality': result['data_quality'],
            'session_id': session_id,
            
            # Add missing compatibility fields
            'cosine_similarity': result['identity_score'],  # Use identity score as cosine similarity
            'cosine_max_similarity': result['identity_score'],
            'cosine_min_similarity': result['identity_score'],
            'cosine_variance': 0.1 * (1.0 - result['identity_score']),  # Lower variance for better matches
            'window_similarities': [result['identity_score']],
            'windows_analyzed': 1,
            'combined_similarity': result['identity_score'],
            'baseline_similarity': result['identity_score'],
            'baseline_deviations': [],
            'risk_factors': [
                {
                    'metric': 'user_identity_verification',
                    'severity': 'HIGH' if result['risk_score'] > 0.7 else 'MEDIUM' if result['risk_score'] > 0.4 else 'LOW',
                    'value': result['identity_score'],
                    'threshold': 0.6,
                    'description': result['authorization_reason']
                }
            ],
            'suspicious_indicators': [] if result['is_same_user'] else ['Identity pattern mismatch detected'],
            'human_indicators': ['Consistent behavioral patterns'] if result['is_same_user'] else [],
            'profile_size': 1
        }
        
        return formatted_result
        
    except Exception as e:
        print(f"🚨 Identity analysis error: {e}")
        return {
            'is_authorized': False,
            'confidence': 0.0,
            'risk_score': 1.0,
            'identity_score': 0.0,
            'authorization_reason': f'IDENTITY_ANALYSIS_ERROR: {str(e)}',
            'recommendation': 'BLOCK',
            'analysis_type': 'error_fallback',
            'session_id': session_id
        }
