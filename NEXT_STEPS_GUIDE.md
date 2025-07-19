# AI Tutor: Next Steps Guide

This guide outlines the next steps for enhancing the AI Tutor system after completing the core restructuring and PostgreSQL database integration. The following production-grade enhancements will improve performance, scalability, and user experience.

## 1. Integrate Celery and Redis for Background Tasks

### Why It's Needed
- **Asynchronous Processing**: Long-running tasks like AI model interactions should run asynchronously to prevent blocking the main application thread
- **Improved Responsiveness**: Users get faster responses while heavy processing happens in the background
- **Task Scheduling**: Enables scheduling of periodic tasks like data aggregation, report generation, and cleanup operations
- **Reliability**: Failed tasks can be automatically retried with configurable backoff strategies

### Implementation Steps

#### 1.1. Set Up Redis
1. **On Render**:
   - Create a new Redis service in your Render dashboard
   - Note the connection URL provided by Render

2. **Local Development**:
   - Install Redis locally for development
   - For Windows: Use WSL2 or Docker
   - For macOS/Linux: Install via package manager

#### 1.2. Install Required Packages
Add the following to `requirements.txt`:
```
celery>=5.2.7
redis>=4.5.1
flower>=1.2.0  # Optional: Web UI for monitoring Celery
```

#### 1.3. Configure Celery in the Application
Create `app/celery_app.py`:
```python
from celery import Celery

def create_celery_app(app=None):
    """Create and configure Celery app"""
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
```

#### 1.4. Update Configuration
In `app/config.py`, add:
```python
# Celery Configuration
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
```

#### 1.5. Initialize Celery in the Flask App Factory
Update `app/__init__.py`:
```python
from app.celery_app import create_celery_app

# Inside create_app function
celery = create_celery_app(app)
app.celery = celery
```

#### 1.6. Create Task Modules
Create `app/tasks/`:
```
app/
  tasks/
    __init__.py
    ai_tasks.py
    analytics_tasks.py
    maintenance_tasks.py
```

Example task in `app/tasks/ai_tasks.py`:
```python
from app import celery

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def process_ai_response(self, prompt, model_params):
    """Process AI response asynchronously"""
    try:
        # AI processing logic here
        return result
    except Exception as exc:
        self.retry(exc=exc)
```

#### 1.7. Create Celery Worker Start Script
Create `celery_worker.py` in the project root:
```python
from app import create_app
from app.celery_app import create_celery_app

app = create_app()
celery = create_celery_app(app)
```

#### 1.8. Update Procfile for Render
Add to `Procfile`:
```
web: gunicorn run:app
worker: celery -A celery_worker.celery worker --loglevel=info
```

### Usage Examples
In your service layer:
```python
from app.tasks.ai_tasks import process_ai_response

# Synchronous call
result = ai_service.generate_response(prompt)

# Asynchronous call
task = process_ai_response.delay(prompt, model_params)
task_id = task.id  # Store this to check status later
```

## 2. Implement Session Analytics in Admin Dashboard

### Why It's Needed
- **Performance Insights**: Understand how the AI Tutor is performing across different subjects and student demographics
- **Usage Patterns**: Identify peak usage times and optimize resource allocation
- **Quality Monitoring**: Track session quality metrics to continuously improve the AI tutor
- **Student Progress**: Visualize individual and aggregate student progress over time

### Implementation Steps

#### 2.1. Define Analytics Data Models
Update or create models in `app/models/`:

```python
# app/models/analytics.py
from app.models.base import Base
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class SessionMetrics(Base):
    __tablename__ = 'session_metrics'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey('sessions.id'))
    duration_seconds = Column(Integer)
    message_count = Column(Integer)
    student_satisfaction = Column(Float, nullable=True)
    topic_coverage = Column(Float, nullable=True)
    created_at = Column(DateTime)
    
    session = relationship("Session", back_populates="metrics")

class DailyStats(Base):
    __tablename__ = 'daily_stats'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    total_sessions = Column(Integer)
    avg_duration = Column(Float)
    total_users = Column(Integer)
    popular_topics = Column(String)  # JSON string of topic:count pairs
```

#### 2.2. Create Analytics Repository
Create `app/repositories/analytics_repository.py`:

