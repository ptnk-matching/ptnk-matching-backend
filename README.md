# PTNK Matching Backend

Backend API cho hệ thống matching giảng viên và học sinh.

## Cấu trúc

```
ptnk-matching-backend/
├── api/
│   ├── index.py          # Vercel serverless function handler
│   └── requirements.txt  # Python dependencies
├── backend/
│   ├── main.py          # FastAPI application
│   ├── routers/         # API routes
│   ├── services/         # Business logic
│   ├── models/          # Data models
│   ├── database/        # Database connections
│   └── middleware/       # Middleware (auth, CORS, etc.)
└── vercel.json          # Vercel configuration
```

## Deploy lên Vercel

1. **Tạo Project mới trên Vercel:**
   - Import repository này
   - Root Directory: Để trống (empty)
   - Framework: Other

2. **Thêm Environment Variables:**
   - `OPENAI_API_KEY`
   - `MONGODB_URI`
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_S3_BUCKET_NAME`
   - `NEXTAUTH_SECRET` (phải giống với frontend)
   - `CORS_ORIGINS` (URL của frontend)

3. **Deploy**

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/upload-and-match` - Upload file và match với giảng viên
- `GET /api/professors` - Lấy danh sách giảng viên
- `POST /api/users/` - Tạo user mới
- `GET /api/users/me` - Lấy thông tin user hiện tại
- Và nhiều endpoints khác...

Xem `backend/main.py` để biết đầy đủ các endpoints.

