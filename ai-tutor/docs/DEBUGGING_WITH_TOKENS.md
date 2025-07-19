# Debugging and Testing with Access Tokens

This guide explains how to use token-based authentication for debugging and testing the AI Tutor system, with a specific focus on troubleshooting transcript analysis issues. It includes instructions for both human developers and AI assistants.

## Overview

The AI Tutor system supports token-based authentication for API access and debugging. This allows you to:

- Debug issues in the production environment without needing browser sessions
- Access system logs and diagnostics to identify problems
- Test specific components like transcript analysis
- Perform regression testing to ensure system stability
- Enable AI assistants to help with debugging by providing them with tokens

## Prerequisites

- Access to the Admin UI to generate tokens
- Basic understanding of HTTP requests and APIs
- Familiarity with the AI Tutor system architecture

## Generating Access Tokens

1. **Log in to the Admin UI**
   - URL: `https://ai-tutor-ptnl.onrender.com/admin/login`
   - Use your admin credentials

2. **Navigate to the Tokens Page**
   - Click on "🔑 Tokens" in the main navigation

3. **Generate a New Token**
   - Fill out the token generation form:
     - **Token Name**: A descriptive name (e.g., "Transcript Analysis Debug")
     - **Token Scopes**: Select appropriate scopes:
       - `logs:read` - For accessing system logs
       - `api:read` - For accessing API endpoints
       - `mcp:access` - For accessing MCP server functionality
     - **Expiration Time**: Choose an appropriate duration (1-24 hours recommended for debugging)
   - Click "Generate Token"
   - **Copy the token immediately** - it will not be displayed again

## Using Access Tokens for Debugging

### 1. Accessing System Logs

System logs can provide valuable information about errors in transcript analysis:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  https://ai-tutor-ptnl.onrender.com/admin/api/logs?category=TRANSCRIPT_ANALYSIS&days=1
```

This will return logs related to transcript analysis from the past day.

### 2. Accessing MCP Server for Student Data

The MCP server provides access to student data, including session transcripts:

```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"student_id": "student_id_here"}' \
  https://ai-tutor-ptnl.onrender.com:3001/mcp/get-student-context
```

### 3. Retrieving Session Transcripts

To examine a specific session transcript:

```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"student_id": "student_id_here", "session_date": "YYYY-MM-DD"}' \
  https://ai-tutor-ptnl.onrender.com:3001/mcp/get-session-transcript
```

## Debugging Transcript Analysis Issues

### Common Issues and Solutions

1. **No Information Extracted from Transcript**

   **Symptoms:**
   - Student profile not updated after a call
   - No information extracted from the transcript
   
   **Debugging Steps:**
   
   a. **Check System Logs for Errors**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     https://ai-tutor-ptnl.onrender.com/admin/api/logs?category=TRANSCRIPT_ANALYSIS&level=ERROR&days=1
   ```
   
   b. **Examine the Raw Transcript**
   ```bash
   curl -X POST -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -H "Content-Type: application/json" \
     -d '{"student_id": "student_id_here", "session_date": "YYYY-MM-DD"}' \
     https://ai-tutor-ptnl.onrender.com:3001/mcp/get-session-transcript
   ```
   
   c. **Check AI Provider Status**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     https://ai-tutor-ptnl.onrender.com/admin/api/ai-stats
   ```
   
   **Potential Solutions:**
   - Transcript too short (less than 100 characters)
   - AI provider API error or rate limiting
   - JSON parsing error in the AI response
   - No explicit student information in the transcript

2. **Incorrect Information Extracted**

   **Symptoms:**
   - Wrong age, grade, or interests added to student profile
   
   **Debugging Steps:**
   
   a. **Check the AI Analysis Response**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     https://ai-tutor-ptnl.onrender.com/admin/api/logs?category=AI_ANALYSIS&days=1
   ```
   
   b. **Examine the Student Profile**
   ```bash
   curl -X POST -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -H "Content-Type: application/json" \
     -d '{"student_id": "student_id_here"}' \
     https://ai-tutor-ptnl.onrender.com:3001/mcp/get-student-profile
   ```
   
   **Potential Solutions:**
   - Adjust AI prompt for better information extraction
   - Improve validation of extracted information
   - Add more explicit questions in the conversation script

## Testing Transcript Analysis with Sample Data

You can test the transcript analysis system with sample data:

```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Student: Hi, my name is John. I am 10 years old and in 4th grade. I really like math and playing soccer.",
    "test_mode": true
  }' \
  https://ai-tutor-ptnl.onrender.com/admin/api/test-transcript-analysis
```

This will process the sample transcript and return the extracted information without updating any student profiles.

## Regression Testing

To ensure that transcript analysis continues to work correctly after code changes:

