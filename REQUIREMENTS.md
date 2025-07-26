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
- **Production Testing Tools**: Built-in testing infrastructure for VAPI integration and system health monitoring.
- **Log Management**: Comprehensive PostgreSQL-based logging system with automatic 30-day retention and categorized event tracking.
- **AI Tutor Performance Assessment**: Automated evaluation of AI tutor effectiveness using evidence-based tutoring guidelines to generate performance assessments and improvement recommendations.

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

## 7. AI Tutor Performance Assessment Requirements

### 7.1. Functional Requirements

#### 7.1.1. Automated Assessment Trigger
- **Post-Session Processing**: System must automatically initiate tutor performance assessment after each completed tutoring session (excluding welcome/introductory sessions)
- **Session Validation**: Assessment must only process sessions with valid student_id and sufficient transcript content (minimum 50 characters)
- **Non-Blocking Operation**: Assessment process must not interfere with primary session processing or user experience
- **Error Isolation**: Assessment failures must not impact session completion or data storage

#### 7.1.2. Data Source Integration
- **Session Transcript**: Complete conversation transcript between student and AI tutor
- **Tutoring Guidelines**: Evidence-based best practices from dedicated guidelines file
- **Student Profile**: Complete student context including demographics, interests, learning preferences, and historical data
- **AI Tutor Prompt**: Current prompt system configuration used during the session
- **Comprehensive Context**: All data sources must be successfully gathered before assessment generation

#### 7.1.3. Evidence-Based Assessment Criteria
The system must evaluate AI tutor performance against research-backed tutoring strategies:
- **Storytelling and Narrative Learning**: Use of stories and examples to engage students
- **Gamification Elements**: Implementation of game-like elements and motivational rewards
- **Interactive Dialogue**: Socratic questioning, student engagement, and two-way conversation
- **Spaced Repetition**: Strategic review and reinforcement of previously learned material
- **Novelty and Variety**: Maintenance of student attention through varied activities and approaches
- **Scaffolding and Adaptive Challenge**: Appropriate difficulty level and support provision
- **Positive Reinforcement**: Encouragement, praise, and confidence-building techniques
- **Age-Appropriate Strategies**: Developmental stage considerations and suitable communication style
- **Personalization**: Adaptation to individual student interests, learning style, and needs

#### 7.1.4. Assessment Output Requirements
- **Structured JSON Response**: AI must provide assessment in predefined JSON format with two required fields
- **Performance Evaluation**: Detailed paragraph(s) analyzing what went well and areas for improvement
- **Actionable Recommendations**: Specific, implementable suggestions for prompt and approach improvements
- **Evidence-Based Analysis**: Assessment must reference specific examples from the session transcript
- **Constructive Feedback**: Balanced evaluation highlighting both strengths and growth opportunities

### 7.2. Technical Requirements

#### 7.2.1. Database Schema Updates
- **Sessions Table Extension**: Add `tutor_assessment` and `prompt_suggestions` TEXT columns to sessions table
- **Data Integrity**: Assessment data must be stored atomically with proper transaction management
- **Null Handling**: Assessment fields must gracefully handle missing or failed assessments
- **Migration Support**: Schema changes must be deployable without data loss

#### 7.2.2. Service Architecture
- **TutorAssessmentService**: Dedicated service class for assessment workflow orchestration
- **Modular Design**: Clear separation of data gathering, AI interaction, and result storage
- **Error Handling**: Comprehensive error catching with detailed logging and graceful degradation
- **MCP Integration**: Full logging of assessment workflow for monitoring and debugging

#### 7.2.3. AI Integration Requirements
- **Model Selection**: Use GPT-4 or equivalent high-quality language model for assessment generation
- **Prompt Engineering**: Comprehensive assessment prompt incorporating all data sources and evaluation criteria
- **Response Validation**: JSON structure validation before database storage
- **Timeout Handling**: Appropriate timeouts for AI model calls with fallback strategies
- **Rate Limiting**: Respect AI provider rate limits and implement retry mechanisms

#### 7.2.4. File Management
- **Guidelines Storage**: Tutoring guidelines stored in organized file structure within application
- **Resource Access**: Reliable file reading with proper error handling for missing resources
- **Path Management**: Platform-independent file path handling for different deployment environments
- **Version Control**: Guidelines and resources tracked in version control for change management

### 7.3. User Interface Requirements

#### 7.3.1. Admin Dashboard Integration
- **Session Detail View**: Dedicated section for displaying tutor assessment results
- **Visual Design**: Clear, professional presentation with color-coded sections and intuitive navigation
- **Assessment Status**: Visual indicators showing assessment availability and processing status
- **Copy Functionality**: Easy copying of assessment text for sharing and analysis
- **Quick Navigation**: Scroll-to functionality for easy access to assessment content

#### 7.3.2. Assessment Display Features
- **Performance Evaluation Section**: Formatted display of AI-generated tutor assessment
- **Improvement Suggestions Section**: Clear presentation of actionable recommendations
- **Status Indicators**: Visual confirmation of assessment completion or processing state
- **Responsive Design**: Proper display across different screen sizes and devices
- **Accessibility**: Screen reader compatible and keyboard navigable

#### 7.3.3. Data Export and Sharing
- **Copy to Clipboard**: Individual and bulk copying of assessment data
- **Print Support**: Printer-friendly formatting for assessment reports
- **Integration with Existing Features**: Assessment data included in session data exports
- **Search Integration**: Assessment content searchable within admin interface

### 7.4. Performance and Reliability Requirements

#### 7.4.1. Processing Performance
- **Asynchronous Processing**: Assessment must not block session completion
- **Reasonable Processing Time**: Complete assessment within 30 seconds under normal conditions
- **Resource Management**: Efficient memory and CPU usage during assessment generation
- **Concurrent Processing**: Support for multiple simultaneous assessments

#### 7.4.2. Monitoring and Observability
- **Success Rate Tracking**: Monitor percentage of successful assessments vs failures
- **Performance Metrics**: Track assessment processing times and identify bottlenecks
- **Error Pattern Analysis**: Identify common failure modes and implement preventive measures
- **Real-time Status**: Live monitoring of assessment queue and processing status

#### 7.4.3. Data Quality Assurance
- **Input Validation**: Verify transcript quality and completeness before assessment
- **Output Validation**: Ensure assessment quality and completeness before storage
- **Fallback Mechanisms**: Graceful handling of incomplete or low-quality data
- **Quality Metrics**: Track assessment relevance and usefulness over time

### 7.5. Security and Privacy Requirements

#### 7.5.1. Data Protection
- **Sensitive Data Handling**: Secure processing of student conversation transcripts
- **Access Control**: Assessment data access restricted to authorized administrators
- **Data Retention**: Assessment data subject to same retention policies as session data
- **GDPR Compliance**: Assessment processing must comply with privacy regulations

