import React from 'react';
import { Job } from '../../services/job-search';
import JobCard from './JobCard';

interface JobSearchResultsProps {
  jobs: Job[];
  loading: boolean;
  searchPerformed: boolean;
  onSelectJob: (job: Job) => void;
}

const JobSearchResults: React.FC<JobSearchResultsProps> = ({ 
  jobs, 
  loading, 
  searchPerformed,
  onSelectJob
}) => {
  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mb-4"></div>
        <p className="text-gray-600">Searching for jobs...</p>
      </div>
    );
  }

  if (!searchPerformed) {
    return null;
  }

  if (jobs.length === 0) {
    return (
      <div className="bg-white rounded-lg p-6 text-center border border-gray-200">
        <svg 
          className="mx-auto h-12 w-12 text-gray-400" 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor" 
          aria-hidden="true"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No jobs found</h3>
        <p className="mt-1 text-sm text-gray-500">
          Try adjusting your search criteria for better results.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-900">
          {jobs.length} {jobs.length === 1 ? 'Job' : 'Jobs'} Found
        </h2>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {jobs.map((job, index) => (
          <JobCard key={index} job={job} onSelect={() => onSelectJob(job)} />
        ))}
      </div>
    </div>
  );
};

export default JobSearchResults;
