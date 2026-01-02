#!/usr/bin/env python3
"""
Create Tiers table, API endpoints, and add Tier Tab to admin dashboard
Also add filter/sort functionality to all tables
"""

from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://afkzone:afkzone@localhost/afkzone")

def create_tiers_table():
    """Create tiers table in database"""
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # Create tiers table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tiers (
                id SERIAL PRIMARY KEY,
                tier_key VARCHAR(50) UNIQUE NOT NULL,
                tier_name VARCHAR(100) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
        
        # Insert default tiers if not exist
        default_tiers = [
            ('basic', 'Basic', 'Gói cơ bản', True, 1),
            ('pro', 'Pro', 'Gói chuyên nghiệp', True, 2),
            ('enterprise', 'Enterprise', 'Gói doanh nghiệp', True, 3),
            ('test1', 'Test Tier 1', 'Tier test 1', True, 4),
            ('test2', 'Test Tier 2', 'Tier test 2', True, 5),
        ]
        
        for tier in default_tiers:
            try:
                conn.execute(text("""
                    INSERT INTO tiers (tier_key, tier_name, description, is_active, display_order)
                    VALUES (:key, :name, :desc, :active, :order)
                    ON CONFLICT (tier_key) DO NOTHING
                """), {"key": tier[0], "name": tier[1], "desc": tier[2], "active": tier[3], "order": tier[4]})
            except:
                pass
        conn.commit()
        
        print("✅ Created tiers table with default data")

