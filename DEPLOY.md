# Hướng dẫn Deploy Backend lên Vercel

## Bước 1: Push code lên GitHub

1. **Tạo repository mới trên GitHub:**
   - Tên: `ptnk-matching-backend`
   - Public hoặc Private tùy bạn

2. **Push code lên GitHub:**
   ```bash
   cd /Users/longzim/Documents/ZIMAcademy/ptnk-matching-backend
   git init
   git add .
   git commit -m "Initial commit: Backend for PTNK Matching"
   git branch -M main
   git remote add origin https://github.com/your-username/ptnk-matching-backend.git
   git push -u origin main
   ```

## Bước 2: Tạo Project Vercel

1. **Vào Vercel Dashboard:**
   - Truy cập: https://vercel.com/dashboard
   - Click "Add New..." → "Project"

2. **Import Repository:**
   - Chọn repository: `ptnk-matching-backend` (vừa tạo)
   - Click "Import"

3. **Cấu hình Project:**
   - **Project Name**: `ptnk-matching-backend` (hoặc tên bạn muốn)
   - **Root Directory**: Để TRỐNG (empty)
   - **Framework Preset**: Other
   - **Build Command**: Để trống
   - **Output Directory**: Để trống
   - **Install Command**: Để trống

4. **Click "Deploy"**

## Bước 3: Thêm Environment Variables

Vào **Settings** → **Environment Variables**, thêm:

### Bắt buộc:
```
OPENAI_API_KEY=sk-your-openai-api-key
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET_NAME=your-bucket-name
NEXTAUTH_SECRET=s+LakqLlpg0DunI/Mavp+rTlLXtZHTnSQDtgDDD/aTM=
```

**Lưu ý:** `NEXTAUTH_SECRET` phải giống với frontend project!

### Optional:
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

## Bước 4: Deploy và lấy URL

1. **Deploy project:**
   - Sau khi thêm env variables, Vercel sẽ tự động redeploy
   - Hoặc trigger deployment thủ công

2. **Lấy URL:**
   - Sau khi deploy xong, bạn sẽ có URL như: `https://ptnk-matching-backend.vercel.app`
   - Copy URL này

## Bước 5: Cấu hình Frontend

1. **Vào Frontend Project trong Vercel Dashboard:**
   - Project: `ptnk-matching-ten`

2. **Vào Settings → Environment Variables**

3. **Thêm Environment Variable:**
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: URL backend vừa deploy (ví dụ: `https://ptnk-matching-backend.vercel.app`)
   - **Environment**: Production, Preview, Development
   - Click "Save"

4. **Redeploy Frontend:**
   - Trigger một deployment mới để áp dụng env variable

## Bước 6: Kiểm tra

### Test Backend:
```bash
curl https://ptnk-matching-backend.vercel.app/api/health
```
Kết quả mong đợi: `{"status": "ok", ...}`

### Test Frontend kết nối Backend:
- Truy cập: `https://ptnk-matching-ten.vercel.app`
- Kiểm tra xem có còn cảnh báo "Backend không kết nối được" không
- Thử upload file và test matching

## Troubleshooting

### Backend không deploy được
- Kiểm tra `api/index.py` có tồn tại không
- Kiểm tra `api/requirements.txt` có đầy đủ dependencies không
- Xem build logs trong Vercel Dashboard
- Kiểm tra `vercel.json` có đúng format không

### Frontend không kết nối được Backend
- Kiểm tra `NEXT_PUBLIC_API_URL` đã được set chưa
- Kiểm tra URL backend có đúng không
- Kiểm tra CORS settings trong backend
- Xem browser console để xem lỗi cụ thể

### CORS Error
- Thêm frontend URL vào `CORS_ORIGINS` trong backend env variables
- Hoặc kiểm tra CORS settings trong `backend/main.py`

