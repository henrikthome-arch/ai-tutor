# 🏗️ Production Session Management Architecture

## 🎯 Design Principles

**Core Requirements:**
1. **Works in production** - No dependency on local integration scripts
2. **Platform agnostic** - Works with VAPI, Superinterface, or any voice platform
3. **Minimal assumptions** - Only logs what MCP server can actually see
4. **Optional analysis** - Configurable post-processing without hardcoded prompts
5. **Extensible** - Can be enhanced with more data sources later

---

## 🏗️ Architecture Overview

```
Production Flow:
Student → Voice Platform → OpenAI Assistant → MCP Server → Response
                                              ↓
                                         Session Logger
                                              ↓
                                    Session Data Storage
                                              ↓
                                    Optional Analysis Service
```

**Key Insight:** The MCP server is the **only component we control** that's in the production conversation loop.

---

## 📊 What We Can Actually Track

### ✅ Available Data (MCP Server Sees):
- **Function call timestamps** - When AI requests student data
- **Student ID per call** - Which student is being tutored
- **Function parameters** - What specific data was requested
- **Response data** - What student context was provided
- **Session patterns** - Time gaps indicate session boundaries

### ❌ Missing Data (MCP Server Doesn't See):
- **Full conversation** - Student and AI messages
- **Voice interaction quality** - Tone, engagement, etc.
- **Session start/end events** - No explicit session management
- **Platform-specific metadata** - Call duration, interruptions, etc.

---

## 🔧 Proposed Implementation

### Phase 1: Platform-Agnostic Session Tracking

**1. MCP Server Core Session Tracker**
```python
class SessionTracker:
    def log_interaction(self, student_id, timestamp, function_name, response_size):
        # Create session entries based on time gaps
        # Store in simple JSON format
        
    def detect_session_boundary(self, student_id, current_time):
        # If gap > 10 minutes, assume new session
        return gap > SESSION_TIMEOUT
    
    def create_session_id(self, student_id, timestamp):
        # Generate consistent session IDs for webhook matching
        return f"{student_id}_{timestamp.strftime('%Y%m%d_%H%M')}"
```

**2. Core Session Data Structure**
```json
{
  "session_id": "emma_smith_20250117_1430",
  "student_id": "emma_smith",
  "start_time": "2025-01-17T14:30:00Z",
  "end_time": null,
  "platform": "vapi",
  "status": "active",
  "mcp_interactions": [
    {
      "timestamp": "2025-01-17T14:30:05Z",
      "function": "get_student_context",
      "data_provided": ["profile", "progress", "curriculum"]
    }
  ],
  "conversation": {
    "transcript": null,
    "source": "pending",
    "word_count": 0
  },
  "session_summary": {
    "duration_estimated": "15 minutes",
    "data_requests": 3,
    "subjects_accessed": ["mathematics", "reading"]
  }
}
```

### Phase 2: VAPI Integration

**3. VAPI Webhook Endpoint**
```python
@app.route('/webhook/vapi/session-complete', methods=['POST'])
def vapi_session_complete():
    data = request.json
    session_id = generate_session_id(data.get('call_id'), data.get('started_at'))
    
    # Match with existing MCP session or create new one
    session = session_tracker.get_or_create_session(session_id)
    
    # Add VAPI transcript data
    session.update({
        "end_time": data.get('ended_at'),
        "status": "completed",
        "conversation": {
            "transcript": data.get('transcript'),
            "source": "vapi",
            "word_count": len(data.get('transcript', '').split()),
            "call_duration": data.get('duration_seconds')
        },
        "vapi_metadata": {
            "call_id": data.get('call_id'),
            "cost": data.get('cost'),
            "ended_reason": data.get('ended_reason')
        }
    })
    
    # Trigger analysis if configured
    if analysis_enabled:
        trigger_session_analysis(session_id)
```

**4. VAPI Session Matching Logic**
```python
def generate_session_id(vapi_call_id, started_at):
    # Convert VAPI data to match MCP session ID format
    # Use student identification from conversation start
    return extract_student_from_call(vapi_call_id, started_at)

def match_vapi_to_mcp_session(vapi_data):
    # Strategy 1: Time-based matching (±5 minutes)
    # Strategy 2: Student ID extraction from conversation
    # Strategy 3: Explicit session handoff parameter
```

