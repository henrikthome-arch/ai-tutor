"""
StudentSubject model for comprehensive student assessment and progress tracking
"""

from app import db
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY

class StudentSubject(db.Model):
    """StudentSubject model for individual student enrollment in specific subjects with comprehensive assessment data"""
    __tablename__ = 'student_subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    curriculum_detail_id = db.Column(db.Integer, db.ForeignKey('curriculum_details.id'), nullable=False)
    is_active_for_tutoring = db.Column(db.Boolean, default=True, nullable=False)  # Can be toggled by teachers/parents
    is_in_use = db.Column(db.Boolean, default=True, nullable=False)  # Marks if subject is currently active in student's curriculum
    teacher_notes = db.Column(db.Text, nullable=True)  # For guiding the AI on focus areas
    ai_tutor_notes = db.Column(db.Text, nullable=True)  # AI's own notes on student progress
    progress_percentage = db.Column(db.Float, nullable=True)  # Numeric progress from 0.0 to 1.0 (0% to 100%)
    ai_assessment = db.Column(db.Text, nullable=True)  # AI-generated assessment in natural language
    weaknesses = db.Column(db.Text, nullable=True)  # Areas where student needs improvement
    mastery_level = db.Column(db.String(50), nullable=True)  # Current mastery level of the subject
    comments_tutor = db.Column(db.Text, nullable=True)  # Comments from AI tutor
    comments_teacher = db.Column(db.Text, nullable=True)  # Comments from human teacher
    completion_percentage = db.Column(db.Float, nullable=True)  # Percentage of curriculum completed (0.0 to 1.0)
    grade_score = db.Column(db.String(10), nullable=True)  # Letter or numeric grade
    grade_motivation = db.Column(db.Text, nullable=True)  # Motivational feedback for the grade
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    student = db.relationship('Student', back_populates='student_subjects')
    curriculum_detail = db.relationship('CurriculumDetail', back_populates='student_subjects')
    
    # Composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('student_id', 'curriculum_detail_id', name='uix_student_curriculum_detail'),
    )
    
    def __repr__(self):
        subject_name = self.curriculum_detail.subject.name if self.curriculum_detail and self.curriculum_detail.subject else "Unknown"
        return f'<StudentSubject {subject_name} for student_id={self.student_id}>'
    
    @property
    def subject_name(self):
        """Get subject name from curriculum detail"""
        return self.curriculum_detail.subject.name if self.curriculum_detail and self.curriculum_detail.subject else None
    
    @property
    def grade_level(self):
        """Get grade level from curriculum detail"""
        return self.curriculum_detail.grade_level if self.curriculum_detail else None
    
    @property
    def curriculum_name(self):
        """Get curriculum name from curriculum detail"""
        return self.curriculum_detail.curriculum.name if self.curriculum_detail and self.curriculum_detail.curriculum else None
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'curriculum_detail_id': self.curriculum_detail_id,
            'subject_name': self.subject_name,
            'grade_level': self.grade_level,
            'curriculum_name': self.curriculum_name,
            'is_active_for_tutoring': self.is_active_for_tutoring,
            'is_in_use': self.is_in_use,
            'teacher_notes': self.teacher_notes,
            'ai_tutor_notes': self.ai_tutor_notes,
            'progress_percentage': self.progress_percentage,
            'ai_assessment': self.ai_assessment,
            'weaknesses': self.weaknesses,
            'mastery_level': self.mastery_level,
            'comments_tutor': self.comments_tutor,
            'comments_teacher': self.comments_teacher,
            'completion_percentage': self.completion_percentage,
            'grade_score': self.grade_score,
            'grade_motivation': self.grade_motivation,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
