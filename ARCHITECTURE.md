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
- **Purpose**: AI-powered analysis of tutoring session transcripts
- **Framework**: Python with OpenAI/Anthropic API integration
- **Responsibilities**:
  - File-based prompt management (Markdown templates)
  - Multi-provider AI analysis (OpenAI, Anthropic)
  - Structured response parsing and extraction
  - Session quality validation
  - Student profile enhancement from transcripts

### 2.2. External Integrations

#### 2.2.1. VAPI (Voice API)
- **Purpose**: Voice call handling and transcript generation
- **Integration**: Webhook-based real-time processing
- **Data Flow**: Call → Transcript → Student Profile → Session Summary

## 3. Data Architecture

### 3.1. Database Schema

```sql
-- Core Entities
Students (id, first_name, last_name, phone_number, school_id, ...)
Schools (id, name, country, city, description)
Sessions (id, student_id, transcript, summary, start_datetime, ...)
Assessments (id, student_id, grade, subject, mastery_level, ...)

-- System Infrastructure
SystemLogs (id, timestamp, level, category, message)
Tokens (id, token_hash, scopes, expires_at, created_at, last_used, ...)

-- Analytics & Metrics
SessionMetrics (id, session_id, duration_seconds, satisfaction, ...)
DailyStats (id, date, total_sessions, avg_duration, total_users, ...)
StudentProgress (id, student_id, subject, proficiency_level, ...)
```

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
2. Prompt request → Template lookup by name (e.g., 'session_analysis')
3. Parameter injection → Template formatting with student context
4. AI provider call → Formatted prompt sent to OpenAI/Anthropic
5. Response parsing → Structured analysis extraction
6. Database storage → Results saved to PostgreSQL
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