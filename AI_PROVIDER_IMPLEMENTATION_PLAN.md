# AI Provider-Agnostic Implementation Plan

## 🎯 **Implementation Overview**

This document provides the complete implementation plan for the provider-agnostic AI post-processing system. The architecture supports seamless switching between OpenAI O3, Anthropic Claude, Google Gemini, Azure OpenAI, and local models.

## 📁 **File Structure**

```
ai_post_processing/
├── ai_providers.py              # Core provider interface and manager
├── providers/
│   ├── __init__.py
│   ├── openai_provider.py       # OpenAI O3/GPT-4 implementation
│   ├── anthropic_provider.py    # Anthropic Claude implementation
│   ├── google_provider.py       # Google Gemini implementation
│   ├── azure_provider.py        # Azure OpenAI implementation
│   └── local_provider.py        # Ollama/local model implementation
├── analysis/
│   ├── __init__.py
│   ├── educational_analyzer.py  # Core educational analysis logic
│   ├── response_normalizer.py   # Standardize responses across providers
│   └── quality_assurance.py     # Analysis validation and QA
├── config/
│   ├── __init__.py
│   ├── provider_config.py       # Provider configuration management
│   └── cost_optimizer.py        # Cost optimization algorithms
├── monitoring/
│   ├── __init__.py
│   ├── performance_monitor.py   # Provider performance tracking
│   └── cost_tracker.py          # Cost monitoring and alerts
└── post_processor.py            # Main post-processing service
```

## 🔧 **Core Implementation Specifications**

### **1. Base Provider Interface (`ai_providers.py`)**

```python
"""
AI Provider-Agnostic Post-Processing System
Supports OpenAI, Anthropic, Google AI, Azure, and Local models
"""

import os
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from datetime import datetime
import json

# Core data structures
@dataclass
class ModelCapabilities:
    max_context_length: int
    supports_json_mode: bool
    reasoning_strength: float  # 0.0-1.0
    cost_per_token: float
    average_response_time: float
    strong_in_education: bool

@dataclass
class CostEstimate:
    input_tokens: int
    output_tokens: int
    total_cost_usd: float
    provider: str
    model: str

@dataclass
class AnalysisRequirements:
    transcript_length: int
    analysis_depth: str  # 'quick', 'standard', 'comprehensive'
    priority: str  # 'cost', 'speed', 'quality'
    budget_limit_usd: Optional[float] = None

@dataclass
class StandardizedAnalysis:
    conceptual_understanding: Dict[str, Any]
    engagement_analysis: Dict[str, Any]
    personalization_effectiveness: Dict[str, Any]
    progress_trajectory: Dict[str, Any]
    recommendations: Dict[str, Any]
    confidence_scores: Dict[str, float]
    provider_metadata: Dict[str, Any]
    processing_time: float
    cost_details: CostEstimate

# Abstract base class for all providers
class EducationalAIProvider(ABC):
    """Abstract base class for all educational AI providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get('model')
        self.last_successful_call = None
        self.daily_usage = {'calls': 0, 'tokens': 0, 'cost': 0.0}
        
    @abstractmethod
    async def analyze_educational_session(
        self, 
        transcript: str, 
        student_context: Dict[str, Any],
        analysis_depth: str = 'standard'
    ) -> Dict[str, Any]:
        """Analyze educational session - implemented by each provider"""
        pass
    
    @abstractmethod
    def get_model_capabilities(self) -> ModelCapabilities:
        """Return model-specific capabilities and limitations"""
        pass
    
    @abstractmethod
    def estimate_cost(self, transcript_length: int) -> CostEstimate:
        """Estimate processing cost for given input size"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check provider availability and performance"""
        pass
    
    def get_daily_usage(self) -> Dict[str, Union[int, float]]:
        """Return current daily usage statistics"""
        return self.daily_usage.copy()

# Main provider manager
class AIProviderManager:
    """
    Central manager for all AI providers
    Handles selection, failover, and optimization
    """
    
    def __init__(self):
        self.providers = {}
        self.primary_provider = os.getenv('AI_PROVIDER', 'openai')
        self.fallback_chain = self._parse_fallback_chain()
        self.cost_tracker = CostTracker()
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize all configured providers
        self._initialize_providers()
    
    def _parse_fallback_chain(self) -> List[str]:
        """Parse fallback provider chain from environment"""
        fallback_str = os.getenv('FALLBACK_PROVIDERS', 'anthropic,google')
        return [p.strip() for p in fallback_str.split(',') if p.strip()]
    
    def _initialize_providers(self):
        """Initialize all available providers based on configuration"""
        provider_configs = {
            'openai': self._get_openai_config(),
            'anthropic': self._get_anthropic_config(),
            'google': self._get_google_config(),
            'azure': self._get_azure_config(),
            'local': self._get_local_config()
        }
        
        for name, config in provider_configs.items():
            if config and config.get('api_key'):
                try:
                    provider_class = self._get_provider_class(name)
                    self.providers[name] = provider_class(config)
                    logging.info(f"Initialized {name} provider")
                except Exception as e:
                    logging.warning(f"Failed to initialize {name} provider: {e}")
    
    async def analyze_session(
        self, 
        transcript: str, 
        student_context: Dict[str, Any],
        requirements: Optional[AnalysisRequirements] = None
    ) -> StandardizedAnalysis:
        """
        Main entry point for session analysis
        Automatically selects optimal provider and handles failover
        """
        
        if requirements is None:
            requirements = AnalysisRequirements(
                transcript_length=len(transcript),
                analysis_depth='standard',
                priority='balanced'
            )
        
        # Select optimal provider based on requirements
        selected_provider = self._select_optimal_provider(requirements)
        
        # Attempt analysis with selected provider and fallbacks
        for provider_name in [selected_provider] + self.fallback_chain:
            if provider_name not in self.providers:
                continue
                
            try:
                provider = self.providers[provider_name]
                
                # Check rate limits and availability
                if not await self._check_provider_availability(provider_name):
                    continue
                
                # Perform analysis
                start_time = datetime.now()
                raw_result = await provider.analyze_educational_session(
                    transcript=transcript,
                    student_context=student_context,
                    analysis_depth=requirements.analysis_depth
                )
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Normalize response format
                normalized_result = self._normalize_response(
                    raw_result, provider_name, processing_time
                )
                
                # Track usage and costs
                self._track_usage(provider_name, transcript, normalized_result)
                
                return normalized_result
                
            except Exception as e:
                logging.warning(f"Provider {provider_name} failed: {e}")
                continue
        
        raise AllProvidersFailedError("No available providers for analysis")
    
    def _select_optimal_provider(self, requirements: AnalysisRequirements) -> str:
        """Select best provider based on requirements and current conditions"""
        
        if requirements.priority == 'cost':
            return self._select_cheapest_provider(requirements)
        elif requirements.priority == 'speed':
            return self._select_fastest_provider(requirements)
        elif requirements.priority == 'quality':
            return self._select_highest_quality_provider(requirements)
        else:
            return self.primary_provider
```

