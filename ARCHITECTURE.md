# AI Tutor System: System Architecture

This document outlines the system architecture for the AI Tutor platform, detailing components, data flow, security measures, and deployment patterns.

## 1. System Overview

The AI Tutor system is a cloud-native, PostgreSQL-backed platform that provides AI-powered tutoring services via voice calls. The system automatically processes conversations, manages student profiles, and provides administrative oversight through a comprehensive web dashboard.

### 1.1. Architecture Principles

- **Cloud-Native**: Designed for deployment on managed cloud platforms (Render.com)
- **Database-Centric**: PostgreSQL as the single source of truth for all persistent data
- **Microservice-Ready**: Modular design with clear separation of concerns
- **API-First**: All functionality exposed through well-defined APIs
- **Security-First**: Comprehensive authentication, authorization, and audit capabilities

## 2. System Components

### 2.1. Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Tutor System                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Admin Web     │  │   Flask API     │  │   MCP Server    │  │
│  │   Dashboard     │  │    Backend      │  │   (Node.js)     │  │
│  │   (Flask)       │  │                 │  │                 │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│           │                     │                     │          │
│           └─────────────────────┼─────────────────────┘          │
│                                 │                                │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              PostgreSQL Database                            │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────┐  │  │
│  │  │Students │ │Sessions │ │ Tokens  │ │ Logs    │ │School │  │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └───────┘  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                 │                                │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                  VAPI Integration                           │  │
│  │              (External Service)                             │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.1.1. Flask Backend (`ai-tutor/backend/`)
- **Purpose**: Main application server providing web UI and APIs
- **Framework**: Flask with SQLAlchemy ORM
- **Responsibilities**:
  - Admin dashboard web interface
  - RESTful API endpoints
  - VAPI webhook processing
  - Student profile management
  - Session data processing
  - Token-based authentication
  - AI prompt management via file-based system

#### 2.1.2. MCP Server (`mcp-server/`)
- **Purpose**: Model Context Protocol server for external data access
- **Framework**: Node.js with TypeScript
- **Responsibilities**:
  - Secure data retrieval API
  - Token-based authentication validation
  - Student and session data access
  - Integration with AI assistants

#### 2.1.3. PostgreSQL Database
- **Purpose**: Central data store for all system information
- **Deployment**: Managed PostgreSQL on Render.com
- **Responsibilities**:
  - Student profiles and progress tracking
  - Session transcripts and summaries
  - Authentication tokens (persistent storage)
  - System logs and analytics
  - Curriculum and school data

#### 2.1.4. AI Analysis System (`ai-tutor/backend/ai_poc/`)
- **Purpose**: AI-powered analysis of tutoring session transcripts with conditional prompt selection
- **Framework**: Python with OpenAI/Anthropic API integration
- **Responsibilities**:
  - File-based prompt management (Markdown templates)
  - Conditional prompt selection based on call type (introductory vs tutoring)
  - Multi-provider AI analysis (OpenAI, Anthropic)
  - JSON-structured response parsing and extraction
  - Session quality validation
  - Student profile enhancement from transcripts
  - Call type detection (new vs returning students)

### 2.2. External Integrations

#### 2.2.1. VAPI (Voice API)
- **Purpose**: Voice call handling and transcript generation
- **Integration**: Webhook-based real-time processing
- **Data Flow**: Call → Transcript → Student Profile → Session Summary

## 3. Data Architecture

### 3.1. Complete Database Schema

The data model is implemented in PostgreSQL with a comprehensive schema supporting curriculum management, session tracking, authentication, and system monitoring.

