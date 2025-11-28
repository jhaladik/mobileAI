"""
Smart Street Observer v2
- Motion-triggered capture
- ML object detection (MobileNet SSD)
- Only saves frames with activity
- Logs events with timestamps
"""

import cv2
import numpy as np
import subprocess
import json
import os
import time
from datetime import datetime
from pathlib import Path
from PIL import Image

# Configuration
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
LOG_FILE = BASE_DIR / "street_log.txt"

CAPTURE_INTERVAL = 10  # seconds between checks
MOTION_THRESHOLD = 3.0  # % of pixels changed to trigger
DETECTION_CONFIDENCE = 0.30  # 30% confidence threshold

# MobileNet SSD classes
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
           "sofa", "train", "tvmonitor"]

TRAFFIC_CLASSES = {"person", "bicycle", "car", "motorbike", "bus"}


class SmartObserver:
    def __init__(self):
        print("Initializing Smart Street Observer...")

        # Load ML model
        prototxt = str(MODELS_DIR / "MobileNetSSD_deploy.prototxt")
        caffemodel = str(MODELS_DIR / "MobileNetSSD_deploy.caffemodel")
        self.net = cv2.dnn.readNetFromCaffe(prototxt, caffemodel)
        print("  ML model loaded")

        # Motion detection
        self.prev_frame = None
        self.frame_count = 0
        self.events_today = {"person": 0, "car": 0, "bicycle": 0, "motorbike": 0, "bus": 0}

        # Ensure directories exist
        DATA_DIR.mkdir(exist_ok=True)

        print("  Ready!")

    def log_event(self, message):
        """Log event with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)

        with open(LOG_FILE, "a") as f:
            f.write(log_line + "\n")

    def capture_frame(self):
        """Capture frame from camera"""
        temp_path = str(DATA_DIR / "temp_frame.jpg")

        try:
            result = subprocess.run(
                ['termux-camera-photo', '-c', '0', temp_path],
                capture_output=True,
                timeout=15
            )

            if result.returncode == 0:
                img = Image.open(temp_path)
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                # Phone in landscape - no rotation needed
                return frame
        except Exception as e:
            print(f"  Capture error: {e}")

        return None

    def detect_motion(self, frame):
        """Detect motion compared to previous frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        gray = cv2.resize(gray, (320, 240))  # Smaller for speed

        if self.prev_frame is None:
            self.prev_frame = gray
            return 0.0

        diff = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]

        motion_pct = (np.sum(thresh > 0) / thresh.size) * 100
        self.prev_frame = gray

        return motion_pct

    def detect_objects(self, frame):
        """Detect objects using MobileNet SSD"""
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)),
            0.007843, (300, 300), 127.5
        )
        self.net.setInput(blob)
        detections = self.net.forward()

        results = []
        h, w = frame.shape[:2]

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]

            if confidence > DETECTION_CONFIDENCE:
                idx = int(detections[0, 0, i, 1])
                label = CLASSES[idx]

                if label in TRAFFIC_CLASSES:
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    results.append({
                        "class": label,
                        "confidence": float(confidence),
                        "box": box.astype("int").tolist()
                    })

        return results

    def save_frame(self, frame, detections):
        """Save frame with detections drawn"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"event_{timestamp}.jpg"
        filepath = DATA_DIR / filename

        # Draw detections on frame
        for det in detections:
            x1, y1, x2, y2 = det["box"]
            label = f"{det['class']}: {det['confidence']:.0%}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imwrite(str(filepath), frame)
        return filename

    def get_battery(self):
        """Get battery level"""
        try:
            result = subprocess.run(
                ['termux-battery-status'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get('percentage', None)
        except:
            pass
        return None

    def run(self):
        """Main observation loop"""
        self.log_event("=== Smart Street Observer Started ===")
        battery = self.get_battery()
        if battery:
            self.log_event(f"Battery: {battery}%")

        try:
            while True:
                self.frame_count += 1

                # Capture frame
                frame = self.capture_frame()
                if frame is None:
                    time.sleep(CAPTURE_INTERVAL)
                    continue

                # Check for motion
                motion = self.detect_motion(frame)

                if motion < MOTION_THRESHOLD:
                    # No significant motion, skip ML detection
                    if self.frame_count % 10 == 0:  # Log every 10th frame
                        print(f"  Frame {self.frame_count}: No motion ({motion:.1f}%)")
                    time.sleep(CAPTURE_INTERVAL)
                    continue

                # Motion detected - run object detection
                print(f"  Frame {self.frame_count}: Motion detected ({motion:.1f}%)")
                detections = self.detect_objects(frame)

                if detections:
                    # Count objects
                    counts = {}
                    for det in detections:
                        cls = det["class"]
                        counts[cls] = counts.get(cls, 0) + 1
                        self.events_today[cls] = self.events_today.get(cls, 0) + 1

                    # Log event
                    desc = ", ".join([f"{c} {n}" for n, c in counts.items()])
                    self.log_event(f"DETECTED: {desc}")

                    # Save frame with annotations
                    filename = self.save_frame(frame.copy(), detections)
                    self.log_event(f"  Saved: {filename}")
                else:
                    print(f"    Motion but no objects detected")

                time.sleep(CAPTURE_INTERVAL)

        except KeyboardInterrupt:
            self.log_event("=== Observer Stopped ===")
            self.log_event(f"Today's summary: {self.events_today}")
            print("\n" + "="*50)
            print("SESSION SUMMARY")
            print("="*50)
            for obj, count in self.events_today.items():
                if count > 0:
                    print(f"  {obj}: {count}")
            print("="*50)


def main():
    print("""
    ╔═══════════════════════════════════════════════╗
    ║     Smart Street Observer v2                  ║
    ║                                               ║
    ║  Motion-triggered + ML object detection       ║
    ║  Press Ctrl+C to stop                         ║
    ╚═══════════════════════════════════════════════╝
    """)

    observer = SmartObserver()
    observer.run()


if __name__ == "__main__":
    main()
