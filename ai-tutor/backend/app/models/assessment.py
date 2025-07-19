"""
Assessment model
"""

from app import db
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY

class Assessment(db.Model):
    """Assessment model for student academic progress"""
    __tablename__ = 'assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    grade = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    strengths = db.Column(ARRAY(db.String), default=[])
    weaknesses = db.Column(ARRAY(db.String), default=[])
    mastery_level = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    completion_percentage = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    grade_score = db.Column(db.String(2), nullable=True)  # A+, A, A-, B+, etc.
    grade_motivation = db.Column(db.Text, nullable=True)
    comments_tutor = db.Column(db.Text, nullable=True)
    comments_teacher = db.Column(db.Text, nullable=True)
    last_updated = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    student = db.relationship('Student', back_populates='assessments')
    
    # Composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('student_id', 'grade', 'subject', name='uix_assessment'),
    )
    
    def __repr__(self):
        return f'<Assessment {self.subject} Grade {self.grade} for student_id={self.student_id}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'grade': self.grade,
            'subject': self.subject,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'mastery_level': self.mastery_level,
            'completion_percentage': self.completion_percentage,
            'grade_score': self.grade_score,
            'grade_motivation': self.grade_motivation,
            'comments_tutor': self.comments_tutor,
            'comments_teacher': self.comments_teacher,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }