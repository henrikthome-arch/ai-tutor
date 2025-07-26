"""
AI Prompt templates for educational session analysis
Centralized prompt management for easy review and updates
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PromptTemplate:
    """Template for AI prompts with metadata"""
    name: str
    version: str
    description: str
    system_prompt: str
    user_prompt_template: str
    parameters: Dict[str, str]
    created_date: datetime
    last_updated: datetime

class EducationalPromptManager:
    """Manages all educational analysis prompts"""
    
    def __init__(self):
        self.prompts = {}
        self._initialize_prompts()
    
    def _initialize_prompts(self):
        """Initialize all prompt templates"""
        
        # Main Educational Session Analysis Prompt
        self.prompts['session_analysis'] = PromptTemplate(
            name="Educational Session Analysis",
            version="1.0",
            description="Comprehensive analysis of tutoring session transcripts",
            system_prompt="""You are an expert educational analyst specializing in personalized learning assessment. Your role is to analyze tutoring session transcripts and provide actionable insights for educators and students.

ANALYSIS FRAMEWORK:
- Focus on learning outcomes and educational progress
- Consider individual student learning styles and preferences
- Provide evidence-based insights grounded in the session transcript
- Maintain professional, supportive, and constructive tone
- Use educational terminology appropriately for the student's age and level

RESPONSE STRUCTURE:
You must provide analysis in exactly these four categories:
1. Conceptual Understanding
2. Engagement Level  
3. Progress Indicators
4. Recommendations

Each section should be 2-3 sentences with specific examples from the session.""",
            
            user_prompt_template="""Please analyze this tutoring session transcript and provide educational insights.

STUDENT CONTEXT:
- Name: {student_name}
- Age: {student_age}
- Grade: {student_grade}
- Subject Focus: {subject_focus}
- Learning Style: {learning_style}
- Primary Interests: {primary_interests}
- Motivational Triggers: {motivational_triggers}

SESSION TRANSCRIPT:
{transcript}

Please provide your analysis in these four categories:

1. CONCEPTUAL UNDERSTANDING:
[Assess how well the student grasped the core concepts presented. Reference specific moments from the transcript where understanding was demonstrated or challenged.]

