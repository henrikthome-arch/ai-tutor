"""
Curriculum-related models
"""

from app import db
from sqlalchemy.sql import func

class Curriculum(db.Model):
    """Curriculum model for educational frameworks"""
    __tablename__ = 'curriculums'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_default = db.Column(db.Boolean, default=False, nullable=False)  # System-wide default curriculum
    created_at = db.Column(db.DateTime, server_default=func.now())
    
    # Relationships
    curriculum_details = db.relationship('CurriculumDetail', back_populates='curriculum', lazy='dynamic', cascade='all, delete-orphan')
    schools = db.relationship('School', back_populates='curriculums', lazy='dynamic')
    
    def __repr__(self):
        return f'<Curriculum {self.name}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Subject(db.Model):
    """Subject model for academic subjects"""
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # e.g., 'Mathematics', 'History'
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    
    # Relationships
    curriculum_details = db.relationship('CurriculumDetail', back_populates='subject', lazy='dynamic')
    
    def __repr__(self):
        return f'<Subject {self.name}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CurriculumDetail(db.Model):
    """CurriculumDetail model mapping subjects to curriculums by grade level"""
    __tablename__ = 'curriculum_details'
    
    id = db.Column(db.Integer, primary_key=True)
    curriculum_id = db.Column(db.Integer, db.ForeignKey('curriculums.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    grade_level = db.Column(db.Integer, nullable=False)
    is_mandatory = db.Column(db.Boolean, default=True, nullable=False)
    goals_description = db.Column(db.Text, nullable=True)  # Natural language description of learning goals
    
    # Relationships
    curriculum = db.relationship('Curriculum', back_populates='curriculum_details')
    subject = db.relationship('Subject', back_populates='curriculum_details')
    student_subjects = db.relationship('StudentSubject', back_populates='curriculum_detail', lazy='dynamic')
    school_default_subjects = db.relationship('SchoolDefaultSubject', back_populates='curriculum_detail', lazy='dynamic')
    
    # Composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('curriculum_id', 'subject_id', 'grade_level', name='uix_curriculum_subject_grade'),
    )
    
    def __repr__(self):
        return f'<CurriculumDetail {self.curriculum.name if self.curriculum else "Unknown"} - {self.subject.name if self.subject else "Unknown"} Grade {self.grade_level}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'curriculum_id': self.curriculum_id,
            'curriculum_name': self.curriculum.name if self.curriculum else None,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'grade_level': self.grade_level,
            'is_mandatory': self.is_mandatory,
            'goals_description': self.goals_description
        }

class SchoolDefaultSubject(db.Model):
    """SchoolDefaultSubject model for school-specific curriculum templates"""
    __tablename__ = 'school_default_subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    curriculum_detail_id = db.Column(db.Integer, db.ForeignKey('curriculum_details.id'), nullable=False)
    
    # Relationships
    school = db.relationship('School', back_populates='school_default_subjects')
    curriculum_detail = db.relationship('CurriculumDetail', back_populates='school_default_subjects')
    
    # Composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('school_id', 'curriculum_detail_id', name='uix_school_curriculum_detail'),
    )
    
    def __repr__(self):
        return f'<SchoolDefaultSubject {self.school.name if self.school else "Unknown"} - {self.curriculum_detail}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'school_id': self.school_id,
            'school_name': self.school.name if self.school else None,
            'curriculum_detail_id': self.curriculum_detail_id,
            'curriculum_detail': self.curriculum_detail.to_dict() if self.curriculum_detail else None
        }