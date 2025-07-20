"""
Session model
"""

from app import db
from sqlalchemy.sql import func

class Session(db.Model):
    """Session model for tutoring sessions"""
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    call_id = db.Column(db.String(50), nullable=True, unique=True, index=True)
    session_type = db.Column(db.String(20), nullable=False, default='phone')  # 'phone', 'web', etc.
    start_datetime = db.Column(db.DateTime, nullable=False, default=func.now())
    duration = db.Column(db.Integer, nullable=True)  # Duration in seconds
    transcript = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    topics_covered = db.Column(db.JSON, nullable=True)  # Store topics as JSON array
    engagement_score = db.Column(db.Integer, nullable=True)  # Store engagement score
    
    # Relationships
    student = db.relationship('Student', back_populates='sessions')
    
    def __repr__(self):
        return f'<Session {self.id} for student_id={self.student_id}>'
    
    @property
    def duration_minutes(self):
        """Get duration in minutes"""
        return self.duration // 60 if self.duration else None
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'call_id': self.call_id,
            'session_type': self.session_type,
            'start_datetime': self.start_datetime.isoformat() if self.start_datetime else None,
            'duration': self.duration,
            'duration_minutes': self.duration_minutes,
            'has_transcript': bool(self.transcript),
            'has_summary': bool(self.summary),
            'transcript_length': len(self.transcript) if self.transcript else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_dict_with_content(self):
        """Convert to dictionary including transcript and summary"""
        result = self.to_dict()
        result.update({
            'transcript': self.transcript,
            'summary': self.summary
        })
        return result