#!/usr/bin/env python3
"""Fix the license recover endpoint to check for 'success' status"""

def main():
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    # Fix the status check from 'completed' to 'success'
    old = "if status != 'completed':"
    new = "if status not in ['completed', 'success']:"
    
    if old in content:
        content = content.replace(old, new)
        with open('/app/app.py', 'w') as f:
            f.write(content)
        print("Fixed recover endpoint!")
    else:
        print("Already fixed or pattern not found")

if __name__ == "__main__":
    main()

