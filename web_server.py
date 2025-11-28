#!/usr/bin/env python3
"""
Neighborhood Watch - Web Interface
Access your street observer from anywhere
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import subprocess
import urllib.parse
from pathlib import Path
from datetime import datetime
import re
from collections import defaultdict

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOG_FILE = BASE_DIR / "street_log.txt"

# Simple auth (change this!)
AUTH_TOKEN = "neighborhood2024"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neighborhood Watch</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }

        header {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #16213e, #1a1a2e);
            border-radius: 15px;
            margin-bottom: 20px;
            border: 1px solid #0f3460;
        }
        header h1 { font-size: 1.8em; margin-bottom: 5px; }
        header p { color: #888; }

        .status-bar {
            display: flex;
            justify-content: space-around;
            background: #16213e;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .status-item { text-align: center; }
        .status-value { font-size: 1.5em; font-weight: bold; }
        .status-label { color: #888; font-size: 0.85em; }

        .running { color: #4ade80; }
        .stopped { color: #f87171; }

        .controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }

        button {
            padding: 15px 10px;
            border: none;
            border-radius: 10px;
            font-size: 0.95em;
            cursor: pointer;
            transition: transform 0.1s, opacity 0.1s;
        }
        button:hover { transform: scale(1.02); }
        button:active { transform: scale(0.98); }

        .btn-start { background: #4ade80; color: #000; }
        .btn-stop { background: #f87171; color: #000; }
        .btn-snapshot { background: #60a5fa; color: #000; }
        .btn-front { background: #f472b6; color: #000; }
        .btn-refresh { background: #a78bfa; color: #000; }

        .card {
            background: #16213e;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #0f3460;
        }
        .card h2 {
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #0f3460;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .card h2 .subtitle { font-size: 0.6em; color: #888; font-weight: normal; }

        .live-view {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .camera-feed {
            background: #1a1a2e;
            border-radius: 10px;
            padding: 10px;
            text-align: center;
        }
        .camera-feed h3 {
            margin-bottom: 10px;
            color: #888;
            font-size: 0.9em;
        }
        .camera-feed img {
            max-width: 100%;
            max-height: 300px;
            border-radius: 8px;
            cursor: pointer;
            object-fit: contain;
        }
        .camera-feed img.portrait {
            max-height: 350px;
            width: auto;
        }
        .camera-feed img.landscape {
            width: 100%;
            height: auto;
        }
        .camera-feed .no-image {
            padding: 60px 20px;
            color: #555;
        }
        .camera-feed .timestamp {
            margin-top: 8px;
            font-size: 0.75em;
            color: #666;
        }

        .events-list {
            max-height: 250px;
            overflow-y: auto;
        }
        .event-item {
            padding: 10px;
            border-bottom: 1px solid #0f3460;
            display: flex;
            justify-content: space-between;
        }
        .event-item:last-child { border-bottom: none; }
        .event-time { color: #888; }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
            gap: 10px;
        }
        .stat-box {
            background: #1a1a2e;
            padding: 12px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-icon { font-size: 1.5em; margin-bottom: 5px; }
        .stat-value { font-size: 1.3em; font-weight: bold; }
        .stat-label { color: #888; font-size: 0.75em; }

        .image-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
        }
        .image-thumb {
            width: 100%;
            border-radius: 10px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .image-thumb:hover { transform: scale(1.05); }

        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.9);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .modal img {
            max-width: 95%;
            max-height: 95%;
            border-radius: 10px;
        }
        .modal.active { display: flex; }

        .loading { opacity: 0.5; pointer-events: none; }

        @media (max-width: 600px) {
            body { padding: 10px; }
            header h1 { font-size: 1.4em; }
            .status-bar { flex-wrap: wrap; gap: 10px; }
            .live-view { grid-template-columns: 1fr; }
            .controls { grid-template-columns: repeat(3, 1fr); }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏠 Neighborhood Watch</h1>
            <p>Your Personal Home Intelligence</p>
        </header>

        <div class="status-bar">
            <div class="status-item">
                <div class="status-value" id="observer-status">--</div>
                <div class="status-label">Observer</div>
            </div>
            <div class="status-item">
                <div class="status-value" id="battery-level">--</div>
                <div class="status-label">Battery</div>
            </div>
            <div class="status-item">
                <div class="status-value" id="events-today">--</div>
                <div class="status-label">Today</div>
            </div>
        </div>

        <div class="controls">
            <button class="btn-start" onclick="controlObserver('start')">▶ Start</button>
            <button class="btn-stop" onclick="controlObserver('stop')">⏹ Stop</button>
            <button class="btn-snapshot" onclick="takeSnapshot('back')">📷 Street</button>
            <button class="btn-front" onclick="takeSnapshot('front')">🤳 Room</button>
            <button class="btn-refresh" onclick="refreshData()">🔄 Refresh</button>
        </div>

        <div class="card">
            <h2>📹 Live View <span class="subtitle">Click to enlarge</span></h2>
            <div class="live-view">
                <div class="camera-feed">
                    <h3>🚗 Street (Back Camera)</h3>
                    <div id="back-camera">
                        <div class="no-image">No snapshot yet<br>Click "📷 Street" to capture</div>
                    </div>
                    <div class="timestamp" id="back-timestamp"></div>
                </div>
                <div class="camera-feed">
                    <h3>🏠 Room (Front Camera)</h3>
                    <div id="front-camera">
                        <div class="no-image">No snapshot yet<br>Click "🤳 Room" to capture</div>
                    </div>
                    <div class="timestamp" id="front-timestamp"></div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>📊 Today's Statistics</h2>
            <div class="stats-grid" id="stats-grid">
                <div class="stat-box">
                    <div class="stat-icon">🚗</div>
                    <div class="stat-value" id="stat-car">0</div>
                    <div class="stat-label">Cars</div>
                </div>
                <div class="stat-box">
                    <div class="stat-icon">👤</div>
                    <div class="stat-value" id="stat-person">0</div>
                    <div class="stat-label">People</div>
                </div>
                <div class="stat-box">
                    <div class="stat-icon">🚲</div>
                    <div class="stat-value" id="stat-bicycle">0</div>
                    <div class="stat-label">Bikes</div>
                </div>
                <div class="stat-box">
                    <div class="stat-icon">🏍️</div>
                    <div class="stat-value" id="stat-motorcycle">0</div>
                    <div class="stat-label">Motos</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>🕐 Recent Events</h2>
            <div class="events-list" id="events-list">
                <p style="color: #888; text-align: center;">Loading...</p>
            </div>
        </div>

        <div class="card">
            <h2>📷 Recent Captures</h2>
            <div class="image-grid" id="image-grid">
                <p style="color: #888; text-align: center;">Loading...</p>
            </div>
        </div>
    </div>

    <div class="modal" id="modal" onclick="closeModal()">
        <img id="modal-img" src="">
    </div>

    <script>
        const API_TOKEN = localStorage.getItem('auth_token') || prompt('Enter access token:');
        localStorage.setItem('auth_token', API_TOKEN);

        async function api(endpoint, method = 'GET') {
            try {
                const res = await fetch('/api/' + endpoint, {
                    method,
                    headers: { 'Authorization': API_TOKEN }
                });
                return await res.json();
            } catch (e) {
                console.error('API Error:', e);
                return { error: e.message };
            }
        }

        async function refreshData() {
            document.body.classList.add('loading');

            const status = await api('status');
            if (!status.error) {
                document.getElementById('observer-status').textContent =
                    status.running ? '🟢 ON' : '🔴 OFF';
                document.getElementById('observer-status').className =
                    'status-value ' + (status.running ? 'running' : 'stopped');
                document.getElementById('battery-level').textContent =
                    status.battery + '%';
                document.getElementById('events-today').textContent =
                    status.events_today;
            }

            const stats = await api('stats');
            if (!stats.error) {
                document.getElementById('stat-car').textContent = stats.car || 0;
                document.getElementById('stat-person').textContent = stats.person || 0;
                document.getElementById('stat-bicycle').textContent = stats.bicycle || 0;
                document.getElementById('stat-motorcycle').textContent = stats.motorcycle || 0;
            }

            const events = await api('events');
            if (!events.error && events.events) {
                const list = document.getElementById('events-list');
                if (events.events.length === 0) {
                    list.innerHTML = '<p style="color: #888; text-align: center;">No events yet</p>';
                } else {
                    list.innerHTML = events.events.slice(-15).reverse().map(e =>
                        '<div class="event-item"><span>' + e.detection + '</span><span class="event-time">' + e.time + '</span></div>'
                    ).join('');
                }
            }

            const images = await api('images');
            if (!images.error && images.images) {
                const grid = document.getElementById('image-grid');
                if (images.images.length === 0) {
                    grid.innerHTML = '<p style="color: #888; text-align: center;">No images yet</p>';
                } else {
                    grid.innerHTML = images.images.slice(-8).reverse().map(function(img) {
                        return '<img class="image-thumb" src="/image/' + img.filename + '" onclick="openModal(this.src)" title="' + img.filename + '">';
                    }).join('');
                }
            }

            // Load live view snapshots
            await loadLiveView();

            document.body.classList.remove('loading');
        }

        function setImageOrientation(img) {
            img.onload = function() {
                if (this.naturalHeight > this.naturalWidth) {
                    this.classList.add('portrait');
                } else {
                    this.classList.add('landscape');
                }
            };
        }

        async function loadLiveView() {
            const liveData = await api('live');
            if (!liveData.error) {
                if (liveData.back) {
                    var backSrc = '/image/' + liveData.back.filename + '?t=' + Date.now();
                    var backImg = document.createElement('img');
                    backImg.src = backSrc;
                    backImg.onclick = function() { openModal(this.src); };
                    setImageOrientation(backImg);
                    document.getElementById('back-camera').innerHTML = '';
                    document.getElementById('back-camera').appendChild(backImg);
                    document.getElementById('back-timestamp').textContent = liveData.back.time || '';
                }
                if (liveData.front) {
                    var frontSrc = '/image/' + liveData.front.filename + '?t=' + Date.now();
                    var frontImg = document.createElement('img');
                    frontImg.src = frontSrc;
                    frontImg.onclick = function() { openModal(this.src); };
                    setImageOrientation(frontImg);
                    document.getElementById('front-camera').innerHTML = '';
                    document.getElementById('front-camera').appendChild(frontImg);
                    document.getElementById('front-timestamp').textContent = liveData.front.time || '';
                }
            }
        }

        async function controlObserver(action) {
            document.body.classList.add('loading');
            await api(action, 'POST');
            setTimeout(refreshData, 2000);
        }

        async function takeSnapshot(camera) {
            document.body.classList.add('loading');
            const result = await api('snapshot/' + camera, 'POST');
            if (result.error) {
                alert('Error: ' + result.error);
            }
            setTimeout(refreshData, 1500);
        }

        function openModal(src) {
            document.getElementById('modal-img').src = src;
            document.getElementById('modal').classList.add('active');
        }

        function closeModal() {
            document.getElementById('modal').classList.remove('active');
        }

        // Initial load and auto-refresh
        refreshData();
        setInterval(refreshData, 30000);
    </script>
</body>
</html>
"""


class WatchHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")

    def check_auth(self):
        token = self.headers.get('Authorization', '')
        return token == AUTH_TOKEN

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_html(self, html):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def get_battery(self):
        try:
            result = subprocess.run(['termux-battery-status'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get('percentage', 0)
        except:
            pass
        return 0

    def is_observer_running(self):
        try:
            result = subprocess.run(['pgrep', '-f', 'smart_observer.py'],
                                  capture_output=True)
            return result.returncode == 0
        except:
            return False

    def get_events_today(self):
        today = datetime.now().strftime('%Y-%m-%d')
        events = []
        if LOG_FILE.exists():
            with open(LOG_FILE) as f:
                for line in f:
                    if today in line and 'DETECTED' in line:
                        match = re.search(r'\[[\d-]+ ([\d:]+)\] DETECTED: (.+)', line)
                        if match:
                            events.append({
                                'time': match.group(1),
                                'detection': match.group(2)
                            })
        return events

    def get_stats_today(self):
        today = datetime.now().strftime('%Y-%m-%d')
        stats = defaultdict(int)
        if LOG_FILE.exists():
            with open(LOG_FILE) as f:
                for line in f:
                    if today in line and 'DETECTED' in line:
                        match = re.search(r'DETECTED: (.+)', line)
                        if match:
                            for item in match.group(1).split(', '):
                                parts = item.strip().split(' ')
                                if len(parts) == 2:
                                    count, obj_type = int(parts[0]), parts[1]
                                    stats[obj_type] += count
        return dict(stats)

    def get_images(self):
        images = []
        # Get event images and snapshots
        for pattern in ['event_*.jpg', 'snapshot_*.jpg', 'live_*.jpg']:
            for f in sorted(DATA_DIR.glob(pattern)):
                images.append({
                    'filename': f.name,
                    'size': f.stat().st_size,
                    'time': datetime.fromtimestamp(f.stat().st_mtime).strftime('%H:%M:%S')
                })
        # Sort by modification time
        images.sort(key=lambda x: x['filename'], reverse=True)
        return images[:20]

    def get_live_images(self):
        """Get the latest live snapshots for each camera"""
        result = {'back': None, 'front': None}

        # Find latest back camera image
        back_files = sorted(DATA_DIR.glob('live_back_*.jpg'))
        if back_files:
            f = back_files[-1]
            result['back'] = {
                'filename': f.name,
                'time': datetime.fromtimestamp(f.stat().st_mtime).strftime('%H:%M:%S')
            }

        # Find latest front camera image
        front_files = sorted(DATA_DIR.glob('live_front_*.jpg'))
        if front_files:
            f = front_files[-1]
            result['front'] = {
                'filename': f.name,
                'time': datetime.fromtimestamp(f.stat().st_mtime).strftime('%H:%M:%S')
            }

        return result

    def take_snapshot(self, camera='back'):
        """Take a snapshot with specified camera"""
        camera_id = '1' if camera == 'front' else '0'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"live_{camera}_{timestamp}.jpg"
        filepath = DATA_DIR / filename

        try:
            result = subprocess.run(
                ['termux-camera-photo', '-c', camera_id, str(filepath)],
                capture_output=True, timeout=15
            )
            if result.returncode == 0 and filepath.exists():
                # Clean up old live images (keep last 5 per camera)
                old_files = sorted(DATA_DIR.glob(f'live_{camera}_*.jpg'))[:-5]
                for f in old_files:
                    f.unlink()
                return {'success': True, 'filename': filename}
            else:
                return {'success': False, 'error': 'Capture failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        # Main page - no auth required for page, auth for API
        if path == '/' or path == '/index.html':
            self.send_html(HTML_TEMPLATE)
            return

        # API endpoints - auth required
        if path.startswith('/api/'):
            if not self.check_auth():
                self.send_json({'error': 'Unauthorized'}, 401)
                return

            endpoint = path[5:]  # Remove '/api/'

            if endpoint == 'status':
                self.send_json({
                    'running': self.is_observer_running(),
                    'battery': self.get_battery(),
                    'events_today': len(self.get_events_today())
                })
            elif endpoint == 'stats':
                self.send_json(self.get_stats_today())
            elif endpoint == 'events':
                self.send_json({'events': self.get_events_today()})
            elif endpoint == 'images':
                self.send_json({'images': self.get_images()})
            elif endpoint == 'live':
                self.send_json(self.get_live_images())
            else:
                self.send_json({'error': 'Not found'}, 404)
            return

        # Serve images
        if path.startswith('/image/'):
            filename = path[7:].split('?')[0]  # Remove query params
            filepath = DATA_DIR / filename
            if filepath.exists() and filepath.suffix == '.jpg':
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
                return

        self.send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path

        if not path.startswith('/api/'):
            self.send_json({'error': 'Not found'}, 404)
            return

        if not self.check_auth():
            self.send_json({'error': 'Unauthorized'}, 401)
            return

        endpoint = path[5:]

        if endpoint == 'start':
            if not self.is_observer_running():
                subprocess.Popen(
                    ['python3', str(BASE_DIR / 'smart_observer.py')],
                    stdout=open(BASE_DIR / '.observer.log', 'w'),
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
                self.send_json({'message': 'Observer started'})
            else:
                self.send_json({'message': 'Already running'})

        elif endpoint == 'stop':
            subprocess.run(['pkill', '-f', 'smart_observer.py'])
            self.send_json({'message': 'Observer stopped'})

        elif endpoint == 'snapshot/back':
            result = self.take_snapshot('back')
            if result['success']:
                self.send_json({'message': 'Street snapshot saved', 'file': result['filename']})
            else:
                self.send_json({'error': result['error']}, 500)

        elif endpoint == 'snapshot/front':
            result = self.take_snapshot('front')
            if result['success']:
                self.send_json({'message': 'Room snapshot saved', 'file': result['filename']})
            else:
                self.send_json({'error': result['error']}, 500)

        # Legacy single snapshot endpoint
        elif endpoint == 'snapshot':
            result = self.take_snapshot('back')
            if result['success']:
                self.send_json({'message': 'Snapshot saved', 'file': result['filename']})
            else:
                self.send_json({'error': result['error']}, 500)

        else:
            self.send_json({'error': 'Not found'}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Authorization')
        self.end_headers()


def main():
    port = 8080

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           🏠 Neighborhood Watch - Web Server                 ║
╚══════════════════════════════════════════════════════════════╝

  Local URL:    http://localhost:{port}

  To access from other devices on same WiFi:
    1. Find your IP: termux-wifi-connectioninfo
    2. Open: http://YOUR_IP:{port}

  Auth Token: {AUTH_TOKEN}
  (Change AUTH_TOKEN in web_server.py for security)

  Press Ctrl+C to stop
""")

    server = HTTPServer(('0.0.0.0', port), WatchHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        server.shutdown()


if __name__ == '__main__':
    main()
