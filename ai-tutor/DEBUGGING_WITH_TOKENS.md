# AI Tutor Token Authentication Guide

This guide explains how to use the token-based authentication system for debugging, AI assistant access, and automated testing of the AI Tutor system.

## Overview

The AI Tutor system provides token-based authentication for:
- **API Access**: Programmatic access to system logs and data
- **Browser Access**: AI assistants accessing the admin dashboard via URLs
- **MCP Server Access**: Model Context Protocol server integration
- **Automated Testing**: Regression testing and monitoring scripts
- **External Tools**: Integration with monitoring and debugging tools

## Security Model

### Token Generation Security
⚠️ **IMPORTANT**: Tokens can only be generated through the admin interface by authenticated administrators. There are NO public API endpoints for token generation.

### Authentication Methods
1. **Admin Password Login**: Traditional username/password authentication
2. **Token-Based Login**: URL parameter authentication for AI assistants
3. **API Bearer Token**: HTTP Authorization header for programmatic access

## Token Management

### Generating Tokens

1. Log into the admin interface with your admin credentials
2. Navigate to **System** → **Token Management**
3. Click **Generate New Token**
4. Configure the token:
   - **Name**: Descriptive name (e.g., "Claude AI Assistant", "Debug Session", "Monitoring Script")
   - **Scopes**: Select required permissions
   - **Expiration**: Set expiration time (default: 4 hours, max: 24 hours)

### Available Scopes

- `api:read` - Read system data via API endpoints
- `logs:read` - Access system logs and diagnostics
- `mcp:access` - Connect MCP servers
- `admin:read` - Read-only access to admin interface
- `tasks:read` - Access to background task status (if available)

### Token Expiration

- Tokens automatically expire after the configured time
- Expired tokens are automatically revoked
- Default expiration: 4 hours
- Maximum expiration: 24 hours
- Tokens are short-lived by design for security

## Browser Access for AI Assistants

### Token-Based Login URL

AI assistants can access the admin dashboard using token-based authentication:

```
https://ai-tutor-latest-uyq8.onrender.com/admin/login?token=YOUR_TOKEN_HERE
```

### Example Usage

