# Backend API Reference

This document provides a detailed reference for all API endpoints available in the AI Career Coach & Job Search Agent backend.

## Base URL

When running locally, the API is available at:

```
http://localhost:5000/api
```

## API Endpoints

### Job Search Endpoints

#### Search for Jobs

Search for job openings based on provided criteria.

```
POST /search
```

**Request Body:**

```json
{
  "keywords": "data scientist",
  "location": "London",
  "experience": "mid",
  "recency": "week",
  "usePreferences": true
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| keywords | string | Yes | Job title, skills, or other keywords |
| location | string | No | City, state, country, or "remote" |
| experience | string | No | Experience level ("entry", "mid", "senior", "executive") |
| recency | string | No | Time filter ("day", "week", "month"). Default: "week" |
| usePreferences | boolean | No | Whether to enhance search with user preferences. Default: false |

**Response:**

```json
{
  "choices": [
    {
      "message": {
        "content": "...",
        "role": "assistant"
      },
      "index": 0,
      "finish_reason": "stop"
    }
  ],
  "id": "...",
  "object": "chat.completion",
  "created": 1678923928,
  "model": "sonar",
  "usage": {
    "prompt_tokens": 325,
    "completion_tokens": 958,
    "total_tokens": 1283
  }
}
```

### User Preferences Endpoints

#### Get User Preferences

Retrieve the user's stored career preferences.

```
GET /preferences
```

**Response:**

```json
{
  "technicalSkills": ["Python", "Data Analysis", "Machine Learning"],
  "softSkills": ["Communication", "Problem Solving"],
  "careerGoals": "Transition into a data science role in fintech",
  "jobTypes": ["Full-time", "Remote"],
  "workValues": ["Work-life balance", "Growth opportunities"],
  "careerCoachSession": {
    "current_exploration_phase": "refinement",
    "identified_strengths": ["Python", "SQL", "Data Analysis"],
    "identified_gaps": ["Deep Learning", "Cloud Infrastructure"],
    "explored_career_paths": ["Data Scientist", "Machine Learning Engineer"]
  }
}
```

#### Save User Preferences

Save or update the user's career preferences.

```
POST /preferences
```

**Request Body:**

```json
{
  "technicalSkills": ["Python", "Data Analysis", "Machine Learning"],
  "softSkills": ["Communication", "Problem Solving"],
  "careerGoals": "Transition into a data science role in fintech",
  "jobTypes": ["Full-time", "Remote"],
  "workValues": ["Work-life balance", "Growth opportunities"]
}
```

**Response:**

```json
{
  "success": true,
  "preferences": {
    "technicalSkills": ["Python", "Data Analysis", "Machine Learning"],
    "softSkills": ["Communication", "Problem Solving"],
    "careerGoals": "Transition into a data science role in fintech",
    "jobTypes": ["Full-time", "Remote"],
    "workValues": ["Work-life balance", "Growth opportunities"]
  }
}
```

### Career Coach Endpoints

#### Parse CV Text

Analyze CV text content to extract insights.

```
POST /career-coach/parse-cv
```

**Request Body:**

```json
{
  "cv_text": "Full CV text content..."
}
```

**Response:**

```json
{
  "cv_data": {
    "personal_information": { ... },
    "skills": {
      "technical": [ ... ],
      "soft": [ ... ]
    },
    "work_experience": [ ... ],
    "education": [ ... ],
    "certifications": [ ... ]
  },
  "analysis": "Detailed analysis text...",
  "session_summary": {
    "current_phase": "initial",
    "conversation_count": 1,
    "analyzed_documents": ["CV"],
    "identified_strengths": [ ... ],
    "identified_gaps": [ ... ],
    "explored_career_paths": [ ... ]
  }
}
```

#### Upload CV File

Upload and analyze a CV file.

```
POST /career-coach/upload-cv
```

**Request:**

Form data with a file upload field named "file"

**Response:**

```json
{
  "cv_data": { ... },
  "analysis": "Detailed analysis text...",
  "session_summary": { ... },
  "file_info": {
    "filename": "resume.pdf",
    "page_count": 2,
    "metadata": { ... }
  }
}
```

#### Get Next Question

Retrieve the next relevant question for career exploration.

```
GET /career-coach/next-question
```

**Response:**

```json
{
  "question": "What aspects of your current or previous roles have you found most energizing?",
  "context": "values",
  "id": "q_5"
}
```

#### Process Message

Process a user message and get a response from the Career Coach.

```
POST /career-coach/process-message
```

**Request Body:**

```json
{
  "message": "I'm interested in transitioning from software development to data science."
}
```

**Response:**

```json
{
  "response": "That's an excellent career direction to explore...",
  "session_summary": {
    "current_phase": "refinement",
    "conversation_count": 12,
    "analyzed_documents": ["CV"],
    "identified_strengths": [ ... ],
    "identified_gaps": [ ... ],
    "explored_career_paths": [ ... ]
  }
}
```

#### Generate Career Roadmap

Generate a personalized career development roadmap.

```
GET /career-coach/career-roadmap
```

**Response:**

```json
{
  "roadmap": "# PERSONALIZED CAREER ROADMAP\n\n## Short-term Goals (6-12 months)\n...",
  "session_summary": { ... }
}
```

#### Analyze Skill Gaps

Analyze skill gaps for a target role.

```
POST /career-coach/skill-gaps
```

**Request Body:**

```json
{
  "target_role": "Data Scientist"
}
```

**Response:**

```json
{
  "target_role": "Data Scientist",
  "analysis": "# SKILL GAP ANALYSIS\n\n## Essential Skills for Data Scientists\n...",
  "session_summary": { ... }
}
```

#### Get Session Information

Get the current session summary.

```
GET /career-coach/session
```

**Response:**

```json
{
  "current_phase": "values",
  "conversation_count": 8,
  "analyzed_documents": ["CV"],
  "identified_strengths": [ ... ],
  "identified_gaps": [ ... ],
  "explored_career_paths": [ ... ]
}
```

### System Endpoints

#### Health Check

Check if the API is running.

```
GET /api/health
```

**Response:**

```json
{
  "status": "ok"
}
```

## Error Responses

All endpoints return appropriate HTTP status codes and error messages in case of failure:

**Example Error Response:**

```json
{
  "error": "Target role is required"
}
```

**Common Error Status Codes:**

- `400 Bad Request`: Missing or invalid parameters
- `500 Internal Server Error`: Server-side issues

## Authentication

The current implementation does not require authentication for API endpoints, as it's designed for local usage. For production deployment, proper authentication would need to be implemented.
