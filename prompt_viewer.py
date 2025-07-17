"""
Prompt Viewer and Tester
View and test all AI prompts for educational session analysis
"""

import asyncio
import sys
sys.path.append('.')

from ai_poc.prompts import prompt_manager

def view_all_prompts():
    """Display all available prompts"""
    print("🎯 AI Educational Analysis Prompts")
    print("=" * 60)
    
    available_prompts = prompt_manager.get_available_prompts()
    
    for i, (prompt_name, description) in enumerate(available_prompts.items(), 1):
        prompt = prompt_manager.get_prompt(prompt_name)
        
        print(f"\n{i}. {prompt.name}")
        print(f"   Version: {prompt.version}")
        print(f"   Description: {description}")
        print(f"   Created: {prompt.created_date.strftime('%Y-%m-%d')}")
        print(f"   Updated: {prompt.last_updated.strftime('%Y-%m-%d')}")
        
        print(f"\n   📋 SYSTEM PROMPT:")
        print(f"   {prompt.system_prompt[:200]}...")
        
        print(f"\n   📝 PARAMETERS REQUIRED:")
        for param, desc in prompt.parameters.items():
            print(f"   - {param}: {desc}")
        
        print(f"\n   🔧 USER PROMPT TEMPLATE (first 300 chars):")
        print(f"   {prompt.user_prompt_template[:300]}...")
        print("\n" + "-" * 60)

def test_prompt_formatting():
    """Test prompt formatting with sample data"""
    print("\n🧪 TESTING PROMPT FORMATTING")
    print("=" * 60)
    
    # Sample student data for Emma Smith
    sample_data = {
        'student_name': 'Emma Smith',
        'student_age': '9',
        'student_grade': '4',
        'subject_focus': 'Mathematics - Division',
        'learning_style': 'Visual learner, prefers hands-on activities',
        'primary_interests': 'Dinosaurs, space exploration, drawing',
        'motivational_triggers': 'Achievement badges, helping characters solve problems',
        'transcript': '[14:00] AI: Hi Emma! Today we\'re helping paleontologists divide dinosaur fossils...\n[14:01] Emma: Yes! I love dinosaurs!\n[Sample transcript truncated for demo]',
        'math_topic': 'Division with remainders',
        'reading_level': 'Grade 4-5',
        'session_focus': 'Reading comprehension',
        'learning_goals': 'Master division concepts, build mathematical confidence',
        'current_transcript': 'Current session content...',
        'previous_summary': 'Previous session showed progress in basic division...'
    }
    
    # Test each prompt
    for prompt_name in prompt_manager.get_available_prompts().keys():
        try:
            formatted = prompt_manager.format_prompt(prompt_name, **sample_data)
            
            if formatted:
                print(f"\n✅ {formatted['name']} (v{formatted['version']})")
                print(f"System Prompt Length: {len(formatted['system_prompt'])} characters")
                print(f"User Prompt Length: {len(formatted['user_prompt'])} characters")
                
                print(f"\n📋 FORMATTED USER PROMPT (first 500 chars):")
                print(formatted['user_prompt'][:500] + "...")
                
        except Exception as e:
            print(f"\n❌ Error formatting {prompt_name}: {e}")
        
        print("\n" + "-" * 40)

def interactive_prompt_viewer():
    """Interactive prompt exploration"""
    while True:
        print("\n🎯 PROMPT MANAGEMENT MENU")
        print("1. View all prompts")
        print("2. Test prompt formatting")
        print("3. View specific prompt")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            view_all_prompts()
        elif choice == '2':
            test_prompt_formatting()
        elif choice == '3':
            available = list(prompt_manager.get_available_prompts().keys())
            print(f"\nAvailable prompts:")
            for i, name in enumerate(available, 1):
                print(f"{i}. {name}")
            
            try:
                idx = int(input(f"\nSelect prompt (1-{len(available)}): ")) - 1
                if 0 <= idx < len(available):
                    prompt_name = available[idx]
                    prompt = prompt_manager.get_prompt(prompt_name)
                    
                    print(f"\n📋 {prompt.name} (v{prompt.version})")
                    print(f"Description: {prompt.description}")
                    print(f"\nSYSTEM PROMPT:")
                    print(prompt.system_prompt)
                    print(f"\nUSER PROMPT TEMPLATE:")
                    print(prompt.user_prompt_template)
                    print(f"\nPARAMETERS:")
                    for param, desc in prompt.parameters.items():
                        print(f"- {param}: {desc}")
                else:
                    print("Invalid selection")
            except ValueError:
                print("Please enter a number")
                
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please select 1-4.")

if __name__ == "__main__":
    print("🚀 AI Educational Prompt Management System")
    print("🔍 Review and test all analysis prompts")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--all':
        # Show all prompts in detail
        view_all_prompts()
        print("\n🧪 Testing prompt formatting...")
        test_prompt_formatting()
    else:
        # Interactive mode
        interactive_prompt_viewer()