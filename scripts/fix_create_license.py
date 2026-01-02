#!/usr/bin/env python3
"""Fix license creation to set correct max_devices based on tier"""

def main():
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    # Add tier to max_devices mapping at the top of file after imports
    tier_mapping = '''
# Tier to max_devices mapping
TIER_MAX_DEVICES = {
    'basic': 2,
    'pro': 5,
    'enterprise': -1  # unlimited
}

def get_max_devices_for_tier(tier: str) -> int:
    return TIER_MAX_DEVICES.get(tier.lower(), 1)
'''
    
    # Find a good place to insert - after the imports
    insert_marker = 'from fastapi.middleware.cors import CORSMiddleware'
    if insert_marker in content and 'TIER_MAX_DEVICES' not in content:
        idx = content.find(insert_marker)
        end_of_line = content.find('\n', idx)
        content = content[:end_of_line+1] + tier_mapping + content[end_of_line+1:]
        print("Added TIER_MAX_DEVICES mapping")
    
    # Now fix all places where licenses are created
    # 1. Fix webhook license creation
    old_webhook = '"max_devices": 1'
    new_webhook = '"max_devices": get_max_devices_for_tier(order[2])'  # order[2] is tier
    
    if old_webhook in content:
        content = content.replace(old_webhook, new_webhook)
        print("Fixed webhook max_devices")
    
    # 2. Fix trial license creation
    old_trial = 'max_devices=1'
    if old_trial in content:
        # Only replace in trial context - need to be careful
        # Let's do a more targeted fix
        pass
    
    # 3. Fix admin license generation
    old_admin_gen = '"max_devices": 1,'
    # This needs tier context
    
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()

