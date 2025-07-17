# 🛠️ Backend Implementation Todo List

## 📋 Current State vs Required Changes

### **✅ What We Have Working**
```yaml
Current_System:
  ✅ session-enhanced-server.py with VAPI webhooks
  ✅ Session tracking and boundary detection
  ✅ Student data structure (emma_smith example)
  ✅ get-student-context function (student_id based)
  ✅ Session post-processing framework
  ✅ Cloud deployment at https://ai-tutor-ptnl.onrender.com

Current_Function:
  get-student-context(student_id) → returns student profile/progress
```

### **🔧 What Needs Implementation**
```yaml
Required_Changes:
  1. Phone-based student lookup system
  2. Phone-to-student mapping file
  3. New student detection and onboarding response
  4. Welcome session transcript analysis
  5. Automatic student profile creation
  6. Phone number normalization
  7. Enhanced webhook processing for phone numbers

New_Function:
  get-student-context(phone_number) → returns existing OR new student context
```

---

## 🔧 Specific Implementation Tasks

### **Task 1: Create Phone Mapping System**

#### **File: `data/phone_mapping.json` (New)**
```json
{
  "phone_to_student": {
    "+15551234567": "emma_smith",
    "+15559876543": "jane_doe"
  },
  "last_updated": "2025-01-17T14:30:00Z"
}
```

#### **Implementation: Add to session-enhanced-server.py**
```python
class PhoneMappingManager:
    def __init__(self, mapping_file='data/phone_mapping.json'):
        self.mapping_file = mapping_file
        self.phone_mapping = self.load_phone_mapping()
    
    def load_phone_mapping(self):
        """Load phone to student mapping"""
        if os.path.exists(self.mapping_file):
            with open(self.mapping_file, 'r') as f:
                data = json.load(f)
                return data.get('phone_to_student', {})
        return {}
    
    def save_phone_mapping(self):
        """Save phone to student mapping"""
        os.makedirs(os.path.dirname(self.mapping_file), exist_ok=True)
        data = {
            'phone_to_student': self.phone_mapping,
            'last_updated': datetime.utcnow().isoformat()
        }
        with open(self.mapping_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_student_by_phone(self, phone_number):
        """Get student ID by phone number"""
        normalized_phone = self.normalize_phone_number(phone_number)
        return self.phone_mapping.get(normalized_phone)
    
    def add_phone_mapping(self, phone_number, student_id):
        """Add new phone to student mapping"""
        normalized_phone = self.normalize_phone_number(phone_number)
        self.phone_mapping[normalized_phone] = student_id
        self.save_phone_mapping()
        logger.info(f"📞 Mapped {normalized_phone} → {student_id}")
    
    def normalize_phone_number(self, phone_number):
        """Normalize phone number format"""
        digits_only = ''.join(filter(str.isdigit, phone_number))
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return f"+{digits_only}"
        else:
            return f"+{digits_only}"
```

### **Task 2: Modify get-student-context Function**

