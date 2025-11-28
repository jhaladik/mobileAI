#!/usr/bin/env python3
"""
YOLOv8n Object Detector using ONNX Runtime
Optimized for mobile/edge devices
"""

import numpy as np
import onnxruntime as ort
import cv2
from pathlib import Path

# COCO class names (80 classes)
COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
    'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
    'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
    'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
    'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
    'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
    'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
    'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
    'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
    'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
    'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
    'toothbrush'
]

# Classes we care about for traffic monitoring
TRAFFIC_CLASSES = {'person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck', 'dog', 'cat'}


class YOLOv8Detector:
    def __init__(self, model_path=None, conf_threshold=0.4, iou_threshold=0.45):
        """
        Initialize YOLOv8 detector with ONNX Runtime

        Args:
            model_path: Path to yolov8n.onnx model
            conf_threshold: Confidence threshold for detections
            iou_threshold: IoU threshold for NMS
        """
        if model_path is None:
            model_path = Path(__file__).parent / "models" / "yolov8n.onnx"

        self.model_path = Path(model_path)
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.session = None
        self.input_name = None
        self.input_shape = None

    def load(self):
        """Load the ONNX model"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        # Use NNAPI for Android hardware acceleration, fallback to CPU
        providers = ['NnapiExecutionProvider', 'XnnpackExecutionProvider', 'CPUExecutionProvider']

        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        self.session = ort.InferenceSession(
            str(self.model_path),
            sess_options=sess_options,
            providers=providers
        )

        # Get input details
        model_inputs = self.session.get_inputs()
        self.input_name = model_inputs[0].name
        self.input_shape = model_inputs[0].shape  # [batch, channels, height, width]

        print(f"Model loaded: {self.model_path.name}")
        print(f"Input shape: {self.input_shape}")
        print(f"Providers: {self.session.get_providers()}")

        return self

    def preprocess(self, image):
        """
        Preprocess image for YOLOv8

        Args:
            image: BGR image (numpy array)

        Returns:
            Preprocessed tensor and original image dimensions
        """
        original_h, original_w = image.shape[:2]

        # YOLOv8 expects 640x640 input
        input_h, input_w = 640, 640

        # Resize with letterboxing to maintain aspect ratio
        scale = min(input_w / original_w, input_h / original_h)
        new_w, new_h = int(original_w * scale), int(original_h * scale)

        # Resize image
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # Create letterbox image (gray padding)
        letterbox = np.full((input_h, input_w, 3), 114, dtype=np.uint8)

        # Calculate padding
        pad_x = (input_w - new_w) // 2
        pad_y = (input_h - new_h) // 2

        # Place resized image in center
        letterbox[pad_y:pad_y+new_h, pad_x:pad_x+new_w] = resized

        # Convert BGR to RGB
        rgb = cv2.cvtColor(letterbox, cv2.COLOR_BGR2RGB)

        # Normalize to [0, 1] and convert to float32
        blob = rgb.astype(np.float32) / 255.0

        # Transpose to NCHW format: [1, 3, 640, 640]
        blob = np.transpose(blob, (2, 0, 1))
        blob = np.expand_dims(blob, axis=0)

        return blob, (original_w, original_h, pad_x, pad_y, scale)

    def postprocess(self, outputs, image_info, filter_classes=None):
        """
        Process YOLOv8 outputs to get detections

        Args:
            outputs: Raw model outputs
            image_info: (original_w, original_h, pad_x, pad_y, scale)
            filter_classes: Set of class names to keep (None = all)

        Returns:
            List of detections: [(class_name, confidence, x1, y1, x2, y2), ...]
        """
        original_w, original_h, pad_x, pad_y, scale = image_info

        # YOLOv8 output shape: [1, 84, 8400] -> transpose to [1, 8400, 84]
        predictions = outputs[0]
        if predictions.shape[1] == 84:
            predictions = np.transpose(predictions, (0, 2, 1))

        predictions = predictions[0]  # Remove batch dimension: [8400, 84]

        # Split into boxes and class scores
        # First 4 values are box coordinates (x_center, y_center, width, height)
        # Remaining 80 values are class probabilities
        boxes = predictions[:, :4]
        scores = predictions[:, 4:]

        # Get best class for each detection
        class_ids = np.argmax(scores, axis=1)
        confidences = np.max(scores, axis=1)

        # Filter by confidence
        mask = confidences > self.conf_threshold
        boxes = boxes[mask]
        class_ids = class_ids[mask]
        confidences = confidences[mask]

        if len(boxes) == 0:
            return []

        # Convert from center format to corner format
        x_center, y_center, w, h = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
        x1 = x_center - w / 2
        y1 = y_center - h / 2
        x2 = x_center + w / 2
        y2 = y_center + h / 2

        # Scale back to original image coordinates
        x1 = (x1 - pad_x) / scale
        y1 = (y1 - pad_y) / scale
        x2 = (x2 - pad_x) / scale
        y2 = (y2 - pad_y) / scale

        # Clip to image bounds
        x1 = np.clip(x1, 0, original_w)
        y1 = np.clip(y1, 0, original_h)
        x2 = np.clip(x2, 0, original_w)
        y2 = np.clip(y2, 0, original_h)

        # Apply NMS
        boxes_for_nms = np.stack([x1, y1, x2, y2], axis=1)
        indices = self._nms(boxes_for_nms, confidences, self.iou_threshold)

        # Build results
        detections = []
        for i in indices:
            class_name = COCO_CLASSES[class_ids[i]]

            # Filter by class if specified
            if filter_classes and class_name not in filter_classes:
                continue

            detections.append((
                class_name,
                float(confidences[i]),
                int(x1[i]), int(y1[i]),
                int(x2[i]), int(y2[i])
            ))

        return detections

    def _nms(self, boxes, scores, iou_threshold):
        """Non-maximum suppression"""
        x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
        areas = (x2 - x1) * (y2 - y1)

        order = scores.argsort()[::-1]
        keep = []

        while order.size > 0:
            i = order[0]
            keep.append(i)

            if order.size == 1:
                break

            # Compute IoU with remaining boxes
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0, xx2 - xx1)
            h = np.maximum(0, yy2 - yy1)
            intersection = w * h

            iou = intersection / (areas[i] + areas[order[1:]] - intersection)

            # Keep boxes with IoU below threshold
            mask = iou <= iou_threshold
            order = order[1:][mask]

        return keep

    def detect(self, image, filter_classes=None):
        """
        Run detection on an image

        Args:
            image: BGR image (numpy array) or path to image
            filter_classes: Set of class names to keep (default: TRAFFIC_CLASSES)

        Returns:
            List of detections: [(class_name, confidence, x1, y1, x2, y2), ...]
        """
        if self.session is None:
            self.load()

        # Load image if path provided
        if isinstance(image, (str, Path)):
            image = cv2.imread(str(image))
            if image is None:
                return []

        if filter_classes is None:
            filter_classes = TRAFFIC_CLASSES

        # Preprocess
        blob, image_info = self.preprocess(image)

        # Run inference
        outputs = self.session.run(None, {self.input_name: blob})

        # Postprocess
        detections = self.postprocess(outputs, image_info, filter_classes)

        return detections

    def detect_and_draw(self, image, filter_classes=None):
        """
        Run detection and draw bounding boxes on image

        Returns:
            (annotated_image, detections)
        """
        detections = self.detect(image, filter_classes)

        # Draw boxes
        for class_name, conf, x1, y1, x2, y2 in detections:
            # Color based on class
            color = {
                'car': (0, 255, 0),      # Green
                'person': (255, 0, 0),   # Blue
                'bicycle': (0, 255, 255), # Yellow
                'motorcycle': (255, 0, 255), # Magenta
                'truck': (0, 128, 0),    # Dark green
                'bus': (0, 128, 0),      # Dark green
                'dog': (255, 128, 0),    # Orange
                'cat': (128, 0, 255),    # Purple
            }.get(class_name, (128, 128, 128))

            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

            label = f"{class_name}: {conf:.2f}"
            (label_w, label_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(image, (x1, y1 - label_h - 10), (x1 + label_w, y1), color, -1)
            cv2.putText(image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return image, detections


def test_detector():
    """Test the detector on sample images"""
    import glob

    detector = YOLOv8Detector()

    try:
        detector.load()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nTo download the model, run:")
        print("  python3 -c \"from ultralytics import YOLO; YOLO('yolov8n.pt').export(format='onnx')\"")
        print("  mv yolov8n.onnx models/")
        return

    # Find test images
    data_dir = Path(__file__).parent / "data"
    images = list(data_dir.glob("*.jpg"))[:5]

    if not images:
        print("No test images found in data/")
        return

    for img_path in images:
        print(f"\nTesting: {img_path.name}")
        image = cv2.imread(str(img_path))

        import time
        start = time.time()
        detections = detector.detect(image)
        elapsed = time.time() - start

        print(f"  Inference time: {elapsed*1000:.1f}ms")
        print(f"  Detections: {len(detections)}")
        for det in detections:
            print(f"    - {det[0]}: {det[1]:.2f}")


if __name__ == "__main__":
    test_detector()
