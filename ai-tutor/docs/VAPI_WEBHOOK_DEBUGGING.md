# 🔧 VAPI Webhook Debugging Guide

## 🚨 Issue: VAPI Call Not Appearing in Dashboard

### **Checklist for VAPI Webhook Troubleshooting**

## 1. ✅ **Verify VAPI Dashboard Configuration**

### **Server Settings Should Be:**
- **Server URL**: `https://ai-tutor-ptnl.onrender.com/vapi/webhook`
- **Secret Token**: `YomZibB7ZYhys04nJqnWPhXmg2ddkPTJy8r3oLfRCEY=`
- **Timeout**: 20 seconds

### **Server Messages Should Include:**
- ✅ `conversation-update`
- ✅ `end-of-call-report` 
- ✅ `function-call`

---

## 2. 🔍 **Check Webhook Delivery**

### **Test Webhook Endpoint:**
```bash
curl -X POST https://ai-tutor-ptnl.onrender.com/vapi/webhook \
  -H "Content-Type: application/json" \
  -H "X-Vapi-Signature: test" \
  -d '{"message": {"type": "test"}}'
```

**Expected Response:** `{"status": "ok"}` with 200 status

---

## 3. 📱 **Check Phone Mapping**

### **Current Phone Mappings:**
To see existing mappings, go to: **Admin Dashboard > System > Phone Number Mappings**

### **For New Students (Unknown Phone):**
- VAPI should create directory: `../data/students/unknown_<phone_number>`
- Check if this directory exists after your call

### **Debug Commands:**
```bash
# Check for any new student directories
ls -la ai-tutor/data/students/

# Look for "unknown" directories
ls -la ai-tutor/data/students/ | grep unknown
```

---

## 4. 🔍 **Check Production Logs**

### **View Render.com Logs:**
1. Go to [Render.com Dashboard](https://dashboard.render.com)
2. Click on your AI Tutor service
3. Go to **Logs** tab
4. Look for webhook-related messages:
   - `📞 VAPI webhook received: end-of-call-report`
   - `💾 Saved VAPI session: ...`
   - `❌ Error handling end of call: ...`

### **Expected Log Flow:**
```
📞 VAPI webhook received: end-of-call-report
📞 Phone: +1234567890
📄 User transcript: 1250 chars
🤖 Assistant transcript: 890 chars
⚠️  No student found for phone: +1234567890
💾 Saved VAPI session: ../data/students/unknown_1234567890/sessions/...
✅ AI analysis completed for call abc123
```

---

## 5. 🔧 **Debug Webhook Handler**

### **Check HMAC Verification:**
The webhook might be failing HMAC verification. Look for logs:
- `🚨 VAPI webhook signature verification failed`

### **Disable HMAC Temporarily (for testing):**
In `admin-server.py`, temporarily modify:
```python
def verify_vapi_signature(payload_body, signature):
    # TEMPORARY: Skip verification for debugging
    return True
```

**⚠️ Remember to re-enable after testing!**

---

## 6. 📊 **Manual Webhook Test**

### **Send Test Webhook Manually:**
```bash
curl -X POST https://ai-tutor-ptnl.onrender.com/vapi/webhook \
  -H "Content-Type: application/json" \
  -H "X-Vapi-Signature: YomZibB7ZYhys04nJqnWPhXmg2ddkPTJy8r3oLfRCEY=" \
  -d '{
    "message": {
      "type": "end-of-call-report",
      "call": {
        "id": "test-call-123",
        "customer": {
          "number": "+1234567890"
        }
      },
      "durationSeconds": 180,
      "transcript": {
        "user": "Hi, my name is Test Student",
        "assistant": "Nice to meet you, Test Student!"
      }
    }
  }'
```

**This should create:** `../data/students/unknown_1234567890/sessions/`

---

## 7. 🎯 **Common Issues & Solutions**

### **Issue: Webhook URL Wrong**
- **Solution**: Update VAPI dashboard with correct URL
- **Verify**: `https://ai-tutor-ptnl.onrender.com/vapi/webhook` (not `/webhook`)

### **Issue: Secret Mismatch**
- **Solution**: Copy exact secret: `YomZibB7ZYhys04nJqnWPhXmg2ddkPTJy8r3oLfRCEY=`
- **Verify**: Check environment variable in Render.com

### **Issue: Server Sleeping**
- **Solution**: Render.com free tier sleeps after inactivity
- **Fix**: Make a test request to wake it up first

### **Issue: Wrong Message Types**
- **Solution**: Ensure `end-of-call-report` is enabled in VAPI dashboard
- **Check**: Server Messages configuration

---

## 8. 🚀 **Quick Verification Steps**

### **Step 1: Test Webhook Endpoint**
Visit: `https://ai-tutor-ptnl.onrender.com/`
Should show: Redirect to admin dashboard

### **Step 2: Check Student Directory**
After your VAPI call, check:
```bash
ls -la ai-tutor/data/students/
```
Look for new directories (either mapped student or `unknown_*`)

### **Step 3: Check Admin Dashboard**
Go to: Admin Dashboard > Students
New student should appear in the list

---

## 🎯 **Next Steps Based on Findings**

### **If No Logs in Render.com:**
- VAPI webhook URL is wrong
- VAPI webhook not configured
- Server is sleeping

### **If Logs Show Errors:**
- HMAC verification failing
- Path/directory permission issues
- Python errors in webhook handler

### **If Logs Show Success but No Student:**
- File creation permissions
- Directory structure issues
- Admin dashboard not refreshing data

---

## 📞 **Test Call Information**
- **Phone**: `+1 (539) 589-2719`
- **SIP**: `sip:ai-tutor-by-henrik@sip.vapi.ai`
- **Expected Result**: New student appears in dashboard within 1-2 minutes

Run through this checklist systematically to identify where the webhook integration is failing!