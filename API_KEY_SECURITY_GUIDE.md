# API Key Security Guide

## 🔐 **Secure API Key Management**

### **Environment Variables - The Secure Way**

**✅ NEVER put API keys directly in code files**  
**✅ ALWAYS use environment variables**  
**✅ NEVER commit API keys to git**

## 📝 **How to Add API Keys**

### **Step 1: Update Environment Configuration**

Create/Update your local `.env` file:

```bash
# Copy the example template
cp .env.example .env

# Edit with your actual keys
code .env
```

Add your API keys to `.env`:
```bash
# AI Provider API Keys
OPENAI_API_KEY=sk-your-actual-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here
GOOGLE_API_KEY=your-google-gemini-key-here

# Cost and Rate Limiting
AI_COST_LIMIT_DAILY=10.00
AI_RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Admin Security
ADMIN_PASSWORD=your-secure-admin-password-here
SECRET_KEY=your-super-secret-flask-key-here

# Environment
ENVIRONMENT=development
AI_PROVIDER=openai
```

### **Step 2: Install python-dotenv (Recommended)**

```bash
pip install python-dotenv
```

This automatically loads `.env` files and provides better environment variable management.

### **Step 3: Test Your Configuration**

```bash
# Test that environment variables are loaded
python -c "
import os
print('OpenAI Key:', 'sk-' + '*' * 20 if os.getenv('OPENAI_API_KEY') else 'NOT SET')
print('Anthropic Key:', 'sk-ant-' + '*' * 20 if os.getenv('ANTHROPIC_API_KEY') else 'NOT SET')
print('Environment:', os.getenv('ENVIRONMENT', 'NOT SET'))
"
```

## 🛡️ **Production Security**

### **Render.com Deployment (Recommended)**

1. **Set Environment Variables in Dashboard:**
   - Go to your Render service dashboard
   - Navigate to "Environment" tab
   - Add each variable individually:
     ```
     OPENAI_API_KEY = sk-your-key-here
     ANTHROPIC_API_KEY = sk-ant-your-key-here
     ADMIN_PASSWORD = your-secure-password
     SECRET_KEY = generated-secret-key
     ENVIRONMENT = production
     ```

2. **Verify Security:**
   - Keys are encrypted at rest
   - Only visible to service at runtime
   - Not exposed in logs or git
   - Accessible only to your account

### **Railway Deployment**

1. **Add Variables via CLI:**
   ```bash
   railway variables set OPENAI_API_KEY=sk-your-key-here
   railway variables set ANTHROPIC_API_KEY=sk-ant-your-key-here
   railway variables set ENVIRONMENT=production
   ```

2. **Or via Dashboard:**
   - Go to project settings
   - Variables tab
   - Add each key securely

### **Heroku Deployment**

```bash
heroku config:set OPENAI_API_KEY=sk-your-key-here
heroku config:set ANTHROPIC_API_KEY=sk-ant-your-key-here
heroku config:set ENVIRONMENT=production
```

## 🔍 **How to Verify Keys Aren't Exposed**

### **Check 1: Git Repository**
```bash
# Search for any API keys in git history
git log --all --grep="sk-" --oneline
git log --all --grep="API" --oneline

# Search current files
grep -r "sk-" . --exclude-dir=.git
grep -r "API.*KEY" . --exclude-dir=.git
```

### **Check 2: Code Files**
```bash
# Ensure no hardcoded keys
find . -name "*.py" -exec grep -l "sk-" {} \;
find . -name "*.js" -exec grep -l "sk-" {} \;
```

### **Check 3: Environment Loading**
```bash
# Test that keys are properly loaded from environment
python -c "
import os
from ai_poc.config import ai_config

print('✅ Keys loaded from environment variables:')
print('OpenAI:', '***' + ai_config.openai_api_key[-4:] if ai_config.openai_api_key else '❌ NOT SET')
print('Anthropic:', '***' + ai_config.anthropic_api_key[-4:] if ai_config.anthropic_api_key else '❌ NOT SET')
print('Environment:', os.getenv('ENVIRONMENT'))
"
```

### **Check 4: Production Logs**
- **✅ Good**: `"Using OpenAI API (****abcd)"`
- **❌ Bad**: `"API Key: sk-1234567890abcdef"`

Ensure your logs mask API keys.

## ⚠️ **Security Best Practices**

### **1. Key Rotation**
```bash
# Rotate keys regularly (recommended: every 3-6 months)
# 1. Generate new key from provider
# 2. Update environment variable
# 3. Test system works
# 4. Revoke old key
```

### **2. Principle of Least Privilege**
- Create separate API keys for development/staging/production
- Use different OpenAI projects for different environments
- Limit key permissions where possible

