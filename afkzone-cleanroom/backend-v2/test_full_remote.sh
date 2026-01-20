#!/bin/bash
# Test full remote flow with host daemon
BASE=http://127.0.0.1:21121

echo "=== 1. Login as demo ==="
LOGIN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@afkzone.io","password":"demo2026"}')
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
echo "Token obtained"

echo ""
echo "=== 2. Request remote session for dev_cloud01 ==="
SESSION=$(curl -s -X POST $BASE/remote/request \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"dev_cloud01"}')
echo "$SESSION" | python3 -m json.tool
SESSION_ID=$(echo "$SESSION" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session',{}).get('id',''))" 2>/dev/null)
echo "Session ID: $SESSION_ID"

echo ""
echo "=== 3. Wait 3 seconds for host daemon to connect ==="
sleep 3

echo ""
echo "=== 4. Host daemon logs ==="
tail -30 /var/log/host_daemon.log

echo ""
echo "=== 5. Backend WS logs ==="
tail -20 /var/log/backend-v2.log | grep -E "(WS_|SDP|ICE|SESSION)"

echo ""
echo "=== 6. Session status ==="
curl -s $BASE/sessions/$SESSION_ID/status | python3 -m json.tool
