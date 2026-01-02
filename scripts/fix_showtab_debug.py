#!/usr/bin/env python3
"""Add debugging to showTab function"""

def main():
    with open('/app/admin_dashboard.html', 'r') as f:
        content = f.read()
    
    # Add console.log to showTab
    old_showTab = '''function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // Show selected tab
            document.getElementById(`tab-${tabName}`).classList.add('active');
            event.target.classList.add('active');

            // Load data for tab
            if (tabName === 'dashboard') loadDashboard();
            else if (tabName === 'products') loadProducts();
            else if (tabName === 'licenses') loadLicenses();
            else if (tabName === 'devices') loadDevices();
            else if (tabName === 'connections') loadConnections();
            else if (tabName === 'orders') loadOrders();
            else if (tabName === 'trials') loadTrials();
        }'''
    
    new_showTab = '''function showTab(tabName) {
            console.log('🔄 showTab called with:', tabName);
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // Show selected tab
            const tabElement = document.getElementById(`tab-${tabName}`);
            if (!tabElement) {
                console.error('❌ Tab element not found:', `tab-${tabName}`);
                return;
            }
            tabElement.classList.add('active');
            if (event && event.target) {
                event.target.classList.add('active');
            }

            // Load data for tab
            console.log('📊 Loading data for tab:', tabName);
            if (tabName === 'dashboard') loadDashboard();
            else if (tabName === 'products') loadProducts();
            else if (tabName === 'licenses') loadLicenses();
            else if (tabName === 'devices') loadDevices();
            else if (tabName === 'connections') loadConnections();
            else if (tabName === 'orders') loadOrders();
            else if (tabName === 'trials') {
                console.log('🎁 Calling loadTrials()...');
                loadTrials();
            } else {
                console.warn('⚠️ Unknown tab:', tabName);
            }
        }'''
    
    if old_showTab in content:
        content = content.replace(old_showTab, new_showTab)
        print("Added debugging to showTab")
    else:
        print("showTab pattern not found")
    
    with open('/app/admin_dashboard.html', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()

