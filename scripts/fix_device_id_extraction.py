#!/usr/bin/env python3
"""Fix device_id extraction in webhook and manual complete"""

def main():
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    # Fix webhook: device_id = order[1] -> order[2]
    old_webhook = "device_id = order[1]"
    new_webhook = "device_id = order[2]  # order[0]=id, [1]=trans_code, [2]=device_id"
    
    if old_webhook in content:
        content = content.replace(old_webhook, new_webhook)
        print("Fixed webhook device_id extraction")
    
    # Fix manual complete
    old_manual = "trans_code_db, device_id, tier, duration_days, amount = order[0], order[1], order[3], order[4], order[5]"
    new_manual = "trans_code_db, device_id, tier, duration_days, amount = order[1], order[2], order[3], order[4], order[5]  # order[0]=id, [1]=trans_code, [2]=device_id"
    
    if old_manual in content:
        content = content.replace(old_manual, new_manual)
        print("Fixed manual complete device_id extraction")
    
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()

