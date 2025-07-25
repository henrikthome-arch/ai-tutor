#!/usr/bin/env python3
"""
Seed script for AI Tutor database
Populates the database with default curriculum, subjects, and school data
"""

import os
import sys
import re
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.school import School
from app.models.curriculum import Curriculum, Subject, CurriculumDetail
# Note: SchoolDefaultSubject removed - was documented but never implemented
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
    """Create default curriculum assignments for schools"""
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
        
        # Note: SchoolDefaultSubject functionality removed - was documented but never implemented
        # Schools now use the default curriculum system instead
        # Individual students receive curriculum assignments via StudentSubject records
        
        print(f"✅ Assigned default curriculum to {school.name}")
    
    db.session.commit()

def determine_subject_category(subject_name):
    """Determine the category for a subject based on its name"""
    subject_lower = subject_name.lower()
    
    if any(keyword in subject_lower for keyword in ['mathematics', 'math', 'computing', 'science']):
        return 'STEM'
    elif any(keyword in subject_lower for keyword in ['english', 'literacy', 'language']):
        return 'Language Arts'
    elif any(keyword in subject_lower for keyword in ['art', 'music', 'design']):
        return 'Arts'
    elif any(keyword in subject_lower for keyword in ['physical', 'pe', 'sport']):
        return 'Health & Wellness'
    elif any(keyword in subject_lower for keyword in ['global', 'perspectives', 'social']):
        return 'Social Sciences'
    else:
        return 'General'

def determine_if_core_subject(subject_name):
    """Determine if a subject is core based on its name"""
    core_subjects = ['english', 'mathematics', 'science']
    subject_lower = subject_name.lower()
    
    return any(core in subject_lower for core in core_subjects)

def parse_learning_objectives(details_text):
    """Parse learning objectives from the detailed description"""
    # Split by sentence endings or semicolons to create individual objectives
    objectives = re.split(r'[.;]\s+(?=[A-Z])', details_text)
    
    # Clean up objectives and filter out very short ones
    cleaned_objectives = []
    for obj in objectives:
        obj = obj.strip().rstrip('.')
        if len(obj) > 20:  # Only include substantial objectives
            cleaned_objectives.append(obj)
    
    # If we couldn't parse well, return the whole text as one objective
    if not cleaned_objectives:
        cleaned_objectives = [details_text]
    
    return cleaned_objectives[:10]  # Limit to 10 objectives max

def create_cambridge_curriculum():
    """Create Cambridge Primary 2025 curriculum from data file"""
    try:
        # Path to the Cambridge curriculum data file
        data_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'curriculum', 'cambridge_primary_2025.txt')
        
        if not os.path.exists(data_file_path):
            print(f"⚠️ Cambridge curriculum data file not found: {data_file_path}")
            return None

        print(f"📚 Loading Cambridge Primary 2025 curriculum data from TSV file...")
        
        # Check if default curriculum already exists
        existing_curriculum = Curriculum.query.filter_by(name='Cambridge Primary 2025', is_default=True).first()
        if existing_curriculum:
            print(f"ℹ️ Cambridge Primary 2025 curriculum already exists, skipping import")
            return existing_curriculum

        # Create the default Cambridge curriculum
        cambridge_curriculum = Curriculum(
            name='Cambridge Primary 2025',
            description='Cambridge Primary Programme for Grades 1-6 with comprehensive subject coverage',
            curriculum_type='Cambridge',
            grade_levels=[1, 2, 3, 4, 5, 6],
            is_template=True,
            is_default=True,
            created_by='system'
        )
        
        db.session.add(cambridge_curriculum)
        db.session.flush()  # Get the curriculum ID
        
        # Read and parse the TSV file
        with open(data_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Skip header line and process data
        subject_details = {}
        for line_num, line in enumerate(lines[1:], 2):  # Start from line 2 (skip header)
            try:
                parts = line.strip().split('\t')
                if len(parts) < 4:
                    print(f"⚠️ Skipping malformed line {line_num}: {line.strip()}")
                    continue
                
                grade, subject, mandatory, details = parts[0], parts[1], parts[2], parts[3]
                
                # Clean the details field (remove quotes)
                details = details.strip('"')
                
                grade_level = int(grade)
                is_mandatory = mandatory.lower() == 'yes'
                
                # Group by subject for efficient database operations
                if subject not in subject_details:
                    subject_details[subject] = []
                
                subject_details[subject].append({
                    'grade_level': grade_level,
                    'is_mandatory': is_mandatory,
                    'details': details
                })
                
            except (ValueError, IndexError) as e:
                print(f"⚠️ Error parsing line {line_num}: {e}")
                continue
        
        # Create subjects and curriculum details
        subjects_created = 0
        details_created = 0
        
        for subject_name, grade_data in subject_details.items():
            # Create or get subject
            subject = Subject.query.filter_by(name=subject_name).first()
            if not subject:
                # Determine subject category and if it's core
                category = determine_subject_category(subject_name)
                is_core = determine_if_core_subject(subject_name)
                
                subject = Subject(
                    name=subject_name,
                    description=f'{subject_name} curriculum for Cambridge Primary Programme',
                    category=category,
                    is_core=is_core
                )
                db.session.add(subject)
                db.session.flush()  # Get the subject ID
                subjects_created += 1
            
            # Create curriculum details for each grade
            for grade_info in grade_data:
                # Parse learning objectives from details
                learning_objectives = parse_learning_objectives(grade_info['details'])
                
                curriculum_detail = CurriculumDetail(
                    curriculum_id=cambridge_curriculum.id,
                    subject_id=subject.id,
                    grade_level=grade_info['grade_level'],
                    learning_objectives=learning_objectives,
                    assessment_criteria=['Understanding', 'Application', 'Analysis'],
                    recommended_hours_per_week=4 if grade_info['is_mandatory'] else 2,
                    prerequisites=[] if grade_info['grade_level'] == 1 else [f"Grade {grade_info['grade_level']-1} {subject_name}"],
                    resources=['Cambridge Primary Textbook', 'Online Resources', 'Interactive Activities'],
                    is_mandatory=grade_info['is_mandatory']
                )
                
                db.session.add(curriculum_detail)
                details_created += 1
        
        # Commit all changes
        db.session.commit()
        
        print(f"✅ Cambridge Primary 2025 curriculum imported successfully!")
        print(f"   📚 Curriculum: {cambridge_curriculum.name}")
        print(f"   📖 Subjects created: {subjects_created}")
        print(f"   📝 Curriculum details created: {details_created}")
        
        return cambridge_curriculum
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error loading Cambridge curriculum data: {e}")
        import traceback
        print(f"🔍 Stack trace: {traceback.format_exc()}")
        return None

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
        
        # Create Cambridge Primary 2025 curriculum
        print("\n📚 Creating Cambridge Primary 2025 default curriculum...")
        cambridge_curriculum = create_cambridge_curriculum()
        if cambridge_curriculum:
            curriculums.append(cambridge_curriculum)
        
        # Create school defaults
        print("\n🔗 Creating school default assignments...")
        create_school_defaults(schools, curriculums, subjects)
        
        print(f"\n✅ Database seeding completed successfully!")
        print(f"   Created {len(subjects)} subjects")
        print(f"   Created {len(schools)} schools")
        print(f"   Created {len(curriculums)} curriculum templates")
        if cambridge_curriculum:
            print(f"   📚 Cambridge Primary 2025 curriculum loaded as default")
        
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