"""
Student model
"""

from datetime import date
from app import db
from sqlalchemy.sql import func

class Student(db.Model):
    """Student model"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    phone_number = db.Column(db.String(20), nullable=True, unique=True, index=True)
    student_type = db.Column(db.String(20), default='International')  # 'International' or 'Local'
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    school = db.relationship('School', back_populates='students')
    profile = db.relationship('Profile', back_populates='student', uselist=False, cascade='all, delete-orphan')
    sessions = db.relationship('Session', back_populates='student', lazy='dynamic', cascade='all, delete-orphan')
    assessments = db.relationship('Assessment', back_populates='student', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.first_name} {self.last_name}>'
    
    @property
    def age(self):
        """Calculate age from date of birth or get from profile"""
        # First try to get age from profile if it exists
        if self.profile and hasattr(self.profile, 'age_value'):
            return getattr(self.profile, 'age_value', None)
        
        # Otherwise calculate from date_of_birth
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def get_grade(self):
        """Get grade from profile"""
        if self.profile and hasattr(self.profile, 'grade_value'):
            return getattr(self.profile, 'grade_value', None)
        return None
    
    @property
    def full_name(self):
        """Get full name"""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'age': self.age,
            'grade': self.get_grade(),
            'phone_number': self.phone_number,
            'student_type': self.student_type,
            'school_id': self.school_id,
            'school_name': self.school.name if self.school else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }