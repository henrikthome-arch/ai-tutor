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
