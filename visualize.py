"""
Visualization and reporting utility
Generate human-readable reports of what the system has learned
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta
from data_store import DataStore
import config

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)

def visualize_hourly_pattern(hourly_data):
    """Create a simple ASCII visualization of hourly traffic"""
    if not hourly_data:
        print("No data available")
        return
    
    # Find max for scaling
    max_vehicles = max(d['avg_vehicles'] for d in hourly_data)
    
    if max_vehicles == 0:
        print("No vehicles detected in data")
        return
    
    print("\nHourly Traffic Pattern (24-hour view)")
    print("Hour | Traffic")
    print("-----+-" + "-"*50)
    
    for hour in range(24):
        hour_data = [d for d in hourly_data if d['hour'] == hour]
        if hour_data:
            avg = hour_data[0]['avg_vehicles']
            bar_length = int((avg / max_vehicles) * 50)
            bar = "█" * bar_length
            print(f"{hour:02d}   | {bar} {avg:.1f}")
        else:
            print(f"{hour:02d}   | (no data)")

def show_dashboard():
    """Show a comprehensive dashboard of system state"""
    data_store = DataStore()
    
    print("\n" + "╔" + "═"*68 + "╗")
    print("║" + " "*15 + "AUTONOMOUS TRAFFIC OBSERVER DASHBOARD" + " "*15 + "║")
    print("╚" + "═"*68 + "╝")
    
    # System Overview
    print_section("System Overview")
    
    state = data_store.get_current_state('self_awareness')
    if state:
        import json
        metadata = json.loads(state['metadata'])
        print(f"System Name:        {config.SYSTEM_NAME}")
        print(f"Location:           {config.SYSTEM_LOCATION}")
        print(f"Current State:      {metadata.get('current_state', 'unknown')}")
        print(f"Total Observations: {metadata.get('total_observations', 0)}")
        print(f"Existence Duration: {metadata.get('existence_duration', 'unknown')}")
        print(f"Self-Confidence:    {metadata.get('confidence_in_self', 0):.0%}")
    else:
        print("System not yet initialized. Run init_database.py first.")
        return
    
    # Recent Statistics
    print_section("Last 24 Hours")
    
    stats = data_store.get_traffic_statistics(hours=24)
    print(f"Observations:       {stats.get('observation_count', 0)}")
    print(f"Total Vehicles:     {stats.get('total_vehicles', 0)}")
    print(f"Total Pedestrians:  {stats.get('total_pedestrians', 0)}")
    print(f"Avg per Observation: {stats.get('avg_vehicles_per_observation', 0):.1f} vehicles")
    print(f"Detection Confidence: {stats.get('avg_detection_confidence', 0):.0%}")
    
    # Hourly Pattern
    print_section("Traffic Patterns (Last 7 Days)")
    
    hourly_data = data_store.get_hourly_traffic_pattern(days=7)
    visualize_hourly_pattern(hourly_data)
    
    # Discovered Patterns
    print_section("Discovered Patterns")
    
    patterns = data_store.get_patterns()
    if patterns:
        for i, pattern in enumerate(patterns[:10], 1):
            print(f"\n{i}. {pattern['pattern_type'].replace('_', ' ').title()}")
            print(f"   {pattern['description']}")
            print(f"   Confidence: {pattern['confidence']:.0%}")
    else:
        print("No patterns detected yet. More data needed.")
    
    # Recent Anomalies
    print_section("Recent Anomalies (Last 24 Hours)")
    
    anomalies = data_store.get_recent_anomalies(hours=24)
    if anomalies:
        for i, anomaly in enumerate(anomalies[:5], 1):
            timestamp = datetime.fromisoformat(anomaly['timestamp'])
            print(f"\n{i}. {anomaly['anomaly_type'].replace('_', ' ').title()}")
            print(f"   Time: {timestamp.strftime('%Y-%m-%d %H:%M')}")
            print(f"   {anomaly['description']}")
            print(f"   Severity: {anomaly['severity']:.0%}")
    else:
        print("No anomalies detected.")
    
    # Latest Meta-Reflections
    print_section("Recent Meta-Cognitive Reflections")
    
    reflections = data_store.get_meta_reflections(limit=3)
    if reflections:
        for i, reflection in enumerate(reflections, 1):
            timestamp = datetime.fromisoformat(reflection['timestamp'])
            print(f"\n{i}. {reflection['reflection_type'].title()} Reflection")
            print(f"   Time: {timestamp.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Observations analyzed: {reflection['observations_analyzed']}")
            print(f"   Confidence: {reflection['confidence_in_insights']:.0%}")
            print("\n   Excerpt:")
            # Print first few lines
            lines = reflection['content'].split('\n')[:5]
            for line in lines:
                if line.strip():
                    print(f"   {line}")
    else:
        print("No reflections yet.")
    
    # Performance Metrics
    print_section("System Performance")
    
    perf_metrics = data_store.get_performance_trends('processing_time', hours=24)
    if perf_metrics:
        import numpy as np
        times = [m['metric_value'] for m in perf_metrics]
        print(f"Processing Time:")
        print(f"  Average: {np.mean(times):.3f}s")
        print(f"  Min:     {np.min(times):.3f}s")
        print(f"  Max:     {np.max(times):.3f}s")
    
    self_conf = data_store.get_performance_trends('self_confidence', hours=24)
    if self_conf:
        latest = self_conf[0]['metric_value']
        print(f"\nSelf-Confidence: {latest:.0%}")
    
    # Footer
    print("\n" + "="*70)
    print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

def show_latest_reflection():
    """Show the most recent meta-cognitive reflection"""
    data_store = DataStore()
    
    reflections = data_store.get_meta_reflections(limit=1)
    if reflections:
        reflection = reflections[0]
        print("\n" + "="*70)
        print("LATEST META-COGNITIVE REFLECTION")
        print("="*70)
        timestamp = datetime.fromisoformat(reflection['timestamp'])
        print(f"Type: {reflection['reflection_type']}")
        print(f"Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Observations analyzed: {reflection['observations_analyzed']}")
        print("="*70 + "\n")
        print(reflection['content'])
        print("\n" + "="*70 + "\n")
    else:
        print("No reflections available yet.")

def export_data(output_file: str = "traffic_data_export.json"):
    """Export data to JSON for external analysis"""
    import json
    
    data_store = DataStore()
    
    export = {
        'exported_at': datetime.now().isoformat(),
        'statistics': data_store.get_traffic_statistics(hours=24*7),
        'patterns': data_store.get_patterns(),
        'hourly_pattern': data_store.get_hourly_traffic_pattern(days=7),
        'anomalies': data_store.get_recent_anomalies(hours=24*7),
        'meta_reflections': data_store.get_meta_reflections(limit=10)
    }
    
    with open(output_file, 'w') as f:
        json.dump(export, f, indent=2)
    
    print(f"Data exported to: {output_file}")

def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "reflection":
            show_latest_reflection()
        elif command == "export":
            output_file = sys.argv[2] if len(sys.argv) > 2 else "traffic_data_export.json"
            export_data(output_file)
        elif command == "help":
            print("""
Autonomous Traffic Observer - Visualization Tool

Usage:
  python visualize.py              - Show dashboard
  python visualize.py reflection   - Show latest reflection
  python visualize.py export [file] - Export data to JSON
  python visualize.py help         - Show this help
            """)
        else:
            print(f"Unknown command: {command}")
            print("Run 'python visualize.py help' for usage")
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
