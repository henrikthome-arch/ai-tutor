# VAPI Webhook Integration Guide

Complete guide for integrating VAPI voice calls with AI post-processing system.

## 🎯 What I've Implemented

### ✅ Backend Changes Made

1. **VAPI Webhook Endpoint**: `/vapi/webhook` route in [`admin-server.py`](admin-server.py)
2. **HMAC Signature Verification**: Security validation of VAPI payloads
3. **Phone Number to Student Mapping**: Automatic student identification
4. **Session Data Storage**: Complete call transcripts saved to student directories
5. **Automatic AI Analysis**: Triggered after each call ends
6. **Real-time Event Handling**: Speech updates, status changes, and call completion

### 🔄 Complete Flow

```
📞 VAPI Call → 📡 Webhook → 🔍 Student Lookup → 💾 Save Session → 🤖 AI Analysis
```

## 🛠️ VAPI Configuration

### Step 1: Set Server URL in VAPI

**Option A: Assistant Level (Recommended)**

1. Go to VAPI Dashboard → Assistants
2. Select your assistant → Advanced tab
3. Set **Server URL**: `https://ai-tutor-ptnl.onrender.com/vapi/webhook`
4. Set **Secret**: Generate a secure secret for HMAC verification

**Option B: Account Level**

1. Go to VAPI Dashboard → Org Settings
2. Set global webhook URL for all assistants

### Step 2: Configure Webhook Events

Ensure these events are enabled in your assistant:

```json
{
  "serverMessages": [
    "speech-update",        // Real-time transcript chunks
    "end-of-call-report",   // Complete transcript + summary
    "status-update"         // Call status changes
  ]
}
```

### Step 3: Set Up Environment Variables

Add to your `.env` file:

```bash
# VAPI webhook secret (generate a secure random string)
VAPI_SECRET=your_secure_webhook_secret_here
```

In production, set this as an environment variable on your hosting platform.

## 🔒 Security Setup

### Generate VAPI Secret

```bash
# Generate a secure secret for HMAC verification
python -c "import secrets; print(secrets.token_hex(32))"
```

### Configure in VAPI

1. In VAPI Assistant settings, set the **Secret** field to your generated secret
2. This enables HMAC signature verification for webhook security

## 📡 Webhook Events Handled

### 1. `speech-update`
- **Purpose**: Real-time speech recognition updates
- **Action**: Logs final user speech for monitoring
- **Data**: `speaker`, `text`, `final`, `call.id`

### 2. `end-of-call-report`
- **Purpose**: Complete call transcript and metadata
- **Action**: 
  - Saves session to student directory
  - Triggers AI post-processing analysis
  - Creates transcript files
- **Data**: Complete transcript, duration, phone number, call metadata

### 3. `status-update`
- **Purpose**: Call status changes (ringing, answered, ended)
- **Action**: Logs for monitoring and debugging
- **Data**: `status`, `call.id`

## 💾 Data Storage Structure

When a call ends, the system creates:

```
data/students/{student_id}/sessions/
├── 2025-01-14_15-30-45_vapi_session.json    # Session metadata
└── 2025-01-14_15-30-45_vapi_transcript.txt  # Full transcript
```

### Session Metadata Example

```json
{
  "call_id": "ca_123456",
  "student_id": "emma_smith",
  "phone_number": "+1234567890",
  "start_time": "2025-01-14T15:30:45Z",
  "duration_seconds": 180,
  "session_type": "vapi_call",
  "transcript_file": "2025-01-14_15-30-45_vapi_transcript.txt",
  "user_transcript_length": 450,
  "assistant_transcript_length": 890,
  "vapi_data": { /* Complete VAPI response */ }
}
```

## 🤖 AI Analysis Integration

### Automatic Processing

After each call:

1. **Student Identification**: Phone number → student lookup
2. **Context Loading**: Student profile, preferences, learning history
3. **AI Analysis**: OpenAI O3 or Anthropic analysis using our prompt system
4. **Results Storage**: Analysis saved with validation scores

### Analysis Data