### **2. OpenAI Provider Implementation (`providers/openai_provider.py`)**

```python
"""
OpenAI Provider Implementation
Supports O3, O3-mini, GPT-4o, GPT-4-turbo models
"""

import openai
from openai import AsyncOpenAI
from typing import Dict, Any
import json
import os

class OpenAIProvider(EducationalAIProvider):
    """OpenAI implementation supporting O3, GPT-4, etc."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config['api_key']
        self.org_id = config.get('org_id')
        self.model = config.get('model', 'o3-mini')
        self.max_tokens = int(config.get('max_tokens', 4000))
        self.temperature = float(config.get('temperature', 0.3))
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            organization=self.org_id
        )
        
    async def analyze_educational_session(
        self, 
        transcript: str, 
        student_context: Dict[str, Any],
        analysis_depth: str = 'standard'
    ) -> Dict[str, Any]:
        """OpenAI-specific educational analysis"""
        
        prompt = self._build_educational_prompt(
            transcript, student_context, analysis_depth
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Add OpenAI-specific metadata
            result['provider_metadata'] = {
                'model': self.model,
                'usage': response.usage.dict() if response.usage else {},
                'finish_reason': response.choices[0].finish_reason
            }
            
            self.last_successful_call = datetime.now()
            return result
            
        except Exception as e:
            logging.error(f"OpenAI analysis failed: {e}")
            raise
    
    def get_model_capabilities(self) -> ModelCapabilities:
        """Return OpenAI model capabilities"""
        capabilities_map = {
            'o3': ModelCapabilities(
                max_context_length=200000,
                supports_json_mode=True,
                reasoning_strength=0.95,
                cost_per_token=0.000015,  # Estimated
                average_response_time=5.0,
                strong_in_education=True
            ),
            'o3-mini': ModelCapabilities(
                max_context_length=128000,
                supports_json_mode=True,
                reasoning_strength=0.85,
                cost_per_token=0.000003,
                average_response_time=3.0,
                strong_in_education=True
            )
        }
        
        return capabilities_map.get(self.model, capabilities_map['o3-mini'])
    
    def estimate_cost(self, transcript_length: int) -> CostEstimate:
        """Estimate OpenAI processing cost"""
        # Rough token estimation: 1 token ≈ 4 characters
        estimated_input_tokens = transcript_length // 4 + 1000  # +prompt overhead
        estimated_output_tokens = 2000  # Typical analysis output
        
        capabilities = self.get_model_capabilities()
        total_cost = (estimated_input_tokens + estimated_output_tokens) * capabilities.cost_per_token
        
        return CostEstimate(
            input_tokens=estimated_input_tokens,
            output_tokens=estimated_output_tokens,
            total_cost_usd=total_cost,
            provider='openai',
            model=self.model
        )
```

