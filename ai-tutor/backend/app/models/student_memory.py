"""
Student Memory model for scoped tutor memory management
"""

import enum
from app import db
from sqlalchemy.sql import func

class MemoryScope(enum.Enum):
    """Enumeration for different types of student memory"""
    personal_fact = "personal_fact"      # Personal information about the student (pet names, family, etc.)
    game_state = "game_state"            # Game progress and state information
    strategy_log = "strategy_log"        # Teaching strategies that worked or didn't work
    
    def get_description(self):
        """Get human-readable description for memory scope"""
        descriptions = {
            'personal_fact': 'Personal information about the student (name, age, family, pets, etc.)',
            'game_state': 'Current state of educational games and activities',
            'strategy_log': 'Teaching strategies that work well for this student'
        }
        return descriptions.get(self.value, 'Unknown scope')

class StudentMemory(db.Model):
    """
    Scoped key-value store for tutor memory about students.
    Stores different types of information with optional expiration.
    """
    __tablename__ = 'student_memories'
    
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, primary_key=True)
    memory_key = db.Column(db.String(255), nullable=False, primary_key=True)
    scope = db.Column(db.Enum(MemoryScope), nullable=False)
    value = db.Column(db.JSON)  # JSONB in PostgreSQL for flexible data storage
    expires_at = db.Column(db.DateTime, nullable=True)  # NULL means never expires
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    student = db.relationship('Student', backref='memories')
    
    def __repr__(self):
        return f'<StudentMemory {self.student_id}:{self.memory_key} scope={self.scope.value}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'student_id': self.student_id,
            'memory_key': self.memory_key,
            'scope': self.scope.value,
            'value': self.value,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'student_name': self.student.full_name if self.student else None
        }
    
    @property
    def is_expired(self):
        """Check if this memory has expired"""
        if not self.expires_at:
            return False
        return func.now() > self.expires_at
    
    @classmethod
    def get_by_scope(cls, student_id, scope):
        """Get all memories for a student by scope"""
        return cls.query.filter_by(
            student_id=student_id,
            scope=scope
        ).filter(
            db.or_(cls.expires_at.is_(None), cls.expires_at > func.now())
        ).all()
    
    @classmethod
    def get_unexpired(cls, student_id):
        """Get all non-expired memories for a student"""
        return cls.query.filter_by(student_id=student_id).filter(
            db.or_(cls.expires_at.is_(None), cls.expires_at > func.now())
        ).all()