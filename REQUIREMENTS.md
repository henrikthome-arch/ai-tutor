# AI Tutor System: Detailed Requirements

This document outlines the detailed requirements for the AI Tutor system, covering system functionality, data models, user experience, and legal compliance.

## 1. System Requirements

### 1.1. Architectural Requirements

-   **Application Factory Pattern**: The system must use Flask Application Factory pattern for clean, testable, and environment-aware application creation.
-   **Blueprint Architecture**: All routes must be organized into domain-specific blueprints (main, api) for modular development and maintenance.
-   **Service Layer Pattern**: Business logic must be separated from route handlers through a dedicated service layer.
-   **Repository Pattern**: Data access must be abstracted through repository classes for consistent database operations.
-   **Modular Design**: The system must maintain clear separation of concerns with models, services, repositories, and route handlers in separate modules.
-   **Environment Configuration**: Support for multiple environments (development, testing, production) with appropriate configuration classes.

### 1.2. Functional Requirements

-   **Multi-Channel Interaction**: Support for tutoring sessions via phone calls, with a design that accommodates future channels like web and mobile apps.
-   **Context-Aware Conversation**: Provide the AI tutor with relevant student context at the start of each session.
-   **Post-Session Processing**: Automatically process session transcripts to generate summaries and update student profiles and assessments.
-   **Flexible Curriculum Management**: The system must support a multi-layered curriculum model, allowing for default system-wide curriculums, school-specific curriculum templates, and student-level customization.
-   **School-Defined Curriculums**: School administrators must be able to define custom curriculum templates combining subjects from various standards (e.g., national, international, school-specific).
-   **Student-Level Subject Management**: Teachers and admins must be able to activate or deactivate specific subjects for AI tutoring for individual students and add guiding notes for the AI.
-   **AI-Powered Profile Extraction**: Automatically extract and update student information (age, grade, interests, learning preferences) from conversation transcripts using AI analysis.
-   **Conditional Prompt System**: The system must automatically detect call type (introductory vs tutoring) based on phone number lookup and apply appropriate AI prompts for analysis.
-   **JSON-Structured AI Responses**: All AI prompts must generate structured JSON output for consistent data extraction and processing.
-   **Call Type Detection**: Automatic determination of new vs returning students based on phone number presence in the database.
-   **VAPI Integration**: Complete integration with VAPI for voice call handling, including webhook processing, call data retrieval, and transcript analysis.
-   **AI-Driven Webhook Processing**: Post-processing of VAPI webhook calls must focus on having the AI deliver extracted data and analysis in structured JSON format. The system code should simply take this JSON data and move it to the database without complex transcript parsing or regex operations. This approach ensures simplicity, maintainability, and reliability by leveraging AI intelligence for data extraction rather than brittle text processing.
-   **Automatic Student Registration**: System must automatically create student profiles for new callers using phone number identification and conversation analysis.
-   **Automatic Default Curriculum Assignment**: Upon student creation, system must automatically generate student_subjects records from the system default curriculum, enabling immediate progress tracking.
-   **Phone Number Management**: Robust phone number normalization, mapping, and international format handling for student identification.
-   **Admin Dashboard**: A secure, web-based admin dashboard for system management with database browser functionality.
-   **API Layer**: A dedicated API layer (MCP Server) to serve data to all user interfaces.
-   **MCP Interaction Logging**: Comprehensive logging system for all MCP server communications, tracking request/response pairs, performance metrics, and system health indicators for debugging and monitoring purposes.
-   **Production Testing Tools**: Built-in testing infrastructure for VAPI integration and system health monitoring.
-   **Log Management**: Comprehensive PostgreSQL-based logging system with automatic 30-day retention and categorized event tracking.

### 1.2. Non-Functional Requirements

-   **Scalability**: An architecture designed for growth.
-   **Maintainability**: A well-structured, modular codebase.
-   **Security**: Secure data storage and encrypted communication.
-   **Reliability**: Robust error handling with database transaction rollback, comprehensive logging, and graceful error recovery.
-   **Low-Maintenance**: Use of managed services (Render.com, PostgreSQL) to minimize operational overhead.
-   **Environment Flexibility**: Support for development and production environments with appropriate configuration management.
-   **Health Monitoring**: Built-in health check endpoints and system status monitoring capabilities.
-   **Database Management**: Integrated database browser functionality for data inspection and troubleshooting.
-   **Real-time Event Tracking**: Live system event monitoring through PostgreSQL-based logging with categorized event types.
-   **Session Security**: Secure admin session management with password hashing and session timeout protection.
-   **Data Migration Support**: Database schema migration capabilities and automated table creation for deployment.
-   **GDPR Compliance**: The system must be designed and operated in adherence to the General Data Protection Regulation (GDPR), ensuring student data is handled with the highest standards of privacy and security.