### **3. Monitoring and Alerts**
- Monitor API usage for unusual patterns
- Set up cost alerts
- Track failed authentication attempts

### **4. Key Validation**
```python
# Example: Validate keys at startup
def validate_api_keys():
    """Validate API keys are present and properly formatted"""
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key or not openai_key.startswith('sk-'):
        raise ValueError("Invalid or missing OPENAI_API_KEY")
    
    anthropic_key = os.getenv('ANTHROPIC_API_KEY') 
    if not anthropic_key or not anthropic_key.startswith('sk-ant-'):
        raise ValueError("Invalid or missing ANTHROPIC_API_KEY")
    
    print("✅ API keys validated")
```

## 🚨 **Emergency Response**

### **If API Key is Exposed:**

1. **Immediate Actions:**
   ```bash
   # 1. Revoke the exposed key immediately
   # Go to OpenAI/Anthropic dashboard → API Keys → Revoke
   
   # 2. Generate new key
   # Create replacement key with same permissions
   
   # 3. Update environment variables
   # Production: Update in hosting platform
   # Local: Update .env file
   
   # 4. Restart all services
   # Ensure new key is loaded
   ```

2. **Follow-up Actions:**
   - Review git history for any commits containing keys
   - Monitor API usage for unauthorized activity
   - Consider rotating other related secrets
   - Update team about security incident

## 🧪 **Testing API Key Setup**

### **Local Development Test:**
```bash
# Test with real API keys
python -c "
import asyncio
import os
import sys
sys.path.append('.')

async def test_real_api():
    # This will test with real API calls
    from ai_poc.providers import ProviderManager
    
    # Check if keys are loaded
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    print('🔑 API Key Status:')
    print(f'OpenAI: {\"✅ SET\" if openai_key else \"❌ MISSING\"}')
    print(f'Anthropic: {\"✅ SET\" if anthropic_key else \"❌ MISSING\"}')
    
    if openai_key and anthropic_key:
        print('\\n🧪 Ready for real API testing!')
    else:
        print('\\n⚠️  Add API keys to .env file first')

asyncio.run(test_real_api())
"
```

### **Production Verification:**
```bash
# Test production environment has keys
curl -X GET "https://your-app.onrender.com/admin/system" \
  -H "Authorization: Bearer your-admin-token"
# Should show environment variables are loaded (but not the actual keys)
```

## 📋 **Updated .env.example**

Here's what your `.env.example` should look like:

```bash
# ===========================================
# AI TUTOR SYSTEM - ENVIRONMENT CONFIGURATION  
# ===========================================

# SECURITY WARNING: This is a template file.
# Copy to .env and add your actual values.
# NEVER commit .env to git!

# -------------------------------------------
# AI Provider API Keys (REQUIRED for production)
# -------------------------------------------
OPENAI_API_KEY=sk-your-openai-api-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
GOOGLE_API_KEY=your-google-gemini-api-key-here

# -------------------------------------------
# AI Configuration
# -------------------------------------------
AI_PROVIDER=openai
AI_COST_LIMIT_DAILY=10.00
AI_RATE_LIMIT_REQUESTS_PER_MINUTE=60

# -------------------------------------------
# Security Configuration (REQUIRED)
# -------------------------------------------
ADMIN_PASSWORD=change-this-secure-password
SECRET_KEY=your-super-secret-flask-key-minimum-32-chars

# -------------------------------------------
# Environment Settings
# -------------------------------------------
ENVIRONMENT=development
DEBUG=true

# -------------------------------------------
# Database (if needed in future)
# -------------------------------------------
# DATABASE_URL=postgresql://user:pass@localhost/dbname

# -------------------------------------------
# External Services
# -------------------------------------------
# SMTP_SERVER=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USERNAME=your-email@gmail.com
# SMTP_PASSWORD=your-app-password
```

## 🎯 **Quick Setup Commands**

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit with your keys
code .env

# 3. Install python-dotenv
pip install python-dotenv

# 4. Test configuration
python -c "import os; print('OpenAI:', '✅' if os.getenv('OPENAI_API_KEY') else '❌')"

# 5. Start with real API keys
python admin-server.py
```

## 🔒 **Summary: API Key Security Checklist**

- ✅ API keys stored in environment variables only
- ✅ .env file added to .gitignore
- ✅ Production keys set in hosting platform dashboard
- ✅ Keys validated at application startup
- ✅ Logs mask API keys (show only last 4 characters)
- ✅ Regular key rotation schedule established
- ✅ Emergency key revocation procedure documented
- ✅ Team trained on security practices

**Your API keys will be completely secure when following this guide!**