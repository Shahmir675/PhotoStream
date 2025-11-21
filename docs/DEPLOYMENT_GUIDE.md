# PhotoStream Deployment Guide

Complete step-by-step guide to deploy PhotoStream backend to free cloud services.

## 📋 Prerequisites

- [ ] GitHub account
- [ ] MongoDB Atlas account (free)
- [ ] Cloudinary account (free)
- [ ] Render.com account (free)
- [ ] Git installed locally
- [ ] Python 3.11+ installed

---

## 🗄️ Step 1: Setup MongoDB Atlas (FREE)

### 1.1 Create Account & Cluster

1. Visit [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Sign up for a free account
3. Create a new project (e.g., "PhotoStream")
4. Click "Build a Database"
5. Choose **M0 FREE** tier
6. Select a cloud provider and region (closest to you)
7. Name your cluster (e.g., "photostream-cluster")
8. Click "Create"

### 1.2 Create Database User

1. Go to "Database Access" in left sidebar
2. Click "Add New Database User"
3. Choose "Password" authentication
4. Username: `photostream_user` (or your choice)
5. Auto-generate secure password (save it!)
6. Database User Privileges: "Atlas admin"
7. Click "Add User"

### 1.3 Configure Network Access

1. Go to "Network Access" in left sidebar
2. Click "Add IP Address"
3. Click "Allow Access from Anywhere" (for development)
4. Or add `0.0.0.0/0` manually
5. Click "Confirm"

### 1.4 Get Connection String

1. Go to "Database" in left sidebar
2. Click "Connect" on your cluster
3. Choose "Connect your application"
4. Driver: Python, Version: 3.6 or later
5. Copy the connection string:
```
mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority
```
6. Replace `<username>` and `<password>` with your credentials
7. Save this connection string for later

---

## ☁️ Step 2: Setup Cloudinary (FREE)

### 2.1 Create Account

1. Visit [Cloudinary](https://cloudinary.com/users/register/free)
2. Sign up for a free account
3. Verify your email

### 2.2 Get API Credentials

1. Go to Dashboard
2. Copy the following from the "Account Details" section:
   - **Cloud Name**
   - **API Key**
   - **API Secret**
3. Save these credentials

### 2.3 Verify Free Tier Limits

Free tier includes:
- ✅ 25 GB storage
- ✅ 25 GB bandwidth/month
- ✅ 25,000 transformations/month
- ✅ Image optimization
- ✅ CDN delivery

---

## 🚀 Step 3: Deploy to Render.com (FREE)

### 3.1 Prepare Your Code

1. Ensure all code is committed to GitHub:
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

2. Make sure these files exist in your repo:
   - `requirements.txt`
   - `render.yaml`
   - `Procfile`
   - `runtime.txt`

### 3.2 Create Render Account

1. Visit [Render.com](https://render.com/)
2. Sign up with GitHub (recommended)
3. Authorize Render to access your repositories

### 3.3 Create Web Service

1. Click "New +" button
2. Select "Web Service"
3. Connect your PhotoStream repository
4. Configure the service:

**Basic Settings:**
- Name: `photostream-api`
- Region: Choose closest to you
- Branch: `main`
- Root Directory: Leave empty
- Runtime: `Python 3`

**Build Settings:**
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Plan:**
- Select: **Free** (0$/month)

### 3.4 Add Environment Variables

Click "Advanced" and add these environment variables:

| Key | Value | Notes |
|-----|-------|-------|
| `MONGODB_URL` | `mongodb+srv://user:pass@cluster...` | From MongoDB Atlas |
| `DATABASE_NAME` | `photostream` | Database name |
| `SECRET_KEY` | Click "Generate" | For JWT tokens |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | 24 hours |
| `CLOUDINARY_CLOUD_NAME` | Your cloud name | From Cloudinary |
| `CLOUDINARY_API_KEY` | Your API key | From Cloudinary |
| `CLOUDINARY_API_SECRET` | Your API secret | From Cloudinary |
| `MAX_UPLOAD_SIZE` | `10485760` | 10MB |
| `ALLOWED_IMAGE_TYPES` | `image/jpeg,image/png,image/jpg,image/webp` | Allowed types |

### 3.5 Deploy

1. Click "Create Web Service"
2. Wait for deployment (5-10 minutes)
3. Your API will be live at: `https://photostream-api.onrender.com`

### 3.6 Verify Deployment

1. Visit: `https://your-app.onrender.com/`
2. You should see:
```json
{
  "status": "healthy",
  "message": "Welcome to PhotoStream API",
  "version": "1.0.0"
}
```

3. Check API docs: `https://your-app.onrender.com/api/docs`

---

## 🔄 Step 4: Setup CI/CD with GitHub Actions

### 4.1 Get Render API Key

1. Go to Render Dashboard
2. Click on your account (top right)
3. Select "Account Settings"
4. Scroll to "API Keys"
5. Create new API key
6. Copy the key (you won't see it again!)

### 4.2 Get Render Service ID

1. Go to your web service dashboard
2. Copy the Service ID from the URL:
```
https://dashboard.render.com/web/srv-XXXXXXXXXXXXX
                                   ^^^^^^^^^^^^^^^^
                                   This is your Service ID
```

### 4.3 Add GitHub Secrets

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add these secrets:

| Name | Value |
|------|-------|
| `MONGODB_URL` | Your MongoDB connection string |
| `RENDER_API_KEY` | Your Render API key |
| `RENDER_SERVICE_ID` | Your Render service ID |

### 4.4 Verify CI/CD

1. Make a small change to your code
2. Commit and push to main branch:
```bash
git add .
git commit -m "Test CI/CD"
git push origin main
```
3. Go to GitHub → Actions tab
4. Watch the workflow run
5. If successful, changes will be deployed automatically!

---

## 👤 Step 5: Create Creator Account

There are multiple ways to create creator accounts:

### 5.1 Via API (Easiest for Testing)

First, register and login as a consumer, then upgrade:

```bash
# Register consumer
curl -X POST "https://your-app.onrender.com/api/auth/register-consumer" \
  -H "Content-Type: application/json" \
  -d '{"email":"creator@example.com","username":"creator1","password":"securepass123"}'

# Login
curl -X POST "https://your-app.onrender.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"creator@example.com","password":"securepass123"}'

# Copy the access_token from the response, then upgrade
curl -X POST "https://your-app.onrender.com/api/auth/upgrade-to-creator" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Login again to get a new token with creator role
curl -X POST "https://your-app.onrender.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"creator@example.com","password":"securepass123"}'
```

### 5.2 Using Script Locally

```bash
python scripts/create_creator.py
```

### 5.3 On Render (using Shell)

1. Go to your Render service dashboard
2. Click "Shell" tab
3. Run:
```bash
python scripts/create_creator.py
```

Enter the creator credentials when prompted.

---

## 🧪 Step 6: Test Your Deployment

### 6.1 Register a Consumer

```bash
curl -X POST "https://your-app.onrender.com/api/auth/register-consumer" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "securepassword123"
  }'
```

### 6.2 Login

```bash
curl -X POST "https://your-app.onrender.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

Copy the `access_token` from the response.

### 6.3 Access Protected Endpoint

```bash
curl -X GET "https://your-app.onrender.com/api/photos?page=1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 📊 Monitoring & Logs

### Render Logs

1. Go to your service dashboard
2. Click "Logs" tab
3. View real-time logs

### MongoDB Monitoring

1. Go to MongoDB Atlas
2. Select your cluster
3. View metrics, logs, and queries

### Cloudinary Usage

1. Go to Cloudinary Dashboard
2. View storage and bandwidth usage

---

## 🔧 Troubleshooting

### Issue: Service won't start

**Check:**
- All environment variables are set correctly
- MongoDB connection string is valid
- MongoDB IP whitelist includes 0.0.0.0/0

**Solution:**
```bash
# Test MongoDB connection locally
python -c "from pymongo import MongoClient; client = MongoClient('YOUR_MONGODB_URL'); print('Connected!')"
```

### Issue: 500 errors when uploading photos

**Check:**
- Cloudinary credentials are correct
- File size is under 10MB
- File type is allowed

**Solution:**
- Check Render logs for detailed error messages
- Verify Cloudinary credentials in dashboard

### Issue: Free service sleeping

**Note:** Render free tier services sleep after 15 minutes of inactivity.

**Solutions:**
- First request after sleep takes ~30 seconds (cold start)
- Upgrade to paid plan for 24/7 uptime
- Use uptime monitoring services (ping every 14 minutes)

### Issue: Database connection timeout

**Check:**
- MongoDB Atlas IP whitelist
- Connection string format
- Database user permissions

---

## 💰 Cost Breakdown (FREE)

| Service | Free Tier | Cost |
|---------|-----------|------|
| **MongoDB Atlas** | 512MB storage | $0/month |
| **Cloudinary** | 25GB storage, 25GB bandwidth | $0/month |
| **Render.com** | 750 hours/month, 512MB RAM | $0/month |
| **GitHub Actions** | 2000 minutes/month | $0/month |
| **Total** | | **$0/month** |

---

## 🎯 Production Checklist

Before going to production:

- [ ] Change SECRET_KEY to a strong random value
- [ ] Enable HTTPS (Render provides this automatically)
- [ ] Set up custom domain (optional)
- [ ] Configure proper CORS origins
- [ ] Set up monitoring/alerts
- [ ] Configure MongoDB backup
- [ ] Review and adjust file upload limits
- [ ] Add rate limiting (production consideration)
- [ ] Set up error tracking (e.g., Sentry)
- [ ] Document API endpoints
- [ ] Create user documentation

---

## 🚀 Next Steps

1. Connect frontend application
2. Test all endpoints thoroughly
3. Add more features:
   - User profiles
   - Photo albums
   - Advanced search
   - Real-time notifications

---

## 📞 Support

If you encounter issues:

1. Check Render logs
2. Check MongoDB Atlas metrics
3. Review API documentation: `/api/docs`
4. Check GitHub Issues

---

**Congratulations! Your PhotoStream backend is now deployed and running on 100% free services! 🎉**
