# User Onboarding Flow

This diagram illustrates the user onboarding process for the Agentic AI Job Search Assistant.

```mermaid
flowchart TD
    Start([Start]) --> A[Landing Page]
    A -->|Sign Up| B[Account Creation]
    B --> C[Authentication]
    C --> D[Profile Setup]
    
    subgraph Profile Setup Process
        D -->|Upload CV| E[Document Processing]
        D -->|Connect LinkedIn| F[LinkedIn Profile Import]
        D -->|Manual Entry| G[Direct Preference Input]
        
        E --> H[AI Document Analysis]
        F --> H
        G --> I[Preference Confirmation]
        
        H -->|Generate Career Profile| I
        I -->|Review & Adjust| J[Profile Refinement]
        J -->|Confirm| K[Profile Finalization]
    end
    
    K --> L[Agent Activation]
    
    subgraph Agent Configuration
        L -->|Set Automation Level| M[Agent Permission Setup]
        M -->|Configure Notifications| N[Notification Preferences]
        N -->|Set Search Parameters| O[Job Search Criteria]
    end
    
    O --> P[Guided Tour]
    P --> Q[Dashboard Preview]
    Q --> End([Onboarding Complete])
    
    style Start fill:#6CE5E8,stroke:#333,stroke-width:2px
    style End fill:#6CE5E8,stroke:#333,stroke-width:2px
    style Profile Setup Process fill:#f5f5f5,stroke:#ddd,stroke-width:2px
    style Agent Configuration fill:#f5f5f5,stroke:#ddd,stroke-width:2px
```

## Detailed Process Description

### Initial Access
1. **Landing Page**: User encounters the system's landing page highlighting key features
2. **Account Creation**: User creates an account with email or social login
3. **Authentication**: User completes authentication process

### Profile Setup Process
4. **Profile Setup Options**:
   - **Upload CV**: User uploads resume/CV document(s)
   - **Connect LinkedIn**: User authorizes LinkedIn profile access
   - **Manual Entry**: User manually enters career information
   
5. **AI Document Analysis**: The system automatically processes documents to extract:
   - Skills and competencies
   - Work history and achievements
   - Education and certifications
   - Career trajectory

6. **Preference Confirmation**: The system presents extracted information for user confirmation
7. **Profile Refinement**: User reviews AI-generated insights and makes adjustments
8. **Profile Finalization**: User confirms the final career profile

### Agent Configuration
9. **Agent Activation**: The autonomous agent system is initialized
10. **Agent Permission Setup**: User configures automation levels:
    - Full automation (agent acts independently)
    - Semi-automation (agent requests approval for key actions)
    - Guided mode (agent suggests but user initiates actions)
    
11. **Notification Preferences**: User sets communication preferences
12. **Job Search Criteria**: User confirms initial job search parameters

### Orientation
13. **Guided Tour**: Interactive walkthrough of key features
14. **Dashboard Preview**: Preview of personalized dashboard with initial agent insights

The onboarding process emphasizes minimal user effort with maximum data collection, setting the stage for highly personalized autonomous operation.
