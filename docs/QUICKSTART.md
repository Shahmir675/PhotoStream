# PhotoStream - Quick Start Guide

Get PhotoStream running locally in 5 minutes!

## 🚀 Quick Start

### 1. Clone & Install (2 min)

```bash
# Clone repository
git clone https://github.com/yourusername/PhotoStream.git
cd PhotoStream

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Free Services (3 min)

#### MongoDB Atlas (FREE - 512MB)
1. Go to: https://www.mongodb.com/cloud/atlas/register
2. Create M0 FREE cluster
3. Create database user
4. Allow access from anywhere (0.0.0.0/0)
5. Copy connection string

#### Cloudinary (FREE - 25GB)
1. Go to: https://cloudinary.com/users/register/free
2. Sign up
3. Copy: Cloud Name, API Key, API Secret

### 3. Configure Environment (1 min)

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your favorite editor
```

Required variables:
```env
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/
DATABASE_NAME=photostream
SECRET_KEY=your-secret-key-here
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

### 4. Run! (30 seconds)

```bash
uvicorn app.main:app --reload
```

✅ API running at: http://localhost:8000
✅ Docs at: http://localhost:8000/api/docs

## 🧪 Test It!

### Register a Consumer

```bash
curl -X POST http://localhost:8000/api/auth/register-consumer \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123"
  }'
```

### Login & Get Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### Create a Creator Account

**Option 1: Upgrade via API (Easiest)**
```bash
# First, login with your consumer account to get a token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' \
  | jq -r '.access_token')

# Upgrade to creator
curl -X POST http://localhost:8000/api/auth/upgrade-to-creator \
  -H "Authorization: Bearer $TOKEN"

# Login again to get new token with creator role
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

**Option 2: Use Script**
```bash
python scripts/create_creator.py
```

## 📚 What's Next?

- Read [README.md](README.md) for full documentation
- Check [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for API details
- Follow [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) to deploy
- Explore API at http://localhost:8000/api/docs

## 🆘 Common Issues

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "Connection refused" to MongoDB
- Check MONGODB_URL in .env
- Verify IP whitelist in MongoDB Atlas (0.0.0.0/0)
- Test connection: `python -c "from pymongo import MongoClient; client = MongoClient('YOUR_URL'); print('OK!')"`

### "Invalid credentials" for Cloudinary
- Double-check Cloud Name, API Key, and API Secret
- No spaces or quotes in .env file values

## 💡 Pro Tips

1. Use Swagger UI for testing: http://localhost:8000/api/docs
2. Check logs in terminal for debugging
3. MongoDB Atlas has built-in data explorer
4. Cloudinary dashboard shows uploaded images

---

**That's it! You're ready to build! 🎉**
