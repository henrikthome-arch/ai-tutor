# AI Tutor - Render.com Deployment Guide

## Overview
This guide covers deploying the refactored AI Tutor system to Render.com using the new application factory pattern.

## Prerequisites
- Render.com account
- GitHub repository connected to Render
- PostgreSQL database on Render (or external)
- Redis instance for Celery (optional but recommended)

## Deployment Configuration

### 1. Web Service Configuration
```yaml
# render.yaml (if using Infrastructure as Code)
services:
  - type: web
    name: ai-tutor-web
    env: python
    buildCommand: "cd ai-tutor && pip install -r requirements.txt"
    startCommand: "cd ai-tutor/backend && gunicorn 'app:create_app()' --bind 0.0.0.0:$PORT --workers 2 --threads 2 --worker-class gevent"
    plan: starter
    envVars:
      - key: FLASK_ENV
        value: production
      - key: SECRET_KEY
        generateValue: true
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: ai-tutor-db
          property: connectionString
```

### 2. Environment Variables
Set these in Render Dashboard > Service > Environment:

**Required:**
- `FLASK_ENV=production`
- `SECRET_KEY` (auto-generated secure key)
- `JWT_SECRET_KEY` (auto-generated secure key)
- `DATABASE_URL` (PostgreSQL connection string)

**Optional:**
- `VAPI_API_KEY` (for voice API integration)
- `VAPI_SECRET` (for webhook verification)
- `OPENAI_API_KEY` (for AI features)
- `ANTHROPIC_API_KEY` (for AI features)
- `REDIS_URL` (for Celery background tasks)

### 3. Database Setup
1. Create PostgreSQL database in Render
2. Database will auto-initialize tables on first run
3. Run database reset if needed: `/admin/database/reset` (admin panel)

### 4. Build and Start Commands

**Build Command:**
```bash
cd ai-tutor && pip install -r requirements.txt
```

**Start Command:**
```bash
cd ai-tutor/backend && gunicorn 'app:create_app()' --bind 0.0.0.0:$PORT --workers 2 --threads 2 --worker-class gevent
```

### 5. File Structure
```
ai-tutor/
├── requirements.txt        # Python dependencies
├── Procfile               # Process definitions
├── backend/
│   ├── run.py            # Alternative entry point
│   ├── app/              # Application factory
│   │   ├── __init__.py   # create_app function
│   │   ├── config.py     # Configuration
│   │   ├── models/       # Database models
│   │   ├── services/     # Business logic
│   │   ├── main/         # Main blueprint (admin UI)
│   │   └── api/          # API blueprint
│   └── admin-server.py   # Legacy (archived)
└── data/                 # Student/curriculum data
```

## Deployment Steps

### 1. Connect Repository
1. Go to Render Dashboard
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select the ai-tutor repository

### 2. Configure Service
1. **Name:** `ai-tutor-web`
2. **Environment:** `Python 3`
3. **Build Command:** `cd ai-tutor && pip install -r requirements.txt`
4. **Start Command:** `cd ai-tutor/backend && gunicorn 'app:create_app()' --bind 0.0.0.0:$PORT --workers 2 --threads 2 --worker-class gevent`
5. **Plan:** Choose appropriate plan (Starter recommended for testing)

### 3. Environment Variables
Add all required environment variables in the Environment tab.

### 4. Database
1. Create PostgreSQL database if not exists
2. Copy DATABASE_URL to environment variables
3. Database tables will be created automatically

### 5. Deploy
Click "Create Web Service" - deployment will start automatically.

## Post-Deployment Verification

### 1. Health Check
Visit: `https://your-app.onrender.com/health`
Should return: `{"status": "healthy"}`

### 2. Admin Login
Visit: `https://your-app.onrender.com/admin/login`
- Default credentials in environment variables
- Should show login page

### 3. Dashboard Test
After login, check dashboard for:
- Total students count (should not be 0 if data exists)
- System statistics
- No error messages

### 4. API Test
Test API endpoint: `https://your-app.onrender.com/admin/api/stats`
Should return JSON with system statistics.

## Troubleshooting

### Common Issues

**1. "Total Students = 0" Bug**
- Check database connection in logs
- Verify DATABASE_URL is correct
- Run database reset if needed: `/admin/database/reset`

**2. Import Errors**
- Verify all dependencies in requirements.txt
- Check Python path in application factory

**3. Database Connection Issues**
- Verify PostgreSQL database is running
- Check DATABASE_URL format
- Ensure database allows connections

**4. Static Files Not Loading**
- Check template paths in blueprints
- Verify static file references

### Log Analysis
Check deployment logs in Render Dashboard:
1. Build logs for dependency issues
2. Runtime logs for application errors
3. Database logs for connection issues

## Performance Optimization

### 1. Database
- Add database indexes for frequently queried fields
- Use connection pooling (built into SQLAlchemy)
- Regular database maintenance

### 2. Application
- Use gevent workers for better concurrency
- Enable caching where appropriate
- Monitor memory usage

### 3. Monitoring
- Set up health checks
- Monitor response times
- Track error rates

## Security Notes

1. **Environment Variables:** Never commit secrets to repository
2. **HTTPS:** Render provides HTTPS by default
3. **Database:** Use strong passwords and restrict access
4. **Authentication:** Verify admin credentials are secure

## Support

For deployment issues:
1. Check Render documentation
2. Review application logs
3. Test locally with same configuration
4. Contact support if needed

## Migration from Legacy

The refactoring replaced the monolithic `admin-server.py` with:
- Application factory pattern (`app/__init__.py`)
- Modular blueprints (`app/main/`, `app/api/`)
- Service layer architecture (`app/services/`)
- Proper database models (`app/models/`)

The old `admin-server.py` has been archived and is no longer used.