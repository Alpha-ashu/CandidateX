# CandidateX Backend

A comprehensive AI-powered mock interview and hiring platform backend built with FastAPI, MongoDB, and Redis.

## Features

- **Authentication & Authorization**: JWT-based auth with role-based access control
- **User Management**: Complete user lifecycle management with profiles and administration
- **Interview Management**: AI-powered interview creation, execution, and evaluation
- **Real-time Communication**: WebSocket support for live interviews and notifications
- **AI Integration**: Google Gemini/OpenAI integration for question generation and feedback
- **Dashboard & Analytics**: Comprehensive analytics for candidates, recruiters, and admins
- **Feedback System**: User feedback collection and management with ratings and categorization
- **Admin Panel**: System administration, monitoring, and configuration
- **Anti-cheat System**: Real-time monitoring and violation detection
- **Resume Processing**: ATS scoring and skills analysis
- **Cloud Storage**: AWS S3/Firebase integration for file uploads

## Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: MongoDB (with Motor async driver)
- **Cache**: Redis
- **AI Services**: Google Gemini AI / OpenAI
- **Authentication**: JWT tokens with bcrypt password hashing
- **Real-time**: WebSockets
- **File Storage**: AWS S3 / Firebase
- **Email**: SMTP integration
- **Deployment**: Docker, Gunicorn, Uvicorn

## Quick Start

### Prerequisites

- Python 3.9+
- MongoDB
- Redis
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backend
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
   # Edit .env with your configuration
   ```

5. **Start MongoDB and Redis**
   ```bash
   # Using Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   docker run -d -p 6379:6379 --name redis redis:latest
   ```

6. **Run the application**
   ```bash
   python -m app.main
   # or
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## Environment Configuration

### Required Environment Variables

```bash
# Application
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production

# Database
MONGODB_URL=mongodb://localhost:27017/candidatex

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# AI Services (at least one required)
GOOGLE_AI_API_KEY=your-google-ai-key
OPENAI_API_KEY=your-openai-key

# Email (optional)
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Optional Environment Variables

See `.env.example` for all available configuration options.

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh-token` - Refresh access token
- `POST /api/v1/auth/forgot-password` - Password reset request
- `POST /api/v1/auth/reset-password` - Reset password
- `GET /api/v1/auth/me` - Get current user profile

### Users
- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update user profile
- `GET /api/v1/users/users` - List users (Admin)
- `GET /api/v1/users/users/{user_id}` - Get user by ID (Admin)
- `PUT /api/v1/users/users/{user_id}` - Update user (Admin)
- `DELETE /api/v1/users/users/{user_id}` - Delete user (Admin)

### Interviews
- `POST /api/v1/interviews/` - Create interview
- `GET /api/v1/interviews/` - List user interviews
- `GET /api/v1/interviews/{interview_id}` - Get interview details
- `PUT /api/v1/interviews/{interview_id}` - Update interview
- `DELETE /api/v1/interviews/{interview_id}` - Delete interview
- `POST /api/v1/interviews/{interview_id}/start` - Start interview
- `POST /api/v1/interviews/{interview_id}/submit-response` - Submit response
- `POST /api/v1/interviews/{interview_id}/complete` - Complete interview

### Dashboard
- `GET /api/v1/dashboard/candidate/overview` - Candidate dashboard
- `GET /api/v1/dashboard/candidate/analytics` - Candidate analytics
- `GET /api/v1/dashboard/recruiter/overview` - Recruiter dashboard
- `GET /api/v1/dashboard/recruiter/analytics` - Recruiter analytics
- `GET /api/v1/dashboard/admin/overview` - Admin dashboard
- `GET /api/v1/dashboard/admin/analytics` - Admin analytics

### Feedback
- `POST /api/v1/feedback/` - Submit feedback
- `GET /api/v1/feedback/` - List feedback submissions
- `GET /api/v1/feedback/{feedback_id}` - Get feedback by ID
- `PUT /api/v1/feedback/{feedback_id}/status` - Update feedback status
- `DELETE /api/v1/feedback/{feedback_id}` - Delete feedback
- `GET /api/v1/feedback/stats/summary` - Get feedback statistics

### Administration
- `GET /api/v1/admin/system/health` - System health check
- `GET /api/v1/admin/system/metrics` - System metrics
- `GET /api/v1/admin/audit/logs` - Audit logs
- `POST /api/v1/admin/system/maintenance` - Trigger maintenance
- `GET /api/v1/admin/config` - Get system config
- `PUT /api/v1/admin/config/{config_key}` - Update config
- `GET /api/v1/admin/reports/user-activity` - User activity report
- `GET /api/v1/admin/reports/interview-performance` - Interview performance report

### WebSocket Endpoints
- `WS /api/v1/ws/interview/{interview_id}` - Interview real-time communication
- `WS /api/v1/ws/live-interview/{interview_id}` - Live interview sessions
- `WS /api/v1/ws/notifications` - Real-time notifications

## Database Schema

### Collections

- **users**: User accounts and profiles
- **interviews**: Interview sessions and responses
- **feedback**: User feedback submissions and management
- **anti_cheat_events**: Anti-cheat monitoring events
- **audit_logs**: System audit trail
- **live_interviews**: Live interview sessions
- **live_interview_feedback**: Live interview feedback

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
isort .
```

### Type Checking
```bash
mypy app/
```

### Linting
```bash
flake8 app/
```

## Deployment

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t candidatex-backend .
   ```

2. **Run with Docker Compose**
   ```yaml
   # docker-compose.yml
   version: '3.8'
   services:
     app:
       image: candidatex-backend
       ports:
         - "8000:8000"
       environment:
         - MONGODB_URL=mongodb://mongodb:27017/candidatex
         - REDIS_HOST=redis
       depends_on:
         - mongodb
         - redis

     mongodb:
       image: mongo:latest
       ports:
         - "27017:27017"

     redis:
       image: redis:latest
       ports:
         - "6379:6379"
   ```

### Production Deployment

Use Gunicorn with Uvicorn workers:

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Security

- JWT token authentication with secure storage
- Password hashing with bcrypt
- Role-based access control (RBAC)
- Input validation and sanitization
- CORS protection
- Rate limiting (configurable)
- Audit logging
- Anti-cheat monitoring

## Monitoring

- Health check endpoints
- System metrics collection
- Error tracking with Sentry (optional)
- Performance monitoring
- Database connection pooling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@candidatex.com or create an issue in the repository.
