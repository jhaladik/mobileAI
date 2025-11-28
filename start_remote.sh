#!/bin/bash
#
# Start Neighborhood Watch with Remote Access
#

cd /data/data/com.termux/files/home/traffic_observer

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        🌐 Neighborhood Watch - Remote Access                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Start web server in background
echo "Starting web server..."
python3 web_server.py > .web_server.log 2>&1 &
WEB_PID=$!
sleep 2

# Check if server started
if ! kill -0 $WEB_PID 2>/dev/null; then
    echo "❌ Web server failed to start"
    exit 1
fi
echo "✅ Web server running on port 8080"
echo ""

# Start Cloudflare tunnel and capture URL
echo "Starting Cloudflare tunnel..."
echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  Waiting for public URL..."
echo "  (Copy this URL to access from anywhere)"
echo "══════════════════════════════════════════════════════════════"
echo ""
echo "  Auth token: neighborhood2024"
echo ""

# Run tunnel and highlight the URL
cloudflared tunnel --url http://localhost:8080 2>&1 | while read line; do
    if echo "$line" | grep -q "trycloudflare.com"; then
        echo ""
        echo "══════════════════════════════════════════════════════════════"
        echo "  🌐 YOUR URL:"
        echo "$line" | grep -oE 'https://[^ ]+'
        echo "══════════════════════════════════════════════════════════════"
        echo ""
    fi
    echo "$line"
done

# Cleanup when tunnel stops
kill $WEB_PID 2>/dev/null
echo ""
echo "Server stopped."
