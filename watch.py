#!/usr/bin/env python3
"""
Neighborhood Watch - Simple Interface
Your personal street observer control panel
"""

import os
import sys
import subprocess
import signal
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
OBSERVER_SCRIPT = BASE_DIR / "smart_observer.py"
LOG_FILE = BASE_DIR / "street_log.txt"
DATA_DIR = BASE_DIR / "data"
PID_FILE = BASE_DIR / ".observer.pid"


def clear_screen():
    os.system('clear')


def print_header():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              🏠  NEIGHBORHOOD WATCH  🏠                      ║
║                                                              ║
║         Your Personal Street Intelligence System             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def get_battery():
    try:
        result = subprocess.run(['termux-battery-status'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            return data.get('percentage', '?'), data.get('status', '?')
    except:
        pass
    return '?', '?'


def is_observer_running():
    """Check if observer is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'smart_observer.py'],
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False


def count_events_today():
    """Count today's events"""
    today = datetime.now().strftime('%Y-%m-%d')
    count = 0
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            for line in f:
                if today in line and 'DETECTED' in line:
                    count += 1
    return count


def count_images():
    """Count saved event images"""
    return len(list(DATA_DIR.glob('event_*.jpg')))


def get_last_event():
    """Get last detection"""
    if not LOG_FILE.exists():
        return None

    last = None
    with open(LOG_FILE) as f:
        for line in f:
            if 'DETECTED' in line:
                last = line.strip()
    return last


def show_status():
    """Show current system status"""
    clear_screen()
    print_header()

    running = is_observer_running()
    battery, charging = get_battery()
    events_today = count_events_today()
    total_images = count_images()
    last_event = get_last_event()

    status = "🟢 RUNNING" if running else "🔴 STOPPED"

    print(f"  System Status: {status}")
    print(f"  Battery: {battery}% ({charging})")
    print()
    print(f"  📊 Today's Events: {events_today}")
    print(f"  📷 Total Images: {total_images}")
    print()

    if last_event:
        print(f"  🕐 Last Event:")
        print(f"     {last_event}")
    else:
        print("  🕐 No events recorded yet")

    print()
    print("─" * 60)
    input("\nPress Enter to continue...")


def start_observer():
    """Start the observer in background"""
    if is_observer_running():
        print("\n⚠️  Observer is already running!")
        input("Press Enter to continue...")
        return

    print("\n🚀 Starting observer...")
    subprocess.Popen(
        ['python3', str(OBSERVER_SCRIPT)],
        stdout=open(BASE_DIR / '.observer.log', 'w'),
        stderr=subprocess.STDOUT,
        start_new_session=True
    )
    print("✅ Observer started!")
    print("   Position your phone facing the street.")
    input("\nPress Enter to continue...")


def stop_observer():
    """Stop the observer"""
    if not is_observer_running():
        print("\n⚠️  Observer is not running!")
        input("Press Enter to continue...")
        return

    print("\n🛑 Stopping observer...")
    subprocess.run(['pkill', '-f', 'smart_observer.py'])
    print("✅ Observer stopped!")
    input("\nPress Enter to continue...")


def show_report():
    """Show daily report"""
    clear_screen()
    print_header()

    # Import and run report
    sys.path.insert(0, str(BASE_DIR))
    from report import generate_report
    print(generate_report())

    print()
    input("Press Enter to continue...")


def show_recent_events():
    """Show recent events from log"""
    clear_screen()
    print_header()
    print("  RECENT EVENTS")
    print("─" * 60)

    if not LOG_FILE.exists():
        print("  No events recorded yet.")
    else:
        # Get last 20 lines with DETECTED
        events = []
        with open(LOG_FILE) as f:
            for line in f:
                if 'DETECTED' in line:
                    events.append(line.strip())

        if events:
            for event in events[-20:]:
                print(f"  {event}")
        else:
            print("  No detections yet.")

    print()
    input("Press Enter to continue...")


def view_last_image():
    """View the last captured event image"""
    images = sorted(DATA_DIR.glob('event_*.jpg'))

    if not images:
        print("\n⚠️  No event images saved yet!")
        input("Press Enter to continue...")
        return

    last_image = images[-1]
    print(f"\n📷 Last image: {last_image.name}")
    print(f"   Size: {last_image.stat().st_size / 1024:.1f} KB")
    print(f"\n   Opening with termux-open...")

    try:
        subprocess.run(['termux-open', str(last_image)], timeout=5)
    except:
        print(f"   Path: {last_image}")

    input("\nPress Enter to continue...")


def take_snapshot():
    """Take a quick snapshot now"""
    print("\n📸 Taking snapshot...")

    temp_path = DATA_DIR / f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

    try:
        result = subprocess.run(
            ['termux-camera-photo', '-c', '0', str(temp_path)],
            capture_output=True, timeout=15
        )

        if result.returncode == 0 and temp_path.exists():
            print(f"✅ Saved: {temp_path.name}")
            print(f"   Size: {temp_path.stat().st_size / 1024:.1f} KB")

            # Offer to open
            response = input("\nOpen image? [y/N]: ").strip().lower()
            if response == 'y':
                subprocess.run(['termux-open', str(temp_path)], timeout=5)
        else:
            print("❌ Capture failed!")
    except Exception as e:
        print(f"❌ Error: {e}")

    input("\nPress Enter to continue...")


def cleanup_old_files():
    """Clean up old frame files (not events)"""
    clear_screen()
    print_header()
    print("  CLEANUP")
    print("─" * 60)

    # Count different file types
    frames = list(DATA_DIR.glob('frame_*.jpg'))
    events = list(DATA_DIR.glob('event_*.jpg'))
    snapshots = list(DATA_DIR.glob('snapshot_*.jpg'))

    frames_size = sum(f.stat().st_size for f in frames) / (1024*1024)
    events_size = sum(f.stat().st_size for f in events) / (1024*1024)

    print(f"  📁 Frame files (old observer): {len(frames)} ({frames_size:.1f} MB)")
    print(f"  📁 Event files (detections):   {len(events)} ({events_size:.1f} MB)")
    print(f"  📁 Snapshots:                  {len(snapshots)}")
    print()

    if frames:
        response = input("  Delete old frame files? [y/N]: ").strip().lower()
        if response == 'y':
            for f in frames:
                f.unlink()
            print(f"  ✅ Deleted {len(frames)} frame files")

    input("\nPress Enter to continue...")


def show_settings():
    """Show current settings"""
    clear_screen()
    print_header()
    print("  SETTINGS")
    print("─" * 60)
    print()
    print("  Current configuration:")
    print("  • Capture interval: 10 seconds")
    print("  • Motion threshold: 3%")
    print("  • Detection confidence: 30%")
    print("  • Camera: Back (0)")
    print()
    print("  Paths:")
    print(f"  • Base: {BASE_DIR}")
    print(f"  • Data: {DATA_DIR}")
    print(f"  • Log:  {LOG_FILE}")
    print()
    print("  (Edit smart_observer.py to change settings)")
    print()
    input("Press Enter to continue...")


def main_menu():
    """Main menu loop"""
    while True:
        clear_screen()
        print_header()

        running = is_observer_running()
        status = "🟢 Running" if running else "🔴 Stopped"
        events_today = count_events_today()

        print(f"  Status: {status}    |    Today: {events_today} events")
        print()
        print("─" * 60)
        print()
        print("  CONTROL")
        print("    1. Start observer")
        print("    2. Stop observer")
        print("    3. Take snapshot now")
        print()
        print("  VIEW")
        print("    4. System status")
        print("    5. Daily report")
        print("    6. Recent events")
        print("    7. View last image")
        print()
        print("  MANAGE")
        print("    8. Cleanup files")
        print("    9. Settings")
        print()
        print("    0. Exit")
        print()
        print("─" * 60)

        choice = input("\n  Enter choice: ").strip()

        if choice == '1':
            start_observer()
        elif choice == '2':
            stop_observer()
        elif choice == '3':
            take_snapshot()
        elif choice == '4':
            show_status()
        elif choice == '5':
            show_report()
        elif choice == '6':
            show_recent_events()
        elif choice == '7':
            view_last_image()
        elif choice == '8':
            cleanup_old_files()
        elif choice == '9':
            show_settings()
        elif choice == '0':
            clear_screen()
            print("\n  👋 Goodbye! Stay safe.\n")
            break
        elif choice == '':
            continue
        else:
            print(f"\n  Unknown option: {choice}")
            input("  Press Enter to continue...")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n  👋 Goodbye!\n")
