#!/bin/bash
BASE=http://127.0.0.1:21121

echo "=== 1. Login as DEMO ==="
DEMO_LOGIN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@afkzone.io","password":"demo2026"}')
DEMO_TOKEN=$(echo "$DEMO_LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
echo "Demo token: ${DEMO_TOKEN:0:30}..."

echo ""
echo "=== 2. Login as ADMIN ==="
ADMIN_LOGIN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@afkzone.io","password":"admin2026"}')
ADMIN_TOKEN=$(echo "$ADMIN_LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
echo "Admin token: ${ADMIN_TOKEN:0:30}..."

echo ""
echo "=== 3. Register NEW device for DEMO ==="
curl -s -X POST $BASE/devices/register \
  -H "Authorization: Bearer $DEMO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"DEMO_STATION_01","type":"pc","vcpu":4,"ram_gb":16,"description":"Demo test device"}' | python3 -m json.tool

echo ""
echo "=== 4. Register NEW device for ADMIN ==="
curl -s -X POST $BASE/devices/register \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"ADMIN_SERVER_01","type":"cloud","vcpu":8,"ram_gb":32,"description":"Admin cloud server"}' | python3 -m json.tool

echo ""
echo "=== 5. DEMO devices ==="
curl -s $BASE/devices -H "Authorization: Bearer $DEMO_TOKEN" | python3 -m json.tool

echo ""
echo "=== 6. ADMIN devices ==="
curl -s $BASE/devices -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -m json.tool

echo ""
echo "=== 7. Test heartbeat on demo device ==="
curl -s -X POST $BASE/devices/dev_cloud01/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"status":"online"}' | python3 -m json.tool

echo ""
echo "=== 8. Test remote-access toggle ==="
curl -s -X PATCH $BASE/devices/dev_cloud01/remote-access \
  -H "Authorization: Bearer $DEMO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled":false}' | python3 -m json.tool

echo ""
echo "=== 9. GET remote-access state ==="
curl -s $BASE/devices/dev_cloud01/remote-access \
  -H "Authorization: Bearer $DEMO_TOKEN" | python3 -m json.tool
