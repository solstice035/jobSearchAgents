import React, { useState } from 'react';
import { JobSearchParams, searchJobs, JobSearchResponse } from '../../services/job-search';

interface JobSearchFormProps {
  onSearchComplete: (results: JobSearchResponse) => void;
  onSearchStart: () => void;
  userId?: string;
}

const JobSearchForm: React.FC<JobSearchFormProps> = ({ onSearchComplete, onSearchStart, userId }) => {
  const [keywords, setKeywords] = useState('');
  const [location, setLocation] = useState('');
  const [recency, setRecency] = useState<JobSearchParams['recency']>();
  const [experienceLevel, setExperienceLevel] = useState<JobSearchParams['experience_level']>();
  const [remote, setRemote] = useState(false);
  const [usePreferences, setUsePreferences] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!keywords.trim()) {
      setError('Please enter keywords for your search');
      return;
    }
    
    // Clear previous error
    setError(null);
    
    const searchParams: JobSearchParams = {
      keywords,
      location: location || undefined,
      recency,
      experience_level: experienceLevel,
      remote,
      use_preferences: usePreferences,
      user_id: usePreferences ? userId : undefined,
    };
    
    try {
      setIsLoading(true);
      onSearchStart();
      
      const results = await searchJobs(searchParams);
      onSearchComplete(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during search');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-4">Find Job Opportunities</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="keywords" className="block text-sm font-medium text-gray-700 mb-1">
            Job Title, Skills, or Keywords*
          </label>
          <input
            id="keywords"
            type="text"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., Software Engineer, Marketing, Data Science"
            required
          />
        </div>
        
        <div className="mb-4">
          <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
            Location
          </label>
          <input
            id="location"
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., New York, Remote, United States"
          />
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label htmlFor="recency" className="block text-sm font-medium text-gray-700 mb-1">
              Posted Within
            </label>
            <select
              id="recency"
              value={recency || ''}
              onChange={(e) => setRecency(e.target.value as JobSearchParams['recency'] || undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Any time</option>
              <option value="hour">Past hour</option>
              <option value="day">Past day</option>
              <option value="week">Past week</option>
              <option value="month">Past month</option>
            </select>
          </div>
          
          <div>
            <label htmlFor="experienceLevel" className="block text-sm font-medium text-gray-700 mb-1">
              Experience Level
            </label>
            <select
              id="experienceLevel"
              value={experienceLevel || ''}
              onChange={(e) => setExperienceLevel(e.target.value as JobSearchParams['experience_level'] || undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Any level</option>
              <option value="entry">Entry level</option>
              <option value="mid">Mid level</option>
              <option value="senior">Senior level</option>
            </select>
          </div>
        </div>
        
        <div className="flex flex-col gap-2 mb-6">
          <div className="flex items-center">
            <input
              id="remote"
              type="checkbox"
              checked={remote}
              onChange={(e) => setRemote(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="remote" className="ml-2 block text-sm text-gray-700">
              Remote positions only
            </label>
          </div>
          
          {userId && (
            <div className="flex items-center">
              <input
                id="usePreferences"
                type="checkbox"
                checked={usePreferences}
                onChange={(e) => setUsePreferences(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="usePreferences" className="ml-2 block text-sm text-gray-700">
                Enhance search with my preferences
              </label>
            </div>
          )}
        </div>
        
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md text-sm">
            {error}
          </div>
        )}
        
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Searching...' : 'Search Jobs'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default JobSearchForm;