```python
from app.repositories.base_repository import BaseRepository
from app.models.analytics import SessionMetrics, DailyStats
from sqlalchemy import func, desc
from datetime import datetime, timedelta

class AnalyticsRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session)
    
    def get_session_metrics(self, session_id):
        return self.session.query(SessionMetrics).filter_by(session_id=session_id).first()
    
    def get_daily_stats(self, start_date, end_date):
        return self.session.query(DailyStats).filter(
            DailyStats.date.between(start_date, end_date)
        ).order_by(DailyStats.date).all()
    
    def get_popular_topics(self, days=30):
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = self.session.query(DailyStats).filter(
            DailyStats.date >= cutoff_date
        ).all()
        # Process and aggregate popular_topics from results
        return aggregated_topics
```

#### 2.3. Create Analytics Service
Create `app/services/analytics_service.py`:

```python
import json
from datetime import datetime, timedelta
from app.repositories.analytics_repository import AnalyticsRepository
from app.tasks.analytics_tasks import aggregate_daily_stats

class AnalyticsService:
    def __init__(self, db_session):
        self.repository = AnalyticsRepository(db_session)
    
    def get_dashboard_data(self, time_range='week'):
        """Get data for the analytics dashboard"""
        today = datetime.utcnow().date()
        
        if time_range == 'week':
            start_date = today - timedelta(days=7)
        elif time_range == 'month':
            start_date = today - timedelta(days=30)
        elif time_range == 'quarter':
            start_date = today - timedelta(days=90)
        else:
            start_date = today - timedelta(days=7)
        
        daily_stats = self.repository.get_daily_stats(start_date, today)
        popular_topics = self.repository.get_popular_topics(days=int((today-start_date).days))
        
        return {
            'daily_stats': daily_stats,
            'popular_topics': popular_topics,
            'time_range': time_range
        }
    
    def schedule_metrics_aggregation(self):
        """Schedule the daily metrics aggregation task"""
        aggregate_daily_stats.delay()
```

#### 2.4. Create Analytics Tasks
In `app/tasks/analytics_tasks.py`:

```python
from app import celery
from app.models.analytics import DailyStats
from app.models.session import Session
from sqlalchemy import func
import json
from datetime import datetime, timedelta

@celery.task
def aggregate_daily_stats():
    """Aggregate session data into daily statistics"""
    from app import db
    
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    start = datetime.combine(yesterday, datetime.min.time())
    end = datetime.combine(yesterday, datetime.max.time())
    
    # Get session stats for yesterday
    sessions = db.session.query(Session).filter(
        Session.created_at.between(start, end)
    ).all()
    
    if not sessions:
        return "No sessions found for aggregation"
    
    # Calculate metrics
    total_sessions = len(sessions)
    total_duration = sum(s.duration_seconds for s in sessions if s.duration_seconds)
    avg_duration = total_duration / total_sessions if total_sessions > 0 else 0
    
    # Count unique users
    unique_users = set(s.student_id for s in sessions)
    total_users = len(unique_users)
    
    # Aggregate topics
    topics = {}
    for session in sessions:
        if session.topics:
            for topic in session.topics.split(','):
                topic = topic.strip()
                topics[topic] = topics.get(topic, 0) + 1
    
    # Sort topics by count
    sorted_topics = {k: v for k, v in sorted(
        topics.items(), key=lambda item: item[1], reverse=True
    )[:10]}  # Top 10 topics
    
    # Create or update daily stats
    stats = DailyStats(
        date=yesterday,
        total_sessions=total_sessions,
        avg_duration=avg_duration,
        total_users=total_users,
        popular_topics=json.dumps(sorted_topics)
    )
    
    db.session.add(stats)
    db.session.commit()
    
    return f"Aggregated stats for {yesterday}"
```

#### 2.5. Create Admin Dashboard Routes
Update `app/main/routes.py`:

```python
from flask import render_template, request
from app.services.analytics_service import AnalyticsService

@main.route('/admin/analytics')
@login_required
def analytics_dashboard():
    time_range = request.args.get('range', 'week')
    analytics_service = AnalyticsService(db.session)
    dashboard_data = analytics_service.get_dashboard_data(time_range)
    
    return render_template(
        'admin/analytics.html',
        data=dashboard_data
    )
```

