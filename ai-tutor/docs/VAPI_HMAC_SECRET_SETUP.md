# VAPI HMAC Secret Setup Guide

## 🔒 Generate Secure HMAC Secret

### Step 1: Generate a Secure Secret

**Option A: Using Python (Recommended)**
```python
import secrets
import base64

# Generate a secure 32-byte secret
secret_bytes = secrets.token_bytes(32)
hmac_secret = base64.b64encode(secret_bytes).decode('utf-8')
print(f"VAPI_SECRET={hmac_secret}")
```

**Option B: Using OpenSSL Command Line**
```bash
openssl rand -base64 32
```

**Option C: Using Node.js**
```javascript
const crypto = require('crypto');
const secret = crypto.randomBytes(32).toString('base64');
console.log(`VAPI_SECRET=${secret}`);
```

**Generated Secret Example:**
```
VAPI_SECRET=rX8k9mN2pQ7sV4tY6wZ3cF5gH8jL1nM4rP7sT0uW3xA=
```

### Step 2: Configure in Render.com

1. **Go to Render.com Dashboard**
   - Navigate to: https://dashboard.render.com
   - Select your `ai-tutor` service

2. **Add Environment Variable**
   - Go to **Environment** tab
   - Click **Add Environment Variable**
   - Set:
     - **Key**: `VAPI_SECRET`
     - **Value**: `[YOUR_GENERATED_SECRET]`
   - Click **Save Changes**

3. **Deploy Changes**
   - Render will automatically redeploy with the new environment variable

### Step 3: Configure in VAPI Dashboard

1. **Access VAPI Dashboard**
   - Go to: https://dashboard.vapi.ai
   - Navigate to your assistant/phone number settings

2. **Set Webhook Configuration**
   - **Webhook URL**: `https://ai-tutor-ptnl.onrender.com/vapi/webhook`
   - **Secret**: `[YOUR_GENERATED_SECRET]` (same as Step 2)

3. **Enable Webhook Events**
   - ✅ `speech-update` (real-time transcription)
   - ✅ `end-of-call-report` (complete transcript)
   - ✅ `status-update` (call status changes)

## 🔧 Complete Configuration Example

### Environment Variables for Render.com
```bash
VAPI_SECRET=rX8k9mN2pQ7sV4tY6wZ3cF5gH8jL1nM4rP7sT0uW3xA=
FLASK_ENV=production
ADMIN_PASSWORD=your_secure_admin_password
FLASK_SECRET_KEY=your_flask_secret_key
```

### VAPI Assistant Configuration
```json
{
  "webhook": {
    "url": "https://ai-tutor-ptnl.onrender.com/vapi/webhook",
    "secret": "rX8k9mN2pQ7sV4tY6wZ3cF5gH8jL1nM4rP7sT0uW3xA="
  },
  "events": [
    "speech-update",
    "end-of-call-report", 
    "status-update"
  ]
}
```

## 🧪 Testing the Integration

### Test Webhook Security
```bash
# Test without signature (should fail)
curl -X POST https://ai-tutor-ptnl.onrender.com/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# Expected response: 401 Unauthorized
```

### Test with Valid Signature
```python
import hmac
import hashlib
import requests

# Your secret and payload
secret = "rX8k9mN2pQ7sV4tY6wZ3cF5gH8jL1nM4rP7sT0uW3xA="
payload = '{"message": {"type": "test"}}'

# Generate signature
signature = hmac.new(
    secret.encode('utf-8'),
    payload.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# Send request
response = requests.post(
    'https://ai-tutor-ptnl.onrender.com/vapi/webhook',
    headers={
        'Content-Type': 'application/json',
        'X-Vapi-Signature': signature
    },
    data=payload
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
```

## 🚨 Security Best Practices

### Secret Management
- **Never commit secrets to git** ❌
- **Use environment variables** ✅
- **Rotate secrets periodically** ✅
- **Use strong, random secrets** ✅

### Production Checklist
- [ ] Generated secure 32-byte secret
- [ ] Added `VAPI_SECRET` to Render.com environment
- [ ] Configured webhook URL in VAPI dashboard
- [ ] Set matching secret in VAPI dashboard
- [ ] Tested webhook with signature verification
- [ ] Confirmed call transcripts are being processed

## 🔍 Troubleshooting

### Common Issues

**1. 401 Unauthorized Errors**
- Check secret matches between Render.com and VAPI
- Verify signature generation algorithm
- Ensure secret is base64 encoded

**2. 500 Internal Server Errors**
- Check Render.com logs for Python errors
- Verify all environment variables are set
- Test webhook locally first

**3. No Transcript Processing**
- Confirm VAPI events are enabled
- Check webhook URL is correct
- Verify phone number mapping exists

### Debug Commands
```bash
# Check environment variables in Render.com
echo $VAPI_SECRET

# Test webhook endpoint
curl https://ai-tutor-ptnl.onrender.com/vapi/webhook

# View application logs
# (Available in Render.com dashboard)
```

## 📞 Phone Number Mapping

Don't forget to update your phone mappings in:
`ai-tutor/data/phone_mapping.json`

```json
{
  "555-123-4567": "emma_smith",
  "555-987-6543": "jane_doe"
}
```

## ✅ Success Indicators

When properly configured, you should see:
- ✅ Webhook responds with `200 OK` for valid requests
- ✅ Call transcripts appear in student session directories
- ✅ AI analysis is triggered automatically
- ✅ Admin dashboard shows new sessions
- ✅ No signature verification errors in logs

---

**🎯 Next Step**: Test with a live phone call to verify end-to-end functionality!