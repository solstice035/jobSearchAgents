"""
Conversation Flow Structure for Career Coach Agent

This module defines the conversation flow for the Career Coach Agent, structuring
the coaching conversation through several phases to guide users in their career 
development journey.
"""

from enum import Enum
from typing import Dict, List, Any, Optional

class ConversationPhase(Enum):
    """Defines the different phases of the career coaching conversation."""
    
    INITIAL = "initial"
    SKILLS_EXPLORATION = "skills_exploration"
    VALUES_EXPLORATION = "values_exploration"
    MARKET_ALIGNMENT = "market_alignment"
    REFINEMENT = "refinement"
    ROADMAP = "roadmap"


class ConversationFlow:
    """
    Manages the structured flow of career coaching conversations.
    
    The conversation follows a progression through distinct phases:
    1. Initial Phase: Understanding the user's current situation and goals
    2. Skills Exploration: Identifying strengths, weaknesses, and skill gaps
    3. Values Exploration: Understanding what matters most in their career
    4. Market Alignment: Connecting profile with current market opportunities
    5. Refinement: Focusing options and creating specific action plans
    6. Roadmap: Generating a personalized career development plan
    """
    
    def __init__(self):
        """Initialize the conversation flow with phase definitions and transitions."""
        # Phase definitions with descriptions and objectives
        self.phases = {
            ConversationPhase.INITIAL: {
                "description": "Understanding your current situation and career goals",
                "objectives": [
                    "Establish a baseline understanding of your career background",
                    "Identify your primary career goals and aspirations",
                    "Understand any specific challenges you're facing",
                    "Set expectations for the coaching process"
                ],
                "completion_criteria": [
                    "Current role/situation identified",
                    "Primary career goals articulated",
                    "Timeline expectations established"
                ]
            },
            ConversationPhase.SKILLS_EXPLORATION: {
                "description": "Exploring your skills, strengths, and areas for development",
                "objectives": [
                    "Identify your core technical and professional skills",
                    "Recognize your key strengths and competitive advantages",
                    "Discover skill gaps relevant to your goals",
                    "Prioritize skills for development"
                ],
                "completion_criteria": [
                    "Key strengths identified",
                    "Priority skill gaps recognized",
                    "Skill development priorities established"
                ]
            },
            ConversationPhase.VALUES_EXPLORATION: {
                "description": "Understanding what matters most to you in your career",
                "objectives": [
                    "Identify your core professional values",
                    "Explore work environment preferences",
                    "Understand your motivation drivers",
                    "Clarify work-life balance considerations"
                ],
                "completion_criteria": [
                    "Top professional values articulated",
                    "Work environment preferences established",
                    "Key motivational factors identified"
                ]
            },
            ConversationPhase.MARKET_ALIGNMENT: {
                "description": "Aligning your profile with current market opportunities",
                "objectives": [
                    "Identify market sectors/industries aligned with your profile",
                    "Explore relevant roles based on your skills and values",
                    "Consider market trends affecting your target paths",
                    "Evaluate potential career paths based on market demand"
                ],
                "completion_criteria": [
                    "Target industries/sectors identified",
                    "Potential roles matching profile explored",
                    "Market demand factors considered"
                ]
            },
            ConversationPhase.REFINEMENT: {
                "description": "Refining your focus and creating specific plans",
                "objectives": [
                    "Narrow down optimal career paths",
                    "Develop specific action steps for each potential path",
                    "Identify potential obstacles and mitigation strategies",
                    "Prioritize next actions based on impact and feasibility"
                ],
                "completion_criteria": [
                    "Primary career path(s) selected",
                    "Specific action steps defined",
                    "Potential obstacles identified",
                    "Next actions prioritized"
                ]
            },
            ConversationPhase.ROADMAP: {
                "description": "Creating your personalized career development roadmap",
                "objectives": [
                    "Develop a comprehensive career roadmap with timelines",
                    "Define short, medium, and long-term goals",
                    "Outline specific skill development plans",
                    "Establish success metrics and milestones"
                ],
                "completion_criteria": [
                    "Comprehensive roadmap created",
                    "Timelined goals established",
                    "Success metrics defined"
                ]
            }
        }
        
        # Define phase transitions (which phase can lead to which)
        self.transitions = {
            ConversationPhase.INITIAL: [ConversationPhase.SKILLS_EXPLORATION],
            ConversationPhase.SKILLS_EXPLORATION: [ConversationPhase.VALUES_EXPLORATION],
            ConversationPhase.VALUES_EXPLORATION: [ConversationPhase.MARKET_ALIGNMENT],
            ConversationPhase.MARKET_ALIGNMENT: [ConversationPhase.REFINEMENT],
            ConversationPhase.REFINEMENT: [ConversationPhase.ROADMAP],
            ConversationPhase.ROADMAP: []  # End of flow
        }
        
        # Questions for each phase to guide the conversation
        self.phase_questions = {
            ConversationPhase.INITIAL: [
                "Can you tell me about your current role and responsibilities?",
                "What are your main career goals right now?",
                "What timeline are you considering for your next career move?",
                "Are there specific challenges you're facing in your career?",
                "What prompted you to seek career guidance at this time?"
            ],
            ConversationPhase.SKILLS_EXPLORATION: [
                "What technical skills do you consider your strongest?",
                "Which soft skills or professional competencies set you apart?",
                "In your current or most recent role, what skills have you used most frequently?",
                "What skills do you think you need to develop for your target career path?",
                "Are there skills you've started learning but haven't fully developed yet?"
            ],
            ConversationPhase.VALUES_EXPLORATION: [
                "What aspects of your work bring you the most satisfaction?",
                "How important is work-life balance to you?",
                "Do you prefer working independently or as part of a team?",
                "What type of company culture do you thrive in?",
                "How important are factors like compensation, growth opportunities, and job security to you?"
            ],
            ConversationPhase.MARKET_ALIGNMENT: [
                "Which industries or sectors interest you the most?",
                "Are you open to roles in emerging fields related to your experience?",
                "How familiar are you with current trends in your target industry?",
                "What role titles would you consider for your next position?",
                "Are there geographical preferences or constraints for your job search?"
            ],
            ConversationPhase.REFINEMENT: [
                "Based on our discussion, which career path seems most aligned with your goals and values?",
                "What specific steps would you need to take to move toward this path?",
                "What potential obstacles do you anticipate in pursuing this direction?",
                "What resources or support might you need to succeed?",
                "Which actions would make the most impact in the short term?"
            ],
            ConversationPhase.ROADMAP: [
                "What would you like to accomplish in the next 6-12 months?",
                "Where do you see yourself in 3-5 years?",
                "How will you measure your progress and success?",
                "Which skill development areas should we prioritize in your roadmap?",
                "How frequently would you like to revisit and adjust your career plan?"
            ]
        }
    
    def get_phase_info(self, phase: ConversationPhase) -> Dict[str, Any]:
        """
        Get information about a specific conversation phase.
        
        Args:
            phase: The conversation phase to get information for
            
        Returns:
            Dictionary with phase description, objectives, and completion criteria
        """
        return self.phases.get(phase, {})
    
    def get_next_phases(self, current_phase: ConversationPhase) -> List[ConversationPhase]:
        """
        Get possible next phases from the current phase.
        
        Args:
            current_phase: The current conversation phase
            
        Returns:
            List of possible next phases
        """
        return self.transitions.get(current_phase, [])
    
    def get_questions_for_phase(self, phase: ConversationPhase) -> List[str]:
        """
        Get guiding questions for a specific phase.
        
        Args:
            phase: The conversation phase to get questions for
            
        Returns:
            List of questions for the specified phase
        """
        return self.phase_questions.get(phase, [])
    
    def determine_next_question(self, 
                               phase: ConversationPhase, 
                               conversation_history: List[Dict[str, str]],
                               user_data: Dict[str, Any]) -> Optional[str]:
        """
        Determine the next most appropriate question based on the conversation history.
        
        This is a placeholder for more sophisticated logic that could use LLM to
        generate contextually relevant questions based on the conversation so far.
        
        Args:
            phase: Current conversation phase
            conversation_history: List of previous messages
            user_data: Additional user data and preferences
            
        Returns:
            Next question to ask, or None if no appropriate question is found
        """
        # Simple implementation - just get questions for the phase and select one
        # that hasn't been covered yet
        
        # In a more advanced implementation, this would use the OpenAI API to 
        # generate contextually appropriate questions
        
        available_questions = self.get_questions_for_phase(phase)
        if not available_questions:
            return None
            
        # For now, just return the first question
        # In a real implementation, this would be much more sophisticated
        return available_questions[0]
    
    def check_phase_completion(self, 
                              phase: ConversationPhase, 
                              conversation_history: List[Dict[str, str]],
                              user_data: Dict[str, Any]) -> bool:
        """
        Check if the current phase can be considered complete.
        
        This is a placeholder for more sophisticated logic using LLMs to
        determine if the phase's objectives have been met.
        
        Args:
            phase: Current conversation phase
            conversation_history: List of previous messages
            user_data: Additional user data and preferences
            
        Returns:
            True if the phase is complete, False otherwise
        """
        # In a real implementation, this would use the OpenAI API to
        # analyze the conversation and determine if completion criteria are met
        
        # For now, just return False as a placeholder
        return False

