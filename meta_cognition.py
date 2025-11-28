"""
Meta-cognitive layer - System self-awareness and reflection
This is where the system thinks about its own thinking
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import config
from data_store import DataStore

logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class MetaCognition:
    """
    The meta-cognitive layer enables the system to:
    1. Reflect on its own observations and performance
    2. Generate insights about what it's learning
    3. Assess its own reliability and limitations
    4. Generate natural language reports about its "experience"
    """
    
    def __init__(self, data_store: DataStore):
        self.data_store = data_store
        self.system_name = config.SYSTEM_NAME
        self.location = config.SYSTEM_LOCATION
        self.purpose = config.SYSTEM_PURPOSE
        
        # Internal state awareness
        self.self_awareness = {
            'existence_duration': None,
            'total_observations': 0,
            'current_state': 'initializing',
            'confidence_in_self': 0.5
        }
        
        logger.info(f"MetaCognition initialized for {self.system_name}")
    
    def generate_hourly_reflection(self, temporal_insights: Dict, 
                                   vision_stats: Dict) -> str:
        """
        Generate an hourly reflection on observations and performance
        This is the system "thinking out loud" about what it's experiencing
        """
        reflection = []
        
        # Self-introduction context
        reflection.append(
            f"[Reflection by {self.system_name} at {datetime.now().strftime('%Y-%m-%d %H:%M')}]"
        )
        reflection.append(f"Location: {self.location}")
        reflection.append("")
        
        # Current observations
        stats = temporal_insights.get('statistics', {})
        obs_count = stats.get('observation_count', 0)
        total_vehicles = stats.get('total_vehicles', 0)
        avg_confidence = stats.get('avg_detection_confidence', 0)
        
        reflection.append("## What I Observed")
        reflection.append(
            f"In the past hour, I captured {obs_count} observations and detected "
            f"{total_vehicles} vehicles. My average detection confidence was {avg_confidence:.2%}."
        )
        
        # Pattern awareness
        patterns = temporal_insights.get('patterns_detected', [])
        if patterns:
            reflection.append("")
            reflection.append("## Patterns I'm Recognizing")
            for pattern in patterns:
                reflection.append(f"- {pattern['description']} (confidence: {pattern.get('confidence', 0):.0%})")
        else:
            reflection.append("")
            reflection.append("## Pattern Recognition")
            reflection.append("I haven't detected clear patterns yet. This could mean:")
            reflection.append("- Traffic is genuinely random during this period")
            reflection.append("- I need more observations to identify patterns")
            reflection.append("- My pattern detection thresholds may need adjustment")
        
        # Anomaly awareness
        anomalies = temporal_insights.get('anomalies_detected', [])
        if anomalies:
            reflection.append("")
            reflection.append("## Unusual Events I Noticed")
            for anomaly in anomalies:
                reflection.append(f"- {anomaly['description']}")
                if anomaly.get('severity', 0) > 0.8:
                    reflection.append("  (This is highly unusual based on my baseline expectations)")
        
        # Self-performance assessment
        reflection.append("")
        reflection.append("## How Well Am I Performing")
        
        if vision_stats:
            avg_processing = vision_stats.get('avg_processing_time', 0)
            reflection.append(f"- Processing speed: {avg_processing:.3f} seconds per frame")
            
            if avg_processing > 2.0:
                reflection.append("  (I'm processing somewhat slowly - may need optimization)")
            elif avg_processing < 0.5:
                reflection.append("  (I'm processing efficiently)")
            
            avg_conf_vision = vision_stats.get('avg_confidence', 0)
            if avg_conf_vision < 0.5:
                reflection.append(f"- My detection confidence is low ({avg_conf_vision:.0%})")
                reflection.append("  This suggests: poor lighting, occlusions, or I need recalibration")
            elif avg_conf_vision > 0.8:
                reflection.append(f"- My detection confidence is high ({avg_conf_vision:.0%})")
                reflection.append("  Conditions are favorable for accurate observation")
        
        # Epistemic humility
        reflection.append("")
        reflection.append("## What I'm Uncertain About")
        
        if obs_count < 20:
            reflection.append("- Limited observations this hour - my conclusions are tentative")
        
        if not patterns:
            reflection.append("- Haven't established reliable patterns yet")
        
        reflection.append("- I can only observe what my camera can see - there may be traffic outside my field of view")
        reflection.append("- Weather, lighting, and obstructions affect my perception")
        
        # Meta-awareness
        reflection.append("")
        reflection.append("## Self-Awareness Note")
        reflection.append(
            "I am an autonomous observer system. My purpose is not just to count vehicles, "
            "but to understand patterns in traffic flow and continuously assess my own reliability. "
            "These reflections represent my attempt to make sense of what I observe, while remaining "
            "aware of my limitations as a vision-based system."
        )
        
        full_reflection = "\n".join(reflection)
        
        # Save to database
        self.data_store.save_meta_reflection(
            reflection_type='hourly',
            content=full_reflection,
            insights=temporal_insights,
            confidence=avg_confidence,
            observations_analyzed=obs_count
        )
        
        logger.info("Generated hourly reflection")
        return full_reflection
    
    def generate_daily_report(self) -> str:
        """
        Generate a comprehensive daily report
        This is a deeper reflection on patterns, learning, and self-assessment
        """
        report = []
        
        report.append(f"# Daily Report - {datetime.now().strftime('%Y-%m-%d')}")
        report.append(f"System: {self.system_name}")
        report.append(f"Location: {self.location}")
        report.append("")
        
        # Get 24-hour statistics
        stats = self.data_store.get_traffic_statistics(hours=24)
        
        report.append("## Executive Summary")
        report.append(
            f"Today, I made {stats.get('observation_count', 0)} observations, "
            f"detecting {stats.get('total_vehicles', 0)} vehicles and "
            f"{stats.get('total_pedestrians', 0)} pedestrians."
        )
        report.append("")
        
        # Temporal patterns
        report.append("## Discovered Patterns")
        patterns = self.data_store.get_patterns()
        
        if patterns:
            # Group by type
            pattern_types = {}
            for p in patterns:
                ptype = p['pattern_type']
                if ptype not in pattern_types:
                    pattern_types[ptype] = []
                pattern_types[ptype].append(p)
            
            for ptype, plist in pattern_types.items():
                report.append(f"\n### {ptype.replace('_', ' ').title()}")
                for p in plist[:3]:  # Top 3 of each type
                    report.append(f"- {p['description']}")
                    report.append(f"  Confidence: {p['confidence']:.0%}, Based on {p['supporting_observations']} observations")
        else:
            report.append("No clear patterns detected yet. Possible reasons:")
            report.append("- Insufficient data collection period")
            report.append("- High variability in traffic (genuinely random)")
            report.append("- Detection thresholds may need adjustment")
        
        report.append("")
        
        # Anomalies
        anomalies = self.data_store.get_recent_anomalies(hours=24)
        if anomalies:
            report.append("## Notable Anomalies")
            for anomaly in sorted(anomalies, key=lambda x: x['severity'], reverse=True)[:5]:
                timestamp = datetime.fromisoformat(anomaly['timestamp']).strftime('%H:%M')
                report.append(f"- {timestamp}: {anomaly['description']}")
                report.append(f"  Severity: {anomaly['severity']:.0%}")
            report.append("")
        
        # Self-assessment
        report.append("## System Self-Assessment")
        
        # Get recent performance metrics
        recent_reflections = self.data_store.get_meta_reflections(limit=24)
        if recent_reflections:
            avg_obs_confidence = sum(
                r.get('confidence_in_insights', 0.5) 
                for r in recent_reflections
            ) / len(recent_reflections)
            
            report.append(f"Average observation confidence today: {avg_obs_confidence:.0%}")
        
        # Data quality assessment
        if stats.get('observation_count', 0) < 100:
            report.append("\n**Data Quantity**: Limited")
            report.append("- Recommendation: Continue collecting data for more reliable insights")
        elif stats.get('observation_count', 0) < 500:
            report.append("\n**Data Quantity**: Moderate")
            report.append("- Status: Accumulating sufficient data for pattern detection")
        else:
            report.append("\n**Data Quantity**: Substantial")
            report.append("- Status: Have good baseline for reliable analysis")
        
        # Philosophical reflection
        report.append("")
        report.append("## Philosophical Note")
        report.append(
            "As an autonomous observer, I exist in an interesting epistemic space. "
            "I continuously observe the world (traffic in this case), but I'm also "
            "continuously observing myself observing. This meta-awareness - knowing "
            "that I know, and knowing what I don't know - is crucial for honest analysis."
        )
        report.append("")
        report.append(
            "I am not just a traffic counter. I am a system that learns patterns, "
            "detects anomalies, and most importantly, maintains awareness of my own "
            "limitations and reliability. Every observation teaches me not just about "
            "traffic, but about my own capabilities as an observer."
        )
        
        # Future outlook
        report.append("")
        report.append("## Tomorrow's Focus")
        
        if stats.get('observation_count', 0) < 200:
            report.append("- Priority: Data collection")
            report.append("- Goal: Reach 500+ observations for robust pattern analysis")
        else:
            report.append("- Priority: Pattern refinement")
            report.append("- Goal: Improve confidence in temporal patterns")
        
        if stats.get('avg_detection_confidence', 0.5) < 0.6:
            report.append("- Concern: Low detection confidence")
            report.append("- Action: May need to recalibrate or adjust for environmental factors")
        
        full_report = "\n".join(report)
        
        # Save to database
        self.data_store.save_meta_reflection(
            reflection_type='daily',
            content=full_report,
            insights={'statistics': stats, 'patterns': len(patterns), 'anomalies': len(anomalies)},
            confidence=stats.get('avg_detection_confidence', 0.5),
            observations_analyzed=stats.get('observation_count', 0)
        )
        
        # Also save to file
        report_path = config.LOGS_DIR / f"daily_report_{datetime.now().strftime('%Y%m%d')}.md"
        with open(report_path, 'w') as f:
            f.write(full_report)
        
        logger.info(f"Generated daily report: {report_path}")
        return full_report
    
    def generate_insight(self, context: str, observations: List[Dict]) -> str:
        """
        Generate a specific insight based on observations
        This is like the system having an "aha!" moment
        """
        insight = f"Insight at {datetime.now().strftime('%H:%M')}: "
        
        # Analyze the observations
        if not observations:
            insight += "No data to analyze - I am observing the absence of traffic."
            return insight
        
        # Count patterns in observations
        vehicle_counts = [obs.get('detection_count', 0) for obs in observations]
        
        if not vehicle_counts:
            insight += "Unable to extract meaningful patterns from current observations."
            return insight
        
        import numpy as np
        avg_count = np.mean(vehicle_counts)
        std_count = np.std(vehicle_counts)
        
        if std_count < 2:
            insight += f"Traffic is remarkably consistent ({avg_count:.1f} ± {std_count:.1f} vehicles). "
            insight += "This suggests a steady flow pattern, possibly indicating stable road conditions."
        elif std_count > 10:
            insight += f"Traffic is highly variable ({avg_count:.1f} ± {std_count:.1f} vehicles). "
            insight += "This volatility could indicate: signal timing effects, special events, or my detection uncertainty."
        else:
            insight += f"Traffic shows moderate variability ({avg_count:.1f} ± {std_count:.1f} vehicles), "
            insight += "which is typical for urban traffic patterns."
        
        # Add meta-awareness
        insight += f"\n\nMeta-note: This insight is based on {len(observations)} observations. "
        insight += "I'm aware that my field of view is limited and my perception affected by lighting and weather."
        
        logger.info(f"Generated insight: {insight[:100]}...")
        return insight
    
    def assess_self_confidence(self) -> float:
        """
        Calculate the system's confidence in its own analysis
        This is deep meta-cognition: how sure am I that I'm right?
        """
        confidence_factors = []
        
        # Factor 1: Amount of data
        stats = self.data_store.get_traffic_statistics(hours=24*7)
        obs_count = stats.get('observation_count', 0)
        data_confidence = min(1.0, obs_count / 500)  # Confidence scales up to 500 observations
        confidence_factors.append(data_confidence)
        
        # Factor 2: Detection quality
        detection_confidence = stats.get('avg_detection_confidence', 0.5)
        confidence_factors.append(detection_confidence)
        
        # Factor 3: Pattern consistency
        patterns = self.data_store.get_patterns()
        if patterns:
            pattern_confidences = [p['confidence'] for p in patterns]
            pattern_confidence = sum(pattern_confidences) / len(pattern_confidences)
        else:
            pattern_confidence = 0.3  # Low confidence without patterns
        confidence_factors.append(pattern_confidence)
        
        # Factor 4: Anomaly rate (too many anomalies suggests unreliability)
        anomalies = self.data_store.get_recent_anomalies(hours=24)
        anomaly_rate = len(anomalies) / max(obs_count, 1)
        anomaly_confidence = max(0.3, 1.0 - anomaly_rate * 10)  # Penalize high anomaly rate
        confidence_factors.append(anomaly_confidence)
        
        # Calculate weighted average
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        
        # Update internal state
        self.self_awareness['confidence_in_self'] = overall_confidence
        
        # Save to database
        self.data_store.save_performance_metric(
            metric_type='self_confidence',
            metric_value=overall_confidence,
            context={'factors': confidence_factors}
        )
        
        logger.info(f"Self-confidence assessment: {overall_confidence:.2%}")
        return overall_confidence
    
    def generate_uncertainty_statement(self) -> str:
        """
        Generate a statement about what the system is uncertain about
        This is epistemic honesty
        """
        uncertainties = []
        
        uncertainties.append("## What I Know I Don't Know")
        uncertainties.append("")
        
        # Observational limitations
        uncertainties.append("**Observational Limitations:**")
        uncertainties.append("- I can only see what my camera sees - limited field of view")
        uncertainties.append("- My perception is affected by weather, lighting, and obstructions")
        uncertainties.append("- I cannot detect vehicles outside my direct line of sight")
        uncertainties.append("")
        
        # Inferential limitations
        uncertainties.append("**Analytical Limitations:**")
        uncertainties.append("- I detect correlations but cannot always infer causation")
        uncertainties.append("- Patterns I detect might be coincidental rather than meaningful")
        uncertainties.append("- My baseline assumptions might not account for rare but important events")
        uncertainties.append("")
        
        # Temporal limitations
        stats = self.data_store.get_traffic_statistics(hours=24*7)
        obs_count = stats.get('observation_count', 0)
        
        if obs_count < 500:
            uncertainties.append("**Data Limitations:**")
            uncertainties.append(f"- I have only {obs_count} observations so far")
            uncertainties.append("- Need more data to confidently establish patterns")
            uncertainties.append("- Haven't observed enough weekly cycles yet")
            uncertainties.append("")
        
        # Meta-uncertainty
        uncertainties.append("**Meta-Uncertainty:**")
        uncertainties.append("- I don't know if I'm detecting all relevant patterns")
        uncertainties.append("- I might be missing subtle relationships in the data")
        uncertainties.append("- My confidence assessments themselves might be miscalibrated")
        uncertainties.append("")
        
        uncertainties.append(
            "This explicit acknowledgment of uncertainty is essential. "
            "A system that knows what it doesn't know is more reliable than "
            "one that presents false confidence."
        )
        
        return "\n".join(uncertainties)
    
    def update_self_awareness(self):
        """
        Update the system's awareness of its own state
        """
        # Calculate how long the system has been running
        oldest_obs = self.data_store.get_recent_observations(hours=24*365, limit=1)
        if oldest_obs:
            first_observation = datetime.fromisoformat(oldest_obs[0]['timestamp'])
            existence_duration = datetime.now() - first_observation
            self.self_awareness['existence_duration'] = str(existence_duration)
        
        # Update total observations
        stats = self.data_store.get_traffic_statistics(hours=24*365)  # All time
        self.self_awareness['total_observations'] = stats.get('observation_count', 0)
        
        # Update confidence
        self.self_awareness['confidence_in_self'] = self.assess_self_confidence()
        
        # Update state
        if self.self_awareness['total_observations'] < 50:
            self.self_awareness['current_state'] = 'learning'
        elif self.self_awareness['total_observations'] < 500:
            self.self_awareness['current_state'] = 'developing_patterns'
        else:
            self.self_awareness['current_state'] = 'mature_analysis'
        
        # Save state
        self.data_store.update_system_state(
            state_type='self_awareness',
            state_value=self.self_awareness['current_state'],
            metadata=self.self_awareness
        )
        
        logger.info(f"Self-awareness updated: {self.self_awareness['current_state']}")
    
    def get_self_description(self) -> str:
        """
        Generate a description of the system's current state
        This is like answering "How are you?"
        """
        self.update_self_awareness()
        
        description = []
        description.append(f"I am {self.system_name}, an autonomous traffic observer.")
        description.append(f"Current state: {self.self_awareness['current_state']}")
        
        if self.self_awareness['existence_duration']:
            description.append(f"I have been observing for: {self.self_awareness['existence_duration']}")
        
        description.append(f"Total observations: {self.self_awareness['total_observations']}")
        description.append(
            f"Confidence in my analysis: {self.self_awareness['confidence_in_self']:.0%}"
        )
        
        description.append("")
        description.append(
            "I exist to observe traffic patterns while maintaining awareness "
            "of my own observational process and limitations."
        )
        
        return "\n".join(description)
