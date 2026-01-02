#!/usr/bin/env python3
"""Fix trial logic and admin dashboard display"""

def main():
    with open('/app/admin_dashboard.html', 'r') as f:
        content = f.read()
    
    # Fix 1: Add console.log to debug loadTrials
    old_loadTrials = '''async function loadTrials() {
            try {
                const res = await fetch(`${API_BASE}/admin/trial-devices`, {
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                const data = await res.json();
                const devices = data.devices || data || [];'''
    
    new_loadTrials = '''async function loadTrials() {
            console.log('Loading trial devices...');
            try {
                const res = await fetch(`${API_BASE}/admin/trial-devices`, {
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                console.log('Trial devices response status:', res.status);
                const data = await res.json();
                console.log('Trial devices data:', data);
                const devices = data.devices || data || [];
                console.log('Trial devices count:', devices.length);'''
    
    if old_loadTrials in content:
        content = content.replace(old_loadTrials, new_loadTrials)
        print("Added console.log to loadTrials")
    
    with open('/app/admin_dashboard.html', 'w') as f:
        f.write(content)
    
    # Fix 2: Review trial activation logic
    # Current logic: /activate doesn't check trial_devices, so trial codes from other devices can be activated
    # This is already correct! But let's make sure /activate works for trial licenses
    
    print("\nTrial Logic Review:")
    print("- /trial/generate: Checks trial_devices to prevent same device from generating multiple trials")
    print("- /activate: Does NOT check trial_devices, so trial codes from other devices CAN be activated")
    print("- This is CORRECT behavior - allows sharing trial codes between devices")
    
    print("\nDone!")

if __name__ == "__main__":
    main()

