"""
Vision processing and object detection for traffic analysis
"""

import cv2
import numpy as np
import time
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import logging
import config

logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class VisionProcessor:
    def __init__(self):
        self.camera_index = config.CAMERA_INDEX
        self.frame_width = config.FRAME_WIDTH
        self.frame_height = config.FRAME_HEIGHT
        self.confidence_threshold = config.DETECTION_CONFIDENCE_THRESHOLD
        
        # Initialize detector (we'll start with background subtraction, then add ML)
        self.detector = None
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=True
        )
        
        # Performance tracking
        self.processing_times = []
        self.detection_confidences = []
        
        logger.info("VisionProcessor initialized")
    
    def capture_frame(self, save_path: Optional[str] = None) -> Optional[np.ndarray]:
        """
        Capture a single frame from camera
        On Android/Termux, we'll use termux-camera-photo command
        """
        try:
            # For Termux on Android
            import subprocess
            from PIL import Image
            
            # Use termux-camera-photo to capture
            temp_path = "/data/data/com.termux/files/home/traffic_observer/data/traffic_frame.jpg"
            result = subprocess.run(
                ['termux-camera-photo', '-c', str(self.camera_index), temp_path],
                capture_output=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Load and optionally resize
                img = Image.open(temp_path)
                img = img.resize((self.frame_width, self.frame_height))
                
                if save_path:
                    img.save(save_path)
                
                # Convert to numpy array for OpenCV
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                logger.debug(f"Frame captured: {frame.shape}")
                return frame
            else:
                logger.error(f"Camera capture failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            return None
    
    def detect_motion(self, frame: np.ndarray) -> Tuple[bool, float]:
        """
        Detect if there's significant motion in frame
        Returns: (has_motion, motion_percentage)
        """
        try:
            # Apply background subtraction
            fg_mask = self.background_subtractor.apply(frame)
            
            # Calculate percentage of foreground pixels
            motion_pixels = np.sum(fg_mask > 0)
            total_pixels = fg_mask.size
            motion_percentage = (motion_pixels / total_pixels) * 100
            
            # Motion threshold (configurable)
            has_motion = motion_percentage > 1.0  # More than 1% change
            
            return has_motion, motion_percentage
            
        except Exception as e:
            logger.error(f"Error in motion detection: {e}")
            return False, 0.0
    
    def detect_objects_basic(self, frame: np.ndarray) -> List[Dict]:
        """
        Basic object detection using classical CV methods
        This is a fallback/baseline before we load ML models
        """
        detections = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            # Filter and analyze contours
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filter by size (vehicles should be reasonably large)
                if area > 1000:  # Minimum area threshold
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    
                    # Heuristic: vehicles typically have aspect ratio between 0.5 and 3
                    if 0.5 < aspect_ratio < 3:
                        detection = {
                            'class': 'vehicle',  # Generic for now
                            'confidence': min(0.6, area / 10000),  # Rough confidence based on size
                            'bbox': [x, y, w, h],
                            'area': area
                        }
                        detections.append(detection)
            
            logger.debug(f"Basic detection found {len(detections)} objects")
            
        except Exception as e:
            logger.error(f"Error in basic detection: {e}")
        
        return detections
    
    def detect_objects_ml(self, frame: np.ndarray) -> List[Dict]:
        """
        ML-based object detection using TensorFlow Lite
        We'll implement this with MobileNet SSD
        """
        detections = []
        
        try:
            # TODO: Load and run TFLite model
            # For now, this will use basic detection
            # We'll implement this in the next iteration
            
            # Placeholder for TFLite inference
            # interpreter = tflite.Interpreter(model_path=model_path)
            # ...
            
            logger.debug("ML detection not yet implemented, using basic detection")
            return self.detect_objects_basic(frame)
            
        except Exception as e:
            logger.error(f"Error in ML detection: {e}")
            return []
    
    def process_frame(self, frame: np.ndarray, use_ml: bool = False) -> Dict:
        """
        Complete frame processing pipeline
        Returns detection results and metadata
        """
        start_time = time.time()
        
        result = {
            'timestamp': time.time(),
            'detections': [],
            'motion_detected': False,
            'motion_percentage': 0.0,
            'processing_time': 0.0,
            'frame_quality': 1.0
        }
        
        try:
            # Check for motion
            has_motion, motion_pct = self.detect_motion(frame)
            result['motion_detected'] = has_motion
            result['motion_percentage'] = motion_pct
            
            # Only run detection if motion detected (saves processing)
            if has_motion or not use_ml:  # Always detect in non-ML mode for testing
                if use_ml:
                    detections = self.detect_objects_ml(frame)
                else:
                    detections = self.detect_objects_basic(frame)
                
                # Filter by confidence threshold
                detections = [
                    d for d in detections 
                    if d.get('confidence', 0) >= self.confidence_threshold
                ]
                
                result['detections'] = detections
                
                # Track detection quality
                if detections:
                    avg_confidence = sum(d['confidence'] for d in detections) / len(detections)
                    self.detection_confidences.append(avg_confidence)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            self.processing_times.append(processing_time)
            
            # Assess frame quality (based on blur detection)
            laplacian_var = cv2.Laplacian(
                cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.CV_64F
            ).var()
            result['frame_quality'] = min(1.0, laplacian_var / 500)
            
            logger.info(f"Processed frame: {len(result['detections'])} detections in {processing_time:.3f}s")
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
        
        return result
    
    def get_performance_stats(self) -> Dict:
        """
        Get current performance statistics
        This is for self-monitoring
        """
        stats = {
            'avg_processing_time': 0.0,
            'min_processing_time': 0.0,
            'max_processing_time': 0.0,
            'avg_confidence': 0.0,
            'total_frames_processed': len(self.processing_times)
        }
        
        if self.processing_times:
            stats['avg_processing_time'] = np.mean(self.processing_times)
            stats['min_processing_time'] = np.min(self.processing_times)
            stats['max_processing_time'] = np.max(self.processing_times)
        
        if self.detection_confidences:
            stats['avg_confidence'] = np.mean(self.detection_confidences)
        
        return stats
    
    def classify_vehicle_type(self, detection: Dict) -> str:
        """
        Attempt to classify vehicle type based on size and aspect ratio
        This is a heuristic until we have proper ML classification
        """
        if 'bbox' not in detection:
            return 'unknown'
        
        _, _, w, h = detection['bbox']
        area = detection.get('area', w * h)
        aspect_ratio = w / h if h > 0 else 0
        
        # Simple heuristics
        if aspect_ratio > 2.5:
            return 'truck' if area > 5000 else 'car'
        elif aspect_ratio < 1.5 and area < 3000:
            return 'bicycle' if area < 2000 else 'motorcycle'
        else:
            return 'car'
    
    def analyze_traffic_flow(self, detections_over_time: List[List[Dict]]) -> Dict:
        """
        Analyze traffic flow from multiple frames
        Can estimate speed and direction (future enhancement)
        """
        analysis = {
            'total_detections': 0,
            'vehicles_per_frame': 0.0,
            'vehicle_types': {}
        }
        
        if not detections_over_time:
            return analysis
        
        total_detections = sum(len(frame_detections) for frame_detections in detections_over_time)
        analysis['total_detections'] = total_detections
        analysis['vehicles_per_frame'] = total_detections / len(detections_over_time)
        
        # Count vehicle types
        for frame_detections in detections_over_time:
            for detection in frame_detections:
                vehicle_type = self.classify_vehicle_type(detection)
                analysis['vehicle_types'][vehicle_type] = \
                    analysis['vehicle_types'].get(vehicle_type, 0) + 1
        
        return analysis
    
    def self_calibrate(self):
        """
        Self-calibration routine
        The system adjusts its own parameters based on performance
        """
        stats = self.get_performance_stats()
        
        # Adjust confidence threshold if we're getting too many/few detections
        if stats['avg_confidence'] < 0.4:
            self.confidence_threshold = max(0.3, self.confidence_threshold - 0.05)
            logger.info(f"Lowered confidence threshold to {self.confidence_threshold}")
        elif stats['avg_confidence'] > 0.9:
            self.confidence_threshold = min(0.8, self.confidence_threshold + 0.05)
            logger.info(f"Raised confidence threshold to {self.confidence_threshold}")
        
        # Reset tracking arrays (keep memory bounded)
        if len(self.processing_times) > config.PERFORMANCE_WINDOW:
            self.processing_times = self.processing_times[-config.PERFORMANCE_WINDOW:]
            self.detection_confidences = self.detection_confidences[-config.PERFORMANCE_WINDOW:]


# Utility functions
def get_battery_level() -> Optional[int]:
    """Get current battery level (Android/Termux specific)"""
    try:
        import subprocess
        result = subprocess.run(
            ['termux-battery-status'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            import json
            battery_info = json.loads(result.stdout)
            return battery_info.get('percentage', None)
    except Exception as e:
        logger.warning(f"Could not get battery level: {e}")
    return None


def get_light_level() -> Optional[float]:
    """Get ambient light level (if sensor available)"""
    try:
        import subprocess
        result = subprocess.run(
            ['termux-sensor', '-s', 'light', '-n', '1'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            import json
            sensor_data = json.loads(result.stdout)
            if sensor_data:
                return sensor_data[0].get('values', [None])[0]
    except Exception as e:
        logger.warning(f"Could not get light level: {e}")
    return None