1. Generate a token with `admin:read` scope in the admin interface
2. Copy the generated token immediately (it won't be displayed again)
3. Use the login URL with the token parameter:
   ```
   https://ai-tutor-latest-uyq8.onrender.com/admin/login?token=XRbs9-NmQsdqIFGtgy2apNRTtlC2LNnm9Dp5yPgB5yM
   ```
4. The AI assistant will be automatically logged in and redirected to the dashboard

### Session Information

When logged in via token:
- Session shows `token_user` as username
- Login method is recorded as `token`
- Token name is displayed in session info
- All admin actions are logged with token attribution

## API Access

### HTTP Authorization Header

To use a token for API access, include it in the `Authorization` header:

```
Authorization: Bearer YOUR_TOKEN_HERE
```

### Available API Endpoints

#### System Information
- `GET /admin/api/stats` - Get system-wide statistics (requires `admin:read` scope)
- `GET /admin/api/ai-stats` - Get AI processing statistics (requires `admin:read` scope)

#### Logs and Diagnostics
- `GET /api/v1/logs` - Get system logs (requires `logs:read` scope)
- `GET /api/v1/logs?date=YYYY-MM-DD` - Get logs for specific date
- `GET /api/v1/logs?level=ERROR&category=WEBHOOK&days=3` - Get filtered logs

### PowerShell Examples

#### Get System Logs
```powershell
$headers = @{
    "Authorization" = "Bearer YOUR_TOKEN_HERE"
    "Content-Type" = "application/json"
}

# Get recent logs
Invoke-RestMethod -Uri "https://ai-tutor-latest-uyq8.onrender.com/api/v1/logs" -Headers $headers

# Get logs with filters
Invoke-RestMethod -Uri "https://ai-tutor-latest-uyq8.onrender.com/api/v1/logs?days=3&level=ERROR" -Headers $headers

# Get logs for specific date
Invoke-RestMethod -Uri "https://ai-tutor-latest-uyq8.onrender.com/api/v1/logs?date=2025-01-21" -Headers $headers
```

#### Test Token Access
```powershell
# Test token validity
$response = Invoke-RestMethod -Uri "https://ai-tutor-latest-uyq8.onrender.com/api/v1/logs?limit=1" -Headers $headers
Write-Host "Token is valid. Found $($response.data.count) log entries."
```

### cURL Examples

#### Get System Logs
```bash
# Get recent logs
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -H "Content-Type: application/json" \
     "https://ai-tutor-latest-uyq8.onrender.com/api/v1/logs"

# Get filtered logs
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -H "Content-Type: application/json" \
     "https://ai-tutor-latest-uyq8.onrender.com/api/v1/logs?category=WEBHOOK&level=ERROR&days=1"

# Get system statistics
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     "https://ai-tutor-latest-uyq8.onrender.com/admin/api/stats"
```

### Python Examples

#### Basic API Access
```python
import requests

headers = {
    'Authorization': 'Bearer YOUR_TOKEN_HERE'
}

# Get system logs
response = requests.get('https://ai-tutor-latest-uyq8.onrender.com/api/v1/logs', headers=headers)
print(response.json())

# Get system statistics
stats_response = requests.get('https://ai-tutor-latest-uyq8.onrender.com/admin/api/stats', headers=headers)
print(stats_response.json())
```

#### Automated Monitoring Script
```python
import requests
import time
from datetime import datetime

class TutorMonitor:
    def __init__(self, token, base_url):
        self.headers = {'Authorization': f'Bearer {token}'}
        self.base_url = base_url
    
    def check_system_health(self):
        try:
            response = requests.get(f'{self.base_url}/admin/api/stats', headers=self.headers)
            response.raise_for_status()
            stats = response.json()
            
            print(f"[{datetime.now()}] System Status: {stats.get('server_status', 'Unknown')}")
            print(f"Total Students: {stats.get('total_students', 0)}")
            print(f"Sessions Today: {stats.get('sessions_today', 0)}")
            
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now()}] Health check failed: {e}")
    
    def get_recent_errors(self):
        try:
            response = requests.get(
                f'{self.base_url}/api/v1/logs?level=ERROR&days=1&limit=10',
                headers=self.headers
            )
            response.raise_for_status()
            logs = response.json()
            
            if logs['data']['count'] > 0:
                print(f"[{datetime.now()}] Found {logs['data']['count']} recent errors")
                for log in logs['data']['logs'][:5]:
                    print(f"  - {log['timestamp']}: {log['message']}")
            else:
                print(f"[{datetime.now()}] No recent errors found")
                
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now()}] Error log check failed: {e}")

# Usage
monitor = TutorMonitor('YOUR_TOKEN_HERE', 'https://ai-tutor-latest-uyq8.onrender.com')
monitor.check_system_health()
monitor.get_recent_errors()
```

### MCP Server Access

The MCP server supports token-based authentication for accessing system logs:

```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-01-21", "limit": 100}' \
  https://ai-tutor-latest-uyq8.onrender.com:3001/mcp/get-system-logs
```

## Token Management

### Viewing Active Tokens

All active tokens are displayed on the **System** → **Token Management** page, showing:
- Token name/description
- Assigned scopes
- Creation and expiration dates
- Time remaining until expiration

### Revoking Tokens

To revoke a token before its expiration:
1. Go to the **System** → **Token Management** page
2. Find the token in the "Active Tokens" list
3. Click the "Revoke" button

Revoked tokens are immediately invalidated and cannot be used again.

## Security Best Practices

### Token Security
- ⚠️ **Never share tokens in public repositories or documentation**
- 🔐 **Use minimum required scopes for each token**
- ⏰ **Set appropriate expiration times (tokens are short-lived by design)**
- 🗑️ **Revoke tokens when no longer needed**
- 📝 **Use descriptive names to track token usage**
- 🔒 **Always use HTTPS when transmitting tokens**

### Admin Interface Security
- 🔒 **Change default admin password in production**
- 🛡️ **Use strong passwords for admin accounts**
- 🔍 **Monitor token usage in system logs**
- ⚡ **Revoke suspicious or compromised tokens immediately**

### Network Security
- 🌐 **Always use HTTPS in production**
- 🔒 **Verify SSL certificates**
- 🚫 **Never send tokens over HTTP**
- 🔐 **Do not share tokens in insecure channels**

## Troubleshooting

### Common Issues

#### Invalid Token Errors
If you receive a 401 Unauthorized error with "Invalid or expired token":
- Has the token expired?
- Are you using the correct token?
- Is the token properly formatted in the Authorization header?
- Has the token been revoked?

#### Insufficient Scope Errors
If you receive a 403 Forbidden error with "Token missing required scope":
- Does your token have the necessary scope for the endpoint?
- Are you using the correct endpoint for your use case?
- Check the endpoint documentation for required scopes

#### Browser Login Failing
1. Verify token has `admin:read` scope
2. Check token expiration
3. Ensure URL is correctly formatted
4. Try copying token again to avoid character issues

#### API Access Denied
1. Verify `Authorization` header format: `Bearer YOUR_TOKEN`
2. Check required scopes for the endpoint
3. Confirm token is not expired
4. Review system logs for authentication errors

### Error Messages

- `Invalid token` - Token not found or malformed
- `Token expired` - Token has passed expiration time
- `Token does not have required scopes` - Missing required permissions
- `Missing or invalid Authorization header` - Header format issue

## Token Usage Monitoring

### Admin Interface Monitoring
- View active tokens in **System** → **Token Management**
- Monitor token usage in **System** → **Logs**
- Track authentication events in system logs

### Log Categories
- `ADMIN` - Admin interface actions
- `API` - API endpoint access
- `TOKEN` - Token-related events
- `SECURITY` - Authentication failures

## Integration Examples

### MCP Server Configuration
```json
{
  "servers": {
    "ai-tutor": {
      "command": "node",
      "args": ["path/to/mcp-server"],
      "env": {
        "AI_TUTOR_TOKEN": "YOUR_TOKEN_HERE",
        "AI_TUTOR_BASE_URL": "https://ai-tutor-latest-uyq8.onrender.com"
      }
    }
  }
}
```

### Claude Desktop Configuration
For AI assistants using the admin interface:

1. Generate token with `admin:read` scope
2. Use browser access URL:
   ```
   https://ai-tutor-latest-uyq8.onrender.com/admin/login?token=YOUR_TOKEN
   ```
3. Bookmark the URL for easy access
4. Monitor token expiration and regenerate as needed

### Automated Testing Scripts

#### Regression Test Example
```bash
#!/bin/bash
# AI Tutor System Health Check

TOKEN="YOUR_TOKEN_HERE"
BASE_URL="https://ai-tutor-latest-uyq8.onrender.com"

echo "Running AI Tutor system health check..."

# Test API access
echo "Testing API access..."
response=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/v1/logs?limit=1")
if [[ $? -eq 0 ]]; then
    echo "✓ API access successful"
else
    echo "✗ API access failed"
    exit 1
fi

# Test system stats
echo "Testing system statistics..."
stats=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/admin/api/stats")
if [[ $? -eq 0 ]]; then
    echo "✓ System stats accessible"
else
    echo "✗ System stats failed"
    exit 1
fi

echo "All tests passed!"
```

## Implementation Details

The token-based authentication system is implemented using:
- Simple in-memory token storage for debugging and development
- Scope-based authorization for fine-grained access control
- Custom Flask decorators for endpoint protection
- Token service for generation, validation, and management

For developers extending the system, see the implementation in:
- `backend/admin-server.py` - Main admin server with token authentication
- Token service class (lines 65-133) - Token generation and validation
- Token decorators (lines 135-181) - Authentication decorators
- API endpoints with `@token_required` decorator

## Production Deployment Notes

### Environment Variables
- `ADMIN_PASSWORD` - Secure admin password (never use default)
- `FLASK_SECRET_KEY` - Secure session key
- `DATABASE_URL` - PostgreSQL connection string
- `FLASK_ENV` - Set to 'production' for production deployment

### Security Checklist
- [ ] Admin password changed from default (`admin123`)
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Database connection secured with PostgreSQL
- [ ] Token expiration policies configured appropriately
- [ ] Log monitoring configured and working
- [ ] Backup and disaster recovery planned
- [ ] System logs being written to PostgreSQL database

## Support

For issues with token authentication:
1. Check system logs in **System** → **Logs** section of admin interface
2. Verify token configuration and scopes in **System** → **Token Management**
3. Test with fresh token generation
4. Review this documentation for proper usage patterns
5. Check that tokens are not being used after expiration
6. Ensure proper Authorization header format for API calls

---

*Last updated: 2025-01-21*
*Version: 2.0 - Consolidated from multiple token authentication guides*