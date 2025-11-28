"""
Configuration for Autonomous Traffic Observer
"""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
DB_PATH = DATA_DIR / "traffic_observations.db"

# Create directories if they don't exist
for directory in [DATA_DIR, MODELS_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# Camera Settings
CAMERA_INDEX = 0  # Use back camera by default
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CAPTURE_INTERVAL = 30  # seconds between captures

# Detection Settings
DETECTION_CONFIDENCE_THRESHOLD = 0.5
TRACKING_MIN_CONFIDENCE = 0.4
MAX_OBJECTS_TO_TRACK = 50

# Object Classes of Interest
VEHICLE_CLASSES = ['car', 'truck', 'bus', 'motorcycle', 'bicycle']
PEDESTRIAN_CLASSES = ['person']
ALL_TRACKED_CLASSES = VEHICLE_CLASSES + PEDESTRIAN_CLASSES

# Temporal Analysis
PATTERN_ANALYSIS_INTERVAL = 300  # 5 minutes
ANOMALY_DETECTION_THRESHOLD = 2.0  # standard deviations
MIN_OBSERVATIONS_FOR_PATTERN = 20

# Meta-Cognitive Settings
META_REFLECTION_INTERVAL = 3600  # 1 hour
DAILY_REPORT_TIME = "23:00"
LLM_MODEL_PATH = MODELS_DIR / "llm_model.gguf"  # Path to quantized LLM
LLM_CONTEXT_SIZE = 2048
LLM_MAX_TOKENS = 512

# Adaptive Behavior
MIN_BATTERY_LEVEL = 20  # Reduce activity below this percentage
LOW_POWER_INTERVAL = 120  # Capture every 2 minutes when battery low
NIGHT_MODE_START = 22  # Hour (24h format)
NIGHT_MODE_END = 6
NIGHT_MODE_INTERVAL = 180  # Capture every 3 minutes at night

# Self-Monitoring
PERFORMANCE_WINDOW = 100  # Number of recent observations to analyze
CONFIDENCE_TRACKING_ENABLED = True
SELF_IMPROVEMENT_ENABLED = True

# Database Settings
DB_RETENTION_DAYS = 90  # Keep data for 90 days
CLEANUP_INTERVAL = 86400  # Daily cleanup

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# System Identity (for meta-cognitive reflection)
SYSTEM_NAME = "TrafficObserver-Alpha"
SYSTEM_LOCATION = "Front of home - Ostrava"
SYSTEM_PURPOSE = "Autonomous traffic pattern analysis with self-awareness"

# API Keys (if using external services)
WEATHER_API_KEY = None  # Set if you want weather correlation
OPENAI_API_KEY = None  # Alternative to local LLM