#### 7.5.2. AI Provider Security
- **Secure API Communication**: Encrypted communication with AI service providers
- **Data Minimization**: Only necessary data sent to external AI services
- **Provider Selection**: Use of reputable AI providers with appropriate data handling policies
- **Audit Trail**: Complete logging of data sent to and received from AI providers

### 7.6. Maintenance and Operations Requirements

#### 7.6.1. System Administration
- **Manual Retry**: Ability to manually trigger assessment for failed sessions
- **Bulk Processing**: Support for batch assessment of historical sessions
- **Configuration Management**: Adjustable assessment parameters and thresholds
- **Health Monitoring**: Dashboard indicators for assessment system health

#### 7.6.2. Continuous Improvement
- **Assessment Analytics**: Analysis of assessment patterns to improve system prompts
- **Feedback Integration**: Mechanism to incorporate assessment insights into system improvements
- **Guidelines Updates**: Support for updating tutoring guidelines and assessment criteria
- **Model Updates**: Ability to upgrade AI models while maintaining assessment consistency

### 7.7. Integration Requirements

#### 7.7.1. VAPI Workflow Integration
- **Seamless Integration**: Assessment trigger integrated into existing VAPI webhook processing
- **Session Type Detection**: Automatic determination of assessment eligibility based on session type
- **Workflow Isolation**: Assessment processing must not interfere with existing session workflows
- **Error Recovery**: Failed assessments must not impact primary session processing

#### 7.7.2. API and MCP Integration
- **Assessment Data Access**: Assessment results available through existing API endpoints
- **MCP Server Support**: Assessment data accessible through MCP server for AI assistant access
- **Authentication**: Assessment data access subject to existing authentication and authorization mechanisms
- **Consistent Data Format**: Assessment data follows established API response patterns

## 8. Student Profile and Tutor Memory System Requirements

### 8.1. Overview and Core Problems

**Status: ✅ FULLY IMPLEMENTED AND OPERATIONAL (January 2025)**

The Student Profile and Tutor Memory System addresses critical limitations in the AI tutor's ability to store, version, and recall nuanced data about each student. This system is now fully operational and provides comprehensive memory persistence and profile management.

#### 8.1.1. Core Problems Solved
- **Memory Persistence**: Eliminate repeated questions by AI tutor ("What's your dog's name again?")
- **Profile Evolution Tracking**: Maintain historical record of student development and changing needs
- **Structured Data Storage**: Enable rich, searchable student profiles with both structured and natural language data
- **Personalized Context**: Provide AI tutor with comprehensive student context for each session

### 8.2. Data Model Requirements

#### 8.2.1. Student Profile Management
- **Versioned Profiles**: System must maintain complete history of student profile evolution with timestamps
- **AI-Generated Narratives**: Store natural language descriptions of student characteristics and learning patterns
- **Structured Traits**: JSON-based storage of student characteristics for queryability and analysis
- **Current Profile View**: Optimized database view (`student_profiles_current`) for efficient latest profile retrieval
- **Profile Versioning Logic**: Automatic creation of new profile versions when significant changes occur

#### 8.2.2. Scoped Memory System
- **Memory Categorization**: Three distinct memory scopes with different retention and usage patterns:
  - `personal_fact`: Persistent personal information (pet names, family details, preferences)
  - `game_state`: Temporary game progress and achievements with configurable expiration
  - `strategy_log`: Learning strategies and pedagogical approaches that work for the student
- **Key-Value Storage**: Flexible memory storage allowing arbitrary key-value pairs within each scope
- **Expiration Management**: Optional expiration dates for temporary memories with automatic cleanup
- **UPSERT Operations**: Efficient update-or-insert logic for memory entries

### 8.3. Repository Pattern Requirements

#### 8.3.1. StudentProfileRepository Implementation
- **Current Profile Access**: `get_current(student_id)` method for efficient latest profile retrieval
- **Profile Versioning**: `add_version(student_id, narrative, traits)` for creating new profile versions
- **Trait Management**: `upsert_trait(student_id, trait_key, trait_value)` for granular profile updates
- **History Retrieval**: `get_history(student_id)` for complete profile evolution tracking
- **Transaction Safety**: All operations wrapped in database transactions with proper error handling

#### 8.3.2. StudentMemoryRepository Implementation
- **Scoped Retrieval**: `get_many(student_id, scope=None)` for filtered memory access by scope
- **Memory Operations**: `set(student_id, key, value, scope, expires_at=None)` with UPSERT logic
- **Memory Deletion**: `delete_key(student_id, key)` for individual memory removal
- **Bulk Operations**: Efficient batch operations for multiple memory updates
- **Expiration Handling**: Automatic filtering of expired memories during retrieval

### 8.4. AI Integration Requirements

#### 8.4.1. Post-Session Update Workflow
- **Automatic Triggering**: AI analysis triggered after every completed tutoring session
- **Context Compilation**: Gather current profile, memories, session transcript, and student demographics
- **Structured AI Prompts**: Use dedicated prompt template (`post_session_update.md`) for consistent analysis
- **JSON Delta Processing**: AI must provide structured updates in predefined JSON format
- **Atomic Updates**: Profile and memory updates applied atomically with rollback capability

#### 8.4.2. AI Response Format Requirements
- **Profile Updates**: Structured changes to student narrative and traits
- **Memory Updates**: Scoped memory changes with clear categorization
- **Versioning Decisions**: AI-driven determination of when to create new profile versions
- **Update Validation**: JSON schema validation before database application
- **Error Recovery**: Graceful handling of malformed or incomplete AI responses

### 8.5. Memory Management Requirements

#### 8.5.1. Expiration and Cleanup
- **Automatic Cleanup**: Nightly Celery task `purge_expired_memory` for expired memory removal
- **Configurable Retention**: Different expiration policies by memory scope:
  - `personal_fact`: No expiration (persistent)
  - `game_state`: 30-day expiration (configurable)
  - `strategy_log`: 365-day expiration (long-term insights)
- **Graceful Expiration**: Expired memories filtered during retrieval without breaking functionality

#### 8.5.2. Legacy Data Synchronization
- **Migration Support**: Temporary synchronization with legacy `students.interests` and `students.learning_preferences` arrays
- **Gradual Migration**: Nightly Celery task `sync_legacy_arrays` for backward compatibility
- **Deprecation Timeline**: Planned phaseout of legacy array-based storage

### 8.6. Admin Interface Requirements

#### 8.6.1. Student Detail Page Enhancements
- **Tabbed Interface**: Additional tabs for "Profile History" and "Tutor Memory" on student detail pages
- **Profile History View**: Timeline display of profile evolution with version comparison capabilities
- **Memory Editor**: Scope-based memory management interface with real-time editing
- **Visual Design**: Professional, responsive interface with clear navigation and status indicators

#### 8.6.2. Profile History Features
- **Version Timeline**: Chronological display of profile changes with timestamps
- **Current vs Historical**: Clear indication of current profile version vs historical versions
- **Trait Display**: Formatted display of structured profile traits
- **Export Capabilities**: Profile history export for parent/teacher review
- **Refresh Functionality**: Manual refresh capability for latest data

