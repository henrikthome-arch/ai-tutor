"""
Profile model
"""

from app import db
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY

class Profile(db.Model):
    """Profile model for student's detailed information"""
    __tablename__ = 'profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, unique=True)
    interests = db.Column(ARRAY(db.String), default=[])
    learning_preferences = db.Column(ARRAY(db.String), default=[])
    motivational_triggers = db.Column(ARRAY(db.String), default=[])
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    student = db.relationship('Student', back_populates='profile')
    
    def __repr__(self):
        return f'<Profile for student_id={self.student_id}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'interests': self.interests,
            'learning_preferences': self.learning_preferences,
            'motivational_triggers': self.motivational_triggers,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }