#!/usr/bin/env python3
"""Fix trial activation security - prevent devices that activated trial from generating new trials"""

def main():
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    # Find the activate endpoint and add trial_devices check/insert
    old_activate = '''    # Activate on this device
    try:
        db.execute(
            text("INSERT INTO license_devices (license_key, device_id, activated_at) VALUES (:key, :device, NOW())"),
            {"key": license_key, "device": device_id}
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add device: {str(e)}")'''
    
    new_activate = '''    # Activate on this device
    try:
        db.execute(
            text("INSERT INTO license_devices (license_key, device_id, activated_at) VALUES (:key, :device, NOW())"),
            {"key": license_key, "device": device_id}
        )
        
        # If this is a trial license, also mark device in trial_devices to prevent generating new trials
        if license_key.startswith('AFK-TRIAL-'):
            # Check if device already in trial_devices
            existing_trial = db.execute(
                text("SELECT id FROM trial_devices WHERE device_fingerprint=:device"),
                {"device": device_id}
            ).fetchone()
            
            if not existing_trial:
                # Get IP address from request (if available) or use device_id
                # Insert into trial_devices to mark this device as having used a trial
                try:
                    db.execute(
                        text("INSERT INTO trial_devices (device_fingerprint, license_key, created_at) VALUES (:device, :key, NOW())"),
                        {"device": device_id, "key": license_key}
                    )
                except Exception as e:
                    # Ignore duplicate errors, just log
                    print(f"Warning: Could not insert into trial_devices: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add device: {str(e)}")'''
    
    if old_activate in content:
        content = content.replace(old_activate, new_activate)
        print("Added trial_devices check/insert in activate endpoint")
    else:
        print("Pattern not found, trying alternative...")
        # Try to find and replace just the INSERT part
        if 'INSERT INTO license_devices' in content:
            # Find the section and add trial check after it
            insert_pattern = 'INSERT INTO license_devices (license_key, device_id, activated_at) VALUES (:key, :device, NOW())'
            if insert_pattern in content:
                # Add trial check after the INSERT
                trial_check = '''
        
        # If this is a trial license, mark device in trial_devices to prevent generating new trials
        if license_key.startswith('AFK-TRIAL-'):
            existing_trial = db.execute(
                text("SELECT id FROM trial_devices WHERE device_fingerprint=:device"),
                {"device": device_id}
            ).fetchone()
            if not existing_trial:
                try:
                    db.execute(
                        text("INSERT INTO trial_devices (device_fingerprint, license_key, created_at) VALUES (:device, :key, NOW())"),
                        {"device": device_id, "key": license_key}
                    )
                except Exception as e:
                    print(f"Warning: Could not insert into trial_devices: {e}")'''
                
                # Insert after the license_devices INSERT
                content = content.replace(
                    insert_pattern + '"),',
                    insert_pattern + '"),' + trial_check
                )
                print("Added trial_devices check after license_devices insert")
    
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()