### 1.3. Authentication and Access Control Requirements

-   **Token-Based API Authentication**: The system must provide secure, scope-limited access tokens for debugging, testing, and AI assistant integration.
-   **Admin Token Management**: The admin dashboard must include a token management interface for generating, viewing, and revoking access tokens.
-   **API Access Control**: All API endpoints must support token-based authentication with appropriate scope validation.
-   **MCP Server Integration**: The MCP server must accept and validate access tokens for secure data retrieval operations.
-   **AI Assistant Access**: The system must support providing temporary access tokens to AI assistants for debugging and troubleshooting purposes.
-   **Persistent Token Storage**: All tokens must be stored in PostgreSQL database to ensure they survive application deployments and restarts.

#### Token Requirements:
- **Scope-Based Authorization**: Tokens must be issued with specific scopes limiting access to relevant functionality:
  - `api:read` - Read access to API endpoints
  - `api:write` - Write access to API endpoints
  - `logs:read` - Access to system logs and diagnostics
  - `mcp:access` - Access to MCP server functionality
  - `admin:read` - Read access to admin dashboard data
- **Short-Lived Tokens**: Tokens must have configurable expiration times (1 hour to 7 days maximum) to limit security exposure
- **Token Revocation**: Admins must be able to immediately revoke active tokens
- **Secure Storage**: Tokens must be securely generated using cryptographic standards and stored as SHA-256 hashes in the database
- **Audit Trail**: Token generation, usage, and revocation must be logged for security auditing
- **Deployment Persistence**: Tokens must survive application deployments, restarts, and scaling operations through PostgreSQL storage
- **Usage Tracking**: The system must track token usage statistics including last used timestamp and total usage count
- **Automatic Cleanup**: Expired tokens must be automatically cleaned up from the database to maintain performance

#### Token Implementation:
- **Database Model**: A dedicated `Token` model with fields for hashed tokens, scopes, expiration, usage tracking, and metadata
- **Repository Pattern**: Token operations must use the repository pattern for clean database abstraction
- **Secure Hashing**: Raw tokens are hashed using SHA-256 before database storage for security
- **Transaction Safety**: Token operations must be wrapped in database transactions with proper error handling
- **Browser Integration**: Admin dashboard must support automatic token validation for seamless browser-based access

### 1.4. MCP Interaction Logging Requirements

The system must implement comprehensive logging of all Model Context Protocol (MCP) server interactions to support debugging, monitoring, and performance analysis.

#### 1.4.1. Core Logging Requirements
- **Complete Request/Response Tracking**: Log all incoming requests and outgoing responses for every MCP endpoint
- **Unique Request Identification**: Each request must receive a unique identifier for correlation between request and response
- **Performance Metrics**: Track request duration, response times, and success/failure rates for all endpoints
- **Session Correlation**: Link MCP interactions to user sessions when available for enhanced debugging
- **Token Association**: Associate logged interactions with authentication tokens for security auditing

#### 1.4.2. Data Storage Requirements
- **PostgreSQL Storage**: All MCP interaction logs stored in dedicated `mcp_interactions` table
- **JSON Payload Storage**: Store complete request and response payloads as JSONB for flexible querying
- **Indexing Strategy**: Implement appropriate database indexes for efficient querying by timestamp, endpoint, session, and status
- **Data Retention**: Configurable retention period with automatic cleanup of old interaction logs
- **Storage Optimization**: Balance detailed logging with storage efficiency through selective payload inclusion

#### 1.4.3. Monitoring and Analytics
- **Real-time Health Metrics**: Track system health indicators including stuck requests, completion rates, and average response times
- **Endpoint Statistics**: Generate per-endpoint analytics showing call frequency, success rates, and performance trends
- **Error Pattern Detection**: Identify and alert on patterns of failed requests or performance degradation
- **Usage Analytics**: Analyze MCP usage patterns to optimize system performance and identify bottlenecks

