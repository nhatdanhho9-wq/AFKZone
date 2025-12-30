# AFK Zone Admin Dashboard Setup Guide

## Tổng quan

Admin Dashboard cho phép quản lý:
- ✅ Sản phẩm (Products) - Thêm, sửa, xóa, đổi giá
- ✅ Licenses - Tạo, xem, thu hồi licenses
- ✅ Thiết bị (Devices) - Xem thông tin, xóa thiết bị
- ✅ Kết nối (Connections) - Tracking tất cả kết nối với full info
- ✅ Dashboard - Thống kê tổng quan

## Cài đặt

### 1. Database Migration

Chạy SQL migration để tạo các bảng cần thiết:

```bash
# SSH vào server
ssh ubuntu

# Vào container database hoặc connect trực tiếp
docker exec -i afkzone-license-api psql -U postgres -d afkzone_license < admin_database_migration.sql
```

Hoặc chạy từng lệnh SQL trong file `admin_database_migration.sql`.

### 2. Thêm Admin Endpoints vào app.py

Copy nội dung từ `admin_endpoints.py` và thêm vào cuối file `app.py.original` trên server.

**Lưu ý:** Cần import thêm:
```python
import secrets  # Đã có
from datetime import datetime, timedelta  # Đã có
```

### 3. Deploy Admin Dashboard Frontend

Có 2 cách:

#### Cách 1: Serve static file từ FastAPI

Thêm vào `app.py`:
```python
from fastapi.staticfiles import StaticFiles

app.mount("/admin", StaticFiles(directory="admin_dashboard", html=True), name="admin")
```

Sau đó copy `admin_dashboard.html` vào thư mục `admin_dashboard/` trên server.

#### Cách 2: Deploy riêng (Nginx/Apache)

1. Copy `admin_dashboard.html` lên server
2. Cấu hình Nginx/Apache để serve file này
3. Đảm bảo CORS được cấu hình đúng

### 4. Tạo Admin User

Mặc định có user `admin` với password `admin123` (đã hash trong SQL).

**QUAN TRỌNG:** Đổi password ngay sau khi deploy!

Để tạo user mới:
```sql
-- Hash password bằng Python
python3 -c "import bcrypt; print(bcrypt.hashpw('your_password'.encode(), bcrypt.gensalt()).decode())"

-- Insert vào database
INSERT INTO admin_users (username, password_hash, role)
VALUES ('newadmin', '$2b$12$...', 'admin');
```

### 5. Cấu hình CORS (nếu cần)

Nếu dashboard chạy trên domain khác, cần thêm vào `app.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://admin.afkzone.cloud"],  # Domain của dashboard
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Sử dụng

### Đăng nhập

1. Mở `https://api.afkzone.cloud/admin` (hoặc domain bạn deploy)
2. Đăng nhập với:
   - Username: `admin`
   - Password: `admin123` (đổi ngay!)

### Quản lý Sản phẩm

1. Vào tab **Sản phẩm**
2. Click **+ Thêm sản phẩm**
3. Điền thông tin:
   - Tên sản phẩm
   - Tier (basic/pro/enterprise)
   - Thời hạn (ngày)
   - Giá (VND)
   - Số thiết bị tối đa (-1 = không giới hạn)
   - Mô tả
4. Click **Lưu**

**Lưu ý:** Sau khi thay đổi sản phẩm, clients sẽ tự động refresh khi gọi `/products` (có cache-busting).

### Tạo License

1. Vào tab **Licenses**
2. Click **+ Tạo License**
3. Điền thông tin:
   - Tier
   - Thời hạn (ngày)
   - Số thiết bị tối đa
   - Ghi chú
4. Click **Tạo License**
5. Copy license key được tạo

### Xóa Thiết bị

1. Vào tab **Thiết bị**
2. Tìm thiết bị cần xóa
3. Click **Xóa**
4. Xác nhận

**Lưu ý:** Xóa thiết bị sẽ:
- Deactivate device từ tất cả licenses
- Xóa device record khỏi database

### Xem Lịch sử Kết nối

1. Vào tab **Kết nối**
2. Xem danh sách tất cả kết nối với:
   - Device ID
   - Peer ID
   - Loại kết nối (remote/file_transfer/view_camera/terminal)
   - IP Address
   - Thời gian kết nối/ngắt
   - Thời lượng
   - License key

## Tracking Connections

Để tracking connections tự động, cần integrate với RustDesk server:

1. **Từ RustDesk Server:** Gọi `/admin/connections/log` khi có connection mới
2. **Từ Client:** Gọi `/admin/connections/log` khi connect (optional)

Example:
```python
# In RustDesk server code
import requests

def log_connection(device_id, peer_id, connection_type, ip_address, license_key=None):
    requests.post('https://api.afkzone.cloud/admin/connections/log', json={
        'device_id': device_id,
        'peer_id': peer_id,
        'connection_type': connection_type,
        'ip_address': ip_address,
        'license_key': license_key
    })
```

## API Endpoints

### Admin Endpoints (require JWT token)

- `POST /admin/login` - Đăng nhập
- `GET /admin/dashboard/stats` - Thống kê
- `GET /admin/products` - List products
- `POST /admin/products` - Tạo product
- `PUT /admin/products/{id}` - Sửa product
- `DELETE /admin/products/{id}` - Xóa product
- `GET /admin/users` - List devices
- `GET /admin/devices/{device_id}` - Thông tin device
- `DELETE /admin/devices/{device_id}` - Xóa device
- `POST /admin/licenses/generate` - Tạo license
- `POST /admin/licenses/{key}/revoke` - Thu hồi license
- `GET /admin/connections` - List connections
- `POST /admin/connections/log` - Log connection

## Security

1. **Đổi password mặc định ngay!**
2. Sử dụng HTTPS
3. Giới hạn IP access cho admin dashboard (Nginx/Apache)
4. Rotate JWT secret key định kỳ
5. Log tất cả admin actions

## Troubleshooting

### Không đăng nhập được

- Kiểm tra admin_users table có user không
- Kiểm tra password hash đúng format bcrypt không
- Kiểm tra JWT secret key trong code

### Không thấy connections

- Kiểm tra connection_logs table có data không
- Kiểm tra RustDesk server có gọi `/admin/connections/log` không
- Kiểm tra CORS settings

### Products không update trên client

- Client cần có cache-busting (timestamp parameter)
- Kiểm tra `/products` endpoint trả về data mới không

## Next Steps

1. ✅ Deploy admin dashboard
2. ✅ Test tất cả tính năng
3. ⏳ Add more analytics (revenue charts, device trends)
4. ⏳ Add export functionality (CSV/Excel)
5. ⏳ Add email notifications
6. ⏳ Add audit logs for admin actions

