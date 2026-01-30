# PTNK Matching Backend

Backend API cho hệ thống matching giảng viên và học sinh. Deploy trên Vercel như Python Serverless Functions.

## 📁 Cấu trúc

```
ptnk-matching-backend/
├── api/
│   ├── index.py          # Vercel serverless function handler
│   └── requirements.txt  # Python dependencies
├── backend/
│   ├── main.py          # FastAPI application
│   ├── routers/         # API routes
│   ├── services/        # Business logic
│   ├── models/          # Data models
│   ├── database/        # Database connections
│   └── middleware/      # Middleware (auth, CORS, etc.)
├── vercel.json          # Vercel configuration
├── README.md            # File này
└── DEPLOY.md            # Hướng dẫn deploy chi tiết
```

## 🚀 Hướng dẫn Deploy lên Vercel

### Bước 1: Push code lên GitHub

1. **Tạo repository mới trên GitHub:**
   - Tên: `ptnk-matching-backend`
   - Public hoặc Private tùy bạn

2. **Push code lên GitHub:**
   ```bash
   cd ptnk-matching-backend
   git init
   git add .
   git commit -m "Initial commit: Backend for PTNK Matching"
   git branch -M main
   git remote add origin https://github.com/your-username/ptnk-matching-backend.git
   git push -u origin main
   ```

### Bước 2: Tạo Project Vercel

1. **Vào Vercel Dashboard:**
   - Truy cập: https://vercel.com/dashboard
   - Click "Add New..." → "Project"

2. **Import Repository:**
   - Chọn repository: `ptnk-matching-backend` (vừa tạo)
   - Click "Import"

3. **Cấu hình Project:**
   - **Project Name**: `ptnk-matching-backend` (hoặc tên bạn muốn)
   - **Root Directory**: Để TRỐNG (empty) ⚠️ Quan trọng!
   - **Framework Preset**: Other
   - **Build Command**: Để trống
   - **Output Directory**: Để trống
   - **Install Command**: Để trống

4. **Click "Deploy"** (sẽ fail lần đầu vì chưa có env variables, không sao)

### Bước 3: Thêm Environment Variables

Vào **Settings** → **Environment Variables** của backend project, thêm các biến sau:

#### 🔴 Bắt buộc:
```
OPENAI_API_KEY=sk-your-openai-api-key
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET_NAME=your-bucket-name
NEXTAUTH_SECRET=s+LakqLlpg0DunI/Mavp+rTlLXtZHTnSQDtgDDD/aTM=
```

**Lưu ý:** `NEXTAUTH_SECRET` phải giống với frontend project!

#### 🟡 Optional:
```
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini
MONGODB_DB_NAME=hanh_matching
AWS_REGION=us-east-1
CORS_ORIGINS=https://ptnk-matching-ten.vercel.app
```

**Lưu ý về CORS_ORIGINS:**
- Set thành URL của frontend để tránh CORS errors
- Ví dụ: `https://ptnk-matching-ten.vercel.app`
- Hoặc set `*` để allow all (chỉ dùng cho development)

### Bước 4: Deploy và lấy URL

1. **Redeploy project:**
   - Sau khi thêm env variables, Vercel sẽ tự động redeploy
   - Hoặc vào Deployments → Click "Redeploy"

2. **Lấy URL:**
   - Sau khi deploy xong, bạn sẽ có URL như: `https://ptnk-matching-backend.vercel.app`
   - Copy URL này để cấu hình frontend

### Bước 5: Cấu hình Frontend để kết nối với Backend

1. **Vào Frontend Project trong Vercel Dashboard:**
   - Project: `ptnk-matching-ten` (hoặc tên frontend project của bạn)

2. **Vào Settings → Environment Variables**

3. **Thêm Environment Variable:**
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: URL backend vừa deploy (ví dụ: `https://ptnk-matching-backend.vercel.app`)
   - **Environment**: Production, Preview, Development
   - Click "Save"

4. **Redeploy Frontend:**
   - Trigger một deployment mới để áp dụng env variable

### Bước 6: Kiểm tra

