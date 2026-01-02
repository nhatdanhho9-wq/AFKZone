#!/usr/bin/env python3
"""Fix trial table structure to match other tabs"""

def main():
    with open('/app/admin_dashboard.html', 'r') as f:
        content = f.read()
    
    # Fix table structure - wrap in table-container like other tabs
    old_structure = '''        <div id="tab-trials" class="tab-content">
            <div class="section-header">
                <h2>🎁 Quản lý Trial Devices</h2>
                <button class="btn btn-danger" onclick="clearAllTrials()">🗑️ Xóa tất cả</button>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Device Fingerprint</th>
                        <th>IP Address</th>
                        <th>License Key</th>
                        <th>Ngày tạo</th>
                        <th>Thao tác</th>
                    </tr>
                </thead>
                <tbody id="trials-tbody">
                    <tr><td colspan="6" style="text-align: center; padding: 20px;">Đang tải...</td></tr>
                </tbody>
            </table>
        </div>'''
    
    new_structure = '''        <div id="tab-trials" class="tab-content">
            <div class="section-header">
                <h2>🎁 Quản lý Trial Devices</h2>
                <button class="btn btn-danger" onclick="clearAllTrials()">🗑️ Xóa tất cả</button>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Device Fingerprint</th>
                            <th>IP Address</th>
                            <th>License Key</th>
                            <th>Ngày tạo</th>
                            <th>Thao tác</th>
                        </tr>
                    </thead>
                    <tbody id="trials-tbody">
                        <tr><td colspan="6" style="text-align: center; padding: 20px;">Đang tải...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>'''
    
    if old_structure in content:
        content = content.replace(old_structure, new_structure)
        print("Fixed table structure to use table-container")
    else:
        print("Structure pattern not found, trying partial match...")
        # Try to just replace the table tag
        if '<table class="data-table">' in content:
            content = content.replace('<table class="data-table">', '<div class="table-container"><table>')
            # Also need to close the div
            if '</table>\n        </div>' in content:
                content = content.replace('</table>\n        </div>', '</table>\n            </div>\n        </div>')
            print("Fixed table wrapper")
    
    with open('/app/admin_dashboard.html', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()

