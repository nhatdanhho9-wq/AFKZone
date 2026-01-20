#!/bin/bash
BASE=http://127.0.0.1:21121

echo "=== 1. Register demo user ==="
curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@afkzone.io","password":"demo2026","username":"commander_demo"}' | python3 -m json.tool

echo ""
echo "=== 2. Register admin user ==="
curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@afkzone.io","password":"admin2026","username":"commander_admin"}' | python3 -m json.tool

echo ""
echo "=== 3. Seed demo data ==="
curl -s -X POST $BASE/admin/seed | python3 -m json.tool

echo ""
echo "=== 4. Login demo ==="
LOGIN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@afkzone.io","password":"demo2026"}')
echo "$LOGIN" | python3 -m json.tool
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

echo ""
echo "=== 5. Get devices ==="
curl -s $BASE/devices -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "=== 6. Test heartbeat (online) ==="
curl -s -X POST $BASE/devices/dev_cloud01/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"status":"online"}' | python3 -m json.tool

echo ""
echo "=== 7. Test remote-access toggle ==="
curl -s -X PATCH $BASE/devices/dev_cloud01/remote-access \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled":true}' | python3 -m json.tool

echo ""
echo "=== 8. Logs ==="
tail -15 /var/log/backend-v2.log
