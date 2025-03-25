import React, { useState } from 'react';
import { Job } from '../../services/job-search';

interface JobCardProps {
  job: Job;
  onSelect?: (job: Job) => void;
}

const JobCard: React.FC<JobCardProps> = ({ job, onSelect }) => {
  const [expanded, setExpanded] = useState(false);

  const toggleExpanded = () => {
    setExpanded(!expanded);
  };

  const handleSelect = () => {
    if (onSelect) {
      onSelect(job);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
      <div className="p-5">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              {job.title || 'Untitled Position'}
            </h3>
            <p className="text-sm text-gray-600 mb-1">
              {job.company || 'Unknown Company'}
            </p>
            
            <div className="flex flex-wrap gap-2 mb-3">
              {job.location && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {job.location}
                </span>
              )}
              
              {job.job_type && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  {job.job_type}
                </span>
              )}
              
              {job.salary && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                  {job.salary}
                </span>
              )}
            </div>
          </div>
          
          <button
            onClick={handleSelect}
            className="ml-2 px-3 py-1 text-sm text-blue-600 hover:text-blue-800 font-medium rounded-md hover:bg-blue-50 transition-colors"
          >
            Match CV
          </button>
        </div>
        
        {expanded ? (
          <div className="mt-4 space-y-4">
            {job.description && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-1">Description</h4>
                <p className="text-sm text-gray-600">{job.description}</p>
              </div>
            )}
            
            {job.requirements && job.requirements.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-1">Requirements</h4>
                <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
                  {job.requirements.map((req, index) => (
                    <li key={index}>{req}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {job.benefits && job.benefits.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-1">Benefits</h4>
                <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
                  {job.benefits.map((benefit, index) => (
                    <li key={index}>{benefit}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {job.application_link && (
              <div className="pt-2">
                <a
                  href={job.application_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Apply Now
                </a>
              </div>
            )}
          </div>
        ) : (
          job.description && (
            <p className="mt-2 text-sm text-gray-500 line-clamp-2">
              {job.description}
            </p>
          )
        )}
      </div>
      
      <div className="px-5 py-3 bg-gray-50 text-right">
        <button
          onClick={toggleExpanded}
          className="text-sm text-gray-600 hover:text-gray-900 font-medium focus:outline-none"
        >
          {expanded ? 'Show Less' : 'Show More'}
        </button>
      </div>
    </div>
  );
};

export default JobCard;
