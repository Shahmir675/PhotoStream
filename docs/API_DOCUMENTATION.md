# PhotoStream API Documentation

## Base URL
```
Production: https://your-app.onrender.com
Development: http://localhost:8000
```

## Authentication

All endpoints except registration and login require a JWT token in the Authorization header:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## 🔐 Authentication Endpoints

### Register Consumer

Create a new consumer account.

**Endpoint:** `POST /api/auth/register-consumer`

**Request Body:**
```json
{
  "email": "consumer@example.com",
  "username": "consumer1",
  "password": "securepassword123"
}
```

**Response:** `201 Created`
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "email": "consumer@example.com",
  "username": "consumer1",
  "role": "consumer",
  "created_at": "2024-01-15T10:30:00"
}
```

**Errors:**
- `400`: Email already registered
- `400`: Username already taken
- `422`: Validation error

---

### Login

Authenticate and receive JWT token.

**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
  "email": "consumer@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:**
- `401`: Incorrect email or password

---

### Get Current User

Get authenticated user information.

**Endpoint:** `GET /api/auth/me`

**Headers:** `Authorization: Bearer TOKEN`

**Response:** `200 OK`
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "email": "consumer@example.com",
  "username": "consumer1",
  "role": "consumer",
  "created_at": "2024-01-15T10:30:00"
}
```

**Errors:**
- `401`: Invalid or expired token

---

## 📸 Creator Endpoints

### Upload Photo

Upload a new photo with metadata. **Creator role only.**

**Endpoint:** `POST /api/creator/photos`

**Headers:**
- `Authorization: Bearer TOKEN`
- `Content-Type: multipart/form-data`

**Form Data:**
- `file` (required): Image file (JPEG, PNG, JPG, WebP)
- `title` (required): Photo title
- `caption` (optional): Photo description
- `location` (optional): Photo location
- `people_present` (optional): JSON array of names

**Example Request (cURL):**
```bash
curl -X POST "http://localhost:8000/api/creator/photos" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/photo.jpg" \
  -F "title=Beautiful Sunset" \
  -F "caption=Amazing view from the beach" \
  -F "location=California Beach" \
  -F 'people_present=["Alice", "Bob"]'
```

**Response:** `201 Created`
```json
{
  "_id": "507f1f77bcf86cd799439012",
  "creator_id": "507f1f77bcf86cd799439011",
  "title": "Beautiful Sunset",
  "caption": "Amazing view from the beach",
  "location": "California Beach",
  "people_present": ["Alice", "Bob"],
  "cloudinary_url": "https://res.cloudinary.com/...",
  "thumbnail_url": "https://res.cloudinary.com/.../w_300,h_300...",
  "upload_date": "2024-01-15T14:30:00",
  "average_rating": 0.0,
  "total_ratings": 0
}
```

**Errors:**
- `400`: Invalid file type
- `400`: File too large (>10MB)
- `403`: Not authorized (not a creator)

---

### Get My Photos

Get all photos uploaded by the authenticated creator.

**Endpoint:** `GET /api/creator/photos`

**Headers:** `Authorization: Bearer TOKEN`

**Response:** `200 OK`
```json
[
  {
    "_id": "507f1f77bcf86cd799439012",
    "creator_id": "507f1f77bcf86cd799439011",
    "title": "Beautiful Sunset",
    "cloudinary_url": "https://res.cloudinary.com/...",
    "upload_date": "2024-01-15T14:30:00",
    "average_rating": 4.5,
    "total_ratings": 10
  }
]
```

---

### Update Photo

Update photo metadata. **Creator role only, own photos only.**

**Endpoint:** `PUT /api/creator/photos/{photo_id}`

**Headers:** `Authorization: Bearer TOKEN`

**Request Body:**
```json
{
  "title": "Updated Title",
  "caption": "Updated caption",
  "location": "New Location",
  "people_present": ["Updated", "Names"]
}
```

**Response:** `200 OK`
```json
{
  "_id": "507f1f77bcf86cd799439012",
  "title": "Updated Title",
  "caption": "Updated caption",
  ...
}
```

**Errors:**
- `404`: Photo not found
- `403`: Not authorized to update this photo

---

### Delete Photo

Delete a photo. **Creator role only, own photos only.**

**Endpoint:** `DELETE /api/creator/photos/{photo_id}`

**Headers:** `Authorization: Bearer TOKEN`

**Response:** `204 No Content`

**Errors:**
- `404`: Photo not found
- `403`: Not authorized to delete this photo

---

## 🖼️ Photo Endpoints

### Get All Photos

Get paginated list of all photos.

**Endpoint:** `GET /api/photos`

**Headers:** `Authorization: Bearer TOKEN`

**Query Parameters:**
- `page` (default: 1): Page number
- `page_size` (default: 20, max: 100): Items per page
- `search` (optional): Search in title and caption
- `location` (optional): Filter by location

**Example Request:**
```
GET /api/photos?page=1&page_size=20&search=sunset&location=beach
```