```mermaid
erDiagram
    %% Core Educational Entities
    schools {
        int id PK
        string name
        string country
        string city
        text description
        int default_curriculum_id FK "Optional: School's preferred curriculum"
    }

    students {
        int id PK
        string first_name
        string last_name
        date date_of_birth
        string phone_number
        int school_id FK
        int grade_level
        string student_type
        timestamp created_at
        timestamp updated_at
    }

    student_progress {
        int id PK
        int student_id FK
        string subject
        float proficiency_level
        timestamp last_updated
        timestamp created_at
    }

    %% Curriculum System
    curriculums {
        int id PK
        string name
        text description
        bool is_default "The system-wide default curriculum"
        timestamp created_at
    }

    subjects {
        int id PK
        string name "e.g., 'Mathematics', 'History'"
        text description
        timestamp created_at
    }

    curriculum_details {
        int id PK
        int curriculum_id FK
        int subject_id FK
        int grade_level
        bool is_mandatory
    }

    school_default_subjects {
        int id PK
        int school_id FK
        int curriculum_detail_id FK "Default subject template for the school"
        int grade_level "Grade level this applies to"
    }

    student_subjects {
        int id PK
        int student_id FK
        int curriculum_detail_id FK "Links to a specific subject in a specific curriculum"
        bool is_active_for_tutoring "Can be toggled by teachers/parents"
        text teacher_notes "For guiding the AI on focus areas"
        text ai_tutor_notes "AI's own notes on student progress"
        float progress_percentage "Numeric progress from 0.0 to 1.0 (0% to 100%)"
        text teacher_assessment "Descriptive assessment by teacher about student's current status"
        timestamp created_at
        timestamp updated_at
    }

    %% Session Management
    sessions {
        int id PK
        int student_id FK
        string session_type
        timestamp start_datetime
        int duration_seconds
        text transcript
        text summary
        timestamp created_at
    }

    assessments {
        int id PK
        int student_id FK
        string grade
        string subject
        text strengths
        text weaknesses
        string mastery_level
        text comments_tutor
        text comments_teacher
        float completion_percentage
        string grade_score
        text grade_motivation
        timestamp last_updated
        timestamp created_at
    }

    %% System Infrastructure
    system_logs {
        int id PK
        timestamp timestamp
        string level
        string category
        text message
        text metadata
    }

    tokens {
        int id PK
        string token_hash
        string scopes
        timestamp expires_at
        timestamp created_at
        timestamp last_used
        int usage_count
        bool is_active
    }

    %% Analytics & Metrics
    session_metrics {
        int id PK
        int session_id FK
        int duration_seconds
        float satisfaction_score
        timestamp created_at
    }

    daily_stats {
        int id PK
        date date
        int total_sessions
        float avg_duration
        int total_users
        int active_students
    }

    %% Relationships
    schools ||--o{ students : "enrolls"
    schools ||--o{ school_default_subjects : "defines templates"
    schools }o--|| curriculums : "uses default"
    
    students ||--o{ student_progress : "has progress records"
    students ||--o{ student_subjects : "enrolled in"
    students ||--o{ sessions : "participates in"
    students ||--o{ assessments : "has"
    
    curriculums ||--|{ curriculum_details : "contains"
    subjects ||--|{ curriculum_details : "part of curriculum"
    curriculum_details ||--o{ student_subjects : "instantiated as"
    curriculum_details ||--o{ school_default_subjects : "template includes"
    
    sessions ||--o| session_metrics : "measured by"
```

### 3.2. System Data Architecture Overview

The database schema supports four primary functional areas:

#### 3.2.1. Educational Structure Management
-   **Schools & Students**: Core institutional relationships with comprehensive student profiles including learning psychology, preferences, and family context
-   **Curriculum System**: Flexible, multi-layered curriculum management supporting system defaults, school-specific templates, and individual student customization
-   **Subject Enrollment**: Granular subject-level management with AI tutoring controls and progress tracking per subject

#### 3.2.2. Session & Learning Analytics
-   **Session Recording**: Complete conversation transcripts with AI-generated summaries and metadata
-   **Assessment Tracking**: Subject-specific assessments tracking strengths, weaknesses, and mastery levels
-   **Progress Monitoring**: Dual-tracking system with numeric progress percentages and descriptive teacher assessments
-   **Performance Metrics**: Session quality metrics, duration tracking, and satisfaction scoring

#### 3.2.3. System Operations & Security
-   **Authentication Framework**: Secure token-based access control with scope-based permissions
-   **Audit & Logging**: Comprehensive system event logging with categorized retention and real-time monitoring
-   **Analytics Infrastructure**: Daily statistics, usage patterns, and system performance tracking

#### 3.2.4. AI Integration Architecture
-   **Student Profile Integration**: Rich student profiles with learning psychology data feed directly into AI tutoring sessions
-   **Session Context Loading**: Complete student context (curriculum, progress, preferences) available to AI tutor
-   **Post-Session Processing**: AI analysis updates student profiles, assessments, and learning recommendations
-   **Adaptive Learning**: AI recommendations inform curriculum adjustments and teaching strategies

#### 3.2.5. Key Workflows

