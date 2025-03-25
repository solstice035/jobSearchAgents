# System Architecture

This document outlines the agentic architecture of the AI Job Search Assistant, illustrating how multiple specialized agents coordinate to deliver a cohesive, autonomous job search experience.

## Agent-Based Architecture

The application follows an agentic architecture with specialized agents communicating through a central message bus. A React frontend interacts with the agent system through a Flask backend API. The system leverages AI services through the OpenAI API and Perplexity API to power different agent capabilities.

```mermaid
graph TD
    User([User]) <--> UserDashboard[User Dashboard]
    UserDashboard <--> API[Agent API Layer]
    
    subgraph "Agent Framework"
        API <--> MessageBus[Message Bus]
        MessageBus <--> AgentRegistry[Agent Registry]
        MessageBus <--> AgentOrchestrator[Agent Orchestrator]
        
        AgentOrchestrator <--> CVAnalysisAgent[CV Analysis Agent]
        AgentOrchestrator <--> CareerCoachAgent[Career Coach Agent]
        AgentOrchestrator <--> JobSearchAgent[Job Search Agent]
        AgentOrchestrator <--> ApplicationAgent[Application Tracking Agent]
        AgentOrchestrator <--> InterviewAgent[Interview Prep Agent]
        AgentOrchestrator <--> LearningAgent[Learning System Agent]
        
        AgentRegistry --- MonitorSystem[Monitoring System]
    end
    
    CVAnalysisAgent <--> DocumentStore[(Document Store)]
    CareerCoachAgent <--> OpenAI[OpenAI GPT-4o API]
    JobSearchAgent <--> Perplexity[Perplexity API]
    ApplicationAgent <--> EmailServices[Email Services]
    
    subgraph "Memory System"
        SharedMemory[Shared Memory]
        UserPreferences[User Preferences]
        AgentContext[Agent Context]
    end
    
    AgentOrchestrator <--> SharedMemory
    
    classDef agentNode fill:#b3e0ff,stroke:#0066cc,stroke-width:2px
    classDef systemNode fill:#ffe6cc,stroke:#ff9933,stroke-width:2px
    classDef externalNode fill:#f5f5f5,stroke:#cccccc,stroke-width:1px
    
    class CVAnalysisAgent,CareerCoachAgent,JobSearchAgent,ApplicationAgent,InterviewAgent,LearningAgent agentNode
    class MessageBus,AgentRegistry,AgentOrchestrator,MonitorSystem systemNode
    class OpenAI,Perplexity,EmailServices externalNode
```

## Agent Framework Components

The agent system consists of specialized agents with specific responsibilities:

```mermaid
graph TD
    AgentFramework[Agent Framework] --> BaseAgent[Base Agent]
    AgentFramework --> MessageBus[Message Bus]
    AgentFramework --> Registry[Agent Registry]
    AgentFramework --> Monitoring[Agent Monitoring]
    AgentFramework --> Memory[Memory Management]
    
    BaseAgent --> CVAgent[CV Analysis Agent]
    BaseAgent --> CoachAgent[Career Coach Agent]
    BaseAgent --> JobAgent[Job Search Agent]
    BaseAgent --> DocAgent[Document Customization Agent]
    BaseAgent --> ApplicationAgent[Application Tracking Agent]
    BaseAgent --> InterviewAgent[Interview Preparation Agent]
    BaseAgent --> LearningAgent[Learning System Agent]
    
    CVAgent -->|Capabilities| CV_Cap[Document Analysis]
    CoachAgent -->|Capabilities| Coach_Cap[Conversation & Roadmap]
    JobAgent -->|Capabilities| Job_Cap[Job Discovery & Matching]
    DocAgent -->|Capabilities| Doc_Cap[Resume & Cover Letter Generation]
    ApplicationAgent -->|Capabilities| App_Cap[Status Tracking & Follow-up]
    InterviewAgent -->|Capabilities| Int_Cap[Question Generation & Feedback]
    LearningAgent -->|Capabilities| Learn_Cap[Pattern Learning & Optimization]
    
    classDef baseNode fill:#f0f8ff,stroke:#0066cc,stroke-width:2px
    classDef agentNode fill:#b3e0ff,stroke:#0066cc,stroke-width:2px
    classDef capabilityNode fill:#d9f2d9,stroke:#339933,stroke-width:2px
    
    class BaseAgent,MessageBus,Registry,Monitoring,Memory baseNode
    class CVAgent,CoachAgent,JobAgent,DocAgent,ApplicationAgent,InterviewAgent,LearningAgent agentNode
    class CV_Cap,Coach_Cap,Job_Cap,Doc_Cap,App_Cap,Int_Cap,Learn_Cap capabilityNode
```

## Agentic Data Flow

This diagram illustrates the flow of data through the system, emphasizing the autonomous, asynchronous nature of the agent architecture:

