#!/bin/bash
curl -s -X POST http://127.0.0.1:21121/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@afkzone.io","password":"admin2026","username":"commander_admin"}' | python3 -m json.tool
