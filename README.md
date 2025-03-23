# Agentic AI Job Search Assistant

An autonomous AI agent that manages the entire job search lifecycle - from analyzing career goals and preferences, identifying job opportunities, customizing application materials, to preparing for interviews.

## Project Structure

```
jobSearchAgents/
├── backend/             # Flask backend
│   ├── api/             # API endpoints
│   ├── blueprints/      # Flask blueprints
│   ├── models/          # Data models
│   ├── services/        # Business logic and services
│   ├── utils/           # Utility functions
│   ├── config/          # Configuration files
│   ├── app.py           # Main application entry point
│   └── requirements.txt # Python dependencies
│
└── frontend/            # React/TypeScript frontend
    ├── public/          # Static files
    └── src/             # Source files
        ├── components/  # Reusable UI components
        ├── pages/       # Page components
        ├── services/    # API services
        ├── utils/       # Utility functions
        ├── hooks/       # Custom React hooks
        ├── contexts/    # React contexts
        ├── types/       # TypeScript type definitions
        └── styles/      # CSS and styling files
```

## Getting Started

### Backend Setup
1. Navigate to the backend directory: `cd backend`
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure environment variables
6. Run the application: `python app.py`

### Frontend Setup
1. Navigate to the frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Start the development server: `npm start`

## Features

- CV analysis and career coaching using OpenAI GPT-4o
- Job search and matching using the Perplexity API
  - Basic and preference-enhanced job searching
  - Resume-job matching and analysis
  - Multiple source job discovery
- Career roadmap generation
- Application tracking
- Document customization
