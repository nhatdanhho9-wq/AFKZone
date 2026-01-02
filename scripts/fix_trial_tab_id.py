#!/usr/bin/env python3
"""Fix trial tab ID mismatch"""

def main():
    with open('/app/admin_dashboard.html', 'r') as f:
        content = f.read()
    
    # Fix tab ID from "trials-tab" to "tab-trials" to match showTab pattern
    old_id = 'id="trials-tab"'
    new_id = 'id="tab-trials"'
    
    if old_id in content:
        content = content.replace(old_id, new_id)
        print("Fixed trial tab ID from 'trials-tab' to 'tab-trials'")
    
    with open('/app/admin_dashboard.html', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()

