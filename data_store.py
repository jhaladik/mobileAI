"""
Data storage and retrieval for the Autonomous Traffic Observer
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import config

class DataStore:
    def __init__(self, db_path: str = str(config.DB_PATH)):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Observations table - what the system sees
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                frame_path TEXT,
                detection_count INTEGER,
                detections JSON,
                processing_time REAL,
                confidence_avg REAL,
                battery_level INTEGER,
                light_level REAL,
                notes TEXT
            )
        """)
        
        # Traffic events table - aggregated vehicle counts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traffic_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                vehicle_count INTEGER,
                pedestrian_count INTEGER,
                bicycle_count INTEGER,
                vehicle_types JSON,
                avg_confidence REAL,
                observation_id INTEGER,
                FOREIGN KEY (observation_id) REFERENCES observations(id)
            )
        """)
        
        # Patterns table - learned temporal patterns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                pattern_type TEXT,
                description TEXT,
                time_window TEXT,
                confidence REAL,
                supporting_observations INTEGER,
                metadata JSON
            )
        """)
        
        # Performance metrics - system self-monitoring
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric_type TEXT,
                metric_value REAL,
                context JSON,
                notes TEXT
            )
        """)
        
        # Meta-cognitive reflections - system's thoughts about itself
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meta_reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                reflection_type TEXT,
                content TEXT,
                insights JSON,
                confidence_in_insights REAL,
                observations_analyzed INTEGER
            )
        """)
        
        # System state - internal awareness
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                state_type TEXT,
                state_value TEXT,
                metadata JSON
            )
        """)
        
        # Anomalies - detected unusual events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                anomaly_type TEXT,
                description TEXT,
                severity REAL,
                baseline_value REAL,
                observed_value REAL,
                observation_id INTEGER,
                FOREIGN KEY (observation_id) REFERENCES observations(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    # Observation methods
    def save_observation(self, detections: List[Dict], 
                        processing_time: float,
                        battery_level: int = None,
                        light_level: float = None,
                        frame_path: str = None) -> int:
        """Save a single observation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        detection_count = len(detections)
        confidence_avg = sum(d.get('confidence', 0) for d in detections) / detection_count if detection_count > 0 else 0
        
        cursor.execute("""
            INSERT INTO observations 
            (frame_path, detection_count, detections, processing_time, 
             confidence_avg, battery_level, light_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (frame_path, detection_count, json.dumps(detections), processing_time,
              confidence_avg, battery_level, light_level))
        
        observation_id = cursor.lastrowid
        
        # Also save traffic event summary
        vehicle_count = sum(1 for d in detections if d.get('class') in config.VEHICLE_CLASSES)
        pedestrian_count = sum(1 for d in detections if d.get('class') in config.PEDESTRIAN_CLASSES)
        bicycle_count = sum(1 for d in detections if d.get('class') == 'bicycle')
        
        vehicle_types = {}
        for d in detections:
            cls = d.get('class', 'unknown')
            vehicle_types[cls] = vehicle_types.get(cls, 0) + 1
        
        cursor.execute("""
            INSERT INTO traffic_events
            (vehicle_count, pedestrian_count, bicycle_count, vehicle_types, 
             avg_confidence, observation_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (vehicle_count, pedestrian_count, bicycle_count, 
              json.dumps(vehicle_types), confidence_avg, observation_id))
        
        conn.commit()
        conn.close()
        return observation_id
    
    def get_recent_observations(self, hours: int = 24, limit: int = None) -> List[Dict]:
        """Get recent observations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        
        query = """
            SELECT * FROM observations 
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, (since,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    # Traffic analysis methods
    def get_traffic_statistics(self, hours: int = 24) -> Dict:
        """Get traffic statistics for a time period"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as observation_count,
                SUM(vehicle_count) as total_vehicles,
                SUM(pedestrian_count) as total_pedestrians,
                AVG(vehicle_count) as avg_vehicles_per_observation,
                AVG(avg_confidence) as avg_detection_confidence
            FROM traffic_events
            WHERE timestamp > ?
        """, (since,))
        
        result = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        stats = dict(zip(columns, result))
        
        conn.close()
        return stats
    
    def get_hourly_traffic_pattern(self, days: int = 7) -> List[Dict]:
        """Get average traffic by hour of day"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
            SELECT 
                CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                AVG(vehicle_count) as avg_vehicles,
                AVG(pedestrian_count) as avg_pedestrians,
                COUNT(*) as sample_count
            FROM traffic_events
            WHERE timestamp > ?
            GROUP BY hour
            ORDER BY hour
        """, (since,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    # Pattern methods
    def save_pattern(self, pattern_type: str, description: str,
                    time_window: str, confidence: float,
                    supporting_observations: int,
                    metadata: Dict = None) -> int:
        """Save a discovered pattern"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO patterns
            (pattern_type, description, time_window, confidence,
             supporting_observations, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pattern_type, description, time_window, confidence,
              supporting_observations, json.dumps(metadata or {})))
        
        pattern_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return pattern_id
    
    def get_patterns(self, pattern_type: str = None) -> List[Dict]:
        """Get discovered patterns"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if pattern_type:
            cursor.execute("""
                SELECT * FROM patterns 
                WHERE pattern_type = ?
                ORDER BY confidence DESC, discovered_at DESC
            """, (pattern_type,))
        else:
            cursor.execute("""
                SELECT * FROM patterns 
                ORDER BY confidence DESC, discovered_at DESC
            """)
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    # Performance tracking methods
    def save_performance_metric(self, metric_type: str, metric_value: float,
                               context: Dict = None, notes: str = None):
        """Save a performance metric"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO performance_metrics
            (metric_type, metric_value, context, notes)
            VALUES (?, ?, ?, ?)
        """, (metric_type, metric_value, json.dumps(context or {}), notes))
        
        conn.commit()
        conn.close()
    
    def get_performance_trends(self, metric_type: str, hours: int = 24) -> List[Dict]:
        """Get performance metric trends"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        
        cursor.execute("""
            SELECT * FROM performance_metrics
            WHERE metric_type = ? AND timestamp > ?
            ORDER BY timestamp DESC
        """, (metric_type, since))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    # Meta-cognitive methods
    def save_meta_reflection(self, reflection_type: str, content: str,
                           insights: Dict = None, confidence: float = 0.5,
                           observations_analyzed: int = 0) -> int:
        """Save a meta-cognitive reflection"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO meta_reflections
            (reflection_type, content, insights, confidence_in_insights,
             observations_analyzed)
            VALUES (?, ?, ?, ?, ?)
        """, (reflection_type, content, json.dumps(insights or {}),
              confidence, observations_analyzed))
        
        reflection_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return reflection_id
    
    def get_meta_reflections(self, reflection_type: str = None, limit: int = 10) -> List[Dict]:
        """Get recent meta-cognitive reflections"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if reflection_type:
            cursor.execute("""
                SELECT * FROM meta_reflections
                WHERE reflection_type = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (reflection_type, limit))
        else:
            cursor.execute("""
                SELECT * FROM meta_reflections
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    # Anomaly methods
    def save_anomaly(self, anomaly_type: str, description: str,
                    severity: float, baseline_value: float,
                    observed_value: float, observation_id: int = None):
        """Save a detected anomaly"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO anomalies
            (anomaly_type, description, severity, baseline_value,
             observed_value, observation_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (anomaly_type, description, severity, baseline_value,
              observed_value, observation_id))
        
        conn.commit()
        conn.close()
    
    def get_recent_anomalies(self, hours: int = 24) -> List[Dict]:
        """Get recent anomalies"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        
        cursor.execute("""
            SELECT * FROM anomalies
            WHERE timestamp > ?
            ORDER BY severity DESC, timestamp DESC
        """, (since,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    # System state methods
    def update_system_state(self, state_type: str, state_value: str, metadata: Dict = None):
        """Update system state"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO system_state
            (state_type, state_value, metadata)
            VALUES (?, ?, ?)
        """, (state_type, state_value, json.dumps(metadata or {})))
        
        conn.commit()
        conn.close()
    
    def get_current_state(self, state_type: str) -> Optional[Dict]:
        """Get most recent system state"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM system_state
            WHERE state_type = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (state_type,))
        
        result = cursor.fetchone()
        if result:
            columns = [desc[0] for desc in cursor.description]
            state = dict(zip(columns, result))
        else:
            state = None
        
        conn.close()
        return state
    
    # Cleanup methods
    def cleanup_old_data(self, days: int = config.DB_RETENTION_DAYS):
        """Remove old data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff = datetime.now() - timedelta(days=days)
        
        tables = ['observations', 'traffic_events', 'patterns', 
                 'performance_metrics', 'meta_reflections', 'anomalies']
        
        for table in tables:
            cursor.execute(f"DELETE FROM {table} WHERE timestamp < ?", (cutoff,))
        
        conn.commit()
        conn.close()
