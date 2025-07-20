# 🗄️ Database Configuration Guide

## 🚨 Critical Issue: SQLite vs PostgreSQL in Production

If you're seeing this error:
```
Error getting sessions from database: (sqlite3.OperationalError) no such table: sessions
```

This means your application is trying to use SQLite instead of PostgreSQL in production, which will cause data loss and functionality issues.

## 🔍 Root Cause

The application is falling back to SQLite because:

1. The `DATABASE_URL` environment variable is either:
   - Not set at all in your Render.com environment
   - Set to the placeholder value from render-production.env
   - Not properly formatted for SQLAlchemy

## ✅ Solution: Properly Configure DATABASE_URL

### Step 1: Create PostgreSQL Database on Render.com

1. In your Render dashboard, click "New +" → "PostgreSQL"
2. Configure database:
   ```
   Name: ai-tutor-db
   Database: ai_tutor
   User: (leave default)
   Region: Oregon (US West) or Frankfurt (Europe)
   PostgreSQL Version: 14
   Plan Type: Free
   ```
3. Click "Create Database"
4. Wait for creation (2-3 minutes)
5. **Copy the Internal Database URL** (you'll need this for your web service)
6. **Important**: Change `postgres://` to `postgresql://` in the URL for SQLAlchemy compatibility

### Step 2: Set DATABASE_URL in Render.com Environment

1. Go to your web service in the Render dashboard
2. Click on "Environment" in the left sidebar
3. Find the `DATABASE_URL` variable
4. If it exists with a placeholder value, click "Edit" and replace it with your actual Internal Database URL
5. If it doesn't exist, click "Add Environment Variable" and add:
   - Key: `DATABASE_URL`
   - Value: Your Internal Database URL (with `postgresql://`)
6. Click "Save Changes"
7. Redeploy your application by clicking "Manual Deploy" → "Deploy latest commit"

### Step 3: Verify Database Connection

1. After deployment, check your application logs in the Render dashboard
2. Look for this message: `🗄️ Using database URL from environment: postgresql...`
3. If you see `⚠️ DATABASE_URL environment variable not found. Using default SQLite database.`, the environment variable is not set correctly

## 🔄 Testing Database Connection

You can verify your database connection by visiting:
```
https://your-app-name.onrender.com/health
```

This endpoint will return database connection status information.

## 📝 Important Notes

1. **Never use SQLite in production** - it's only for local development
2. The DATABASE_URL in render-production.env is just a placeholder and must be replaced with your actual database URL
3. Always ensure the URL starts with `postgresql://` (not `postgres://`)
4. If you change database credentials, you must update the DATABASE_URL environment variable

## 🛠️ Database Migrations

The application now uses Flask-Migrate to manage database schema changes. When the application starts, it will:

1. Check if you're using SQLite (development) or PostgreSQL (production)
2. For PostgreSQL, it will attempt to run database migrations
3. If migrations directory doesn't exist, it will create initial migrations
4. If migrations fail, it will fall back to `db.create_all()`

### Common Migration Errors

If you see errors like:
```
relation "system_logs" does not exist
```

This means the database tables haven't been created yet. The application should automatically handle this on startup, but if it doesn't:

1. Check the application logs for migration errors
2. Verify that Flask-Migrate is installed (`pip install Flask-Migrate`)
3. If needed, manually run migrations:
   ```
   cd ai-tutor
   export FLASK_APP=backend/admin-server.py
   flask db init     # Only if migrations directory doesn't exist
   flask db migrate  # Create migration
   flask db upgrade  # Apply migration
   ```

## 🛠️ Troubleshooting

If you continue to have database connection issues:

1. Verify the PostgreSQL database is running in the Render dashboard
2. Check that the DATABASE_URL environment variable is set correctly
3. Ensure you changed `postgres://` to `postgresql://` in the URL
4. Try creating a new database and updating the DATABASE_URL
5. Check the application logs for specific error messages
6. Verify that database migrations have run successfully
7. If all else fails, you can try manually creating the tables using the SQL schema