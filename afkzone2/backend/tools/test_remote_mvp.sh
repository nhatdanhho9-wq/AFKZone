#!/bin/bash
# Remote MVP v0.1 - API Test Script
# Run backend first: uvicorn app.main:app --host 0.0.0.0 --port 8888

BASE_URL="${1:-http://127.0.0.1:8888}"

echo "========================================"
echo "Remote MVP v0.1 - API Test Script"
echo "BASE_URL: $BASE_URL"
echo "========================================"

# 1. Register account
echo ""
echo "=== 1. Register Account ==="
curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}' | python -m json.tool

# 2. Login
echo ""
echo "=== 2. Login ==="
LOGIN_RESP=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}')
echo "$LOGIN_RESP" | python -m json.tool

TOKEN=$(echo "$LOGIN_RESP" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "TOKEN: ${TOKEN:0:30}..."

# 3. Register device
echo ""
echo "=== 3. Register Device ==="
curl -s -X POST "$BASE_URL/devices/register" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"device_id":"dev-pixel7","device_name":"Pixel 7 Pro","device_type":"android"}' | python -m json.tool

# 4. List devices
echo ""
echo "=== 4. List Devices ==="
curl -s "$BASE_URL/devices" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# 5. Heartbeat
echo ""
echo "=== 5. Heartbeat ==="
curl -s -X POST "$BASE_URL/devices/dev-pixel7/heartbeat" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# 6. Create share token
echo ""
echo "=== 6. Create Share Token ==="
SHARE_RESP=$(curl -s -X POST "$BASE_URL/share/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"device_id":"dev-pixel7","expires_hours":24,"max_uses":5}')
echo "$SHARE_RESP" | python -m json.tool

SHARE_TOKEN=$(echo "$SHARE_RESP" | python -c "import sys,json; print(json.load(sys.stdin)['token'])")
echo "SHARE_TOKEN: $SHARE_TOKEN"

# 7. Resolve share token
echo ""
echo "=== 7. Resolve Share Token ==="
curl -s -X POST "$BASE_URL/share/resolve" \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"$SHARE_TOKEN\"}" | python -m json.tool

# 8. Request remote via token (anonymous)
echo ""
echo "=== 8. Request Remote (via token) ==="
REMOTE_RESP=$(curl -s -X POST "$BASE_URL/remote/request" \
  -H "Content-Type: application/json" \
  -d "{\"share_token\":\"$SHARE_TOKEN\"}")
echo "$REMOTE_RESP" | python -m json.tool

REQUEST_ID=$(echo "$REMOTE_RESP" | python -c "import sys,json; print(json.load(sys.stdin)['request_id'])")
echo "REQUEST_ID: $REQUEST_ID"

# 9. Get pending requests (owner)
echo ""
echo "=== 9. Pending Remote Requests ==="
curl -s "$BASE_URL/remote/pending" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# 10. Approve remote request
echo ""
echo "=== 10. Approve Remote Request ==="
APPROVE_RESP=$(curl -s -X POST "$BASE_URL/remote/approve" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"request_id\":\"$REQUEST_ID\"}")
echo "$APPROVE_RESP" | python -m json.tool

SESSION_ID=$(echo "$APPROVE_RESP" | python -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
echo "SESSION_ID: $SESSION_ID"

# 11. Get TURN credentials
echo ""
echo "=== 11. TURN Credentials ==="
curl -s "$BASE_URL/sessions/$SESSION_ID/turn-credentials" | python -m json.tool

# 12. List trusted entries
echo ""
echo "=== 12. Trusted Allowlist ==="
curl -s "$BASE_URL/trusted/list" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

echo ""
echo "========================================"
echo "All tests completed!"
echo "========================================"
