# AI Provider Environment Configuration

## 🔧 **Complete Environment Setup**

This document provides the complete environment configuration template for the multi-provider AI post-processing system. Copy the relevant sections to your `.env` file to enable provider switching.

## 📄 **Environment File Template (`.env`)**

```bash
# =============================================================================
# AI POST-PROCESSING SYSTEM CONFIGURATION
# =============================================================================

# =============================================================================
# PROVIDER SELECTION (Change anytime without code changes)
# =============================================================================
AI_PROVIDER=openai                    # Current: OpenAI O3
# AI_PROVIDER=anthropic               # Alternative: Claude
# AI_PROVIDER=google                  # Alternative: Gemini  
# AI_PROVIDER=azure                   # Alternative: Azure OpenAI
# AI_PROVIDER=local                   # Alternative: Local models

# Automatic fallback chain (comma-separated, no spaces)
FALLBACK_PROVIDERS=anthropic,google,local

# =============================================================================
# OPENAI CONFIGURATION (O3, GPT-4, etc.)
# =============================================================================
OPENAI_API_KEY=sk-proj-your-openai-key-here
OPENAI_ORG_ID=org-your-organization-id-here
OPENAI_MODEL=o3-mini                  # Options: o3 | o3-mini | gpt-4o | gpt-4-turbo
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.3
OPENAI_TIMEOUT=60                     # Request timeout in seconds

# =============================================================================
# ANTHROPIC CONFIGURATION (Claude models)
# =============================================================================
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022  # Options: claude-3-5-sonnet | claude-3-haiku
ANTHROPIC_MAX_TOKENS=4000
ANTHROPIC_TEMPERATURE=0.3
ANTHROPIC_TIMEOUT=60

# =============================================================================
# GOOGLE AI CONFIGURATION (Gemini models)
# =============================================================================
GOOGLE_API_KEY=your-google-ai-key-here
GOOGLE_MODEL=gemini-1.5-pro          # Options: gemini-1.5-pro | gemini-1.5-flash
GOOGLE_PROJECT_ID=your-google-project-id
GOOGLE_MAX_TOKENS=4000
GOOGLE_TEMPERATURE=0.3
GOOGLE_TIMEOUT=60

# =============================================================================
# AZURE OPENAI CONFIGURATION (Enterprise deployment)
# =============================================================================
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-openai-key
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_MODEL=gpt-4o            # Your deployed model name
AZURE_MAX_TOKENS=4000
AZURE_TEMPERATURE=0.3
AZURE_TIMEOUT=60

# =============================================================================
# LOCAL MODEL CONFIGURATION (Ollama, LM Studio, etc.)
# =============================================================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b             # Options: llama3.1 | qwen2.5 | deepseek-coder
OLLAMA_TIMEOUT=120                    # Local models may need more time

# Custom endpoint configuration
CUSTOM_ENDPOINT_URL=http://your-custom-api.com/v1
CUSTOM_MODEL=your-custom-model
CUSTOM_API_KEY=your-custom-key
CUSTOM_TIMEOUT=60

# =============================================================================
# COST AND PERFORMANCE CONTROLS
# =============================================================================
DAILY_ANALYSIS_LIMIT=100             # Maximum sessions per day
COST_LIMIT_USD=50.00                 # Daily cost limit (USD)
MONTHLY_COST_LIMIT_USD=1000.00       # Monthly cost limit (USD)

# Performance preferences
PREFERRED_SPEED=balanced             # Options: fast | balanced | cost-optimized
MAX_CONCURRENT_ANALYSES=3            # Concurrent session processing limit
RETRY_ATTEMPTS=2                     # Number of retry attempts per provider

# =============================================================================
# QUALITY ASSURANCE CONFIGURATION
# =============================================================================
ENABLE_QA_VALIDATION=true            # Enable analysis validation
QA_CONFIDENCE_THRESHOLD=0.8          # Minimum confidence score (0.0-1.0)
ENABLE_HUMAN_REVIEW_FLAG=true        # Flag low-confidence analyses for review

# =============================================================================
# MONITORING AND ALERTING
# =============================================================================
ENABLE_COST_ALERTS=true              # Enable cost monitoring alerts
COST_ALERT_THRESHOLD=0.8             # Alert when reaching 80% of limit
ENABLE_PERFORMANCE_MONITORING=true   # Track provider performance
PERFORMANCE_ALERT_THRESHOLD=10.0     # Alert if response time > 10 seconds

# Email alerts (optional)
ALERT_EMAIL=admin@your-school.edu
SMTP_SERVER=smtp.your-email-provider.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password

# =============================================================================
# ADMIN DASHBOARD CONFIGURATION
# =============================================================================
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$your-bcrypt-hashed-password-here
SESSION_SECRET_KEY=your-very-secure-secret-key-here

# Production security
FORCE_HTTPS=true
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Strict

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOG_LEVEL=INFO                       # Options: DEBUG | INFO | WARNING | ERROR
LOG_FILE=logs/ai_processing.log
MAX_LOG_SIZE_MB=100
LOG_BACKUP_COUNT=5

# Provider-specific logging
LOG_OPENAI_REQUESTS=false            # Log OpenAI API requests (careful: sensitive data)
LOG_ANTHROPIC_REQUESTS=false         # Log Anthropic API requests
LOG_GOOGLE_REQUESTS=false            # Log Google AI requests

# =============================================================================
# DATA STORAGE CONFIGURATION
# =============================================================================
DATA_DIR=data                        # Base directory for student data
BACKUP_DIR=backups                   # Directory for data backups
ANALYSIS_CACHE_DIR=cache/analyses    # Cache directory for processed analyses

# Backup settings
ENABLE_AUTO_BACKUP=true
BACKUP_FREQUENCY_HOURS=24
MAX_BACKUP_RETENTION_DAYS=30

# =============================================================================
# RATE LIMITING CONFIGURATION
# =============================================================================
# OpenAI rate limits (adjust based on your tier)
OPENAI_REQUESTS_PER_MINUTE=500
OPENAI_TOKENS_PER_MINUTE=150000

# Anthropic rate limits
ANTHROPIC_REQUESTS_PER_MINUTE=100
ANTHROPIC_TOKENS_PER_MINUTE=40000

# Google AI rate limits
GOOGLE_REQUESTS_PER_MINUTE=60
GOOGLE_TOKENS_PER_MINUTE=30000

# =============================================================================
# DEVELOPMENT AND TESTING
# =============================================================================
DEVELOPMENT_MODE=false               # Enable development features
ENABLE_TEST_MODE=false               # Use test data instead of real sessions
MOCK_AI_RESPONSES=false              # Use mock responses for testing

# Test provider configuration (for development)
TEST_PROVIDER=mock
MOCK_RESPONSE_DELAY=2                # Simulate API delay in seconds
```

