#!/bin/bash
# OpusB Health Check Script
# Generated: 2026-01-13
# Run: bash opusb_health_check.sh

set -e

echo "========================================"
echo "OpusB Health Check - AFKZone Remote"
echo "========================================"
echo "Timestamp: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo ""

# --- Backend Service ---
echo "--- Backend Service (afkzone2-api) ---"
if systemctl is-active --quiet afkzone2-api 2>/dev/null; then
    echo "Status: RUNNING ✓"
else
    echo "Status: NOT RUNNING ✗"
fi
BACKEND_PID=$(pgrep -f uvicorn 2>/dev/null || echo "N/A")
echo "PID: $BACKEND_PID"
echo ""

# --- Health Endpoint ---
echo "--- Health Endpoint ---"
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:21121/health 2>/dev/null || echo "000")
if [ "$HEALTH" = "200" ]; then
    echo "GET /health: 200 OK ✓"
    curl -s http://127.0.0.1:21121/health 2>/dev/null
    echo ""
else
    echo "GET /health: $HEALTH ✗"
fi
echo ""

# --- TURN Service ---
echo "--- TURN Service (coturn) ---"
if systemctl is-active --quiet coturn 2>/dev/null; then
    echo "Status: RUNNING ✓"
else
    echo "Status: NOT RUNNING ✗"
fi
TURN_PID=$(pgrep turnserver 2>/dev/null || echo "N/A")
echo "PID: $TURN_PID"
echo ""

# --- Port Status ---
echo "--- Port Status ---"
echo "Backend 21121 TCP:"
ss -tlnp 2>/dev/null | grep 21121 | head -1 || echo "  (not found)"
echo "TURN 3478 UDP:"
ss -ulnp 2>/dev/null | grep 3478 | head -1 || echo "  (not found)"
echo "TURN 3478 TCP:"
ss -tlnp 2>/dev/null | grep 3478 | head -1 || echo "  (not found)"
echo ""

# --- ENV Variables ---
echo "--- TURN Environment Variables ---"
ENV_FILE="/home/automation/afkzone2/backend/.env"
if [ -f "$ENV_FILE" ]; then
    grep -E "AFK_TURN" "$ENV_FILE" 2>/dev/null | sed 's/=.*/=***/' || echo "  (no TURN vars found)"
else
    echo "  (.env file not found at $ENV_FILE)"
fi
echo ""

# --- TURN Config Match ---
echo "--- TURN Config Verification ---"
if [ -f "/etc/turnserver.conf" ]; then
    echo "static-auth-secret: $(grep static-auth-secret /etc/turnserver.conf 2>/dev/null | cut -d'=' -f2 | cut -c1-10)... (truncated)"
    echo "realm: $(grep '^realm' /etc/turnserver.conf 2>/dev/null | cut -d'=' -f2 || echo 'not set')"
else
    echo "  (/etc/turnserver.conf not found)"
fi
echo ""

# --- Firewall Status ---
echo "--- Firewall (UFW) ---"
if command -v ufw &>/dev/null; then
    ufw status 2>/dev/null | grep -E "Status|3478|21121" || echo "  (ufw not active or ports not listed)"
else
    echo "  (ufw not installed)"
fi
echo ""

# --- Recent Routing Logs ---
echo "--- Recent Routing Logs (last 5) ---"
journalctl -u afkzone2-api -n 20 --no-pager 2>/dev/null | grep -E "ROUTING|SCREEN_CAPTURE|HOST_READY" | tail -5 || echo "  (no recent routing logs)"
echo ""

# --- Summary ---
echo "========================================"
echo "SUMMARY"
echo "========================================"
echo "Backend PID:  $BACKEND_PID"
echo "TURN PID:     $TURN_PID"
echo "Health HTTP:  $HEALTH"
echo "Check Time:   $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "========================================"
