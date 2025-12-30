// Fixes for admin dashboard JavaScript

// 1. Fix loadLicenses - /list returns {total, licenses}
const FIXED_loadLicenses = `
        async function loadLicenses() {
            try {
                const res = await fetch(\`\${API_BASE}/list\`, {
                    headers: {'admin_key': 'afkzone-admin-2025'}
                });
                if (!res.ok) {
                    throw new Error(\`HTTP \${res.status}: \${res.statusText}\`);
                }
                const data = await res.json();
                const licenses = data.licenses || data; // Handle both formats
                const tbody = document.getElementById('licenses-tbody');
                
                if (!licenses || licenses.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 20px;">Không có license nào</td></tr>';
                    return;
                }
                
                tbody.innerHTML = licenses.map(l => {
                    const expiresAt = l.expires_at ? (typeof l.expires_at === 'number' ? new Date(l.expires_at).toLocaleString('vi-VN') : new Date(l.expires_at).toLocaleString('vi-VN')) : 'Chưa kích hoạt';
                    const activatedAt = l.activated_at ? (typeof l.activated_at === 'number' ? new Date(l.activated_at).toLocaleString('vi-VN') : new Date(l.activated_at).toLocaleString('vi-VN')) : 'Chưa kích hoạt';
                    const isExpired = l.expires_at && (typeof l.expires_at === 'number' ? l.expires_at < Date.now() : new Date(l.expires_at) < new Date());
                    const isRevoked = l.is_revoked || false;
                    
                    return \`
                        <tr>
                            <td><code>\${l.license_key}</code></td>
                            <td><span class="badge badge-info">\${l.tier || 'N/A'}</span></td>
                            <td>\${l.duration_days || 'N/A'} ngày</td>
                            <td>\${l.max_devices === -1 ? 'Không giới hạn' : (l.max_devices || 'N/A')}</td>
                            <td>\${activatedAt}</td>
                            <td>\${expiresAt}</td>
                            <td>
                                \${isRevoked ? '<span class="badge badge-danger">Đã thu hồi</span>' : 
                                  isExpired ? '<span class="badge badge-warning">Hết hạn</span>' : 
                                  '<span class="badge badge-success">Hoạt động</span>'}
                            </td>
                            <td>
                                <button class="btn btn-danger" onclick="revokeLicense('\${l.license_key}')" style="padding: 5px 10px; font-size: 12px;">Thu hồi</button>
                            </td>
                        </tr>
                    \`;
                }).join('');
            } catch (e) {
                console.error('Error loading licenses:', e);
                document.getElementById('licenses-tbody').innerHTML = \`<tr><td colspan="8" style="text-align: center; color: red;">Lỗi: \${e.message}</td></tr>\`;
            }
        }
`;

// 2. Fix loadDevices - handle response format
const FIXED_loadDevices = `
        async function loadDevices() {
            try {
                const res = await fetch(\`\${API_BASE}/admin/users?limit=100\`, {
                    headers: {'Authorization': \`Bearer \${authToken}\`}
                });
                if (!res.ok) {
                    throw new Error(\`HTTP \${res.status}: \${res.statusText}\`);
                }
                const data = await res.json();
                const users = data.users || [];
                const tbody = document.getElementById('devices-tbody');
                
                if (users.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px;">Không có thiết bị nào</td></tr>';
                    return;
                }
                
                tbody.innerHTML = users.map(u => \`
                    <tr>
                        <td><code>\${u.device_id || 'N/A'}</code></td>
                        <td>\${u.device_model || 'N/A'}</td>
                        <td>\${u.app_version || 'N/A'}</td>
                        <td><code>\${u.license_key || 'N/A'}</code></td>
                        <td>\${u.license_tier || 'N/A'}</td>
                        <td>\${u.last_seen ? new Date(u.last_seen).toLocaleString('vi-VN') : 'N/A'}</td>
                        <td>
                            <button class="btn btn-danger" onclick="removeDevice('\${u.device_id}')" style="padding: 5px 10px; font-size: 12px;">Xóa</button>
                        </td>
                    </tr>
                \`).join('');
            } catch (e) {
                console.error('Error loading devices:', e);
                document.getElementById('devices-tbody').innerHTML = \`<tr><td colspan="7" style="text-align: center; color: red;">Lỗi: \${e.message}</td></tr>\`;
            }
        }
`;

