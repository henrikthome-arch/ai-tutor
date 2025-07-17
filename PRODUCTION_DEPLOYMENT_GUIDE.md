# Production Deployment Guide - ai-tutor-ptnl.onrender.com

Complete step-by-step guide for deploying your AI-powered tutoring system to production.

## 🎯 Your Production URLs

- **Main Application**: `https://ai-tutor-ptnl.onrender.com`
- **Admin Dashboard**: `https://ai-tutor-ptnl.onrender.com/admin`
- **VAPI Webhook**: `https://ai-tutor-ptnl.onrender.com/vapi/webhook`
- **MCP Server**: Configure as needed for your infrastructure

## 🚀 Deployment Steps

### Step 1: Environment Variables on Render.com

Set these environment variables in your Render.com dashboard:

```bash
# Core Flask Configuration
FLASK_ENV=production
FLASK_SECRET_KEY=generate_64_char_random_string_here
ADMIN_PASSWORD=your_secure_admin_password

# AI Provider Configuration
OPENAI_API_KEY=sk-proj-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
AI_PROVIDER=openai
AI_MODEL=o3-mini

# VAPI Integration
VAPI_SECRET=your_vapi_webhook_secret_here

# Optional: Advanced Configuration
AI_MAX_COST_PER_REQUEST=5.00
AI_TIMEOUT_SECONDS=60
AI_MAX_RETRIES=3
```

### Step 2: Generate Secure Secrets

```bash
# Generate Flask secret key (64 characters)
python -c "import secrets; print(secrets.token_hex(32))"

# Generate VAPI webhook secret (64 characters)
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 3: Configure VAPI Dashboard

1. **Go to VAPI Dashboard** → Assistants
2. **Select your assistant** → Advanced tab
3. **Set Server URL**: `https://ai-tutor-ptnl.onrender.com/vapi/webhook`
4. **Set Secret**: Use the VAPI_SECRET value you generated
5. **Enable Server Messages**:
   - ✅ `speech-update`
   - ✅ `end-of-call-report`
   - ✅ `status-update`

### Step 4: Deploy to Render.com

1. **Connect Repository**: Link your GitHub repository
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `python admin-server.py`
4. **Environment**: Set to Python 3.11+
5. **Auto-Deploy**: Enable for automatic updates

### Step 5: Import Environment Variables

Use the clean [`render-production.env`](render-production.env) file:

1. Copy all KEY=VALUE pairs from the file
2. In Render.com dashboard → Environment tab
3. Add each variable individually with your actual values

## 🔍 Testing Your Production Deployment

### 1. Test Admin Dashboard

```bash
# Check admin access
curl -I https://ai-tutor-ptnl.onrender.com/admin

# Should return 200 OK and redirect to login
```

### 2. Test VAPI Webhook

```bash
# Test webhook endpoint (will return 405 Method Not Allowed for GET - this is correct)
curl -I https://ai-tutor-ptnl.onrender.com/vapi/webhook

# Should return 405 (expecting POST requests only)
```

### 3. Test with Real VAPI Call

1. **Make a test call** to your VAPI assistant
2. **Check Render.com logs** for webhook events:
   - `📞 VAPI webhook received: speech-update`
   - `📊 Call ca_xxx status: in-progress`
   - `📝 End of call ca_xxx: 180s duration`
   - `💾 Saved VAPI session: data/students/xxx`
   - `✅ AI analysis completed for call ca_xxx`

## 🔒 Security Checklist

### ✅ Environment Variables
- [ ] All API keys set as environment variables (not in code)
- [ ] VAPI_SECRET matches VAPI dashboard configuration
- [ ] FLASK_SECRET_KEY is 64+ random characters
- [ ] ADMIN_PASSWORD is strong and unique

### ✅ VAPI Configuration
- [ ] Webhook URL: `https://ai-tutor-ptnl.onrender.com/vapi/webhook`
- [ ] HMAC secret configured in VAPI dashboard
- [ ] Server messages enabled for all required events

### ✅ Application Security
- [ ] Flask runs in production mode (FLASK_ENV=production)
- [ ] Admin dashboard protected with authentication
- [ ] HTTPS enabled (automatic with Render.com)
- [ ] No sensitive data in logs or git repository

## 📊 Monitoring & Maintenance

### Application Logs

Monitor Render.com logs for:

```
✅ SUCCESS patterns:
- "📞 VAPI webhook received"
- "💾 Saved VAPI session"
- "✅ AI analysis completed"
- "Admin dashboard access: user authenticated"

❌ ERROR patterns:
- "❌ Signature verification failed"
- "❌ Student not found for phone"
- "❌ AI analysis failed"
- "❌ OpenAI/Anthropic API error"
```

### Cost Monitoring

Check AI usage costs regularly:

1. **OpenAI Dashboard**: Monitor O3 usage and costs
2. **Anthropic Console**: Track Claude usage
3. **Admin Dashboard**: Review cost estimates in session analysis

### Performance Monitoring

Monitor response times:

- **VAPI webhooks**: Should respond within 5 seconds
- **AI analysis**: Typically 15-45 seconds for complete analysis
- **Admin dashboard**: Page loads should be under 3 seconds

## 🚨 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Webhook not receiving calls** | Check VAPI URL configuration, verify HTTPS |
| **Signature verification failed** | Ensure VAPI_SECRET matches dashboard secret |
| **Student not found** | Check phone mapping in `data/phone_mapping.json` |
| **AI analysis timeout** | Increase `AI_TIMEOUT_SECONDS` environment variable |
| **Admin login failed** | Verify `ADMIN_PASSWORD` environment variable |

### Emergency Response

If webhooks fail:

1. **Check Render.com status**: Verify service is running
2. **Review environment variables**: Ensure all required vars are set
3. **Check VAPI logs**: Look for webhook delivery failures
4. **Restart service**: Redeploy if necessary

## 📞 VAPI Integration Flow

Complete end-to-end flow:

```
📱 Student calls VAPI number
    ↓
📡 VAPI processes call and sends webhook
    ↓
🔍 System identifies student by phone number
    ↓
💾 Session transcript saved to student directory
    ↓
🤖 AI analysis triggered (OpenAI O3 or Anthropic)
    ↓
📊 Results saved with confidence scores
    ↓
👨‍💼 Admin can review in dashboard
```

## 🎯 Next Steps After Deployment

1. **Test with Real Students**: Make test calls to verify complete workflow
2. **Monitor AI Costs**: Set up alerts for usage thresholds
3. **Review Session Quality**: Check AI analysis accuracy with real data
4. **Scale Resources**: Upgrade Render.com plan if needed for performance
5. **Add Monitoring**: Set up external monitoring for uptime/performance

## 📞 Support & Maintenance

### Regular Tasks

- **Weekly**: Review AI analysis quality and costs
- **Monthly**: Check system performance and update dependencies
- **Quarterly**: Review security settings and rotate secrets

### Backup Strategy

- **Student Data**: Regularly backup `data/` directory
- **Environment Config**: Keep secure copy of environment variables
- **Prompt Templates**: Version control all prompt files in `ai_poc/prompts/`

---

Your AI-powered tutoring system is now production-ready! The complete VAPI → AI analysis pipeline will automatically process every student call and provide detailed educational insights.

**Production URL**: https://ai-tutor-ptnl.onrender.com
**VAPI Webhook**: https://ai-tutor-ptnl.onrender.com/vapi/webhook