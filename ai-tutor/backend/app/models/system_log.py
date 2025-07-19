"""
SystemLog model
"""

from app import db
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

class SystemLog(db.Model):
    """SystemLog model for system events"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=func.now())
    level = db.Column(db.String(20), nullable=False, index=True)  # INFO, WARNING, ERROR, etc.
    category = db.Column(db.String(50), nullable=False, index=True)  # SYSTEM, WEBHOOK, AI_ANALYSIS, etc.
    message = db.Column(db.Text, nullable=False)
    data = db.Column(JSONB, nullable=True)  # Additional structured data
    
    def __repr__(self):
        return f'<SystemLog {self.id} {self.level} {self.category}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'level': self.level,
            'category': self.category,
            'message': self.message,
            'data': self.data
        }
    
    @classmethod
    def get_logs_by_date(cls, date, category=None, level=None):
        """Get logs for a specific date"""
        query = cls.query.filter(
            func.date(cls.timestamp) == date
        )
        
        if category:
            query = query.filter(cls.category == category)
        
        if level:
            query = query.filter(cls.level == level)
        
        return query.order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_logs_by_date_range(cls, start_date, end_date, category=None, level=None):
        """Get logs for a date range"""
        query = cls.query.filter(
            func.date(cls.timestamp) >= start_date,
            func.date(cls.timestamp) <= end_date
        )
        
        if category:
            query = query.filter(cls.category == category)
        
        if level:
            query = query.filter(cls.level == level)
        
        return query.order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def delete_logs_older_than(cls, days):
        """Delete logs older than a certain number of days"""
        cutoff_date = func.current_date() - days
        deleted = cls.query.filter(func.date(cls.timestamp) < cutoff_date).delete()
        db.session.commit()
        return deleted