// 3. Add editProduct function
const ADD_editProduct = `
        let editingProductId = null;
        
        function editProduct(productId) {
            editingProductId = productId;
            // Load product data and show modal
            fetch(\`\${API_BASE}/products?active_only=false\`)
                .then(res => res.json())
                .then(data => {
                    const product = data.products.find(p => p.id === productId);
                    if (product) {
                        document.getElementById('product-modal-title').textContent = 'Sửa sản phẩm';
                        document.getElementById('product-name').value = product.name;
                        document.getElementById('product-tier').value = product.tier;
                        document.getElementById('product-duration').value = product.duration_days;
                        document.getElementById('product-price').value = product.price;
                        document.getElementById('product-max-devices').value = product.max_devices;
                        document.getElementById('product-description').value = product.description || '';
                        document.getElementById('product-modal').classList.add('active');
                    }
                })
                .catch(e => alert('Lỗi: ' + e.message));
        }
        
        async function deleteProduct(productId) {
            if (!confirm('Bạn có chắc muốn xóa sản phẩm này?')) return;
            
            try {
                const res = await fetch(\`\${API_BASE}/admin/products/\${productId}\`, {
                    method: 'DELETE',
                    headers: {'Authorization': \`Bearer \${authToken}\`}
                });
                
                if (res.ok) {
                    alert('Sản phẩm đã được xóa!');
                    loadProducts();
                } else {
                    const error = await res.json();
                    alert('Lỗi: ' + (error.detail || 'Không thể xóa sản phẩm'));
                }
            } catch (e) {
                alert('Lỗi: ' + e.message);
            }
        }
`;

// 4. Fix saveProduct to handle both create and update
const FIXED_saveProduct = `
        async function saveProduct() {
            const product = {
                name: document.getElementById('product-name').value,
                tier: document.getElementById('product-tier').value,
                duration_days: parseInt(document.getElementById('product-duration').value),
                price: parseInt(document.getElementById('product-price').value),
                max_devices: parseInt(document.getElementById('product-max-devices').value),
                description: document.getElementById('product-description').value,
                is_active: true
            };

            if (!product.name || !product.tier || !product.duration_days || product.price === undefined) {
                alert('Vui lòng điền đầy đủ thông tin');
                return;
            }

            try {
                let res;
                if (editingProductId) {
                    // Update
                    res = await fetch(\`\${API_BASE}/admin/products/\${editingProductId}\`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': \`Bearer \${authToken}\`
                        },
                        body: JSON.stringify(product)
                    });
                } else {
                    // Create
                    res = await fetch(\`\${API_BASE}/admin/products\`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': \`Bearer \${authToken}\`
                        },
                        body: JSON.stringify(product)
                    });
                }

                if (res.ok) {
                    alert(editingProductId ? 'Sản phẩm đã được cập nhật!' : 'Sản phẩm đã được tạo thành công!');
                    closeProductModal();
                    editingProductId = null;
                    loadProducts();
                } else {
                    const error = await res.json();
                    alert('Lỗi: ' + (error.detail || 'Không thể lưu sản phẩm'));
                }
            } catch (e) {
                alert('Lỗi: ' + e.message);
            }
        }
        
        function closeProductModal() {
            document.getElementById('product-modal').classList.remove('active');
            editingProductId = null;
            // Clear form
            document.getElementById('product-name').value = '';
            document.getElementById('product-tier').value = 'basic';
            document.getElementById('product-duration').value = '';
            document.getElementById('product-price').value = '';
            document.getElementById('product-max-devices').value = '';
            document.getElementById('product-description').value = '';
        }
`;

// 5. Fix generateLicense - use correct endpoint format
const FIXED_generateLicense = `
        async function generateLicense() {
            const tier = document.getElementById('license-tier').value;
            const duration_days = parseInt(document.getElementById('license-duration').value);
            const max_devices = parseInt(document.getElementById('license-max-devices').value) || null;
            const notes = document.getElementById('license-notes').value;

            if (!tier || !duration_days) {
                document.getElementById('license-result').innerHTML = '<div class="alert alert-error">Vui lòng điền đầy đủ thông tin</div>';
                return;
            }

            try {
                const res = await fetch(\`\${API_BASE}/admin/licenses/generate\`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': \`Bearer \${authToken}\`
                    },
                    body: JSON.stringify({tier, duration_days, max_devices, notes})
                });

                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('license-result').innerHTML = \`
                        <div class="alert alert-success">
                            <strong>License đã được tạo!</strong><br>
                            License Key: <code>\${data.license_key}</code><br>
                            <button class="btn btn-primary" onclick="navigator.clipboard.writeText('\${data.license_key}')" style="margin-top: 10px;">Copy License Key</button>
                        </div>
                    \`;
                    loadLicenses();
                } else {
                    const error = await res.json();
                    let errorMsg = error.detail || 'Không thể tạo license';
                    if (Array.isArray(error.detail)) {
                        errorMsg = error.detail.map(e => e.msg || e).join(', ');
                    }
                    document.getElementById('license-result').innerHTML = \`
                        <div class="alert alert-error">Lỗi: \${errorMsg}</div>
                    \`;
                }
            } catch (e) {
                document.getElementById('license-result').innerHTML = \`
                    <div class="alert alert-error">Lỗi: \${e.message}</div>
                \`;
            }
        }
`;

console.log('All fixes ready to apply');

