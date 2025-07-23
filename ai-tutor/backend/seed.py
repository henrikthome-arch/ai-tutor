#!/usr/bin/env python3
"""
Seed script for AI Tutor database
Populates the database with default curriculum, subjects, and school data
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.school import School
from app.models.curriculum import Curriculum, Subject, CurriculumDetail, SchoolDefaultSubject
from app.models.student import Student

def create_default_subjects():
    """Create default subjects for all curricula"""
    default_subjects = [
        {
            'name': 'Mathematics',
            'description': 'Core mathematical concepts and problem-solving skills',
            'category': 'STEM',
            'is_core': True
        },
        {
            'name': 'English Language Arts',
            'description': 'Reading, writing, speaking, and listening skills',
            'category': 'Language Arts',
            'is_core': True
        },
        {
            'name': 'Science',
            'description': 'Natural sciences including physics, chemistry, and biology',
            'category': 'STEM',
            'is_core': True
        },
        {
            'name': 'Social Studies',
            'description': 'History, geography, civics, and cultural studies',
            'category': 'Social Sciences',
            'is_core': True
        },
        {
            'name': 'Physical Education',
            'description': 'Physical fitness, sports, and health education',
            'category': 'Health & Wellness',
            'is_core': False
        },
        {
            'name': 'Art',
            'description': 'Visual arts, creativity, and artistic expression',
            'category': 'Arts',
            'is_core': False
        },
        {
            'name': 'Music',
            'description': 'Musical education, theory, and performance',
            'category': 'Arts',
            'is_core': False
        },
        {
            'name': 'Computer Science',
            'description': 'Programming, computational thinking, and digital literacy',
            'category': 'STEM',
            'is_core': False
        },
        {
            'name': 'Foreign Language',
            'description': 'Second language acquisition and cultural awareness',
            'category': 'Language Arts',
            'is_core': False
        }
    ]
    
    created_subjects = []
    for subject_data in default_subjects:
        # Check if subject already exists
        existing_subject = Subject.query.filter_by(name=subject_data['name']).first()
        if not existing_subject:
            subject = Subject(**subject_data)
            db.session.add(subject)
            created_subjects.append(subject)
            print(f"✅ Created subject: {subject_data['name']}")
        else:
            created_subjects.append(existing_subject)
            print(f"ℹ️ Subject already exists: {subject_data['name']}")
    
    db.session.commit()
    return created_subjects

def create_default_schools():
    """Create default example schools"""
    default_schools = [
        {
            'name': 'International School of Athens',
            'country': 'Greece',
            'city': 'Athens',
            'description': 'A premier international school offering IB and American curriculum',
            'core_values': ['Excellence', 'Innovation', 'Global Citizenship', 'Integrity']
        },
        {
            'name': 'American Community School',
            'country': 'Greece',
            'city': 'Athens',
            'description': 'American-style education with international perspective',
            'core_values': ['Academic Excellence', 'Character Development', 'Community Service']
        },
        {
            'name': 'Generic International School',
            'country': 'International',
            'city': 'Global',
            'description': 'Default school template for international students',
            'core_values': ['Global Learning', 'Cultural Diversity', 'Academic Achievement']
        }
    ]
    
    created_schools = []
    for school_data in default_schools:
        # Check if school already exists
        existing_school = School.query.filter_by(name=school_data['name']).first()
        if not existing_school:
            school = School(**school_data)
            db.session.add(school)
            created_schools.append(school)
            print(f"✅ Created school: {school_data['name']}")
        else:
            created_schools.append(existing_school)
            print(f"ℹ️ School already exists: {school_data['name']}")
    
    db.session.commit()
    return created_schools

def create_default_curriculums(schools, subjects):
    """Create default curriculum templates"""
    # Create IB Primary Years Programme
    ib_pyp_data = {
        'name': 'IB Primary Years Programme',
        'description': 'International Baccalaureate Primary Years Programme for ages 3-12',
        'curriculum_type': 'IB',
        'grade_levels': [1, 2, 3, 4, 5, 6],
        'is_template': True,
        'created_by': 'system'
    }
    
    # Create American Elementary Curriculum
    american_elem_data = {
        'name': 'American Elementary Curriculum',
        'description': 'Standard American elementary education curriculum',
        'curriculum_type': 'American',
        'grade_levels': [1, 2, 3, 4, 5],
        'is_template': True,
        'created_by': 'system'
    }
    
    # Create British Primary Curriculum
    british_primary_data = {
        'name': 'British Primary Curriculum',
        'description': 'UK National Curriculum for primary education',
        'curriculum_type': 'British',
        'grade_levels': [1, 2, 3, 4, 5, 6],
        'is_template': True,
        'created_by': 'system'
    }
    
    curriculum_templates = [ib_pyp_data, american_elem_data, british_primary_data]
    created_curriculums = []
    
    for curriculum_data in curriculum_templates:
        # Check if curriculum already exists
        existing_curriculum = Curriculum.query.filter_by(name=curriculum_data['name']).first()
        if not existing_curriculum:
            curriculum = Curriculum(**curriculum_data)
            db.session.add(curriculum)
            db.session.flush()  # Flush to get the ID
            created_curriculums.append(curriculum)
            print(f"✅ Created curriculum: {curriculum_data['name']}")
            
            # Create curriculum details for each subject and grade level
            create_curriculum_details(curriculum, subjects)
            
        else:
            created_curriculums.append(existing_curriculum)
            print(f"ℹ️ Curriculum already exists: {curriculum_data['name']}")
    
    db.session.commit()
    return created_curriculums

def create_curriculum_details(curriculum, subjects):
    """Create detailed curriculum content for each subject and grade"""
    core_subjects = [s for s in subjects if s.is_core]
    
    for grade in curriculum.grade_levels:
        for subject in core_subjects:
            # Create age-appropriate learning objectives
            if subject.name == 'Mathematics':
                objectives = get_math_objectives(grade)
            elif subject.name == 'English Language Arts':
                objectives = get_english_objectives(grade)
            elif subject.name == 'Science':
                objectives = get_science_objectives(grade)
            elif subject.name == 'Social Studies':
                objectives = get_social_studies_objectives(grade)
            else:
                objectives = [f"Grade {grade} {subject.name} fundamentals"]
            
            curriculum_detail = CurriculumDetail(
                curriculum_id=curriculum.id,
                subject_id=subject.id,
                grade_level=grade,
                learning_objectives=objectives,
                assessment_criteria=['Understanding', 'Application', 'Analysis'],
                recommended_hours_per_week=4 if subject.is_core else 2,
                prerequisites=[] if grade == 1 else [f"Grade {grade-1} {subject.name}"],
                resources=['Textbook', 'Online Materials', 'Interactive Activities']
            )
            
            db.session.add(curriculum_detail)
    
    print(f"  ✅ Created curriculum details for {curriculum.name}")

def get_math_objectives(grade):
    """Get grade-appropriate math learning objectives"""
    objectives = {
        1: ['Count to 100', 'Basic addition and subtraction', 'Identify shapes'],
        2: ['Place value to 100', 'Two-digit addition/subtraction', 'Measurement basics'],
        3: ['Multiplication tables', 'Fractions introduction', 'Time and money'],
        4: ['Multi-digit operations', 'Decimals introduction', 'Area and perimeter'],
        5: ['Fraction operations', 'Decimal operations', 'Basic geometry'],
        6: ['Ratio and proportion', 'Integers', 'Basic algebra concepts']
    }
    return objectives.get(grade, [f'Grade {grade} mathematics'])

def get_english_objectives(grade):
    """Get grade-appropriate English learning objectives"""
    objectives = {
        1: ['Phonics and sight words', 'Simple sentence writing', 'Reading comprehension'],
        2: ['Expanded vocabulary', 'Story structure', 'Grammar basics'],
        3: ['Reading fluency', 'Paragraph writing', 'Parts of speech'],
        4: ['Complex sentences', 'Research skills', 'Literary elements'],
        5: ['Essay writing', 'Critical thinking', 'Advanced grammar'],
        6: ['Persuasive writing', 'Text analysis', 'Public speaking']
    }
    return objectives.get(grade, [f'Grade {grade} English language arts'])

def get_science_objectives(grade):
    """Get grade-appropriate science learning objectives"""
    objectives = {
        1: ['Living vs. non-living', 'Weather observation', 'Basic properties of matter'],
        2: ['Plant and animal life cycles', 'States of matter', 'Simple machines'],
        3: ['Food chains', 'Forces and motion', 'Earth science basics'],
        4: ['Ecosystems', 'Energy forms', 'Rock cycle introduction'],
        5: ['Human body systems', 'Chemistry basics', 'Space science'],
        6: ['Scientific method', 'Genetics introduction', 'Environmental science']
    }
    return objectives.get(grade, [f'Grade {grade} science'])

def get_social_studies_objectives(grade):
    """Get grade-appropriate social studies learning objectives"""
    objectives = {
        1: ['Community helpers', 'Maps and globes', 'Traditions and holidays'],
        2: ['Local history', 'Geographic features', 'Citizenship basics'],
        3: ['Ancient civilizations', 'World geography', 'Government introduction'],
        4: ['National history', 'Cultural diversity', 'Economic concepts'],
        5: ['World history', 'Global connections', 'Democratic principles'],
        6: ['Current events', 'Comparative governments', 'Global citizenship']
    }
    return objectives.get(grade, [f'Grade {grade} social studies'])

def create_school_defaults(schools, curriculums, subjects):
    """Create default subject assignments for schools"""
    for school in schools:
        # Assign default curriculum if not already set
        if not school.default_curriculum_id and curriculums:
            if 'International' in school.name:
                # Assign IB curriculum to international schools
                ib_curriculum = next((c for c in curriculums if 'IB' in c.name), curriculums[0])
                school.default_curriculum_id = ib_curriculum.id
            else:
                # Assign first available curriculum
                school.default_curriculum_id = curriculums[0].id
        
        # Create default subject assignments
        core_subjects = [s for s in subjects if s.is_core]
        for subject in core_subjects:
            # Check if assignment already exists
            existing_assignment = SchoolDefaultSubject.query.filter_by(
                school_id=school.id, 
                subject_id=subject.id
            ).first()
            
            if not existing_assignment:
                assignment = SchoolDefaultSubject(
                    school_id=school.id,
                    subject_id=subject.id,
                    is_required=subject.is_core,
                    default_hours_per_week=4 if subject.is_core else 2,
                    grade_levels=[1, 2, 3, 4, 5, 6]
                )
                db.session.add(assignment)
        
        print(f"✅ Created default subjects for {school.name}")
    
    db.session.commit()

def seed_database():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    
    try:
        # Create default subjects
        print("\n📚 Creating default subjects...")
        subjects = create_default_subjects()
        
        # Create default schools
        print("\n🏫 Creating default schools...")
        schools = create_default_schools()
        
        # Create default curriculums
        print("\n📋 Creating default curriculums...")
        curriculums = create_default_curriculums(schools, subjects)
        
        # Create school defaults
        print("\n🔗 Creating school default assignments...")
        create_school_defaults(schools, curriculums, subjects)
        
        print(f"\n✅ Database seeding completed successfully!")
        print(f"   Created {len(subjects)} subjects")
        print(f"   Created {len(schools)} schools")
        print(f"   Created {len(curriculums)} curriculum templates")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        db.session.rollback()
        raise e

if __name__ == '__main__':
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        print("🔗 Connected to database")
        
        # Ensure tables exist
        db.create_all()
        print("📊 Database tables verified")
        
        # Run seeding
        seed_database()