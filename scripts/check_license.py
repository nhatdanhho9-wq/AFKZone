#!/usr/bin/env python3
import subprocess
result = subprocess.run([
    'psql', '-U', 'postgres', '-h', 'localhost', '-p', '21114', '-d', 'license_db',
    '-c', "SELECT license_key, tier, max_devices FROM licenses WHERE license_key LIKE '%9FBE1B13%'"
], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)

