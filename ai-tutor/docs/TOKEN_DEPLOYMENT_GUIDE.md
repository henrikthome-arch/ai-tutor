# Token-Based Authentication Deployment Guide

This guide explains how to deploy the token-based authentication system to the production environment.

## Prerequisites

Before deploying the token-based authentication system, ensure that you have:

1. Access to the production environment (Render.com)
2. Permissions to update environment variables
3. Ability to trigger a new deployment

## Deployment Steps

### 1. Update Dependencies

The token-based authentication system requires the Flask-JWT-Extended package. Add it to your production environment by:

1. Adding the following packages to your requirements.txt file:
   ```
   flask-jwt-extended==4.5.3
   pyjwt==2.8.0
   ```

2. Trigger a new deployment to install these dependencies.

### 2. Configure Environment Variables

The token-based authentication system requires a JWT secret key. Add it to your production environment by:

1. Log in to your Render.com dashboard
2. Navigate to your AI Tutor service
3. Go to the "Environment" tab
4. Add the following environment variable:
   ```
   JWT_SECRET_KEY=your-secure-random-secret-key
   ```
   (Replace `your-secure-random-secret-key` with a secure random string)

5. Click "Save Changes"

### 3. Deploy the Code

Deploy the token-based authentication code to the production environment:

1. Ensure all changes are committed and pushed to the main branch
2. Trigger a new deployment on Render.com

### 4. Uncomment the Token Management Link

After the deployment is complete and you've verified that the token-based authentication system is working correctly, uncomment the token management link in the base.html template:

1. Open `ai-tutor/frontend/templates/base.html`
2. Uncomment the token management link:
   ```html
   <a href="{{ url_for('main.admin_tokens') }}"
      class="{% if request.endpoint in ['main.admin_tokens', 'main.generate_token', 'main.revoke_token'] %}active{% endif %}">
      🔑 Tokens
   </a>
   ```
3. Commit and push the changes
4. Trigger a new deployment

## Verification

After deploying the token-based authentication system, verify that it's working correctly:

1. Log in to the Admin UI
2. Navigate to the Tokens page
3. Generate a new token
4. Use the token to access the API endpoints

## Troubleshooting

If you encounter issues with the token-based authentication system:

1. Check the Render.com logs for error messages
2. Verify that the JWT_SECRET_KEY environment variable is set correctly
3. Ensure that the Flask-JWT-Extended package is installed
4. Check that the token management link is using the correct route name

## Rollback

If you need to roll back the token-based authentication system:

1. Revert the commits that added the token-based authentication system
2. Push the changes to the main branch
3. Trigger a new deployment

## Security Considerations

1. Keep the JWT_SECRET_KEY secure and do not share it
2. Regularly rotate the JWT_SECRET_KEY
3. Use HTTPS for all API requests
4. Set appropriate token expiration times
5. Revoke tokens when they are no longer needed