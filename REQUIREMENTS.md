# AI Tutor System: Detailed Requirements

This document outlines the detailed requirements for the AI Tutor system, covering system functionality, data models, user experience, and legal compliance.

## 1. System Requirements

### 1.1. Functional Requirements

-   **Multi-Channel Interaction**: Support for tutoring sessions via phone calls, with a design that accommodates future channels like web and mobile apps.
-   **Context-Aware Conversation**: Provide the AI tutor with relevant student context at the start of each session.
-   **Post-Session Processing**: Automatically process session transcripts to generate summaries and update student profiles and assessments.
-   **Admin Dashboard**: A secure, web-based admin dashboard for system management.
-   **API Layer**: A dedicated API layer (MCP Server) to serve data to all user interfaces.
-   **Log Management**: System logs will be automatically deleted after 30 days to ensure data hygiene.

### 1.2. Non-Functional Requirements

-   **Scalability**: An architecture designed for growth.
-   **Maintainability**: A well-structured, modular codebase.
-   **Security**: Secure data storage and encrypted communication.
-   **Reliability**: Robust error handling and logging.
-   **Low-Maintenance**: Use of managed services to minimize operational overhead.
-   **GDPR Compliance**: The system must be designed and operated in adherence to the General Data Protection Regulation (GDPR), ensuring student data is handled with the highest standards of privacy and security.

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