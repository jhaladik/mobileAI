# Mobile AI Project Memory

## Current Setup
- Phone: Nothing Phone, Android 14, Termux
- Camera: Back (street view) + Front (room)
- ML: YOLOv8n via ONNX Runtime (~275ms inference)
- Remote access: Cloudflare tunnel → home.ethicline.eu
- Web dashboard on port 8080

## Future Ideas

### Weather Detection
- Analyze sky portion of image (top 1/3)
- Simple metrics: brightness, blue ratio, contrast
- Detect: sunny, cloudy, overcast, foggy, rainy, night
- Compare with external API (wttr.in)
- Display on dashboard

### Video Processing Improvements
- Try NanoDet for faster inference (10-15 FPS possible)
- Lower resolution option (320x320) for speed
- Frame skipping for motion detection

### Other Possibilities
- Sound monitoring (termux-microphone-record)
- Power outage detection (battery status monitoring)
- Intercom feature (two-way audio)
- Time-lapse generation from captures
- Traffic pattern analysis (peak hours, trends)

## Technical Notes
- Images captured in portrait, need rotation
- NNAPI has compatibility issues with YOLOv8, use XNNPACK
- termux-camera-photo captures at 4096x3072 (12MP)
- MobileNet SSD works but YOLOv8 is more accurate

## Repository
https://github.com/jhaladik/mobileAI
