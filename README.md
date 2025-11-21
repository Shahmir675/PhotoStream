# PhotoStream - Cloud-Native Photo Sharing Platform

A scalable, cloud-native web application for sharing and interacting with photo-based content. Built with FastAPI, MongoDB Atlas, and Cloudinary.

## 🌟 Features

### Two User Roles

**Creators:**
- Upload photos with metadata (title, caption, location, people present)
- Manage their photo collection (view, update, delete)
- Dedicated creator dashboard

**Consumers:**
- Browse all photos with pagination
- Search photos by title, caption, or location
- View photo details
- Comment on photos
- Rate photos (1-5 stars)

### Technical Features
- ✅ RESTful API with FastAPI
- ✅ JWT-based authentication
- ✅ Role-based access control (RBAC)
- ✅ Cloud storage with Cloudinary CDN
- ✅ MongoDB Atlas for scalable database
- ✅ Automatic image optimization and thumbnails
- ✅ Full-text search functionality
- ✅ Pagination and filtering
- ✅ CI/CD pipeline with GitHub Actions
- ✅ Free deployment on Render.com

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
│  (Frontend) │
└──────┬──────┘
       │
       │ HTTPS/REST
       │
┌──────▼──────────────────────────┐
│   FastAPI Backend (Render.com)  │
│  - Authentication & Authorization│
│  - Business Logic                │
│  - API Endpoints                 │
└───┬─────────────────┬───────────┘
    │                 │
    │                 │
┌───▼────────┐   ┌───▼──────────┐
│  MongoDB   │   │  Cloudinary  │
│   Atlas    │   │   Storage    │
│ (Database) │   │   (Images)   │
└────────────┘   └──────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- MongoDB Atlas account (free tier)
- Cloudinary account (free tier)
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/PhotoStream.git
cd PhotoStream
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
DATABASE_NAME=photostream

SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

5. **Run the application**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

6. **Access API Documentation**
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## 📝 Setting Up Free Services

### MongoDB Atlas (FREE)

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free account
3. Create a new M0 (Free) cluster
4. Create a database user
5. Get your connection string
6. Add your IP to the whitelist (or allow from anywhere: 0.0.0.0/0)

### Cloudinary (FREE)

