"""
Test script to verify all components are working
Run this before starting the full system
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required packages are installed"""
    print("Testing imports...")
    
    try:
        import numpy as np
        print("  ✓ numpy")
    except ImportError as e:
        print(f"  ✗ numpy - {e}")
        return False
    
    try:
        import cv2
        print("  ✓ opencv-python")
    except ImportError as e:
        print(f"  ✗ opencv-python - {e}")
        return False
    
    try:
        from PIL import Image
        print("  ✓ Pillow")
    except ImportError as e:
        print(f"  ✗ Pillow - {e}")
        return False
    
    try:
        import schedule
        print("  ✓ schedule")
    except ImportError as e:
        print(f"  ✗ schedule - {e}")
        return False
    
    try:
        from scipy import stats
        print("  ✓ scipy")
    except ImportError as e:
        print(f"  ✗ scipy - {e}")
        return False
    
    print("All imports successful!\n")
    return True

def test_database():
    """Test database functionality"""
    print("Testing database...")
    
    try:
        from data_store import DataStore
        db = DataStore()
        
        # Test basic operations
        obs_id = db.save_observation(
            detections=[{'class': 'car', 'confidence': 0.9}],
            processing_time=0.5,
            battery_level=100
        )
        print(f"  ✓ Database write (observation #{obs_id})")
        
        stats = db.get_traffic_statistics(hours=1)
        print(f"  ✓ Database read (found {stats.get('observation_count', 0)} observations)")
        
        print("Database test successful!\n")
        return True
        
    except Exception as e:
        print(f"  ✗ Database test failed: {e}\n")
        return False

def test_camera():
    """Test camera access"""
    print("Testing camera access...")
    
    try:
        from vision_processor import VisionProcessor
        vision = VisionProcessor()
        
        # Try to capture a frame
        frame = vision.capture_frame()
        
        if frame is not None:
            print(f"  ✓ Camera capture successful (frame shape: {frame.shape})")
            
            # Test basic processing
            result = vision.process_frame(frame)
            print(f"  ✓ Frame processing (detected {len(result['detections'])} objects)")
            
            print("Camera test successful!\n")
            return True
        else:
            print("  ✗ Camera capture returned None")
            print("  This might be normal if:")
            print("    - Termux doesn't have camera permission")
            print("    - You're running in an environment without camera")
            print("    - Camera is already in use\n")
            return False
            
    except Exception as e:
        print(f"  ✗ Camera test failed: {e}")
        print("  Note: Camera functionality requires Termux:API on Android\n")
        return False

def test_sensors():
    """Test sensor access (battery, light)"""
    print("Testing sensor access...")
    
    try:
        from vision_processor import get_battery_level, get_light_level
        
        battery = get_battery_level()
        if battery is not None:
            print(f"  ✓ Battery sensor (level: {battery}%)")
        else:
            print("  ⚠ Battery sensor not available (may be normal)")
        
        light = get_light_level()
        if light is not None:
            print(f"  ✓ Light sensor (level: {light})")
        else:
            print("  ⚠ Light sensor not available (may be normal)")
        
        print("Sensor test complete!\n")
        return True
        
    except Exception as e:
        print(f"  ✗ Sensor test failed: {e}\n")
        return False

def test_components():
    """Test individual components"""
    print("Testing system components...")
    
    try:
        from data_store import DataStore
        from temporal_analyzer import TemporalAnalyzer
        from meta_cognition import MetaCognition
        
        db = DataStore()
        print("  ✓ DataStore")
        
        temporal = TemporalAnalyzer(db)
        print("  ✓ TemporalAnalyzer")
        
        meta = MetaCognition(db)
        print("  ✓ MetaCognition")
        
        # Test temporal analysis
        analysis = temporal.analyze_recent_patterns(hours=1)
        print(f"  ✓ Temporal analysis (found {len(analysis['patterns_detected'])} patterns)")
        
        # Test meta-cognition
        self_desc = meta.get_self_description()
        print("  ✓ Meta-cognitive self-description")
        
        print("Component test successful!\n")
        return True
        
    except Exception as e:
        print(f"  ✗ Component test failed: {e}\n")
        return False

def test_file_permissions():
    """Test that we can write to required directories"""
    print("Testing file permissions...")
    
    try:
        import config
        
        # Test data directory
        test_file = config.DATA_DIR / "test.txt"
        test_file.write_text("test")
        test_file.unlink()
        print(f"  ✓ Can write to {config.DATA_DIR}")
        
        # Test logs directory
        test_file = config.LOGS_DIR / "test.txt"
        test_file.write_text("test")
        test_file.unlink()
        print(f"  ✓ Can write to {config.LOGS_DIR}")
        
        print("File permission test successful!\n")
        return True
        
    except Exception as e:
        print(f"  ✗ File permission test failed: {e}\n")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("AUTONOMOUS TRAFFIC OBSERVER - SYSTEM TEST")
    print("="*70 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("File Permissions", test_file_permissions()))
    results.append(("Database", test_database()))
    results.append(("Components", test_components()))
    results.append(("Sensors", test_sensors()))
    results.append(("Camera", test_camera()))
    
    # Summary
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:20} {status}")
    
    print("="*70 + "\n")
    
    # Overall result
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    if passed_count == total_count:
        print("🎉 All tests passed! System is ready to run.")
        print("\nNext steps:")
        print("  1. Position your phone to view the street")
        print("  2. Run: python orchestrator.py")
        print("  3. Monitor with: python visualize.py")
    else:
        print(f"⚠️  {total_count - passed_count} test(s) failed.")
        print("\nSome functionality may not work. Common issues:")
        print("  - Camera: Requires Termux:API and permissions")
        print("  - Sensors: May not be available on all devices")
        print("  - Most tests should pass for basic functionality")
        
        if passed_count >= 4:  # If core tests pass
            print("\nCore components are working. You can still run the system,")
            print("but some features (like camera) may not work.")
    
    print()

if __name__ == "__main__":
    main()
