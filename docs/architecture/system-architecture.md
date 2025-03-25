# System Architecture

This document outlines the architecture of the AI Career Coach & Job Search Agent application, illustrating how various components interact to deliver the functionality.

## High-Level Architecture

The application follows a client-server architecture with a React frontend communicating with a Flask backend. The backend leverages AI services through the OpenAI API and Perplexity API to provide job search and career coaching capabilities.

```mermaid
graph TD
    User([User]) <--> Frontend[React Frontend]
    Frontend <--> Backend[Flask Backend API]
    Backend <--> OpenAI[OpenAI GPT-4o API]
    Backend <--> Perplexity[Perplexity API]
    Backend <--> LocalStorage[(Local Storage)]
    
    subgraph "Client Side"
        Frontend
    end
    
    subgraph "Server Side"
        Backend
        LocalStorage
    end
    
    subgraph "External Services"
        OpenAI
        Perplexity
    end
```

## Component Diagram

The application is organized into the following key components:

```mermaid
graph TD
    Frontend[Frontend] --> JobSearchUI[Job Search Interface]
    Frontend --> CareerCoachUI[Career Coach Interface]
    Frontend --> ProfileUI[User Profile Interface]
    
    Backend[Backend] --> JobSearchAgent[Job Search Agent]
    Backend --> CareerCoachAgent[Career Coach Agent]
    Backend --> DocumentParser[Document Parser]
    Backend --> PreferencesManager[Preferences Manager]
    
    JobSearchAgent --> PerplexityAPI[Perplexity API]
    CareerCoachAgent --> OpenAIAPI[OpenAI API]
    DocumentParser --> PDFExtractor[PDF Extractor]
    
    PreferencesManager --> LocalStorage[(Local Storage)]
```

## Data Flow Diagram

This diagram illustrates the flow of data through the system for key user actions:

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant AI Services
    participant Storage
    
    %% Job Search Flow
    User->>Frontend: Search for Jobs
    Frontend->>Backend: API Request
    Backend->>AI Services: Query Perplexity API
    AI Services->>Backend: Job Results
    Backend->>Frontend: Formatted Results
    Frontend->>User: Display Job Listings
    
    %% CV Analysis Flow
    User->>Frontend: Upload CV
    Frontend->>Backend: Send CV for Analysis
    Backend->>DocumentParser: Extract Text
    DocumentParser->>Backend: CV Text
    Backend->>AI Services: Request Analysis (OpenAI)
    AI Services->>Backend: CV Analysis & Insights
    Backend->>Storage: Store User Profile Data
    Backend->>Frontend: Analysis Results
    Frontend->>User: Display Career Insights
    
    %% Career Roadmap Flow
    User->>Frontend: Request Career Roadmap
    Frontend->>Backend: API Request
    Backend->>Storage: Retrieve User Profile Data
    Storage->>Backend: User Preferences & Data
    Backend->>AI Services: Generate Roadmap (OpenAI)
    AI Services->>Backend: Personalized Roadmap
    Backend->>Frontend: Roadmap Data
    Frontend->>User: Display Career Roadmap
```

## Technology Stack Details

### Frontend
- **React**: JavaScript library for building the user interface
- **React Router**: For client-side routing
- **Tailwind CSS**: Utility-first CSS framework for styling
- **Framer Motion**: For animations and transitions

### Backend
- **Flask**: Python web framework serving the REST API
- **OpenAI Agents SDK**: For creating and managing AI agents
- **Python libraries**:
  - pypdf: For PDF text extraction
  - requests: For API communication
  - dotenv: For environment variable management

### External Services
- **OpenAI API**: Powers the Career Coach agent using GPT-4o
- **Perplexity API**: Powers the Job Search agent

### Storage
- Local file system for storing user preferences

## Security Considerations

- API keys for OpenAI and Perplexity services are stored in environment variables
- User data is stored locally and not shared with third parties
- File uploads are limited to common document formats for CV analysis