#### 2.6. Create Analytics Templates
Create `app/templates/admin/analytics.html`:

```html
{% extends "admin/base.html" %}

{% block content %}
<div class="analytics-dashboard">
    <h1>Session Analytics Dashboard</h1>
    
    <div class="time-range-selector">
        <a href="{{ url_for('main.analytics_dashboard', range='week') }}" 
           class="btn {% if data.time_range == 'week' %}btn-primary{% else %}btn-outline-primary{% endif %}">
            Last Week
        </a>
        <a href="{{ url_for('main.analytics_dashboard', range='month') }}"
           class="btn {% if data.time_range == 'month' %}btn-primary{% else %}btn-outline-primary{% endif %}">
            Last Month
        </a>
        <a href="{{ url_for('main.analytics_dashboard', range='quarter') }}"
           class="btn {% if data.time_range == 'quarter' %}btn-primary{% else %}btn-outline-primary{% endif %}">
            Last Quarter
        </a>
    </div>
    
    <div class="row mt-4">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5>Daily Sessions</h5>
                </div>
                <div class="card-body">
                    <canvas id="sessionsChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5>Popular Topics</h5>
                </div>
                <div class="card-body">
                    <canvas id="topicsChart"></canvas>
                </div>
            </div>
        </div>
    </div>
    
    <div class="row mt-4">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <h5>Session Duration Trends</h5>
                </div>
                <div class="card-body">
                    <canvas id="durationChart"></canvas>
                </div>
            </div>
        </div>
    </div>
</div>

{% block scripts %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    // Parse data from server
    const dailyStats = {{ data.daily_stats|tojson }};
    const popularTopics = {{ data.popular_topics|tojson }};
    
    // Format data for charts
    const dates = dailyStats.map(stat => stat.date);
    const sessions = dailyStats.map(stat => stat.total_sessions);
    const durations = dailyStats.map(stat => stat.avg_duration);
    
    const topicLabels = Object.keys(popularTopics);
    const topicCounts = Object.values(popularTopics);
    
    // Create charts
    const sessionsChart = new Chart(
        document.getElementById('sessionsChart'),
        {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Number of Sessions',
                    data: sessions,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            }
        }
    );
    
    const topicsChart = new Chart(
        document.getElementById('topicsChart'),
        {
            type: 'bar',
            data: {
                labels: topicLabels,
                datasets: [{
                    label: 'Topic Frequency',
                    data: topicCounts,
                    backgroundColor: 'rgba(153, 102, 255, 0.6)'
                }]
            }
        }
    );
    
    const durationChart = new Chart(
        document.getElementById('durationChart'),
        {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Average Session Duration (minutes)',
                    data: durations.map(d => d / 60), // Convert seconds to minutes
                    borderColor: 'rgb(255, 99, 132)',
                    tension: 0.1
                }]
            }
        }
    );
</script>
{% endblock %}
{% endblock %}
```

#### 2.7. Add CSS for Analytics Dashboard
Add to your CSS files:

```css
.analytics-dashboard {
    padding: 20px;
}

.time-range-selector {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin-bottom: 20px;
}

.card {
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.card-header {
    background-color: #f8f9fa;
    font-weight: bold;
}

canvas {
    max-height: 300px;
}
```

## Getting Started

To implement these enhancements, follow these steps:

1. **Set up the development environment**:
   ```bash
   # Install Redis (Windows/WSL2)
   sudo apt update
   sudo apt install redis-server
   
   # Install Redis (macOS)
   brew install redis
   
   # Start Redis
   redis-server
   
   # Install new Python dependencies
   pip install -r requirements.txt
   ```

2. **Implement Celery integration** following the steps in Section 1

3. **Implement analytics** following the steps in Section 2

4. **Test locally** before deploying to Render

5. **Update Render configuration** with Redis service

## Benefits

These enhancements will provide:

- **Improved Performance**: Offloading heavy tasks to background workers
- **Better User Experience**: Faster response times and more informative analytics
- **Scalability**: Ability to handle more concurrent users and sessions
- **Data-Driven Improvements**: Analytics to guide future development

## Timeline

Estimated implementation time:
- Celery and Redis integration: 2-3 days
- Analytics dashboard: 3-4 days
- Testing and deployment: 1-2 days

Total: 6-9 days of development effort