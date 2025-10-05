# Photo Proof API

A comprehensive FastAPI backend for the professional photo proofing gallery system.

## Features

- **RESTful API** with comprehensive endpoints for projects, images, categories, and comments
- **JSON-based data storage** for easy migration to DynamoDB
- **Mock data generation** with 100-250+ realistic images for performance testing
- **CORS support** for frontend integration
- **Automatic API documentation** with Swagger UI
- **Scalable data models** designed for real-world usage

## Quick Start

1. **Start the API server:**

   ```bash
   ./start.sh
   ```

2. **Access the API:**
   - API Base URL: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc

## Data Structure

The API uses a hierarchical data structure designed for easy DynamoDB migration:

```
Studio → Projects → Categories → Images → Versions
                              → Comments
```

### Key Entities

- **Studios**: Photography studios with settings and branding
- **Users**: Studio photographers and clients with role-based access
- **Projects**: Individual photo sessions (weddings, engagements, etc.)
- **Categories**: Image organization within projects (Candid, Portrait, Traditional, etc.)
- **Images**: Photos with metadata, versions, and client interactions
- **Comments**: Client feedback on individual images

## API Endpoints

### Projects

- `GET /api/projects` - List projects with filtering
- `GET /api/projects/{id}` - Get project details
- `GET /api/projects/access/{access_url}` - Client access by URL
- `POST /api/projects` - Create new project

### Categories

- `GET /api/projects/{id}/categories` - List project categories
- `POST /api/projects/{id}/categories` - Add new category

### Images

- `GET /api/projects/{id}/images` - List images with pagination
- `GET /api/projects/{id}/images/{image_id}` - Get image details
- `PATCH /api/projects/{id}/images/{image_id}` - Update image (select/favorite)

### Comments

- `GET /api/projects/{id}/images/{image_id}/comments` - List image comments
- `POST /api/projects/{id}/images/{image_id}/comments` - Add comment

### Statistics

- `GET /api/projects/{id}/stats` - Project statistics and breakdowns

## Mock Data

The system generates realistic mock data including:

- **3 projects** with different themes (wedding, engagement, family)
- **330+ total images** across multiple categories
- **5 users** (studio photographers and clients)
- **2 studios** with different settings
- **Random comments** on images for testing

### Project Breakdown:

- **Sarah & Michael Wedding**: 150 images (5 categories × 30 images)
- **Emma & David Engagement**: 75 images (3 categories × 25 images)
- **Henderson Family Portraits**: 105 images (3 categories × 35 images)

## Data Storage

All data is stored in JSON files in the `data/` directory:

- `users.json` - User accounts and authentication
- `studios.json` - Studio information and settings
- `projects.json` - Projects with all images and categories
- `comments.json` - Image comments and replies

### DynamoDB Migration Ready

The JSON structure directly maps to DynamoDB tables:

- Composite keys for efficient queries
- Denormalized data for performance
- Hierarchical relationships preserved

## Development

### Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Generate mock data
python generate_mock_data.py

# Start server
uvicorn main:app --reload
```

### Environment Configuration

- **CORS**: Configured for localhost:3000 and localhost:5173
- **Host**: 0.0.0.0 (accessible from network)
- **Port**: 8000 (configurable)

## Performance Considerations

- **Pagination**: Images API supports limit/offset for large datasets
- **Filtering**: Category-based filtering for efficient queries
- **Lazy Loading**: Supports frontend virtual scrolling implementations
- **Memory Management**: JSON files kept lightweight with external image URLs

## Future Enhancements

- **Authentication**: JWT-based authentication system
- **File Upload**: Image upload and processing endpoints
- **Real Database**: Easy migration to PostgreSQL or DynamoDB
- **Caching**: Redis integration for improved performance
- **Image Processing**: Thumbnail generation and optimization