#### 1.4.4. Administrative Interface
- **Admin Dashboard Integration**: Dedicated admin interface for browsing and analyzing MCP interaction logs
- **Advanced Search Capabilities**: Filter interactions by endpoint, time range, status code, session, and token
- **Detailed Interaction Views**: Individual interaction detail pages showing complete request/response data with formatted JSON display
- **Export Functionality**: Markdown export capabilities for sharing interaction details with development teams
- **Cleanup Controls**: Admin interface for managing log retention and triggering manual cleanup operations

#### 1.4.5. Performance and Reliability
- **Asynchronous Logging**: MCP logging must not impact primary request/response performance
- **Fault Tolerance**: Logging failures must not affect MCP server functionality
- **Configurable Logging**: System administrators must be able to enable/disable logging and configure detail levels
- **Graceful Degradation**: System must continue operating normally even if logging infrastructure is unavailable

## 2. Core Data Entities & Functions

The system manages educational data through a comprehensive PostgreSQL database schema (detailed technical specification available in [`ARCHITECTURE.md`](ARCHITECTURE.md)). The core functional data entities include:

### 2.1. Educational Structure
-   **Schools**: Educational institutions with customizable curriculum templates
-   **Students**: Individual learners linked to schools and grade levels
-   **Curriculums**: Named educational frameworks (e.g., 'Cambridge Primary 2025')
-   **Subjects**: Master catalog of academic subjects across all curriculums
-   **Curriculum Composition**: Flexible mapping of subjects to curriculums by grade level (mandatory/optional)

### 2.2. Personalized Learning Management
-   **School Templates**: Default subject combinations per grade level for each school
-   **Student Curriculum**: Individual student enrollment in specific subjects with:
    -   AI tutoring activation controls per subject
    -   Curriculum status flag (is_in_use) to manage active vs replaced subjects
    -   Teacher guidance notes for AI personalization
    -   Comprehensive assessment data (weaknesses, mastery level, completion percentage, grades, motivational feedback)
    -   Dual progress tracking (numeric percentage + descriptive AI assessment)
    -   Separate comments from AI tutor and human teacher

### 2.3. Session & Assessment Tracking
-   **Tutoring Sessions**: Complete conversation records with AI-generated summaries
-   **Academic Assessments**: Subject-specific progress evaluations integrated into student_subjects records, including strengths, weaknesses, mastery levels, completion percentages, grades, and motivational feedback
-   **Progress Analytics**: Session metrics, daily statistics, and learning trend analysis

### 2.4. System Operations
-   **Authentication**: Secure token-based access control with scope limitations
-   **Audit Logging**: Comprehensive system event tracking for security and debugging
-   **Performance Monitoring**: Session quality metrics and system health indicators

## 3. Prompt Management

All prompts used in the system (for both VAPI and internal AI processing) are stored as individual Markdown files in the `ai-tutor/backend/ai_poc/prompts/` directory. This approach provides a clear separation of concerns and makes it easy to manage and version control the prompts.

### 3.0. VAPI Conversation Prompt

The primary VAPI conversation prompt that guides the AI tutor's interactions with students during phone calls is stored as [`vapi_conversation.md`](ai-tutor/backend/ai_poc/prompts/vapi_conversation.md). This prompt includes:

- **Student Recognition Logic**: Instructions for handling new vs. returning students
- **Conversation Guidelines**: Age-appropriate communication patterns and session flow
- **Session Management**: Critical timing controls to prevent call cutoffs
- **Technical Integration**: Silent function call handling and context retrieval
- **Child-Friendly Interaction**: Specific guidance for engaging with young learners

This prompt serves as the core behavioral template for all voice-based tutoring sessions and is version-controlled alongside other system prompts for consistency and maintainability.

### 3.1. Conditional Prompt System Requirements

The system must implement a conditional prompt selection mechanism to provide appropriate AI analysis based on the caller's status (new vs returning student).

#### 3.1.1. Call Type Detection Requirements
- **Phone Number Lookup**: System must query PostgreSQL database to check if caller's phone number exists in the students table
- **Call Classification**:
  - **Introductory Call**: When phone number is NOT found in students table (new student)
  - **Tutoring Session**: When phone number IS found in students table (existing student)
- **Database Query Performance**: Phone number lookup must be optimized with appropriate database indexing
- **Error Handling**: System must gracefully handle database connection issues during call type detection

