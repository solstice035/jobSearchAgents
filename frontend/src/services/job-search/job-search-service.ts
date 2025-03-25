/**
 * Service for interacting with the Job Search API
 */

import { API_BASE_URL } from '../config';

/**
 * Job search parameters
 */
export interface JobSearchParams {
  keywords: string;
  location?: string;
  recency?: 'month' | 'week' | 'day' | 'hour';
  experience_level?: 'entry' | 'mid' | 'senior';
  remote?: boolean;
  use_preferences?: boolean;
  user_id?: string;
}

/**
 * Job object returned from the API
 */
export interface Job {
  title: string | null;
  company: string | null;
  location: string | null;
  job_type: string | null;
  salary: string | null;
  description: string | null;
  requirements: string[];
  benefits: string[];
  application_link: string | null;
  full_text: string;
}

/**
 * Search response metadata
 */
export interface SearchMetadata {
  search_criteria: {
    keywords: string;
    location?: string;
    recency?: string;
    experience_level?: string;
    remote?: boolean;
  };
  enhanced_criteria?: {
    keywords: string;
    location?: string;
    recency?: string;
    experience_level?: string;
    remote?: boolean;
  };
  preferences_used?: boolean;
  timestamp: string;
  search_id: string;
}

/**
 * Job search response
 */
export interface JobSearchResponse {
  jobs: Job[];
  metadata: SearchMetadata;
  status: string;
}

/**
 * Resume match parameters
 */
export interface ResumeMatchParams {
  job_description: string;
  resume_text?: string;
  resume_file?: File;
}

/**
 * Resume match response
 */
export interface ResumeMatchResponse {
  match_score: number;
  analysis: string;
  status: string;
}

/**
 * User preferences
 */
export interface UserPreferences {
  technicalSkills?: string[];
  softSkills?: string[];
  careerGoals?: string;
  jobTypes?: string[];
  workValues?: string[];
  [key: string]: any;
}

/**
 * Search for jobs based on criteria
 */
export const searchJobs = async (params: JobSearchParams): Promise<JobSearchResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/job-search/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Failed to search for jobs');
    }
    
    return response.json();
  } catch (error) {
    console.error('Error searching for jobs:', error);
    throw error;
  }
};

/**
 * Analyze how well a resume matches a job description
 */
export const analyzeResumeMatch = async (params: ResumeMatchParams): Promise<ResumeMatchResponse> => {
  try {
    let response;
    
    if (params.resume_file) {
      // Send as form data if a file is provided
      const formData = new FormData();
      formData.append('resume_file', params.resume_file);
      formData.append('job_description', params.job_description);
      
      response = await fetch(`${API_BASE_URL}/job-search/match`, {
        method: 'POST',
        body: formData,
      });
    } else if (params.resume_text) {
      // Send as JSON if text is provided
      response = await fetch(`${API_BASE_URL}/job-search/match`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resume_text: params.resume_text,
          job_description: params.job_description,
        }),
      });
    } else {
      throw new Error('Either resume_text or resume_file must be provided');
    }
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Failed to analyze resume match');
    }
    
    return response.json();
  } catch (error) {
    console.error('Error analyzing resume match:', error);
    throw error;
  }
};

/**
 * Save user preferences
 */
export const saveUserPreferences = async (userId: string, preferences: UserPreferences): Promise<{ status: string; message: string }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/job-search/preferences`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        preferences,
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Failed to save preferences');
    }
    
    return response.json();
  } catch (error) {
    console.error('Error saving preferences:', error);
    throw error;
  }
};

/**
 * Get user preferences
 */
export const getUserPreferences = async (userId: string): Promise<{ preferences: UserPreferences; status: string }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/job-search/preferences/${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Failed to get preferences');
    }
    
    return response.json();
  } catch (error) {
    console.error('Error getting preferences:', error);
    throw error;
  }
};