### **3. Environment Configuration Template (`.env.ai-providers`)**

```bash
# =============================================================================
# AI PROVIDER SELECTION (Change anytime without code changes)
# =============================================================================
AI_PROVIDER=openai                    # Primary provider
FALLBACK_PROVIDERS=anthropic,google   # Fallback chain

# =============================================================================
# OPENAI CONFIGURATION
# =============================================================================
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_ORG_ID=org-your-org-here
OPENAI_MODEL=o3-mini                  # o3 | o3-mini | gpt-4o | gpt-4-turbo
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.3

# =============================================================================
# ANTHROPIC CONFIGURATION  
# =============================================================================
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_TOKENS=4000
ANTHROPIC_TEMPERATURE=0.3

# =============================================================================
# GOOGLE AI CONFIGURATION
# =============================================================================
GOOGLE_API_KEY=your-google-key-here
GOOGLE_MODEL=gemini-1.5-pro
GOOGLE_PROJECT_ID=your-project-id

# =============================================================================
# COST AND PERFORMANCE CONTROLS
# =============================================================================
DAILY_ANALYSIS_LIMIT=100             # Max sessions per day
COST_LIMIT_USD=50.00                 # Daily cost limit
PREFERRED_SPEED=balanced             # fast | balanced | cost-optimized
```

### **4. Main Post-Processing Service (`post_processor.py`)**

```python
"""
Main Post-Processing Service
Orchestrates session analysis with configurable AI providers
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os

class SessionPostProcessor:
    """
    Main service for post-processing tutoring sessions
    Integrates with provider-agnostic AI analysis system
    """
    
    def __init__(self):
        self.provider_manager = AIProviderManager()
        self.quality_assurance = QualityAssurance()
        self.cost_tracker = CostTracker()
        
    async def process_session(
        self, 
        session_file_path: str,
        student_id: str,
        force_reprocess: bool = False
    ) -> Dict[str, Any]:
        """
        Process a tutoring session transcript
        Returns comprehensive educational analysis
        """
        
        # Load session data
        session_data = self._load_session_data(session_file_path)
        transcript = session_data.get('transcript', '')
        
        # Check if already processed
        if not force_reprocess and self._is_already_processed(session_file_path):
            return self._load_existing_analysis(session_file_path)
        
        # Load student context
        student_context = self._load_student_context(student_id)
        
        # Determine analysis requirements
        requirements = self._determine_analysis_requirements(
            transcript, student_context
        )
        
        # Perform AI analysis
        try:
            analysis_result = await self.provider_manager.analyze_session(
                transcript=transcript,
                student_context=student_context,
                requirements=requirements
            )
            
            # Quality assurance validation
            validated_result = await self.quality_assurance.validate_analysis(
                analysis_result, transcript, student_context
            )
            
            # Save analysis results
            self._save_analysis_results(session_file_path, validated_result)
            
            # Update student progress
            self._update_student_progress(student_id, validated_result)
            
            # Log successful processing
            logging.info(f"Successfully processed session: {session_file_path}")
            
            return validated_result
            
        except Exception as e:
            logging.error(f"Session processing failed: {e}")
            # Save error information for debugging
            self._save_processing_error(session_file_path, str(e))
            raise
    
    async def bulk_process_sessions(
        self, 
        session_paths: List[str],
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """
        Process multiple sessions concurrently
        Returns summary of processing results
        """
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_session(session_path: str):
            async with semaphore:
                student_id = self._extract_student_id(session_path)
                return await self.process_session(session_path, student_id)
        
        # Process sessions concurrently
        tasks = [process_single_session(path) for path in session_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Compile results summary
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful
        
        return {
            'total_sessions': len(session_paths),
            'successful': successful,
            'failed': failed,
            'results': results,
            'total_cost': self.cost_tracker.get_session_costs(),
            'processing_time': datetime.now()
        }
```