**Response:** `200 OK`
```json
{
  "photos": [
    {
      "_id": "507f1f77bcf86cd799439012",
      "title": "Beautiful Sunset",
      "cloudinary_url": "https://res.cloudinary.com/...",
      "average_rating": 4.5,
      "total_ratings": 10
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

---

### Search Photos

Search photos by title, caption, or location.

**Endpoint:** `GET /api/photos/search`

**Headers:** `Authorization: Bearer TOKEN`

**Query Parameters:**
- `q`: Search query
- `location`: Location filter
- `page`: Page number
- `page_size`: Items per page

**Example:**
```
GET /api/photos/search?q=sunset&location=california&page=1
```

---

### Get Photo Details

Get detailed information about a specific photo.

**Endpoint:** `GET /api/photos/{photo_id}`

**Headers:** `Authorization: Bearer TOKEN`

**Response:** `200 OK`
```json
{
  "_id": "507f1f77bcf86cd799439012",
  "creator_id": "507f1f77bcf86cd799439011",
  "title": "Beautiful Sunset",
  "caption": "Amazing view",
  "location": "California Beach",
  "people_present": ["Alice", "Bob"],
  "cloudinary_url": "https://res.cloudinary.com/...",
  "thumbnail_url": "https://res.cloudinary.com/...",
  "upload_date": "2024-01-15T14:30:00",
  "average_rating": 4.5,
  "total_ratings": 10
}
```

---

## 💬 Comment Endpoints

### Add Comment

Add a comment to a photo. **Consumer role only.**

**Endpoint:** `POST /api/photos/{photo_id}/comments`

**Headers:** `Authorization: Bearer TOKEN`

**Request Body:**
```json
{
  "content": "Beautiful photo! Love the colors."
}
```

**Response:** `201 Created`
```json
{
  "_id": "507f1f77bcf86cd799439013",
  "photo_id": "507f1f77bcf86cd799439012",
  "user_id": "507f1f77bcf86cd799439011",
  "username": "consumer1",
  "content": "Beautiful photo! Love the colors.",
  "created_at": "2024-01-15T15:00:00",
  "updated_at": "2024-01-15T15:00:00"
}
```

**Errors:**
- `404`: Photo not found
- `403`: Not authorized (not a consumer)
- `400`: Content too long (>500 chars)

---

### Get Photo Comments

Get all comments for a photo. **Consumer role only.**

**Endpoint:** `GET /api/photos/{photo_id}/comments`

**Headers:** `Authorization: Bearer TOKEN`

**Response:** `200 OK`
```json
{
  "comments": [
    {
      "_id": "507f1f77bcf86cd799439013",
      "username": "consumer1",
      "content": "Beautiful photo!",
      "created_at": "2024-01-15T15:00:00"
    }
  ],
  "total": 1
}
```

---

## ⭐ Rating Endpoints

### Rate Photo

Rate a photo (1-5 stars). **Consumer role only.**

**Endpoint:** `POST /api/photos/{photo_id}/ratings`

**Headers:** `Authorization: Bearer TOKEN`

**Request Body:**
```json
{
  "rating": 5
}
```

**Response:** `201 Created`
```json
{
  "_id": "507f1f77bcf86cd799439014",
  "photo_id": "507f1f77bcf86cd799439012",
  "user_id": "507f1f77bcf86cd799439011",
  "rating": 5
}
```

**Notes:**
- If user already rated this photo, the rating will be updated
- Rating must be between 1 and 5

**Errors:**
- `404`: Photo not found
- `403`: Not authorized (not a consumer)
- `400`: Invalid rating value

---

### Get Photo Ratings

Get rating statistics for a photo. **Consumer role only.**

**Endpoint:** `GET /api/photos/{photo_id}/ratings`

**Headers:** `Authorization: Bearer TOKEN`

**Response:** `200 OK`
```json
{
  "average_rating": 4.2,
  "total_ratings": 25,
  "rating_distribution": {
    "1": 2,
    "2": 1,
    "3": 5,
    "4": 7,
    "5": 10
  }
}
```

---

## 🏥 Health Check

### Root Health Check

**Endpoint:** `GET /`

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "message": "Welcome to PhotoStream API",
  "version": "1.0.0"
}
```

### Detailed Health Check

**Endpoint:** `GET /api/health`

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "database": "connected",
  "api_version": "1.0.0"
}
```

---

## 📋 Common Error Responses

### 400 Bad Request
```json
{
  "detail": "Error message describing what went wrong"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Only creators can access this resource"
}
```

### 404 Not Found
```json
{
  "detail": "Photo not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## 🔍 Testing with cURL

### Complete Workflow Example

1. **Register Consumer:**
```bash
curl -X POST http://localhost:8000/api/auth/register-consumer \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"password123"}'
```

2. **Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

3. **Get Photos (using token):**
```bash
curl -X GET http://localhost:8000/api/photos \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

4. **Rate a Photo:**
```bash
curl -X POST http://localhost:8000/api/photos/PHOTO_ID/ratings \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"rating": 5}'
```

---

## 📱 Rate Limits

Currently, there are no rate limits implemented, but they can be added using middleware for production use.

---

## 🔒 Security Best Practices

1. Always use HTTPS in production
2. Store tokens securely (never in localStorage for sensitive apps)
3. Implement token refresh mechanism for long-lived sessions
4. Validate file uploads on client side before sending
5. Use environment variables for sensitive configuration

---

For interactive API documentation, visit:
- **Swagger UI:** `/api/docs`
- **ReDoc:** `/api/redoc`