**Student Enrollment Workflow:**
1. New student creation with basic demographics
2. School's default curriculum template automatically copied to student subjects
3. Individual subject customization and AI tutoring activation
4. Continuous profile enhancement through AI session analysis

**Tutoring Session Workflow:**
1. Student call triggers profile and curriculum context loading
2. AI tutor receives complete student context for personalized interaction
3. Session transcript captured with quality metrics
4. Post-session AI analysis updates progress tracking and recommendations

**Curriculum Management Workflow:**
1. System-wide curriculum definitions with subject mappings
2. School-specific curriculum template creation
3. Grade-level default subject assignment
4. Individual student curriculum customization and progress tracking

### 3.2. Repository Pattern

All database operations are abstracted through repository classes:
- `StudentRepository`: Student CRUD operations
- `SessionRepository`: Session management
- `TokenRepository`: Authentication token management
- `SystemLogRepository`: Event logging and retrieval

## 4. Security Architecture

### 4.1. Authentication & Authorization

#### 4.1.1. Admin Dashboard Authentication
- **Method**: Password-based with secure session management
- **Session Storage**: Server-side session with timeout protection
- **Password Security**: BCrypt hashing with salt

#### 4.1.2. API Token Authentication
- **Purpose**: Secure access for debugging, testing, and AI integration
- **Storage**: PostgreSQL with SHA-256 hashed tokens
- **Scopes**: Granular permission system
  - `api:read` - Read access to API endpoints
  - `api:write` - Write access to API endpoints  
  - `logs:read` - Access to system logs
  - `mcp:access` - MCP server functionality
  - `admin:read` - Admin dashboard data

#### 4.1.3. Token Security Features
- **Persistent Storage**: Tokens survive deployments via PostgreSQL
- **Secure Generation**: Cryptographically secure random tokens
- **Hashed Storage**: Only SHA-256 hashes stored in database
- **Expiration Control**: Configurable token lifetime (1 hour - 7 days)
- **Usage Tracking**: Last used timestamp and usage count
- **Automatic Cleanup**: Expired tokens removed automatically
- **Revocation**: Immediate token invalidation capability

### 4.2. Data Security
- **Encryption**: All data encrypted in transit (HTTPS)
- **Database Security**: Managed PostgreSQL with access controls
- **GDPR Compliance**: Privacy-by-design data handling
- **Audit Trail**: Comprehensive logging of all system operations

## 5. API Architecture

### 5.1. RESTful API Design
- **Base URL**: `/api/v1/`
- **Authentication**: Bearer token in Authorization header
- **Content Type**: JSON request/response format
- **Error Handling**: Consistent HTTP status codes and error messages

### 5.2. Key API Endpoints
```
GET  /api/v1/students          # List students
POST /api/v1/students          # Create student
GET  /api/v1/students/{id}     # Get student details
PUT  /api/v1/students/{id}     # Update student

GET  /api/v1/sessions          # List sessions
GET  /api/v1/sessions/{id}     # Get session details

POST /api/v1/vapi/webhook      # VAPI webhook endpoint
GET  /api/v1/logs              # System logs (with filtering)
```

### 5.3. MCP Server API
- **Protocol**: Model Context Protocol over stdio/HTTP
- **Authentication**: Token-based with scope validation
- **Resources**: Student data, session transcripts, system logs
- **Tools**: Data query and analysis capabilities

## 6. Data Flow Architecture

### 6.1. Voice Call Processing Flow
```
1. Student calls → VAPI
2. VAPI processes call → Generates transcript
3. VAPI webhook → Flask backend
4. Backend processes transcript:
   - Identifies/creates student profile
   - Creates session record
   - Triggers AI post-processing
5. AI analysis → Updates student assessment
6. Session summary generated
7. Data stored in PostgreSQL
```

### 6.3. AI Prompt Management Flow
```
1. System startup → FileBasedPromptManager loads all .md files
2. Call processing → Phone number lookup to determine call type
3. Conditional prompt selection:
   - New student (phone not in system) → Introductory call prompts
   - Existing student (phone in system) → Tutoring session prompts
4. Template lookup → Load appropriate prompt based on call type
5. Parameter injection → Template formatting with student context
6. AI provider call → Formatted prompt sent to OpenAI/Anthropic
7. JSON response parsing → Structured data extraction
8. Database storage → Results saved to PostgreSQL
```

### 6.4. Conditional Prompt System Architecture

