# AI Tutor: Final Setup Guide

This comprehensive guide provides step-by-step instructions for setting up the AI Tutor system from scratch. It covers local development setup, database configuration, and deployment to Render.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Structure](#project-structure)
3. [Local Development Setup](#local-development-setup)
4. [Database Configuration](#database-configuration)
5. [Running the Application](#running-the-application)
6. [Deployment to Render](#deployment-to-render)
7. [Maintenance and Troubleshooting](#maintenance-and-troubleshooting)

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+**: Required for running the application
- **pip**: Python package manager
- **Git**: Version control system
- **PostgreSQL**: Database system (local installation for development)
- **Redis**: Message broker for Celery (optional, for background tasks)

### Installation Instructions

#### Python and pip

- **Windows**: Download and install from [python.org](https://www.python.org/downloads/)
- **macOS**: 
  ```bash
  brew install python
  ```
- **Linux**: 
  ```bash
  sudo apt update
  sudo apt install python3 python3-pip
  ```

#### Git

- **Windows**: Download and install from [git-scm.com](https://git-scm.com/download/win)
- **macOS**: 
  ```bash
  brew install git
  ```
- **Linux**: 
  ```bash
  sudo apt install git
  ```

#### PostgreSQL

- **Windows**: Download and install from [postgresql.org](https://www.postgresql.org/download/windows/)
- **macOS**: 
  ```bash
  brew install postgresql
  brew services start postgresql
  ```
- **Linux**: 
  ```bash
  sudo apt install postgresql postgresql-contrib
  sudo systemctl start postgresql
  sudo systemctl enable postgresql
  ```

#### Redis (Optional)

- **Windows**: Install using WSL2 or Docker
- **macOS**: 
  ```bash
  brew install redis
  brew services start redis
  ```
- **Linux**: 
  ```bash
  sudo apt install redis-server
  sudo systemctl start redis
  sudo systemctl enable redis
  ```

## Project Structure

The AI Tutor follows a modular, layered architecture:

```
ai-tutor/
├── app/                      # Main application package
│   ├── __init__.py           # Flask app factory
│   ├── config.py             # Configuration settings
│   ├── main/                 # Admin UI blueprint
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── api/                  # API blueprint
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── routes.py
│   ├── models/               # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── session.py
│   │   └── student.py
│   ├── repositories/         # Data access layer
│   │   ├── __init__.py
│   │   ├── base_repository.py
│   │   ├── user_repository.py
│   │   └── session_repository.py
│   ├── services/             # Business logic layer
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── session_service.py
│   │   └── ai_service.py
│   ├── ai/                   # AI provider abstraction
│   │   ├── __init__.py
│   │   ├── provider.py
│   │   ├── openai_provider.py
│   │   └── anthropic_provider.py
│   ├── static/               # Static assets
│   └── templates/            # Jinja2 templates
├── migrations/               # Alembic migrations
├── scripts/                  # Utility scripts
│   └── db_setup.py
├── data/                     # Application data
│   ├── curriculum/
│   └── students/
├── tests/                    # Test suite
├── run.py                    # Application entry point
├── celery_worker.py          # Celery worker entry point
├── Procfile                  # Render deployment configuration
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ai-tutor.git
cd ai-tutor
```

### 2. Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

Create a `.env` file in the project root:

```
# Flask
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/ai_tutor

# AI Providers
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Redis (optional)
REDIS_URL=redis://localhost:6379/0
```

## Database Configuration

### 1. Create PostgreSQL Database

```bash
# Log into PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE ai_tutor;
CREATE USER ai_tutor_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE ai_tutor TO ai_tutor_user;
\q
```

### 2. Initialize the Database

```bash
# Initialize migrations
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

### 3. Seed Initial Data (Optional)

```bash
python scripts/db_setup.py
```

## Running the Application

### 1. Start the Flask Application

```bash
# Development mode
flask run

# Or using the run.py script
python run.py
```

### 2. Start Celery Worker (Optional)

If you've implemented Celery for background tasks:

```bash
# Start Celery worker
celery -A celery_worker.celery worker --loglevel=info

# Start Flower monitoring (optional)
celery -A celery_worker.celery flower
```

### 3. Access the Application

- **Admin UI**: http://localhost:5000/admin
- **API**: http://localhost:5000/api/v1
- **Flower Dashboard** (if enabled): http://localhost:5555

## Deployment to Render

### 1. Create a Render Account

Sign up at [render.com](https://render.com) if you don't have an account.

### 2. Set Up PostgreSQL on Render

1. In your Render dashboard, go to **New** > **PostgreSQL**
2. Configure your database:
   - **Name**: ai-tutor-db
   - **Database**: ai_tutor
   - **User**: ai_tutor_user
   - **Region**: Choose the closest to your users
   - **Plan**: Select appropriate plan (Free for development)
3. Click **Create Database**
4. Note the connection details provided by Render

### 3. Set Up Redis on Render (Optional)

1. In your Render dashboard, go to **New** > **Redis**
2. Configure your Redis instance:
   - **Name**: ai-tutor-redis
   - **Region**: Choose the closest to your users
   - **Plan**: Select appropriate plan
3. Click **Create Redis**
4. Note the connection URL provided by Render

### 4. Deploy the Web Service

1. In your Render dashboard, go to **New** > **Web Service**
2. Connect your GitHub repository
3. Configure the web service:
   - **Name**: ai-tutor
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt && flask db upgrade`
   - **Start Command**: `gunicorn run:app`
   - **Plan**: Select appropriate plan
4. Add environment variables:
   - `SECRET_KEY`: Your secret key
   - `DATABASE_URL`: PostgreSQL connection URL from step 2
   - `REDIS_URL`: Redis connection URL from step 3 (if using Celery)
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `ANTHROPIC_API_KEY`: Your Anthropic API key
   - `FLASK_ENV`: production
5. Enable **Auto-Deploy** if desired
6. Click **Create Web Service**

### 5. Configure Persistent Disk (Optional)

For storing session data, curriculum files, etc.:

1. In your web service settings, go to **Disks**
2. Click **Add Disk**
3. Configure:
   - **Name**: ai-tutor-data
   - **Mount Path**: /app/data
   - **Size**: Choose appropriate size (e.g., 1 GB)
4. Click **Save**

## Maintenance and Troubleshooting

### Database Migrations

When you make changes to your models, create and apply migrations:

```bash
# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade

# Rollback migration (if needed)
flask db downgrade
```

### Logs

- **Local**: Check the terminal output
- **Render**: View logs in the Render dashboard for each service

### Common Issues

#### Database Connection Issues

- Verify connection string in environment variables
- Check if the database server is running
- Ensure firewall rules allow connections

#### Application Errors

- Check application logs for error messages
- Verify all required environment variables are set
- Ensure dependencies are installed correctly

#### Deployment Issues

- Check Render build logs for errors
- Verify Procfile configuration
- Ensure environment variables are set correctly in Render

### Backup and Restore

#### Database Backup

```bash
# Local backup
pg_dump -U username -d ai_tutor > backup.sql

# Render managed PostgreSQL
# Backups are automatic, but you can download them from the dashboard
```

#### Database Restore

```bash
# Local restore
psql -U username -d ai_tutor < backup.sql

# Render managed PostgreSQL
# Restore from the dashboard
```

## Next Steps

After completing the basic setup, consider implementing the following enhancements:

1. **Celery and Redis Integration**: For background task processing (see [NEXT_STEPS_GUIDE.md](NEXT_STEPS_GUIDE.md))
2. **Session Analytics Dashboard**: For monitoring and improving the AI Tutor (see [NEXT_STEPS_GUIDE.md](NEXT_STEPS_GUIDE.md))
3. **Authentication and Authorization**: Implement user roles and permissions
4. **API Documentation**: Add Swagger/OpenAPI documentation
5. **Automated Testing**: Expand test coverage for critical components

## Support and Resources

- **GitHub Repository**: [github.com/your-username/ai-tutor](https://github.com/your-username/ai-tutor)
- **Documentation**: Check the `docs/` directory for additional guides
- **Issues**: Report issues on the GitHub repository