#### 3.1.2. Prompt Template Requirements
- **Template Organization**: Prompts must be organized by call type in the file system
- **Introductory Call Prompts**:
  - `introductory_analysis.md`: New student profile creation and initial assessment
  - Focus on student discovery, learning preferences, and initial capability assessment
- **Tutoring Session Prompts**:
  - `session_analysis.md`: General tutoring session analysis for existing students
  - `math_analysis.md`: Mathematics-focused analysis
  - `reading_analysis.md`: Reading comprehension analysis
  - `quick_assessment.md`: Rapid capability assessment
  - `progress_tracking.md`: Learning progress evaluation

#### 3.1.3. JSON Response Format Requirements
- **Standardized Structure**: All prompts must generate JSON responses with consistent field naming to enable direct database storage without complex processing
- **AI-Driven Data Extraction**: The AI must perform all data extraction, analysis, and structuring, delivering ready-to-store JSON data that requires no additional parsing, regex operations, or complex text processing by the application code
- **Required JSON Fields**:
  - `student_profile`: Student information and characteristics
  - `session_analysis`: Session content analysis and insights
  - `recommendations`: Action items and next steps
  - `metadata`: Call type, confidence scores, and processing timestamps
- **Data Validation**: System must validate JSON structure before database storage
- **Error Recovery**: Invalid JSON responses must be logged and trigger fallback processing
- **Schema Versioning**: JSON schema must support future extensions without breaking existing functionality
- **Processing Simplicity**: Application code should perform simple JSON-to-database mapping without transcript analysis, pattern matching, or data interpretation

#### 3.1.4. Prompt Selection Logic Requirements
- **Automatic Detection**: System must automatically select appropriate prompts without manual intervention
- **Fallback Mechanism**: If call type detection fails, system must default to general session analysis
- **Logging**: All prompt selection decisions must be logged for debugging and monitoring
- **Performance**: Prompt selection must complete within 100ms to avoid call processing delays
- **Context Injection**: Selected prompts must receive appropriate student context based on call type

#### 3.1.5. Integration Requirements
- **VAPI Webhook Integration**: Call type detection must integrate seamlessly with existing VAPI webhook processing
- **Transcript Analyzer Updates**: Existing transcript analyzer must be updated to use conditional prompt selection
- **AI Provider Compatibility**: JSON output format must be compatible with both OpenAI and Anthropic providers
- **Database Storage**: Structured JSON responses must be stored efficiently in PostgreSQL
- **Admin Dashboard**: Admin interface must display call type information and prompt selection results

## 4. User Experience (UX)

### 3.1. Student User Experience

The student's interaction is designed to be simple, natural, and personalized, providing a consistent experience across all communication channels.

### 3.2. Admin User Experience

The admin dashboard will be the central control panel for the system.
- **Clean Navigation**: The interface will have a logical and intuitive main navigation structure.
- **Dashboard Overview**: A summary of key system metrics.
- **Student Management**: Full CRUD operations for student profiles.
- **School Management**: Full CRUD operations for schools and curriculums.
- **Session Review**: Access to session transcripts and AI-generated summaries.
- **Progress Monitoring**: Detailed view of student assessments.
- **Log Viewer**: A tool for viewing and filtering system logs.

## 4. Admin UI Requirements

### 5.1. Curriculum Management Interface

#### 5.1.1. CSV Upload System
- **Generic File Upload Location**: A dedicated "System > File Uploads" section in the admin dashboard
- **Supported Upload Types**:
  - **Curriculums CSV Format**: `name,description,is_default`
    - Example: `"Cambridge Primary 2025","Cambridge Primary Curriculum for 2025",false`
  - **Subjects CSV Format**: `name,description`
    - Example: `"Mathematics","Mathematical concepts and problem solving"`
  - **Curriculum Details CSV Format**: `curriculum_name,subject_name,grade_level,is_mandatory,goals_description`
    - Example: `"Cambridge Primary 2025","Mathematics",4,true,"Develop numerical fluency and problem-solving skills"`
  - **Schools CSV Format**: `name,country,city,description,core_values`
    - Example: `"International School Athens","Greece","Athens","Premier international education","Excellence, Integrity, Global Citizenship"`
- **Upload Validation**: Real-time validation with clear error messages for format issues
- **File Processing**: Batch processing with progress indicators and detailed success/failure reports

