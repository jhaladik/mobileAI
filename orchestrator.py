"""
Main orchestrator - Coordinates all components and manages adaptive behavior
This is the "executive function" of the system
"""

import time
import schedule
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging
import signal
import sys

import config
from data_store import DataStore
from vision_processor import VisionProcessor, get_battery_level, get_light_level
from temporal_analyzer import TemporalAnalyzer
from meta_cognition import MetaCognition

logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class Orchestrator:
    """
    The orchestrator manages the entire system lifecycle:
    - Schedules observations based on adaptive rules
    - Coordinates between vision, temporal analysis, and meta-cognition
    - Adjusts behavior based on battery, time, and learned patterns
    - Manages system state and graceful shutdown
    """
    
    def __init__(self):
        logger.info("Initializing Orchestrator...")
        
        # Initialize components
        self.data_store = DataStore()
        self.vision = VisionProcessor()
        self.temporal = TemporalAnalyzer(self.data_store)
        self.meta = MetaCognition(self.data_store)
        
        # System state
        self.running = False
        self.observation_count = 0
        self.current_interval = config.CAPTURE_INTERVAL
        
        # Adaptive behavior state
        self.is_low_power_mode = False
        self.is_night_mode = False
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Orchestrator initialized successfully")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
        # Generate final reflection
        print("\nGenerating final reflection before shutdown...")
        self._perform_meta_reflection()
        
        sys.exit(0)
    
    def determine_capture_interval(self) -> int:
        """
        Adaptively determine capture interval based on:
        - Battery level
        - Time of day
        - Learned traffic patterns
        - Recent anomaly detection
        """
        interval = config.CAPTURE_INTERVAL
        
        # Check battery
        battery = get_battery_level()
        if battery and battery < config.MIN_BATTERY_LEVEL:
            logger.info(f"Low battery ({battery}%), entering low power mode")
            self.is_low_power_mode = True
            interval = config.LOW_POWER_INTERVAL
        else:
            self.is_low_power_mode = False
        
        # Check time of day
        current_hour = datetime.now().hour
        if config.NIGHT_MODE_START <= current_hour or current_hour < config.NIGHT_MODE_END:
            logger.debug("Night mode active")
            self.is_night_mode = True
            interval = max(interval, config.NIGHT_MODE_INTERVAL)
        else:
            self.is_night_mode = False
        
        # Check predicted traffic level
        prediction = self.temporal.predict_traffic_level()
        if prediction['predicted_level'] == 'high':
            # Increase sampling during high traffic
            interval = max(15, interval // 2)
            logger.debug("High traffic predicted, increasing sampling rate")
        elif prediction['predicted_level'] == 'low':
            # Decrease sampling during low traffic
            interval = min(120, interval * 2)
            logger.debug("Low traffic predicted, decreasing sampling rate")
        
        # Check for recent anomalies (increase sampling if detected)
        recent_anomalies = self.data_store.get_recent_anomalies(hours=1)
        if recent_anomalies:
            interval = max(20, interval // 2)
            logger.info(f"Recent anomalies detected, increasing sampling rate")
        
        if interval != self.current_interval:
            logger.info(f"Capture interval adjusted: {self.current_interval}s → {interval}s")
            self.current_interval = interval
        
        return interval
    
    def capture_and_analyze(self):
        """
        Main observation cycle: capture frame, detect objects, store data
        """
        try:
            logger.info(f"--- Observation #{self.observation_count + 1} ---")
            
            # Get current context
            battery = get_battery_level()
            light = get_light_level()
            
            # Capture frame
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            frame_path = config.DATA_DIR / f"frame_{timestamp}.jpg"
            
            frame = self.vision.capture_frame(save_path=str(frame_path))
            
            if frame is None:
                logger.warning("Failed to capture frame")
                return
            
            # Process frame
            result = self.vision.process_frame(frame, use_ml=False)  # Start with basic CV
            
            # Store observation
            observation_id = self.data_store.save_observation(
                detections=result['detections'],
                processing_time=result['processing_time'],
                battery_level=battery,
                light_level=light,
                frame_path=str(frame_path)
            )
            
            self.observation_count += 1
            
            # Log summary
            logger.info(
                f"Observation complete: {len(result['detections'])} objects detected, "
                f"processing time: {result['processing_time']:.3f}s, "
                f"battery: {battery}%"
            )
            
            # Store performance metrics
            self.data_store.save_performance_metric(
                metric_type='processing_time',
                metric_value=result['processing_time']
            )
            
            self.data_store.save_performance_metric(
                metric_type='detection_count',
                metric_value=len(result['detections'])
            )
            
            # Self-calibrate periodically
            if self.observation_count % 50 == 0:
                logger.info("Performing self-calibration...")
                self.vision.self_calibrate()
            
        except Exception as e:
            logger.error(f"Error in capture_and_analyze: {e}", exc_info=True)
    
    def _perform_temporal_analysis(self):
        """
        Perform temporal pattern analysis
        Runs every 5 minutes
        """
        try:
            logger.info("Performing temporal analysis...")
            
            analysis = self.temporal.analyze_recent_patterns(hours=24)
            
            # Update baseline if needed
            if self.observation_count % 100 == 0:
                logger.info("Recalculating baseline statistics...")
                self.temporal.calculate_baseline_statistics()
            
            logger.info(
                f"Temporal analysis complete: "
                f"{len(analysis['patterns_detected'])} patterns, "
                f"{len(analysis['anomalies_detected'])} anomalies"
            )
            
        except Exception as e:
            logger.error(f"Error in temporal analysis: {e}", exc_info=True)
    
    def _perform_meta_reflection(self):
        """
        Generate meta-cognitive reflection
        Runs hourly
        """
        try:
            logger.info("Generating meta-cognitive reflection...")
            
            # Get data for reflection
            temporal_insights = self.temporal.analyze_recent_patterns(hours=1)
            vision_stats = self.vision.get_performance_stats()
            
            # Generate reflection
            reflection = self.meta.generate_hourly_reflection(
                temporal_insights=temporal_insights,
                vision_stats=vision_stats
            )
            
            # Print to console (so user can see the system "thinking")
            print("\n" + "="*80)
            print("META-COGNITIVE REFLECTION")
            print("="*80)
            print(reflection)
            print("="*80 + "\n")
            
            # Update self-awareness
            self.meta.update_self_awareness()
            
            # Display self-description
            self_desc = self.meta.get_self_description()
            logger.info(f"System self-description:\n{self_desc}")
            
        except Exception as e:
            logger.error(f"Error in meta reflection: {e}", exc_info=True)
    
    def _generate_daily_report(self):
        """
        Generate comprehensive daily report
        Runs once per day
        """
        try:
            logger.info("Generating daily report...")
            
            report = self.meta.generate_daily_report()
            
            print("\n" + "="*80)
            print("DAILY REPORT")
            print("="*80)
            print(report)
            print("="*80 + "\n")
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}", exc_info=True)
    
    def _cleanup_old_data(self):
        """
        Cleanup old data to manage storage
        Runs daily
        """
        try:
            logger.info("Cleaning up old data...")
            self.data_store.cleanup_old_data(days=config.DB_RETENTION_DAYS)
            logger.info("Cleanup complete")
        except Exception as e:
            logger.error(f"Error in cleanup: {e}", exc_info=True)
    
    def setup_schedule(self):
        """
        Setup the schedule for all recurring tasks
        """
        # Main observation loop will be handled separately with adaptive intervals
        
        # Temporal analysis every 5 minutes
        schedule.every(config.PATTERN_ANALYSIS_INTERVAL).seconds.do(
            self._perform_temporal_analysis
        )
        
        # Meta-cognitive reflection every hour
        schedule.every(config.META_REFLECTION_INTERVAL).seconds.do(
            self._perform_meta_reflection
        )
        
        # Daily report
        schedule.every().day.at(config.DAILY_REPORT_TIME).do(
            self._generate_daily_report
        )
        
        # Daily cleanup
        schedule.every().day.at("03:00").do(
            self._cleanup_old_data
        )
        
        logger.info("Schedule configured")
    
    def run(self):
        """
        Main run loop - this is where the system comes alive
        """
        logger.info("="*80)
        logger.info(f"Starting {config.SYSTEM_NAME}")
        logger.info(f"Location: {config.SYSTEM_LOCATION}")
        logger.info(f"Purpose: {config.SYSTEM_PURPOSE}")
        logger.info("="*80)
        
        # Setup schedule
        self.setup_schedule()
        
        # Initial self-introduction
        print("\n" + self.meta.get_self_description() + "\n")
        
        # Mark system as running
        self.running = True
        self.data_store.update_system_state(
            state_type='system_status',
            state_value='running',
            metadata={'started_at': datetime.now().isoformat()}
        )
        
        # Main loop
        last_capture_time = time.time()
        
        try:
            while self.running:
                # Run scheduled tasks
                schedule.run_pending()
                
                # Check if it's time for next observation
                current_time = time.time()
                time_since_capture = current_time - last_capture_time
                
                # Determine adaptive interval
                interval = self.determine_capture_interval()
                
                if time_since_capture >= interval:
                    self.capture_and_analyze()
                    last_capture_time = current_time
                
                # Sleep briefly to prevent busy-waiting
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """
        Graceful shutdown
        """
        logger.info("Shutting down...")
        
        # Mark system as stopped
        self.data_store.update_system_state(
            state_type='system_status',
            state_value='stopped',
            metadata={'stopped_at': datetime.now().isoformat()}
        )
        
        # Final report
        print("\n" + "="*80)
        print("SHUTDOWN SUMMARY")
        print("="*80)
        print(f"Total observations: {self.observation_count}")
        print(f"System ran for: {self.meta.self_awareness.get('existence_duration', 'unknown')}")
        print(f"Final confidence: {self.meta.self_awareness.get('confidence_in_self', 0):.0%}")
        print("="*80 + "\n")
        
        logger.info("Shutdown complete")


def main():
    """
    Entry point
    """
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     Autonomous Traffic Observer - Self-Aware Edition      ║
    ║                                                           ║
    ║  A system that observes traffic and observes itself       ║
    ║  observing traffic. Meta-cognition meets edge AI.         ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    orchestrator = Orchestrator()
    orchestrator.run()


if __name__ == "__main__":
    main()
