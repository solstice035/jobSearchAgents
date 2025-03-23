#!/usr/bin/env python3
"""
Test script for the Conversation Flow structure.

This script instantiates the ConversationFlow class and validates the basic structure
by printing information about each phase and transitions.
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.career_coach.conversation_flow import ConversationFlow, ConversationPhase

def test_conversation_flow():
    """Test the conversation flow structure by printing out phase information."""
    
    # Create an instance of ConversationFlow
    flow = ConversationFlow()
    
    print("===== CAREER COACH CONVERSATION FLOW STRUCTURE =====\n")
    
    # Test and print information for each phase
    for phase in ConversationPhase:
        print(f"PHASE: {phase.name} ({phase.value})")
        
        # Get phase info
        phase_info = flow.get_phase_info(phase)
        
        print(f"Description: {phase_info.get('description', 'N/A')}")
        
        print("\nObjectives:")
        for objective in phase_info.get('objectives', []):
            print(f"- {objective}")
        
        print("\nCompletion Criteria:")
        for criterion in phase_info.get('completion_criteria', []):
            print(f"- {criterion}")
        
        print("\nSample Questions:")
        for question in flow.get_questions_for_phase(phase):
            print(f"- {question}")
        
        # Get next phases
        next_phases = flow.get_next_phases(phase)
        
        print("\nPossible Next Phases:")
        if next_phases:
            for next_phase in next_phases:
                print(f"- {next_phase.name} ({next_phase.value})")
        else:
            print("- None (End of flow)")
        
        print("\n" + "=" * 60 + "\n")
    
    # Test the flow sequence
    print("Full Conversation Flow Sequence:")
    current_phase = ConversationPhase.INITIAL
    sequence = [current_phase]
    
    while True:
        next_phases = flow.get_next_phases(current_phase)
        if not next_phases:
            break
        current_phase = next_phases[0]  # Take the first possible next phase
        sequence.append(current_phase)
    
    print(" -> ".join([phase.name for phase in sequence]))

if __name__ == "__main__":
    test_conversation_flow()