#### **Update in session-enhanced-server.py**
```python
# Replace existing handle_get_student_context method
def handle_get_student_context(self, request_data):
    """Enhanced student context handler with phone number support"""
    
    # Check if phone_number or student_id provided
    phone_number = request_data.get('phone_number')
    student_id = request_data.get('student_id')
    
    if phone_number:
        # Phone-based lookup
        return self.handle_phone_based_context(phone_number)
    elif student_id:
        # Legacy student_id lookup (backwards compatibility)
        return self.handle_student_id_context(student_id)
    else:
        self.send_error(400, "phone_number or student_id is required")

def handle_phone_based_context(self, phone_number):
    """Handle phone number based student context"""
    logger.info(f"📞 Phone-based lookup: {phone_number}")
    
    # Check if this is a known student
    student_id = self.phone_manager.get_student_by_phone(phone_number)
    
    if student_id:
        # Known student - return full context
        logger.info(f"✅ Known student: {student_id}")
        return self.get_existing_student_context(student_id, phone_number)
    else:
        # New student - return onboarding context
        logger.info(f"🆕 New student with phone: {phone_number}")
        return self.get_new_student_context(phone_number)

def get_existing_student_context(self, student_id, phone_number):
    """Get full context for existing student"""
    try:
        # Load student data (existing logic)
        profile = self.read_json_file(f'data/students/{student_id}/profile.json')
        progress = self.read_json_file(f'data/students/{student_id}/progress.json')
        curriculum = self.read_json_file('data/curriculum/international_school_greece.json')
        
        # Get recent sessions
        sessions_dir = f'data/students/{student_id}/sessions'
        recent_sessions = []
        if os.path.exists(sessions_dir):
            session_files = [f for f in os.listdir(sessions_dir) if f.endswith('_session.json')]
            session_files.sort(reverse=True)
            
            for session_file in session_files[:3]:
                try:
                    session_data = self.read_json_file(f'{sessions_dir}/{session_file}')
                    recent_sessions.append({
                        'date': session_file.split('_')[2],  # Extract date
                        'summary': session_data.get('summary', 'Session completed')
                    })
                except Exception as e:
                    logger.warning(f"Could not read session file {session_file}: {e}")
        
        grade_data = curriculum.get('grades', {}).get(str(profile.get('grade', 4)), {})
        
        response_data = {
            'student_type': 'existing',
            'student_id': student_id,
            'phone_number': phone_number,
            'profile': profile,
            'progress': progress,
            'recent_sessions': recent_sessions,
            'curriculum_context': {
                'grade_subjects': grade_data,
                'school_type': curriculum.get('school_type'),
                'curriculum_system': curriculum.get('curriculum_system')
            },
            'greeting_suggestion': f"Hi {profile.get('name', 'there')}! Ready for some learning today?"
        }
        
        logger.info(f"📚 Loaded context for existing student: {student_id}")
        self.send_json_response({'success': True, 'data': response_data})
        
    except Exception as e:
        logger.error(f"Error loading existing student context: {e}")
        self.send_error(500, str(e))

def get_new_student_context(self, phone_number):
    """Get onboarding context for new student"""
    try:
        # Load curriculum overview for onboarding
        curriculum = self.read_json_file('data/curriculum/international_school_greece.json')
        
        response_data = {
            'student_type': 'new',
            'phone_number': phone_number,
            'onboarding_needed': True,
            'greeting_suggestion': "Hello! I'm your AI tutor. I'd love to learn about you so I can help you with your studies!",
            'questions_to_ask': [
                "What's your name?",
                "How old are you?", 
                "What grade are you in?",
                "What are your favorite subjects?",
                "What do you like to do for fun?",
                "How do you like to learn? Do you like pictures, stories, or hands-on activities?"
            ],
            'curriculum_overview': {
                'grades_available': list(curriculum.get('grades', {}).keys()),
                'subjects': ['Mathematics', 'English', 'Science', 'History', 'Geography']
            }
        }
        
        logger.info(f"🆕 Generated onboarding context for: {phone_number}")
        self.send_json_response({'success': True, 'data': response_data})
        
    except Exception as e:
        logger.error(f"Error generating new student context: {e}")
        self.send_error(500, str(e))

def handle_student_id_context(self, student_id):
    """Legacy student_id based lookup (backwards compatibility)"""
    # Existing implementation remains unchanged
    logger.info(f"Getting context for student: {student_id}")
    # ... existing get_student_context logic ...
```

### **Task 3: Enhance VAPI Webhook Processing**

#### **Update webhook handler in session-enhanced-server.py**
```python
def handle_vapi_webhook(self, request_data):
    """Enhanced VAPI webhook with phone number extraction"""
    logger.info("📞 Received VAPI webhook")
    
    try:
        # Extract VAPI data
        call_id = request_data.get('call_id')
        transcript = request_data.get('transcript', '')
        started_at = request_data.get('started_at')
        ended_at = request_data.get('ended_at')
        duration = request_data.get('duration_seconds', 0)
        
        # NEW: Extract phone number from VAPI data
        phone_number = self.extract_phone_from_vapi_data(request_data)
        
        if not phone_number:
            logger.warning("No phone number found in VAPI webhook")
            self.send_json_response({'success': False, 'error': 'phone_number required'})
            return
        
        # Get student ID from phone number
        student_id = self.phone_manager.get_student_by_phone(phone_number)
        
        if not student_id:
            # This is a new student welcome call
            logger.info(f"🆕 Processing welcome call for: {phone_number}")
            return self.process_welcome_call(phone_number, request_data)
        
        # Existing student - process normally
        logger.info(f"📚 Processing session for existing student: {student_id}")
        
        # Create/update session
        session = self.get_or_create_session_by_phone(phone_number, student_id)
        
        # Update session with VAPI data
        session.update({
            'end_time': ended_at,
            'platform': 'vapi',
            'status': 'completed',
            'conversation': {
                'transcript': transcript,
                'source': 'vapi',
                'word_count': len(transcript.split()),
                'duration_seconds': duration
            },
            'vapi_metadata': {
                'call_id': call_id,
                'phone_number': phone_number,
                'ended_reason': request_data.get('ended_reason')
            }
        })
        
        # Save session
        self.close_session(session['session_id'])
        
        logger.info(f"✅ Processed VAPI webhook for session {session['session_id']}")
        self.send_json_response({'success': True, 'session_id': session['session_id']})
        
    except Exception as e:
        logger.error(f"❌ Error processing VAPI webhook: {e}")
        self.send_error(500, str(e))

def extract_phone_from_vapi_data(self, vapi_data):
    """Extract phone number from VAPI webhook data"""
    # Method 1: Direct phone_number field
    if 'phone_number' in vapi_data:
        return vapi_data['phone_number']
    
    # Method 2: Customer data
    if 'customer' in vapi_data and 'number' in vapi_data['customer']:
        return vapi_data['customer']['number']
    
    # Method 3: Metadata
    if 'metadata' in vapi_data and 'phone_number' in vapi_data['metadata']:
        return vapi_data['metadata']['phone_number']
    
    # Method 4: Call data (common VAPI structure)
    if 'call' in vapi_data and 'customer' in vapi_data['call']:
        return vapi_data['call']['customer'].get('number')
    
    return None
```

