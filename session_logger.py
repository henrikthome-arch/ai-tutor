#!/usr/bin/env python3
"""
Session Logger for AI Tutor System
Automatically logs conversations and generates post-session analysis
"""

import os
import json
import requests
from datetime import datetime
from openai import OpenAI

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class SessionLogger:
    def __init__(self, student_id, cloud_server_url="https://ai-tutor-ptnl.onrender.com"):
        self.student_id = student_id
        self.cloud_server_url = cloud_server_url
        self.session_date = datetime.now().strftime("%Y-%m-%d")
        self.session_dir = f"data/students/{student_id}/sessions"
        self.transcript_file = f"{self.session_dir}/{self.session_date}_transcript.txt"
        self.summary_file = f"{self.session_dir}/{self.session_date}_summary.json"
        
        # Ensure session directory exists
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Initialize transcript
        self.conversation_log = []
        
        # OpenAI client for analysis
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def log_message(self, role, message, function_call=None):
        """Log a message in the conversation"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        log_entry = {
            "timestamp": timestamp,
            "role": role,
            "message": message
        }
        
        if function_call:
            log_entry["function_call"] = function_call
        
        self.conversation_log.append(log_entry)
        
        # Append to transcript file
        with open(self.transcript_file, 'a', encoding='utf-8') as f:
            if function_call:
                f.write(f"[{timestamp}] {role.upper()}: {message}\n")
                f.write(f"[{timestamp}] FUNCTION_CALL: {function_call}\n")
            else:
                f.write(f"[{timestamp}] {role.upper()}: {message}\n")
    
    def generate_session_summary(self):
        """Generate AI-powered session analysis"""
        if not self.conversation_log:
            return None
        
        # Prepare conversation text for analysis
        conversation_text = ""
        for entry in self.conversation_log:
            role = entry["role"].upper()
            message = entry["message"]
            conversation_text += f"{role}: {message}\n"
        
        # Get current student context
        student_context = self._get_student_context()
        
        # Generate analysis prompt
        analysis_prompt = f"""
        Analyze this tutoring session for {self.student_id}:

        CONVERSATION:
        {conversation_text}

        STUDENT CONTEXT:
        {json.dumps(student_context, indent=2)}

        Please provide a comprehensive session analysis in JSON format with:
        1. session_summary: Brief overview of what was covered
        2. learning_outcomes: What the student learned or practiced
        3. engagement_level: High/Medium/Low with explanation
        4. concepts_mastered: List of concepts student showed understanding of
        5. concepts_struggling: List of areas where student needed help
        6. next_session_recommendations: Specific suggestions for next session
        7. progress_updates: Suggested updates to student progress tracking
        8. curriculum_alignment: How this session aligns with curriculum goals

        Return only valid JSON.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse JSON response
            analysis = json.loads(analysis_text)
            
            # Add metadata
            session_summary = {
                "session_date": self.session_date,
                "student_id": self.student_id,
                "session_duration": len(self.conversation_log),
                "analysis": analysis,
                "generated_at": datetime.now().isoformat()
            }
            
            # Save summary to file
            with open(self.summary_file, 'w', encoding='utf-8') as f:
                json.dump(session_summary, f, indent=2, ensure_ascii=False)
            
            return session_summary
            
        except Exception as e:
            print(f"❌ Error generating session summary: {e}")
            return None
    
    def _get_student_context(self):
        """Get current student context from cloud server"""
        try:
            response = requests.get(
                f"{self.cloud_server_url}/mcp/get-student-context",
                params={"student_id": self.student_id},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error getting student context: {e}")
            return {}
    
    def update_student_progress(self, session_summary):
        """Update student progress based on session analysis"""
        if not session_summary or 'analysis' not in session_summary:
            return False
        
        try:
            analysis = session_summary['analysis']
            progress_file = f"data/students/{self.student_id}/progress.json"
            
            # Load current progress
            if os.path.exists(progress_file):
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
            else:
                progress = {}
            
            # Update with new insights
            if 'progress_updates' in analysis:
                progress['last_session'] = {
                    'date': self.session_date,
                    'concepts_mastered': analysis.get('concepts_mastered', []),
                    'concepts_struggling': analysis.get('concepts_struggling', []),
                    'next_recommendations': analysis.get('next_session_recommendations', '')
                }
            
            # Add session history
            if 'session_history' not in progress:
                progress['session_history'] = []
            
            progress['session_history'].append({
                'date': self.session_date,
                'summary': analysis.get('session_summary', ''),
                'engagement': analysis.get('engagement_level', 'Unknown')
            })
            
            # Keep only last 10 sessions
            progress['session_history'] = progress['session_history'][-10:]
            
            # Save updated progress
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Updated progress for {self.student_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating student progress: {e}")
            return False
    
    def finalize_session(self):
        """Complete session logging and analysis"""
        print(f"\n🔄 Finalizing session for {self.student_id}...")
        
        # Generate session summary
        summary = self.generate_session_summary()
        
        if summary:
            print(f"✅ Session summary generated: {self.summary_file}")
            
            # Update student progress
            if self.update_student_progress(summary):
                print(f"✅ Student progress updated")
            
            # Print key insights
            analysis = summary.get('analysis', {})
            print(f"\n📊 SESSION INSIGHTS:")
            print(f"   Engagement: {analysis.get('engagement_level', 'Unknown')}")
            print(f"   Concepts Mastered: {len(analysis.get('concepts_mastered', []))}")
            print(f"   Areas for Improvement: {len(analysis.get('concepts_struggling', []))}")
            
            return summary
        else:
            print("❌ Failed to generate session summary")
            return None

# Example usage function
def demo_session_logging():
    """Demonstrate session logging functionality"""
    logger = SessionLogger("emma_smith")
    
    # Simulate a conversation
    logger.log_message("user", "Hi! Can you help me with math today?")
    logger.log_message("assistant", "Hello Emma! I'd love to help you with math. Let me check your progress first.", 
                       function_call="get_student_context({'student_id': 'emma_smith'})")
    logger.log_message("assistant", "I can see you're working on Grade 4 math and doing well with addition. Would you like to practice multiplication today?")
    logger.log_message("user", "Yes! I want to learn the 7 times table.")
    logger.log_message("assistant", "Great choice! Let's start with 7 x 1. What do you think that equals?")
    logger.log_message("user", "7!")
    logger.log_message("assistant", "Perfect! Now try 7 x 2.")
    logger.log_message("user", "14!")
    logger.log_message("assistant", "Excellent! You're getting the hang of this. How about 7 x 3?")
    logger.log_message("user", "Hmm... 21?")
    logger.log_message("assistant", "That's absolutely right! You're doing fantastic with the 7 times table.")
    
    # Finalize the session
    summary = logger.finalize_session()
    return summary

if __name__ == "__main__":
    demo_session_logging()