def add_tiers_api():
    """Add Tiers API endpoints to app.py"""
    with open('/app/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '/admin/tiers' in content:
        print("⚠️ Tiers API already exists, skipping...")
        return
    
    api_code = '''

# ==================== TIERS MANAGEMENT ====================
@app.get("/admin/tiers")
def get_tiers(token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Get all tiers"""
    result = db.execute(text("SELECT * FROM tiers ORDER BY display_order")).fetchall()
    return [{
        "id": r[0],
        "tier_key": r[1],
        "tier_name": r[2],
        "description": r[3],
        "is_active": r[4],
        "display_order": r[5]
    } for r in result]

@app.get("/tiers")
def get_active_tiers(db: Session = Depends(get_db)):
    """Public: Get active tiers for dropdowns"""
    result = db.execute(text("SELECT tier_key, tier_name FROM tiers WHERE is_active=TRUE ORDER BY display_order")).fetchall()
    return [{"value": r[0], "label": r[1]} for r in result]

class TierCreate(BaseModel):
    tier_key: str
    tier_name: str
    description: Optional[str] = None
    is_active: bool = True
    display_order: int = 0

@app.post("/admin/tiers")
def create_tier(tier: TierCreate, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Create new tier"""
    try:
        db.execute(text("""
            INSERT INTO tiers (tier_key, tier_name, description, is_active, display_order)
            VALUES (:key, :name, :desc, :active, :order)
        """), {"key": tier.tier_key, "name": tier.tier_name, "desc": tier.description, "active": tier.is_active, "order": tier.display_order})
        db.commit()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/admin/tiers/{tier_id}")
def update_tier(tier_id: int, tier: TierCreate, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Update tier"""
    db.execute(text("""
        UPDATE tiers SET tier_key=:key, tier_name=:name, description=:desc, is_active=:active, display_order=:order
        WHERE id=:id
    """), {"id": tier_id, "key": tier.tier_key, "name": tier.tier_name, "desc": tier.description, "active": tier.is_active, "order": tier.display_order})
    db.commit()
    return {"success": True}

@app.delete("/admin/tiers/{tier_id}")
def delete_tier(tier_id: int, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Delete tier"""
    db.execute(text("DELETE FROM tiers WHERE id=:id"), {"id": tier_id})
    db.commit()
    return {"success": True}
'''
    
    # Add before the last line or at end
    content += api_code
    
    with open('/app/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Added Tiers API endpoints")

def add_tier_tab_and_filters():
    """Add Tier tab and filter/sort to admin dashboard"""
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('/app/admin_dashboard.html.bak_tier', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 1. Add Tier tab button
    tab_button = '<button class="nav-tab" onclick="showTab(\'tiers\')">Tiers</button>'
    if 'showTab(\'tiers\')' not in content:
        # Find the nav tabs and add Tier tab
        content = content.replace(
            "onclick=\"showTab('connections')\">Kết nối</button>",
            "onclick=\"showTab('connections')\">Kết nối</button>\n                " + tab_button
        )
        print("✅ Added Tier tab button")
    
    # 2. Add Tier tab content
    tier_tab_content = '''
    <!-- Tiers Tab -->
    <div id="tiers-tab" class="tab-content" style="display: none;">
        <div class="card">
            <div class="card-header">
                <h2>Quản lý Tier</h2>
                <button class="btn btn-primary" onclick="openTierModal()">+ Thêm Tier</button>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th onclick="sortTable('tiers', 'id')" style="cursor:pointer">ID ↕</th>
                            <th onclick="sortTable('tiers', 'tier_key')" style="cursor:pointer">Key ↕</th>
                            <th onclick="sortTable('tiers', 'tier_name')" style="cursor:pointer">Tên ↕</th>
                            <th>Mô tả</th>
                            <th onclick="sortTable('tiers', 'is_active')" style="cursor:pointer">Trạng thái ↕</th>
                            <th onclick="sortTable('tiers', 'display_order')" style="cursor:pointer">Thứ tự ↕</th>
                            <th>Thao tác</th>
                        </tr>
                    </thead>
                    <tbody id="tiers-table"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Tier Modal -->
    <div id="tier-modal" class="modal" style="display:none">
        <div class="modal-content">
            <div class="modal-header">
                <h3 id="tier-modal-title">Thêm Tier</h3>
                <button class="close-btn" onclick="closeTierModal()">&times;</button>
            </div>
            <input type="hidden" id="tier-edit-id">
            <div class="form-group">
                <label>Tier Key (unique)</label>
                <input type="text" id="tier-key" placeholder="vd: premium">
            </div>
            <div class="form-group">
                <label>Tên hiển thị</label>
                <input type="text" id="tier-name" placeholder="vd: Premium">
            </div>
            <div class="form-group">
                <label>Mô tả</label>
                <textarea id="tier-description" placeholder="Mô tả tier..."></textarea>
            </div>
            <div class="form-group">
                <label>Thứ tự hiển thị</label>
                <input type="number" id="tier-order" value="0">
            </div>
            <div class="form-group">
                <label><input type="checkbox" id="tier-active" checked> Kích hoạt</label>
            </div>
            <button class="btn btn-primary" onclick="saveTier()" style="width:100%">Lưu</button>
        </div>
    </div>
'''
    
    if 'tiers-tab' not in content:
        # Add before the last </div> of main container
        content = content.replace('</body>', tier_tab_content + '\n</body>')
        print("✅ Added Tier tab content")
    
    # 3. Add JavaScript functions for Tier management
    tier_js = '''
<script>
// ==================== TIERS MANAGEMENT ====================
let cachedTiers = [];
let tierSortField = 'display_order';
let tierSortAsc = true;

async function loadTiers() {
    try {
        const res = await fetch(`${API_BASE}/admin/tiers`, {
            headers: {'Authorization': `Bearer ${authToken}`}
        });
        cachedTiers = await res.json();
        renderTiers();
        // Also update all tier dropdowns
        updateTierDropdowns();
    } catch (e) {
        console.error('Error loading tiers:', e);
    }
}

function renderTiers() {
    const sorted = [...cachedTiers].sort((a, b) => {
        let valA = a[tierSortField];
        let valB = b[tierSortField];
        if (typeof valA === 'string') valA = valA.toLowerCase();
        if (typeof valB === 'string') valB = valB.toLowerCase();
        if (valA < valB) return tierSortAsc ? -1 : 1;
        if (valA > valB) return tierSortAsc ? 1 : -1;
        return 0;
    });
    
    const tbody = document.getElementById('tiers-table');
    tbody.innerHTML = sorted.map(t => `
        <tr>
            <td>${t.id}</td>
            <td><code>${t.tier_key}</code></td>
            <td>${t.tier_name}</td>
            <td>${t.description || '-'}</td>
            <td><span class="status-badge ${t.is_active ? 'status-active' : 'status-inactive'}">${t.is_active ? 'Kích hoạt' : 'Tắt'}</span></td>
            <td>${t.display_order}</td>
            <td>
                <button class="btn btn-action btn-edit" onclick="editTier(${t.id})">Sửa</button>
                <button class="btn btn-action btn-delete" onclick="deleteTier(${t.id})">Xóa</button>
            </td>
        </tr>
    `).join('');
}

function updateTierDropdowns() {
    const activeTiers = cachedTiers.filter(t => t.is_active);
    const options = activeTiers.map(t => `<option value="${t.tier_key}">${t.tier_name}</option>`).join('');
    
    const dropdowns = ['product-tier', 'license-tier'];
    dropdowns.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = options;
    });
}

function openTierModal(editId = null) {
    document.getElementById('tier-modal').style.display = 'flex';
    document.getElementById('tier-modal-title').textContent = editId ? 'Sửa Tier' : 'Thêm Tier';
    document.getElementById('tier-edit-id').value = editId || '';
    
    if (editId) {
        const tier = cachedTiers.find(t => t.id === editId);
        if (tier) {
            document.getElementById('tier-key').value = tier.tier_key;
            document.getElementById('tier-name').value = tier.tier_name;
            document.getElementById('tier-description').value = tier.description || '';
            document.getElementById('tier-order').value = tier.display_order;
            document.getElementById('tier-active').checked = tier.is_active;
        }
    } else {
        document.getElementById('tier-key').value = '';
        document.getElementById('tier-name').value = '';
        document.getElementById('tier-description').value = '';
        document.getElementById('tier-order').value = 0;
        document.getElementById('tier-active').checked = true;
    }
}

function closeTierModal() {
    document.getElementById('tier-modal').style.display = 'none';
}

function editTier(id) {
    openTierModal(id);
}

async function saveTier() {
    const editId = document.getElementById('tier-edit-id').value;
    const data = {
        tier_key: document.getElementById('tier-key').value,
        tier_name: document.getElementById('tier-name').value,
        description: document.getElementById('tier-description').value,
        display_order: parseInt(document.getElementById('tier-order').value) || 0,
        is_active: document.getElementById('tier-active').checked
    };
    
    try {
        const url = editId ? `${API_BASE}/admin/tiers/${editId}` : `${API_BASE}/admin/tiers`;
        const method = editId ? 'PUT' : 'POST';
        
        const res = await fetch(url, {
            method: method,
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (res.ok) {
            alert('Đã lưu tier!');
            closeTierModal();
            loadTiers();
        } else {
            const error = await res.json();
            alert('Lỗi: ' + (error.detail || 'Không thể lưu tier'));
        }
    } catch (e) {
        alert('Lỗi: ' + e.message);
    }
}

async function deleteTier(id) {
    const confirmed = await afkConfirm('Xóa tier này? Các sản phẩm/license sử dụng tier này có thể bị ảnh hưởng!');
    if (!confirmed) return;
    
    try {
        const res = await fetch(`${API_BASE}/admin/tiers/${id}`, {
            method: 'DELETE',
            headers: {'Authorization': `Bearer ${authToken}`}
        });
        if (res.ok) {
            alert('Đã xóa tier!');
            loadTiers();
        } else {
            alert('Lỗi: Không thể xóa tier');
        }
    } catch (e) {
        alert('Lỗi: ' + e.message);
    }
}

// Generic sort function for tables
function sortTable(table, field) {
    switch(table) {
        case 'tiers':
            if (tierSortField === field) tierSortAsc = !tierSortAsc;
            else { tierSortField = field; tierSortAsc = true; }
            renderTiers();
            break;
        case 'products':
            if (productSortField === field) productSortAsc = !productSortAsc;
            else { productSortField = field; productSortAsc = true; }
            renderProducts();
            break;
        case 'licenses':
            if (licenseSortField === field) licenseSortAsc = !licenseSortAsc;
            else { licenseSortField = field; licenseSortAsc = true; }
            renderLicenses();
            break;
        case 'orders':
            if (orderSortField === field) orderSortAsc = !orderSortAsc;
            else { orderSortField = field; orderSortAsc = true; }
            renderOrders();
            break;
    }
}

// Load tiers when page loads
const originalShowTab = showTab;
showTab = function(tab) {
    originalShowTab(tab);
    if (tab === 'tiers') loadTiers();
};

// Initial load of tiers for dropdowns
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(loadTiers, 1000);
});
</script>
'''
    
    if 'loadTiers' not in content:
        content = content.replace('</body>', tier_js + '\n</body>')
        print("✅ Added Tier JavaScript functions")
    
    # 4. Add sortable headers to other tables (Products, Licenses, Orders)
    # Products table headers
    content = content.replace(
        '<th>ID</th>\n                            <th>Tên</th>',
        '<th onclick="sortTable(\'products\', \'id\')" style="cursor:pointer">ID ↕</th>\n                            <th onclick="sortTable(\'products\', \'name\')" style="cursor:pointer">Tên ↕</th>'
    )
    
    # Add CSS for better table headers
    table_css = '''
<style>
/* Sortable table headers */
th[onclick] {
    cursor: pointer;
    user-select: none;
}
th[onclick]:hover {
    background: rgba(0,0,0,0.1);
}

/* Filter inputs */
.filter-input {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    margin-right: 10px;
}

/* Better status badges */
.status-active { background: #28a745; color: white; }
.status-inactive { background: #dc3545; color: white; }
.status-pending { background: #ffc107; color: #333; }
.status-badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
}
</style>
'''
    if 'Sortable table headers' not in content:
        content = content.replace('</head>', table_css + '\n</head>')
        print("✅ Added sortable table CSS")
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ DONE! All changes applied")

if __name__ == '__main__':
    create_tiers_table()
    add_tiers_api()
    add_tier_tab_and_filters()
