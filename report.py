#!/usr/bin/env python3
"""
Neighborhood Report Generator
Analyzes events and generates daily/hourly reports
"""

import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "street_log.txt"
DATA_DIR = BASE_DIR / "data"


def parse_log():
    """Parse street_log.txt into structured events"""
    events = []

    if not LOG_FILE.exists():
        return events

    with open(LOG_FILE, 'r') as f:
        for line in f:
            # Parse: [2025-11-28 16:48:55] DETECTED: 1 car
            match = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] DETECTED: (.+)', line)
            if match:
                timestamp = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                detection_str = match.group(2)

                # Parse "1 car" or "2 person, 1 car"
                detections = {}
                for item in detection_str.split(', '):
                    parts = item.strip().split(' ')
                    if len(parts) == 2:
                        count, obj_type = int(parts[0]), parts[1]
                        detections[obj_type] = count

                events.append({
                    'timestamp': timestamp,
                    'detections': detections
                })

    return events


def get_event_images():
    """Get list of saved event images with timestamps"""
    images = []

    for f in DATA_DIR.glob('event_*.jpg'):
        # Parse: event_20251128_164855.jpg
        match = re.match(r'event_(\d{8})_(\d{6})\.jpg', f.name)
        if match:
            date_str = match.group(1)
            time_str = match.group(2)
            timestamp = datetime.strptime(f'{date_str}_{time_str}', '%Y%m%d_%H%M%S')
            images.append({
                'path': str(f),
                'filename': f.name,
                'timestamp': timestamp,
                'size': f.stat().st_size
            })

    return sorted(images, key=lambda x: x['timestamp'])


