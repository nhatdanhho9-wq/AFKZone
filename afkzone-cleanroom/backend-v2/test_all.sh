#!/bin/bash
BASE=http://127.0.0.1:21121

echo "=== LOGIN ==="
LOGIN=$(curl -s -X POST $BASE/auth/login -H "Content-Type: application/json" -d '{"email":"demo@afkzone.io","password":"demo2026"}')
echo "$LOGIN" | python3 -m json.tool
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

echo ""
echo "=== GET /user/profile ==="
curl -s $BASE/user/profile -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "=== GET /devices ==="
curl -s $BASE/devices -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "=== GET /user/notifications ==="
curl -s $BASE/user/notifications -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "=== GET /plans ==="
curl -s $BASE/plans | python3 -m json.tool