#### Test Backend:
```bash
curl https://ptnk-matching-backend.vercel.app/api/health
```
Kết quả mong đợi: `{"status": "ok", ...}`

#### Test Frontend kết nối Backend:
- Truy cập: `https://ptnk-matching-ten.vercel.app`
- Kiểm tra xem có còn cảnh báo "Backend không kết nối được" không
- Thử upload file và test matching

## 📡 API Endpoints

### Health Check
- `GET /api/health` - Kiểm tra server có hoạt động không

### Matching
- `POST /api/upload-and-match` - Upload file và match với giảng viên
- `POST /api/match` - Match text với giảng viên

### Professors
- `GET /api/professors` - Lấy danh sách giảng viên
- `GET /api/professor-profile/` - Lấy profile giảng viên hiện tại
- `POST /api/professor-profile/` - Tạo profile giảng viên
- `PUT /api/professor-profile/` - Cập nhật profile giảng viên

### Users
- `POST /api/users/` - Tạo user mới
- `GET /api/users/me` - Lấy thông tin user hiện tại

### Documents
- `POST /api/documents/` - Upload document
- `GET /api/documents/me` - Lấy documents của user hiện tại
- `GET /api/documents/{id}` - Lấy document theo ID
- `GET /api/documents/{id}/download` - Download document

### Registrations
- `POST /api/registrations/` - Tạo registration mới
- `GET /api/registrations/` - Lấy registrations của user
- `PUT /api/registrations/{id}/status` - Cập nhật status registration
- `DELETE /api/registrations/{id}` - Xóa registration

### Notifications
- `GET /api/notifications/` - Lấy notifications
- `GET /api/notifications/unread-count` - Lấy số notifications chưa đọc
- `PUT /api/notifications/{id}/read` - Đánh dấu đã đọc
- `PUT /api/notifications/read-all` - Đánh dấu tất cả đã đọc
- `DELETE /api/notifications/{id}` - Xóa notification

Xem `backend/main.py` để biết đầy đủ các endpoints và request/response formats.

## 🔧 Troubleshooting

### Backend không deploy được
- ✅ Kiểm tra `api/index.py` có tồn tại không
- ✅ Kiểm tra `api/requirements.txt` có đầy đủ dependencies không
- ✅ Xem build logs trong Vercel Dashboard
- ✅ Kiểm tra `vercel.json` có đúng format không
- ✅ Kiểm tra Root Directory có để trống không

### Frontend không kết nối được Backend
- ✅ Kiểm tra `NEXT_PUBLIC_API_URL` đã được set chưa
- ✅ Kiểm tra URL backend có đúng không
- ✅ Kiểm tra CORS settings trong backend
- ✅ Xem browser console để xem lỗi cụ thể

### CORS Error
- ✅ Thêm frontend URL vào `CORS_ORIGINS` trong backend env variables
- ✅ Kiểm tra CORS settings trong `backend/main.py`
- ✅ Đảm bảo frontend URL không có trailing slash

### 404 Not Found khi gọi API
- ✅ Kiểm tra route trong `vercel.json` có đúng không
- ✅ Kiểm tra `api/index.py` có được deploy không
- ✅ Xem function logs trong Vercel Dashboard

## 📝 Lưu ý quan trọng

1. **Root Directory phải để trống** - Vercel cần thấy `api/index.py` ở root
2. **NEXTAUTH_SECRET** phải giống nhau giữa frontend và backend
3. **CORS_ORIGINS** nên set thành URL của frontend để tránh CORS errors
4. **Environment Variables** phải được set đầy đủ trước khi deploy
5. **Sau khi thêm env variables**, cần redeploy để áp dụng

## 🔗 Liên kết

- Frontend Project: `ptnk-matching-ten` trên Vercel
- Backend API: `https://ptnk-matching-backend.vercel.app`
- GitHub Repository: `ptnk-matching/ptnk-matching-backend`

## 📚 Tài liệu tham khảo

- [Vercel Python Functions](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Mangum Documentation](https://mangum.io/) - AWS Lambda/ASGI adapter
