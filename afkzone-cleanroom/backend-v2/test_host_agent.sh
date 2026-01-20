#!/bin/bash
# Test remote access endpoint + start host agent
BASE=http://127.0.0.1:21121

echo "=== 1. Login as demo ==="
LOGIN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@afkzone.io","password":"demo2026"}')
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
echo "Token: ${TOKEN:0:30}..."

echo ""
echo "=== 2. GET /devices/dev_cloud01/remote-access ==="
curl -s $BASE/devices/dev_cloud01/remote-access \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "=== 3. Request remote session ==="
SESSION=$(curl -s -X POST $BASE/remote/request \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"dev_cloud01"}')
echo "$SESSION" | python3 -m json.tool
SESSION_ID=$(echo "$SESSION" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session',{}).get('id',''))" 2>/dev/null)
echo "Session ID: $SESSION_ID"

echo ""
echo "=== 4. Start host agent in background ==="
cd /opt/afkzone/afkzone-cleanroom/backend-v2
timeout 15 python3 host_agent.py "$SESSION_ID" "$TOKEN" &
HOST_PID=$!
echo "Host agent PID: $HOST_PID"

sleep 3

echo ""
echo "=== 5. Check backend logs ==="
tail -20 /var/log/backend-v2.log | grep -E "(WS_|SDP|HOST|SESSION)"

echo ""
echo "=== 6. Get session status ==="
curl -s $BASE/sessions/$SESSION_ID/status | python3 -m json.tool

# Kill host agent
kill $HOST_PID 2>/dev/null