## 🔄 **Quick Provider Switching Examples**

### **Switch to OpenAI O3**
```bash
AI_PROVIDER=openai
OPENAI_MODEL=o3
FALLBACK_PROVIDERS=anthropic,google
```

### **Switch to Anthropic Claude**
```bash
AI_PROVIDER=anthropic
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
FALLBACK_PROVIDERS=openai,google
```

### **Switch to Google Gemini**
```bash
AI_PROVIDER=google
GOOGLE_MODEL=gemini-1.5-pro
FALLBACK_PROVIDERS=openai,anthropic
```

### **Cost-Optimized Configuration**
```bash
AI_PROVIDER=openai
OPENAI_MODEL=o3-mini                 # Most cost-effective OpenAI model
PREFERRED_SPEED=cost-optimized
FALLBACK_PROVIDERS=anthropic
DAILY_ANALYSIS_LIMIT=50
COST_LIMIT_USD=20.00
```

### **Performance-Optimized Configuration**
```bash
AI_PROVIDER=openai
OPENAI_MODEL=gpt-4o                  # Fastest OpenAI model
PREFERRED_SPEED=fast
MAX_CONCURRENT_ANALYSES=5
FALLBACK_PROVIDERS=google,anthropic
```

## 🔒 **Security Best Practices**

### **API Key Security**
```bash
# ✅ CORRECT: Use environment variables
OPENAI_API_KEY=sk-proj-actual-key-here

# ❌ WRONG: Never hardcode in source code
# api_key = "sk-proj-actual-key-here"  # DON'T DO THIS
```

