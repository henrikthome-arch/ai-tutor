"""
Curriculum model
"""

from app import db
from sqlalchemy.sql import func

class Curriculum(db.Model):
    """Curriculum model for educational frameworks"""
    __tablename__ = 'curriculums'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    grade = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    student_type = db.Column(db.String(20), nullable=False)  # 'International', 'Local', or 'Both'
    goals = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    school = db.relationship('School', back_populates='curriculums')
    
    # Composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('school_id', 'grade', 'subject', 'student_type', name='uix_curriculum'),
    )
    
    def __repr__(self):
        return f'<Curriculum {self.subject} Grade {self.grade} ({self.student_type})>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'school_id': self.school_id,
            'school_name': self.school.name if self.school else None,
            'grade': self.grade,
            'subject': self.subject,
            'student_type': self.student_type,
            'goals': self.goals,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }