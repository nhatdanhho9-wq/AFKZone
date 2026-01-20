#!/bin/bash
BASE=http://127.0.0.1:21121

echo "=== 1. Health Check ==="
curl -s $BASE/health | python3 -m json.tool

echo ""
echo "=== 2. Register ==="
curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@afkzone.io","password":"demo2026","username":"commander_demo"}' | python3 -m json.tool

echo ""
echo "=== 3. Login with EMAIL ==="
LOGIN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@afkzone.io","password":"demo2026"}')
echo "$LOGIN" | python3 -m json.tool

TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
echo "Token: ${TOKEN:0:30}..."

echo ""
echo "=== 4. Get Profile ==="
curl -s $BASE/user/profile -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "=== 5. Get Plans ==="
curl -s $BASE/plans | python3 -m json.tool

echo ""
echo "=== 6. VPS Logs ==="
tail -10 /var/log/backend-v2.log
