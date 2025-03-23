"""
Career Coach Agent

This module implements the Career Coach Agent using the OpenAI API and the conversation
flow structure to provide personalized career guidance to users.
"""

import os
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from openai import OpenAI

from .conversation_flow import ConversationPhase, ConversationFlow, PHASE_SYSTEM_PROMPTS

class CareerCoachAgent:
    """
    AI-powered Career Coach Agent that guides users through a structured
    career development conversation using OpenAI.
    """
    
    def __init__(self):
        """Initialize the Career Coach Agent with OpenAI configuration and conversation flow."""
        # Set up OpenAI API
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        
        # Base configuration
        self.model = "gpt-4-turbo"
        self.user_data_dir = os.path.expanduser(os.getenv("USER_DATA_DIR", "~/.jobSearchAgent"))
        
        # Ensure user data directory exists
        os.makedirs(self.user_data_dir, exist_ok=True)
        
        # Initialize conversation flow
        self.flow = ConversationFlow()
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
    
    def create_session(self, user_id: str) -> Dict[str, Any]:
        """
        Create a new coaching session for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Dictionary containing session information
        """
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Create session data
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "current_phase": ConversationPhase.INITIAL.value,
            "conversation": [],
            "collected_information": {
                "career_goals": [],
                "skills": {
                    "technical": [],
                    "soft": []
                },
                "values": [],
                "target_industries": [],
                "target_roles": [],
                "skill_gaps": [],
                "action_items": []
            }
        }
        
        # Save session data
        self._save_session_data(session_id, session_data)
        
        return {"session_id": session_id}
    
    def process_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """
        Process a user message within an existing coaching session.
        
        Args:
            session_id: Unique identifier for the session
            message: User's message text
            
        Returns:
            Dictionary containing the assistant's response and updated session information
        """
        # Load session data
        session_data = self._load_session_data(session_id)
        if not session_data:
            raise ValueError(f"Session not found: {session_id}")
        
        # Update conversation with user message
        session_data["conversation"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Get current phase
        current_phase_value = session_data.get("current_phase", ConversationPhase.INITIAL.value)
        current_phase = ConversationPhase(current_phase_value)
        
        # Get system prompt for current phase
        system_prompt = PHASE_SYSTEM_PROMPTS.get(current_phase, "")
        
        # Build messages for OpenAI
        messages = self._build_messages(session_data, system_prompt)
        
        # Get response from OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        
        # Extract response content
        assistant_message = response.choices[0].message.content
        
        # Update conversation with assistant response
        session_data["conversation"].append({
            "role": "assistant",
            "content": assistant_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Check if phase should progress and update if needed
        new_phase = self._check_phase_progression(current_phase, session_data)
        if new_phase != current_phase:
            session_data["current_phase"] = new_phase.value
        
        # Update session data
        session_data["last_updated"] = datetime.now().isoformat()
        self._save_session_data(session_id, session_data)
        
        # Return response
        return {
            "response": assistant_message,
            "session_id": session_id,
            "current_phase": session_data["current_phase"]
        }
    
    def analyze_cv(self, session_id: str, cv_text: str) -> Dict[str, Any]:
        """
        Analyze a CV and integrate insights into the coaching session.
        
        Args:
            session_id: Unique identifier for the session
            cv_text: Text content of the CV
            
        Returns:
            Dictionary containing analysis results and updated session information
        """
        # Load session data
        session_data = self._load_session_data(session_id)
        if not session_data:
            raise ValueError(f"Session not found: {session_id}")
        
        # Prepare prompt for CV analysis
        prompt = self._create_cv_analysis_prompt(cv_text)
        
        # Get analysis from OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are an expert career coach and CV analyst. Extract detailed information from the CV and provide a comprehensive analysis."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse the analysis results
        analysis_results = json.loads(response.choices[0].message.content)
        
        # Update session data with CV insights
        session_data["cv_analysis"] = analysis_results
        
        # Extract key information for the conversation
        self._update_session_with_cv_insights(session_data, analysis_results)
        
        # Save updated session data
        self._save_session_data(session_id, session_data)
        
        return {
            "analysis": analysis_results,
            "session_id": session_id
        }
    
    def generate_roadmap(self, session_id: str) -> Dict[str, Any]:
        """
        Generate a personalized career roadmap based on the coaching session.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            Dictionary containing the roadmap and updated session information
        """
        # Load session data
        session_data = self._load_session_data(session_id)
        if not session_data:
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if we have enough information for a roadmap
        if session_data.get("current_phase") != ConversationPhase.ROADMAP.value:
            raise ValueError("Cannot generate roadmap before reaching the roadmap phase")
        
        # Prepare roadmap prompt
        prompt = self._create_roadmap_prompt(session_data)
        
        # Get roadmap from OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are an expert career coach specializing in career planning and professional development. Create a detailed, personalized career roadmap."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse the roadmap
        roadmap_results = json.loads(response.choices[0].message.content)
        
        # Update session data with roadmap
        session_data["roadmap"] = roadmap_results
        session_data["last_updated"] = datetime.now().isoformat()
        
        # Save updated session data
        self._save_session_data(session_id, session_data)
        
        return {
            "roadmap": roadmap_results,
            "session_id": session_id
        }
    
    def extract_cv_data(self, cv_text: str) -> Dict[str, Any]:
        """
        Extract structured data from a CV.
        
        Args:
            cv_text: The text content of the CV
            
        Returns:
            Structured CV data with skills, experience, education, etc.
        """
        # Implement CV data extraction logic
        prompt = self._create_cv_analysis_prompt(cv_text)
        
        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are an expert CV analyst. Extract detailed information from the CV."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return json.loads(response.choices[0].message.content)
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get a summary of the current coaching session.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            Summary of key information collected in the session
        """
        # Load session data
        session_data = self._load_session_data(session_id)
        if not session_data:
            return {"error": "Session not found"}
        
        # Extract relevant information for summary
        return {
            "current_phase": session_data.get("current_phase"),
            "collected_information": session_data.get("collected_information", {}),
            "conversation_length": len(session_data.get("conversation", [])) // 2,  # Count of exchanges
            "cv_analysis_available": "cv_analysis" in session_data,
            "roadmap_available": "roadmap" in session_data
        }
    
    def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, str]:
        """
        Save user preferences to storage.
        
        Args:
            user_id: Unique identifier for the user
            preferences: Dictionary of user preferences
            
        Returns:
            Status message
        """
        preferences_path = os.path.join(self.user_data_dir, "preferences.json")
        
        # Load existing preferences if available
        all_preferences = {}
        if os.path.exists(preferences_path):
            try:
                with open(preferences_path, "r") as f:
                    all_preferences = json.load(f)
            except json.JSONDecodeError:
                all_preferences = {}
        
        # Update with new preferences
        all_preferences[user_id] = preferences
        
        # Save updated preferences
        with open(preferences_path, "w") as f:
            json.dump(all_preferences, f, indent=2)
        
        return {"status": "success", "message": "User preferences saved successfully"}
    
    def _build_messages(self, session_data: Dict[str, Any], system_prompt: str) -> List[Dict[str, str]]:
        """Build messages for OpenAI API from session data."""
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (limited to last 10 exchanges)
        conversation = session_data.get("conversation", [])
        
        # If we have more than 20 messages, include the first 4 for context and the last 16 for recency
        if len(conversation) > 20:
            start_messages = conversation[:4]
            recent_messages = conversation[-16:]
            relevant_conversation = start_messages + recent_messages
        else:
            relevant_conversation = conversation
        
        for message in relevant_conversation:
            messages.append({
                "role": message["role"],
                "content": message["content"]
            })
        
        return messages
    
    def _check_phase_progression(self, current_phase: ConversationPhase, 
                               session_data: Dict[str, Any]) -> ConversationPhase:
        """
        Check if the conversation should progress to the next phase.
        
        This is a simplified implementation. In a full implementation, we would use
        more sophisticated logic or even LLM evaluation to determine phase transitions.
        """
        # Get conversation
        conversation = session_data.get("conversation", [])
        
        # Simplified logic: progress to next phase after a certain number of exchanges
        # In a real implementation, this would be based on objective completion
        num_exchanges = len(conversation) // 2  # Each exchange is a user message and assistant response
        
        if current_phase == ConversationPhase.INITIAL and num_exchanges >= 3:
            return ConversationPhase.SKILLS_EXPLORATION
        elif current_phase == ConversationPhase.SKILLS_EXPLORATION and num_exchanges >= 6:
            return ConversationPhase.VALUES_EXPLORATION
        elif current_phase == ConversationPhase.VALUES_EXPLORATION and num_exchanges >= 9:
            return ConversationPhase.MARKET_ALIGNMENT
        elif current_phase == ConversationPhase.MARKET_ALIGNMENT and num_exchanges >= 12:
            return ConversationPhase.REFINEMENT
        elif current_phase == ConversationPhase.REFINEMENT and num_exchanges >= 15:
            return ConversationPhase.ROADMAP
        
        # Default: stay in current phase
        return current_phase
    
    def _create_cv_analysis_prompt(self, cv_text: str) -> str:
        """Create a structured prompt for CV analysis."""
        return f"""
        Please analyze the following CV and extract structured information including personal information, 
        skills (both technical and soft skills), work experience, education, certifications, projects, and other relevant 
        information. Also provide a brief analysis of the CV's strengths and potential areas for improvement.
        
        Format your response as a JSON object with the following structure:
        {{
            "personal_information": {{
                "name": "full name",
                "email": "email address",
                "phone": "phone number",
                "location": "location"
            }},
            "skills": {{
                "technical": ["skill1", "skill2", ...],
                "soft": ["skill1", "skill2", ...]
            }},
            "work_experience": [
                {{
                    "company": "company name",
                    "position": "position title",
                    "duration": "duration",
                    "description": "brief description",
                    "achievements": ["achievement1", "achievement2", ...]
                }},
                ...
            ],
            "education": [
                {{
                    "institution": "institution name",
                    "degree": "degree name",
                    "field": "field of study",
                    "duration": "duration"
                }},
                ...
            ],
            "certifications": [
                {{
                    "name": "certification name",
                    "issuer": "issuing organization",
                    "date": "issue date"
                }},
                ...
            ],
            "projects": [
                {{
                    "name": "project name",
                    "description": "brief description",
                    "technologies": ["tech1", "tech2", ...]
                }},
                ...
            ],
            "analysis": {{
                "strengths": ["strength1", "strength2", ...],
                "improvement_areas": ["area1", "area2", ...],
                "industry_fit": ["industry1", "industry2", ...],
                "role_fit": ["role1", "role2", ...]
            }}
        }}
        
        CV Text:
        {cv_text}
        """
    
    def _create_roadmap_prompt(self, session_data: Dict[str, Any]) -> str:
        """Create a structured prompt for roadmap generation."""
        # Extract relevant information from session data
        collected_info = session_data.get("collected_information", {})
        cv_analysis = session_data.get("cv_analysis", {})
        
        prompt = f"""
        Please create a detailed career development roadmap based on the following user information. The roadmap should include 
        short-term goals (6-12 months), medium-term goals (1-3 years), and long-term vision (3-5+ years). Include specific 
        skills to develop, learning resources, networking strategies, and success metrics.
        
        Format your response as a JSON object with the following structure:
        {{
            "short_term_goals": [
                {{
                    "goal": "specific goal",
                    "actions": ["action1", "action2", ...],
                    "timeline": "estimated timeline",
                    "success_criteria": "how to measure success"
                }},
                ...
            ],
            "medium_term_goals": [
                {{
                    "goal": "specific goal",
                    "actions": ["action1", "action2", ...],
                    "timeline": "estimated timeline",
                    "success_criteria": "how to measure success"
                }},
                ...
            ],
            "long_term_vision": {{
                "career_path": "target career path",
                "position": "target position",
                "industry": "target industry",
                "timeline": "estimated timeline"
            }},
            "skills_to_develop": [
                {{
                    "skill": "skill name",
                    "priority": "high/medium/low",
                    "resources": ["resource1", "resource2", ...],
                    "estimated_time": "time investment"
                }},
                ...
            ],
            "networking_strategy": [
                {{
                    "approach": "networking approach",
                    "platforms": ["platform1", "platform2", ...],
                    "actions": ["action1", "action2", ...]
                }},
                ...
            ],
            "success_metrics": ["metric1", "metric2", ...]
        }}
        
        User Information:
        {json.dumps({
            "career_goals": collected_info.get("career_goals", []),
            "skills": collected_info.get("skills", {}),
            "values": collected_info.get("values", []),
            "target_industries": collected_info.get("target_industries", []),
            "target_roles": collected_info.get("target_roles", []),
            "skill_gaps": collected_info.get("skill_gaps", []),
            "cv_analysis": {
                "skills": cv_analysis.get("skills", {}),
                "work_experience": cv_analysis.get("work_experience", []),
                "education": cv_analysis.get("education", []),
                "analysis": cv_analysis.get("analysis", {})
            }
        }, indent=2)}
        
        Conversation Highlights:
        {self._extract_conversation_highlights(session_data)}
        """
        
        return prompt
    
    def _extract_conversation_highlights(self, session_data: Dict[str, Any]) -> str:
        """Extract key highlights from the conversation history."""
        highlights = []
        
        # Get conversation
        conversation = session_data.get("conversation", [])
        
        # Simplified approach: extract user messages
        for message in conversation:
            if message["role"] == "user":
                # Add to highlights if the message is substantial (more than 20 chars)
                if len(message["content"]) > 20:
                    highlights.append(f"- \"{message['content'][:100]}...\"")
        
        # Limit to 10 highlights
        if len(highlights) > 10:
            highlights = highlights[-10:]
        
        return "\n".join(highlights)
    
    def _update_session_with_cv_insights(self, session_data: Dict[str, Any], cv_analysis: Dict[str, Any]) -> None:
        """Update session data with insights from CV analysis."""
        collected_info = session_data.get("collected_information", {})
        
        # Extract skills
        skills = cv_analysis.get("skills", {})
        collected_info["skills"] = {
            "technical": collected_info.get("skills", {}).get("technical", []) + skills.get("technical", []),
            "soft": collected_info.get("skills", {}).get("soft", []) + skills.get("soft", [])
        }
        
        # Remove duplicates
        collected_info["skills"]["technical"] = list(set(collected_info["skills"]["technical"]))
        collected_info["skills"]["soft"] = list(set(collected_info["skills"]["soft"]))
        
        # Extract industry and role fit
        analysis = cv_analysis.get("analysis", {})
        collected_info["target_industries"] = list(set(
            collected_info.get("target_industries", []) + analysis.get("industry_fit", [])
        ))
        collected_info["target_roles"] = list(set(
            collected_info.get("target_roles", []) + analysis.get("role_fit", [])
        ))
        
        # Update session data
        session_data["collected_information"] = collected_info
    
    def _load_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data from storage."""
        session_file = os.path.join(self.user_data_dir, f"session_{session_id}.json")
        
        if not os.path.exists(session_file):
            return None
        
        try:
            with open(session_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None
    
    def _save_session_data(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """Save session data to storage."""
        session_file = os.path.join(self.user_data_dir, f"session_{session_id}.json")
        
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)