```json
{
  "provider_used": "openai",
  "confidence_score": 0.92,
  "processing_time": 3.45,
  "cost_estimate": 0.0234,
  "summary": "Student demonstrated strong understanding...",
  "strengths": ["Clear communication", "Logical thinking"],
  "areas_for_improvement": ["Math vocabulary", "Problem solving"],
  "recommendations": ["Practice word problems", "Review fractions"]
}
```

## 🧪 Testing Setup

### 1. Local Testing with ngrok

```bash
# Terminal 1: Start your Flask server
python admin-server.py

# Terminal 2: Create public tunnel
ngrok http 5000

# Use the ngrok URL in VAPI webhook configuration
# Example: https://abc123.ngrok.io/vapi/webhook
```

### 2. Test with VAPI CLI

```bash
# Install VAPI CLI
npm install -g @vapi-ai/cli

# Forward webhooks to local server
vapi listen --forward-to localhost:5000/vapi/webhook

# This creates a temporary webhook URL for testing
```

### 3. Test Call Flow

1. **Make a test call** to your VAPI assistant
2. **Check webhook logs** in your Flask terminal
3. **Verify data storage** in `data/students/` directory
4. **Check AI analysis** results in admin dashboard

## 🔍 Monitoring & Debugging

### Webhook Logs

The Flask server logs all webhook events:

```
📞 VAPI webhook received: speech-update
🗣️  Final user speech in call ca_123: "I need help with fractions"
📊 Call ca_123 status: in-progress
📝 End of call ca_123: 180s duration
📞 Phone: +1234567890
📄 User transcript: 450 chars
🤖 Assistant transcript: 890 chars
💾 Saved VAPI session: data/students/emma_smith/sessions/2025-01-14_15-30-45_vapi_session.json
✅ AI analysis completed for call ca_123
```

### Common Issues

| Issue | Solution |
|-------|----------|
| **No webhooks received** | Check ngrok URL, VAPI server URL configuration |
| **Signature verification failed** | Verify VAPI_SECRET matches VAPI dashboard secret |
| **Student not found** | Check phone number mapping in `data/phone_mapping.json` |
| **AI analysis failed** | Check OpenAI/Anthropic API keys and configuration |

## 📋 Production Deployment Checklist

### Environment Variables

```bash
# Required for production
VAPI_SECRET=your_secure_webhook_secret
OPENAI_API_KEY=sk-proj-your-key
FLASK_ENV=production
ADMIN_PASSWORD=secure_password
FLASK_SECRET_KEY=64_char_random_key
```

### VAPI Configuration

- [ ] Set production webhook URL: `https://yourdomain.com/vapi/webhook`
- [ ] Configure HMAC secret in VAPI dashboard
- [ ] Enable required serverMessages: `speech-update`, `end-of-call-report`
- [ ] Test with a live call

### Security Verification

- [ ] HMAC signature verification working
- [ ] No API keys in code/logs
- [ ] Environment variables properly set
- [ ] HTTPS enabled for production

## 🔗 Integration Points

### With Existing System

1. **MCP Server**: Student context loaded via existing MCP tools
2. **Phone Mapping**: Uses existing `data/phone_mapping.json`
3. **AI Post-Processing**: Uses existing AI POC system
4. **Admin Dashboard**: Webhook events visible in system monitoring

### Data Flow

```
VAPI Call
    ↓
Webhook Event
    ↓
Student Lookup (phone → student_id)
    ↓
Session Storage (transcript + metadata)
    ↓
AI Analysis (O3/Claude processing)
    ↓
Results Storage (analysis + validation)
    ↓
Admin Dashboard (monitoring + review)
```

## 🎯 Next Steps

After webhook integration:

1. **Test with real students**: Make test calls and verify analysis
2. **Monitor performance**: Check AI analysis quality and costs
3. **Tune prompts**: Adjust AI prompts based on real transcript data
4. **Add alerts**: Set up notifications for call analysis completion
5. **Scale resources**: Monitor and adjust cost limits and timeouts

---

Your VAPI integration is now complete! Every call will automatically:
- ✅ Save complete transcripts
- ✅ Identify students by phone number  
- ✅ Trigger AI analysis with O3/Claude
- ✅ Store results for admin review
- ✅ Provide real-time monitoring

The system bridges VAPI voice calls with your AI post-processing pipeline seamlessly.