### Phase 3: Platform-Agnostic Webhook Framework

**5. Generic Session Webhook**
```python
@app.route('/webhook/session-data', methods=['POST'])
def generic_session_webhook():
    """Platform-agnostic endpoint for any voice platform"""
    data = request.json
    platform = data.get('platform', 'unknown')
    
    if platform == 'vapi':
        return handle_vapi_webhook(data)
    elif platform == 'superinterface':
        return handle_superinterface_webhook(data)
    else:
        return handle_generic_webhook(data)
```

**6. Analysis Framework**
```python
class SessionAnalyzer:
    def __init__(self, config_path=None):
        self.config = load_config(config_path) if config_path else None
        
    def analyze_session(self, session_data):
        if not self.config or not self.config.get('analysis_enabled'):
            return None
            
        # Combine MCP metadata + full transcript for analysis
        combined_data = {
            'mcp_patterns': session_data['mcp_interactions'],
            'conversation': session_data['conversation']['transcript'],
            'student_context': self.get_student_context(session_data['student_id'])
        }
        
        return self.run_configurable_analysis(combined_data)
```

**7. Configuration Structure**
```yaml
# session_config.yaml
session_tracking:
  timeout_minutes: 10
  auto_save: true
  
webhooks:
  vapi:
    enabled: true
    endpoint: "/webhook/vapi/session-complete"
    auth_token: ${VAPI_WEBHOOK_TOKEN}
    
analysis:
  enabled: true
  openai_api_key: ${ANALYSIS_API_KEY}
  triggers:
    - on_session_complete
    - on_request
  prompts:
    session_summary: "Analyze this tutoring session..."
    progress_update: "Update student progress based on..."
    learning_insights: "Identify learning patterns from..."
```

---

## 🎯 Minimum Viable Product (MVP)

**What we implement first:**

1. **MCP Server Session Logging**
   - Log each function call with timestamp
   - Detect session boundaries using time gaps
   - Store basic session metadata

2. **Simple Session Files**
   - One JSON file per detected session
   - Contains: student_id, timestamps, function_calls, basic stats
   - No LLM analysis initially

3. **Optional Webhook Endpoint**
   - `/webhook/session-data` endpoint in MCP server
   - External systems can POST additional session data
   - Merges with function call logs

**Benefits of MVP:**
- ✅ **Works immediately** with current system
- ✅ **No additional API costs** or dependencies
- ✅ **Captures core session patterns** from function calls
- ✅ **Extensible** - can add full transcript analysis later

---

## 🔄 Implementation Phases

### Phase 1: MCP Server Logging (1-2 hours)
- Add session tracking to existing MCP server
- Create basic session detection logic
- Store session files with function call data

### Phase 2: Analysis Framework (2-3 hours)  
- Create configurable analysis system
- Separate analysis service (optional)
- Template-based prompts for different use cases

### Phase 3: Platform Integration (Future)
- Webhook endpoints for voice platforms
- Full transcript integration
- Real-time session monitoring

---

## 📋 Design Decisions

### Session Detection Strategy
**Option A: Time-based** (Recommended for MVP)
- Gap > 10 minutes = new session
- Simple, works immediately
- May miss short breaks

**Option B: Platform webhooks** 
- Voice platform sends session start/end events
- More accurate but requires platform integration
- Future enhancement

### Data Storage
**Current: JSON Files** (Keep for simplicity)
- Easy to debug and extend
- No additional dependencies
- Can migrate to database later

### Analysis Trigger
**Phase 1: Manual/On-demand**
- Analysis runs when requested
- No automatic processing costs
- Predictable resource usage

**Phase 2: Configurable Auto-analysis**
- Configurable triggers
- Optional automatic processing
- Cost and resource management

---

## 🎯 Success Criteria

**MVP Success:**
- ✅ MCP server logs all function calls in production
- ✅ Session boundaries detected automatically  
- ✅ Session data stored in readable format
- ✅ No impact on existing system performance
- ✅ Foundation for future enhancements

**Future Success:**
- Voice platform integration
- Full conversation analysis
- Real-time progress tracking
- Multi-platform support

This architecture provides a solid foundation that works with the current system while being extensible for future enhancements.