# AI Tutor MCP Server

This is a Model Context Protocol (MCP) server that provides access to student data for the AI tutoring system.

## Setup Instructions

### 1. Install Dependencies

```bash
cd mcp-server
npm install
```

### 2. Build the TypeScript Code

```bash
npm run build
```

### 3. Start the Server

```bash
npm start
```

Or for development with automatic recompilation:

```bash
npm run dev
```

## Available Endpoints

The server runs on `http://localhost:3000` by default.

### Health Check
- `GET /health` - Returns server status

### MCP Tools Manifest
- `GET /mcp/tools` - Returns list of available tools and their schemas

### MCP Tool Endpoints

All tool endpoints use POST requests and return JSON responses.

#### 1. Get Student Profile
- **Endpoint**: `POST /mcp/get-student-profile`
- **Purpose**: Get detailed profile information for a student
- **Request Body**:
  ```json
  {
    "student_id": "emma_smith"
  }
  ```

#### 2. Get Student Progress
- **Endpoint**: `POST /mcp/get-student-progress`
- **Purpose**: Get current progress assessment across all subjects
- **Request Body**:
  ```json
  {
    "student_id": "emma_smith"
  }
  ```

#### 3. Get Curriculum Data
- **Endpoint**: `POST /mcp/get-curriculum`
- **Purpose**: Get curriculum requirements and learning goals
- **Request Body**:
  ```json
  {
    "curriculum_name": "international_school_greece",
    "grade": "4",
    "subject": "mathematics"
  }
  ```

#### 4. Get Session Summary
- **Endpoint**: `POST /mcp/get-session-summary`
- **Purpose**: Get detailed summary of a specific session
- **Request Body**:
  ```json
  {
    "student_id": "emma_smith",
    "session_date": "2025-01-14"
  }
  ```

#### 5. Get Session Transcript
- **Endpoint**: `POST /mcp/get-session-transcript`
- **Purpose**: Get full conversation transcript from a session
- **Request Body**:
  ```json
  {
    "student_id": "emma_smith",
    "session_date": "2025-01-14"
  }
  ```

#### 6. Get Recent Sessions
- **Endpoint**: `POST /mcp/get-recent-sessions`
- **Purpose**: Get summaries of recent sessions
- **Request Body**:
  ```json
  {
    "student_id": "emma_smith",
    "limit": 5
  }
  ```

#### 7. Get Student Context (Comprehensive)
- **Endpoint**: `POST /mcp/get-student-context`
- **Purpose**: Get all student data in one call (profile, progress, recent sessions, curriculum)
- **Request Body**:
  ```json
  {
    "student_id": "emma_smith"
  }
  ```

## Data Structure

The server expects the following directory structure in the parent directory:

```
data/
├── curriculum/
│   └── international_school_greece.json
└── students/
    └── emma_smith/
        ├── profile.json
        ├── progress.json
        └── sessions/
            ├── 2025-01-14_transcript.txt
            └── 2025-01-14_summary.json
```

## Testing the Server

1. Start the server:
   ```bash
   npm start
   ```

2. Test the health endpoint:
   ```bash
   curl http://localhost:3000/health
   ```

3. Test getting student context:
   ```bash
   curl -X POST http://localhost:3000/mcp/get-student-context \
     -H "Content-Type: application/json" \
     -d '{"student_id": "emma_smith"}'
   ```

## Environment Variables

- `PORT` - Server port (default: 3000)

## Exposing to Internet (for OpenAI Assistant)

To make this server accessible to OpenAI Assistant, you'll need to expose it to the internet. The recommended approach for development is using ngrok:

1. Install ngrok: https://ngrok.com/download
2. Start your MCP server: `npm start`
3. In another terminal, expose the server: `ngrok http 3000`
4. Use the generated ngrok URL in your OpenAI Assistant tool configuration

Example ngrok output:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:3000
```

Use `https://abc123.ngrok.io` as your tool endpoint base URL in OpenAI Assistant.

## Security Notes

- This is a development server with no authentication
- Do not use in production without proper security measures
- The ngrok tunnel exposes your local data to the internet
- Only use with test data, not real student information