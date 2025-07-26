"""
Student Profile model for versioned student profile management
"""

from app import db
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint

class StudentProfile(db.Model):
    """
    Versioned student profile model that stores narrative descriptions and traits.
    Each profile version is timestamped and linked to a specific student.
    """
    __tablename__ = 'student_profiles'
    
    id = db.Column(db.BigInteger, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    as_of = db.Column(db.DateTime, nullable=False, default=func.now())
    narrative = db.Column(db.Text, nullable=False)  # Human-readable paragraph about the student
    traits = db.Column(db.JSON, nullable=False, default=dict)  # JSON object storing structured traits
    
    # Unique constraint ensuring one profile per student per timestamp
    __table_args__ = (
        UniqueConstraint('student_id', 'as_of', name='uq_student_profile_as_of'),
    )
    
    # Relationships
    student = db.relationship('Student', backref='profile_history')
    
    def __repr__(self):
        return f'<StudentProfile {self.student_id} as_of={self.as_of}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'as_of': self.as_of.isoformat() if self.as_of else None,
            'narrative': self.narrative,
            'traits': self.traits or {},
            'student_name': self.student.full_name if self.student else None
        }
    
    def get_trait(self, key, default=None):
        """Get a specific trait value"""
        return self.traits.get(key, default) if self.traits else default
    
    def set_trait(self, key, value):
        """Set a specific trait value (creates new dict if needed)"""
        if not self.traits:
            self.traits = {}
        self.traits[key] = value
        # Mark the column as modified for SQLAlchemy
        db.session.merge(self)
        db.session.flush()