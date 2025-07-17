# AI Tutor System

A comprehensive AI-powered tutoring system for an international school in Greece, featuring phone-based student identification, VAPI voice integration, session transcript analysis, and an admin dashboard.

## 🏗️ Project Structure

```
ai-tutor/
├── backend/                    # Core backend components
│   ├── admin-server.py        # Flask admin dashboard with VAPI webhook
│   ├── session-enhanced-server.py  # MCP server with phone identification
│   ├── requirements.txt       # Python dependencies
│   └── ai_poc/               # AI post-processing system
│       ├── config.py         # Provider configuration
│       ├── providers.py      # AI provider implementations
│       ├── validator.py      # Quality validation
│       ├── session_processor.py  # Session analysis orchestration
│       └── prompts/          # AI analysis prompts
├── frontend/                  # Web interface components
│   ├── templates/            # HTML templates for admin dashboard
│   └── static/              # CSS, JavaScript, images
├── data/                     # Student data and configuration
│   ├── phone_mapping.json   # Phone to student ID mapping
│   ├── students/            # Student profiles and sessions
│   └── curriculum/          # Course information
├── config/                   # Environment and deployment config
│   ├── .env.example         # Development environment template
│   └── render-production.env  # Production configuration
├── docs/                     # Comprehensive documentation
│   ├── PRODUCTION_DEPLOYMENT_GUIDE.md
│   ├── VAPI_WEBHOOK_INTEGRATION_GUIDE.md
│   ├── API_KEY_SECURITY_GUIDE.md
│   └── [30+ other guides]
├── scripts/                  # Utility scripts and tools
│   ├── test_phone_system.py
│   ├── session_logger.py
│   └── [other utilities]
└── mcp-server/              # TypeScript MCP server
    ├── src/index.ts
    ├── package.json
    └── tsconfig.json
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+ (for MCP server)
- VAPI account with phone number
- AI provider API keys (OpenAI, Anthropic, etc.)

### Development Setup

1. **Clone and Navigate**
   ```bash
   cd ai-tutor
   ```

2. **Install Python Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Install Node.js Dependencies**
   ```bash
   cd ../mcp-server
   npm install
   ```

4. **Configure Environment**
   ```bash
   cd ../config
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Start MCP Server**
   ```bash
   cd ../mcp-server
   ./start-server.sh
   ```

6. **Start Admin Dashboard**
   ```bash
   cd ../backend
   python admin-server.py
   ```

### Production Deployment

See [`docs/PRODUCTION_DEPLOYMENT_GUIDE.md`](docs/PRODUCTION_DEPLOYMENT_GUIDE.md) for complete deployment instructions.

## 🔧 Core Features

### 📞 Phone-Based Student Identification
- Automatic student identification via phone numbers
- VAPI integration for voice conversations
- Real-time session tracking and logging

### 🤖 AI-Powered Session Analysis
- Provider-agnostic architecture (OpenAI, Anthropic, Google Gemini)
- Comprehensive transcript analysis
- Educational insights and progress tracking
- Quality validation and evidence grounding

### 🎛️ Admin Dashboard
- Student management and profiles
- Session monitoring and analysis
- File management and system status
- Secure authentication and access control

### 🔗 VAPI Webhook Integration
- Real-time transcript reception
- HMAC signature verification
- Background AI processing
- Automatic session data storage

## 📋 Key Components

### Backend Services
- **`admin-server.py`**: Main Flask application with admin dashboard and VAPI webhook endpoint
- **`session-enhanced-server.py`**: MCP server with phone-based student identification
- **`ai_poc/`**: Complete AI post-processing system with provider abstraction

### AI Processing Pipeline
1. **Transcript Reception**: VAPI webhook receives session transcripts
2. **Student Identification**: Phone number mapping to student profiles
3. **AI Analysis**: Provider-agnostic analysis using configured AI models
4. **Quality Validation**: Educational content verification and grounding
5. **Data Storage**: Session summaries and insights saved to student profiles

### Security Features
- Environment variable-based configuration
- HMAC webhook signature verification
- Secure API key management
- Production deployment security guidelines

## 🌐 Live Deployment

**Production URL**: `https://ai-tutor-ptnl.onrender.com`

### VAPI Configuration
- **Webhook URL**: `https://ai-tutor-ptnl.onrender.com/vapi/webhook`
- **Authentication**: HMAC signature verification
- **Phone Integration**: Automatic student identification

## 📚 Documentation

Comprehensive guides available in [`docs/`](docs/):

- **[Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT_GUIDE.md)**: Complete deployment instructions
- **[VAPI Webhook Integration](docs/VAPI_WEBHOOK_INTEGRATION_GUIDE.md)**: Webhook setup and configuration
- **[API Key Security Guide](docs/API_KEY_SECURITY_GUIDE.md)**: Security best practices
- **[AI Provider Architecture](docs/AI_PROVIDER_AGNOSTIC_ARCHITECTURE.md)**: Provider-agnostic design
- **[Admin Dashboard Setup](docs/ADMIN_DASHBOARD_SETUP.md)**: Dashboard configuration

## 🔧 Configuration

### Environment Variables
See [`config/.env.example`](config/.env.example) for all available configuration options:

```bash
# Core Configuration
ADMIN_PASSWORD=your_secure_password
SECRET_KEY=your_flask_secret_key

# AI Providers
AI_PROVIDER=openai  # openai, anthropic, google
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# VAPI Integration
VAPI_WEBHOOK_SECRET=your_vapi_secret
```

### Student Data
- **Phone Mapping**: [`data/phone_mapping.json`](data/phone_mapping.json)
- **Student Profiles**: [`data/students/`](data/students/)
- **Curriculum**: [`data/curriculum/`](data/curriculum/)

## 🧪 Testing

### Phone System Testing
```bash
cd scripts
python test_phone_system.py
```

### Session Tracking Testing
```bash
cd scripts
python test_session_tracking.py
```

### AI Analysis Testing
```bash
cd backend
python -m ai_poc.session_processor
```

## 🛠️ Development Tools

### Utility Scripts
- **`scripts/ai_tutor_integration.py`**: Integration testing
- **`scripts/prompt_viewer.py`**: Prompt management utility
- **`scripts/session_logger.py`**: Session logging and debugging

### MCP Server Development
```bash
cd mcp-server
npm run build
npm run start
```

## 📈 Next Steps

1. **Phase 2 Features**:
   - CRUD operations for student management
   - Advanced session analytics
   - Enhanced file management

2. **Production Enhancements**:
   - Real AI provider API keys
   - Advanced monitoring and logging
   - Performance optimization

3. **Integration Improvements**:
   - Extended VAPI features
   - Multi-language support
   - Advanced curriculum integration

## 📞 Support

For technical support and deployment assistance, refer to the comprehensive documentation in the [`docs/`](docs/) directory.

## 🔒 Security

This system implements enterprise-grade security practices:
- Secure API key management
- HMAC webhook verification
- Environment-based configuration
- Production deployment security

See [`docs/API_KEY_SECURITY_GUIDE.md`](docs/API_KEY_SECURITY_GUIDE.md) for detailed security information.