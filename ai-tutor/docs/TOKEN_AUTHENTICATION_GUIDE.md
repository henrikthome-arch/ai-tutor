# Token-Based Authentication for Debugging and Testing

This guide explains how to use the token-based authentication system for debugging and regression testing the AI Tutor system.

## Overview

The AI Tutor system now supports token-based authentication for API access, which allows for:

- Debugging against the production environment without needing browser sessions
- Automated regression testing via scripts
- Secure access to system logs and diagnostics
- Integration with external monitoring tools

Tokens are short-lived, scope-limited JWT (JSON Web Token) credentials that can be generated from the admin UI. They provide a secure way to access the system's API endpoints without requiring a full browser session.

## Token Scopes

Tokens are issued with specific scopes that limit what they can access:

- `admin:read` - Access to admin dashboard statistics and system information
- `logs:read` - Access to system logs and diagnostics
- `tasks:read` - Access to background task status and information

## Generating Access Tokens

To generate an access token:

1. Log in to the Admin UI
2. Navigate to the "Tokens" page from the main navigation
3. Fill out the token generation form:
   - **Token Name/Description**: A descriptive name to identify the token's purpose
   - **Token Scopes**: Select the required scopes for your use case
   - **Expiration Time**: Choose how long the token should be valid (1 hour to 7 days)
4. Click "Generate Token"
5. Copy the generated token immediately - it will not be displayed again

![Token Generation Page](../docs/images/token_generation.png)

## Using Access Tokens

### HTTP Authorization Header

To use a token, include it in the `Authorization` header of your HTTP requests:

```
Authorization: Bearer YOUR_TOKEN_HERE
```

### Example API Requests

#### cURL Example

```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" https://your-tutor-instance.com/admin/api/logs
```

#### Python Example

```python
import requests

headers = {
    'Authorization': 'Bearer YOUR_TOKEN_HERE'
}
response = requests.get('https://your-tutor-instance.com/admin/api/logs', headers=headers)
print(response.json())
```

### Available API Endpoints

The following API endpoints support token-based authentication:

#### System Information

- `GET /admin/api/stats` - Get system-wide statistics (requires `admin:read` scope)
- `GET /admin/api/ai-stats` - Get AI processing statistics (requires `admin:read` scope)

#### Logs and Diagnostics

- `GET /admin/api/logs` - Get system logs (requires `logs:read` scope)
- `GET /admin/api/logs/sessions` - Get session logs (requires `logs:read` scope)

#### Task Management

- `GET /admin/api/task/<task_id>` - Get status of a specific task (requires `tasks:read` scope)

### MCP Server Access

The MCP server also supports token-based authentication for accessing system logs:

```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-07-19", "limit": 100}' \
  https://your-tutor-instance.com:3001/mcp/get-system-logs
```

## Managing Tokens

### Viewing Active Tokens

All active tokens are displayed on the Tokens page, showing:
- Token name/description
- Assigned scopes
- Creation and expiration dates

### Revoking Tokens

To revoke a token before its expiration:
1. Go to the Tokens page
2. Find the token in the "Active Tokens" list
3. Click the "Revoke" button

Revoked tokens are immediately invalidated and cannot be used again.

## Security Considerations

- Tokens are short-lived by design to limit the security risk if they are compromised
- Always use HTTPS when transmitting tokens
- Only assign the minimum scopes needed for your use case
- Revoke tokens when they are no longer needed
- Do not share tokens in public repositories or insecure channels

## Troubleshooting

### Invalid Token Errors

If you receive a 401 Unauthorized error with the message "Invalid or expired token", check:
- Has the token expired?
- Are you using the correct token?
- Is the token properly formatted in the Authorization header?

### Insufficient Scope Errors

If you receive a 403 Forbidden error with the message "Token missing required scope", check:
- Does your token have the necessary scope for the endpoint you're accessing?
- Are you using the correct endpoint for your use case?

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