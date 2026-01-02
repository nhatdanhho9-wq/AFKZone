#!/usr/bin/env python3
"""Add more debugging to trial render"""

def main():
    with open('/app/admin_dashboard.html', 'r') as f:
        content = f.read()
    
    # Add more debugging before and after rendering
    old_render = '''                const devices = data.devices || data || [];
                console.log('📊 Trial devices count:', devices.length);
                
                if (!devices || devices.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #999;">Không có trial device nào</td></tr>';
                    return;
                }
                
                tbody.innerHTML = devices.map(d => `
                    <tr>
                        <td>${d.id || 'N/A'}</td>
                        <td style="font-family: monospace; font-size: 11px;">${d.device_fingerprint || 'N/A'}</td>
                        <td>${d.ip_address || 'N/A'}</td>
                        <td style="font-family: monospace; font-size: 11px; color: #007bff;">${d.license_key || 'N/A'}</td>
                        <td>${d.created_at || 'N/A'}</td>
                        <td><button class="btn btn-danger" onclick="removeTrialDevice(${d.id})" style="padding: 5px 10px; font-size: 12px;">Xóa</button></td>
                    </tr>
                `).join('');
                
                console.log('✅ Trial devices loaded successfully!');'''
    
    new_render = '''                const devices = data.devices || data || [];
                console.log('📊 Trial devices count:', devices.length);
                console.log('📋 Devices array:', devices);
                
                if (!devices || devices.length === 0) {
                    console.log('⚠️ No devices found, showing empty message');
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #999;">Không có trial device nào</td></tr>';
                    return;
                }
                
                console.log('🔨 Starting to render devices...');
                try {
                    const html = devices.map(d => {
                        console.log('🔍 Rendering device:', d);
                        return '<tr>' +
                            '<td>' + (d.id || 'N/A') + '</td>' +
                            '<td style="font-family: monospace; font-size: 11px;">' + (d.device_fingerprint || 'N/A') + '</td>' +
                            '<td>' + (d.ip_address || 'N/A') + '</td>' +
                            '<td style="font-family: monospace; font-size: 11px; color: #007bff;">' + (d.license_key || 'N/A') + '</td>' +
                            '<td>' + (d.created_at || 'N/A') + '</td>' +
                            '<td><button class="btn btn-danger" onclick="removeTrialDevice(' + d.id + ')" style="padding: 5px 10px; font-size: 12px;">Xóa</button></td>' +
                            '</tr>';
                    }).join('');
                    
                    console.log('📝 Generated HTML length:', html.length);
                    console.log('📝 Generated HTML preview:', html.substring(0, 200));
                    
                    tbody.innerHTML = html;
                    
                    console.log('✅ Trial devices loaded successfully!');
                    console.log('✅ tbody.innerHTML length:', tbody.innerHTML.length);
                } catch (renderError) {
                    console.error('❌ Error rendering devices:', renderError);
                    throw renderError;
                }'''
    
    if old_render in content:
        content = content.replace(old_render, new_render)
        print("Added detailed debugging to render process")
    else:
        print("Render pattern not found, trying alternative...")
        # Try simpler replacement
        if 'tbody.innerHTML = devices.map(d =>' in content:
            # Replace template string with string concatenation
            print("Found template string, will need manual fix")
    
    with open('/app/admin_dashboard.html', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()