```mermaid
sequenceDiagram
    participant User
    participant Dashboard as User Dashboard
    participant MessageBus
    participant Memory as Shared Memory
    
    %% Initial CV Upload Flow
    User->>Dashboard: Upload CV
    Dashboard->>MessageBus: CV Upload Event
    MessageBus->>CVAgent: Process CV
    CVAgent->>ExternalAPI: Extract & Analyze
    ExternalAPI->>CVAgent: Analysis Results
    CVAgent->>Memory: Store Profile Data
    CVAgent->>MessageBus: Profile Created Event
    MessageBus->>Dashboard: Update UI
    Dashboard->>User: Show Profile Insights
    
    %% Autonomous Job Discovery Flow
    Note over MessageBus,JobAgent: Continuous Background Process
    MessageBus->>JobAgent: Start Job Discovery
    JobAgent->>Memory: Get User Preferences
    Memory->>JobAgent: Career Preferences
    JobAgent->>ExternalAPI: Search Job Sources
    ExternalAPI->>JobAgent: Job Listings
    JobAgent->>JobAgent: Rank & Filter Jobs
    JobAgent->>Memory: Store Opportunities
    JobAgent->>MessageBus: New Opportunities Event
    MessageBus->>Dashboard: Update Opportunities
    Dashboard->>User: Notify About Matches
    
    %% User-Triggered Application Flow
    User->>Dashboard: Select Job to Apply
    Dashboard->>MessageBus: Application Request
    MessageBus->>DocAgent: Generate Documents
    DocAgent->>Memory: Get User Profile
    Memory->>DocAgent: User Experience & Skills
    DocAgent->>DocAgent: Customize Documents
    DocAgent->>MessageBus: Documents Ready
    MessageBus->>ApplicationAgent: Submit Application
    ApplicationAgent->>ExternalAPI: Submit to Job Portal
    ApplicationAgent->>Memory: Update Application Status
    ApplicationAgent->>MessageBus: Application Submitted
    MessageBus->>Dashboard: Update Application Status
    Dashboard->>User: Confirm Submission
    
    %% Autonomous Follow-up Flow
    Note over ApplicationAgent,Memory: Periodic Background Process
    ApplicationAgent->>Memory: Check Application Status
    ApplicationAgent->>ExternalAPI: Monitor Email
    ExternalAPI->>ApplicationAgent: Status Updates
    ApplicationAgent->>Memory: Update Status
    ApplicationAgent->>MessageBus: Status Change Event
    MessageBus->>Dashboard: Update Status Display
    Dashboard->>User: Notify About Changes
```

## Technology Stack Details

### Agent Framework
- **Base Agent Framework**: Provides core agent capabilities including lifecycle management and messaging
- **Message Bus**: Asynchronous communication system for inter-agent messaging
- **Agent Registry**: Service for agent discovery and management
- **Monitoring System**: Telemetry collection for agent activities and performance
- **Memory Management**: Shared state and context persistence across agents

### Frontend
- **React**: JavaScript library for building the user interface
- **React Router**: For client-side routing
- **Tailwind CSS**: Utility-first CSS framework for styling
- **WebSocket**: For real-time communication with the agent system
- **Framer Motion**: For animations and transitions

### Backend Integration
- **Flask**: Python web framework serving the REST and WebSocket APIs
- **OpenAI Agents SDK**: For creating and managing AI agents
- **Python libraries**:
  - pypdf: For PDF text extraction
  - asyncio: For asynchronous agent operations
  - requests: For API communication
  - websockets: For real-time notifications
  - dotenv: For environment variable management

### External Services
- **OpenAI API**: Powers multiple agents including Career Coach using GPT-4o
- **Perplexity API**: Powers the Job Search agent for opportunity discovery
- **Email Services**: For application tracking and status monitoring

### Storage
- **Document Store**: For CV, resume, and cover letter storage and versioning
- **Preference Store**: For user preferences and settings
- **Agent Memory**: For agent state and context management

## Agent Autonomy Control

The system provides a flexible autonomy management framework that allows users to control the level of agent independence:

```mermaid
graph TD
    UserControls[User Controls] --> AutonomyManager[Autonomy Manager]
    AutonomyManager --> AgentConfig[Agent Configuration]
    
    AgentConfig --> FullAuto[Full Autonomy]
    AgentConfig --> SemiAuto[Semi-Autonomous]
    AgentConfig --> Guided[Guided Mode]
    
    FullAuto --> AutoActions[Autonomous Actions]
    SemiAuto --> ApprovalGates[Approval Gates]
    Guided --> Suggestions[Suggestions Only]
    
    AutoActions --> Notifications[User Notifications]
    ApprovalGates --> UserApproval[User Approval]
    Suggestions --> UserSelection[User Selection]
    
    classDef controlNode fill:#ffe6cc,stroke:#ff9933,stroke-width:2px
    classDef modeNode fill:#f0f8ff,stroke:#0066cc,stroke-width:2px
    classDef actionNode fill:#d9f2d9,stroke:#339933,stroke-width:2px
    
    class UserControls,AutonomyManager,AgentConfig controlNode
    class FullAuto,SemiAuto,Guided modeNode
    class AutoActions,ApprovalGates,Suggestions,Notifications,UserApproval,UserSelection actionNode
```

The autonomy levels are defined as:

1. **Full Autonomy Mode**: Agents operate independently with minimal user intervention
   - Automatic job discovery and matching
   - Automatic document customization
   - Automated application tracking
   - User is notified of significant events and outcomes

2. **Semi-Autonomous Mode**: Agents perform routine tasks but seek approval for significant actions
   - Autonomous research and analysis
   - User approves job applications
   - User confirms document customizations
   - System manages follow-up with user approval

3. **Guided Mode**: Agents suggest actions but do not act without user initiation
   - Recommendations for jobs to apply to
   - Suggestions for resume customizations
   - Proposed follow-up actions
   - User initiates all external actions

Users can set global autonomy preferences or configure autonomy levels for individual agents based on their comfort level.

## Security Considerations

- API keys for OpenAI and Perplexity services are stored in environment variables
- User data is stored locally and not shared with third parties
- File uploads are limited to common document formats for CV analysis
- User has explicit control over agent autonomy levels
- All agent actions are logged for transparency
