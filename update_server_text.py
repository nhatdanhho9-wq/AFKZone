#!/usr/bin/env python3
"""Update server app.py to change 'Vô cực' to 'Không giới hạn thiết bị'"""
import subprocess

# SSH and update file
ssh_cmd = [
    'ssh', 'ubuntu',
    '''cd ~/license-api && python3 << 'EOF'
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the text
content = content.replace('max_devices_display = "Vô cực"', 'max_devices_display = "Không giới hạn thiết bị"')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated app.py successfully")
EOF
docker-compose restart
'''
]

result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
print("STDOUT:", result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

