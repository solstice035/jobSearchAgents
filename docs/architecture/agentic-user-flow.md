# Agentic User Flow

This document outlines the integrated agentic user flow for the AI Job Search Assistant, describing how various agents work together to provide an end-to-end job search experience.

## Overview

The AI Job Search Assistant employs a coordinated multi-agent approach that guides users through the complete job search lifecycle - from initial career assessment through application tracking and interview preparation. Unlike traditional job search tools, the system operates autonomously on the user's behalf while keeping them informed and in control.

```mermaid
{{include /Users/nicksolly/Dev/jobSearchAgents/docs/diagrams/agentic-job-search-flow.mermaid}}
```

## Phase Descriptions

### 1. Initial Assessment Phase

The process begins with CV analysis, which serves as the foundation for all subsequent agent activities:

- **CV Analysis Agent**: Analyzes the user's resume to extract structured information about skills, experience, education, and achievements
- **Profile Creation**: Automatically generates a comprehensive user profile based on CV analysis
- **Initial Feedback**: Provides immediate insights about resume strengths and improvement areas

This phase leverages the existing document parsing capabilities but enhances them with agent-based analysis that builds a structured knowledge representation of the user's career background.

### 2. Career Coaching Phase

The system then activates the Career Coach Agent which builds upon the CV analysis:

- **Career Goals Exploration**: Uses a structured conversation flow to understand the user's career aspirations
- **Skills Gap Analysis**: Identifies gaps between current skills and career goals
- **Values Assessment**: Explores the user's professional values and work preferences
- **Market Alignment**: Analyzes how the user's profile aligns with current market opportunities
- **Career Roadmap**: Generates a personalized career development plan

This phase leverages the existing Career Coach backend but integrates it with the CV analysis results for a more personalized experience. The coach operates semi-autonomously, guiding the conversation through defined phases.

### 3. Autonomous Job Search Phase

With a rich understanding of the user's background and goals, the system activates the Job Search Agent:

- **Continuous Job Discovery**: Monitors multiple job sources in the background
- **Opportunity Ranking**: Prioritizes opportunities based on match quality and preferences
- **Match Analysis**: Provides detailed assessment of fit for each opportunity
- **Document Customization**: Automatically customizes resumes and cover letters for specific opportunities

Unlike traditional implementations, this phase operates continuously in the background, bringing relevant opportunities to the user's attention rather than requiring manual searches.

### 4. Application Tracking Phase

When the user decides to apply for a position, the Application Tracking Agent activates:

- **Submit Application**: Manages the application submission process
- **Monitor Status**: Tracks application status through email integration and periodic checks
- **Follow-up**: Suggests and potentially automates follow-up communications
- **Outcome Analysis**: Analyzes application results to improve future strategies

This adds a completely new capability to track the full application lifecycle.

### 5. Interview Preparation Phase

For interviews, the Interview Preparation Agent provides specialized assistance:

- **Generate Questions**: Creates customized practice questions based on the job and company
- **Practice Session**: Facilitates interactive interview practice
- **Feedback Analysis**: Provides detailed feedback on responses
- **Strategy Suggestions**: Offers personalized interview strategies

This phase represents another specialized capability focused on interview success.

### 6. Continuous Learning System

Throughout the process, the system continually learns and improves:

- **System Learning**: Updates its knowledge based on application outcomes
- **Improve Matching**: Refines matching algorithms based on user feedback
- **Refine Strategies**: Adapts job search strategies based on what works

## User Dashboard and Control

The User Dashboard serves as the central interface, showing:
- Current agent activities and discoveries
- Recommended actions
- Application status updates
- Upcoming interviews
- Customization opportunities

The user maintains control through preference updates and action selections, but the system operates autonomously based on these preferences.

## Autonomy Levels

The system supports different levels of autonomy that users can adjust:

1. **Guided Mode**: Agents suggest actions but wait for user confirmation
2. **Semi-Autonomous**: Agents perform routine tasks automatically but seek approval for significant actions
3. **Fully Autonomous**: Agents operate independently with minimal user intervention

Users can set global autonomy preferences or adjust settings for specific agents based on their comfort level.

## Agent Communication

Agents communicate through a central message bus, sharing information and coordinating activities:

- **CV Analysis Agent** → **Career Coach Agent**: Shares structured profile information
- **Career Coach Agent** → **Job Search Agent**: Shares career preferences and goals
- **Job Search Agent** → **Document Customization Agent**: Shares job requirements for tailoring
- **Application Tracking Agent** → **Learning System**: Shares outcome data

This inter-agent communication enables a seamless, integrated experience while maintaining a modular architecture.
