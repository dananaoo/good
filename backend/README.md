# SmartBot 2.0 Backend

AI recruiter chatbot backend for conducting real-time interviews with candidates through a web widget.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+
- Redis

### Installation

1. **Clone and setup environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment configuration:**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and database credentials
   ```

3. **Start services with Docker:**
   ```bash
   docker-compose up -d db redis
   ```

4. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Start the application:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Alternative: Full Docker Setup

```bash
docker-compose up --build
```

## 📋 API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://smartbot_user:smartbot_password@localhost:5432/smartbot_db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `SECRET_KEY` | JWT secret key | **Change in production** |
| `GEMINI_API_KEY` | Google Gemini API key | Required for AI features |
| `OPENAI_API_KEY` | OpenAI API key | Optional |

### Database Schema

The application includes comprehensive models for:

- **Users & Authentication:** JWT-based auth with role-based access
- **Employers:** Company profiles and job postings
- **Candidates:** Personal profiles, skills, experience, education
- **Resumes:** File upload and text extraction
- **Vacancies:** Job postings with detailed requirements
- **Interviews:** Real-time chat sessions with AI evaluation
- **Evaluation:** Dynamic scoring across multiple categories

## 🧠 AI Features

### Interview Process

1. **Resume Fit Check:** Compare candidate profile with job requirements
2. **Hard Skills Assessment:** Technical competency evaluation
3. **Soft Skills & Motivation:** Communication and cultural fit

### Real-time WebSocket Communication

- Live chat between AI and candidates
- Dynamic score updates during interview
- Session management with Redis
- Automatic evaluation and reasoning generation

## 📊 HR Dashboard

HR endpoints provide:

- Interview analytics and statistics
- Candidate evaluation summaries
- Real-time interview monitoring
- Export capabilities for candidate data

## 🔐 Authentication

- JWT-based authentication
- Role-based access control (Admin, Employer, Candidate)
- Secure password hashing with bcrypt

## 🚀 Deployment

### Production Checklist

1. Set strong `SECRET_KEY`
2. Configure production database
3. Set up Redis cluster for session management
4. Configure AI API keys
5. Set up file storage for resumes
6. Configure CORS for production domains
7. Set up monitoring and logging

### Docker Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 📝 API Endpoints

### Authentication
- `POST /api/auth/register/employer` - Register employer
- `POST /api/auth/register/candidate` - Register candidate
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Candidates
- `POST /api/candidates/` - Create candidate profile
- `GET /api/candidates/me` - Get own profile
- `PUT /api/candidates/me` - Update profile
- `POST /api/candidates/me/experiences` - Add work experience
- `POST /api/candidates/me/skills` - Add skills

### Vacancies
- `POST /api/vacancies/` - Create vacancy
- `GET /api/vacancies/` - List vacancies (with filtering)
- `GET /api/vacancies/{id}` - Get vacancy details

### Resumes
- `POST /api/resumes/upload` - Upload resume file
- `GET /api/resumes/me` - Get own resumes

### Interviews
- `POST /api/interviews/` - Create interview
- `GET /api/interviews/` - List interviews
- `WebSocket /api/interviews/ws/{id}` - Real-time interview chat

### HR Dashboard
- `GET /api/hr/interviews` - HR interview list
- `GET /api/hr/interviews/{id}` - Interview details
- `GET /api/hr/interviews/{id}/messages` - Chat history
- `GET /api/hr/interviews/{id}/evaluation` - Evaluation summary
- `GET /api/hr/dashboard/stats` - Dashboard statistics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
