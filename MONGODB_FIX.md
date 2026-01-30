# Fix MongoDB SSL/TLS Connection Error trên Vercel

## Lỗi hiện tại:
```
[SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error
```

## Giải pháp:

### 1. Kiểm tra MongoDB URI trong Vercel Environment Variables

Vào **Vercel Dashboard** → **Settings** → **Environment Variables**, kiểm tra `MONGODB_URI`:

**Format đúng:**
```
mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
```

**Lưu ý:**
- Phải có `retryWrites=true&w=majority`
- Password không được có ký tự đặc biệt hoặc phải URL encode
- Nếu password có `@`, `:`, `/`, `#`, `?`, `&`, `=` → phải URL encode

### 2. Whitelist IP trong MongoDB Atlas

**QUAN TRỌNG:** Vercel serverless functions có IP động, cần whitelist tất cả IPs:

1. Vào https://cloud.mongodb.com/
2. Chọn cluster của bạn
3. Vào **Network Access** (bên trái)
4. Click **Add IP Address**
5. Click **Allow Access from Anywhere** → Nhập `0.0.0.0/0`
6. Click **Confirm**
7. Đợi 1-2 phút để apply

### 3. Kiểm tra Database User

1. Vào **Database Access** (bên trái)
2. Kiểm tra user có tồn tại không
3. Đảm bảo user có quyền **Atlas admin** hoặc **Read and write to any database**

### 4. Test MongoDB URI

Thử test connection string trực tiếp:

```bash
# Test với mongosh (nếu có)
mongosh "mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"
```

Hoặc test với Python:
```python
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def test():
    uri = "mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"
    client = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
    try:
        await client.admin.command('ping')
        print("✅ Connection successful!")
    except Exception as e:
        print(f"❌ Error: {e}")

asyncio.run(test())
```

### 5. Nếu vẫn lỗi, thử các cách sau:

#### Option A: Tạo MongoDB User mới
1. Tạo user mới với password đơn giản (không có ký tự đặc biệt)
2. Copy connection string mới
3. Update trong Vercel Environment Variables

#### Option B: URL Encode Password
Nếu password có ký tự đặc biệt:
- `@` → `%40`
- `:` → `%3A`
- `/` → `%2F`
- `#` → `%23`
- `?` → `%3F`
- `&` → `%26`
- `=` → `%3D`

Ví dụ: Password `p@ssw:rd` → `p%40ssw%3Ard`

#### Option C: Dùng mongodb:// thay vì mongodb+srv://
Nếu `mongodb+srv://` không work, thử `mongodb://` với đầy đủ hosts:

```
mongodb://username:password@host1:27017,host2:27017,host3:27017/?ssl=true&replicaSet=atlas-xxxxx-shard-0&authSource=admin&retryWrites=true&w=majority
```

Lấy connection string này từ MongoDB Atlas → Connect → Connect your application → Standard connection string

### 6. Kiểm tra Logs trong Vercel

1. Vào **Vercel Dashboard** → **Deployments**
2. Chọn deployment mới nhất
3. Click vào **Functions** tab
4. Xem logs để biết lỗi cụ thể

### 7. Temporary Workaround

Code đã được update để:
- Handle MongoDB connection errors gracefully
- Sử dụng Google ID làm fallback nếu MongoDB không available
- Vẫn hoạt động được (nhưng không lưu vào database)

Hệ thống sẽ vẫn chạy được nhưng:
- Users không được lưu vào MongoDB
- Documents không được lưu vào MongoDB
- Registrations không được lưu vào MongoDB

Nhưng matching vẫn hoạt động bình thường!

## Checklist:

- [ ] MongoDB URI format đúng: `mongodb+srv://...?retryWrites=true&w=majority`
- [ ] IP whitelist: `0.0.0.0/0` trong MongoDB Atlas
- [ ] Database user có quyền đúng
- [ ] Password không có ký tự đặc biệt hoặc đã URL encode
- [ ] Test connection string thành công
- [ ] Redeploy trên Vercel sau khi sửa env variables