#### 5.1.2. Curriculum Data Management
- **View All Types**: Tabular views for curriculums, subjects, and curriculum details with search and filtering
- **Individual Entry Deletion**: Ability to delete individual entries with confirmation dialogs
- **Bulk Operations**: Select multiple entries for deletion or status changes
- **Data Integrity Checks**: Prevent deletion of entries that would break foreign key relationships

### 5.2. School Default Curriculum Management

#### 5.2.1. School Template Configuration
- **Per-School Grade Templates**: Interface to define which curriculum details apply to each grade at each school
- **Grade-Level Views**: Organized by grade level showing all subjects for that grade
- **Template Copying**: Ability to copy curriculum templates between grades or schools
- **Template Validation**: Ensure mandatory subjects are included for each grade

#### 5.2.2. Student Curriculum Assignment
- **Automatic Default Assignment**: Upon student creation, system automatically creates student_subjects records from system default curriculum (all marked as is_in_use=true)
- **Apply School Default**: One-click application of school's default curriculum for a student's grade
  - **Process**: Copy all entries from `school_default_subjects` for the student's grade to `student_subjects`
  - **Replacement Mode**: Mark existing system default subjects as is_in_use=false, new school subjects as is_in_use=true
  - **Conflict Handling**: Options to merge with existing subjects or replace entirely
- **Manual Subject Management**:
  - **Add Subjects**: Filter by curriculum and grade to add individual subjects to a student
  - **Remove Subjects**: Remove individual subjects from student's curriculum or toggle is_in_use flag
  - **Subject Status**: Toggle `is_active_for_tutoring` and `is_in_use` for individual subjects
  - **Progress Tracking**: Update `progress_percentage` (0-100% slider) and comprehensive assessment fields
  - **Assessment Management**: Edit all assessment fields including weaknesses, mastery_level, comments_tutor, comments_teacher, completion_percentage, grade_score, grade_motivation

### 5.3. Student Progress Management Interface

#### 5.3.1. Individual Student Views
- **Subject Progress Dashboard**: Visual progress indicators (progress bars, charts) for each active subject (is_in_use=true)
- **Comprehensive Assessment Editor**:
  - Rich text editor for AI assessment (ai_assessment field)
  - Separate fields for AI tutor comments (comments_tutor) and teacher comments (comments_teacher)
  - Weaknesses identification field (weaknesses)
  - Mastery level dropdown (mastery_level)
  - Completion percentage slider (completion_percentage)
  - Grade score field (grade_score)
  - Grade motivation text area (grade_motivation)
- **AI Tutor Notes**: Display and edit AI-generated notes about student progress (ai_tutor_notes)
- **Subject Status Management**: Toggle is_in_use and is_active_for_tutoring flags
- **Progress History**: Timeline view of progress changes over time for all assessment fields
- **Curriculum Status Filter**: View active subjects (is_in_use=true) vs all subjects including replaced ones

#### 5.3.2. Bulk Progress Management
- **Grade-Level Views**: See progress across all students in a grade for specific subjects
- **Export Capabilities**: Generate progress reports in PDF/Excel format
- **Progress Analytics**: Charts showing class averages, individual progress trends

### 5.4. File Management System

#### 5.4.1. Upload History and Management
- **Upload Log**: History of all file uploads with timestamps, user info, and processing results
- **File Validation Results**: Detailed reports of what was successfully imported vs. errors
- **Rollback Capability**: Ability to undo recent imports if errors are discovered
- **Template Downloads**: Provide CSV templates for each upload type with proper formatting