def generate_report(hours=24, date=None):
    """Generate a comprehensive report"""

    events = parse_log()
    images = get_event_images()

    # Filter by time range
    if date:
        start_time = datetime.strptime(date, '%Y-%m-%d')
        end_time = start_time + timedelta(days=1)
    else:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

    events = [e for e in events if start_time <= e['timestamp'] <= end_time]
    images = [i for i in images if start_time <= i['timestamp'] <= end_time]

    # Aggregate statistics
    totals = defaultdict(int)
    hourly = defaultdict(lambda: defaultdict(int))

    for event in events:
        hour = event['timestamp'].hour
        for obj_type, count in event['detections'].items():
            totals[obj_type] += count
            hourly[hour][obj_type] += count

    # Find peak hours
    hourly_totals = {h: sum(counts.values()) for h, counts in hourly.items()}
    peak_hours = sorted(hourly_totals.items(), key=lambda x: -x[1])[:3] if hourly_totals else []

    # Find quiet periods
    all_hours = set(range(24))
    active_hours = set(hourly.keys())
    quiet_hours = sorted(all_hours - active_hours)

    # Identify potential deliveries (person + vehicle close in time)
    deliveries = []
    for i, event in enumerate(events):
        if 'person' in event['detections']:
            # Check for vehicle within 5 minutes
            for other in events[max(0,i-5):i+5]:
                if other != event and any(v in other['detections'] for v in ['car', 'truck', 'bus']):
                    time_diff = abs((event['timestamp'] - other['timestamp']).total_seconds())
                    if time_diff < 300:  # 5 minutes
                        deliveries.append(event['timestamp'])
                        break

    # Unusual activity (late night)
    unusual = [e for e in events if e['timestamp'].hour >= 23 or e['timestamp'].hour < 5]

    # Generate report
    report = []
    report.append("=" * 60)
    report.append(f"  NEIGHBORHOOD REPORT")
    report.append(f"  {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
    report.append("=" * 60)
    report.append("")

    # Summary
    report.append("SUMMARY")
    report.append("-" * 40)
    total_events = len(events)
    report.append(f"  Total events detected: {total_events}")
    report.append(f"  Images saved: {len(images)}")
    report.append("")

    # Object counts
    if totals:
        report.append("DETECTIONS BY TYPE")
        report.append("-" * 40)

        icons = {'car': '🚗', 'person': '👤', 'bicycle': '🚲', 'motorcycle': '🏍️',
                 'bus': '🚌', 'truck': '🚚', 'dog': '🐕'}

        for obj_type, count in sorted(totals.items(), key=lambda x: -x[1]):
            icon = icons.get(obj_type, '•')
            report.append(f"  {icon} {obj_type.capitalize()}: {count}")
        report.append("")

    # Hourly breakdown
    if hourly:
        report.append("HOURLY ACTIVITY")
        report.append("-" * 40)

        for hour in sorted(hourly.keys()):
            counts = hourly[hour]
            total = sum(counts.values())
            bar = "█" * min(total, 20)
            items = ", ".join([f"{c} {t}" for t, c in counts.items()])
            report.append(f"  {hour:02d}:00  {bar} ({items})")
        report.append("")

    # Peak hours
    if peak_hours:
        report.append("PEAK ACTIVITY")
        report.append("-" * 40)
        for hour, count in peak_hours:
            report.append(f"  {hour:02d}:00 - {count} detections")
        report.append("")

    # Quiet periods
    if quiet_hours and len(quiet_hours) < 20:  # Only show if not too many
        report.append("QUIET PERIODS")
        report.append("-" * 40)
        # Group consecutive hours
        ranges = []
        start = quiet_hours[0] if quiet_hours else None
        for i, h in enumerate(quiet_hours):
            if i == len(quiet_hours) - 1 or quiet_hours[i+1] != h + 1:
                if start == h:
                    ranges.append(f"{h:02d}:00")
                else:
                    ranges.append(f"{start:02d}:00-{h:02d}:59")
                start = quiet_hours[i+1] if i < len(quiet_hours) - 1 else None
        report.append(f"  {', '.join(ranges[:5])}")
        report.append("")

    # Possible deliveries
    if deliveries:
        report.append("POSSIBLE DELIVERIES")
        report.append("-" * 40)
        for dt in deliveries[:5]:
            report.append(f"  📦 {dt.strftime('%H:%M')}")
        report.append("")

    # Unusual activity
    if unusual:
        report.append("⚠️  UNUSUAL ACTIVITY (Night)")
        report.append("-" * 40)
        for event in unusual[:5]:
            items = ", ".join([f"{c} {t}" for t, c in event['detections'].items()])
            report.append(f"  {event['timestamp'].strftime('%H:%M')} - {items}")
        report.append("")

    # Recent events
    report.append("RECENT EVENTS")
    report.append("-" * 40)
    for event in events[-10:]:
        items = ", ".join([f"{c} {t}" for t, c in event['detections'].items()])
        report.append(f"  {event['timestamp'].strftime('%H:%M:%S')} - {items}")

    if not events:
        report.append("  No events recorded in this period")

    report.append("")
    report.append("=" * 60)
    report.append(f"  Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 60)

    return "\n".join(report)


def quick_status():
    """Quick status check - what's happening now?"""
    events = parse_log()

    if not events:
        return "No events recorded yet."

    last_event = events[-1]
    time_ago = datetime.now() - last_event['timestamp']

    # Count last hour
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent = [e for e in events if e['timestamp'] > one_hour_ago]

    totals = defaultdict(int)
    for e in recent:
        for obj_type, count in e['detections'].items():
            totals[obj_type] += count

    status = []
    status.append(f"Last activity: {time_ago.seconds // 60} minutes ago")
    status.append(f"Last hour: {len(recent)} events")

    if totals:
        items = ", ".join([f"{c} {t}" for t, c in totals.items()])
        status.append(f"Detected: {items}")

    return "\n".join(status)


def main():
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == 'status':
            print(quick_status())
        elif cmd == 'today':
            print(generate_report(hours=24))
        elif cmd == 'hour':
            print(generate_report(hours=1))
        elif cmd == 'week':
            print(generate_report(hours=168))
        elif cmd.startswith('20'):  # Date like 2025-11-28
            print(generate_report(date=cmd))
        else:
            print(f"Unknown command: {cmd}")
            print("\nUsage:")
            print("  python report.py          - Full daily report")
            print("  python report.py status   - Quick status")
            print("  python report.py today    - Today's report")
            print("  python report.py hour     - Last hour")
            print("  python report.py week     - Last 7 days")
            print("  python report.py 2025-11-28 - Specific date")
    else:
        print(generate_report())


if __name__ == "__main__":
    main()
