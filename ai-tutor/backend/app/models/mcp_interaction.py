"""
MCP Interaction model for logging MCP server communications
"""

import uuid
from datetime import datetime
from app import db
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

class MCPInteraction(db.Model):
    """Model for logging MCP server request/response interactions"""
    __tablename__ = 'mcp_interactions'
    
    id = db.Column(db.Integer, primary_key=True)  # SERIAL primary key
    request_id = db.Column(db.String(36), nullable=False, unique=True, index=True)  # UUID as string
    session_id = db.Column(db.String(100), nullable=True, index=True)  # Optional session identifier
    token_id = db.Column(db.String(36), db.ForeignKey('tokens.id'), nullable=True, index=True)  # FK to tokens (UUID)
    request_timestamp = db.Column(db.DateTime, nullable=False, default=func.now(), index=True)
    request_payload = db.Column(JSONB, nullable=False)  # Full request JSON
    response_timestamp = db.Column(db.DateTime, nullable=True, index=True)
    response_payload = db.Column(JSONB, nullable=True)  # Full response JSON
    http_status_code = db.Column(db.Integer, nullable=True)  # HTTP response status
    duration_ms = db.Column(db.Integer, nullable=True)  # Request duration in milliseconds
    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    
    # Foreign key relationship
    token = db.relationship('Token', backref='mcp_interactions', lazy=True)
    
    def __repr__(self):
        return f'<MCPInteraction {self.request_id} {self.request_timestamp}>'
    
    @staticmethod
    def generate_request_id():
        """Generate a unique request ID"""
        return str(uuid.uuid4())
    
    def is_completed(self):
        """Check if interaction has received a response"""
        return self.response_timestamp is not None
    
    def calculate_duration(self):
        """Calculate duration between request and response"""
        if self.response_timestamp and self.request_timestamp:
            delta = self.response_timestamp - self.request_timestamp
            return int(delta.total_seconds() * 1000)  # Convert to milliseconds
        return None
    
    def complete_interaction(self, response_payload, http_status_code=None):
        """Complete the interaction with response data"""
        self.response_timestamp = func.now()
        self.response_payload = response_payload
        self.http_status_code = http_status_code
        self.duration_ms = self.calculate_duration()
        db.session.commit()
    
    def to_dict(self, include_payloads=True):
        """Convert to dictionary for API responses"""
        result = {
            'id': self.id,
            'request_id': self.request_id,
            'session_id': self.session_id,
            'token_id': self.token_id,
            'request_timestamp': self.request_timestamp.isoformat() if self.request_timestamp else None,
            'response_timestamp': self.response_timestamp.isoformat() if self.response_timestamp else None,
            'http_status_code': self.http_status_code,
            'duration_ms': self.duration_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_completed': self.is_completed()
        }
        
        # Include payloads if requested (may be large)
        if include_payloads:
            result['request_payload'] = self.request_payload
            result['response_payload'] = self.response_payload
            
        return result
    
    @classmethod
    def create_interaction(cls, request_payload, session_id=None, token_id=None):
        """Create a new MCP interaction record for incoming request"""
        interaction = cls(
            request_id=cls.generate_request_id(),
            session_id=session_id,
            token_id=token_id,
            request_payload=request_payload
        )
        
        db.session.add(interaction)
        db.session.commit()
        
        return interaction
    
    @classmethod
    def find_by_request_id(cls, request_id):
        """Find interaction by request ID"""
        return cls.query.filter_by(request_id=request_id).first()
    
    @classmethod
    def get_recent_interactions(cls, limit=100):
        """Get recent interactions ordered by request timestamp"""
        return cls.query.order_by(cls.request_timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_interactions_by_session(cls, session_id, limit=50):
        """Get interactions for a specific session"""
        return cls.query.filter_by(session_id=session_id).order_by(
            cls.request_timestamp.desc()
        ).limit(limit).all()
    
    @classmethod
    def get_interactions_by_token(cls, token_id, limit=50):
        """Get interactions for a specific token"""
        return cls.query.filter_by(token_id=token_id).order_by(
            cls.request_timestamp.desc()
        ).limit(limit).all()
    
    @classmethod
    def get_incomplete_interactions(cls, older_than_minutes=30):
        """Get interactions that haven't received responses within time limit"""
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(minutes=older_than_minutes)
        
        return cls.query.filter(
            cls.response_timestamp.is_(None),
            cls.request_timestamp < cutoff_time
        ).all()
    
    @classmethod
    def get_interactions_summary(cls, hours=24):
        """Get summary statistics for interactions in the last N hours"""
        from datetime import timedelta
        since_time = datetime.utcnow() - timedelta(hours=hours)
        
        total = cls.query.filter(cls.request_timestamp >= since_time).count()
        completed = cls.query.filter(
            cls.request_timestamp >= since_time,
            cls.response_timestamp.isnot(None)
        ).count()
        
        # Average duration for completed interactions
        avg_duration = db.session.query(func.avg(cls.duration_ms)).filter(
            cls.request_timestamp >= since_time,
            cls.duration_ms.isnot(None)
        ).scalar()
        
        return {
            'total_interactions': total,
            'completed_interactions': completed,
            'incomplete_interactions': total - completed,
            'completion_rate': (completed / total * 100) if total > 0 else 0,
            'average_duration_ms': int(avg_duration) if avg_duration else None
        }
    
    @classmethod
    def cleanup_old_interactions(cls, days=30):
        """Remove interactions older than specified days"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted_count = cls.query.filter(
            cls.created_at <= cutoff_date
        ).delete()
        db.session.commit()
        
        return deleted_count