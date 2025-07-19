# AI Tutor: Quick Setup Instructions

This guide provides concise instructions for setting up the AI Tutor system. For a more comprehensive guide, see [FINAL_SETUP_GUIDE.md](FINAL_SETUP_GUIDE.md).

## Local Development Setup

### Prerequisites

- Python 3.9+
- PostgreSQL
- Git
- Redis (optional, for background tasks)

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/ai-tutor.git
cd ai-tutor
```

### Step 2: Set Up Python Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://username:password@localhost:5432/ai_tutor
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### Step 4: Set Up Database

```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE ai_tutor;
CREATE USER ai_tutor_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE ai_tutor TO ai_tutor_user;
\q

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Step 5: Run the Application

```bash
# Start the Flask application
flask run
```

Access the application at http://localhost:5000

## Deployment to Render

### Step 1: Create Render Services

1. **PostgreSQL Database**:
   - Create a new PostgreSQL service in Render
   - Note the connection URL

2. **Web Service**:
   - Connect your GitHub repository
   - Build Command: `pip install -r requirements.txt && flask db upgrade`
   - Start Command: `gunicorn run:app`
   - Add environment variables (DATABASE_URL, SECRET_KEY, etc.)

### Step 2: Configure Environment Variables

Set the following environment variables in your Render web service:

- `SECRET_KEY`: Your secret key
- `DATABASE_URL`: PostgreSQL connection URL
- `OPENAI_API_KEY`: Your OpenAI API key
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `FLASK_ENV`: production

### Step 3: Deploy

Click "Create Web Service" and wait for the deployment to complete.

## Next Steps

For advanced features and enhancements, see:
- [NEXT_STEPS_GUIDE.md](NEXT_STEPS_GUIDE.md) - Celery integration and analytics dashboard
- [FINAL_SETUP_GUIDE.md](FINAL_SETUP_GUIDE.md) - Comprehensive setup and maintenance guide