#### 8.6.3. Tutor Memory Features
- **Scope Organization**: Memory entries grouped by scope with clear descriptions
- **Real-Time Editing**: Add, edit, and delete memory entries with immediate persistence
- **Modal Interface**: Professional modal dialogs for memory entry editing
- **Bulk Operations**: Efficient management of multiple memory entries
- **Status Indicators**: Visual feedback for memory operations and data loading

### 8.7. API Requirements

#### 8.7.1. Enhanced Student Endpoints
- **Extended Student Details**: `GET /api/v1/students/{id}` must include current profile and memory data
- **Memory Management**: `PUT /api/v1/students/{id}/memory` for manual memory updates with scope validation
- **Profile History**: `GET /api/v1/students/{id}/profiles` for complete profile history access
- **Backward Compatibility**: All API changes must maintain compatibility with existing integrations

#### 8.7.2. Admin Interface Endpoints
- **Profile History**: `GET /admin/students/{id}/profile/history` for admin interface data loading
- **Memory Scopes**: `GET /admin/students/{id}/memory/scopes` for scoped memory management
- **Authentication**: All admin endpoints require proper authentication and authorization
- **Error Handling**: Comprehensive error responses with appropriate HTTP status codes

### 8.8. Performance Requirements

#### 8.8.1. Query Optimization
- **Database Indexes**: Optimized indexes for profile and memory retrieval:
  - `student_profiles(student_id, created_at DESC)` for current profile queries
  - `student_memories(student_id, scope)` for scoped memory retrieval
  - `student_memories(expires_at)` for cleanup operations
- **Caching Strategy**: Current profile caching with invalidation on updates
- **Efficient Views**: `student_profiles_current` view for optimized latest profile access

#### 8.8.2. Scalability Design
- **Stateless Services**: All service components designed for horizontal scaling
- **Connection Pooling**: Database connection pooling for concurrent access
- **Asynchronous Processing**: Non-blocking AI processing to prevent user-facing delays
- **Data Growth Management**: Configurable retention policies and archive strategies

### 8.9. Security and Privacy Requirements

#### 8.9.1. Data Protection
- **GDPR Compliance**: Complete student data deletion including all profile versions and memories
- **Data Portability**: Memory and profile export capabilities for data portability requirements
- **Access Control**: Scope-based API permissions for memory access
- **Audit Trails**: Comprehensive logging of all profile and memory access operations

#### 8.9.2. Data Integrity
- **Transaction Management**: Atomic updates for profile and memory changes with rollback capability
- **Validation Framework**: JSON schema validation for profile traits and memory data
- **Input Sanitization**: Proper sanitization of all user-provided content
- **Concurrent Access**: Consistent state maintenance across concurrent profile/memory updates

### 8.10. Monitoring and Observability Requirements

#### 8.10.1. Performance Metrics
- **Profile Operations**: Track profile update frequency, success rate, and performance
- **Memory Operations**: Monitor memory retrieval performance by scope and usage patterns
- **AI Processing**: Track AI delta processing time and accuracy rates
- **Database Performance**: Monitor view performance and query optimization effectiveness

#### 8.10.2. Business Intelligence
- **Student Engagement**: Correlation analysis between memory persistence and engagement
- **Profile Evolution**: Pattern analysis of student development across demographics
- **Memory Utilization**: Analysis of memory scope usage and effectiveness
- **System Effectiveness**: Track AI update success rates and system improvement over time

### 8.11. Integration Requirements

#### 8.11.1. VAPI Workflow Integration
- **Seamless Context Loading**: Student context (profile + memories) provided to AI tutor at session start
- **Post-Session Updates**: Automatic profile and memory updates after session completion
- **Error Isolation**: Profile/memory system failures must not impact primary tutoring functionality
- **Performance**: Context loading must complete quickly to avoid session delays

#### 8.11.2. Service Layer Integration
- **Enhanced StudentService**: `get_full_context(student_id)` method for complete student context
- **Enhanced SessionService**: `get_last_n_summaries(student_id, n)` for historical session context
- **Clean Interfaces**: Well-defined service interfaces for profile and memory operations
- **Dependency Injection**: Proper service layer design for testability and maintainability

## 9. Granular Mastery Tracking System Requirements

### 9.1. Overview

**Status: ✅ FULLY IMPLEMENTED AND OPERATIONAL (January 2025)**

The Granular Mastery Tracking System provides fine-grained assessment of student mastery at the individual curriculum sub-goal and knowledge component (KC) level. This system enables precise identification of learning gaps and targeted remediation strategies.

### 9.2. Core Functional Requirements

#### 9.2.1. Curriculum Structure Management
- **Hierarchical Goal Organization**: System must support structured curriculum goals with unique identifiers (e.g., "4M-01")
- **Knowledge Component Decomposition**: Each goal must be decomposable into multiple knowledge components with unique identifiers (e.g., "4M-01-KC1")
- **Subject and Grade Organization**: Goals must be organized by subject (Mathematics, English, etc.) and grade level (1-12)
- **Prerequisite Mapping**: System must track relationships between goals and their constituent knowledge components

#### 9.2.2. Mastery Progress Tracking
- **Percentage-Based Mastery**: Both goals and knowledge components must track mastery as percentages (0.0 to 100.0)
- **Student-Specific Progress**: Individual mastery tracking for each student-goal and student-KC combination
- **Timestamp Tracking**: All mastery updates must include last_updated timestamps for audit trails
- **Composite Key Design**: Progress tables must use composite primary keys (student_id, goal_id) and (student_id, kc_id)

#### 9.2.3. AI-Driven Mastery Updates
- **Session-Based Updates**: AI analysis of tutoring sessions must automatically update mastery percentages
- **Evidence-Based Assessment**: Mastery updates must be based on concrete evidence from session transcripts
- **Structured JSON Responses**: AI must provide updates in structured format with goal_patches and kc_patches arrays
- **Incremental Updates**: System must support partial mastery updates without affecting unrelated progress

### 9.3. Data Model Requirements

