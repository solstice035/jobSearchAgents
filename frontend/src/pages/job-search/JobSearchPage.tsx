import React, { useState, useEffect } from 'react';
import { 
  JobSearchForm, 
  JobSearchResults, 
  ResumeMatchModal 
} from '../../components/job-search';
import { Job, JobSearchResponse, getUserPreferences, UserPreferences } from '../../services/job-search';

// Assuming we have a user context or auth service to get the current user
// For now, we'll use a fixed user ID for demonstration
const DEMO_USER_ID = 'demo_user_123';

const JobSearchPage: React.FC = () => {
  // State for job search results
  const [searchResults, setSearchResults] = useState<JobSearchResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchPerformed, setSearchPerformed] = useState(false);
  
  // State for resume match modal
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // State for user data
  const [userId] = useState<string>(DEMO_USER_ID);
  const [userPreferences, setUserPreferences] = useState<UserPreferences | null>(null);
  const [userResume, setUserResume] = useState<string>('');
  
  // Load user preferences when the component mounts
  useEffect(() => {
    const loadUserPreferences = async () => {
      try {
        const response = await getUserPreferences(userId);
        setUserPreferences(response.preferences);
        
        // If the user has a stored resume in preferences, load it
        if (response.preferences.resumeText) {
          setUserResume(response.preferences.resumeText);
        }
      } catch (error) {
        console.error('Error loading user preferences:', error);
      }
    };
    
    loadUserPreferences();
  }, [userId]);
  
  const handleSearchStart = () => {
    setIsSearching(true);
    setSearchResults(null);
  };
  
  const handleSearchComplete = (results: JobSearchResponse) => {
    setSearchResults(results);
    setIsSearching(false);
    setSearchPerformed(true);
  };
  
  const handleSelectJob = (job: Job) => {
    setSelectedJob(job);
    setIsModalOpen(true);
  };
  
  const closeModal = () => {
    setIsModalOpen(false);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Job Search</h1>
        <p className="mt-2 text-lg text-gray-600">
          Discover opportunities that match your skills and career goals
        </p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <JobSearchForm 
            onSearchStart={handleSearchStart} 
            onSearchComplete={handleSearchComplete}
            userId={userId}
          />
          
          {/* You can add additional components here like filters, saved searches, etc. */}
          {userPreferences && (
            <div className="mt-6 bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-lg font-semibold mb-2">Your Preferences</h2>
              
              {userPreferences.technicalSkills && userPreferences.technicalSkills.length > 0 && (
                <div className="mb-3">
                  <h3 className="text-sm font-medium text-gray-700">Technical Skills</h3>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {userPreferences.technicalSkills.map((skill, index) => (
                      <span key={index} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {userPreferences.jobTypes && userPreferences.jobTypes.length > 0 && (
                <div className="mb-3">
                  <h3 className="text-sm font-medium text-gray-700">Job Types</h3>
                  <div className="mt-1">
                    {userPreferences.jobTypes.join(', ')}
                  </div>
                </div>
              )}
              
              {userPreferences.careerGoals && (
                <div className="mb-3">
                  <h3 className="text-sm font-medium text-gray-700">Career Goals</h3>
                  <div className="mt-1 text-sm">
                    {userPreferences.careerGoals}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        
        <div className="lg:col-span-2">
          <JobSearchResults 
            jobs={searchResults?.jobs || []}
            loading={isSearching}
            searchPerformed={searchPerformed}
            onSelectJob={handleSelectJob}
          />
        </div>
      </div>
      
      <ResumeMatchModal 
        job={selectedJob}
        isOpen={isModalOpen}
        onClose={closeModal}
        userResume={userResume}
      />
    </div>
  );
};

export default JobSearchPage;
