# AI Tutor System: Detailed Requirements

This document outlines the detailed requirements for the AI Tutor system, covering system functionality, data models, user experience, and legal compliance.

## 1. System Requirements

### 1.1. Functional Requirements

-   **Multi-Channel Interaction**: Support for tutoring sessions via phone calls, with a design that accommodates future channels like web and mobile apps.
-   **Context-Aware Conversation**: Provide the AI tutor with relevant student context at the start of each session.
-   **Post-Session Processing**: Automatically process session transcripts to generate summaries and update student profiles and assessments.
-   **AI-Powered Profile Extraction**: Automatically extract and update student information (age, grade, interests, learning preferences) from conversation transcripts using AI analysis.
-   **Conditional Prompt System**: The system must automatically detect call type (introductory vs tutoring) based on phone number lookup and apply appropriate AI prompts for analysis.
-   **JSON-Structured AI Responses**: All AI prompts must generate structured JSON output for consistent data extraction and processing.
-   **Call Type Detection**: Automatic determination of new vs returning students based on phone number presence in the database.
-   **VAPI Integration**: Complete integration with VAPI for voice call handling, including webhook processing, call data retrieval, and transcript analysis.
-   **Automatic Student Registration**: System must automatically create student profiles for new callers using phone number identification and conversation analysis.
-   **Phone Number Management**: Robust phone number normalization, mapping, and international format handling for student identification.
-   **Admin Dashboard**: A secure, web-based admin dashboard for system management with database browser functionality.
-   **API Layer**: A dedicated API layer (MCP Server) to serve data to all user interfaces.
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

## 2. Data Models and Functions

The system's data will be stored in a managed PostgreSQL database.

| Data Model | Description | Key Attributes |
| :--- | :--- | :--- |
| **School** | Represents a school. | `id`, `name`, `country`, `city`, `description` |
| **Student** | Represents a student. | `id`, `first_name`, `last_name`, `date_of_birth`, `phone_number`, `school_id` (FK), `student_type` |
| **Curriculum** | Defines the educational framework. | `id`, `school_id` (FK), `grade`, `subject`, `student_type`, `goals` (Text) |
| **Session**| Represents a tutoring session. | `id`, `student_id` (FK), `session_type`, `start_datetime`, `duration`, `transcript`, `summary` (Text) |
| **Assessment**| Tracks academic progress. | `id`, `student_id` (FK), `grade`, `subject`, `strengths`, `weaknesses`, `mastery_level`, `comments_tutor` (Text), `comments_teacher` (Text), `completion_percentage`, `grade_score`, `grade_motivation` (Text), `last_updated` (DateTime) |
| **SystemLog**| Records system events. | `id`, `timestamp`, `level`, `category`, `message`|

## 3. Prompt Management

All prompts used in the system (for both VAPI and internal AI processing) will be stored as individual Markdown files in a dedicated `prompts` directory. This approach provides a clear separation of concerns and makes it easy to manage and version control the prompts.

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
- **Standardized Structure**: All prompts must generate JSON responses with consistent field naming
- **Required JSON Fields**:
  - `student_profile`: Student information and characteristics
  - `session_analysis`: Session content analysis and insights
  - `recommendations`: Action items and next steps
  - `metadata`: Call type, confidence scores, and processing timestamps
- **Data Validation**: System must validate JSON structure before database storage
- **Error Recovery**: Invalid JSON responses must be logged and trigger fallback processing
- **Schema Versioning**: JSON schema must support future extensions without breaking existing functionality

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

## 4. Detailed Implementation Plan

**Phase 1: Project Restructuring**
1.  Create the new, layered directory structure.
2.  Move files and rename `ai_poc` to `ai`.

**Phase 2: Flask App and API Refactoring**
1.  Implement the Flask app factory and `run.py`.
2.  Refactor `admin-server.py` into separate Blueprints for the admin UI and API.

**Phase 3: Database Integration**
4.  Create a script for initial data seeding (e.g., default curriculums).
1.  Set up a managed PostgreSQL database on Render.
2.  Define the complete database schema using SQLAlchemy.
3.  Implement the repository and service layers for all data entities.

**Phase 4: Production-Grade Enhancements**
1.  Integrate Celery and Redis for asynchronous task processing.
2.  Implement AI-powered session summary and assessment generation.
3.  Develop analytics and visualizations for the admin dashboard.