### **Production Security Checklist**
- [ ] All API keys stored in environment variables
- [ ] Admin password properly hashed with bcrypt
- [ ] Session secret key is cryptographically secure (64+ characters)
- [ ] HTTPS forced in production (`FORCE_HTTPS=true`)
- [ ] Secure cookie settings enabled
- [ ] Sensitive request logging disabled in production
- [ ] Cost limits configured to prevent unexpected charges
- [ ] Regular backup of configuration and data

### **API Key Validation**
```bash
# Validate OpenAI key format
echo $OPENAI_API_KEY | grep -E "^sk-proj-[a-zA-Z0-9]{48,}$"

# Validate Anthropic key format  
echo $ANTHROPIC_API_KEY | grep -E "^sk-ant-[a-zA-Z0-9-]{95,}$"

# Validate Google AI key format
echo $GOOGLE_API_KEY | grep -E "^[a-zA-Z0-9_-]{39}$"
```

## 🎛️ **Admin Dashboard Environment Variables**

### **Provider Management**
```bash
# Enable provider switching in admin dashboard
ENABLE_PROVIDER_SWITCHING=true
ENABLE_COST_MONITORING=true
ENABLE_PERFORMANCE_DASHBOARD=true

# Provider health check intervals
PROVIDER_HEALTH_CHECK_INTERVAL=300   # Check every 5 minutes
PROVIDER_TIMEOUT_THRESHOLD=30        # Mark as unhealthy after 30s timeout
```

### **Session Processing Control**
```bash
# Bulk processing settings
MAX_BULK_PROCESSING_SESSIONS=50      # Maximum sessions per bulk operation
BULK_PROCESSING_TIMEOUT=1800         # 30 minutes timeout for bulk operations
ENABLE_BACKGROUND_PROCESSING=true    # Allow background processing

# Processing queues
PROCESSING_QUEUE_SIZE=100            # Maximum queued sessions
PROCESSING_PRIORITY_LEVELS=3         # High, medium, low priority
```

## 📊 **Monitoring Configuration**

### **Cost Monitoring**
```bash
# Cost tracking
TRACK_PER_STUDENT_COSTS=true         # Track costs per student
TRACK_PER_SESSION_COSTS=true         # Track costs per session
COST_REPORTING_INTERVAL=daily        # daily | weekly | monthly

# Alerts
COST_ALERT_EMAIL=admin@school.edu
COST_ALERT_SLACK_WEBHOOK=https://hooks.slack.com/your-webhook
```

### **Performance Monitoring**
```bash
# Performance tracking
TRACK_RESPONSE_TIMES=true            # Monitor API response times
TRACK_SUCCESS_RATES=true             # Monitor provider success rates
PERFORMANCE_RETENTION_DAYS=90        # Keep performance data for 90 days

# Alerts
PERFORMANCE_ALERT_EMAIL=tech@school.edu
RESPONSE_TIME_THRESHOLD=15.0         # Alert if response > 15 seconds
SUCCESS_RATE_THRESHOLD=95.0          # Alert if success rate < 95%
```

## 🚀 **Deployment Configurations**

### **Development Environment**
```bash
DEVELOPMENT_MODE=true
LOG_LEVEL=DEBUG
ENABLE_TEST_MODE=true
MOCK_AI_RESPONSES=true
COST_LIMIT_USD=5.00                  # Low limit for development
```

### **Staging Environment**
```bash
DEVELOPMENT_MODE=false
LOG_LEVEL=INFO
ENABLE_TEST_MODE=false
MOCK_AI_RESPONSES=false
COST_LIMIT_USD=25.00                 # Medium limit for staging
```

### **Production Environment**
```bash
DEVELOPMENT_MODE=false
LOG_LEVEL=WARNING
ENABLE_TEST_MODE=false
MOCK_AI_RESPONSES=false
FORCE_HTTPS=true
SESSION_COOKIE_SECURE=true
COST_LIMIT_USD=100.00                # Production limit
```

---

**🎯 Quick Start:**
1. Copy the environment template to your `.env` file
2. Set your primary `AI_PROVIDER` (start with `openai`)
3. Add your API keys for the providers you want to use
4. Configure cost limits and performance preferences
5. Test with a single session before bulk processing

**The system will automatically handle provider switching, failover, and cost optimization based on your configuration!**