2. ENGAGEMENT LEVEL:
[Evaluate the student's participation, enthusiasm, and active involvement throughout the session. Cite specific examples of engagement or disengagement.]

3. PROGRESS INDICATORS:
[Identify evidence of learning progression, skill development, or knowledge building during the session. Note any breakthroughs or persistent challenges.]

4. RECOMMENDATIONS:
[Provide 2-3 specific, actionable suggestions for future sessions based on this student's learning profile and session performance.]

Base all insights on evidence from the transcript and consider the student's individual learning context.""",
            
            parameters={
                "student_name": "Student's name",
                "student_age": "Student's age",
                "student_grade": "Current grade level",
                "subject_focus": "Main subject/topic of session",
                "learning_style": "Student's preferred learning approach",
                "primary_interests": "Student's interests and hobbies",
                "motivational_triggers": "What motivates this student",
                "transcript": "Full session transcript"
            },
            created_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Quick Assessment Prompt (for shorter sessions)
        self.prompts['quick_assessment'] = PromptTemplate(
            name="Quick Session Assessment",
            version="1.0", 
            description="Rapid analysis for shorter tutoring sessions",
            system_prompt="""You are an educational assessment specialist providing rapid insights on tutoring sessions. Focus on the most important learning indicators and provide concise, actionable feedback.

Keep responses focused and practical for immediate educator use.""",
            
            user_prompt_template="""Analyze this brief tutoring session for key educational insights.

STUDENT: {student_name} (Age {student_age}, Grade {student_grade})
SUBJECT: {subject_focus}

TRANSCRIPT:
{transcript}

Provide a concise analysis covering:
1. Key learning achievement in this session
2. Student engagement level and participation
3. One specific recommendation for the next session

Keep each point to 1-2 sentences with transcript evidence.""",
            
            parameters={
                "student_name": "Student's name",
                "student_age": "Student's age", 
                "student_grade": "Current grade level",
                "subject_focus": "Main subject/topic",
                "transcript": "Session transcript"
            },
            created_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Progress Tracking Prompt (for multi-session analysis)
        self.prompts['progress_tracking'] = PromptTemplate(
            name="Progress Tracking Analysis",
            version="1.0",
            description="Compare progress across multiple sessions",
            system_prompt="""You are a learning progress specialist analyzing student development across multiple tutoring sessions. Focus on growth patterns, skill development, and long-term educational trends.

Provide insights that help educators understand learning trajectories and adjust teaching strategies accordingly.""",
            
            user_prompt_template="""Analyze this student's progress by comparing their current session with previous sessions.

STUDENT PROFILE:
- Name: {student_name}
- Age: {student_age}, Grade: {student_grade}
- Learning Goals: {learning_goals}

CURRENT SESSION:
{current_transcript}

PREVIOUS SESSION SUMMARY:
{previous_summary}

ANALYSIS FOCUS:
1. PROGRESS COMPARISON: How has the student's understanding/performance changed?
2. SKILL DEVELOPMENT: What new abilities or improvements are evident?
3. LEARNING PATTERNS: What consistent strengths or challenges emerge?
4. TRAJECTORY ASSESSMENT: Is the student on track toward their learning goals?
5. STRATEGIC RECOMMENDATIONS: How should teaching approach be adjusted based on progress patterns?

Provide specific examples from both sessions to support your analysis.""",
            
            parameters={
                "student_name": "Student's name",
                "student_age": "Student's age",
                "student_grade": "Current grade level", 
                "learning_goals": "Student's learning objectives",
                "current_transcript": "Most recent session transcript",
                "previous_summary": "Summary of previous session"
            },
            created_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Subject-Specific Math Prompt
        self.prompts['math_analysis'] = PromptTemplate(
            name="Mathematics Session Analysis",
            version="1.0",
            description="Specialized analysis for mathematics tutoring sessions",
            system_prompt="""You are a mathematics education specialist with expertise in mathematical learning progression and problem-solving development. Analyze the session with focus on mathematical thinking, problem-solving strategies, and conceptual understanding.

Pay special attention to:
- Mathematical reasoning and logic
- Problem-solving approaches and strategies
- Conceptual vs. procedural understanding
- Mathematical communication and vocabulary
- Common misconceptions and error patterns""",
            
            user_prompt_template="""Analyze this mathematics tutoring session for mathematical learning insights.

STUDENT: {student_name} (Age {student_age}, Grade {student_grade})
MATH TOPIC: {math_topic}
LEARNING STYLE: {learning_style}

SESSION TRANSCRIPT:
{transcript}

MATHEMATICAL ANALYSIS:

1. CONCEPTUAL UNDERSTANDING:
[Assess grasp of mathematical concepts, not just procedures. What mathematical ideas did the student demonstrate understanding of?]

2. PROBLEM-SOLVING STRATEGIES:
[Evaluate the approaches and methods the student used. What strategies were effective or ineffective?]

3. MATHEMATICAL COMMUNICATION:
[How well did the student explain their thinking and use mathematical vocabulary?]

4. ERROR ANALYSIS:
[Identify any misconceptions, calculation errors, or flawed reasoning patterns.]

5. MATHEMATICAL CONFIDENCE:
[Assess the student's confidence and willingness to tackle mathematical challenges.]

6. NEXT STEPS:
[Recommend specific mathematical concepts, skills, or strategies to focus on in future sessions.]

Ground all observations in specific examples from the transcript.""",
            
            parameters={
                "student_name": "Student's name",
                "student_age": "Student's age",
                "student_grade": "Current grade level",
                "math_topic": "Specific math topic covered",
                "learning_style": "Student's learning preferences",
                "transcript": "Session transcript"
            },
            created_date=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Reading/Language Arts Prompt
        self.prompts['reading_analysis'] = PromptTemplate(
            name="Reading & Language Arts Analysis", 
            version="1.0",
            description="Specialized analysis for reading and language arts sessions",
            system_prompt="""You are a literacy specialist with expertise in reading comprehension, language development, and literary analysis. Focus on reading skills, comprehension strategies, vocabulary development, and communication abilities.

Key areas of assessment:
- Reading fluency and accuracy
- Comprehension strategies and depth
- Vocabulary acquisition and usage
- Written and oral communication skills
- Literary analysis and critical thinking""",
            
            user_prompt_template="""Analyze this reading/language arts tutoring session for literacy development insights.

STUDENT: {student_name} (Age {student_age}, Grade {student_grade}) 
READING LEVEL: {reading_level}
SESSION FOCUS: {session_focus}

SESSION TRANSCRIPT:
{transcript}

LITERACY ANALYSIS:

1. READING SKILLS:
[Assess fluency, accuracy, and reading strategies demonstrated during the session.]

2. COMPREHENSION:
[Evaluate understanding of text, inference skills, and comprehension strategies used.]

3. VOCABULARY DEVELOPMENT:
[Note new vocabulary encountered, understanding of word meanings, and usage in context.]

4. COMMUNICATION SKILLS:
[Assess both verbal and written expression, clarity of ideas, and language use.]

5. CRITICAL THINKING:
[Evaluate analytical thinking, text connections, and depth of literary understanding.]

6. LITERACY RECOMMENDATIONS:
[Suggest specific reading skills, comprehension strategies, or literacy activities for future sessions.]

Provide specific examples from the session to support each assessment.""",
            
            parameters={
                "student_name": "Student's name",
                "student_age": "Student's age", 
                "student_grade": "Current grade level",
                "reading_level": "Student's reading level",
                "session_focus": "Reading/writing focus of session",
                "transcript": "Session transcript"
            },
            created_date=datetime.now(),
            last_updated=datetime.now()
        )
    
    def get_prompt(self, prompt_name: str) -> Optional[PromptTemplate]:
        """Get a specific prompt template"""
        return self.prompts.get(prompt_name)
    
    def get_available_prompts(self) -> Dict[str, str]:
        """Get list of available prompts with descriptions"""
        return {
            name: prompt.description 
            for name, prompt in self.prompts.items()
        }
    
    def format_prompt(self, prompt_name: str, **kwargs) -> Optional[Dict[str, str]]:
        """Format a prompt with provided parameters"""
        prompt = self.get_prompt(prompt_name)
        if not prompt:
            return None
        
        try:
            formatted_user_prompt = prompt.user_prompt_template.format(**kwargs)
            return {
                'system_prompt': prompt.system_prompt,
                'user_prompt': formatted_user_prompt,
                'name': prompt.name,
                'version': prompt.version
            }
        except KeyError as e:
            raise ValueError(f"Missing required parameter for prompt '{prompt_name}': {e}")
    
    def update_prompt(self, prompt_name: str, **updates):
        """Update an existing prompt template"""
        if prompt_name not in self.prompts:
            raise ValueError(f"Prompt '{prompt_name}' not found")
        
        prompt = self.prompts[prompt_name]
        
        for field, value in updates.items():
            if hasattr(prompt, field):
                setattr(prompt, field, value)
        
        prompt.last_updated = datetime.now()
        return prompt
    
    def add_custom_prompt(self, prompt_template: PromptTemplate):
        """Add a new custom prompt template"""
        self.prompts[prompt_template.name.lower().replace(' ', '_')] = prompt_template

# Global prompt manager instance
prompt_manager = EducationalPromptManager()