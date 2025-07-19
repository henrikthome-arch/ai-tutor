# AI Tutor Service: System Architecture

This document provides a comprehensive architectural overview of the AI Tutor service, including its components, data flows, security measures, and a roadmap for future development. Its purpose is to serve as a single source of truth for understanding how the system works end-to-end.

## 1. High-Level Overview

The AI Tutor service provides personalized, voice-based tutoring for students. It uses a combination of a third-party telephony provider (VAPI), a custom backend with a dedicated API layer (MCP Server), a post-call AI analysis pipeline, and a web-based admin dashboard. The architecture is designed for scalability and maintainability, supporting multiple user interfaces and leveraging a managed database service.

## 2. Full System Workflow & Data Flow

### 2.1. Complete Architectural Diagram

```mermaid
graph TD
    subgraph "User Interfaces"
        AdminUI[Admin Web UI]
        MobileApp[Future Mobile App]
    end

    subgraph "VAPI Platform (Third-Party)"
        VAPI_Service[VAPI Telephony Service]
        VAPI_API[VAPI REST API]
    end
    
    subgraph "AI Tutor Backend (Hosted on Render)"
        direction LR
        APILayer[API Layer / MCP Server]
        VAPI_Client[VAPI API Client]
        Celery[Celery Task Queue<br>(with Redis)]
        DB["Managed PostgreSQL<br>(Render)"]

        APILayer -- "Serves data to" --> AdminUI
        APILayer -- "Serves data to" --> MobileApp
        APILayer -- "Reads/Writes" --> DB
        APILayer -- "Uses" --> VAPI_Client
        APILayer -- "Enqueues Task" --> Celery
        
        VAPI_Client -- "Calls" --> VAPI_API
        Celery -- "Processes Task" --> AI_Processor
        AI_Processor[AI Analysis Worker] -- "Reads/Writes" --> DB
    end

    %% Real-Time Pre-Call Flow
    VAPI_Service -- "1. REAL-TIME: `get_student_context(phone)`" --> APILayer
    APILayer -- "2. Identify student" --> DB
    DB -- "3. Return student data" --> APILayer
    APILayer -- "4. Return context JSON" --> VAPI_Service
    
    %% Asynchronous Post-Call Flow
    VAPI_Service -- "5. ASYNC: `end-of-call-report` Webhook" --> APILayer
    APILayer -- "6. Fetch call data & enqueue analysis job" --> Celery
    
    %% Admin Interaction
    AdminUser[Admin User]
    AdminUser -- "Accesses" --> AdminUI

```

### 2.2. Asynchronous Post-Call Flow with Celery

To ensure a robust and scalable system, the post-call AI analysis is handled by a Celery task queue with Redis as the message broker.
1.  **Webhook Ingestion**: The API Layer receives the `end-of-call-report` webhook from VAPI.
2.  **Task Enqueueing**: The API Layer immediately enqueues an AI analysis task in the Celery queue, passing the necessary `call_id`. This makes the webhook response fast and reliable.
3.  **Task Execution**: A separate Celery worker process picks up the task from the queue.
4.  **Data Processing**: The Celery worker fetches the session transcript, runs the AI analysis, and updates the database with the results.
5.  **Error Handling**: The task queue provides built-in support for retries and error handling, ensuring that AI analysis is not lost in case of transient failures.

## 3. Security

-   **Authentication**:
    -   **Admin UI**: Secure, session-based login for the admin dashboard.
    -   **API Layer**: JWT-based authentication will be implemented to secure the API endpoints. The authentication flow will involve a dedicated `/auth/token` endpoint that returns a short-lived JWT upon successful credential validation.
-   **Webhook Security**: HMAC-SHA256 signature verification for all incoming webhooks.
-   **Secret Management**: All credentials will be managed through environment variables and a dedicated Flask configuration object.

## 4. Implementation Roadmap

1.  **Phase 1: Foundational Refactor**
    -   Restructure the project into the new layered architecture.
    -   Implement the Flask application with separate Blueprints for the Admin UI and the API layer.
2.  **Phase 2: Database Integration**
    -   Set up a managed PostgreSQL database on Render.
    -   Define the database schema using SQLAlchemy.
    -   Implement the repository and service layers.
3.  **Phase 3: Production-Grade Enhancements**
    -   Integrate Celery and Redis for asynchronous task processing.
    -   Implement the JWT-based authentication for the API layer.
    -   Implement comprehensive session analytics in the admin dashboard.
