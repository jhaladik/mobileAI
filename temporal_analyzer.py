"""
Temporal intelligence and pattern recognition
This module learns traffic patterns and detects anomalies
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from scipy import stats
import logging
import config
from data_store import DataStore

logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class TemporalAnalyzer:
    def __init__(self, data_store: DataStore):
        self.data_store = data_store
        self.learned_patterns = {}
        self.baseline_statistics = {}
        
        logger.info("TemporalAnalyzer initialized")
    
    def analyze_recent_patterns(self, hours: int = 24) -> Dict:
        """
        Analyze recent traffic data for patterns
        """
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'analysis_period_hours': hours,
            'patterns_detected': [],
            'anomalies_detected': [],
            'statistics': {}
        }
        
        try:
            # Get recent data
            stats = self.data_store.get_traffic_statistics(hours=hours)
            analysis['statistics'] = stats
            
            # Get hourly patterns
            hourly_data = self.data_store.get_hourly_traffic_pattern(days=7)
            
            # Detect patterns
            patterns = self._detect_temporal_patterns(hourly_data)
            analysis['patterns_detected'] = patterns
            
            # Check for anomalies
            recent_obs = self.data_store.get_recent_observations(hours=1, limit=20)
            anomalies = self._detect_anomalies(recent_obs)
            analysis['anomalies_detected'] = anomalies
            
            # Update learned patterns
            self._update_learned_patterns(patterns)
            
            logger.info(f"Temporal analysis complete: {len(patterns)} patterns, {len(anomalies)} anomalies")
            
        except Exception as e:
            logger.error(f"Error in temporal analysis: {e}")
        
        return analysis
    
    def _detect_temporal_patterns(self, hourly_data: List[Dict]) -> List[Dict]:
        """
        Detect recurring temporal patterns in traffic
        """
        patterns = []
        
        if len(hourly_data) < config.MIN_OBSERVATIONS_FOR_PATTERN:
            logger.debug("Insufficient data for pattern detection")
            return patterns
        
        try:
            # Extract hourly averages
            hours = [d['hour'] for d in hourly_data]
            avg_vehicles = [d['avg_vehicles'] for d in hourly_data]
            
            # Find peak hours
            if avg_vehicles:
                mean_traffic = np.mean(avg_vehicles)
                std_traffic = np.std(avg_vehicles)
                
                peak_threshold = mean_traffic + std_traffic
                peak_hours = [
                    hours[i] for i, v in enumerate(avg_vehicles) 
                    if v > peak_threshold
                ]
                
                if peak_hours:
                    patterns.append({
                        'type': 'peak_hours',
                        'description': f'High traffic during hours: {peak_hours}',
                        'hours': peak_hours,
                        'threshold': peak_threshold,
                        'confidence': 0.8
                    })
                
                # Find quiet hours
                quiet_threshold = mean_traffic - std_traffic
                quiet_hours = [
                    hours[i] for i, v in enumerate(avg_vehicles)
                    if v < quiet_threshold
                ]
                
                if quiet_hours:
                    patterns.append({
                        'type': 'quiet_hours',
                        'description': f'Low traffic during hours: {quiet_hours}',
                        'hours': quiet_hours,
                        'threshold': quiet_threshold,
                        'confidence': 0.8
                    })
                
                # Detect morning rush (6-9am with elevated traffic)
                morning_hours = [6, 7, 8, 9]
                morning_traffic = [
                    avg_vehicles[i] for i, h in enumerate(hours)
                    if h in morning_hours
                ]
                if morning_traffic and np.mean(morning_traffic) > mean_traffic:
                    patterns.append({
                        'type': 'morning_rush',
                        'description': 'Morning rush hour pattern detected',
                        'hours': morning_hours,
                        'avg_traffic': np.mean(morning_traffic),
                        'confidence': 0.75
                    })
                
                # Detect evening rush (16-19)
                evening_hours = [16, 17, 18, 19]
                evening_traffic = [
                    avg_vehicles[i] for i, h in enumerate(hours)
                    if h in evening_hours
                ]
                if evening_traffic and np.mean(evening_traffic) > mean_traffic:
                    patterns.append({
                        'type': 'evening_rush',
                        'description': 'Evening rush hour pattern detected',
                        'hours': evening_hours,
                        'avg_traffic': np.mean(evening_traffic),
                        'confidence': 0.75
                    })
            
            logger.debug(f"Detected {len(patterns)} temporal patterns")
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
        
        return patterns
    
    def _detect_anomalies(self, recent_observations: List[Dict]) -> List[Dict]:
        """
        Detect anomalous traffic events
        """
        anomalies = []
        
        if len(recent_observations) < 10:
            return anomalies
        
        try:
            # Get detection counts
            detection_counts = [
                obs['detection_count'] for obs in recent_observations
                if obs['detection_count'] is not None
            ]
            
            if not detection_counts:
                return anomalies
            
            # Calculate baseline statistics
            mean_count = np.mean(detection_counts)
            std_count = np.std(detection_counts)
            
            # Z-score anomaly detection
            for obs in recent_observations[-5:]:  # Check last 5 observations
                count = obs['detection_count']
                if count is None:
                    continue
                
                z_score = (count - mean_count) / std_count if std_count > 0 else 0
                
                if abs(z_score) > config.ANOMALY_DETECTION_THRESHOLD:
                    anomaly_type = 'unusually_high_traffic' if z_score > 0 else 'unusually_low_traffic'
                    anomalies.append({
                        'type': anomaly_type,
                        'description': f'Traffic count {count} deviates {z_score:.2f} std devs from baseline',
                        'z_score': z_score,
                        'observed_value': count,
                        'baseline_mean': mean_count,
                        'baseline_std': std_count,
                        'severity': abs(z_score) / 3,  # Normalized severity
                        'observation_id': obs['id']
                    })
                    
                    # Save to database
                    self.data_store.save_anomaly(
                        anomaly_type=anomaly_type,
                        description=anomalies[-1]['description'],
                        severity=anomalies[-1]['severity'],
                        baseline_value=mean_count,
                        observed_value=count,
                        observation_id=obs['id']
                    )
            
            # Check for sudden confidence drops (could indicate occlusion, fog, etc.)
            confidences = [
                obs['confidence_avg'] for obs in recent_observations
                if obs['confidence_avg'] is not None
            ]
            
            if confidences and len(confidences) > 5:
                mean_conf = np.mean(confidences)
                recent_conf = np.mean(confidences[-3:])
                
                if recent_conf < mean_conf - 0.2:  # 20% drop in confidence
                    anomalies.append({
                        'type': 'confidence_drop',
                        'description': f'Detection confidence dropped from {mean_conf:.2f} to {recent_conf:.2f}',
                        'observed_value': recent_conf,
                        'baseline_mean': mean_conf,
                        'severity': 0.5
                    })
            
            logger.debug(f"Detected {len(anomalies)} anomalies")
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
        
        return anomalies
    
    def _update_learned_patterns(self, patterns: List[Dict]):
        """
        Update the internal knowledge of learned patterns
        """
        for pattern in patterns:
            pattern_type = pattern['type']
            
            if pattern_type not in self.learned_patterns:
                self.learned_patterns[pattern_type] = []
            
            # Add pattern with timestamp
            pattern['learned_at'] = datetime.now().isoformat()
            self.learned_patterns[pattern_type].append(pattern)
            
            # Save to database
            self.data_store.save_pattern(
                pattern_type=pattern_type,
                description=pattern['description'],
                time_window='7days',  # Based on analysis window
                confidence=pattern.get('confidence', 0.5),
                supporting_observations=len(pattern.get('hours', [])),
                metadata=pattern
            )
        
        # Keep only recent patterns (last 30 days)
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        for pattern_type in self.learned_patterns:
            self.learned_patterns[pattern_type] = [
                p for p in self.learned_patterns[pattern_type]
                if p.get('learned_at', '') > cutoff
            ]
    
    def predict_traffic_level(self, target_hour: Optional[int] = None) -> Dict:
        """
        Predict expected traffic level for a given hour
        If no hour provided, uses current hour
        """
        if target_hour is None:
            target_hour = datetime.now().hour
        
        prediction = {
            'hour': target_hour,
            'predicted_level': 'medium',
            'confidence': 0.5,
            'reasoning': []
        }
        
        try:
            # Get historical data for this hour
            hourly_pattern = self.data_store.get_hourly_traffic_pattern(days=7)
            
            # Find data for target hour
            hour_data = [d for d in hourly_pattern if d['hour'] == target_hour]
            
            if hour_data:
                avg_vehicles = hour_data[0]['avg_vehicles']
                
                # Get overall average
                all_averages = [d['avg_vehicles'] for d in hourly_pattern]
                overall_mean = np.mean(all_averages)
                overall_std = np.std(all_averages)
                
                # Classify traffic level
                if avg_vehicles > overall_mean + overall_std:
                    prediction['predicted_level'] = 'high'
                    prediction['confidence'] = 0.7
                    prediction['reasoning'].append(
                        f'Hour {target_hour} historically has {avg_vehicles:.1f} vehicles vs average {overall_mean:.1f}'
                    )
                elif avg_vehicles < overall_mean - overall_std:
                    prediction['predicted_level'] = 'low'
                    prediction['confidence'] = 0.7
                    prediction['reasoning'].append(
                        f'Hour {target_hour} historically has {avg_vehicles:.1f} vehicles vs average {overall_mean:.1f}'
                    )
                else:
                    prediction['predicted_level'] = 'medium'
                    prediction['confidence'] = 0.6
                
                # Check learned patterns
                for pattern_type, patterns in self.learned_patterns.items():
                    for pattern in patterns:
                        if target_hour in pattern.get('hours', []):
                            prediction['reasoning'].append(
                                f'Pattern {pattern_type}: {pattern["description"]}'
                            )
            
            logger.debug(f"Traffic prediction for hour {target_hour}: {prediction['predicted_level']}")
            
        except Exception as e:
            logger.error(f"Error predicting traffic: {e}")
        
        return prediction
    
    def calculate_baseline_statistics(self):
        """
        Calculate baseline statistics for comparison
        This establishes what "normal" looks like
        """
        try:
            # Get 7 days of data
            hourly_data = self.data_store.get_hourly_traffic_pattern(days=7)
            
            if not hourly_data:
                logger.warning("No data available for baseline calculation")
                return
            
            # Calculate overall statistics
            all_vehicle_counts = [d['avg_vehicles'] for d in hourly_data]
            all_pedestrian_counts = [d['avg_pedestrians'] for d in hourly_data]
            
            self.baseline_statistics = {
                'vehicles': {
                    'mean': np.mean(all_vehicle_counts),
                    'std': np.std(all_vehicle_counts),
                    'median': np.median(all_vehicle_counts),
                    'min': np.min(all_vehicle_counts),
                    'max': np.max(all_vehicle_counts)
                },
                'pedestrians': {
                    'mean': np.mean(all_pedestrian_counts),
                    'std': np.std(all_pedestrian_counts),
                    'median': np.median(all_pedestrian_counts),
                    'min': np.min(all_pedestrian_counts),
                    'max': np.max(all_pedestrian_counts)
                },
                'calculated_at': datetime.now().isoformat(),
                'data_points': len(hourly_data)
            }
            
            # Store in database
            self.data_store.update_system_state(
                state_type='baseline_statistics',
                state_value='calculated',
                metadata=self.baseline_statistics
            )
            
            logger.info(f"Baseline statistics calculated from {len(hourly_data)} data points")
            
        except Exception as e:
            logger.error(f"Error calculating baseline: {e}")
    
    def get_insights_summary(self) -> Dict:
        """
        Generate a summary of learned insights
        This is data for the meta-cognitive layer
        """
        summary = {
            'timestamp': datetime.now().isoformat(),
            'patterns_known': {},
            'baseline_established': bool(self.baseline_statistics),
            'confidence_in_patterns': 0.0,
            'observations_analyzed': 0
        }
        
        try:
            # Count patterns by type
            for pattern_type, patterns in self.learned_patterns.items():
                summary['patterns_known'][pattern_type] = len(patterns)
            
            # Calculate overall confidence
            all_confidences = []
            for patterns in self.learned_patterns.values():
                all_confidences.extend([p.get('confidence', 0.5) for p in patterns])
            
            if all_confidences:
                summary['confidence_in_patterns'] = np.mean(all_confidences)
            
            # Count total observations
            stats = self.data_store.get_traffic_statistics(hours=24*7)  # Last week
            summary['observations_analyzed'] = stats.get('observation_count', 0)
            
            # Add baseline info
            if self.baseline_statistics:
                summary['baseline_info'] = {
                    'vehicle_mean': self.baseline_statistics['vehicles']['mean'],
                    'data_points': self.baseline_statistics['data_points']
                }
            
        except Exception as e:
            logger.error(f"Error generating insights summary: {e}")
        
        return summary
    
    def self_assess_reliability(self) -> Dict:
        """
        Assess the reliability of the temporal analysis
        This is meta-cognition about the analysis quality
        """
        assessment = {
            'overall_reliability': 0.5,
            'factors': [],
            'recommendations': []
        }
        
        try:
            # Factor 1: Amount of data
            stats = self.data_store.get_traffic_statistics(hours=24*7)
            obs_count = stats.get('observation_count', 0)
            
            if obs_count < 100:
                assessment['factors'].append('Limited data (< 100 observations)')
                assessment['recommendations'].append('Need more observations for reliable patterns')
                data_score = 0.3
            elif obs_count < 500:
                assessment['factors'].append('Moderate data (100-500 observations)')
                data_score = 0.6
            else:
                assessment['factors'].append('Substantial data (> 500 observations)')
                data_score = 0.9
            
            # Factor 2: Pattern consistency
            pattern_count = sum(len(p) for p in self.learned_patterns.values())
            if pattern_count < 3:
                assessment['factors'].append('Few patterns detected')
                pattern_score = 0.4
            elif pattern_count < 10:
                assessment['factors'].append('Moderate pattern set')
                pattern_score = 0.7
            else:
                assessment['factors'].append('Rich pattern set detected')
                pattern_score = 0.9
            
            # Factor 3: Detection confidence
            avg_conf = stats.get('avg_detection_confidence', 0.5)
            if avg_conf < 0.5:
                assessment['factors'].append('Low detection confidence')
                assessment['recommendations'].append('Consider adjusting detection thresholds')
                conf_score = 0.4
            elif avg_conf < 0.7:
                assessment['factors'].append('Moderate detection confidence')
                conf_score = 0.7
            else:
                assessment['factors'].append('High detection confidence')
                conf_score = 0.9
            
            # Calculate overall reliability
            assessment['overall_reliability'] = np.mean([data_score, pattern_score, conf_score])
            
            # Add specific recommendations
            if assessment['overall_reliability'] < 0.6:
                assessment['recommendations'].append('Continue collecting data to improve reliability')
            
            if not self.baseline_statistics:
                assessment['recommendations'].append('Baseline statistics not yet calculated')
            
            logger.info(f"Self-assessment: reliability = {assessment['overall_reliability']:.2f}")
            
        except Exception as e:
            logger.error(f"Error in self-assessment: {e}")
        
        return assessment
