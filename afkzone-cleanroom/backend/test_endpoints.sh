#!/bin/bash
BASE=http://127.0.0.1:21121

echo "=== 1. Health Check ==="
curl -s $BASE/health | python3 -m json.tool

echo ""
echo "=== 2. Register ==="
curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"cleanroom_test3","password":"test123"}' | python3 -m json.tool

echo ""
echo "=== 3. Login ==="
LOGIN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"cleanroom_test3","password":"test123"}')
echo "$LOGIN" | python3 -m json.tool

TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('access_token',''))" 2>/dev/null)
echo "Token: ${TOKEN:0:30}..."

echo ""
echo "=== 4. Get Devices ==="
curl -s "$BASE/devices" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "=== 5. Logs ==="
tail -10 /var/log/afkzone-cleanroom.log
