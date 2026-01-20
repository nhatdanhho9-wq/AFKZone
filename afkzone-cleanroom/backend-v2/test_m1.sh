#!/bin/bash
BASE=http://127.0.0.1:21121

echo "=== 1. Login ==="
LOGIN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@afkzone.io","password":"demo2026"}')
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
echo "Token: ${TOKEN:0:30}..."

echo ""
echo "=== 2. Register NEW device (with agent_token) ==="
curl -s -X POST $BASE/devices/register \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"HOST_PC_TEST","type":"pc","vcpu":8,"ram_gb":16,"description":"Test Windows PC"}' | python3 -m json.tool

echo ""
echo "=== 3. Heartbeat with stats ==="
curl -s -X POST $BASE/devices/dev_cloud01/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"status":"online","fps":60,"bitrate_kbps":3500}' | python3 -m json.tool

echo ""
echo "=== 4. Get pending sessions ==="
curl -s "$BASE/sessions/pending?device_id=dev_cloud01" | python3 -m json.tool

echo ""
echo "=== 5. Logs ==="
tail -10 /var/log/backend-v2.log | grep -E "(DEVICE|HEARTBEAT|CONTROL)"
