#!/bin/bash
#
# Start Neighborhood Watch with Permanent Cloudflare Tunnel
#

cd /data/data/com.termux/files/home/traffic_observer

DOMAIN="home.ethicline.eu"
TUNNEL_NAME="watch"

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

echo "══════════════════════════════════════════════════════════════"
echo ""
echo "  🌐 YOUR PERMANENT URL:"
echo ""
echo "     https://$DOMAIN"
echo ""
echo "  Auth token: neighborhood2024"
echo ""
echo "══════════════════════════════════════════════════════════════"
echo ""
echo "Starting Cloudflare tunnel..."
echo ""

# Run the named tunnel
cloudflared tunnel run $TUNNEL_NAME

# Cleanup when tunnel stops
kill $WEB_PID 2>/dev/null
echo ""
echo "Server stopped."