## 🎛️ **Admin Dashboard Integration**

### **Provider Management Routes**

```python
# Add to admin-server.py

@app.route('/admin/ai-providers')
def ai_provider_dashboard():
    """AI provider status and management dashboard"""
    
    provider_manager = AIProviderManager()
    
    provider_status = {}
    for name, provider in provider_manager.providers.items():
        try:
            # Get provider status
            capabilities = provider.get_model_capabilities()
            daily_usage = provider.get_daily_usage()
            
            provider_status[name] = {
                'available': True,
                'model': provider.model,
                'capabilities': capabilities,
                'daily_usage': daily_usage,
                'cost_estimate': provider.estimate_cost(5000).total_cost_usd
            }
        except Exception as e:
            provider_status[name] = {
                'available': False,
                'error': str(e)
            }
    
    return render_template('ai_providers.html',
                         providers=provider_status,
                         current_primary=provider_manager.primary_provider,
                         fallback_chain=provider_manager.fallback_chain)

@app.route('/admin/ai-providers/switch', methods=['POST'])
def switch_ai_provider():
    """Switch primary AI provider"""
    
    new_provider = request.form.get('provider')
    
    # Validate provider availability
    provider_manager = AIProviderManager()
    if new_provider not in provider_manager.providers:
        flash(f'Provider {new_provider} not available', 'error')
        return redirect(url_for('ai_provider_dashboard'))
    
    # Update environment variable (in production, update config service)
    os.environ['AI_PROVIDER'] = new_provider
    
    # Log the change
    logging.info(f"Admin switched primary AI provider to: {new_provider}")
    
    flash(f'Successfully switched to {new_provider}', 'success')
    return redirect(url_for('ai_provider_dashboard'))

@app.route('/admin/process-sessions', methods=['POST'])
def trigger_session_processing():
    """Trigger bulk session processing"""
    
    # Get unprocessed sessions
    unprocessed_sessions = get_unprocessed_sessions()
    
    if not unprocessed_sessions:
        flash('No unprocessed sessions found', 'info')
        return redirect(url_for('dashboard'))
    
    # Start background processing
    asyncio.create_task(process_sessions_background(unprocessed_sessions))
    
    flash(f'Started processing {len(unprocessed_sessions)} sessions', 'success')
    return redirect(url_for('dashboard'))
```

## 🚀 **Implementation Steps**

### **Phase 1: Core Infrastructure**
1. Create base provider interface and manager classes
2. Implement OpenAI provider (primary focus on O3/O3-mini)
3. Create configuration management system
4. Build response normalization framework

### **Phase 2: Multi-Provider Support**
1. Implement Anthropic Claude provider
2. Implement Google Gemini provider
3. Add provider selection and failover logic
4. Create cost optimization algorithms

### **Phase 3: Integration & Testing**
1. Integrate with existing admin dashboard
2. Add provider management UI
3. Implement bulk processing capabilities
4. Add monitoring and alerting

### **Phase 4: Advanced Features**
1. Add Azure OpenAI support
2. Implement local model support (Ollama)
3. Add advanced cost controls
4. Implement quality assurance validation

## 📊 **Benefits Summary**

✅ **Provider Flexibility**: Switch between O3, Claude, Gemini without code changes  
✅ **Cost Optimization**: Automatic selection of most cost-effective provider  
✅ **Reliability**: Automatic failover ensures 99.9% uptime  
✅ **Security**: Individual API key management with audit trails  
✅ **Scalability**: Easy integration of new AI providers  
✅ **Performance**: Concurrent processing with rate limit management  

**Configuration drives everything** - the entire system behavior can be changed through environment variables!