### **Task 4: Create Welcome Call Processor**

#### **Add new class to session-enhanced-server.py**
```python
class WelcomeCallProcessor:
    def __init__(self, phone_manager):
        self.phone_manager = phone_manager
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def process_welcome_call(self, phone_number, vapi_data):
        """Process welcome call and create new student if info complete"""
        transcript = vapi_data.get('transcript', '')
        
        # Extract student information from conversation
        student_info = self.extract_student_info_from_transcript(transcript)
        
        if self.is_complete_profile(student_info):
            # Create new student
            student_id = self.create_new_student(phone_number, student_info)
            
            # Create session for this welcome call
            session_id = self.create_welcome_session(phone_number, student_id, vapi_data)
            
            return {
                'success': True,
                'student_created': True,
                'student_id': student_id,
                'session_id': session_id,
                'message': f"Welcome {student_info.get('name', 'new student')}! Profile created."
            }
        else:
            # Incomplete profile - just log the attempt
            return {
                'success': True,
                'student_created': False,
                'partial_info': student_info,
                'message': "Welcome call processed, but more information needed"
            }
    
    def extract_student_info_from_transcript(self, transcript):
        """Extract student information using OpenAI"""
        if not transcript or len(transcript) < 50:
            return {}
        
        extraction_prompt = f"""
        Analyze this welcome conversation with a new student and extract their information:
        
        TRANSCRIPT: {transcript}
        
        Extract the following information if clearly mentioned:
        - name: Student's first name only
        - age: Age in years (number)
        - grade: School grade (1-6, as number)
        - favorite_subjects: List of subjects they mentioned liking
        - interests: Hobbies, favorite activities, things they like
        - learning_preferences: How they prefer to learn (visual, auditory, hands-on)
        
        Return ONLY valid JSON with the information that was clearly stated.
        If something wasn't mentioned clearly, don't include it.
        Use this exact format:
        {{
          "name": "Emma",
          "age": 9,
          "grade": 4,
          "favorite_subjects": ["math", "science"],
          "interests": ["animals", "space"],
          "learning_preferences": ["visual"]
        }}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": extraction_prompt}],
                max_tokens=500,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            # Clean up the response to ensure it's valid JSON
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            return json.loads(content)
        
        except Exception as e:
            logger.error(f"Error extracting student info: {e}")
            return {}
    
    def is_complete_profile(self, student_info):
        """Check if we have enough info to create a student profile"""
        required_fields = ['name', 'age', 'grade']
        return all(field in student_info and student_info[field] for field in required_fields)
    
    def create_new_student(self, phone_number, student_info):
        """Create new student profile and files"""
        # Generate student_id
        name = student_info.get('name', 'student').lower().replace(' ', '_')
        phone_suffix = phone_number[-4:]
        student_id = f"{name}_{phone_suffix}"
        
        # Ensure unique student_id
        counter = 1
        original_id = student_id
        while os.path.exists(f'data/students/{student_id}'):
            student_id = f"{original_id}_{counter}"
            counter += 1
        
        # Create student directory
        student_dir = f'data/students/{student_id}'
        os.makedirs(student_dir, exist_ok=True)
        os.makedirs(f'{student_dir}/sessions', exist_ok=True)
        
        # Create profile
        profile = {
            'student_id': student_id,
            'name': student_info.get('name', ''),
            'age': student_info.get('age'),
            'grade': student_info.get('grade', 4),
            'phone_number': phone_number,
            'interests': student_info.get('interests', []),
            'favorite_subjects': student_info.get('favorite_subjects', []),
            'learning_style': {
                'visual': 0.5,
                'auditory': 0.5,
                'kinesthetic': 0.5
            },
            'learning_preferences': student_info.get('learning_preferences', []),
            'created_at': datetime.utcnow().isoformat(),
            'last_updated': datetime.utcnow().isoformat(),
            'created_via': 'welcome_call'
        }
        
        # Create initial progress
        grade = student_info.get('grade', 4)
        progress = {
            'student_id': student_id,
            'grade_level': grade,
            'subjects': {
                'mathematics': {
                    'current_level': f'Grade {grade}',
                    'strengths': [],
                    'areas_for_improvement': [],
                    'next_steps': [f'Grade {grade} introduction']
                },
                'english': {
                    'current_level': f'Grade {grade}',
                    'strengths': [],
                    'areas_for_improvement': [],
                    'next_steps': [f'Grade {grade} reading']
                }
            },
            'created_at': datetime.utcnow().isoformat(),
            'last_updated': datetime.utcnow().isoformat()
        }
        
        # Save files
        with open(f'{student_dir}/profile.json', 'w') as f:
            json.dump(profile, f, indent=2)
        
        with open(f'{student_dir}/progress.json', 'w') as f:
            json.dump(progress, f, indent=2)
        
        # Add phone mapping
        self.phone_manager.add_phone_mapping(phone_number, student_id)
        
        logger.info(f"🎉 Created new student: {student_id} for {phone_number}")
        return student_id

# Add to main handler class
def process_welcome_call(self, phone_number, vapi_data):
    """Process welcome call for new student"""
    welcome_processor = WelcomeCallProcessor(self.phone_manager)
    return welcome_processor.process_welcome_call(phone_number, vapi_data)
```