#### 9.3.1. CurriculumGoal Model
```sql
CREATE TABLE curriculum_goals (
    id SERIAL PRIMARY KEY,
    goal_id VARCHAR(50) UNIQUE NOT NULL,
    subject VARCHAR(100) NOT NULL,
    grade INTEGER NOT NULL,
    goal_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 9.3.2. GoalKC Model
```sql
CREATE TABLE goal_kcs (
    id SERIAL PRIMARY KEY,
    goal_id VARCHAR(50) REFERENCES curriculum_goals(goal_id),
    kc_id VARCHAR(50) UNIQUE NOT NULL,
    kc_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 9.3.3. StudentGoalProgress Model
```sql
CREATE TABLE student_goal_progress (
    student_id INTEGER REFERENCES students(id),
    goal_id VARCHAR(50) REFERENCES curriculum_goals(goal_id),
    mastery_percentage FLOAT NOT NULL DEFAULT 0.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id, goal_id)
);
```

#### 9.3.4. StudentKCProgress Model
```sql
CREATE TABLE student_kc_progress (
    student_id INTEGER REFERENCES students(id),
    kc_id VARCHAR(50) REFERENCES goal_kcs(kc_id),
    mastery_percentage FLOAT NOT NULL DEFAULT 0.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id, kc_id)
);
```

### 9.4. Repository Pattern Requirements

#### 9.4.1. CurriculumGoalRepository
- **Read-Only Access**: Repository must provide read-only access to curriculum structure
- **Filtered Queries**: Support filtering by grade, subject, and specific goal IDs
- **Relationship Loading**: Efficient loading of goals with their associated knowledge components
- **Caching Support**: Repository design must support query result caching

**Required Methods:**
- `get_all_goals()`: Retrieve all curriculum goals
- `get_goals_for_grade_subject(grade, subject)`: Filter goals by grade and subject
- `get_kcs_for_goal(goal_id)`: Get all knowledge components for a specific goal
- `get_all_kcs()`: Retrieve all knowledge components

#### 9.4.2. StudentGoalProgressRepository
- **UPSERT Operations**: Repository must support update-or-insert operations for progress tracking
- **Bulk Operations**: Support for batch updates of multiple goal progress records
- **Threshold Filtering**: Ability to filter progress records below specified mastery thresholds
- **Student Aggregation**: Efficient retrieval of all progress for a specific student

**Required Methods:**
- `upsert(student_id, goal_id, mastery_percentage)`: Update or create progress record
- `get_progress_for_student(student_id)`: Get all goal progress for student
- `get_progress_below_threshold(student_id, threshold)`: Filter incomplete goals
- `bulk_upsert(progress_records)`: Batch update multiple progress records

#### 9.4.3. StudentKCProgressRepository
- **UPSERT Operations**: Repository must support update-or-insert operations for KC progress
- **Goal-Based Filtering**: Ability to retrieve KC progress for all components of a specific goal
- **Cross-Reference Queries**: Support for queries that span goals and knowledge components
- **Performance Optimization**: Efficient handling of potentially large numbers of KC records

**Required Methods:**
- `upsert(student_id, kc_id, mastery_percentage)`: Update or create KC progress record
- `get_progress_for_student(student_id)`: Get all KC progress for student
- `get_progress_for_goal_kcs(student_id, goal_id)`: Get KC progress for specific goal
- `bulk_upsert(progress_records)`: Batch update multiple KC progress records

### 9.5. Data Seeding Requirements

#### 9.5.1. JSON Data Source Format
- **File Location**: Curriculum data must be stored in structured JSON format at `ai-tutor/backend/data/cambridge_goals_kcs.json`
- **Dual Array Structure**: JSON must contain separate arrays for "goals" and "goal_kcs"
- **Referential Integrity**: KC records must reference valid goal_id values from goals array
- **Validation Support**: JSON structure must support automated validation during import

**Required JSON Schema:**
```json
{
  "goals": [
    {
      "goal_id": "string",
      "subject": "string",
      "grade": "integer",
      "goal_text": "string"
    }
  ],
  "goal_kcs": [
    {
      "goal_id": "string",
      "kc_id": "string",
      "kc_text": "string"
    }
  ]
}
```

#### 9.5.2. Database Import Process
- **Automated Import**: System must automatically import curriculum data during database reset operations
- **Idempotent Operations**: Import process must be safe to run multiple times without creating duplicates
- **Error Handling**: Import failures must be logged with detailed error messages and not prevent system operation
- **Transaction Safety**: All import operations must be wrapped in database transactions with rollback capability

### 9.6. AI Integration Requirements

#### 9.6.1. Context Enhancement
- **Student Context Loading**: AI tutor must receive mastery map data as part of student context
- **Incomplete Progress Focus**: Context must filter to only include goals and KCs with <100% mastery
- **Structured Data Format**: Mastery context must be provided in structured format for AI consumption
- **Performance Optimization**: Context loading must not significantly impact session start time

#### 9.6.2. AI Prompt Integration
- **Mastery Update Task**: Existing AI prompts must be enhanced with mastery tracking instructions
- **Evidence-Based Updates**: AI must be instructed to only update mastery based on concrete evidence from transcripts
- **Structured Response Format**: AI must provide mastery updates in predefined JSON structure
- **Backward Compatibility**: Prompt enhancements must not break existing AI analysis functionality

**Required AI Response Format:**
```json
{
  "goal_patches": [
    {
      "goal_id": "string",
      "new_mastery_percentage": "float",
      "evidence": "string"
    }
  ],
  "kc_patches": [
    {
      "kc_id": "string",
      "new_mastery_percentage": "float",
      "evidence": "string"
    }
  ]
}
```

#### 9.6.3. Post-Session Processing
- **Automatic Triggers**: Mastery updates must be automatically processed after each tutoring session
- **Delta Processing**: System must extract and apply goal_patches and kc_patches from AI responses
- **Transaction Management**: All mastery updates must be applied atomically with rollback capability
- **Error Resilience**: Failed mastery updates must not impact primary session processing

### 9.7. API Requirements

#### 9.7.1. Enhanced Student Endpoint
- **Mastery Map Integration**: `GET /api/v1/students/{id}` must include mastery_map data in response
- **Backward Compatibility**: API enhancements must not break existing client integrations
- **Optional Expansion**: Consider supporting query parameters to control inclusion of mastery data
- **Performance Consideration**: Mastery map loading must not significantly impact API response times

#### 9.7.2. Dedicated Mastery Endpoint
- **Admin Interface Support**: New endpoint `/admin/students/<student_id>/mastery-map` for admin interface
- **Authentication Required**: Endpoint must require admin authentication and proper authorization
- **Structured Response**: Endpoint must return mastery data in consistent format with overview and detail sections
- **Error Handling**: Comprehensive error responses with appropriate HTTP status codes

**Required Response Format:**
```json
{
  "success": true,
  "data": {
    "student_id": "integer",
    "overview": {
      "total_goals": "integer",
      "goals_with_progress": "integer",
      "average_mastery": "float"
    },
    "subjects": {
      "subject_name": {
        "goals": {
          "goal_id": {
            "goal_text": "string",
            "mastery_percentage": "float",
            "kcs": {
              "kc_id": {
                "kc_text": "string",
                "mastery_percentage": "float"
              }
            }
          }
        }
      }
    }
  }
}
```

### 9.8. User Interface Requirements

#### 9.8.1. Admin Interface Integration
- **Tabbed Interface**: Student detail page must include new "Mastery Map" tab alongside existing tabs
- **AJAX Data Loading**: Mastery data must be loaded asynchronously to avoid blocking page load
- **Visual Design Consistency**: New tab must follow existing design patterns and styling
- **Responsive Design**: Interface must work properly across different screen sizes

#### 9.8.2. Mastery Visualization
- **Overview Statistics**: Display total goals, goals with progress, and average mastery percentage
- **Subject Organization**: Group mastery data by subject with clear visual separation
- **Color-Coded Progress**: Use color coding to indicate mastery levels (high/medium/low/none)
- **Progress Indicators**: Visual progress bars or percentage displays for goals and knowledge components

**Required CSS Classes:**
```css
.mastery-high { background-color: #d4edda; }    /* 80-100% mastery */
.mastery-medium { background-color: #fff3cd; }  /* 50-79% mastery */
.mastery-low { background-color: #f8d7da; }     /* 1-49% mastery */
.mastery-none { background-color: #f8f9fa; }    /* 0% mastery */
```

#### 9.8.3. User Interaction Features
- **View Switching**: Support for switching between overview and detailed views
- **Data Export**: Functionality to export mastery data in JSON format
- **Real-Time Updates**: Support for refreshing mastery data without page reload
- **Error Handling**: User-friendly error messages for data loading failures

### 9.9. MCP Server Integration Requirements

#### 9.9.1. Planned MCP Tool
- **Tool Name**: `get-mastery-map` for integration with AI assistants
- **Authentication**: Token-based authentication following existing MCP patterns
- **Request Format**: Simple student_id parameter for data retrieval
- **Response Format**: Consistent with admin API endpoint format

#### 9.9.2. Implementation Standards
- **Logging Integration**: Complete request/response logging for debugging and monitoring
- **Error Handling**: Graceful error handling with appropriate error messages
- **Performance**: Efficient data retrieval without impacting MCP server performance
- **Future Extensibility**: Design to support future mastery-related MCP tools

### 9.10. Performance Requirements

#### 9.10.1. Database Performance
- **Index Strategy**: Appropriate indexes on frequently queried columns
  - `curriculum_goals(grade, subject)` for filtered goal retrieval
  - `student_goal_progress(student_id)` for student-specific queries
  - `student_kc_progress(student_id)` for KC progress retrieval
  - `goal_kcs(goal_id)` for goal-to-KC mapping
- **Query Optimization**: Efficient queries using composite primary keys and proper joins
- **Bulk Operations**: Support for batch UPSERT operations to minimize database round trips

#### 9.10.2. API Performance
- **Response Time**: Mastery map endpoint must respond within 500ms for typical student data
- **Memory Efficiency**: Mastery data loading must not consume excessive memory
- **Concurrent Access**: System must handle multiple simultaneous mastery map requests
- **Caching Strategy**: Consider implementing caching for frequently accessed mastery data

### 9.11. Security Requirements

#### 9.11.1. Data Protection
- **Access Control**: Mastery data must be protected by appropriate authentication and authorization
- **GDPR Compliance**: Mastery tracking data must be included in student data deletion and export operations
- **Audit Trails**: All mastery updates must be logged for security and compliance purposes
- **Input Validation**: All mastery update data must be validated before database storage

#### 9.11.2. API Security
- **Authentication Required**: All mastery-related endpoints must require proper authentication
- **Authorization Checks**: Verify user permissions for accessing specific student mastery data
- **Input Sanitization**: Sanitize all input parameters to prevent injection attacks
- **Rate Limiting**: Implement appropriate rate limiting for mastery data endpoints

### 9.12. Data Integrity Requirements

#### 9.12.1. Referential Integrity
- **Foreign Key Constraints**: Enforce database-level referential integrity between related tables
- **Cascade Deletion**: Properly handle deletion of students, goals, and knowledge components
- **Data Consistency**: Ensure mastery percentages remain within valid ranges (0.0 to 100.0)
- **Transaction Safety**: All multi-table operations must be wrapped in database transactions

#### 9.12.2. Data Validation
- **Range Validation**: Mastery percentages must be validated to be between 0.0 and 100.0
- **ID Format Validation**: Goal and KC IDs must follow established naming conventions
- **Required Field Validation**: All required fields must be validated before database insertion
- **JSON Schema Validation**: AI response data must be validated against predefined schemas

### 9.13. Testing Requirements

#### 9.13.1. Unit Testing
- **Repository Testing**: Comprehensive unit tests for all repository methods
- **Service Testing**: Unit tests for mastery-related service methods
- **AI Integration Testing**: Tests for AI response processing and mastery update logic
- **Data Validation Testing**: Tests for all data validation rules and constraints

#### 9.13.2. Integration Testing
- **API Endpoint Testing**: Full integration tests for all mastery-related API endpoints
- **Database Integration**: Tests for database operations and data integrity
- **UI Integration**: Tests for admin interface functionality and data display
- **End-to-End Testing**: Complete workflow tests from AI analysis to UI display

### 9.14. Documentation Requirements

#### 9.14.1. Technical Documentation
- **API Documentation**: Complete documentation of all mastery-related API endpoints
- **Database Schema**: Detailed documentation of new database tables and relationships
- **Service Documentation**: Documentation of all service methods and their usage
- **Integration Guide**: Documentation for integrating with the mastery tracking system

#### 9.14.2. User Documentation
- **Admin Interface Guide**: Documentation for using the mastery map features
- **Troubleshooting Guide**: Common issues and solutions for mastery tracking
- **Performance Guidelines**: Best practices for optimal system performance
- **Security Guidelines**: Security considerations for mastery data handling

### 9.15. Monitoring and Observability Requirements

#### 9.15.1. Performance Monitoring
- **Response Time Tracking**: Monitor API response times for mastery-related endpoints
- **Database Performance**: Track query performance and identify optimization opportunities
- **Memory Usage**: Monitor memory consumption during mastery data processing
- **Error Rate Monitoring**: Track error rates for all mastery-related operations

#### 9.15.2. Business Metrics
- **Usage Analytics**: Track adoption and usage of mastery tracking features
- **Data Quality Metrics**: Monitor accuracy and completeness of mastery data
- **AI Performance**: Track effectiveness of AI-driven mastery updates
- **User Engagement**: Monitor admin interface usage and feature adoption

### 9.16. Future Enhancement Requirements

#### 9.16.1. Extensibility Requirements
- **Multi-Curriculum Support**: Design to support multiple curriculum standards
- **Custom Goal Definition**: Support for school-specific goal and KC definitions
- **Historical Tracking**: Potential for tracking mastery progress over time
- **Advanced Analytics**: Foundation for sophisticated learning analytics

#### 9.16.2. Integration Requirements
- **External Assessment**: Design to integrate with external assessment platforms
- **Learning Management Systems**: Potential integration with LMS platforms
- **Parent Portal**: Design to support parent access to mastery information
- **Analytics Platforms**: Integration with advanced analytics and reporting tools

## 10. AI Tutor System Enhancement (v4 Context & VAPI v3) Requirements

### 10.1. Overview

**Status: ✅ FULLY IMPLEMENTED AND OPERATIONAL (January 2025)**

The AI Tutor System Enhancement represents a major modernization initiative that transforms the platform from a basic conversational AI into a sophisticated, memory-enabled, game-state-aware tutoring system. This enhancement implements a standardized v4 context contract, enhanced VAPI prompt system, comprehensive MCP server tools, and performance optimizations through Redis caching.

### 10.2. Core Enhancement Requirements

#### 10.2.1. v4 Context Contract Requirements
- **Standardized Data Structure**: System must implement a consistent v4 context format with five distinct blocks: demographics, profile, memories, progress, and _curriculum
- **Version Identification**: All context objects must include `context_version: 4` for API compatibility tracking
- **Backwards Compatibility**: v4 context must be designed to support future evolution without breaking existing integrations
- **JSON Schema Validation**: All v4 context objects must conform to a strict JSON schema for data integrity

#### 10.2.2. Goal Prerequisites System Requirements
- **Prerequisite Mapping**: System must track logical dependencies between curriculum goals and prerequisite knowledge components
- **Database Schema**: New `goal_prerequisites` table linking curriculum goals to required prerequisite knowledge components
- **SQL View Integration**: Efficient `grade_subject_goals_v` view must aggregate curriculum data with prerequisite relationships
- **Curriculum Atlas Enhancement**: Curriculum atlas must include prerequisite data for AI tutor consumption

#### 10.2.3. Enhanced VAPI Prompt (v3) Requirements
- **Personality System**: Implement "Sunny" AI tutor personality with warm, encouraging, and slightly playful characteristics
- **Memory Integration**: AI tutor must reference stored memories from previous conversations for personalized interactions
- **Game State Management**: Support for persistent educational games and progress tracking across sessions
- **Conditional Flow Management**: Different conversation approaches for new vs returning students based on memory availability

#### 10.2.4. Redis Caching Requirements
- **Performance Optimization**: Implement intelligent caching for frequently accessed curriculum atlas data
- **Cache Key Strategy**: Use structured cache keys following pattern `curriculum_atlas:{curriculum_id}:{grade_level}`
- **TTL Management**: Appropriate time-to-live settings for different data types (curriculum: 1 hour, student context: 5 minutes)
- **Cache Invalidation**: Automatic cache invalidation on curriculum or student data changes

### 10.3. Database Schema Requirements

#### 10.3.1. Goal Prerequisites Table
```sql
CREATE TABLE goal_prerequisites (
    id SERIAL PRIMARY KEY,
    goal_id VARCHAR(50) NOT NULL REFERENCES curriculum_goals(goal_id),
    prerequisite_kc_id VARCHAR(50) NOT NULL REFERENCES goal_kcs(kc_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(goal_id, prerequisite_kc_id)
);
```

- **Referential Integrity**: Foreign key constraints must ensure data consistency
- **Unique Constraints**: Prevent duplicate prerequisite relationships
- **Index Strategy**: Optimize queries with appropriate indexes on goal_id and prerequisite_kc_id

#### 10.3.2. Grade Subject Goals SQL View
```sql
CREATE VIEW grade_subject_goals_v AS
SELECT
    cd.curriculum_id,
    cd.grade_level,
    cd.subject_id,
    s.name as subject_name,
    cg.goal_id,
    cg.goal_text,
    gkc.kc_id,
    gkc.kc_text,
    COALESCE(
        json_agg(DISTINCT gp.prerequisite_kc_id)
        FILTER (WHERE gp.prerequisite_kc_id IS NOT NULL),
        '[]'::json
    ) as prerequisites
FROM curriculum_details cd
JOIN subjects s ON cd.subject_id = s.id
JOIN curriculum_goals cg ON s.name = cg.subject AND cd.grade_level = cg.grade
JOIN goal_kcs gkc ON cg.goal_id = gkc.goal_id
LEFT JOIN goal_prerequisites gp ON cg.goal_id = gp.goal_id
GROUP BY cd.curriculum_id, cd.grade_level, cd.subject_id, s.name,
         cg.goal_id, cg.goal_text, gkc.kc_id, gkc.kc_text
ORDER BY subject_name, cg.goal_id, gkc.kc_id;
```

- **Single Query Efficiency**: View must enable single-query access to complete curriculum atlas
- **JSON Aggregation**: Prerequisites must be aggregated as JSON arrays for efficient consumption
- **Performance**: View must be optimized for frequent access through indexing strategy

### 10.4. v4 Context Contract Schema Requirements

#### 10.4.1. Complete v4 Context Structure
The system must implement a standardized v4 context with the following mandatory structure:

```json
{
  "context_version": 4,
  "student_id": "emma_smith",
  "demographics": {
    "first_name": "string",
    "last_name": "string",
    "grade_level": "integer",
    "school_name": "string",
    "interests": ["array of strings"],
    "learning_preferences": ["array of strings"]
  },
  "profile": {
    "narrative": "AI-generated personality description",
    "traits": {
      "learning_style": "string",
      "confidence_level": "string",
      "motivation_triggers": ["array"]
    },
    "version_timestamp": "ISO 8601 timestamp"
  },
  "memories": {
    "personal_fact": {
      "key": "value pairs"
    },
    "game_state": {
      "key": "value pairs with game progress"
    },
    "strategy_log": {
      "key": "value pairs with effective teaching strategies"
    }
  },
  "progress": {
    "subjects": {
      "subject_name": {
        "overall_progress": "float",
        "mastery_level": "string",
        "recent_achievements": ["array"],
        "focus_areas": ["array"]
      }
    }
  },
  "_curriculum": {
    "curriculum_id": "integer",
    "curriculum_name": "string",
    "grade_level": "integer",
    "subjects": {
      "subject_name": {
        "goals": {
          "goal_id": {
            "goal_text": "string",
            "knowledge_components": {
              "kc_id": {
                "kc_text": "string",
                "prerequisites": ["array of prerequisite KC IDs"]
              }
            }
          }
        }
      }
    }
  }
}
```

#### 10.4.2. Context Block Responsibilities
- **Demographics Block**: Static student information and school enrollment data
- **Profile Block**: AI-generated personality insights with versioning support
- **Memories Block**: Scoped key-value storage for personalization (personal_fact, game_state, strategy_log)
- **Progress Block**: Subject-level achievement and mastery tracking
- **_Curriculum Block**: Complete curriculum atlas with goal hierarchy and prerequisites

### 10.5. StudentContextService Requirements

#### 10.5.1. Service Architecture
- **Location**: Must be implemented as dedicated service at `ai-tutor/backend/app/services/student_context_service.py`
- **Dependency Injection**: Service must use repository pattern for data access
- **Error Handling**: Comprehensive error handling with graceful degradation
- **Performance**: Context building must complete within 500ms for typical student data

#### 10.5.2. Core Method Requirements
**`build(student_id: int, curriculum_id: int = None) -> dict`**:
- **Input Validation**: Validate student_id exists and curriculum_id is valid
- **Data Assembly**: Gather data from multiple repositories (student, profile, memory, progress, curriculum)
- **Redis Integration**: Utilize Redis caching for curriculum atlas data
- **Structured Output**: Return complete v4 context structure
- **Null Handling**: Gracefully handle missing profile or memory data

#### 10.5.3. Block Building Methods
- **`build_demographics_block(student)`**: Convert student model to demographics structure
- **`build_profile_block(current_profile)`**: Format AI profile data with version timestamp
- **`build_memories_block(memories)`**: Organize memories by scope (personal_fact, game_state, strategy_log)
- **`build_progress_block(progress)`**: Aggregate subject-level progress and achievements
- **Error Isolation**: Each block builder must handle missing data gracefully

### 10.6. Redis Caching Requirements

#### 10.6.1. Cache Strategy Implementation
- **Cache Keys**: Structured cache keys using pattern `curriculum_atlas:{curriculum_id}:{grade_level}`
- **Cache Client**: Redis client must be properly configured with connection pooling
- **Serialization**: JSON serialization/deserialization for complex data structures
- **Error Handling**: Cache failures must not impact application functionality (graceful degradation)

#### 10.6.2. CurriculumRepository.get_grade_atlas() Requirements
```python
def get_grade_atlas(self, curriculum_id: int, grade_level: int) -> dict:
    # 1. Check Redis cache first
    # 2. If cache miss, query grade_subject_goals_v view
    # 3. Build atlas structure from query results
    # 4. Cache result with 1-hour TTL
    # 5. Return atlas data
```

- **Cache-First Strategy**: Always check cache before database query
- **TTL Management**: 1-hour TTL for curriculum atlas data (relatively static)
- **Cache Warming**: Support for pre-loading frequently accessed atlases
- **Performance Monitoring**: Track cache hit rates and query performance

#### 10.6.3. Cache Management
- **Clear Method**: `clear_curriculum_cache(curriculum_id, grade_level)` for manual cache invalidation
- **Bulk Clear**: Support for clearing all curriculum-related cache entries
- **Health Monitoring**: Monitor Redis connection status and cache performance
- **Fallback Strategy**: Database-only operation when Redis is unavailable

### 10.7. Enhanced VAPI Prompt System (v3) Requirements

#### 10.7.1. Sunny AI Tutor Personality Requirements
- **Character Definition**: Warm, encouraging, slightly playful AI tutor named "Sunny"
- **Engagement Strategies**: Must use games, stories, and interactive elements to maintain student interest
- **Age Appropriateness**: Communication style must adapt to student grade level and developmental stage
- **Consistency**: Personality must remain consistent across all interactions while being personalized

#### 10.7.2. Memory Integration Requirements
- **Personal Context**: AI must reference stored personal facts (pet names, family details, preferences)
- **Game Continuity**: Resume and reference ongoing educational games and achievements
- **Strategy Adaptation**: Apply stored effective teaching strategies specific to each student
- **Memory Validation**: Verify memory accuracy and relevance before referencing in conversation

#### 10.7.3. Conditional Flow Management
- **New Student Detection**: Identify new students by empty or minimal memory stores
- **Relationship Building**: Focus on discovery and rapport building for new students
- **Returning Student Flow**: Reference previous conversations and continue established relationships
- **Adaptive Interaction**: Adjust conversation depth and complexity based on stored student profile

#### 10.7.4. Game State Management
- **Persistent Games**: Support for educational games that span multiple sessions
- **Progress Tracking**: Track student achievements, levels, and game-specific progress
- **Achievement System**: Recognize and celebrate student accomplishments across sessions
- **Game Variety**: Support multiple concurrent educational games with separate state tracking

### 10.8. Enhanced MCP Server Tools Requirements

#### 10.8.1. set_game_state Tool Requirements
**Purpose**: Enable AI tutor to persist game state across sessions

**Parameters**:
- `student_id` (required): Student identifier
- `game_id` (required): Unique game identifier
- `json_blob` (required): Game state data as JSON string
- `is_active` (required): Boolean indicating if game is currently active

**Implementation Requirements**:
- **Storage**: Store game state in student_memories table with scope 'game_state'
- **Key Format**: Use pattern `game_{game_id}` for memory keys
- **Data Validation**: Validate JSON structure and game_id format
- **Error Handling**: Provide meaningful error messages for invalid requests

#### 10.8.2. set_memory Tool Requirements
**Purpose**: Allow AI tutor to store personal facts and learning strategies

**Parameters**:
- `student_id` (required): Student identifier
- `key` (required): Memory key (e.g., "pet_name", "favorite_subject")
- `value` (required): Memory content as string
- `scope` (required): Memory category ("personal_fact", "game_state", "strategy_log")

**Implementation Requirements**:
- **Scope Validation**: Ensure scope is one of the three valid values
- **UPSERT Logic**: Update existing memories or create new ones
- **Data Sanitization**: Sanitize memory content for security
- **Audit Logging**: Log all memory operations for debugging and compliance

#### 10.8.3. log_session_event Tool Requirements
**Purpose**: Track significant learning moments and breakthroughs

**Parameters**:
- `student_id` (required): Student identifier
- `event_json` (required): Structured event data (achievements, milestones, insights)

**Implementation Requirements**:
- **Event Storage**: Store events in appropriate logging table
- **JSON Validation**: Validate event structure before storage
- **Timestamp**: Automatically add timestamp to all events
- **Event Types**: Support different event types (achievement, breakthrough, milestone, etc.)

#### 10.8.4. Enhanced get_student_context Resource Requirements
- **v4 Context Response**: Return complete v4 context from StudentContextService
- **Resource URI**: Update resource URI to indicate v4 context version
- **MIME Type**: JSON MIME type with appropriate content description
- **Performance**: Efficient context loading without blocking MCP server

### 10.9. Frontend UI Requirements (Student Detail v4)

#### 10.9.1. Tabbed Interface Requirements
- **New Template**: Create `student_detail_v4.html` template with modern tabbed interface
- **Tab Structure**: Six tabs covering Demographics, AI Profile, Memories, Progress, Curriculum Atlas, and Raw JSON
- **Responsive Design**: Mobile-friendly design that works across device sizes
- **Navigation**: Smooth tab switching with proper state management

#### 10.9.2. Individual Tab Requirements
**Demographics Tab**:
- Display student basic information and school details
- Clean, readable format with proper spacing and typography
- Edit capability for basic demographic information

**AI Profile Tab**:
- Show AI-generated personality insights and learning style analysis
- Display profile version timestamp and history
- Format traits in human-readable manner

**Memories Tab**:
- Organize memories by scope with clear visual separation
- Real-time editing capability with add/edit/delete operations
- Modal dialogs for memory entry management
- Scope descriptions to help administrators understand memory types

**Progress Tab**:
- Visual progress indicators for subject mastery
- Achievement tracking and display
- Focus areas and recent accomplishments
- Color-coded progress levels

**Curriculum Atlas Tab**:
- Complete curriculum view organized by subject
- Goals and knowledge components with prerequisite relationships
- Expandable/collapsible sections for detailed exploration
- Search and filter capabilities

**Raw JSON Tab**:
- Complete v4 context display in formatted JSON
- Copy to clipboard functionality
- Download as JSON file capability
- Refresh button for latest data

#### 10.9.3. Enhanced UX Features
- **Real-time Updates**: AJAX-powered data loading without page refresh
- **Loading States**: Professional loading indicators during data fetching
- **Error Handling**: User-friendly error messages with retry options
- **Copy/Download**: Easy export of context data for debugging and sharing
- **Visual Feedback**: Status indicators and success/error notifications

### 10.10. Performance Requirements

#### 10.10.1. Context Loading Performance
- **Target Response Time**: v4 context assembly must complete within 500ms
- **Redis Cache Hit Rate**: Target >90% cache hit rate for curriculum atlas data
- **Memory Efficiency**: Context loading must not consume excessive memory
- **Concurrent Access**: Support multiple simultaneous context requests

#### 10.10.2. Database Query Optimization
- **SQL View Performance**: grade_subject_goals_v view must be optimized with appropriate indexes
- **Single Query Design**: Curriculum atlas loading via single view query
- **Composite Key Efficiency**: Leverage composite primary keys for optimal performance
- **Connection Pooling**: Efficient database connection management

#### 10.10.3. Caching Performance
- **Cache Response Time**: Redis operations must complete within 50ms
- **Memory Usage**: Efficient memory usage in Redis with appropriate data structures
- **Cache Size Management**: Monitor cache size and implement eviction policies
- **Network Efficiency**: Minimize Redis network traffic through batch operations

### 10.11. Security and Privacy Requirements

#### 10.11.1. MCP Token Scope Validation
- **Enhanced Scopes**: New scope definitions for enhanced MCP functionality
  - `mcp:read`: Required for student context access
  - `mcp:write`: Required for memory and game state updates
  - `mcp:log`: Required for session event logging
- **Scope Enforcement**: Strict validation of token scopes before allowing operations
- **Audit Trail**: Complete logging of MCP operations with token identification

#### 10.11.2. Data Privacy Controls
- **Memory Scope Security**: Access controls based on memory scope sensitivity
- **Game State Privacy**: Secure handling of student game progress data
- **Context Data Protection**: Encryption of sensitive context data in transit and at rest
- **GDPR Compliance**: Memory and profile data included in data deletion and export operations

#### 10.11.3. Input Validation
- **JSON Schema Validation**: All JSON inputs validated against strict schemas
- **SQL Injection Prevention**: Parameterized queries for all database operations
- **XSS Prevention**: Proper escaping of user-generated content in UI
- **Memory Content Sanitization**: Sanitize all memory values before storage

### 10.12. Integration Requirements

#### 10.12.1. VAPI Workflow Integration
- **Context Loading**: Seamless integration of v4 context loading into VAPI call processing
- **Memory Updates**: Post-session memory and game state updates via new MCP tools
- **Error Isolation**: v4 context failures must not impact voice call functionality
- **Performance**: Context operations must not introduce call latency

#### 10.12.2. Existing System Integration
- **Backward Compatibility**: v4 context must coexist with existing student data structures
- **API Compatibility**: Enhanced APIs must maintain backward compatibility
- **Service Integration**: Clean integration with existing service layer architecture
- **Database Migration**: Schema changes must be deployable without data loss

### 10.13. Monitoring and Analytics Requirements

#### 10.13.1. Performance Monitoring
- **Context Assembly Time**: Track v4 context building performance
- **Cache Performance**: Monitor Redis cache hit rates and response times
- **Memory Operations**: Track memory update frequency and success rates
- **SQL View Performance**: Monitor grade_subject_goals_v query performance

#### 10.13.2. Business Analytics
- **Memory Utilization**: Track memory scope usage patterns
- **Game State Persistence**: Monitor game continuation rates across sessions
- **Profile Evolution**: Track AI profile update frequency and accuracy
- **Context Usage**: Monitor v4 context utilization by AI tutor

#### 10.13.3. Error Monitoring
- **Context Loading Failures**: Track and alert on context assembly failures
- **Cache Failures**: Monitor Redis connection issues and failover scenarios
- **MCP Tool Errors**: Track errors in new MCP tools with detailed logging
- **UI Performance**: Monitor frontend loading times and user interactions

### 10.14. Testing Requirements

#### 10.14.1. Unit Testing
- **Service Layer**: Comprehensive tests for StudentContextService methods
- **Repository Layer**: Tests for enhanced CurriculumRepository with caching
- **MCP Tools**: Individual tests for each new MCP tool
- **Cache Integration**: Tests for Redis caching logic and fallback scenarios

#### 10.14.2. Integration Testing
- **v4 Context Assembly**: End-to-end tests for complete context building
- **MCP Server Integration**: Tests for enhanced MCP server functionality
- **UI Integration**: Tests for new student detail v4 template
- **Database Integration**: Tests for new schema elements and SQL view

#### 10.14.3. Performance Testing
- **Load Testing**: Context loading under concurrent access
- **Cache Performance**: Redis performance under various load scenarios
- **Memory Usage**: Memory consumption during context operations
- **Database Performance**: SQL view performance with large datasets

### 10.15. Documentation Requirements

#### 10.15.1. Technical Documentation
- **v4 Context Schema**: Complete JSON schema documentation
- **API Changes**: Documentation of all API enhancements
- **Caching Strategy**: Redis implementation and cache key documentation
- **Database Changes**: Documentation of new tables, views, and relationships

#### 10.15.2. User Documentation
- **Admin Interface**: Guide for using new student detail v4 features
- **Memory Management**: Documentation for memory scope system
- **Troubleshooting**: Common issues and solutions for enhanced features
- **Performance**: Guidelines for optimal system performance

### 10.16. Deployment Requirements

#### 10.16.1. Database Migration
- **Schema Updates**: Automated creation of goal_prerequisites table and grade_subject_goals_v view
- **Data Seeding**: Automatic import of prerequisite data from cambridge_goals_kcs.json
- **Migration Safety**: Zero-downtime deployment with rollback capability
- **Validation**: Post-migration validation of schema and data integrity

#### 10.16.2. Redis Configuration
- **Redis Setup**: Proper Redis configuration for production deployment
- **Connection Configuration**: Redis connection string and pooling configuration
- **Memory Configuration**: Appropriate Redis memory limits and eviction policies
- **Monitoring Setup**: Redis monitoring and alerting configuration

#### 10.16.3. Application Configuration
- **Environment Variables**: Configuration for Redis connection and caching settings
- **Feature Flags**: Support for enabling/disabling enhanced features
- **Performance Tuning**: Configuration options for cache TTL and performance optimization
- **Error Handling**: Configuration for error reporting and logging levels
