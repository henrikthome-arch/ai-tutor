# Testing VAPI Webhook Integration on Render.com

This guide provides instructions for testing the VAPI webhook integration on Render.com.

## Prerequisites

- Access to the Render.com dashboard for the AI Tutor deployment
- A VAPI account or test environment
- The Render.com deployment URL (e.g., `https://ai-tutor.onrender.com`)

## Testing Steps

### 1. Verify Database Configuration

First, ensure that the PostgreSQL database is properly configured on Render.com:

1. Go to the Render.com dashboard
2. Select your AI Tutor web service
3. Go to the "Environment" tab
4. Verify that `DATABASE_URL` is set to a valid PostgreSQL connection string
5. Verify that `VAPI_SECRET` is set (if you're using HMAC verification)

### 2. Run Database Verification

Use the Render.com shell to run the database verification script:

1. Go to the Render.com dashboard
2. Select your AI Tutor web service
3. Go to the "Shell" tab
4. Run the following commands:

```bash
cd ai-tutor/backend
python verify_database.py
```

This will verify that all required tables exist in the database, including the `system_logs` table.

### 3. Run System Logs Check

Check if the system_logs table is properly configured and accessible:

```bash
cd ai-tutor/backend
python check_system_logs.py
```

This will check if the system_logs table exists and has entries.

### 4. Fix VAPI Integration Issues

If there are issues with the VAPI webhook integration, run the fix script:

```bash
cd ai-tutor/backend
python fix_vapi_integration.py
```

This script will:
- Ensure the system_logs table exists
- Test creating a log entry
- Test webhook logging
- Check app context in webhook handler

### 5. Send a Test Webhook

Use the test script to send a test webhook to your deployment:

```bash
cd ai-tutor/backend
export WEBHOOK_URL=https://your-deployment-url.onrender.com/vapi/webhook
export VAPI_SECRET=your_vapi_secret_here
python test_vapi_webhook.py
```

Replace `your-deployment-url.onrender.com` with your actual Render.com deployment URL and `your_vapi_secret_here` with your actual VAPI secret.

### 6. Check the Logs

After sending the test webhook, check the logs to see if it was processed correctly:

1. Go to the Render.com dashboard
2. Select your AI Tutor web service
3. Go to the "Logs" tab
4. Look for log entries related to the webhook processing

You should see log entries like:
- `VAPI webhook received - starting processing`
- `Processing end-of-call-report with app context`
- `Student identified/created`
- `Saved session to database`

### 7. Verify in Admin Dashboard

Finally, verify that the webhook created the expected database entries:

1. Go to your AI Tutor admin dashboard (e.g., `https://your-deployment-url.onrender.com/admin`)
2. Log in with your admin credentials
3. Go to the "Students" page to see if a new student was created
4. Go to the "Sessions" page to see if a new session was created
5. Go to the "Logs" page to see if webhook logs were created

## Troubleshooting

### System Logs Table Does Not Exist

If the system_logs table does not exist, run the fix script:

```bash
cd ai-tutor/backend
python fix_vapi_integration.py
```

### No Webhook Logs Being Created

If no webhook logs are being created, check:

1. The VAPI webhook URL is correct
2. The VAPI secret is correctly configured
3. The system_logs table exists
4. The webhook handler has proper app context management

### No Students or Sessions Being Created

If no students or sessions are being created, check:

1. The webhook logs for any errors
2. The database connection is working
3. The webhook handler is properly processing the webhook data
4. The database transactions are being committed

## Important Notes

- All testing should be done in the deployment environment on Render.com
- Local testing may not accurately reflect the production environment
- Always check the Render.com logs for detailed error messages
- Remember that database operations require proper app context management