### **Task 5: Initialize Phone Manager in Main Server**

#### **Update session-enhanced-server.py initialization**
```python
# Add to __init__ method or server startup
def __init__(self, timeout_minutes=10):
    # Existing initialization...
    super().__init__(timeout_minutes)
    
    # NEW: Initialize phone manager
    self.phone_manager = PhoneMappingManager()
    
    logger.info("📞 Phone mapping system initialized")
```

---

## 🧪 Testing Implementation

### **Test 1: New Student Phone Lookup**
```bash
# Test new phone number
curl -X POST http://localhost:3000/mcp/get-student-context \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+15551234567"}'

# Expected: new student onboarding context
```

### **Test 2: Welcome Call Processing**
```bash
# Simulate VAPI welcome call webhook
curl -X POST http://localhost:3000/webhook/vapi/session-complete \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "welcome_123",
    "phone_number": "+15551234567",
    "transcript": "AI: Hello! Whats your name? Student: Im Emma! AI: How old are you? Student: Im 9 years old and in 4th grade. I love animals and math!",
    "started_at": "2025-01-17T14:30:00Z",
    "ended_at": "2025-01-17T14:35:00Z"
  }'

# Expected: New student profile created, phone mapped
```

### **Test 3: Existing Student Lookup**
```bash
# Test same phone number after profile creation
curl -X POST http://localhost:3000/mcp/get-student-context \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+15551234567"}'

# Expected: Full Emma profile context returned
```

---

## 📋 Implementation Checklist

### **Files to Modify:**
- [ ] `session-enhanced-server.py` - Add phone manager and logic
- [ ] Create `data/phone_mapping.json` - Phone to student mapping
- [ ] Update `.env` - Ensure OpenAI API key for transcript analysis

### **New Classes to Add:**
- [ ] `PhoneMappingManager` - Handle phone to student mapping
- [ ] `WelcomeCallProcessor` - Process welcome calls and create students

### **Functions to Modify:**
- [ ] `handle_get_student_context()` - Support phone_number parameter
- [ ] `handle_vapi_webhook()` - Extract phone numbers and handle new students
- [ ] Add `get_existing_student_context()` and `get_new_student_context()`

### **New Functions to Add:**
- [ ] `extract_phone_from_vapi_data()` - Phone extraction from VAPI
- [ ] `process_welcome_call()` - Welcome call processing
- [ ] `extract_student_info_from_transcript()` - OpenAI transcript analysis
- [ ] `create_new_student()` - Automatic profile creation

### **Testing Required:**
- [ ] New phone number → onboarding context
- [ ] Welcome call → student profile creation
- [ ] Existing phone → full student context
- [ ] Phone mapping persistence across server restarts

This implementation will enable the complete phone-based onboarding workflow while maintaining backwards compatibility with existing student_id based calls.