#### 5.4.2. Data Export Capabilities
- **Full Data Export**: Export complete curriculum structure to CSV/Excel
- **Selective Export**: Export filtered subsets (e.g., specific school's curriculum)
- **Backup Functionality**: Regular automated exports for data backup purposes

## 6. Default Curriculum Requirements

### 6.1. Cambridge Primary 2025 Default Curriculum

The system must provide a comprehensive default curriculum that is automatically assigned to all new students.

#### 6.1.1. Default Curriculum Data Source
- **Data File**: Cambridge Primary 2025 curriculum stored as tab-separated values (TSV) at [`ai-tutor/data/curriculum/cambridge_primary_2025.txt`](ai-tutor/data/curriculum/cambridge_primary_2025.txt)
- **Format Requirements**: TSV format with headers: Grade, Subject, Mandatory, Details
- **Content Coverage**: Complete curriculum for Grades 1-6 including core subjects (English, Mathematics, Science) and optional subjects (Global Perspectives, Computing/ICT, Art & Design, Music, Physical Education)
- **Data Integrity**: Each curriculum entry must include grade level, subject name, mandatory status, and detailed learning objectives

#### 6.1.2. Automatic Default Assignment
- **Student Creation Trigger**: Upon creation of any new student, the system must automatically generate `student_subjects` records for all grade-appropriate subjects from the default curriculum
- **Subject Status**: All default subjects initially marked as `is_in_use=true` and `is_active_for_tutoring=false`
- **Grade-Level Filtering**: Only subjects appropriate for the student's grade level should be assigned
- **Comprehensive Coverage**: Both mandatory and optional subjects must be assigned to provide complete curriculum coverage

#### 6.1.3. Curriculum Import Process
- **Startup Import**: System must automatically import Cambridge curriculum data on application startup if default curriculum doesn't exist
- **Idempotent Operation**: Import process must be safe to run multiple times without creating duplicates
- **Error Handling**: Import failures must be logged with detailed error messages and system must continue to operate
- **Data Validation**: TSV data must be validated for format compliance and data integrity before import

### 6.2. Curriculum Management Interface Requirements

#### 6.2.1. Curriculum Overview Display
- **Curriculum List**: Admin interface must display all available curricula with name, description, and default status
- **Default Curriculum Indicator**: Clear visual indication of which curriculum is marked as system default
- **Curriculum Statistics**: Display count of subjects and grade levels covered by each curriculum
- **Edit Capabilities**: Allow editing of curriculum name, description, and default status

#### 6.2.2. Curriculum Detail Management
- **Subject List View**: Display all subjects for a curriculum organized by grade level
- **Detail Management**: Add, edit, and delete curriculum detail entries (subject-grade combinations)
- **Mandatory Status**: Toggle mandatory/optional status for curriculum subjects
- **Learning Objectives**: Edit detailed learning objectives and goals for each subject-grade combination
- **Bulk Operations**: Support for bulk editing or importing curriculum details

#### 6.2.3. Default Curriculum Management
- **Single Default**: System must enforce exactly one curriculum marked as default
- **Default Switch**: When changing default curriculum, automatically reassign all students without school-specific curricula
- **Impact Warning**: Display warning when changing default curriculum about potential student impact
- **Rollback Capability**: Ability to revert default curriculum changes if needed

### 6.3. Student Curriculum Assignment Requirements

#### 6.3.1. Automatic Assignment Logic
- **New Student**: Automatically assign complete default curriculum upon student creation
- **Grade-Appropriate**: Only assign subjects appropriate for student's grade level
- **School Override**: When student is assigned to school with custom curriculum, mark default subjects as `is_in_use=false` and add school subjects as `is_in_use=true`
- **AI Tutoring Control**: Teachers must be able to toggle `is_active_for_tutoring` for individual subjects

#### 6.3.2. Curriculum Transition Management
- **School Assignment**: When student joins school, replace default curriculum with school-specific curriculum
- **School Departure**: When student leaves school, revert to default curriculum
- **Grade Progression**: Automatically update student subjects when grade level changes
- **Progress Preservation**: Maintain assessment data and progress when transitioning between curricula

### 6.4. File Management Requirements

#### 6.4.1. Data File Standards
- **File Location**: All curriculum data files stored in [`ai-tutor/data/curriculum/`](ai-tutor/data/curriculum/) directory
- **Naming Convention**: Descriptive file names indicating curriculum type and version (e.g., `cambridge_primary_2025.txt`)
- **Format Consistency**: All curriculum files must follow same TSV format with standard headers
- **Version Control**: Curriculum files tracked in Git for change management and rollback capability

#### 6.4.2. Import Validation Requirements
- **Header Validation**: Verify required columns (Grade, Subject, Mandatory, Details) are present
- **Data Type Validation**: Ensure grade is numeric, mandatory is boolean, details are non-empty
- **Duplicate Detection**: Prevent duplicate curriculum-subject-grade combinations
- **Error Reporting**: Provide detailed error messages for validation failures with line numbers

#### 6.4.3. Backup and Export Requirements
- **Curriculum Export**: Export curriculum data to TSV format for backup
- **Complete Export**: Export all curricula or individual curriculum selection
- **Import History**: Track all curriculum imports with timestamps and success/failure status
- **Data Integrity**: Exported data must be importable without modification