1. **Create a Test Suite**
   - Prepare a set of sample transcripts with known information
   - Create a script that sends each transcript for analysis
   - Verify that the extracted information matches the expected values

2. **Automate Testing**
   ```python
   import requests
   import json
   
   TOKEN = "YOUR_TOKEN_HERE"
   BASE_URL = "https://ai-tutor-ptnl.onrender.com"
   
   def test_transcript_analysis(transcript, expected_info):
       headers = {
           "Authorization": f"Bearer {TOKEN}",
           "Content-Type": "application/json"
       }
       
       data = {
           "transcript": transcript,
           "test_mode": True
       }
       
       response = requests.post(
           f"{BASE_URL}/admin/api/test-transcript-analysis",
           headers=headers,
           json=data
       )
       
       result = response.json()
       
       # Compare result with expected_info
       # Return success/failure
   
   # Run tests with various sample transcripts
   ```

## Troubleshooting Token Issues

### Invalid Token Errors

If you receive a 401 Unauthorized error:
- Check if the token has expired
- Verify you're using the correct token
- Ensure the token is properly formatted in the Authorization header

### Insufficient Scope Errors

If you receive a 403 Forbidden error:
- Check if your token has the necessary scope for the endpoint
- Generate a new token with the required scopes

## Best Practices

1. **Use Short-Lived Tokens**
   - Generate tokens with short expiration times for security
   - Revoke tokens when debugging is complete

2. **Log Debugging Activities**
   - Keep notes of what you tested and the results
   - Document any fixes or improvements made

3. **Test in Isolation**
   - Test individual components before testing the entire system
   - Use test mode when available to avoid affecting production data

4. **Review AI Provider Settings**
   - Check AI provider configuration for transcript analysis
   - Adjust temperature or other settings if needed

## Implementation Details

The token-based authentication system is implemented using:
- JWT (JSON Web Tokens) for secure, stateless authentication
- Scope-based authorization for fine-grained access control
- Custom Flask decorators for endpoint protection
- Token service for generation, validation, and management

For developers extending the system, see the implementation in:
- `app/services/token_service.py` - Token generation and validation
- `app/auth/decorators.py` - Authentication decorators
- `app/api/v1/routes.py` - Protected API endpoints
- `backend/transcript_analyzer.py` - Transcript analysis implementation

## For AI Assistants: Using Provided Tokens

When an admin provides you with an access token, you can use it to help debug issues in the AI Tutor system:

### 1. Understanding the Token

The token provided by the admin is a JWT (JSON Web Token) that grants temporary access to specific parts of the system. It has:
- Limited scope (what you can access)
- Limited duration (when it expires)
- Specific permissions (what actions you can perform)

### 2. Using the Token for API Requests

When the admin provides you with a token like `5cNCenWTWC9TWzVVAoYkEw08BCjbcmdAJzZSsLRxTBE`, you can use it to make API requests to investigate issues:

```bash
# Example: Checking system logs for transcript analysis errors
curl -H "Authorization: Bearer 5cNCenWTWC9TWzVVAoYkEw08BCjbcmdAJzZSsLRxTBE" \
  https://ai-tutor-ptnl.onrender.com/admin/api/logs?category=TRANSCRIPT_ANALYSIS&level=ERROR&days=1
```

### 3. Debugging Transcript Analysis Issues

To investigate why information wasn't extracted from a call transcript:

1. **Check the system logs for errors**:
```bash
curl -H "Authorization: Bearer 5cNCenWTWC9TWzVVAoYkEw08BCjbcmdAJzZSsLRxTBE" \
  https://ai-tutor-ptnl.onrender.com/admin/api/logs?category=TRANSCRIPT_ANALYSIS&level=ERROR&days=1
```

2. **Examine the transcript content**:
```bash
curl -X POST -H "Authorization: Bearer 5cNCenWTWC9TWzVVAoYkEw08BCjbcmdAJzZSsLRxTBE" \
  -H "Content-Type: application/json" \
  -d '{"student_id": "student_id_here"}' \
  https://ai-tutor-ptnl.onrender.com:3001/mcp/get-recent-sessions
```

3. **Check AI provider status**:
```bash
curl -H "Authorization: Bearer 5cNCenWTWC9TWzVVAoYkEw08BCjbcmdAJzZSsLRxTBE" \
  https://ai-tutor-ptnl.onrender.com/admin/api/ai-stats
```

### 4. Reporting Findings

After investigating, provide the admin with:
- The specific error messages found in logs
- The likely cause of the issue
- Recommended solutions
- Any patterns you noticed in the data

### 5. Security Considerations

- Never share the token with anyone other than the admin who provided it
- Don't store the token beyond the current debugging session
- Only use the token for the specific debugging task requested
- Report any security concerns immediately