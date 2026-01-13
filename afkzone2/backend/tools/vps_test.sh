#!/bin/bash
set -e
BASE_URL=http://127.0.0.1:21121

echo "=== 1. Register ==="
curl -s -X POST $BASE_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"vpstest2026","password":"testpass123"}' || echo "(may exist)"

echo ""
echo "=== 2. Login ==="
LOGIN=$(curl -s -X POST $BASE_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"vpstest2026","password":"testpass123"}')
echo "$LOGIN"
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "TOKEN: ${TOKEN:0:30}..."

echo ""
echo "=== 3. Register Device ==="
curl -s -X POST $BASE_URL/devices/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"device_id":"test-dev1","device_name":"Test Device 1"}'

echo ""
echo "=== 4. Create Share Token ==="
SHARE=$(curl -s -X POST $BASE_URL/share/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"device_id":"test-dev1","expires_hours":1}')
echo "$SHARE"
SHARE_TOKEN=$(echo "$SHARE" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
echo "SHARE_TOKEN: $SHARE_TOKEN"

echo ""
echo "=== 5. Remote Request ==="
REMOTE=$(curl -s -X POST $BASE_URL/remote/request \
  -H "Content-Type: application/json" \
  -d "{\"share_token\":\"$SHARE_TOKEN\"}")
echo "$REMOTE"
REQUEST_ID=$(echo "$REMOTE" | python3 -c "import sys,json; print(json.load(sys.stdin)['request_id'])")
echo "REQUEST_ID: $REQUEST_ID"

echo ""
echo "=== 6. Approve ==="
APPROVE=$(curl -s -X POST $BASE_URL/remote/approve \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"request_id\":\"$REQUEST_ID\"}")
echo "$APPROVE"

echo ""
echo "=========================================="
echo "=== ROUTING LOGS ==="
echo "=========================================="
journalctl -u afkzone2-api -n 50 --no-pager | grep -E "APPROVE_ROUTING|ENABLE_SCREEN_CAPTURE|HOST_READY"
