#!/usr/bin/env python3
"""Ensure tab is visible before rendering"""

def main():
    with open('/app/admin_dashboard.html', 'r') as f:
        content = f.read()
    
    # Add check to ensure tab is visible
    old_check = '''async function loadTrials() {
            console.log('🔄 Loading trial devices...');
            const tbody = document.getElementById('trials-tbody');
            if (!tbody) {
                console.error('❌ trials-tbody not found!');
                return;
            }'''
    
    new_check = '''async function loadTrials() {
            console.log('🔄 Loading trial devices...');
            
            // Ensure tab is visible first
            const tabElement = document.getElementById('tab-trials');
            if (!tabElement) {
                console.error('❌ tab-trials not found!');
                return;
            }
            
            // Make sure tab is active
            if (!tabElement.classList.contains('active')) {
                console.log('⚠️ Tab not active, activating...');
                tabElement.classList.add('active');
            }
            
            const tbody = document.getElementById('trials-tbody');
            if (!tbody) {
                console.error('❌ trials-tbody not found!');
                return;
            }
            
            console.log('✅ Tab element found and active');
            console.log('✅ Tbody element found:', tbody);'''
    
    if old_check in content:
        content = content.replace(old_check, new_check)
        print("Added tab visibility check")
    else:
        print("Pattern not found")
    
    with open('/app/admin_dashboard.html', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()