#### 6.4.1. Call Type Detection Logic
```
1. VAPI webhook receives call data with phone number
2. Student lookup in PostgreSQL database:
   - SELECT * FROM students WHERE phone_number = caller_phone
3. Call type determination:
   - If student exists → TUTORING_SESSION
   - If student not found → INTRODUCTORY_CALL
4. Prompt selection based on call type
```

#### 6.4.2. Prompt Template Organization
```
ai-tutor/backend/ai_poc/prompts/
├── introductory_analysis.md     # New student profile creation
├── session_analysis.md          # General tutoring session analysis
├── math_analysis.md             # Mathematics-focused analysis
├── reading_analysis.md          # Reading comprehension analysis
├── quick_assessment.md          # Rapid capability assessment
└── progress_tracking.md         # Learning progress evaluation
```

#### 6.4.3. JSON Response Format
All prompts generate structured JSON responses with standardized fields:
```json
{
  "student_profile": {
    "name": "string",
    "grade_level": "string",
    "subjects_discussed": ["array"],
    "learning_style": "string"
  },
  "session_analysis": {
    "key_topics": ["array"],
    "understanding_level": "string",
    "areas_for_improvement": ["array"],
    "strengths": ["array"]
  },
  "recommendations": {
    "next_steps": ["array"],
    "focus_areas": ["array"],
    "suggested_resources": ["array"]
  },
  "metadata": {
    "call_type": "introductory|tutoring",
    "confidence_score": "number",
    "analysis_timestamp": "string"
  }
}
```

### 6.2. Admin Dashboard Flow
```
1. Admin login → Session authentication
2. Dashboard queries → Repository layer
3. Repository → PostgreSQL queries
4. Data formatting → Web interface
5. Admin actions → API calls → Database updates
```

### 6.3. Token Authentication Flow
```
1. Admin generates token → Token stored in PostgreSQL (hashed)
2. Client/AI assistant → API request with token
3. Token validation → Database lookup and scope check
4. Authorized request → Repository layer → Response
5. Usage tracking → Token statistics updated
```

## 7. Deployment Architecture

### 7.1. Render.com Deployment
- **Platform**: Render.com managed services
- **Web Service**: Flask application (auto-deploy from Git)
- **Database**: Managed PostgreSQL service
- **Environment**: Production-ready with health checks

### 7.2. Environment Configuration
- **Development**: Local SQLite for rapid development
- **Production**: Managed PostgreSQL with connection pooling
- **Configuration**: Environment variables for all secrets
- **Logging**: Centralized logging to PostgreSQL

### 7.3. Deployment Features
- **Auto-Deploy**: Git-based deployment triggers
- **Health Checks**: Built-in endpoint monitoring
- **Database Migrations**: Automatic schema updates
- **Token Persistence**: Tokens survive all deployments
- **Zero-Downtime**: Managed service ensures availability

## 8. Monitoring & Observability

### 8.1. System Logging
- **Storage**: PostgreSQL-based log storage
- **Categories**: VAPI, Database, Authentication, System, Error
- **Retention**: Automatic 30-day log cleanup
- **Filtering**: Advanced log search and filtering
- **Real-time**: Live system event monitoring

### 8.2. Performance Monitoring
- **Database Performance**: Query optimization and indexing
- **API Response Times**: Endpoint performance tracking
- **Token Usage**: Authentication statistics and monitoring
- **Session Analytics**: Student engagement metrics

### 8.3. Health Monitoring
- **Application Health**: Built-in health check endpoints
- **Database Connectivity**: Connection pool monitoring
- **External Service Status**: VAPI integration monitoring
- **Error Rate Tracking**: Automated error detection and alerting

## 9. Future Architecture Considerations

### 9.1. Scalability
- **Database Scaling**: Read replicas for query optimization
- **Service Decomposition**: Microservice extraction as needed
- **Caching Layer**: Redis for frequently accessed data
- **Load Balancing**: Multiple application instances

### 9.2. Integration Expansion
- **Multi-Channel Support**: Web and mobile app integration
- **Additional AI Services**: Extended AI processing capabilities
- **Third-Party APIs**: School system integrations
- **Analytics Platform**: Advanced reporting and insights

### 9.3. Security Enhancements
- **OAuth2 Integration**: External authentication providers
- **Role-Based Access**: Enhanced permission system
- **API Rate Limiting**: Request throttling and abuse prevention
- **Compliance Automation**: GDPR and privacy compliance tools