1. Go to [Cloudinary](https://cloudinary.com/)
2. Sign up for a free account
3. Get your Cloud Name, API Key, and API Secret from the dashboard
4. Free tier includes:
   - 25 GB storage
   - 25 GB bandwidth/month
   - Automatic image optimization

### Render.com Deployment (FREE)

1. Go to [Render.com](https://render.com/)
2. Create a free account
3. Connect your GitHub repository
4. Create a new Web Service
5. Select the repository
6. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
7. Add environment variables from your `.env` file
8. Deploy!

## 🔑 Creating Creator Accounts

There are two ways to create creator accounts:

### Option 1: API Endpoint (Recommended for Testing)

Upgrade an existing consumer account to creator via API:

```bash
# 1. Register as consumer
curl -X POST "http://localhost:8000/api/auth/register-consumer" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"user","password":"password123"}'

# 2. Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# 3. Upgrade to creator (using token from step 2)
curl -X POST "http://localhost:8000/api/auth/upgrade-to-creator" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. Login again to get new token with creator role
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

### Option 2: Database Script

Use the provided script to create a creator account directly:

```bash
python scripts/create_creator.py
```

Follow the prompts to create a creator account.

## 📚 API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register-consumer` | Register consumer user | No |
| POST | `/api/auth/login` | Login and get JWT token | No |
| GET | `/api/auth/me` | Get current user info | Yes |
| POST | `/api/auth/upgrade-to-creator` | Upgrade user to creator role | Yes |

### Creator Endpoints

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| POST | `/api/creator/photos` | Upload photo | Yes | Creator |
| GET | `/api/creator/photos` | Get my photos | Yes | Creator |
| PUT | `/api/creator/photos/{id}` | Update photo | Yes | Creator |
| DELETE | `/api/creator/photos/{id}` | Delete photo | Yes | Creator |

### Photo Endpoints

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/api/photos` | Get all photos (paginated) | Yes | Any |
| GET | `/api/photos/search` | Search photos | Yes | Any |
| GET | `/api/photos/{id}` | Get photo details | Yes | Any |

### Comment Endpoints

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| POST | `/api/photos/{id}/comments` | Add comment | Yes | Consumer |
| GET | `/api/photos/{id}/comments` | Get comments | Yes | Consumer |

### Rating Endpoints

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| POST | `/api/photos/{id}/ratings` | Rate photo | Yes | Consumer |
| GET | `/api/photos/{id}/ratings` | Get rating stats | Yes | Consumer |

## 🧪 Testing

Run tests with pytest:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=app --cov-report=html
```

## 🔐 Authentication Flow

1. **Register** (Consumer only via API)
```bash
curl -X POST "http://localhost:8000/api/auth/register-consumer" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"user","password":"password123"}'
```

2. **Login**
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

3. **Use token in requests**
```bash
curl -X GET "http://localhost:8000/api/photos" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 📷 Photo Upload Example

```bash
curl -X POST "http://localhost:8000/api/creator/photos" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@photo.jpg" \
  -F "title=Beautiful Sunset" \
  -F "caption=Amazing sunset at the beach" \
  -F "location=Malibu Beach" \
  -F 'people_present=["John", "Jane"]'
```

## 🌐 Deployment

### Deploy to Render.com

1. Push your code to GitHub
2. Connect repository to Render
3. Set environment variables
4. Deploy automatically via GitHub Actions

### CI/CD Pipeline

The project includes GitHub Actions workflow that:
- Runs tests on every push
- Automatically deploys to Render on main branch updates

## 📊 Database Schema

### Users Collection
```javascript
{
  "_id": ObjectId,
  "email": String,
  "username": String,
  "password_hash": String,
  "role": "creator" | "consumer",
  "created_at": DateTime,
  "updated_at": DateTime
}
```

### Photos Collection
```javascript
{
  "_id": ObjectId,
  "creator_id": String,
  "title": String,
  "caption": String,
  "location": String,
  "people_present": [String],
  "cloudinary_public_id": String,
  "cloudinary_url": String,
  "thumbnail_url": String,
  "upload_date": DateTime,
  "average_rating": Float,
  "total_ratings": Int,
  "metadata": {
    "width": Int,
    "height": Int,
    "format": String,
    "size": Int
  }
}
```

## 🛡️ Security Features

- Password hashing with bcrypt
- JWT token authentication
- Role-based access control
- CORS configuration
- File type validation
- File size limits (10MB max)
- Input validation with Pydantic

## 🚀 Performance & Scalability

- **MongoDB Indexing**: Optimized queries with proper indexes
- **Cloudinary CDN**: Fast image delivery worldwide
- **Pagination**: Efficient data loading
- **Async/Await**: Non-blocking I/O operations
- **Connection Pooling**: Efficient database connections
- **Image Optimization**: Automatic format conversion and compression

## 📦 Project Structure

```
PhotoStream/
├── app/
│   ├── models/          # Data models
│   ├── schemas/         # Pydantic schemas
│   ├── routes/          # API endpoints
│   ├── services/        # Business logic
│   ├── middleware/      # Auth middleware
│   ├── utils/           # Utilities
│   ├── config.py        # Configuration
│   ├── database.py      # DB connection
│   └── main.py          # FastAPI app
├── tests/               # Unit tests
├── scripts/             # Utility scripts
├── .github/workflows/   # CI/CD
├── requirements.txt     # Dependencies
├── .env.example         # Environment template
├── render.yaml          # Render config
└── README.md            # Documentation
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 👨‍💻 Developer

Created as part of COM769 - Scalable Advanced Software Solutions coursework.

## 🆘 Support

For issues and questions:
- Check the API documentation at `/api/docs`
- Review the code comments
- Open an issue on GitHub

## 🎯 Future Enhancements

- User profiles
- Photo albums/collections
- Advanced search filters
- Real-time notifications
- Social features (follow, like)
- Image editing capabilities
- Mobile app
- Analytics dashboard

---

**Built with ❤️ using FastAPI, MongoDB, and Cloudinary**