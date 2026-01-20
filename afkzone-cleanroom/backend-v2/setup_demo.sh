#!/bin/bash
BASE=http://127.0.0.1:21121

# Register demo
curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@afkzone.io","password":"demo2026","username":"commander_demo"}'

echo ""

# Seed
curl -s -X POST $BASE/admin/seed