# Additional context prompts for the agent to use during different phases
PHASE_SYSTEM_PROMPTS = {
    ConversationPhase.INITIAL: """
    You are an expert AI Career Coach in the initial exploration phase. Your goal is to understand the 
    user's current situation and career aspirations. Ask open-ended questions to learn about their:
    
    - Current role and responsibilities
    - Career background and experience level
    - Primary career goals and aspirations
    - Timeline for career transitions
    - Specific challenges they're facing
    
    Be warm, empathetic, and encouraging. Focus on building rapport and understanding their situation
    before jumping into advice or solutions. Take notes on key information they share to reference later.
    """,
    
    ConversationPhase.SKILLS_EXPLORATION: """
    You are an expert AI Career Coach in the skills exploration phase. Your goal is to help the user
    identify their technical and soft skills, strengths, and areas for development. Focus on:
    
    - Identifying core technical and professional skills
    - Recognizing key strengths and competitive advantages
    - Discovering skill gaps relevant to career goals
    - Prioritizing skills for development
    
    Ask probing questions about past experiences, achievements, and challenges to uncover skills
    they might not explicitly mention. Help them articulate their unique value proposition.
    """,
    
    ConversationPhase.VALUES_EXPLORATION: """
    You are an expert AI Career Coach in the values exploration phase. Your goal is to help the user
    understand what truly matters to them in their career. Focus on:
    
    - Identifying core professional values
    - Exploring work environment preferences
    - Understanding motivation drivers
    - Clarifying work-life balance considerations
    
    Ask reflective questions about what brings them satisfaction, when they've felt most engaged,
    and what aspects of work culture matter most to them. Listen for alignment or misalignment 
    between their current situation and values.
    """,
    
    ConversationPhase.MARKET_ALIGNMENT: """
    You are an expert AI Career Coach in the market alignment phase. Your goal is to help the user
    connect their profile with current market opportunities. Focus on:
    
    - Identifying market sectors/industries aligned with their profile
    - Exploring relevant roles based on their skills and values
    - Considering market trends affecting their target paths
    - Evaluating potential career paths based on market demand
    
    Share insights about current market conditions in their field of interest. Help them
    understand how their skills and experience might transfer to different roles or industries.
    """,
    
    ConversationPhase.REFINEMENT: """
    You are an expert AI Career Coach in the refinement phase. Your goal is to help the user
    narrow down their focus and create specific plans. Focus on:
    
    - Narrowing down optimal career paths
    - Developing specific action steps for each potential path
    - Identifying potential obstacles and mitigation strategies
    - Prioritizing next actions based on impact and feasibility
    
    Help them make decisions about which direction to pursue by weighing options against their
    skills, values, and market opportunities. Create specific, actionable steps rather than
    general advice.
    """,
    
    ConversationPhase.ROADMAP: """
    You are an expert AI Career Coach in the roadmap creation phase. Your goal is to help the user
    develop a comprehensive career development plan. Focus on:
    
    - Developing a comprehensive career roadmap with timelines
    - Defining short, medium, and long-term goals
    - Outlining specific skill development plans
    - Establishing success metrics and milestones
    
    Create a structured, timelined plan that the user can follow. Be specific about actions,
    resources, and measurements of success. Help them understand how each action connects
    to their larger career goals.
    """
}
