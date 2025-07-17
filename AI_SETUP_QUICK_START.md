# AI Post-Processing Quick Start Guide

This guide shows you exactly how to add OpenAI/Anthropic API keys for testing and production.

## 🚀 For Testing (Local Development)

### Step 1: Get Your API Key

**Option A: OpenAI** (Recommended for starting)
1. Go to https://platform.openai.com/api-keys
2. Create account/sign in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-` or `sk-`)

**Option B: Anthropic**
1. Go to https://console.anthropic.com/
2. Create account/sign in
3. Go to "API Keys" section
4. Create new key
5. Copy the key

### Step 2: Create Local Environment File

```bash
# Copy the example file
cp .env.example .env
```

### Step 3: Add Your API Key

Edit `.env` file and replace the placeholder:

```bash
# For OpenAI (recommended configuration)
OPENAI_API_KEY=sk-proj-your-actual-key-here
OPENAI_MODEL=o3-mini
AI_PROVIDER=openai

# For Anthropic
ANTHROPIC_API_KEY=your-actual-anthropic-key-here
AI_PROVIDER=anthropic

# Optional: Model alternatives
# OPENAI_MODEL=gpt-4                    # Most capable, higher cost
# OPENAI_MODEL=gpt-4-turbo             # Fast and capable
# OPENAI_MODEL=o3-mini                 # Latest reasoning model (default)

# Other settings (optional)
DAILY_COST_LIMIT_USD=15.0              # Higher limit for powerful models
```

### Step 4: Test the Integration

```bash
# Test with real API key
python -c "
import asyncio
import sys
sys.path.append('.')

async def test_real_api():
    from ai_poc.session_processor import session_processor
    
    # Load example data
    with open('data/students/emma_smith/sessions/2025-01-14_transcript.txt', 'r', encoding='utf-8') as f:
        transcript = f.read()
    
    student_context = {
        'name': 'Emma Smith',
        'age': '9',
        'grade': '4',
        'subject_focus': 'Mathematics',
        'learning_style': 'Visual learner',
        'primary_interests': 'Dinosaurs, space',
        'motivational_triggers': 'Achievement badges',
    }
    
    print('🧪 Testing real AI analysis...')
    analysis, validation = await session_processor.process_session_transcript(
        transcript=transcript,
        student_context=student_context,
        save_results=False
    )
    
    print(f'✅ Success! Provider: {analysis.provider_used}')
    print(f'Cost: ${analysis.cost_estimate:.4f}')
    return True

asyncio.run(test_real_api())
"
```

## 🏭 For Production Deployment

### Method 1: Environment Variables (Recommended)

**For Render.com:**

Render.com has an environment variable importer, but it doesn't handle comments well. Use the clean production file:

1. Go to your Render.com service dashboard
2. Click "Environment" tab
3. Click "Add from .env file"
4. Upload the [`render-production.env`](render-production.env) file (not .env.example!)
5. Replace the placeholder values with your real keys:
   - `OPENAI_API_KEY` → your actual OpenAI key
   - `ADMIN_PASSWORD` → strong password
   - `FLASK_SECRET_KEY` → generate with: `python -c "import secrets; print(secrets.token_hex(32))"`

**For Heroku, etc.:**

1. Go to your hosting platform dashboard
2. Find "Environment Variables" or "Config Vars" section
3. Add these variables manually:

```
OPENAI_API_KEY=sk-proj-your-actual-key-here
AI_PROVIDER=openai
OPENAI_MODEL=o3
DAILY_COST_LIMIT_USD=25.0
FLASK_ENV=production
ADMIN_USERNAME=your_secure_username
ADMIN_PASSWORD=your_secure_password_here
FLASK_SECRET_KEY=your_64_char_random_secret_key
```

**For VPS/Dedicated Server:**

Add to your deployment script or systemd service:
```bash
export OPENAI_API_KEY="sk-proj-your-key-here"
export AI_PROVIDER="openai"
export FLASK_ENV="production"
```

### Method 2: Secure File (Alternative)

Create `/etc/ai-tutor/.env` (Linux) or similar secure location:
```bash
# Secure permissions
sudo mkdir -p /etc/ai-tutor
sudo chmod 700 /etc/ai-tutor
echo "OPENAI_API_KEY=sk-proj-your-key" | sudo tee /etc/ai-tutor/.env
sudo chmod 600 /etc/ai-tutor/.env
```

Modify your startup script to load from this file.

## 🔒 Security Verification

### Check 1: Keys Not in Code
```bash
# This should return nothing
grep -r "sk-" . --exclude-dir=.git --exclude="*.env*"
```

### Check 2: .env Files Ignored
```bash
# Check .gitignore contains .env
cat .gitignore | grep "\.env"
```

### Check 3: Environment Loading Works
```bash
# Test environment loading
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('✅ OpenAI key loaded' if os.getenv('OPENAI_API_KEY') else '❌ No OpenAI key')
print('✅ Anthropic key loaded' if os.getenv('ANTHROPIC_API_KEY') else '❌ No Anthropic key')
"
```

## 💰 Cost Management

### Monitor Usage

**OpenAI:**
- Dashboard: https://platform.openai.com/usage
- Set billing limits in account settings

**Anthropic:**
- Dashboard: https://console.anthropic.com/
- Monitor usage in console

### Set Alerts

The system includes built-in cost limiting:
```bash
# In .env
DAILY_COST_LIMIT_USD=10.0  # Stops processing after $10/day
```

## 🚨 Emergency: Key Compromised

If your API key is accidentally exposed:

1. **Immediately revoke** the key in provider dashboard
2. **Generate new key**
3. **Update environment variables**
4. **Restart application**
5. **Check billing** for unexpected usage

## 📊 Success Checklist

- [ ] API key obtained from provider
- [ ] `.env` file created with real key
- [ ] Test script runs successfully
- [ ] No API keys in git repository
- [ ] Production environment variables set
- [ ] Cost monitoring enabled
- [ ] Backup plan for key rotation ready

## 🔧 Common Issues

**"Invalid API key" error:**
- Double-check key is copied correctly
- Ensure no extra spaces/characters
- Check key hasn't expired

**"Module not found" error:**
- Install dependencies: `pip install openai anthropic python-dotenv`

**Cost concerns:**
- Start with `gpt-4o-mini` (cheapest OpenAI model)
- Use `claude-3-haiku` (cheapest Anthropic model)
- Set low daily limits initially

---

## Next Steps

Once your API keys are working:
1. Test with real student sessions
2. Configure provider preferences
3. Set up monitoring and alerts
4. Plan production deployment

For detailed security information, see: [`API_KEY_SECURITY_GUIDE.md`](API_KEY_SECURITY_GUIDE.md)